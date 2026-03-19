"""
水印去除功能演示测试
运行此脚本测试去水印效果

用法：
    python tests/test_watermark_demo.py
"""

import sys
from pathlib import Path

# 添加 core 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from watermark import (
    WatermarkRemover,
    WatermarkDetector,
    batch_remove_watermarks,
    process_pdf_with_watermark_removal
)
from pdf_extractor import (
    PDFExtractor,
    PDFMerger,
    pdf_to_images,
    images_to_pdf
)


def test_watermark_detector():
    """测试水印检测器"""
    print("=" * 60)
    print("测试 1: 水印检测器")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建测试图像（带浅色水印效果）
        img = np.ones((500, 500, 3), dtype=np.uint8) * 240  # 浅灰色背景
        
        # 添加一些"水印"文字效果（白色区域）
        cv2.putText(img, "WATERMARK", (50, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        detector = WatermarkDetector()
        mask = detector.detect(img)
        
        print(f"[OK] 检测器创建成功")
        print(f"  输入图像尺寸：{img.shape}")
        print(f"  输出掩码尺寸：{mask.shape}")
        print(f"  掩码非零像素：{cv2.countNonZero(mask)}")
        
        # 保存测试结果
        output_dir = Path(__file__).parent / "output" / "detector_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cv2.imwrite(str(output_dir / "input.png"), img)
        cv2.imwrite(str(output_dir / "mask.png"), mask)
        
        print(f"[OK] 测试图像已保存到：{output_dir}")
        return True
        
    except Exception as e:
        print(f"[FAIL] 测试失败：{e}")
        return False


def test_watermark_removal():
    """测试水印去除"""
    print("\n" + "=" * 60)
    print("测试 2: 水印去除 (OpenCV 模式)")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建测试图像
        img = np.ones((500, 500, 3), dtype=np.uint8) * 240
        cv2.putText(img, "SAMPLE TEXT", (50, 250),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
        
        # 添加一些背景纹理
        cv2.circle(img, (100, 100), 50, (200, 200, 200), -1)
        cv2.rectangle(img, (300, 300), (400, 400), (180, 180, 180), -1)
        
        # 保存输入图像
        output_dir = Path(__file__).parent / "output" / "removal_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        input_path = output_dir / "input.png"
        output_path = output_dir / "output.png"
        
        cv2.imwrite(str(input_path), img)
        
        # 测试去水印
        remover = WatermarkRemover(method="opencv")
        success = remover.remove(input_path, output_path)
        
        if success:
            print(f"[OK] 去水印成功")
            print(f"  输入：{input_path}")
            print(f"  输出：{output_path}")
            
            # 比较文件大小
            input_size = input_path.stat().st_size
            output_size = output_path.stat().st_size
            print(f"  输入大小：{input_size} bytes")
            print(f"  输出大小：{output_size} bytes")
            
            return True
        else:
            print(f"[FAIL] 去水印失败")
            return False
        
    except Exception as e:
        print(f"[FAIL] 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_processing():
    """测试批量处理"""
    print("\n" + "=" * 60)
    print("测试 3: 批量去水印")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建测试目录
        input_dir = Path(__file__).parent / "output" / "batch_test" / "input"
        output_dir = Path(__file__).parent / "output" / "batch_test" / "output"
        
        input_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建多个测试图像
        for i in range(5):
            img = np.ones((300, 300, 3), dtype=np.uint8) * 240
            cv2.putText(img, f"IMG_{i}", (50, 150),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            img_path = input_dir / f"test_{i:03d}.png"
            cv2.imwrite(str(img_path), img)
        
        print(f"[OK] 创建 {5} 个测试图像")
        
        # 批量处理
        success, fail, results = batch_remove_watermarks(
            input_dir,
            output_dir,
            method="opencv"
        )
        
        print(f"\n批量处理结果:")
        print(f"  成功：{success}")
        print(f"  失败：{fail}")
        print(f"  总计：{len(results)}")
        
        if success > 0:
            print(f"[OK] 批量处理成功")
            return True
        else:
            print(f"[FAIL] 批量处理失败")
            return False
        
    except Exception as e:
        print(f"[FAIL] 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_extractor():
    """测试 PDF 提取器"""
    print("\n" + "=" * 60)
    print("测试 4: PDF 提取器")
    print("=" * 60)
    
    try:
        # 检查是否有测试 PDF
        sample_pdf = Path(__file__).parent / "sample_contract.pdf"
        
        if not sample_pdf.exists():
            print(f"⚠️  样本 PDF 不存在：{sample_pdf}")
            print(f"   跳过此测试")
            return True
        
        output_dir = Path(__file__).parent / "output" / "pdf_extract_test"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # PDF 转图片
        print(f"转换 PDF: {sample_pdf.name}")
        success, fail = pdf_to_images(
            sample_pdf,
            output_dir,
            dpi=150  # 降低 DPI 加快测试
        )
        
        print(f"  成功：{success} 页")
        print(f"  失败：{fail} 页")
        
        if success > 0:
            print(f"[OK] PDF 提取成功")
            print(f"  输出目录：{output_dir}")
            return True
        else:
            print(f"[FAIL] PDF 提取失败")
            return False
        
    except Exception as e:
        print(f"[FAIL] 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def test_pdf_merger():
    """测试 PDF 合并器"""
    print("\n" + "=" * 60)
    print("测试 5: PDF 合并器")
    print("=" * 60)
    
    try:
        import cv2
        import numpy as np
        
        # 创建测试图片
        img_dir = Path(__file__).parent / "output" / "pdf_merge_test" / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(3):
            img = np.ones((800, 600, 3), dtype=np.uint8) * 255
            cv2.putText(img, f"Page {i+1}", (200, 300),
                       cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
            
            img_path = img_dir / f"page_{i+1:03d}.png"
            cv2.imwrite(str(img_path), img)
        
        print(f"[OK] 创建 {3} 个测试图像")
        
        # 合并为 PDF
        output_pdf = Path(__file__).parent / "output" / "pdf_merge_test" / "merged.pdf"
        
        result = images_to_pdf(img_dir, output_pdf, page_size="A4")
        
        if result:
            print(f"[OK] PDF 合并成功")
            print(f"  输出：{output_pdf}")
            print(f"  大小：{output_pdf.stat().st_size} bytes")
            return True
        else:
            print(f"[FAIL] PDF 合并失败")
            return False
        
    except Exception as e:
        print(f"[FAIL] 测试失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("=" * 60)
    print(" " * 18 + "水印去除功能演示测试" + " " * 18)
    print("=" * 60)
    print()
    
    results = {
        "水印检测器": test_watermark_detector(),
        "水印去除": test_watermark_removal(),
        "批量处理": test_batch_processing(),
        "PDF 提取器": test_pdf_extractor(),
        "PDF 合并器": test_pdf_merger(),
    }
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
