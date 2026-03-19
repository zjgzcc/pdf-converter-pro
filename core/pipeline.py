"""
统一处理流程模块
🔍 龙二【技术】负责实现
⚙️ 紫影【研发】负责评审
🌙 月影【情报】转开发 - 流程整合

整合完整流程：去水印 → OCR → 转换
支持进度追踪和错误恢复机制

使用示例:
    from core.pipeline import ProcessingPipeline, create_pipeline
    
    # 方式 1: 直接创建
    pipeline = ProcessingPipeline(
        remove_watermark=False,
        ocr_enabled=True,
        convert_method="paddleocr"
    )
    result = pipeline.process_single(Path("input.pdf"), Path("output.docx"))
    
    # 方式 2: 使用工厂函数
    config = {"ocr_enabled": True, "convert_method": "paddleocr"}
    pipeline = create_pipeline(config)
    
    # 方式 3: 批量处理
    results = pipeline.process_batch(
        input_dir=Path("./pdfs"),
        output_dir=Path("./output")
    )
    
    # 方式 4: 带进度回调
    def on_progress(progress: PipelineProgress):
        print(f"{progress.overall_progress:.0%} - {progress.message}")
    
    pipeline = create_pipeline(config, progress_callback=on_progress)
"""

import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
import logging
import shutil
import tempfile
from datetime import datetime

