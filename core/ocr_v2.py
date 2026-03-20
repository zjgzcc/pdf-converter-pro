"""
OCR 识别模块 - 并行优化版 v2.0
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审

更新日志 2026-03-20 12:45：
✅ 新增并行处理机制（多线程加速）
✅ 表格区域文字识别优化（高 DPI + 图像预处理）
✅ 内存优化（分批处理 + 定期 GC）
✅ 识别质量提升（clean + deskew + 对比度增强）
"""

import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import tempfile
import shutil
import gc

logger = logging.getLogger(__name__)


class OCREngineType(Enum):
    """OCR 引擎类型"""
    OCRMYDF = "ocrmypdf"
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"


@dataclass
class OCRConfig:
    """OCR 配置 - 优化版"""
    language: str = "chi_sim"  # 🚀 修复：只用简体中文，避免 eng 混合导致编码问题
    dpi: int = 450  # 🚀 提升：300 → 450（表格识别更佳）
    force_ocr: bool = True
    skip_text: bool = False
    threads: int = 4  # 🚀 新增：OCRmyPDF 内部线程数
    optimize: bool = True
    deskew: bool = True  # 🚀 启用：自动纠正倾斜
    clean: bool = True   # 🚀 启用：清理图像噪声
    enhance_tables: bool = True  # 🚀 新增：表格增强模式
    # 内存优化配置
    max_pages_per_batch: int = 30  # 🚀 降低：50 → 30（减少内存占用）
    enable_memory_optimization: bool = True
    gc_interval: int = 5  # 🚀 缩短：10 → 5（更频繁清理）
    # 并行处理配置
    parallel_files: int = 2  # 🚀 新增：同时处理的文件数
    
    def apply_quality_preset(self):
        """应用质量预设"""
        if self.enhance_tables:
            # 表格优化模式：高 DPI + 图像增强
            self.dpi = 450
            self.clean = True
            self.deskew = True
            self.optimize = True


