#!/usr/bin/env python3
"""
PDF Converter Pro - PyInstaller 打包脚本
⚡ 雷影【执行】一键打包为 EXE

用法：python scripts/build_exe.py
输出：dist/PDF Converter Pro.exe
"""

import subprocess
import sys
import shutil
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent


def build_exe():
    """使用 PyInstaller 打包为单文件 EXE"""
    
    print("⚡ PDF Converter Pro - EXE 打包")
    print("=" * 60)
    
    # 输出目录
    dist_dir = ROOT_DIR / "dist"
    build_dir = ROOT_DIR / "build"
    spec_file = ROOT_DIR / "pdf_converter.spec"
    
    # 清理旧构建
    if dist_dir.exists():
        print("🧹 清理旧构建...")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()
    
    # 创建 spec 文件
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('core', 'core'),
        ('ui', 'ui'),
    ],
    hiddenimports=[
        'ui.main_window',
        'ui.file_preview_widget',
        'ui.history_manager',
        'core.converter',
        'core.ocr',
        'core.pipeline',
        'core.watermark',
        'fitz',
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'cv2',
        'numpy',
        'PIL',
        'paddleocr',
        'paddle',
        'pdf2docx',
        'ocrmypdf',
        'docx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pytest',
    ],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    spec_file.write_text(spec_content, encoding='utf-8')
    print(f"✅ 创建 spec 文件：pdf_converter.spec")
    
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
                
                # 创建便携版目录
                create_portable_version(dist_dir, exe_path)
                
                return True
            else:
                print("⚠️  未找到生成的 EXE 文件")
                return False
        else:
            print(f"\n❌ 打包失败！")
            print(f"错误输出：{result.stderr[:500] if result.stderr else '未知错误'}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n❌ 打包超时（10 分钟）")
        return False
    except Exception as e:
        print(f"\n❌ 打包异常：{e}")
        return False


def create_portable_version(dist_dir: Path, exe_path: Path):
    """创建便携版目录结构"""
    
    portable_dir = ROOT_DIR / "pdf-converter-pro-portable"
    
    print(f"\n📦 创建便携版...")
    
    # 清理旧便携版
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # 复制 EXE
    portable_exe = portable_dir / exe_path.name
    shutil.copy2(exe_path, portable_exe)
    
    # 创建使用说明
    readme_content = f'''# PDF Converter Pro - 便携版
⚡ 雷影【执行】开箱即用版本

## 📦 文件说明

- **{exe_path.name}**: 主程序（双击运行）
- **README.txt**: 使用说明

## 🚀 使用方法

### 方法 1: 双击运行
直接双击 `{exe_path.name}` 启动图形界面

### 方法 2: 命令行运行
```cmd
{exe_path.name} --help
```

## 📋 功能说明

✅ PDF 转 Word（DOCX）
✅ PDF OCR 文字识别
✅ 批量处理
✅ 图形界面操作

## ⚠️ 注意事项

1. 首次运行可能需要几秒初始化
2. 确保输出目录有写入权限
3. 大文件处理时间较长，请耐心等待

## 🆘 故障排除

### 程序无法启动
- 检查是否被杀毒软件拦截
- 尝试以管理员身份运行

### 转换失败
- 确保 PDF 文件未损坏
- 检查磁盘空间是否充足

## 📞 技术支持

如有问题，请联系开发团队。

---
版本：MVP 0.1.0 | 团队：影诺办 | ⚡ 雷影【执行】
'''
    
    (portable_dir / "README.txt").write_text(readme_content, encoding='gbk')
    
    # 创建快捷方式批处理
    shortcut_content = f'''@echo off
chcp 65001 >nul
start "" "{exe_path.name}"
'''
    
    (portable_dir / "启动程序.bat").write_text(shortcut_content, encoding='gbk')
    
    print(f"✅ 便携版创建完成：{portable_dir}")
    print(f"   包含：{exe_path.name}, README.txt, 启动程序.bat")


def main():
    """主函数"""
    print()
    print("⚡ " + "=" * 58)
    print("⚡  PDF Converter Pro - 打包工具")
    print("⚡  ⚡ 雷影【执行】PyInstaller 打包")
    print("⚡ " + "=" * 58)
    print()
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✅ PyInstaller 已安装：v{PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装")
        print("   请运行：pip install pyinstaller")
        sys.exit(1)
    
    # 打包
    success = build_exe()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 打包完成！")
        print("=" * 60)
        print("\n📂 EXE 输出：dist/PDF Converter Pro.exe")
        print("📦 便携版：pdf-converter-pro-portable/")
        print("\n💡 提示：便携版可直接复制到另一台电脑运行")
    else:
        print("\n❌ 打包失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
