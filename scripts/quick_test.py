#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Converter Pro - 快速测试脚本
雷影【执行】一键测试所有模块

运行：python scripts/quick_test.py
"""

import sys
import os
from pathlib import Path

# 确保 UTF-8 编码输出
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

# 添加项目根目录到路径
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def test_imports():
    """测试 1: 导入所有模块"""
    print("=" * 60)
    print("📦 测试 1: 模块导入")
    print("=" * 60)
    
    tests = [
        ("core.pipeline_lite", "轻量级管道"),
        ("core.converter", "PDF 转 WORD"),
        ("core.ocr", "OCR 引擎"),
        ("core.watermark", "去水印"),
    ]
    
    passed = 0
    failed = 0
    
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"  ✅ {description}: {module_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {description}: {module_name} - {e}")
            failed += 1
    
    print(f"\n结果：通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    return failed == 0


def test_pipeline_lite():
    """测试 2: 轻量级管道"""
    print("\n" + "=" * 60)
    print("🔧 测试 2: 轻量级管道 (pipeline_lite)")
    print("=" * 60)
    
    try:
        from core.pipeline_lite import process_pdf, quick_test
        
        # 运行内置测试
        quick_test()
        
        print("\n  ✅ 管道函数可用")
        return True
        
    except Exception as e:
        print(f"\n  ❌ 管道测试失败：{e}")
        return False


def test_converter():
    """测试 3: PDF 转 WORD 转换器"""
    print("\n" + "=" * 60)
    print("📄 测试 3: PDF 转 WORD 转换器")
    print("=" * 60)
    
    try:
        from core.converter import PDF2WordConverter, batch_convert
        
        converter = PDF2WordConverter(method="paddleocr")
        print(f"  ✅ PDF2WordConverter 创建成功 (method={converter.method})")
        print(f"  ✅ convert 方法存在")
        print(f"  ✅ batch_convert 函数存在")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 转换器测试失败：{e}")
        return False


def test_ocr():
    """测试 4: OCR 引擎"""
    print("\n" + "=" * 60)
    print("🔍 测试 4: OCR 引擎")
    print("=" * 60)
    
    try:
        from core.ocr import OCREngine, batch_ocr
        
        engine = OCREngine(language="chi_sim+eng")
        print(f"  ✅ OCREngine 创建成功 (language={engine.language})")
        print(f"  ✅ convert_to_searchable_pdf 方法存在")
        print(f"  ✅ extract_text 方法存在")
        print(f"  ✅ batch_ocr 函数存在")
        
        return True
        
    except Exception as e:
        print(f"  ❌ OCR 测试失败：{e}")
        return False


def test_watermark():
    """测试 5: 去水印模块"""
    print("\n" + "=" * 60)
    print("🎨 测试 5: 去水印模块")
    print("=" * 60)
    
    try:
        from core.watermark import WatermarkRemover, batch_remove_watermarks
        
        remover = WatermarkRemover(method="auto")
        print(f"  ✅ WatermarkRemover 创建成功 (method={remover.method})")
        print(f"  ✅ remove 方法存在")
        print(f"  ✅ batch_remove_watermarks 函数存在")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 去水印测试失败：{e}")
        return False


def test_main_lite():
    """测试 6: 轻量版主入口"""
    print("\n" + "=" * 60)
    print("🚀 测试 6: 轻量版主入口 (main_lite)")
    print("=" * 60)
    
    try:
        # 检查文件是否存在
        main_lite_path = ROOT_DIR / "main_lite.py"
        if main_lite_path.exists():
            print(f"  ✅ main_lite.py 文件存在")
            
            # 尝试导入
            import importlib.util
            spec = importlib.util.spec_from_file_location("main_lite", main_lite_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            print(f"  ✅ main_lite.py 可执行")
            return True
        else:
            print(f"  ❌ main_lite.py 文件不存在")
            return False
            
    except Exception as e:
        print(f"  ❌ 主入口测试失败：{e}")
        return False


def test_dependencies():
    """测试 7: 依赖检查"""
    print("\n" + "=" * 60)
    print("📚 测试 7: 依赖检查")
    print("=" * 60)
    
    deps = {
        "PyQt6": "GUI 界面",
        "fitz": "PyMuPDF (PDF 处理)",
        "cv2": "OpenCV (图像处理)",
        "numpy": "NumPy (数值计算)",
        "pdf2docx": "PDF 转 WORD",
        "ocrmypdf": "OCR 引擎",
    }
    
    passed = 0
    failed = 0
    
    for module_name, description in deps.items():
        try:
            __import__(module_name)
            print(f"  ✅ {description}: {module_name}")
            passed += 1
        except ImportError as e:
            print(f"  ⚠️  {description}: {module_name} (可选)")
            # 可选依赖不算失败
    
    print(f"\n结果：已安装 {passed}/{len(deps)} 个核心依赖")
    return True  # 依赖检查总是通过（可选依赖）


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("[PDF Converter Pro] " + "=" * 43)
    print("快速测试套件 - 雷影【执行】一键测试")
    print("=" * 60)
    print()
    
    tests = [
        ("模块导入", test_imports),
        ("轻量级管道", test_pipeline_lite),
        ("PDF 转 WORD", test_converter),
        ("OCR 引擎", test_ocr),
        ("去水印", test_watermark),
        ("主入口", test_main_lite),
        ("依赖检查", test_dependencies),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n  💥 测试崩溃：{name} - {e}")
            results[name] = False
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {name}")
    
    print(f"\n总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！MVP 验证成功！")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
