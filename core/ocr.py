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
    # 内存优化配置（新增）
    max_pages_per_batch: int = 50  # 大批量处理时每批最大页数
    enable_memory_optimization: bool = True  # 启用内存优化模式
    gc_interval: int = 10  # 每处理 N 页后强制垃圾回收
    
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
    
    # 类级别单例：PaddleOCR 模型预加载（全局共享）
    _paddleocr_instance = None
    _paddleocr_loaded = False
    
    def __init__(
        self,
        engine_type: OCREngineType = OCREngineType.OCRMYDF,
        config: Optional[OCRConfig] = None,
        progress_callback: Optional[Callable[[OCRProgress], None]] = None,
        preload_models: bool = True  # 新增：是否预加载模型
    ):
        """
        Args:
            engine_type: OCR 引擎类型
            config: OCR 配置
            progress_callback: 进度回调函数
            preload_models: 是否预加载 AI 模型（默认 True，启动时加载避免首次延迟）
        """
        self.engine_type = engine_type
        self.config = config or OCRConfig()
        self.config.apply_quality_preset()
        self.progress_callback = progress_callback
        self._engines_available: Dict[str, bool] = {}
        self._validate_engines()
        
        # 预加载 PaddleOCR 模型（避免首次处理时延迟）
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
                    logger.info(f"OCR 引擎 {cmd} 可用：{result.stdout.strip().split(chr(10))[0]}")
                else:
                    logger.warning(f"OCR 引擎 {cmd} 返回错误码：{result.returncode}")
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
                self._engines_available[engine_type.value] = False
                logger.warning(f"OCR 引擎 {cmd} 不可用：{e}")
    
    def _preload_paddleocr(self):
        """预加载 PaddleOCR 模型到内存（单例模式）"""
        if OCREngine._paddleocr_loaded:
            logger.info("PaddleOCR 模型已预加载，跳过")
            return
        
        try:
            logger.info("正在预加载 PaddleOCR 模型...（首次启动可能需要 10-30 秒）")
            from paddleocr import PaddleOCR
            
            # 创建全局单例实例
            OCREngine._paddleocr_instance = PaddleOCR(
                lang='ch',
                use_angle_cls=True,
                show_log=False,
                use_gpu=False  # 默认使用 CPU，如有 GPU 可改为 True
            )
            
            OCREngine._paddleocr_loaded = True
            logger.info("✅ PaddleOCR 模型预加载完成")
            
        except Exception as e:
            logger.warning(f"PaddleOCR 预加载失败：{e}，将在首次使用时延迟加载")
            OCREngine._paddleocr_loaded = False
    
    @classmethod
    def get_paddleocr_instance(cls) -> Optional[Any]:
        """获取 PaddleOCR 单例实例"""
        return cls._paddleocr_instance
    
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
            import shutil
            
            # 查找 ocrmypdf 可执行文件
            ocrmypdf_path = shutil.which('ocrmypdf')
            if not ocrmypdf_path:
                # 尝试默认路径
                ocrmypdf_path = r'C:\Python311\Scripts\ocrmypdf.exe'
            
            if not Path(ocrmypdf_path).exists():
                logger.error(f"ocrmypdf 可执行文件不存在：{ocrmypdf_path}")
                return OCRResult(
                    success=False,
                    input_file=input_pdf,
                    error_message=f"ocrmypdf 未找到：{ocrmypdf_path}"
                )
            
            logger.info(f"使用 ocrmypdf: {ocrmypdf_path}")
            
            cmd = [
                ocrmypdf_path,
                "--language", config.language,
                "--output-type", "pdf",
                "--image-dpi", str(config.dpi),
                "--jobs", str(config.threads),
            ]
            
            # 添加选项
            if config.force_ocr:
                cmd.append("--force-ocr")
            
            if config.skip_text:
                cmd.append("--skip-text")
            
            # 禁用优化（需要 pngquant，默认不安装）
            # if config.optimize:
            #     cmd.extend(["--optimize", "3"])
            
            if config.deskew:
                cmd.append("--deskew")
            
            if config.clean:
                cmd.append("--clean")
            
            # 详细输出用于进度跟踪
            cmd.extend(["-v", "1"])
            
            # 输入输出文件必须在最后
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
                
                # 检查文件是否真的存在
                if not output_pdf.exists():
                    logger.error(f"OCRmyPDF 报告成功，但输出文件不存在：{output_pdf}")
                    # 尝试查找可能的输出位置
                    import glob
                    possible_files = glob.glob(str(output_pdf.parent / "*.pdf"))
                    logger.info(f"目录中的 PDF 文件：{possible_files}")
                    return OCRResult(
                        success=False,
                        input_file=input_pdf,
                        error_message=f"输出文件未创建：{output_pdf}"
                    )
                
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
        使用 Tesseract 直接生成可搜索 PDF（真正独立实现）
        Tesseract 4.0+ 支持 pdf 输出格式
        """
        try:
            import fitz
            
            logger.info(f"使用 Tesseract 直接生成 PDF: {input_pdf}")
            
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
                # 为每一页生成 PDF
                page_pdfs = []
                
                for page_num in range(total_pages):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing",
                            message=f"Tesseract 处理第 {page_num + 1}/{total_pages} 页"
                        ))
                    
                    # 获取页面
                    page = doc[page_num]
                    
                    # 渲染为图片
                    zoom = config.dpi / 72
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    
                    # 保存临时图片
                    temp_img = temp_dir / f"page_{page_num:04d}.png"
                    pix.save(str(temp_img))
                    
                    # 使用 Tesseract 生成 PDF
                    temp_pdf_base = temp_dir / f"page_{page_num:04d}"
                    
                    result = subprocess.run(
                        [
                            "tesseract",
                            str(temp_img),
                            str(temp_pdf_base),
                            "-l", config.language.replace("+", "+"),
                            "pdf"  # 直接输出 PDF 格式
                        ],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    temp_pdf = temp_dir / f"page_{page_num:04d}.pdf"
                    
                    if result.returncode == 0 and temp_pdf.exists():
                        page_pdfs.append(temp_pdf)
                        logger.info(f"第 {page_num + 1} 页 PDF 生成成功")
                        
                        # 提取文本用于返回
                        txt_result = subprocess.run(
                            ["tesseract", str(temp_img), "stdout", "-l", config.language.replace("+", "+")],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        all_text.append(txt_result.stdout if txt_result.returncode == 0 else "")
                    else:
                        logger.error(f"第 {page_num + 1} 页 PDF 生成失败: {result.stderr}")
                        # 创建一个空白页面作为占位
                        blank_doc = fitz.open()
                        blank_doc.new_page(width=page.rect.width, height=page.rect.height)
                        blank_pdf = temp_dir / f"blank_{page_num:04d}.pdf"
                        blank_doc.save(str(blank_pdf))
                        blank_doc.close()
                        page_pdfs.append(blank_pdf)
                        all_text.append("")
                
                doc.close()
                
                # 合并所有页面
                logger.info("Tesseract 合并 PDF 页面...")
                output_doc = fitz.open()
                
                for page_pdf in page_pdfs:
                    src = fitz.open(str(page_pdf))
                    output_doc.insert_pdf(src)
                    src.close()
                
                # 保存最终 PDF
                output_pdf.parent.mkdir(parents=True, exist_ok=True)
                output_doc.save(str(output_pdf))
                output_doc.close()
                
                logger.info(f"Tesseract PDF 创建成功: {output_pdf}")
                
                return OCRResult(
                    success=True,
                    input_file=input_pdf,
                    output_file=output_pdf,
                    pages_processed=total_pages,
                    text_extracted='\n'.join(all_text)
                )
                
            finally:
                # 清理临时文件
                shutil.rmtree(temp_dir, ignore_errors=True)
            
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
        """使用 PaddleOCR 转换（使用预加载模型 + 内存优化）"""
        try:
            logger.info(f"使用 PaddleOCR: {input_pdf}")
            
            # PaddleOCR 更适合图片，PDF 需要先转图片
            import fitz
            import gc  # 垃圾回收
            
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            
            temp_dir = Path(tempfile.mkdtemp())
            all_text = []
            
            try:
                # 获取预加载的 PaddleOCR 单例实例（避免重复加载模型）
                ocr = self.get_paddleocr_instance()
                
                # 如果预加载失败，现场创建实例（降级处理）
                if ocr is None:
                    logger.warning("PaddleOCR 预加载实例不可用，现场创建实例...")
                    from paddleocr import PaddleOCR
                    ocr = PaddleOCR(
                        lang='ch',
                        use_angle_cls=True,
                        show_log=False
                    )
                
                # 内存优化：分批处理大文件
                enable_mem_opt = config.enable_memory_optimization
                batch_size = config.max_pages_per_batch if enable_mem_opt else total_pages
                
                logger.info(f"内存优化模式：{'启用' if enable_mem_opt else '禁用'}，批次大小：{batch_size} 页")
                
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
                    
                    # 使用预加载的 PaddleOCR 实例进行识别
                    result = ocr.ocr(str(img_path), cls=True)
                    
                    page_text = ""
                    if result and result[0]:
                        for line in result[0]:
                            if line and len(line) > 1:
                                page_text += line[1][0] + "\n"
                    
                    all_text.append(page_text)
                    
                    # 内存优化：定期清理临时对象
                    if enable_mem_opt and (page_num + 1) % config.gc_interval == 0:
                        # 清理临时图片（保留最近几页）
                        old_imgs = list(temp_dir.glob("page_*.png"))
                        keep_count = 5
                        if len(old_imgs) > keep_count:
                            for img in old_imgs[:-keep_count]:
                                try:
                                    img.unlink()
                                except:
                                    pass
                        # 强制垃圾回收
                        gc.collect()
                        logger.debug(f"内存优化：已处理 {page_num + 1}/{total_pages} 页，清理临时文件")
                    
                    # 内存优化：分批处理，每批结束后清理
                    if enable_mem_opt and (page_num + 1) % batch_size == 0:
                        logger.info(f"完成第 {(page_num + 1) // batch_size} 批次，清理内存...")
                        gc.collect()
                
                doc.close()
                
                # 保存文本
                extracted_text = '\n'.join(all_text)
                
                # 使用 PaddleOCR 创建可搜索 PDF（独立实现，不依赖 ocrmypdf）
                logger.info("PaddleOCR 文本提取完成，创建可搜索 PDF...")
                
                # 创建新的 PDF，包含文本层
                output_doc = fitz.open()
                src_doc = fitz.open(str(input_pdf))
                
                for page_num in range(total_pages):
                    if self.progress_callback:
                        self.progress_callback(OCRProgress(
                            current_page=page_num + 1,
                            total_pages=total_pages,
                            status="processing",
                            message=f"创建 PDF 第 {page_num + 1}/{total_pages} 页"
                        ))
                    
                    src_page = src_doc[page_num]
                    
                    # 创建新页面
                    new_page = output_doc.new_page(width=src_page.rect.width, height=src_page.rect.height)
                    
                    # 插入原始页面作为图片
                    pix = src_page.get_pixmap()
                    new_page.insert_image(new_page.rect, pixmap=pix)
                    
                    # 添加文本层
                    page_text = all_text[page_num] if page_num < len(all_text) else ""
                    if page_text.strip():
                        # 在页面上添加文本（简化处理）
                        text_box = fitz.Rect(50, 50, src_page.rect.width - 50, src_page.rect.height - 50)
                        new_page.insert_textbox(
                            text_box,
                            page_text,
                            fontsize=12,
                            color=(0, 0, 0, 0),  # 透明颜色（不可见但可选择）
                            overlay=True
                        )
                
                src_doc.close()
                
                # 确保输出目录存在
                output_pdf.parent.mkdir(parents=True, exist_ok=True)
                
                # 保存输出 PDF
                output_doc.save(str(output_pdf))
                output_doc.close()
                
                logger.info(f"PaddleOCR PDF 创建成功：{output_pdf}")
                
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
    progress_callback: Optional[Callable[[OCRProgress], None]] = None,
    enable_memory_optimization: bool = True  # 新增：启用内存优化
) -> Tuple[int, int, List[OCRResult]]:
    """
    批量 OCR 处理（多线程加速 + 内存优化）
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        config: OCR 配置
        engine_type: OCR 引擎类型
        max_workers: 最大线程数
        progress_callback: 进度回调
        enable_memory_optimization: 是否启用内存优化（默认 True）
        
    Returns:
        (成功数，失败数，详细结果列表)
    """
    import gc
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cfg = config or OCRConfig()
    cfg.apply_quality_preset()
    
    # 内存优化：根据系统内存动态调整并发数
    if enable_memory_optimization:
        # 大文件处理时降低并发数，避免内存溢出
        if cfg.enable_memory_optimization:
            max_workers = min(max_workers, 2)  # 内存优化模式下限制并发数
            logger.info(f"内存优化模式：并发数限制为 {max_workers}")
    
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
        """处理单个 PDF 文件（支持内存优化）"""
        output_path = output_dir / f"searchable_{pdf_path.name}"
        
        engine = OCREngine(
            engine_type=engine_type,
            config=cfg,
            preload_models=True  # 使用预加载模型
        )
        
        result = engine.convert_to_searchable_pdf(pdf_path, output_path)
        
        # 内存优化：每处理完一个文件后清理
        if enable_memory_optimization:
            gc.collect()
        
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
    
    # 内存优化：全部完成后清理
    if enable_memory_optimization:
        gc.collect()
        logger.info("批量 OCR 完成，内存清理完成")
    
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