from .ocr import OCREngine, OCREngineType, OCRProgress
from .converter import PDF2WordConverter, ConvertMethod, ConvertProgress
from .watermark import WatermarkRemover

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """流水线阶段"""
    WATERMARK_REMOVE = "watermark_remove"
    OCR = "ocr"
    CONVERT = "convert"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineStatus(Enum):
    """流水线状态"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RECOVERED = "recovered"


@dataclass
class PipelineProgress:
    """流水线进度"""
    stage: PipelineStage = PipelineStage.WATERMARK_REMOVE
    status: PipelineStatus = PipelineStatus.PENDING
    current_file: str = ""
    total_files: int = 0
    processed_files: int = 0
    current_stage_progress: float = 0.0  # 当前阶段进度 0-1
    overall_progress: float = 0.0  # 总体进度 0-1
    message: str = ""
    error_message: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def update(
        self,
        stage: Optional[PipelineStage] = None,
        status: Optional[PipelineStatus] = None,
        current_file: Optional[str] = None,
        processed_files: Optional[int] = None,
        stage_progress: Optional[float] = None,
        message: Optional[str] = None,
        error: Optional[str] = None
    ):
        """更新进度"""
        if stage:
            self.stage = stage
        if status:
            self.status = status
        if current_file:
            self.current_file = current_file
        if processed_files is not None:
            self.processed_files = processed_files
        if stage_progress is not None:
            self.current_stage_progress = stage_progress
        if message:
            self.message = message
        if error:
            self.error_message = error
        
        # 计算总体进度
        if self.total_files > 0:
            self.overall_progress = self.processed_files / self.total_files


@dataclass
class PipelineResult:
    """流水线结果"""
    success: bool
    input_file: Path
    output_file: Optional[Path]
    stages_completed: List[PipelineStage] = field(default_factory=list)
    error_message: str = ""
    duration_seconds: float = 0.0
    recovery_attempts: int = 0


class PipelineError(Exception):
    """流水线异常"""
    pass


class ProcessingPipeline:
    """
    统一处理流水线
    
    完整流程：
    1. 去水印（可选）
    2. OCR 识别（扫描件）
    3. 转换为 WORD
    
    特性：
    - 进度追踪
    - 错误恢复
    - 断点续传
    - 临时文件清理
    """
    
    def __init__(
        self,
        remove_watermark: bool = False,
        watermark_method: str = "auto",
        ocr_enabled: bool = True,
        ocr_engine: OCREngineType = OCREngineType.OCRMYDF,
        ocr_language: str = "chi_sim+eng",
        convert_method: ConvertMethod = ConvertMethod.PADDLEOCR,
        convert_fallback_methods: Optional[List[ConvertMethod]] = None,
        preserve_format: bool = True,
        max_recovery_attempts: int = 2,
        cleanup_temp: bool = True,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None
    ):
        """
        Args:
            remove_watermark: 是否去除水印
            watermark_method: 去水印方法
            ocr_enabled: 是否启用 OCR
            ocr_engine: OCR 引擎类型
            ocr_language: OCR 语言
            convert_method: 转换方法
            convert_fallback_methods: 备选转换方法
            preserve_format: 保持格式
            max_recovery_attempts: 最大恢复尝试次数
            cleanup_temp: 清理临时文件
            progress_callback: 进度回调函数
        """
        self.remove_watermark = remove_watermark
        self.watermark_method = watermark_method
        self.ocr_enabled = ocr_enabled
        self.ocr_engine = ocr_engine
        self.ocr_language = ocr_language
        self.convert_method = convert_method
        self.convert_fallback_methods = convert_fallback_methods
        self.preserve_format = preserve_format
        self.max_recovery_attempts = max_recovery_attempts
        self.cleanup_temp = cleanup_temp
        self.progress_callback = progress_callback
        
        self._temp_dir: Optional[Path] = None
        self._current_progress = PipelineProgress()
    
    def _create_temp_dir(self) -> Path:
        """创建临时目录"""
        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="pdf_converter_"))
            logger.info(f"创建临时目录：{self._temp_dir}")
        return self._temp_dir
    
    def _cleanup_temp_dir(self):
        """清理临时目录"""
        if self._temp_dir and self._temp_dir.exists() and self.cleanup_temp:
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"清理临时目录：{self._temp_dir}")
            except Exception as e:
                logger.warning(f"清理临时目录失败：{e}")
    
    def _notify_progress(self, **kwargs):
        """通知进度更新"""
        self._current_progress.update(**kwargs)
        if self.progress_callback:
            self.progress_callback(self._current_progress)
    
    def process_single(
        self,
        input_file: Path,
        output_file: Path
    ) -> PipelineResult:
        """
        处理单个文件
        
        Args:
            input_file: 输入文件
            output_file: 输出文件
            
        Returns:
            PipelineResult: 处理结果
        """
        import time
        start_time = time.time()
        
        if not input_file.exists():
            return PipelineResult(
                success=False,
                input_file=input_file,
                output_file=None,
                error_message=f"输入文件不存在：{input_file}"
            )
        
        self._notify_progress(
            status=PipelineStatus.RUNNING,
            current_file=input_file.name,
            stage=PipelineStage.WATERMARK_REMOVE,
            message="开始处理"
        )
        
        recovery_attempts = 0
        current_file = input_file
        stages_completed = []
        
        try:
            # 阶段 1: 去水印
            if self.remove_watermark:
                self._notify_progress(message="去除水印中...")
                current_file = self._remove_watermark_stage(current_file, recovery_attempts)
                if current_file is None:
                    raise PipelineError("去水印失败")
                stages_completed.append(PipelineStage.WATERMARK_REMOVE)
            
            # 阶段 2: OCR
            if self.ocr_enabled:
                self._notify_progress(
                    stage=PipelineStage.OCR,
                    message="OCR 识别中..."
                )
                current_file = self._ocr_stage(current_file, recovery_attempts)
                if current_file is None:
                    raise PipelineError("OCR 失败")
                stages_completed.append(PipelineStage.OCR)
            
            # 阶段 3: 转换
            self._notify_progress(
                stage=PipelineStage.CONVERT,
                message="转换为 WORD..."
            )
            success = self._convert_stage(current_file, output_file, recovery_attempts)
            
            if not success:
                raise PipelineError("转换失败")
            
            stages_completed.append(PipelineStage.CONVERT)
            
            # 完成
            end_time = time.time()
            self._notify_progress(
                stage=PipelineStage.COMPLETED,
                status=PipelineStatus.COMPLETED,
                processed_files=1,
                message="处理完成"
            )
            
            return PipelineResult(
                success=True,
                input_file=input_file,
                output_file=output_file,
                stages_completed=stages_completed,
                duration_seconds=end_time - start_time,
                recovery_attempts=recovery_attempts
            )
            
        except PipelineError as e:
            end_time = time.time()
            error_msg = str(e)
            logger.error(f"处理失败：{error_msg}")
            
            self._notify_progress(
                stage=PipelineStage.FAILED,
                status=PipelineStatus.FAILED,
                error=error_msg
            )
            
            return PipelineResult(
                success=False,
                input_file=input_file,
                output_file=None,
                stages_completed=stages_completed,
                error_message=error_msg,
                duration_seconds=end_time - start_time,
                recovery_attempts=recovery_attempts
            )
        
        finally:
            self._cleanup_temp_dir()
    
    def _remove_watermark_stage(
        self,
        input_file: Path,
        recovery_attempts: int
    ) -> Optional[Path]:
        """去水印阶段"""
        try:
            temp_dir = self._create_temp_dir()
            output_file = temp_dir / f"nowatermark_{input_file.name}"
            
            remover = WatermarkRemover(method=self.watermark_method)
            
            # 如果是 PDF，需要先转为图片
            if input_file.suffix.lower() == ".pdf":
                import fitz
                doc = fitz.open(str(input_file))
                
                for page_num, page in enumerate(doc):
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat)
                    img_path = temp_dir / f"page_{page_num}.png"
                    pix.save(str(img_path))
                    
                    # 去除水印
                    img_output = temp_dir / f"clean_{page_num}.png"
                    if not remover.remove(img_path, img_output):
                        logger.warning(f"第 {page_num} 页去水印失败")
                
                doc.close()
                
                # 合并回 PDF（简化处理，返回图片目录）
                logger.info("去水印完成，返回图片目录")
                return temp_dir
            else:
                # 图片直接去水印
                if remover.remove(input_file, output_file):
                    return output_file
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"去水印异常：{e}")
            
            # 错误恢复：跳过此阶段
            if recovery_attempts < self.max_recovery_attempts:
                logger.warning(f"去水印失败，尝试跳过此阶段（尝试 {recovery_attempts + 1}/{self.max_recovery_attempts}）")
                recovery_attempts += 1
                return input_file
            
            return None
    
    def _ocr_stage(
        self,
        input_file: Path,
        recovery_attempts: int
    ) -> Optional[Path]:
        """OCR 阶段"""
        try:
            temp_dir = self._create_temp_dir()
            output_file = temp_dir / f"searchable_{input_file.name}"
            
            engine = OCREngine(
                engine_type=self.ocr_engine,
                language=self.ocr_language,
                progress_callback=lambda p: self._notify_progress(
                    stage_progress=p.current_page / max(p.total_pages, 1),
                    message=p.message
                )
            )
            
            if engine.convert_to_searchable_pdf(input_file, output_file):
                return output_file
            else:
                # 错误恢复：尝试其他 OCR 引擎
                if recovery_attempts < self.max_recovery_attempts:
                    logger.warning(f"OCR 失败，尝试备选引擎（尝试 {recovery_attempts + 1}/{self.max_recovery_attempts}）")
                    recovery_attempts += 1
                    
                    # 切换引擎
                    if self.ocr_engine == OCREngineType.OCRMYDF:
                        self.ocr_engine = OCREngineType.TESSERACT
                    elif self.ocr_engine == OCREngineType.TESSERACT:
                        self.ocr_engine = OCREngineType.PADDLEOCR
                    
                    return self._ocr_stage(input_file, recovery_attempts)
                
                return None
                
        except Exception as e:
            logger.error(f"OCR 异常：{e}")
            
            if recovery_attempts < self.max_recovery_attempts:
                logger.warning(f"OCR 异常，尝试跳过（尝试 {recovery_attempts + 1}/{self.max_recovery_attempts}）")
                recovery_attempts += 1
                return input_file
            
            return None
    
    def _convert_stage(
        self,
        input_file: Path,
        output_file: Path,
        recovery_attempts: int
    ) -> bool:
        """转换阶段"""
        try:
            converter = PDF2WordConverter(
                method=self.convert_method,
                fallback_methods=self.convert_fallback_methods,
                preserve_format=self.preserve_format,
                progress_callback=lambda p: self._notify_progress(
                    stage_progress=0.5,  # 简化处理
                    message=p.message
                )
            )
            
            return converter.convert(input_file, output_file)
            
        except Exception as e:
            logger.error(f"转换异常：{e}")
            
            # 错误恢复：尝试备选方法
            if recovery_attempts < self.max_recovery_attempts:
                logger.warning(f"转换失败，尝试备选方法（尝试 {recovery_attempts + 1}/{self.max_recovery_attempts}）")
                recovery_attempts += 1
                
                # 切换备选方法
                if self.convert_fallback_methods:
                    self.convert_method = self.convert_fallback_methods[
                        recovery_attempts % len(self.convert_fallback_methods)
                    ]
                
                return self._convert_stage(input_file, output_file, recovery_attempts)
            
            return False
    
    def process_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        file_pattern: str = "*.pdf"
    ) -> List[PipelineResult]:
        """
        批量处理
        
        Args:
            input_dir: 输入目录
            output_dir: 输出目录
            file_pattern: 文件匹配模式
            
        Returns:
            List[PipelineResult]: 处理结果列表
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        input_files = list(input_dir.glob(file_pattern))
        total_files = len(input_files)
        
        self._current_progress = PipelineProgress(
            total_files=total_files,
            status=PipelineStatus.RUNNING
        )
        
        results = []
        
        for idx, input_file in enumerate(input_files):
            output_file = output_dir / f"{input_file.stem}.docx"
            
            self._notify_progress(
                current_file=input_file.name,
                processed_files=idx,
                stage_progress=0,
                message=f"处理 {idx + 1}/{total_files}: {input_file.name}"
            )
            
            result = self.process_single(input_file, output_file)
            results.append(result)
        
        self._notify_progress(
            status=PipelineStatus.COMPLETED,
            processed_files=total_files,
            message=f"批量处理完成：{sum(1 for r in results if r.success)}/{total_files} 成功"
        )
        
        return results
    
    def resume_from_checkpoint(
        self,
        checkpoint_file: Path,
        output_dir: Path
    ) -> List[PipelineResult]:
        """
        从断点恢复
        
        Args:
            checkpoint_file: 检查点文件（JSON 格式，记录已处理的文件）
            output_dir: 输出目录
            
        Returns:
            List[PipelineResult]: 处理结果
        """
        import json
        
        if not checkpoint_file.exists():
            raise PipelineError(f"检查点文件不存在：{checkpoint_file}")
        
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
        
        processed_files = set(checkpoint.get("processed", []))
        input_dir = Path(checkpoint.get("input_dir", ""))
        
        if not input_dir.exists():
            raise PipelineError(f"输入目录不存在：{input_dir}")
        
        input_files = [f for f in input_dir.glob("*.pdf") if f.name not in processed_files]
        
        logger.info(f"从断点恢复，跳过 {len(processed_files)} 个已处理文件，剩余 {len(input_files)} 个文件")
        
        results = []
        for input_file in input_files:
            output_file = output_dir / f"{input_file.stem}.docx"
            result = self.process_single(input_file, output_file)
            results.append(result)
            
            # 更新检查点
            processed_files.add(input_file.name)
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "input_dir": str(input_dir),
                    "processed": list(processed_files)
                }, f, ensure_ascii=False, indent=2)
        
        return results


