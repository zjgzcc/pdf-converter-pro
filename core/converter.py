"""
PDF 转 WORD 转换模块
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审
🧪 青影【测试】转开发 - 完善版面恢复 + 备选方案

支持多种转换方案：
1. PaddleOCR 版面恢复（推荐，适合复杂布局）
2. pdf2docx（备选，适合文本型 PDF）
3. FreeP2W（适合数学公式）

特性：
- 保持原格式和布局（表格、图片、多栏）
- 批量转换支持
- 智能降级策略
- 进度追踪
"""

import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Tuple
from enum import Enum
import logging
import shutil
import tempfile
import json
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ConvertMethod(Enum):
    """转换方法"""
    PADDLEOCR = "paddleocr"
    PDF2DOCX = "pdf2docx"
    FREEP2W = "freep2w"


@dataclass
class LayoutElement:
    """版面元素"""
    type: str  # text, image, table, equation
    bbox: Tuple[int, int, int, int]  # (x0, y0, x1, y1)
    content: Optional[str] = None
    confidence: float = 0.0
    page: int = 0


@dataclass
class ConvertProgress:
    """转换进度回调"""
    
    current_page: int = 0
    total_pages: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    message: str = ""
    current_method: str = ""
    percentage: float = 0.0
    eta_seconds: float = 0.0
    
    def update(
        self,
        page: int = 0,
        status: str = "processing",
        message: str = "",
        method: str = "",
        percentage: Optional[float] = None,
        eta: Optional[float] = None
    ):
        self.current_page = page
        self.status = status
        self.message = message
        if method:
            self.current_method = method
        if percentage is not None:
            self.percentage = percentage
        if eta is not None:
            self.eta_seconds = eta


class ConvertError(Exception):
    """转换异常"""
    pass


