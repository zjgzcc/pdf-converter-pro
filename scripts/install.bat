@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================
:: PDF Converter Pro - 一键安装脚本
:: ⚡ 雷影【执行】
:: ============================================

echo ⚡ ========================================================
echo ⚡  PDF Converter Pro - 一键安装脚本
echo ⚡  ⚡ 雷影【执行】快速部署
echo ⚡ ========================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.8+
    echo    下载地址：https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python 已安装
python --version
echo.

:: 检查 pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 pip，请检查 Python 安装
    pause
    exit /b 1
)

echo ✅ pip 已安装
echo.

:: 创建虚拟环境（可选）
echo [1/4] 创建虚拟环境...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ⚠️  虚拟环境创建失败，继续全局安装...
    ) else (
        echo ✅ 虚拟环境创建成功
    )
) else (
    echo ✅ 虚拟环境已存在
)
echo.

:: 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [2/4] 激活虚拟环境...
    call venv\Scripts\activate.bat
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  使用全局 Python 环境
)
echo.

:: 升级 pip
echo [3/4] 升级 pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip 已升级
echo.

:: 安装依赖
echo [4/4] 安装项目依赖...
echo    这可能需要几分钟...
echo.

if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo ⚠️  部分依赖安装失败，尝试安装核心依赖...
        echo.
        pip install PyQt6 PyMuPDF opencv-python numpy Pillow tqdm
    )
) else (
    echo ❌ 未找到 requirements.txt
    pause
    exit /b 1
)

echo.
echo ✅ 依赖安装完成
echo.

:: 验证安装
echo ============================================
echo 验证安装...
echo.

python -c "import fitz; print('✅ PyMuPDF:', fitz.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  PyMuPDF 未正确安装
)

python -c "import cv2; print('✅ OpenCV:', cv2.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  OpenCV 未正确安装
)

python -c "import PyQt6; print('✅ PyQt6 已安装')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  PyQt6 未正确安装
)

echo.
echo ============================================
echo 🎉 安装完成！
echo ============================================
echo.
echo 使用方法:
echo   1. 图形界面：python main.py
echo   2. 打包 EXE: python scripts/build_exe.py
echo   3. 运行测试：python tests/run_tests.py
echo.
echo 便携版打包:
echo   运行 python scripts/build_exe.py 后，
echo   会在 pdf-converter-pro-portable/ 目录生成便携版
echo.
echo ============================================
echo ⚡ 雷影【执行】| 影诺办
echo ============================================
echo.

pause
