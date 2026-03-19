# Core modules for PDF Converter Pro
# 🔍 龙二【技术】优化

"""
核心模块导出
"""

from .ocr import (
    OCREngine,
    OCREngineType,
    OCRProgress,
    OCRError,
    batch_ocr
)

from .converter import (
    PDF2WordConverter,
    ConvertMethod,
    ConvertProgress,
    ConvertError,
    batch_convert
)

from .watermark import (
    WatermarkRemover,
    batch_remove_watermarks
)

from .pipeline import (
    ProcessingPipeline,
    PipelineStage,
    PipelineStatus,
    PipelineProgress,
    PipelineResult,
    PipelineError,
    create_pipeline
)

__all__ = [
    # OCR
    "OCREngine",
    "OCREngineType",
    "OCRProgress",
    "OCRError",
    "batch_ocr",
    
    # Converter
    "PDF2WordConverter",
    "ConvertMethod",
    "ConvertProgress",
    "ConvertError",
    "batch_convert",
    
    # Watermark
    "WatermarkRemover",
    "batch_remove_watermarks",
    
    # Pipeline
    "ProcessingPipeline",
    "PipelineStage",
    "PipelineStatus",
    "PipelineProgress",
    "PipelineResult",
    "PipelineError",
    "create_pipeline",
]
