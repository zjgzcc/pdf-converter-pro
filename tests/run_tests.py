"""
测试运行脚本
🧪 青影【测试】负责

使用方法:
    python tests/run_tests.py           # 运行所有测试
    python tests/run_tests.py -v        # 详细输出
    python tests/run_tests.py --report  # 生成测试报告
"""

import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime


def run_tests(verbose: bool = False):
    """运行 pytest 测试"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    # 构建 pytest 命令
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "--tb=short",  # 简短的 traceback
    ]
    
    if verbose:
        cmd.append("-v")
    
    print(f"[TEST] 开始运行测试...")
    print(f"[TEST] 测试目录：{tests_dir}")
    print(f"[TEST] 命令：{' '.join(cmd)}")
    print("-" * 60)
    
    # 运行 pytest
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    # 输出结果
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def generate_report(output_dir: Path = None):
    """生成测试报告"""
    if output_dir is None:
        output_dir = Path(__file__).parent / "reports"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 运行 pytest 并生成 HTML 报告
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = output_dir / f"test_report_{timestamp}.html"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        f"--html={report_file}",
        "--self-contained-html",
        "-v"
    ]
    
    print(f"[REPORT] 生成测试报告...")
    print(f"[REPORT] 报告路径：{report_file}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    print(result.stdout)
    
    # 生成 JSON 摘要
    summary_file = output_dir / f"test_summary_{timestamp}.json"
    summary = {
        "timestamp": timestamp,
        "success": result.returncode == 0,
        "report_html": str(report_file),
        "exit_code": result.returncode
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] 报告已生成：{report_file}")
    print(f"[OK] 摘要已保存：{summary_file}")
    
    return result.returncode == 0


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    project_root = Path(__file__).parent.parent
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ 测试文件不存在：{test_path}")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v"
    ]
    
    print(f"[TEST] 运行测试：{test_file}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF Converter Pro 测试运行器")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--report", action="store_true", help="生成 HTML 测试报告")
    parser.add_argument("--test", type=str, help="运行特定测试文件")
    parser.add_argument("--create-samples", action="store_true", help="创建测试样本文件")
    
    args = parser.parse_args()
    
    # 创建样本文件
    if args.create_samples:
        from create_samples import create_placeholder_files
        create_placeholder_files()
        return
    
    # 运行特定测试
    if args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    
    # 生成报告
    if args.report:
        success = generate_report()
        sys.exit(0 if success else 1)
    
    # 默认：运行所有测试
    success = run_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
