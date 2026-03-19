#!/usr/bin/env python3
"""
PDF Converter Pro - MVP 轻量版
⚡ 雷影【执行】快速验证

命令行版本，跳过 GUI，直接跑通核心流程
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="PDF Converter Pro - MVP 版")
    parser.add_argument("input", type=Path, help="输入 PDF 文件或目录")
    parser.add_argument("-o", "--output", type=Path, required=True, help="输出目录")
    parser.add_argument("--ocr", action="store_true", default=True, help="执行 OCR 识别")
    parser.add_argument("--word", action="store_true", default=True, help="转换为 WORD")
    parser.add_argument("--watermark", action="store_true", default=False, help="去除水印")
    parser.add_argument("--lang", default="chi_sim+eng", help="OCR 语言")
    
    args = parser.parse_args()
    
    # 验证输入
    if not args.input.exists():
        print(f"❌ 输入路径不存在：{args.input}")
        sys.exit(1)
    
    # 创建输出目录
    args.output.mkdir(parents=True, exist_ok=True)
    
    print(f"🦎 PDF Converter Pro - MVP 版")
    print(f"📁 输入：{args.input}")
    print(f"📂 输出：{args.output}")
    print(f"🔧 选项：OCR={args.ocr}, WORD={args.word}, 水印={args.watermark}")
    print("-" * 50)
    
    try:
        from core.pipeline_lite import process_pdf
        
        success, message = process_pdf(
            input_path=args.input,
            output_dir=args.output,
            do_ocr=args.ocr,
            convert_to_word=args.word,
            remove_watermark=args.watermark,
            language=args.lang
        )
        
        if success:
            print(f"\n✅ {message}")
            sys.exit(0)
        else:
            print(f"\n❌ {message}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 处理失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
