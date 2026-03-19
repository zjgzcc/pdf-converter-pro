"""
PDF Converter Pro 使用示例
🔍 龙二【技术】编写

演示如何使用优化后的技术模块
"""

from pathlib import Path
from core import (
    OCREngine,
    OCREngineType,
    PDF2WordConverter,
    ConvertMethod,
    ProcessingPipeline,
    create_pipeline,
    PipelineProgress
)


# ==================== 示例 1: OCR 模块使用 ====================

def example_ocr_basic():
    """基础 OCR 使用"""
    from pathlib import Path
    
    engine = OCREngine(engine_type=OCREngineType.OCRMYDF)
    
    input_pdf = Path("input.pdf")
    output_pdf = Path("searchable.pdf")
    
    success = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
    print(f"OCR 完成：{success}")


def example_ocr_with_progress():
    """带进度回调的 OCR"""
    from pathlib import Path
    
    def on_progress(progress):
        print(f"OCR 进度：{progress.current_page}/{progress.total_pages} - {progress.message}")
    
    engine = OCREngine(
        engine_type=OCREngineType.TESSERACT,
        language="chi_sim+eng",
        progress_callback=on_progress
    )
    
    input_pdf = Path("input.pdf")
    output_pdf = Path("searchable.pdf")
    
    success = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
    print(f"OCR 完成：{success}")


def example_ocr_batch():
    """批量 OCR"""
    from pathlib import Path
    
    def on_progress(progress):
        print(f"批量进度：{progress.current_page}/{progress.total_files}")
    
    input_dir = Path("input_pdfs")
    output_dir = Path("output_searchable")
    
    success, fail, results = batch_ocr(
        input_dir=input_dir,
        output_dir=output_dir,
        language="chi_sim+eng",
        engine_type=OCREngineType.OCRMYDF,
        progress_callback=on_progress
    )
    
    print(f"成功：{success}, 失败：{fail}")
    for r in results:
        print(f"  {r['file']}: {r['status']}")


# ==================== 示例 2: 转换模块使用 ====================

def example_convert_basic():
    """基础 PDF 转 WORD"""
    from pathlib import Path
    
    converter = PDF2WordConverter(method=ConvertMethod.PADDLEOCR)
    
    input_pdf = Path("input.pdf")
    output_docx = Path("output.docx")
    
    success = converter.convert(input_pdf, output_docx)
    print(f"转换完成：{success}")


def example_convert_with_fallback():
    """带备选方案的转换"""
    from pathlib import Path
    
    # 主方法失败时自动尝试备选方法
    converter = PDF2WordConverter(
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[
            ConvertMethod.PDF2DOCX,
            ConvertMethod.FREEP2W
        ],
        preserve_format=True
    )
    
    input_pdf = Path("input.pdf")
    output_docx = Path("output.docx")
    
    success = converter.convert(input_pdf, output_docx)
    print(f"转换完成（可能使用了备选方案）：{success}")


def example_convert_with_options():
    """带选项的转换"""
    from pathlib import Path
    
    converter = PDF2WordConverter()
    
    input_pdf = Path("input.pdf")
    output_docx = Path("output.docx")
    
    # 指定先 OCR 再转换（适合扫描件）
    success = converter.convert_with_options(
        input_pdf=input_pdf,
        output_docx=output_docx,
        options={
            "method": "paddleocr",
            "preserve_format": True,
            "ocr_first": True,  # 先 OCR
        }
    )
    
    print(f"转换完成：{success}")


# ==================== 示例 3: 流水线使用 ====================

def example_pipeline_basic():
    """基础流水线使用"""
    from pathlib import Path
    
    # 创建流水线
    pipeline = ProcessingPipeline(
        remove_watermark=False,  # 不去水印
        ocr_enabled=True,        # 启用 OCR
        convert_method=ConvertMethod.PADDLEOCR
    )
    
    input_file = Path("input.pdf")
    output_file = Path("output.docx")
    
    result = pipeline.process_single(input_file, output_file)
    
    print(f"处理完成：{result.success}")
    print(f"耗时：{result.duration_seconds:.2f}秒")
    print(f"完成阶段：{result.stages_completed}")
    
    if not result.success:
        print(f"错误：{result.error_message}")


