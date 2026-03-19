#!/usr/bin/env python3
"""
PDF Converter Pro - 打包脚本
⚡ 雷影【执行】使用 PyInstaller 打包为 EXE

运行：python scripts/build.py
输出：dist/PDF Converter Pro.exe
"""

import subprocess
import sys
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


def build_exe():
    """使用 PyInstaller 打包为单文件 EXE"""
    
    print("🦎 PDF Converter Pro - EXE 打包")
    print("=" * 60)
    
    # 输出目录
    dist_dir = ROOT_DIR / "dist"
    build_dir = ROOT_DIR / "build"
    
    # 清理旧构建
    if dist_dir.exists():
        print("🧹 清理旧构建...")
        import shutil
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # PyInstaller 命令
    # 使用 main_lite.py 作为入口（轻量版，无 GUI 依赖）
    spec_file = ROOT_DIR / "pdf_converter.spec"
    
    # 创建 spec 文件
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main_lite.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'core.pipeline_lite',
        'core.converter',
        'core.ocr',
        'core.watermark',
        'fitz',
        'cv2',
        'numpy',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDF Converter Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    spec_file.write_text(spec_content, encoding='utf-8')
    print(f"✅ 创建 spec 文件：{spec_file.name}")
    
    # 执行 PyInstaller
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath", str(dist_dir),
        "--workpath", str(build_dir),
        "--specpath", str(ROOT_DIR),
        str(spec_file)
    ]
    
    print(f"\n🔨 执行 PyInstaller...")
    print(f"📁 输出目录：{dist_dir}")
    print(f"📝 Spec 文件：{spec_file.name}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        if result.returncode == 0:
            print("\n✅ 打包成功！")
            
            # 查找生成的 EXE
            exe_files = list(dist_dir.glob("*.exe"))
            if exe_files:
                exe_path = exe_files[0]
                print(f"\n📦 生成的 EXE: {exe_path.name}")
                print(f"📏 文件大小：{exe_path.stat().st_size / 1024 / 1024:.2f} MB")
                print(f"📂 位置：{exe_path}")
                
                # 创建使用说明
                create_readme(dist_dir, exe_path)
                
                return True
            else:
                print("⚠️  未找到生成的 EXE 文件")
                return False
        else:
            print(f"\n❌ 打包失败！")
            print(f"错误输出：{result.stderr[:500]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 打包超时（10 分钟）")
        return False
    except Exception as e:
        print(f"\n❌ 打包异常：{e}")
        return False


def create_readme(dist_dir: Path, exe_path: Path):
    """创建部署说明文件"""
    
    readme_content = f'''# PDF Converter Pro - 部署说明
⚡ 雷影【执行】快速部署指南

## 📦 打包信息

- **EXE 文件**: {exe_path.name}
- **文件大小**: {exe_path.stat().st_size / 1024 / 1024:.2f} MB
- **打包时间**: 2026-03-19
- **Python 版本**: {sys.version}

## 🚀 快速使用

### 方法 1: 直接运行 EXE
```bash
# 双击运行或命令行执行
"{exe_path.name}" --help
```

### 方法 2: 命令行使用
```bash
# 单个文件处理
"{exe_path.name}" input.pdf -o output_dir

# 批量处理目录
"{exe_path.name}" input_dir/ -o output_dir/

# 仅 OCR
"{exe_path.name}" input.pdf -o output_dir --ocr --no-word

# 仅转 WORD
"{exe_path.name}" input.pdf -o output_dir --no-ocr --word
```

## 📋 命令行参数

```
位置参数:
  input                 输入 PDF 文件或目录

选项:
  -o, --output OUTPUT   输出目录（必需）
  --ocr                 执行 OCR 识别（默认：启用）
  --word                转换为 WORD（默认：启用）
  --watermark           去除水印（默认：禁用）
  --lang LANG           OCR 语言（默认：chi_sim+eng）
  --help                显示帮助信息
```

## 📚 依赖说明

### 核心依赖（已打包）
- PyQt6 (GUI，可选)
- PyMuPDF (fitz)
- OpenCV (cv2)
- NumPy
- pdf2docx
- ocrmypdf (可选，需要单独安装 Tesseract)

### 可选依赖（需要单独安装）
如果需要使用完整功能，在目标机器上安装：

```bash
# Windows (需要管理员权限)
# 1. 安装 Tesseract OCR
# 下载：https://github.com/UB-Mannheim/tesseract/wiki
# 安装后添加到 PATH

# 2. 安装 Python 依赖
pip install ocrmypdf paddlepaddle paddleocr

# 3. 验证安装
ocrmypdf --version
paddleocr --help
```

## 🔧 故障排除

### 问题 1: 找不到 ocrmypdf
```
解决方案：跳过 OCR 或使用 --no-ocr 参数
```

### 问题 2: WORD 转换失败
```
解决方案：确保安装了 pdf2docx
pip install pdf2docx
```

### 问题 3: 去水印功能不可用
```
解决方案：MVP 版本暂不支持，后续版本会添加
```

## 📝 日志和调试

运行时有详细日志输出，如遇问题请：
1. 查看控制台输出
2. 检查输出目录是否可写
3. 确保输入文件存在且可访问

## 🦎 版本信息

- **版本**: MVP 0.1.0
- **团队**: 影诺办
- **执行**: ⚡ 雷影【执行】

---
快速部署 | 高效执行 | MVP 验证
'''
    
    readme_path = dist_dir / "DEPLOYMENT.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"\n📄 创建部署说明：{readme_path.name}")


def build_gui_version():
    """打包 GUI 版本（需要 PyQt6）"""
    
    print("\n" + "=" * 60)
    print("🎨 打包 GUI 版本（可选）")
    print("=" * 60)
    
    dist_gui = ROOT_DIR / "dist_gui"
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--windowed",  # 无控制台窗口
        "--name", "PDF Converter Pro GUI",
        "--distpath", str(dist_gui),
        "main.py"
    ]
    
    print("⚠️  注意：GUI 版本需要 PyQt6 完整环境")
    print("   如要打包，请确保已安装：pip install PyQt6")
    
    response = input("\n是否继续打包 GUI 版本？(y/n): ")
    if response.lower() != 'y':
        print("⏭️  跳过 GUI 版本打包")
        return
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            timeout=600
        )
        
        if result.returncode == 0:
            print("✅ GUI 版本打包成功！")
        else:
            print("❌ GUI 版本打包失败")
    except Exception as e:
        print(f"❌ GUI 打包异常：{e}")


def main():
    """主函数"""
    print()
    print("🦎 " + "=" * 58)
    print("🦎  PDF Converter Pro - 打包工具")
    print("🦎  ⚡ 雷影【执行】PyInstaller 打包")
    print("🦎 " + "=" * 58)
    print()
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安装：v{PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("   请运行：pip install pyinstaller")
        sys.exit(1)
    
    # 打包命令行版本
    success = build_exe()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 打包完成！")
        print("=" * 60)
        print("\n📂 查看输出目录：dist/")
        print("📄 部署说明：dist/DEPLOYMENT.md")
        print("\n💡 提示：可以在另一台电脑上测试运行")
    else:
        print("\n❌ 打包失败，请检查错误信息")
        sys.exit(1)
    
    # 可选：打包 GUI 版本
    # build_gui_version()


if __name__ == "__main__":
    main()
