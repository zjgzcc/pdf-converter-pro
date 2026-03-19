"""
OCR 功能使用示例
📊 赤影【技术】开发

演示 OCR 模块的核心功能：
1. 单文件 OCR
2. 批量 OCR（多线程）
3. PDF 文本层添加
"""

from pathlib import Path
import sys

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from ocr import (
    OCREngine, OCREngineType, OCRConfig, OCRQuality,
    batch_ocr, add_text_layer, quick_ocr, OCRProgress
)


def example_1_single_file():
    """示例 1: 单文件 OCR 处理"""
    print("=" * 60)
    print("示例 1: 单文件 OCR 处理")
    print("=" * 60)
    
    # 创建配置
    config = OCRConfig(
        language="chi_sim+eng",  # 中英文混合
        dpi=300,                  # 300 DPI
        force_ocr=True,           # 强制 OCR
        quality=OCRQuality.STANDARD
    )
    
    # 创建 OCR 引擎
    engine = OCREngine(
        engine_type=OCREngineType.OCRMYDF,
        config=config
    )
    
    # 检查引擎是否可用
    if not engine.is_engine_available():
        print("⚠️  OCRmyPDF 不可用，尝试使用其他引擎...")
        available = engine.get_available_engine()
        if available:
            print(f"✓ 使用 {available.value}")
            engine = OCREngine(engine_type=available, config=config)
        else:
            print("❌ 没有可用的 OCR 引擎")
            return
    
    # 转换文件
    input_pdf = Path("tests/sample_scan.pdf")
    output_pdf = Path("tests/output_searchable.pdf")
    
    if input_pdf.exists():
        print(f"处理文件：{input_pdf}")
        result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
        
        if result.success:
            print(f"✅ 成功！")
            print(f"   输出：{result.output_file}")
            print(f"   页数：{result.pages_processed}")
            print(f"   耗时：{result.processing_time:.2f} 秒")
            print(f"   提取文本：{len(result.text_extracted)} 字符")
        else:
            print(f"❌ 失败：{result.error_message}")
    else:
        print(f"⚠️  测试文件不存在：{input_pdf}")
        print("   请确保 tests/sample_scan.pdf 存在")


def example_2_batch_processing():
    """示例 2: 批量 OCR 处理（多线程）"""
    print("\n" + "=" * 60)
    print("示例 2: 批量 OCR 处理（多线程）")
    print("=" * 60)
    
    # 创建测试目录
    input_dir = Path("tests/batch_input")
    output_dir = Path("tests/batch_output")
    
    # 复制测试文件（如果存在）
    sample_file = Path("tests/sample_scan.pdf")
    if sample_file.exists():
        input_dir.mkdir(exist_ok=True)
        for i in range(3):
            (input_dir / f"sample_{i}.pdf").write_bytes(sample_file.read_bytes())
        
        # 批量处理
        config = OCRConfig(
            language="chi_sim+eng",
            quality=OCRQuality.STANDARD
        )
        
        def show_progress(progress):
            if progress.total_files > 0:
                percent = (progress.current_page / progress.total_files * 100)
                print(f"\r进度：{progress.current_page}/{progress.total_files} ({percent:.1f}%)", end="")
        
        print(f"处理目录：{input_dir}")
        print(f"输出目录：{output_dir}")
        print(f"线程数：4")
        
        success, fail, results = batch_ocr(
            input_dir=input_dir,
            output_dir=output_dir,
            config=config,
            max_workers=4,
            progress_callback=show_progress
        )
        
        print(f"\n✅ 完成！成功：{success}, 失败：{fail}")
        
        # 显示结果
        for result in results:
            status = "✅" if result.success else "❌"
            print(f"{status} {result.input_file.name}")
    else:
        print("⚠️  测试文件不存在，跳过批量处理示例")