def example_pipeline_full():
    """完整流水线（去水印→OCR→转换）"""
    from pathlib import Path
    
    def on_progress(progress):
        print(f"进度：{progress.overall_progress*100:.1f}%")
        print(f"  阶段：{progress.stage.value}")
        print(f"  状态：{progress.status.value}")
        print(f"  消息：{progress.message}")
    
    pipeline = ProcessingPipeline(
        remove_watermark=True,           # 去水印
        watermark_method="auto",
        ocr_enabled=True,                # OCR
        ocr_engine=OCREngineType.OCRMYDF,
        ocr_language="chi_sim+eng",
        convert_method=ConvertMethod.PADDLEOCR,
        convert_fallback_methods=[ConvertMethod.PDF2DOCX],
        preserve_format=True,
        max_recovery_attempts=2,
        progress_callback=on_progress
    )
    
    input_file = Path("scanned_with_watermark.pdf")
    output_file = Path("output.docx")
    
    result = pipeline.process_single(input_file, output_file)
    
    print(f"\n处理结果：{result.success}")
    print(f"耗时：{result.duration_seconds:.2f}秒")
    print(f"恢复尝试：{result.recovery_attempts}次")


def example_pipeline_batch():
    """批量处理"""
    from pathlib import Path
    
    def on_progress(progress):
        print(f"总体进度：{progress.overall_progress*100:.1f}%")
        print(f"当前文件：{progress.current_file}")
        print(f"已处理：{progress.processed_files}/{progress.total_files}")
    
    pipeline = create_pipeline(
        config={
            "remove_watermark": False,
            "ocr_enabled": True,
            "ocr_engine": "ocrmypdf",
            "convert_method": "paddleocr",
            "convert_fallback_methods": ["pdf2docx"],
            "preserve_format": True,
        },
        progress_callback=on_progress
    )
    
    input_dir = Path("input_pdfs")
    output_dir = Path("output_word")
    
    results = pipeline.process_batch(input_dir, output_dir)
    
    success_count = sum(1 for r in results if r.success)
    print(f"\n批量处理完成：{success_count}/{len(results)} 成功")


def example_pipeline_resume():
    """断点续传"""
    from pathlib import Path
    
    pipeline = ProcessingPipeline(
        ocr_enabled=True,
        convert_method=ConvertMethod.PADDLEOCR
    )
    
    checkpoint_file = Path("checkpoint.json")
    output_dir = Path("output_word")
    
    # 从检查点恢复
    results = pipeline.resume_from_checkpoint(checkpoint_file, output_dir)
    
    print(f"恢复处理完成：{sum(1 for r in results if r.success)} 成功")


# ==================== 示例 4: 错误处理 ====================

def example_error_handling():
    """错误处理示例"""
    from pathlib import Path
    from core import PipelineError, ConvertError, OCRError
    
    pipeline = ProcessingPipeline(
        ocr_enabled=True,
        max_recovery_attempts=2
    )
    
    input_file = Path("input.pdf")
    output_file = Path("output.docx")
    
    try:
        result = pipeline.process_single(input_file, output_file)
        
        if not result.success:
            print(f"处理失败：{result.error_message}")
            print(f"已完成的阶段：{result.stages_completed}")
            print(f"恢复尝试次数：{result.recovery_attempts}")
            
            # 根据失败阶段决定下一步
            if PipelineStage.OCR not in result.stages_completed:
                print("OCR 失败，可以尝试其他 OCR 引擎")
            elif PipelineStage.CONVERT not in result.stages_completed:
                print("转换失败，可以尝试备选转换方法")
    
    except PipelineError as e:
        print(f"流水线错误：{e}")
    except Exception as e:
        print(f"未知错误：{e}")


# ==================== 运行示例 ====================

if __name__ == "__main__":
    print("=== PDF Converter Pro 使用示例 ===\n")
    
    # 取消注释运行相应示例
    # example_ocr_basic()
    # example_ocr_with_progress()
    # example_convert_basic()
    # example_convert_with_fallback()
    # example_pipeline_basic()
    # example_pipeline_full()
    
    print("示例代码已就绪，取消注释即可运行")
