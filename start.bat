@echo off
chcp 65001 >nul
echo 🦎 PDF Converter Pro 启动中...
echo.

cd /d "%~dp0"

if not exist "venv\" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
)

echo [2/3] 激活虚拟环境...
call venv\Scripts\activate.bat

if not exist "venv\Lib\site-packages\PyQt6" (
    echo [3/3] 安装依赖（首次启动需要几分钟）...
    pip install -r requirements.txt -q
)

echo.
echo ✅ 启动 GUI 界面...
echo.

python main.py

pause
