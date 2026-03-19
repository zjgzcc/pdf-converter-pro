"""
PDF 转 WORD 高级使用示例
🧪 青影【测试】转开发 - 演示增强功能

本示例演示：
1. PaddleOCR 版面恢复
2. 备选方案自动降级
3. 批量转换
4. 进度追踪
5. 格式保持选项
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.converter import (
    PDF2WordConverter,
    ConvertMethod,
    ConvertProgress,
    batch_convert,
    BatchConvertResult,
    convert_with_layout_recovery
)


def print_progress(progress: ConvertProgress):
    """打印进度信息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if progress.percentage > 0:
        print(f"[{timestamp}] {progress.status.upper()}: {progress.message} ({progress.percentage:.1f}%)")
    else:
        print(f"[{timestamp}] {progress.status.upper()}: {progress.message}")


def example_basic_conversion():
    """
    示例 1: 基本转换
    
    使用 PaddleOCR 进行转换，失败时自动尝试 pdf2docx
    """
    print("\n" + "="*60)
    print("示例 1: 基本转换")
    print("="*60)
    
    converter = PDF2WordConverter(
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[ConvertMethod.PDF2DOCX],
        preserve_format=True,
        progress_callback=print_progress
    )
    
    input_pdf = PROJECT_ROOT / "tests" / "sample_contract.pdf"
    output_docx = PROJECT_ROOT / "output" / "sample_contract.docx"
    
    if not input_pdf.exists():
        print(f"⚠️  示例文件不存在：{input_pdf}")
        print("   请确保测试文件存在或修改为实际文件路径")
        return
    
    print(f"\n开始转换：{input_pdf.name}")
    success = converter.convert(input_pdf, output_docx)
    
    if success:
        print(f"✓ 转换成功：{output_docx}")
    else:
        print(f"✗ 转换失败")


def example_layout_recovery():
    """
    示例 2: 版面恢复转换
    
    自动分析 PDF 版面结构，优化转换策略
    """
    print("\n" + "="*60)
    print("示例 2: 版面恢复转换")
    print("="*60)
    
    input_pdf = PROJECT_ROOT / "tests" / "sample_invoice.pdf"
    output_docx = PROJECT_ROOT / "output" / "sample_invoice_restored.docx"
    
    if not input_pdf.exists():
        print(f"⚠️  示例文件不存在：{input_pdf}")
        return
    
    print(f"\n开始版面恢复转换：{input_pdf.name}")
    
    success = convert_with_layout_recovery(
        input_pdf,
        output_docx,
        progress_callback=print_progress
    )
    
    if success:
        print(f"✓ 版面恢复完成：{output_docx}")
    else:
        print(f"✗ 版面恢复失败")


def example_custom_options():
    """
    示例 3: 自定义转换选项
    
    启用特定功能：表格检测、图片提取等
    """
    print("\n" + "="*60)
    print("示例 3: 自定义转换选项")
    print("="*60)
    
    converter = PDF2WordConverter(
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[ConvertMethod.PDF2DOCX, ConvertMethod.FREEP2W],
        preserve_format=True,
        layout_analysis=True,      # 启用版面分析
        table_detection=True,       # 启用表格检测
        image_extraction=True,      # 启用图片提取
        progress_callback=print_progress
    )
    
    input_pdf = PROJECT_ROOT / "tests" / "sample_scan.pdf"
    output_docx = PROJECT_ROOT / "output" / "sample_scan_custom.docx"
    
    if not input_pdf.exists():
        print(f"⚠️  示例文件不存在：{input_pdf}")
        return
    
    print(f"\n使用自定义选项转换：{input_pdf.name}")
    print("   - 版面分析：✓")
    print("   - 表格检测：✓")
    print("   - 图片提取：✓")
    
    success = converter.convert(input_pdf, output_docx)
    
    if success:
        print(f"✓ 转换成功：{output_docx}")
    else:
        print(f"✗ 转换失败")


def example_batch_conversion():
    """
    示例 4: 批量转换
    
    转换整个目录的 PDF 文件
    """
    print("\n" + "="*60)
    print("示例 4: 批量转换")
    print("="*60)
    
    input_dir = PROJECT_ROOT / "tests"
    output_dir = PROJECT_ROOT / "output" / "batch_output"
    
    if not input_dir.exists():
        print(f"⚠️  输入目录不存在：{input_dir}")
        return
    
    print(f"\n开始批量转换")
    print(f"   输入目录：{input_dir}")
    print(f"   输出目录：{output_dir}")
    
    result: BatchConvertResult = batch_convert(
        input_dir=input_dir,
        output_dir=output_dir,
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[ConvertMethod.PDF2DOCX],
        preserve_format=True,
        layout_analysis=True,
        table_detection=True,
        image_extraction=True,
        parallel=False,  # 串行处理（更稳定）
        progress_callback=print_progress
    )
    
    print(f"\n{'='*60}")
    print("批量转换结果")
    print(f"{'='*60}")
    print(f"总文件数：{result.total_files}")
    print(f"成功：{result.success_count}")
    print(f"失败：{result.fail_count}")
    print(f"成功率：{result.success_count / max(result.total_files, 1) * 100:.1f}%")
    print(f"耗时：{result.duration_seconds:.2f}秒")
    
    if result.results:
        print(f"\n详细结果:")
        for r in result.results:
            status_icon = "✓" if r["status"] == "success" else "✗"
            print(f"  {status_icon} {r['file']}")
    
    # 保存报告
    report_path = output_dir / "conversion_report.json"
    result.save_report(report_path)
    print(f"\n报告已保存：{report_path}")