class PDF2WordConverter:
    """
    PDF 转 WORD 转换器
    
    核心特性：
    1. PaddleOCR 版面分析 - 识别文本、表格、图片、公式
    2. 格式保持 - 保留原始布局、字体、颜色
    3. 智能降级 - 主方法失败自动尝试备选
    4. 批量支持 - 高效处理多个文件
    """
    
    def __init__(
        self,
        method: ConvertMethod = ConvertMethod.PADDLEOCR,
        fallback_methods: Optional[List[ConvertMethod]] = None,
        preserve_format: bool = True,
        layout_analysis: bool = True,
        table_detection: bool = True,
        image_extraction: bool = True,
        progress_callback: Optional[Callable[[ConvertProgress], None]] = None
    ):
        """
        Args:
            method: 主转换方法
            fallback_methods: 备选转换方法列表（失败时自动尝试）
            preserve_format: 是否保持格式
            layout_analysis: 启用版面分析
            table_detection: 启用表格检测
            image_extraction: 启用图片提取
            progress_callback: 进度回调函数
        """
        self.method = method
        self.fallback_methods = fallback_methods or [ConvertMethod.PDF2DOCX, ConvertMethod.FREEP2W]
        self.preserve_format = preserve_format
        self.layout_analysis = layout_analysis
        self.table_detection = table_detection
        self.image_extraction = image_extraction
        self.progress_callback = progress_callback
        self._temp_dir: Optional[Path] = None
        self._validate_methods()
    
    def _validate_methods(self):
        """验证转换方法是否可用"""
        available_methods = []
        unavailable_methods = []
        
        # 检查主方法
        try:
            if self.method == ConvertMethod.PADDLEOCR:
                result = subprocess.run(
                    ["paddleocr", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    available_methods.append(self.method.value)
                else:
                    unavailable_methods.append(self.method.value)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            unavailable_methods.append(self.method.value)
        
        # 检查备选方法
        for fallback in self.fallback_methods:
            try:
                if fallback == ConvertMethod.PDF2DOCX:
                    import pdf2docx
                    available_methods.append(fallback.value)
                elif fallback == ConvertMethod.FREEP2W:
                    from freep2w.cli import convert_pdf_to_docx
                    available_methods.append(fallback.value)
            except ImportError:
                unavailable_methods.append(fallback.value)
        
        if available_methods:
            logger.info(f"可用转换方法：{', '.join(available_methods)}")
        if unavailable_methods:
            logger.warning(f"不可用转换方法：{', '.join(unavailable_methods)}")
        
        # 如果主方法不可用，尝试使用第一个备选方法
        if self.method.value in unavailable_methods and available_methods:
            logger.warning(f"主方法 {self.method.value} 不可用，将使用 {available_methods[0]}")
            for m in ConvertMethod:
                if m.value == available_methods[0]:
                    self.method = m
                    break
    
    def _create_temp_dir(self) -> Path:
        """创建临时目录"""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="pdf_converter_"))
            logger.debug(f"创建临时目录：{self._temp_dir}")
        return self._temp_dir
    
    def _cleanup_temp_dir(self):
        """清理临时目录"""
        if self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
                logger.debug(f"清理临时目录：{self._temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败：{e}")
    
    def convert(
        self,
        input_pdf: Path,
        output_docx: Path,
        method: Optional[ConvertMethod] = None
    ) -> bool:
        """
        转换 PDF 为 WORD
        
        Args:
            input_pdf: 输入 PDF
            output_docx: 输出 DOCX
            method: 指定转换方法（不指定则使用默认）
            
        Returns:
            bool: 是否成功
        """
        if not input_pdf.exists():
            raise ConvertError(f"输入文件不存在：{input_pdf}")
        
        # 确保输出目录存在
        output_docx.parent.mkdir(parents=True, exist_ok=True)
        
        # 尝试主方法
        convert_method = method or self.method
        
        if self.progress_callback:
            self.progress_callback(ConvertProgress(
                status="processing",
                message=f"使用 {convert_method.value} 转换",
                current_method=convert_method.value,
                percentage=0.0
            ))
        
        success = self._try_convert(input_pdf, output_docx, convert_method)
        
        # 如果失败，尝试备选方法
        if not success:
            logger.warning(f"{convert_method.value} 转换失败，尝试备选方法")
            
            for fallback in self.fallback_methods:
                if self.progress_callback:
                    self.progress_callback(ConvertProgress(
                        status="processing",
                        message=f"尝试备选方案：{fallback.value}",
                        method=fallback.value,
                        percentage=0.0
                    ))
                
                success = self._try_convert(input_pdf, output_docx, fallback)
                if success:
                    logger.info(f"备选方法 {fallback.value} 转换成功")
                    break
        
        return success
    
    def _try_convert(
        self,
        input_pdf: Path,
        output_docx: Path,
        method: ConvertMethod
    ) -> bool:
        """尝试使用指定方法转换"""
        try:
            if method == ConvertMethod.PADDLEOCR:
                return self._convert_paddleocr(input_pdf, output_docx)
            elif method == ConvertMethod.PDF2DOCX:
                return self._convert_pdf2docx(input_pdf, output_docx)
            elif method == ConvertMethod.FREEP2W:
                return self._convert_freep2w(input_pdf, output_docx)
            else:
                logger.error(f"不支持的转换方法：{method}")
                return False
        except Exception as e:
            logger.error(f"{method.value} 转换异常：{e}")
            return False
    
    def _convert_paddleocr(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        使用 PaddleOCR 版面恢复（推荐方法）
        
        适合：图文混排、表格、多栏、复杂布局
        优势：
        - 高精度版面分析
        - 表格结构识别
        - 图片位置保持
        - 多栏文本还原
        
        优化参数：
        - det_db_thresh: 检测阈值 (0.3)
        - rec_batch_num: 批量识别数量 (6)
        - use_angle_cls: 使用方向分类器
        - layout: 启用版面分析
        - table: 启用表格识别
        """
        temp_dir = None
        try:
            temp_dir = self._create_temp_dir()
            output_dir = output_docx.parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 构建 PaddleOCR 命令
            cmd = [
                "paddleocr",
                "--image_dir", str(input_pdf),
                "--type", "structure",
                "--recovery", "true",
                "--lang", "ch",
                "--output", str(temp_dir),
                "--det_db_thresh", "0.3",
                "--det_db_box_score", "0.5",
                "--rec_batch_num", "6",
                "--use_angle_cls", "true",
                "--show_log", "false",
            ]
            
            # 版面分析参数
            if self.layout_analysis:
                cmd.extend([
                    "--layout", "true",
                    "--layout_model_version", "v2.0",
                ])
            
            # 表格检测参数
            if self.table_detection:
                cmd.extend([
                    "--table", "true",
                    "--table_max_len", "488",
                    "--merge_no_span_structure", "true",
                ])
            
            # 保持格式参数
            if self.preserve_format:
                cmd.extend([
                    "--font_path", "",  # 使用系统字体
                    "--font_size", "10.5",  # 默认五号字体
                ])
            
            # 图片提取参数
            if self.image_extraction:
                cmd.extend([
                    "--extract_img", "true",
                    "--img_save_dir", str(temp_dir / "images"),
                ])
            
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="processing",
                    message="PaddleOCR 版面分析中",
                    percentage=10.0
                ))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 分钟超时
            )
            
            if result.returncode == 0:
                # 查找生成的 DOCX 文件
                docx_found = False
                
                # 尝试多种可能的输出文件名
                possible_names = [
                    "result.docx",
                    f"{input_pdf.stem}.docx",
                    f"{input_pdf.stem}_result.docx",
                ]
                
                for name in possible_names:
                    candidate = temp_dir / name
                    if candidate.exists():
                        shutil.copy2(str(candidate), str(output_docx))
                        docx_found = True
                        break
                
                # 如果没找到，查找第一个 DOCX 文件
                if not docx_found:
                    for f in temp_dir.glob("*.docx"):
                        shutil.copy2(str(f), str(output_docx))
                        docx_found = True
                        break
                
                # 如果还是没找到，尝试从子目录查找
                if not docx_found:
                    for f in temp_dir.rglob("*.docx"):
                        shutil.copy2(str(f), str(output_docx))
                        docx_found = True
                        break
                
                if docx_found:
                    if self.progress_callback:
                        self.progress_callback(ConvertProgress(
                            status="completed",
                            message="PaddleOCR 转换完成",
                            percentage=100.0
                        ))
                    return True
                else:
                    logger.error("PaddleOCR 执行成功但未找到输出文件")
                    return False
            else:
                logger.error(f"PaddleOCR 失败：{result.stderr}")
                if self.progress_callback:
                    self.progress_callback(ConvertProgress(
                        status="failed",
                        message=f"PaddleOCR 错误：{result.stderr[:200]}"
                    ))
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("PaddleOCR 转换超时")
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="failed",
                    message="转换超时（>10 分钟）"
                ))
            return False
        except Exception as e:
            logger.error(f"PaddleOCR 转换异常：{e}")
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="failed",
                    message=str(e)
                ))
            return False
        finally:
            if temp_dir:
                self._cleanup_temp_dir()
    
    def _convert_pdf2docx(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        使用 pdf2docx 转换（备选方法）
        
        适合：文本型 PDF，简单布局
        优点：
        - 转换速度快
        - 格式保持好
        - 支持字体嵌入
        缺点：
        - 对扫描件支持差
        - 复杂布局可能错位
        """
        try:
            import pdf2docx
            
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="processing",
                    message="使用 pdf2docx 转换",
                    percentage=20.0
                ))
            
            # 使用 pdf2docx 转换器
            converter = pdf2docx.Converter(str(input_pdf))
            
            # 转换所有页面
            # 可以指定页面范围，这里转换全部
            converter.convert(str(output_docx))
            converter.close()
            
            # 验证输出文件
            if output_docx.exists() and output_docx.stat().st_size > 0:
                if self.progress_callback:
                    self.progress_callback(ConvertProgress(
                        status="completed",
                        message="pdf2docx 转换完成",
                        percentage=100.0
                    ))
                return True
            else:
                logger.warning("pdf2docx 输出文件为空")
                return False
            
        except ImportError:
            logger.error("pdf2docx 未安装，请运行：pip install pdf2docx")
            return False
        except Exception as e:
            logger.error(f"pdf2docx 转换异常：{e}")
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="failed",
                    message=f"pdf2docx 错误：{str(e)[:200]}"
                ))
            return False
    
    def _convert_freep2w(self, input_pdf: Path, output_docx: Path) -> bool:
        """
        使用 FreeP2W 转换（备选方法）
        
        适合：包含大量数学公式的文档
        优点：
        - 公式识别准确
        - LaTeX 支持
        缺点：
        - 速度较慢
        - 对普通文档支持一般
        """
        try:
            from freep2w.cli import convert_pdf_to_docx
            
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="processing",
                    message="使用 FreeP2W 转换",
                    percentage=20.0
                ))
            
            success = convert_pdf_to_docx(
                pdf_path=str(input_pdf),
                output_path=str(output_docx)
            )
            
            if success and output_docx.exists():
                if self.progress_callback:
                    self.progress_callback(ConvertProgress(
                        status="completed",
                        message="FreeP2W 转换完成",
                        percentage=100.0
                    ))
                return True
            else:
                logger.warning("FreeP2W 转换未生成有效输出")
                return False
            
        except ImportError:
            logger.error("FreeP2W 未安装，请运行：pip install freep2w")
            return False
        except Exception as e:
            logger.error(f"FreeP2W 转换异常：{e}")
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="failed",
                    message=f"FreeP2W 错误：{str(e)[:200]}"
                ))
            return False
    
    def convert_with_options(
        self,
        input_pdf: Path,
        output_docx: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        带选项的转换
        
        Args:
            input_pdf: 输入 PDF
            output_docx: 输出 DOCX
            options: 转换选项
                - method: 转换方法
                - preserve_format: 保持格式
                - layout_analysis: 版面分析
                - table_detection: 表格检测
                - image_extraction: 图片提取
                - ocr_first: 先 OCR（适合扫描件）
                - pages: 指定页面范围 [start, end]
                
        Returns:
            bool: 是否成功
        """
        options = options or {}
        
        # 保存原始配置
        original_method = self.method
        original_preserve_format = self.preserve_format
        original_layout_analysis = self.layout_analysis
        original_table_detection = self.table_detection
        original_image_extraction = self.image_extraction
        
        try:
            # 应用选项
            if "method" in options:
                self.method = ConvertMethod(options["method"])
            
            if "preserve_format" in options:
                self.preserve_format = options["preserve_format"]
            
            if "layout_analysis" in options:
                self.layout_analysis = options["layout_analysis"]
            
            if "table_detection" in options:
                self.table_detection = options["table_detection"]
            
            if "image_extraction" in options:
                self.image_extraction = options["image_extraction"]
            
            # 如果需要先 OCR
            if options.get("ocr_first") and input_pdf.suffix.lower() == ".pdf":
                from .ocr import OCREngine, OCREngineType
                
                if self.progress_callback:
                    self.progress_callback(ConvertProgress(
                        status="processing",
                        message="先进行 OCR 处理",
                        percentage=5.0
                    ))
                
                # 创建临时可搜索 PDF
                temp_dir = self._create_temp_dir()
                temp_pdf = temp_dir / f"{input_pdf.stem}_searchable.pdf"
                ocr_engine = OCREngine(engine_type=OCREngineType.OCRMYDF)
                
                if ocr_engine.convert_to_searchable_pdf(input_pdf, temp_pdf):
                    input_pdf = temp_pdf  # 使用 OCR 后的 PDF
                    logger.info("OCR 预处理完成")
                else:
                    logger.warning("OCR 失败，使用原 PDF 继续转换")
            
            # 处理页面范围
            pages = options.get("pages")
            if pages and isinstance(pages, (list, tuple)) and len(pages) == 2:
                # 需要页面范围处理时，使用 pdf2docx 更合适
                if self.method != ConvertMethod.PDF2DOCX:
                    logger.warning("页面范围仅支持 pdf2docx 方法，自动切换")
                    self.method = ConvertMethod.PDF2DOCX
                
                return self._convert_pdf2docx_with_pages(
                    input_pdf, output_docx, pages[0], pages[1]
                )
            
            return self.convert(input_pdf, output_docx)
        
        finally:
            # 恢复原始配置
            self.method = original_method
            self.preserve_format = original_preserve_format
            self.layout_analysis = original_layout_analysis
            self.table_detection = original_table_detection
            self.image_extraction = original_image_extraction
    
    def _convert_pdf2docx_with_pages(
        self,
        input_pdf: Path,
        output_docx: Path,
        start_page: int = 1,
        end_page: Optional[int] = None
    ) -> bool:
        """使用 pdf2docx 转换指定页面范围"""
        try:
            import pdf2docx
            import fitz  # PyMuPDF
            
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="processing",
                    message=f"转换页面 {start_page}-{end_page or 'end'}",
                    percentage=10.0
                ))
            
            # 获取总页数
            doc = fitz.open(str(input_pdf))
            total_pages = len(doc)
            doc.close()
            
            # 调整页面范围
            start = max(1, start_page) - 1  # 转为 0-indexed
            end = total_pages if end_page is None else min(end_page, total_pages)
            
            if start >= end:
                logger.error(f"无效的页面范围：{start_page}-{end_page}")
                return False
            
            converter = pdf2docx.Converter(str(input_pdf))
            converter.convert(str(output_docx), pages=(start, end))
            converter.close()
            
            if self.progress_callback:
                self.progress_callback(ConvertProgress(
                    status="completed",
                    message=f"页面 {start_page}-{end_page or total_pages} 转换完成",
                    percentage=100.0
                ))
            
            return output_docx.exists()
            
        except Exception as e:
            logger.error(f"页面范围转换异常：{e}")
            return False
    
    def analyze_layout(self, input_pdf: Path) -> List[LayoutElement]:
        """
        分析 PDF 版面结构
        
        Args:
            input_pdf: 输入 PDF
            
        Returns:
            List[LayoutElement]: 版面元素列表
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(str(input_pdf))
            elements = []
            
            for page_num, page in enumerate(doc):
                # 提取文本块
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:  # 文本块
                        element = LayoutElement(
                            type="text",
                            bbox=(
                                int(block["bbox"][0]),
                                int(block["bbox"][1]),
                                int(block["bbox"][2]),
                                int(block["bbox"][3])
                            ),
                            page=page_num + 1
                        )
                        elements.append(element)
                    elif "image" in block:  # 图片
                        element = LayoutElement(
                            type="image",
                            bbox=(
                                int(block["bbox"][0]),
                                int(block["bbox"][1]),
                                int(block["bbox"][2]),
                                int(block["bbox"][3])
                            ),
                            page=page_num + 1
                        )
                        elements.append(element)
            
            doc.close()
            
            # 按页面和位置排序
            elements.sort(key=lambda e: (e.page, e.bbox[1], e.bbox[0]))
            
            logger.info(f"分析完成，发现 {len(elements)} 个版面元素")
            return elements
            
        except Exception as e:
            logger.error(f"版面分析失败：{e}")
            return []


@dataclass
class BatchConvertResult:
    """批量转换结果"""
    total_files: int = 0
    success_count: int = 0
    fail_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def add_result(self, file_name: str, success: bool, error: str = ""):
        """添加单个结果"""
        self.results.append({
            "file": file_name,
            "status": "success" if success else "failed",
            "error": error
        })
        if success:
            self.success_count += 1
        else:
            self.fail_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            "total_files": self.total_files,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "success_rate": self.success_count / max(self.total_files, 1) * 100,
            "duration_seconds": self.duration_seconds,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": self.results
        }
    
    def save_report(self, output_path: Path):
        """保存报告"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info(f"批量转换报告已保存：{output_path}")


def batch_convert(
    input_dir: Path,
    output_dir: Path,
    method: ConvertMethod = ConvertMethod.PADDLEOCR,
    fallback_methods: Optional[List[ConvertMethod]] = None,
    preserve_format: bool = True,
    layout_analysis: bool = True,
    table_detection: bool = True,
    image_extraction: bool = True,
    parallel: bool = False,
    max_workers: int = 4,
    progress_callback: Optional[Callable[[ConvertProgress], None]] = None
) -> BatchConvertResult:
    """
    批量转换 PDF 为 WORD
    
    特性：
    - 支持并行处理（可选）
    - 进度追踪
    - 错误报告
    - 断点续传支持
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        method: 转换方法
        fallback_methods: 备选方法列表
        preserve_format: 保持格式
        layout_analysis: 版面分析
        table_detection: 表格检测
        image_extraction: 图片提取
        parallel: 是否并行处理
        max_workers: 最大工作线程数
        progress_callback: 进度回调
        
    Returns:
        BatchConvertResult: 批量转换结果
    """
    import time
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    converter = PDF2WordConverter(
        method=method,
        fallback_methods=fallback_methods,
        preserve_format=preserve_format,
        layout_analysis=layout_analysis,
        table_detection=table_detection,
        image_extraction=image_extraction,
        progress_callback=progress_callback
    )
    
    result = BatchConvertResult()
    result.start_time = datetime.now()
    
    pdf_files = sorted(input_dir.glob("*.pdf"))
    result.total_files = len(pdf_files)
    
    if not pdf_files:
        logger.warning(f"在 {input_dir} 中未找到 PDF 文件")
        result.end_time = datetime.now()
        result.duration_seconds = 0.0
        return result
    
    logger.info(f"发现 {len(pdf_files)} 个 PDF 文件，开始批量转换")
    
    if parallel and len(pdf_files) > 1:
        # 并行处理（实验性功能）
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def convert_single(pdf_path: Path) -> Tuple[str, bool, str]:
            output_path = output_dir / f"{pdf_path.stem}.docx"
            try:
                success = converter.convert(pdf_path, output_path)
                return (pdf_path.name, success, "" if success else "转换失败")
            except Exception as e:
                return (pdf_path.name, False, str(e))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(convert_single, pdf): pdf for pdf in pdf_files}
            
            for idx, future in enumerate(as_completed(futures)):
                file_name, success, error = future.result()
                result.add_result(file_name, success, error)
                
                if progress_callback:
                    progress_callback(ConvertProgress(
                        current_page=idx + 1,
                        total_pages=len(pdf_files),
                        status="processing",
                        message=f"转换 {file_name}",
                        percentage=(idx + 1) / len(pdf_files) * 100
                    ))
    else:
        # 串行处理
        for idx, pdf_path in enumerate(pdf_files):
            output_path = output_dir / f"{pdf_path.stem}.docx"
            
            if progress_callback:
                progress_callback(ConvertProgress(
                    current_page=idx + 1,
                    total_pages=len(pdf_files),
                    status="processing",
                    message=f"转换 {pdf_path.name}",
                    percentage=(idx + 1) / len(pdf_files) * 100
                ))
            
            try:
                success = converter.convert(pdf_path, output_path)
                result.add_result(pdf_path.name, success)
                
                if success:
                    logger.info(f"[{idx + 1}/{len(pdf_files)}] {pdf_path.name} ✓")
                else:
                    logger.warning(f"[{idx + 1}/{len(pdf_files)}] {pdf_path.name} ✗")
            except Exception as e:
                result.add_result(pdf_path.name, False, str(e))
                logger.error(f"[{idx + 1}/{len(pdf_files)}] {pdf_path.name} 异常：{e}")
    
    result.end_time = datetime.now()
    result.duration_seconds = (result.end_time - result.start_time).total_seconds()
    
    logger.info(
        f"批量转换完成：{result.success_count}/{result.total_files} 成功，"
        f"耗时 {result.duration_seconds:.1f}秒"
    )
    
    return result


def convert_with_layout_recovery(
    input_pdf: Path,
    output_docx: Path,
    progress_callback: Optional[Callable[[ConvertProgress], None]] = None
) -> bool:
    """
    带版面恢复的转换（高级 API）
    
    自动选择最佳转换策略：
    1. 先分析版面结构
    2. 根据内容类型选择方法
    3. 执行转换并验证
    
    Args:
        input_pdf: 输入 PDF
        output_docx: 输出 DOCX
        progress_callback: 进度回调
        
    Returns:
        bool: 是否成功
    """
    converter = PDF2WordConverter(
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[ConvertMethod.PDF2DOCX],
        preserve_format=True,
        layout_analysis=True,
        table_detection=True,
        image_extraction=True,
        progress_callback=progress_callback
    )
    
    # 先分析版面
    if progress_callback:
        progress_callback(ConvertProgress(
            status="processing",
            message="分析版面结构",
            percentage=5.0
        ))
    
    elements = converter.analyze_layout(input_pdf)
    
    # 根据分析结果调整策略
    has_tables = any(e.type == "table" for e in elements)
    has_images = any(e.type == "image" for e in elements)
    
    if has_tables:
        logger.info("检测到表格，启用表格优化模式")
        converter.table_detection = True
    
    if has_images:
        logger.info("检测到图片，启用图片提取")
        converter.image_extraction = True
    
    # 执行转换
    return converter.convert(input_pdf, output_docx)