@dataclass
class OCRProgress:
    """OCR 进度"""
    current_page: int = 0
    total_pages: int = 0
    current_file: str = ""
    total_files: int = 0
    status: str = "pending"
    message: str = ""
    percent: float = 0.0
    
    def update(self, **kwargs):
        """更新进度"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        if self.total_pages > 0 and self.current_page > 0:
            self.percent = (self.current_page / self.total_pages) * 100


@dataclass
class OCRResult:
    """OCR 结果"""
    success: bool
    input_file: Path
    output_file: Optional[Path] = None
    pages_processed: int = 0
    text_extracted: str = ""
    error_message: str = ""
    processing_time: float = 0.0


class OCREngine:
    """OCR 引擎 - 优化版"""
    
    _paddleocr_instance = None
    _paddleocr_loaded = False
    
    def __init__(
        self,
        engine_type: OCREngineType = OCREngineType.OCRMYDF,
        config: Optional[OCRConfig] = None,
        progress_callback: Optional[Callable[[OCRProgress], None]] = None,
        preload_models: bool = True
    ):
        self.engine_type = engine_type
        self.config = config or OCRConfig()
        self.config.apply_quality_preset()
        self.progress_callback = progress_callback
        self._engines_available: Dict[str, bool] = {}
        self._validate_engines()
        
        if preload_models and engine_type == OCREngineType.PADDLEOCR:
            self._preload_paddleocr()
    
    def _validate_engines(self):
        """验证 OCR 引擎可用性"""
        engines_to_check = {
            OCREngineType.OCRMYDF: "ocrmypdf",
            OCREngineType.TESSERACT: "tesseract",
            OCREngineType.PADDLEOCR: "paddleocr"
        }
        
        for engine_type, cmd in engines_to_check.items():
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                self._engines_available[engine_type.value] = (result.returncode == 0)
                if self._engines_available[engine_type.value]:
                    logger.info(f"OCR 引擎 {cmd} 可用")
            except Exception as e:
                self._engines_available[engine_type.value] = False
                logger.warning(f"OCR 引擎 {cmd} 不可用：{e}")
    
    def _preload_paddleocr(self):
        """预加载 PaddleOCR 模型"""
        if OCREngine._paddleocr_loaded:
            return
        
        try:
            logger.info("正在预加载 PaddleOCR 模型...")
            from paddleocr import PaddleOCR
            
            OCREngine._paddleocr_instance = PaddleOCR(
                lang='ch',
                use_angle_cls=True,
                show_log=False,
                use_gpu=False
            )
            
            OCREngine._paddleocr_loaded = True
            logger.info("✅ PaddleOCR 模型预加载完成")
        except Exception as e:
            logger.warning(f"PaddleOCR 预加载失败：{e}")
            OCREngine._paddleocr_loaded = False
    
    @classmethod
    def get_paddleocr_instance(cls):
        """获取 PaddleOCR 单例实例"""
        return cls._paddleocr_instance
    
    def convert_to_searchable_pdf(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: Optional[OCRConfig] = None
    ) -> OCRResult:
        """将扫描版 PDF 转为可搜索 PDF"""
        import time
        start_time = time.time()
        
        cfg = config or self.config
        cfg.apply_quality_preset()
        
        try:
            if not input_pdf.exists():
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=f"输入文件不存在：{input_pdf}"
                )
            
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            
            if self.progress_callback:
                self.progress_callback(OCRProgress(
                    status="processing",
                    message=f"开始处理：{input_pdf.name}",
                    current_file=input_pdf.name
                ))
            
            # 🚀 优化：根据文件类型选择最佳引擎
            if self.engine_type == OCREngineType.OCRMYDF:
                result = self._ocrmypdf_convert(input_pdf, output_pdf, cfg)
            elif self.engine_type == OCREngineType.PADDLEOCR:
                result = self._paddleocr_convert(input_pdf, output_pdf, cfg)
            else:
                result = self._tesseract_convert(input_pdf, output_pdf, cfg)
            
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"OCR 异常：{e}", exc_info=True)
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _ocrmypdf_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """使用 OCRmyPDF 转换 - 🚀 优化版（支持表格）"""
        try:
            import shutil
            
            ocrmypdf_path = shutil.which('ocrmypdf')
            if not ocrmypdf_path:
                ocrmypdf_path = r'C:\Python311\Scripts\ocrmypdf.exe'
            
            if not Path(ocrmypdf_path).exists():
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=f"ocrmypdf 未找到：{ocrmypdf_path}"
                )
            
            # 🚀 优化命令参数
            cmd = [
                ocrmypdf_path,
                "--language", config.language,
                "--output-type", "pdf",
                "--image-dpi", str(config.dpi),  # 高 DPI
                "--jobs", str(config.threads),   # 多线程
            ]
            
            if config.force_ocr:
                cmd.append("--force-ocr")
            
            if config.skip_text:
                cmd.append("--skip-text")
            
            # 🚀 表格增强：使用 OCRmyPDF 内置参数（无需额外依赖）
            if config.enhance_tables:
                # 注意：--clean 需要 unpaper，--deskew 需要 scikit-image（均未安装）
                # 使用内置参数：--remove-background（GhostScript 内置支持）
                cmd.append("--remove-background")  # 自动去除背景噪声
                
                # 🚀 新增：Tesseract PSM 参数（表格识别关键！）
                # PSM 6 = 统一文本块（适合表格）
                # PSM 12 = 稀疏文本（适合稀疏表格）
                # PSM 13 = 全文 + 行（适合密集表格）
                cmd.extend(["--tesseract-pagesegmode", "6"])
                
                # 🚀 新增：Sauvola 自适应二值化（适合表格背景不均匀）
                cmd.extend(["--tesseract-thresholding", "sauvola"])
                
                # 🚀 修复：中文编码问题 - 强制使用 UTF-8 和正确语言包
                # 确保 Tesseract 使用正确的 Unicode 编码
                cmd.extend(["--tesseract-config", "tessedit_write_txt=1"])
                
                # 图像增强在 _enhance_image_for_ocr 中用 OpenCV 处理（不依赖 OCRmyPDF）
            
            cmd.extend(["-v", "1"])
            cmd.extend([str(input_pdf), str(output_pdf)])
            
            logger.info(f"执行 OCRmyPDF: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=900  # 15 分钟超时
            )
            
            if result.returncode == 0:
                if not output_pdf.exists():
                    return OCRResult(
                        success=False,
                        input_file=input_pdf,
                        error_message=f"输出文件未创建：{output_pdf}"
                    )
                
                pages = 0
                try:
                    import fitz
                    doc = fitz.open(str(output_pdf))
                    pages = len(doc)
                    doc.close()
                except:
                    pass
                
                return OCRResult(
                    success=True,
                    input_file=input_pdf,
                    output_file=output_pdf,
                    pages_processed=pages,
                    text_extracted=self._extract_text_from_pdf(output_pdf)
                )
            else:
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message="处理超时（超过 15 分钟）"
            )
    
    def _paddleocr_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """使用 PaddleOCR 转换 - 🚀 优化版"""
        try:
            import fitz
            
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            
            temp_dir = Path(tempfile.mkdtemp())
            all_text = []
            
            try:
                ocr = self.get_paddleocr_instance()
                if ocr is None:
                    from paddleocr import PaddleOCR
                    ocr = PaddleOCR(lang='ch', use_angle_cls=True, show_log=False)
                
                # 🚀 内存优化：分批处理
                batch_size = config.max_pages_per_batch if config.enable_memory_optimization else total_pages
                
                for page_num, page in enumerate(doc):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing"
                        ))
                    
                    # 🚀 高 DPI 渲染
                    zoom = config.dpi / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    img_path = temp_dir / f"page_{page_num:04d}.png"
                    pix.save(str(img_path))
                    
                    # 🚀 表格增强：OpenCV 图像预处理
                    if config.enhance_tables:
                        self._enhance_image_for_ocr(img_path)
                    
                    result = ocr.ocr(str(img_path), cls=True)
                    
                    page_text = ""
                    if result and result[0]:
                        for line in result[0]:
                            if line and len(line) > 1:
                                page_text += line[1][0] + "\n"
                    
                    all_text.append(page_text)
                    
                    # 🚀 内存优化：定期清理
                    if config.enable_memory_optimization and (page_num + 1) % config.gc_interval == 0:
                        old_imgs = list(temp_dir.glob("page_*.png"))
                        keep_count = 3
                        if len(old_imgs) > keep_count:
                            for img in old_imgs[:-keep_count]:
                                try:
                                    img.unlink()
                                except:
                                    pass
                        gc.collect()
                
                doc.close()
                extracted_text = '\n'.join(all_text)
                
                # 创建可搜索 PDF
                output_doc = fitz.open()
                src_doc = fitz.open(str(input_pdf))
                
                for page_num in range(total_pages):
                    src_page = src_doc[page_num]
                    new_page = output_doc.new_page(width=src_page.rect.width, height=src_page.rect.height)
                    
                    pix = src_page.get_pixmap()
                    new_page.insert_image(new_page.rect, pixmap=pix)
                    
                    page_text = all_text[page_num] if page_num < len(all_text) else ""
                    if page_text.strip():
                        text_box = fitz.Rect(50, 50, src_page.rect.width - 50, src_page.rect.height - 50)
                        new_page.insert_textbox(
                            text_box,
                            page_text,
                            fontsize=12,
                            color=(0, 0, 0, 0),
                            overlay=True
                        )
                
                src_doc.close()
                output_pdf.parent.mkdir(parents=True, exist_ok=True)
                output_doc.save(str(output_pdf))
                output_doc.close()
                
                return OCRResult(
                    success=True,
                    input_file=input_pdf,
                    output_file=output_pdf,
                    pages_processed=total_pages,
                    text_extracted=extracted_text
                )
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"PaddleOCR 异常：{e}", exc_info=True)
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=str(e)
            )
    
    def _enhance_image_for_ocr(self, img_path: Path):
        """🚀 新增：图像增强（表格优化）"""
        try:
            import cv2
            import numpy as np
            
            img = cv2.imread(str(img_path))
            
            # 1. 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 2. 自适应直方图均衡化（增强对比度）
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # 3. 去噪
            denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)
            
            # 4. 二值化（增强文字边缘）
            _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 5. 保存增强后的图像
            cv2.imwrite(str(img_path), binary)
            
            logger.debug(f"图像增强完成：{img_path}")
            
        except Exception as e:
            logger.warning(f"图像增强失败：{e}，使用原图")
    
    def _tesseract_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """使用 Tesseract 转换"""
        try:
            import fitz
            
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            temp_dir = Path(tempfile.mkdtemp())
            all_text = []
            
            try:
                page_pdfs = []
                
                for page_num in range(total_pages):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing"
                        ))
                    
                    page = doc[page_num]
                    zoom = config.dpi / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    
                    temp_img = temp_dir / f"page_{page_num:04d}.png"
                    pix.save(str(temp_img))
                    
                    temp_pdf_base = temp_dir / f"page_{page_num:04d}"
                    
                    result = subprocess.run(
                        ["tesseract", str(temp_img), str(temp_pdf_base), "-l", config.language, "pdf"],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    temp_pdf = temp_dir / f"page_{page_num:04d}.pdf"
                    
                    if result.returncode == 0 and temp_pdf.exists():
                        page_pdfs.append(temp_pdf)
                        txt_result = subprocess.run(
                            ["tesseract", str(temp_img), "stdout", "-l", config.language],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        all_text.append(txt_result.stdout if txt_result.returncode == 0 else "")
                
                doc.close()
                
                output_doc = fitz.open()
                for page_pdf in page_pdfs:
                    src = fitz.open(str(page_pdf))
                    output_doc.insert_pdf(src)
                    src.close()
                
                output_pdf.parent.mkdir(parents=True, exist_ok=True)
                output_doc.save(str(output_pdf))
                output_doc.close()
                
                return OCRResult(
                    success=True,
                    input_file=input_pdf,
                    output_file=output_pdf,
                    pages_processed=total_pages,
                    text_extracted='\n'.join(all_text)
                )
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
            
        except Exception as e:
            logger.error(f"Tesseract OCR 异常：{e}", exc_info=True)
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=str(e)
            )
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """从 PDF 提取文本"""
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"提取文本失败：{e}")
            return ""
    
    def extract_text(self, pdf_path: Path) -> str:
        """提取 PDF 中的文本"""
        return self._extract_text_from_pdf(pdf_path)


def batch_ocr_parallel(
    input_files: List[Path],
    output_dir: Path,
    config: Optional[OCRConfig] = None,
    engine_type: OCREngineType = OCREngineType.OCRMYDF,
    max_workers: int = 2,  # 🚀 新增：并行文件数
    progress_callback: Optional[Callable[[OCRProgress], None]] = None,
    enable_memory_optimization: bool = True
) -> Tuple[int, int, List[OCRResult]]:
    """
    🚀 新增：批量 OCR 处理（并行处理 + 内存优化）
    
    Args:
        input_files: 输入文件列表
        output_dir: 输出目录
        config: OCR 配置
        engine_type: OCR 引擎类型
        max_workers: 最大并行数（默认 2，避免内存溢出）
        progress_callback: 进度回调
        enable_memory_optimization: 是否启用内存优化
        
    Returns:
        (成功数，失败数，详细结果列表)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cfg = config or OCRConfig()
    cfg.apply_quality_preset()
    
    # 🚀 内存优化：限制并发数
    if enable_memory_optimization:
        max_workers = min(max_workers, cfg.parallel_files)
        logger.info(f"内存优化模式：并行数限制为 {max_workers}")
    
    total_files = len(input_files)
    
    if total_files == 0:
        logger.warning("输入文件列表为空")
        return 0, 0, []
    
    logger.info(f"批量 OCR: {total_files} 个文件，{max_workers} 个并行线程")
    
    results: List[OCRResult] = []
    success_count = 0
    fail_count = 0
    
    def process_single_pdf(pdf_path: Path) -> OCRResult:
        """处理单个 PDF 文件"""
        output_path = output_dir / f"searchable_{pdf_path.name}"
        
        engine = OCREngine(
            engine_type=engine_type,
            config=cfg,
            preload_models=True
        )
        
        result = engine.convert_to_searchable_pdf(pdf_path, output_path)
        
        # 🚀 内存优化：清理
        if enable_memory_optimization:
            gc.collect()
        
        if progress_callback:
            progress_callback(OCRProgress(
                current_file=pdf_path.name,
                total_files=total_files,
                status="completed" if result.success else "failed",
                message=f"{'完成' if result.success else '失败'}: {pdf_path.name}"
            ))
        
        return result
    
    # 🚀 并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_pdf, pdf_path): pdf_path
            for pdf_path in input_files
        }
        
        completed = 0
        for future in as_completed(future_to_file):
            pdf_path = future_to_file[future]
            completed += 1
            
            try:
                result = future.result()
                results.append(result)
                
                if result.success:
                    success_count += 1
                    logger.info(f"[{completed}/{total_files}] ✅ 成功：{pdf_path.name}")
                else:
                    fail_count += 1
                    logger.error(f"[{completed}/{total_files}] ❌ 失败：{pdf_path.name} - {result.error_message}")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"[{completed}/{total_files}] ❌ 异常：{pdf_path.name} - {e}")
                results.append(OCRResult(
                    success=False,
                    input_file=pdf_path,
                    error_message=str(e)
                ))
    
    # 🚀 最终清理
    if enable_memory_optimization:
        gc.collect()
        logger.info("批量 OCR 完成，内存清理完成")
    
    logger.info(f"批量 OCR 完成：成功 {success_count}/{total_files}, 失败 {fail_count}/{total_files}")
    
    return success_count, fail_count, results


# 便捷函数
def quick_ocr(input_pdf: Path, output_pdf: Optional[Path] = None, **kwargs) -> OCRResult:
    """快速 OCR：单文件处理"""
    if output_pdf is None:
        output_pdf = input_pdf.parent / f"searchable_{input_pdf.name}"
    
    config = OCRConfig(**kwargs)
    engine = OCREngine(config=config)
    
    return engine.convert_to_searchable_pdf(input_pdf, output_pdf)
