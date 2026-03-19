"""
批量 OCR 处理工具
📊 赤影【技术】开发

功能：
- 批量处理目录中的所有 PDF
- 多线程加速
- 进度显示
- 结果统计
"""

import argparse
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "core"))

from ocr import batch_ocr, OCREngineType, OCRConfig, OCRQuality


def print_progress(progress):
    """打印进度"""
    if progress.total_files > 0:
        percent = (progress.current_page / progress.total_files * 100) if progress.current_page else 0
        print(f"\r进度：{progress.current_page}/{progress.total_files} ({percent:.1f}%) - {progress.message}", end="", flush=True)
    else:
        print(f"\r{progress.message}", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="批量 OCR 处理工具 - 将扫描 PDF 转为可搜索 PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python batch_ocr.py input/ output/
  python batch_ocr.py input/ output/ --threads 8 --quality high
  python batch_ocr.py input/ output/ --lang eng --force-ocr
        """
    )
    
    parser.add_argument("input_dir", type=Path, help="输入目录（包含 PDF 文件）")
    parser.add_argument("output_dir", type=Path, help="输出目录")
    parser.add_argument("--threads", "-t", type=int, default=4, help="线程数（默认：4）")
    parser.add_argument("--quality", "-q", type=str, default="standard",
                       choices=["fast", "standard", "high", "best"],
                       help="OCR 质量（默认：standard）")
    parser.add_argument("--language", "-l", type=str, default="chi_sim+eng",
                       help="OCR 语言（默认：chi_sim+eng）")
    parser.add_argument("--dpi", type=int, default=300, help="DPI（默认：300）")
    parser.add_argument("--force-ocr", action="store_true", help="强制 OCR（即使已有文本）")
    parser.add_argument("--engine", type=str, default="ocrmypdf",
                       choices=["ocrmypdf", "tesseract", "paddleocr"],
                       help="OCR 引擎（默认：ocrmypdf）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 验证输入目录
    if not args.input_dir.exists():
        print(f"❌ 错误：输入目录不存在：{args.input_dir}")
        sys.exit(1)
    
    # 创建配置
    quality_map = {
        "fast": OCRQuality.FAST,
        "standard": OCRQuality.STANDARD,
        "high": OCRQuality.HIGH,
        "best": OCRQuality.BEST
    }
    
    config = OCRConfig(
        language=args.language,
        dpi=args.dpi,
        force_ocr=args.force_ocr,
        quality=quality_map[args.quality]
    )
    
    # 引擎映射
    engine_map = {
        "ocrmypdf": OCREngineType.OCRMYDF,
        "tesseract": OCREngineType.TESSERACT,
        "paddleocr": OCREngineType.PADDLEOCR
    }
    
    print("=" * 60)
    print("📄 批量 OCR 处理工具")
    print("=" * 60)
    print(f"输入目录：{args.input_dir.absolute()}")
    print(f"输出目录：{args.output_dir.absolute()}")
    print(f"线程数：{args.threads}")
    print(f"质量：{args.quality}")
    print(f"语言：{args.language}")
    print(f"DPI: {args.dpi}")
    print(f"引擎：{args.engine}")
    print(f"强制 OCR: {args.force_ocr}")
    print("=" * 60)
    
    # 执行批量 OCR
    start_time = time.time()
    
    success, fail, results = batch_ocr(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        config=config,
        engine_type=engine_map[args.engine],
        max_workers=args.threads,
        progress_callback=print_progress if not args.verbose else None
    )
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("✅ 处理完成")
    print("=" * 60)
    print(f"成功：{success} 个文件")
    print(f"失败：{fail} 个文件")
    print(f"总计：{success + fail} 个文件")
    print(f"耗时：{elapsed:.2f} 秒")
    
    if success > 0:
        avg_time = elapsed / success
        print(f"平均速度：{avg_time:.2f} 秒/文件")
    
    # 输出失败文件详情
    if fail > 0 and args.verbose:
        print("\n❌ 失败文件:")
        for result in results:
            if not result.success:
                print(f"  - {result.input_file.name}: {result.error_message}")
    
    # 保存结果报告
    report_path = args.output_dir / f"ocr_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("批量 OCR 处理报告\n")
        f.write("=" * 60 + "\n")
        f.write(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"输入目录：{args.input_dir}\n")
        f.write(f"输出目录：{args.output_dir}\n")
        f.write(f"线程数：{args.threads}\n")
        f.write(f"质量：{args.quality}\n")
        f.write(f"语言：{args.language}\n")
        f.write(f"DPI: {args.dpi}\n")
        f.write(f"引擎：{args.engine}\n")
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"成功：{success} 个文件\n")
        f.write(f"失败：{fail} 个文件\n")
        f.write(f"总计：{success + fail} 个文件\n")
        f.write(f"耗时：{elapsed:.2f} 秒\n")
        f.write("\n详细结果:\n")
        f.write("-" * 60 + "\n")
        for result in results:
            status = "✅" if result.success else "❌"
            f.write(f"{status} {result.input_file.name}\n")
            if not result.success:
                f.write(f"   错误：{result.error_message}\n")
            if result.output_file:
                f.write(f"   输出：{result.output_file}\n")
            if result.pages_processed > 0:
                f.write(f"   页数：{result.pages_processed}\n")
            if result.processing_time > 0:
                f.write(f"   耗时：{result.processing_time:.2f} 秒\n")
    
    print(f"\n📋 报告已保存：{report_path}")
    
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