def example_3_quick_ocr():
    """示例 3: 快速 OCR（便捷函数）"""
    print("\n" + "=" * 60)
    print("示例 3: 快速 OCR（便捷函数）")
    print("=" * 60)
    
    input_pdf = Path("tests/sample_scan.pdf")
    
    if input_pdf.exists():
        # 使用便捷函数，一行代码搞定
        result = quick_ocr(
            input_pdf,
            dpi=300,
            language="chi_sim+eng"
        )
        
        if result.success:
            print(f"✅ 快速 OCR 成功！")
            print(f"   输出：{result.output_file}")
        else:
            print(f"❌ 失败：{result.error_message}")
    else:
        print("⚠️  测试文件不存在")


def example_4_add_text_layer():
    """示例 4: 为扫描 PDF 添加文本层"""
    print("\n" + "=" * 60)
    print("示例 4: 为扫描 PDF 添加文本层")
    print("=" * 60)
    
    input_pdf = Path("tests/sample_scan.pdf")
    output_pdf = Path("tests/output_text_layer.pdf")
    
    if input_pdf.exists():
        # 使用便捷函数添加文本层
        success = add_text_layer(
            input_pdf,
            output_pdf,
            language="chi_sim+eng",
            dpi=300
        )
        
        if success:
            print(f"✅ 文本层添加成功！")
            print(f"   输出：{output_pdf}")
        else:
            print(f"❌ 失败")
    else:
        print("⚠️  测试文件不存在")


def example_5_custom_quality():
    """示例 5: 不同质量预设"""
    print("\n" + "=" * 60)
    print("示例 5: 不同质量预设对比")
    print("=" * 60)
    
    qualities = [
        (OCRQuality.FAST, "快速模式", "150 DPI, 不优化"),
        (OCRQuality.STANDARD, "标准模式", "300 DPI, 优化"),
        (OCRQuality.HIGH, "高质量", "450 DPI, 清理噪声"),
        (OCRQuality.BEST, "最佳质量", "600 DPI, 纠正倾斜"),
    ]
    
    for quality, name, desc in qualities:
        config = OCRConfig(quality=quality)
        config.apply_quality_preset()
        print(f"{name:10} - DPI: {config.dpi:3}, 优化：{config.optimize}, 清理：{config.clean}, 纠正：{config.deskew}")
        print(f"           {desc}")


def example_6_progress_callback():
    """示例 6: 进度回调"""
    print("\n" + "=" * 60)
    print("示例 6: 进度回调")
    print("=" * 60)
    
    def detailed_progress(progress: OCRProgress):
        """详细的进度回调"""
        if progress.total_files > 0:
            percent = (progress.current_page / progress.total_files * 100) if progress.current_page else 0
            print(f"[{progress.current_page}/{progress.total_files}] {percent:5.1f}% - {progress.status}: {progress.message}")
        elif progress.total_pages > 0:
            percent = (progress.current_page / progress.total_pages * 100) if progress.current_page else 0
            print(f"页 [{progress.current_page}/{progress.total_pages}] {percent:5.1f}% - {progress.message}")
        else:
            print(f"{progress.status}: {progress.message}")
    
    input_pdf = Path("tests/sample_scan.pdf")
    output_pdf = Path("tests/output_progress.pdf")
    
    if input_pdf.exists():
        config = OCRConfig()
        engine = OCREngine(
            engine_type=OCREngineType.OCRMYDF,
            config=config,
            progress_callback=detailed_progress
        )
        
        if engine.is_engine_available():
            result = engine.convert_to_searchable_pdf(input_pdf, output_pdf)
            print(f"\n结果：{'成功' if result.success else '失败'}")
        else:
            print("⚠️  OCR 引擎不可用")
    else:
        print("⚠️  测试文件不存在")


def main():
    """运行所有示例"""
    print("\n" + "🔍" * 30)
    print("OCR 功能使用示例")
    print("🔍" * 30 + "\n")
    
    # 运行示例
    example_1_single_file()
    example_2_batch_processing()
    example_3_quick_ocr()
    example_4_add_text_layer()
    example_5_custom_quality()
    example_6_progress_callback()
    
    print("\n" + "=" * 60)
    print("所有示例完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
