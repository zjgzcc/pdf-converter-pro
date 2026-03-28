# Core modules for PDF Converter Pro

"""
核心模块导出
"""

from .ocr_v2 import (
    OCREngine,
    OCREngineType,
    OCRConfig,
    OCRProgress,
    OCRResult,
    batch_ocr_parallel
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

__all__ = [
    # OCR
    "OCREngine",
    "OCREngineType",
    "OCRConfig",
    "OCRProgress",
    "OCRResult",
    "batch_ocr_parallel",
    
    # Converter
    "PDF2WordConverter",
    "ConvertMethod",
    "ConvertProgress",
    "ConvertError",
    "batch_convert",
    
    # Watermark
    "WatermarkRemover",
    "batch_remove_watermarks",
]