def create_pipeline(
    config: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[PipelineProgress], None]] = None
) -> ProcessingPipeline:
    """
    创建流水线（工厂函数）
    
    从配置文件或字典创建流水线实例
    
    Args:
        config: 配置字典，可从 config.json 加载
        progress_callback: 进度回调函数，接收 PipelineProgress 参数
        
    Returns:
        ProcessingPipeline: 配置好的流水线实例
    
    示例:
        # 从文件加载配置
        import json
        with open("config.json") as f:
            config = json.load(f)
        
        pipeline = create_pipeline(config["pipeline"])
        
        # 或手动指定配置
        pipeline = create_pipeline({
            "ocr_enabled": True,
            "ocr_language": "chi_sim+eng",
            "convert_method": "paddleocr"
        })
    """
    config = config or {}
    
    # 处理 OCR 引擎类型
    ocr_engine_raw = config.get("ocr_engine", "ocrmypdf")
    if isinstance(ocr_engine_raw, str):
        try:
            ocr_engine = OCREngineType(ocr_engine_raw.lower())
        except ValueError:
            logger.warning(f"无效的 OCR 引擎 '{ocr_engine_raw}'，使用默认值 ocrmypdf")
            ocr_engine = OCREngineType.OCRMYDF
    else:
        ocr_engine = ocr_engine_raw
    
    # 处理转换方法
    convert_method_raw = config.get("convert_method", "paddleocr")
    if isinstance(convert_method_raw, str):
        try:
            convert_method = ConvertMethod(convert_method_raw.lower())
        except ValueError:
            logger.warning(f"无效的转换方法 '{convert_method_raw}'，使用默认值 paddleocr")
            convert_method = ConvertMethod.PADDLEOCR
    else:
        convert_method = convert_method_raw
    
    # 处理备选转换方法
    fallback_methods = []
    for m in config.get("convert_fallback_methods", ["pdf2docx"]):
        try:
            if isinstance(m, str):
                fallback_methods.append(ConvertMethod(m.lower()))
            else:
                fallback_methods.append(m)
        except ValueError:
            logger.warning(f"无效的备选转换方法 '{m}'，已跳过")
    
    return ProcessingPipeline(
        remove_watermark=config.get("remove_watermark", False),
        watermark_method=config.get("watermark_method", "auto"),
        ocr_enabled=config.get("ocr_enabled", True),
        ocr_engine=ocr_engine,
        ocr_language=config.get("ocr_language", "chi_sim+eng"),
        convert_method=convert_method,
        convert_fallback_methods=fallback_methods if fallback_methods else None,
        preserve_format=config.get("preserve_format", True),
        max_recovery_attempts=config.get("max_recovery_attempts", 2),
        cleanup_temp=config.get("cleanup_temp", True),
        progress_callback=progress_callback
    )


# ============================================================================
# 导出公共 API
# ============================================================================

__all__ = [
    # 核心类
    "ProcessingPipeline",
    "PipelineError",
    
    # 枚举类型
    "PipelineStage",
    "PipelineStatus",
    
    # 数据类
    "PipelineProgress",
    "PipelineResult",
    
    # 工厂函数
    "create_pipeline",
]
