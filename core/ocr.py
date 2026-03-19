"""
OCR 识别模块 - 优化版
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审
📊 赤影【市场】转技术优化

功能：
1. OCRmyPDF 和 Tesseract 引擎优化
2. PDF 文本层添加（扫描 PDF 转可搜索 PDF）
3. 批量 OCR 处理（多线程加速）
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

logger = logging.getLogger(__name__)


class OCREngineType(Enum):
    """OCR 引擎类型"""
    OCRMYDF = "ocrmypdf"
    TESSERACT = "tesseract"
    PADDLEOCR = "paddleocr"


class OCRQuality(Enum):
    """OCR 质量预设"""
    FAST = "fast"           # 快速模式，低 DPI
    STANDARD = "standard"   # 标准模式
    HIGH = "high"          # 高质量，高 DPI
    BEST = "best"          # 最佳质量，超高 DPI


@dataclass
class OCRConfig:
    """OCR 配置"""
    language: str = "chi_sim+eng"
    dpi: int = 300
    force_ocr: bool = True
    skip_text: bool = False
    quality: OCRQuality = OCRQuality.STANDARD
    threads: int = 1  # OCRmyPDF 内部线程数
    optimize: bool = True  # 优化输出 PDF
    deskew: bool = False  # 自动纠正倾斜
    clean: bool = False   # 清理图像噪声
    
    def apply_quality_preset(self):
        """应用质量预设"""
        if self.quality == OCRQuality.FAST:
            self.dpi = 150
            self.optimize = False
        elif self.quality == OCRQuality.STANDARD:
            self.dpi = 300
            self.optimize = True
        elif self.quality == OCRQuality.HIGH:
            self.dpi = 450
            self.optimize = True
            self.clean = True
        elif self.quality == OCRQuality.BEST:
            self.dpi = 600
            self.optimize = True
            self.clean = True
            self.deskew = True


@dataclass
class OCRProgress:
    """OCR 进度"""
    current_page: int = 0
    total_pages: int = 0
    current_file: str = ""
    total_files: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    message: str = ""
    percent: float = 0.0
    
    def update(self, **kwargs):
        """更新进度"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 自动计算百分比
        if self.total_pages > 0 and self.current_page > 0:
            self.percent = (self.current_page / self.total_pages) * 100
        elif self.total_files > 0 and self.current_file:
            self.percent = (self.current_page / self.total_files) * 100


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


class OCRError(Exception):
    """OCR 异常"""
    pass


