"""
水印去除功能使用示例
🔍 龙二【技术】编写

本示例展示如何使用水印去除模块的各种功能
"""

from pathlib import Path
import sys

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from watermark import (
    WatermarkRemover,
    WatermarkDetector,
    batch_remove_watermarks,
    process_pdf_images,
    images_to_pdf,
    process_pdf_with_watermark_removal
)


def example_1_simple_remove():
    """示例 1: 简单去水印"""
    print("=" * 60)
    print("示例 1: 简单去水印")
    print("=" * 60)
    
    # 创建去水印器（自动选择方法）
    remover = WatermarkRemover(method="auto")
    
    # 去除单张图片的水印
    input_path = Path("tests/sample_watermark.png")
    output_path = Path("output/watermark_removed.png")
    
    if input_path.exists():
        success = remover.remove(input_path, output_path)
        if success:
            print(f"[OK] 去水印完成：{output_path}")
        else:
            print(f"[FAIL] 去水印失败")
    else:
        print(f"[SKIP] 样本文件不存在：{input_path}")


def example_2_batch_processing():
    """示例 2: 批量去水印"""
    print("\n" + "=" * 60)
    print("示例 2: 批量去水印")
    print("=" * 60)
    
    input_dir = Path("output/batch_input")
    output_dir = Path("output/batch_output")
    
    # 创建测试图片
    input_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        import cv2
        import numpy as np
        
        for i in range(5):
            img = np.ones((400, 400, 3), dtype=np.uint8) * 240
            cv2.putText(img, f"Test {i}", (80, 200),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            img_path = input_dir / f"test_{i:03d}.png"
            cv2.imwrite(str(img_path), img)
        
        print(f"[OK] 创建 {5} 个测试图片")
        
        # 批量处理
        success, fail, results = batch_remove_watermarks(
            input_dir,
            output_dir,
            method="opencv",  # 或 "iopaint" 或 "auto"
            recursive=False
        )
        
        print(f"\n[OK] 批量处理完成:")
        print(f"  成功：{success} 个")
        print(f"  失败：{fail} 个")
        
    except Exception as e:
        print(f"[FAIL] 批量处理失败：{e}")


def example_3_watermark_detection():
    """示例 3: 水印检测"""
    print("\n" + "=" * 60)
    print("示例 3: 水印检测")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建测试图像
        img = np.ones((500, 500, 3), dtype=np.uint8) * 240
        cv2.putText(img, "WATERMARK", (50, 250),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        # 检测水印
        detector = WatermarkDetector()
        mask = detector.detect(img)
        
        # 保存结果
        output_dir = Path("output/detection_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(output_dir / "input.png"), img)
        cv2.imwrite(str(output_dir / "mask.png"), mask)
        
        print(f"[OK] 水印检测完成")
        print(f"  掩码尺寸：{mask.shape}")
        print(f"  非零像素：{cv2.countNonZero(mask)}")
        print(f"  输出目录：{output_dir}")
        
    except Exception as e:
        print(f"[FAIL] 检测失败：{e}")


def example_4_pdf_to_images():
    """示例 4: PDF 转图片"""
    print("\n" + "=" * 60)
    print("示例 4: PDF 转图片")
    print("=" * 60)
    
    from pdf_extractor import PDFExtractor
    
    # 创建提取器
    extractor = PDFExtractor(dpi=300)  # 300 DPI 高质量
    
    # 转换 PDF
    input_pdf = Path("tests/sample_contract.pdf")
    output_dir = Path("output/pdf_pages")
    
    if input_pdf.exists():
        success, fail, results = extractor.pdf_to_images(
            input_pdf,
            output_dir,
            pages=None,  # None=全部页面
            image_format="png"
        )
        
        print(f"\n[OK] PDF 转图片完成:")
        print(f"  成功：{success} 页")
        print(f"  失败：{fail} 页")
    else:
        print(f"[SKIP] 样本 PDF 不存在：{input_pdf}")


def example_5_images_to_pdf():
    """示例 5: 图片合并为 PDF"""
    print("\n" + "=" * 60)
    print("示例 5: 图片合并为 PDF")
    print("=" * 60)
    
    from pdf_extractor import PDFMerger
    
    # 创建合并器
    merger = PDFMerger(page_size="A4")
    
    # 合并图片
    input_dir = Path("output/pdf_pages")
    output_pdf = Path("output/merged.pdf")
    
    if input_dir.exists():
        result = merger.images_to_pdf(
            input_dir,
            output_pdf,
            pattern="*.png",
            fit_page=True  # 自动适应页面
        )
        
        if result:
            print(f"\n[OK] PDF 合并完成：{output_pdf}")
            print(f"  文件大小：{output_pdf.stat().st_size} bytes")
        else:
            print(f"[FAIL] PDF 合并失败")
    else:
        print(f"[SKIP] 输入目录不存在：{input_dir}")


def example_6_pdf_watermark_removal():
    """示例 6: PDF 去水印完整流程"""
    print("\n" + "=" * 60)
    print("示例 6: PDF 去水印完整流程")
    print("=" * 60)
    
    input_pdf = Path("tests/sample_contract.pdf")
    output_pdf = Path("output/clean.pdf")
    
    if input_pdf.exists():
        result = process_pdf_with_watermark_removal(
            input_pdf,
            output_pdf,
            method="auto",  # 自动选择最佳方法
            dpi=300
        )
        
        if result:
            print(f"\n[OK] PDF 去水印完成：{output_pdf}")
        else:
            print(f"[FAIL] PDF 去水印失败")
    else:
        print(f"[SKIP] 样本 PDF 不存在：{input_pdf}")


def example_7_extract_embedded_images():
    """示例 7: 提取 PDF 中的嵌入图片"""
    print("\n" + "=" * 60)
    print("示例 7: 提取 PDF 中的嵌入图片")
    print("=" * 60)
    
    from pdf_extractor import PDFExtractor
    
    extractor = PDFExtractor()
    
    input_pdf = Path("tests/sample_invoice.pdf")
    output_dir = Path("output/extracted_images")
    
    if input_pdf.exists():
        success, fail, results = extractor.extract_embedded_images(
            input_pdf,
            output_dir
        )
        
        print(f"\n[OK] 提取嵌入图片完成:")
        print(f"  成功：{success} 个")
        print(f"  失败：{fail} 个")
    else:
        print(f"[SKIP] 样本 PDF 不存在：{input_pdf}")


def main():
    """运行所有示例"""
    print("\n")
    print("=" * 60)
    print(" " * 18 + "水印去除功能使用示例" + " " * 18)
    print("=" * 60)
    
    # 创建输出目录
    Path("output").mkdir(exist_ok=True)
    
    # 运行示例
    example_1_simple_remove()
    example_2_batch_processing()
    example_3_watermark_detection()
    example_4_pdf_to_images()
    example_5_images_to_pdf()
    example_6_pdf_watermark_removal()
    example_7_extract_embedded_images()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
