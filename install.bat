@echo off
chcp 65001 >nul
title PDF Converter Pro - 安装部署
echo ========================================
echo PDF Converter Pro - 一键安装
echo ========================================
echo.

:: 设置工作目录
cd /d "%~dp0"

:: 检查 Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.11
    echo 下载地址: https://www.python.org/downloads/release/python-3119/
    pause
    exit /b 1
)
python --version
echo.

:: 创建虚拟环境
echo [2/4] 创建虚拟环境...
if exist ".venv311" (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv .venv311
    echo 虚拟环境创建完成
)
echo.

:: 安装依赖
echo [3/4] 安装 GPU 依赖（约 1GB，请耐心等待）...
.venv311\Scripts\pip.exe install -r requirements-gpu.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo.

:: 验证 GPU
echo [4/4] 验证 GPU 可用性...
.venv311\Scripts\python.exe -c "from core.rapid_ocr import detect_device; d=detect_device(); print('GPU:', d['gpu'], '-', d.get('gpu_name','N/A'))"
echo.

echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 启动服务请运行: start_service.bat
echo.
pause