def example_parallel_batch():
    """
    示例 5: 并行批量转换
    
    使用多线程加速处理大量文件
    """
    print("\n" + "="*60)
    print("示例 5: 并行批量转换（实验性）")
    print("="*60)
    
    input_dir = PROJECT_ROOT / "tests"
    output_dir = PROJECT_ROOT / "output" / "parallel_output"
    
    print(f"\n使用并行处理转换")
    print(f"   输入目录：{input_dir}")
    print(f"   输出目录：{output_dir}")
    print(f"   最大线程数：4")
    
    result: BatchConvertResult = batch_convert(
        input_dir=input_dir,
        output_dir=output_dir,
        method=ConvertMethod.PDF2DOCX,  # 并行时建议使用 pdf2docx
        parallel=True,
        max_workers=4,
        progress_callback=print_progress
    )
    
    print(f"\n{'='*60}")
    print("并行转换结果")
    print(f"{'='*60}")
    print(f"总文件数：{result.total_files}")
    print(f"成功：{result.success_count}")
    print(f"失败：{result.fail_count}")
    print(f"耗时：{result.duration_seconds:.2f}秒")


def example_convert_with_pages():
    """
    示例 6: 转换指定页面范围
    
    仅转换 PDF 的特定页面
    """
    print("\n" + "="*60)
    print("示例 6: 转换指定页面范围")
    print("="*60)
    
    converter = PDF2WordConverter(
        method=ConvertMethod.PDF2DOCX,
        progress_callback=print_progress
    )
    
    input_pdf = PROJECT_ROOT / "tests" / "sample_contract.pdf"
    output_docx = PROJECT_ROOT / "output" / "sample_contract_pages.docx"
    
    if not input_pdf.exists():
        print(f"⚠️  示例文件不存在：{input_pdf}")
        return
    
    print(f"\n转换页面范围：1-2")
    
    success = converter.convert_with_options(
        input_pdf,
        output_docx,
        options={
            "pages": [1, 2],  # 转换第 1-2 页
            "method": "pdf2docx"
        }
    )
    
    if success:
        print(f"✓ 页面转换成功：{output_docx}")
    else:
        print(f"✗ 页面转换失败")


def example_ocr_first():
    """
    示例 7: 先 OCR 后转换
    
    适合扫描件：先进行 OCR 识别，再转换为 WORD
    """
    print("\n" + "="*60)
    print("示例 7: 先 OCR 后转换")
    print("="*60)
    
    converter = PDF2WordConverter(
        method=ConvertMethod.PADDLEOCR,
        fallback_methods=[ConvertMethod.PDF2DOCX],
        progress_callback=print_progress
    )
    
    input_pdf = PROJECT_ROOT / "tests" / "sample_scan.pdf"
    output_docx = PROJECT_ROOT / "output" / "sample_scan_ocr.docx"
    
    if not input_pdf.exists():
        print(f"⚠️  示例文件不存在：{input_pdf}")
        return
    
    print(f"\n先 OCR 识别，再转换：{input_pdf.name}")
    
    success = converter.convert_with_options(
        input_pdf,
        output_docx,
        options={
            "ocr_first": True,  # 先进行 OCR 处理
            "preserve_format": True
        }
    )
    
    if success:
        print(f"✓ OCR+ 转换完成：{output_docx}")
    else:
        print(f"✗ 处理失败")


def main():
    """运行所有示例"""
    print("\n" + "="*60)
    print("PDF 转 WORD 高级使用示例")
    print("🧪 青影【测试】转开发")
    print("="*60)
    
    # 创建输出目录
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    
    # 运行示例
    examples = [
        ("基本转换", example_basic_conversion),
        ("版面恢复转换", example_layout_recovery),
        ("自定义选项", example_custom_options),
        ("批量转换", example_batch_conversion),
        # ("并行批量转换", example_parallel_batch),  # 可选
        ("页面范围转换", example_convert_with_pages),
        ("OCR+ 转换", example_ocr_first),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ {name} 示例异常：{e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("所有示例运行完成")
    print("="*60)


if __name__ == "__main__":
    main()