class OCREngine:
    """OCR 引擎 - 支持 OCRmyPDF 和 Tesseract"""
    
    def __init__(
        self,
        engine_type: OCREngineType = OCREngineType.OCRMYDF,
        config: Optional[OCRConfig] = None,
        progress_callback: Optional[Callable[[OCRProgress], None]] = None
    ):
        """
        Args:
            engine_type: OCR 引擎类型
            config: OCR 配置
            progress_callback: 进度回调函数
        """
        self.engine_type = engine_type
        self.config = config or OCRConfig()
        self.config.apply_quality_preset()
        self.progress_callback = progress_callback
        self._engines_available: Dict[str, bool] = {}
        self._validate_engines()
    
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
                    logger.info(f"OCR 引擎 {cmd} 可用：{result.stdout.strip().split(chr(10))[0]}")
                else:
                    logger.warning(f"OCR 引擎 {cmd} 返回错误码：{result.returncode}")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                self._engines_available[engine_type.value] = False
                logger.warning(f"OCR 引擎 {cmd} 不可用：{e}")
    
    def is_engine_available(self) -> bool:
        """检查当前选择的引擎是否可用"""
        return self._engines_available.get(self.engine_type.value, False)
    
    def get_available_engine(self) -> Optional[OCREngineType]:
        """获取第一个可用的引擎"""
        for engine_type in [OCREngineType.OCRMYDF, OCREngineType.TESSERACT, OCREngineType.PADDLEOCR]:
            if self._engines_available.get(engine_type.value, False):
                return engine_type
        return None
    
    def convert_to_searchable_pdf(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: Optional[OCRConfig] = None
    ) -> OCRResult:
        """
        将扫描版 PDF 转为可搜索 PDF（添加文本层）
        
        Args:
            input_pdf: 输入 PDF 路径
            output_pdf: 输出 PDF 路径
            config: OCR 配置（可选，覆盖默认配置）
            
        Returns:
            OCRResult: OCR 结果
        """
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
            
            # 确保输出目录存在
            output_pdf.parent.mkdir(parents=True, exist_ok=True)
            
            if self.progress_callback:
                self.progress_callback(OCRProgress(
                    status="processing",
                    message=f"开始处理：{input_pdf.name}",
                    current_file=input_pdf.name
                ))
            
            if self.engine_type == OCREngineType.OCRMYDF:
                result = self._ocrmypdf_convert(input_pdf, output_pdf, cfg)
            elif self.engine_type == OCREngineType.TESSERACT:
                result = self._tesseract_convert(input_pdf, output_pdf, cfg)
            elif self.engine_type == OCREngineType.PADDLEOCR:
                result = self._paddleocr_convert(input_pdf, output_pdf, cfg)
            else:
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=f"不支持的 OCR 引擎：{self.engine_type}"
                )
            
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"OCR 异常：{e}", exc_info=True)
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=str(e),
                processing_time = time.time() - start_time
            )
    
    def _ocrmypdf_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """
        使用 OCRmyPDF 转换（推荐）
        OCRmyPDF 会自动添加文本层到 PDF
        """
        try:
            cmd = [
                "ocrmypdf",
                "--language", config.language,
                "--output-type", "pdf",
                "--dpi", str(config.dpi),
                "--jobs", str(config.threads),
            ]
            
            # 添加选项
            if config.force_ocr:
                cmd.append("--force-ocr")
            
            if config.skip_text:
                cmd.append("--skip-text")
            
            if config.optimize:
                cmd.extend(["--optimize", "3"])
            
            if config.deskew:
                cmd.append("--deskew")
            
            if config.clean:
                cmd.append("--clean")
            
            # 详细输出用于进度跟踪
            cmd.append("--verbose")
            
            cmd.extend([str(input_pdf), str(output_pdf)])
            
            logger.info(f"执行 OCRmyPDF: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )
            
            if result.returncode == 0:
                logger.info(f"OCRmyPDF 成功：{output_pdf}")
                
                # 提取页数的逻辑
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
                logger.error(f"OCRmyPDF 失败：{result.stderr}")
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=result.stderr
                )
                
        except subprocess.TimeoutExpired:
            logger.error("OCRmyPDF 超时")
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message="处理超时（超过 10 分钟）"
            )
    
    def _tesseract_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """
        使用 Tesseract 转换
        需要先将 PDF 转为图片，OCR 后添加文本层
        """
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io
            
            logger.info(f"使用 Tesseract OCR: {input_pdf}")
            
            # 打开 PDF
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            
            if self.progress_callback:
                self.progress_callback(OCRProgress(
                    total_pages=total_pages,
                    status="processing",
                    message=f"Tesseract OCR: {total_pages} 页"
                ))
            
            temp_dir = Path(tempfile.mkdtemp())
            all_text = []
            
            try:
                for page_num, page in enumerate(doc):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing",
                            message=f"处理第 {page_num + 1}/{total_pages} 页"
                        ))
                    
                    # 渲染页面为图片
                    zoom = config.dpi / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("png")
                    
                    # Tesseract OCR（输出 hOCR 格式）
                    img_path = temp_dir / f"page_{page_num:04d}.png"
                    img_path.write_bytes(img_data)
                    
                    hocr_path = temp_dir / f"page_{page_num:04d}.hocr"
                    
                    try:
                        result = subprocess.run(
                            [
                                "tesseract",
                                str(img_path),
                                str(hocr_path.with_suffix('')),
                                "-l", config.language.replace("+", "+"),
                                "--psm", "3",  # 自动页面分割
                                "hocr"  # 输出 hOCR 格式
                            ],
                            capture_output=True,
                            text=True,
                            timeout=120
                        )
                        
                        if result.returncode == 0:
                            # 读取 hOCR 文件提取文本
                            if hocr_path.exists():
                                hocr_content = hocr_path.read_text(encoding='utf-8')
                                # 简单提取文本（生产环境应用更完善的 hOCR 解析）
                                import re
                                text_matches = re.findall(r'x_text">([^<]+)', hocr_content)
                                page_text = ' '.join(text_matches)
                                all_text.append(page_text)
                            else:
                                # 回退到普通输出
                                txt_path = temp_dir / f"page_{page_num:04d}.txt"
                                if txt_path.exists():
                                    all_text.append(txt_path.read_text(encoding='utf-8'))
                        else:
                            logger.warning(f"第 {page_num + 1} 页 OCR 失败：{result.stderr}")
                            all_text.append("")
                            
                    except subprocess.TimeoutExpired:
                        logger.warning(f"第 {page_num + 1} 页 OCR 超时")
                        all_text.append("")
                
                doc.close()
                
                # 使用 OCRmyPDF 的 pdf-renderer 或 hocrpdf 创建可搜索 PDF
                # 简化方案：直接调用 ocrmypdf 处理
                logger.info("Tesseract OCR 完成，使用 OCRmyPDF 创建可搜索 PDF")
                
                # 实际上，纯 Tesseract 流程复杂，建议回退到 OCRmyPDF
                return self._ocrmypdf_convert(input_pdf, output_pdf, config)
                
            finally:
                # 清理临时文件
                shutil.rmtree(temp_dir, ignore_errors=True)
            
        except ImportError as e:
            logger.error(f"缺少依赖：{e}")
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=f"缺少依赖：{e}"
            )
        except Exception as e:
            logger.error(f"Tesseract OCR 异常：{e}", exc_info=True)
            return OCRResult(
                success=False,
                input_file=input_pdf,
                error_message=str(e)
            )
    
    def _paddleocr_convert(
        self,
        input_pdf: Path,
        output_pdf: Path,
        config: OCRConfig
    ) -> OCRResult:
        """使用 PaddleOCR 转换"""
        try:
            logger.info(f"使用 PaddleOCR: {input_pdf}")
            
            # PaddleOCR 更适合图片，PDF 需要先转图片
            import fitz
            
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            
            temp_dir = Path(tempfile.mkdtemp())
            all_text = []
            
            try:
                for page_num, page in enumerate(doc):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing"
                        ))
                    
                    # 渲染为图片
                    zoom = config.dpi / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    img_path = temp_dir / f"page_{page_num:04d}.png"
                    pix.save(str(img_path))
                    
                    # PaddleOCR
                    from paddleocr import PaddleOCR
                    ocr = PaddleOCR(
                        lang='ch',
                        use_angle_cls=True,
                        show_log=False
                    )
                    
                    result = ocr.ocr(str(img_path), cls=True)
                    
                    page_text = ""
                    if result and result[0]:
                        for line in result[0]:
                            if line and len(line) > 1:
                                page_text += line[1][0] + "\n"
                    
                    all_text.append(page_text)
                
                doc.close()
                
                # 保存文本
                extracted_text = '\n'.join(all_text)
                
                # PaddleOCR 不直接支持输出可搜索 PDF，需要额外处理
                # 建议回退到 OCRmyPDF
                logger.info("PaddleOCR 文本提取完成，使用 OCRmyPDF 创建可搜索 PDF")
                return self._ocrmypdf_convert(input_pdf, output_pdf, config)
                
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"PaddleOCR 异常：{e}", exc_info=True)
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
        """
        提取 PDF 中的文本（直接提取，不进行 OCR）
        
        Args:
            pdf_path: PDF 路径
            
        Returns:
            str: 提取的文本
        """
        return self._extract_text_from_pdf(pdf_path)
    
    def has_text_layer(self, pdf_path: Path) -> bool:
        """
        检查 PDF 是否已有文本层
        
        Args:
            pdf_path: PDF 路径
            
        Returns:
            bool: 是否有文本层
        """
        try:
            import fitz
            doc = fitz.open(str(pdf_path))
            for page in doc:
                if page.get_text().strip():
                    doc.close()
                    return True
            doc.close()
            return False
        except Exception as e:
            logger.error(f"检查文本层失败：{e}")
            return False


