#!/usr/bin/env python3
"""
PDF Converter Pro - 命令行工具
🌙 月影【情报】转开发
⚙️ 紫影【研发】评审

提供完整的命令行接口，支持单文件/批量处理、进度显示、配置管理
"""

# 修复 Windows 编码问题
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import asdict

from tqdm import tqdm

from core.pipeline import (
    ProcessingPipeline,
    PipelineProgress,
    PipelineStatus,
    PipelineStage,
    create_pipeline
)
from core.ocr import OCREngineType
from core.converter import ConvertMethod


# 配置日志
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志"""
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )


def load_config(config_path: Optional[str] = None) -> dict:
    """加载配置文件"""
    if config_path:
        config_file = Path(config_path)
    else:
        config_file = Path(__file__).parent / "config.json"
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 默认配置
        return {
            "pipeline": {
                "remove_watermark": False,
                "watermark_method": "auto",
                "ocr_enabled": True,
                "ocr_engine": "ocrmypdf",
                "ocr_language": "chi_sim+eng",
                "convert_method": "paddleocr",
                "convert_fallback_methods": ["pdf2docx"],
                "preserve_format": True,
                "max_recovery_attempts": 2,
                "cleanup_temp": True
            }
        }


def create_progress_bar():
    """创建进度条"""
    pbar = None
    
    def progress_callback(progress: PipelineProgress):
        nonlocal pbar
        
        if progress.total_files > 0:
            # 批量处理模式
            if pbar is None:
                pbar = tqdm(
                    total=progress.total_files,
                    desc="处理中",
                    unit="file",
                    ncols=100
                )
            
            pbar.n = progress.processed_files
            pbar.set_description(f"{progress.message} | {progress.current_file}")
            pbar.refresh()
            
            if progress.status in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
                pbar.close()
        else:
            # 单文件处理模式
            desc = f"{progress.stage.value}: {progress.message}"
            if progress.current_file:
                desc = f"{progress.current_file} | {desc}"
            
            print(f"\r{desc}", end="", flush=True)
    
    return progress_callback


def cmd_process(args):
    """处理命令"""
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = load_config(args.config)
    
    # 覆盖配置
    if args.no_ocr:
        config["pipeline"]["ocr_enabled"] = False
    if args.no_watermark:
        config["pipeline"]["remove_watermark"] = False
    if args.watermark:
        config["pipeline"]["remove_watermark"] = True
    if args.ocr_language:
        config["pipeline"]["ocr_language"] = args.ocr_language
    if args.convert_method:
        config["pipeline"]["convert_method"] = args.convert_method
    
    # 创建进度回调
    progress_callback = create_progress_bar()
    
    # 创建流水线
    pipeline = create_pipeline(
        config=config.get("pipeline", {}),
        progress_callback=progress_callback
    )
    
    # 处理文件
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else None
    
    if input_path.is_file():
        # 单文件处理
        if not output_path:
            output_path = input_path.parent / f"{input_path.stem}.docx"
        
        logger.info(f"处理文件：{input_path}")
        result = pipeline.process_single(input_path, output_path)
        
        if result.success:
            print(f"\n✅ 处理完成！")
            print(f"   输出：{result.output_file}")
            print(f"   耗时：{result.duration_seconds:.2f}秒")
            print(f"   阶段：{', '.join([s.value for s in result.stages_completed])}")
        else:
            print(f"\n❌ 处理失败：{result.error_message}")
            sys.exit(1)
    
    elif input_path.is_dir():
        # 批量处理
        if not output_path:
            output_path = input_path.parent / f"{input_path.name}_output"
        
        logger.info(f"批量处理目录：{input_path}")
        results = pipeline.process_batch(
            input_path,
            output_path,
            file_pattern=args.pattern
        )
        
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        print(f"\n✅ 批量处理完成！")
        print(f"   成功：{success_count}/{total_count}")
        print(f"   输出目录：{output_path}")
        
        if success_count < total_count:
            print(f"\n失败文件:")
            for r in results:
                if not r.success:
                    print(f"   - {r.input_file.name}: {r.error_message}")
    
    else:
        logger.error(f"输入路径不存在：{input_path}")
        sys.exit(1)


def cmd_init(args):
    """初始化配置命令"""
    config_path = Path(args.output) if args.output else Path(__file__).parent / "config.json"
    
    default_config = {
        "version": "1.0.0",
        "app_name": "PDF Converter Pro",
        "organization": "影诺办",
        "pipeline": {
            "remove_watermark": False,
            "watermark_method": "auto",
            "ocr_enabled": True,
            "ocr_engine": "ocrmypdf",
            "ocr_language": "chi_sim+eng",
            "convert_method": "paddleocr",
            "convert_fallback_methods": ["pdf2docx"],
            "preserve_format": True,
            "max_recovery_attempts": 2,
            "cleanup_temp": True
        },
        "ocr": {
            "engine": "ocrmypdf",
            "language": "chi_sim+eng",
            "dpi": 300,
            "deskew": True,
            "clean": True
        },
        "converter": {
            "default_method": "paddleocr",
            "preserve_images": True,
            "preserve_tables": True,
            "preserve_layout": True
        },
        "watermark": {
            "enabled": False,
            "method": "auto",
            "ai_model": "iopaint"
        },
        "paths": {
            "default_input_dir": "",
            "default_output_dir": "",
            "temp_dir": "",
            "cache_dir": "",
            "log_dir": "logs"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/pdf_converter.log",
            "max_size_mb": 10,
            "backup_count": 5
        }
    }
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 配置文件已创建：{config_path}")


def cmd_info(args):
    """显示信息命令"""
    from core.ocr import OCREngineType
    from core.converter import ConvertMethod
    
    print("📊 PDF Converter Pro - 系统信息\n")
    
    print("支持的 OCR 引擎:")
    for engine in OCREngineType:
        print(f"  - {engine.value}")
    
    print("\n支持的转换方法:")
    for method in ConvertMethod:
        print(f"  - {method.value}")
    
    print("\n支持的 OCR 语言:")
    print("  - chi_sim: 简体中文")
    print("  - chi_tra: 繁体中文")
    print("  - eng: 英文")
    print("  - chi_sim+eng: 中英文混合")
    print("  - chi_tra+eng: 繁体中文 + 英文")
    
    print("\n去水印方法:")
    print("  - auto: 自动检测")
    print("  - opencv: OpenCV 传统方法")
    print("  - iopaint: AI 智能去除")
    
    print("\n📦 版本信息:")
    print("  - 版本：1.0.0")
    print("  - 组织：影诺办")
    print("  - GitHub: https://github.com/zjgzcc/pdf-converter-pro")


def cmd_check(args):
    """检查依赖命令"""
    import subprocess
    
    print("🔍 检查系统依赖...\n")
    
    checks = [
        ("Python", sys.version.split()[0]),
        ("OCRmyPDF", None),
        ("Tesseract", None),
        ("PyMuPDF", None),
        ("PaddleOCR", None),
    ]
    
    for name, version in checks:
        if version:
            print(f"✅ {name}: {version}")
        else:
            # 尝试检查
            try:
                if name == "OCRmyPDF":
                    result = subprocess.run(
                        ["ocrmypdf", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        print(f"✅ {name}: {result.stdout.strip()}")
                    else:
                        print(f"❌ {name}: 未安装")
                elif name == "Tesseract":
                    result = subprocess.run(
                        ["tesseract", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        print(f"✅ {name}: {result.stdout.splitlines()[0]}")
                    else:
                        print(f"❌ {name}: 未安装")
                else:
                    print(f"⚠️  {name}: 待检查")
            except FileNotFoundError:
                print(f"❌ {name}: 未安装")
            except Exception as e:
                print(f"⚠️  {name}: 检查失败 ({e})")
    
    print("\n💡 提示：使用 'pip install -r requirements.txt' 安装 Python 依赖")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog="pdf-converter-pro",
        description="PDF Converter Pro - OCR + 去水印 + WORD 转换",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s process input.pdf                    # 处理单个文件
  %(prog)s process ./pdfs -o ./output          # 批量处理目录
  %(prog)s process input.pdf --no-ocr          # 跳过 OCR
  %(prog)s process input.pdf --watermark       # 启用去水印
  %(prog)s init                                # 初始化配置文件
  %(prog)s info                                # 显示系统信息
  %(prog)s check                               # 检查依赖

GitHub: https://github.com/zjgzcc/pdf-converter-pro
组织：影诺办
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # process 命令
    process_parser = subparsers.add_parser(
        "process",
        help="处理 PDF 文件",
        description="处理单个 PDF 文件或批量处理目录"
    )
    process_parser.add_argument(
        "input",
        help="输入文件路径或目录"
    )
    process_parser.add_argument(
        "-o", "--output",
        help="输出文件路径或目录"
    )
    process_parser.add_argument(
        "-c", "--config",
        help="配置文件路径"
    )
    process_parser.add_argument(
        "-p", "--pattern",
        default="*.pdf",
        help="文件匹配模式 (默认：*.pdf)"
    )
    process_parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="跳过 OCR 处理"
    )
    process_parser.add_argument(
        "--no-watermark",
        action="store_true",
        help="跳过去水印"
    )
    process_parser.add_argument(
        "--watermark",
        action="store_true",
        help="启用去水印"
    )
    process_parser.add_argument(
        "--ocr-language",
        help="OCR 语言 (默认：chi_sim+eng)"
    )
    process_parser.add_argument(
        "--convert-method",
        choices=["paddleocr", "pdf2docx", "pymupdf"],
        help="转换方法"
    )
    process_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别"
    )
    process_parser.add_argument(
        "--log-file",
        help="日志文件路径"
    )
    process_parser.set_defaults(func=cmd_process)
    
    # init 命令
    init_parser = subparsers.add_parser(
        "init",
        help="初始化配置文件",
        description="创建默认配置文件"
    )
    init_parser.add_argument(
        "-o", "--output",
        help="配置文件输出路径"
    )
    init_parser.set_defaults(func=cmd_init)
    
    # info 命令
    info_parser = subparsers.add_parser(
        "info",
        help="显示系统信息",
        description="显示支持的引擎、方法和版本信息"
    )
    info_parser.set_defaults(func=cmd_info)
    
    # check 命令
    check_parser = subparsers.add_parser(
        "check",
        help="检查系统依赖",
        description="检查 OCR 引擎和其他依赖是否已安装"
    )
    check_parser.set_defaults(func=cmd_check)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # 执行命令
    args.func(args)


if __name__ == "__main__":
    main()