def batch_ocr(
    input_dir: Path,
    output_dir: Path,
    config: Optional[OCRConfig] = None,
    engine_type: OCREngineType = OCREngineType.OCRMYDF,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[OCRProgress], None]] = None
) -> Tuple[int, int, List[OCRResult]]:
    """
    批量 OCR 处理（多线程加速）
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        config: OCR 配置
        engine_type: OCR 引擎类型
        max_workers: 最大线程数
        progress_callback: 进度回调
        
    Returns:
        (成功数，失败数，详细结果列表)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cfg = config or OCRConfig()
    cfg.apply_quality_preset()
    
    # 查找所有 PDF 文件
    pdf_files = list(input_dir.glob("*.pdf"))
    total_files = len(pdf_files)
    
    if total_files == 0:
        logger.warning(f"输入目录没有找到 PDF 文件：{input_dir}")
        return 0, 0, []
    
    logger.info(f"批量 OCR: {total_files} 个文件，{max_workers} 个线程")
    
    results: List[OCRResult] = []
    success_count = 0
    fail_count = 0
    
    def process_single_pdf(pdf_path: Path) -> OCRResult:
        """处理单个 PDF 文件"""
        output_path = output_dir / f"searchable_{pdf_path.name}"
        
        engine = OCREngine(
            engine_type=engine_type,
            config=cfg
        )
        
        result = engine.convert_to_searchable_pdf(pdf_path, output_path)
        
        if progress_callback:
            progress_callback(OCRProgress(
                current_file=pdf_path.name,
                total_files=total_files,
                status=result.status if hasattr(result, 'status') else ("completed" if result.success else "failed"),
                message=f"{'完成' if result.success else '失败'}: {pdf_path.name}"
            ))
        
        return result
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(process_single_pdf, pdf_path): pdf_path
            for pdf_path in pdf_files
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
                    logger.info(f"[{completed}/{total_files}] 成功：{pdf_path.name}")
                else:
                    fail_count += 1
                    logger.error(f"[{completed}/{total_files}] 失败：{pdf_path.name} - {result.error_message}")
                    
            except Exception as e:
                fail_count += 1
                logger.error(f"[{completed}/{total_files}] 异常：{pdf_path.name} - {e}")
                results.append(OCRResult(
                    success=False,
                    input_file=pdf_path,
                    error_message=str(e)
                ))
    
    logger.info(f"批量 OCR 完成：成功 {success_count}/{total_files}, 失败 {fail_count}/{total_files}")
    
    return success_count, fail_count, results


def add_text_layer(
    input_pdf: Path,
    output_pdf: Path,
    language: str = "chi_sim+eng",
    dpi: int = 300,
    force_ocr: bool = True
) -> bool:
    """
    便捷函数：为扫描 PDF 添加文本层
    
    Args:
        input_pdf: 输入 PDF
        output_pdf: 输出 PDF
        language: OCR 语言
        dpi: OCR 分辨率
        force_ocr: 是否强制 OCR
        
    Returns:
        bool: 是否成功
    """
    config = OCRConfig(
        language=language,
        dpi=dpi,
        force_ocr=force_ocr
    )
    
    engine = OCREngine(
        engine_type=OCREngineType.OCRMYDF,
        config=config
    )
    
    result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
    return result.success


# 模块级便捷函数
def quick_ocr(input_pdf: Path, output_pdf: Optional[Path] = None, **kwargs) -> OCRResult:
    """
    快速 OCR：单文件处理
    
    Args:
        input_pdf: 输入 PDF
        output_pdf: 输出 PDF（可选，默认在同目录创建 searchable_xxx.pdf）
        **kwargs: OCRConfig 参数
        
    Returns:
        OCRResult: OCR 结果
    """
    if output_pdf is None:
        output_pdf = input_pdf.parent / f"searchable_{input_pdf.name}"
    
    config = OCRConfig(**kwargs)
    engine = OCREngine(config=config)
    
    return engine.convert_to_searchable_pdf(input_pdf, output_pdf)
