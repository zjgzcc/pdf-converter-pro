@echo off
chcp 65001 >nul
title PDF Converter Pro - GPU 服务

echo ========================================
echo PDF Converter Pro - 启动服务
echo ========================================
echo.

:: 设置工作目录
cd /d "%~dp0"

:: 检查虚拟环境
if not exist ".venv311\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在，请先运行 install.bat 安装
    pause
    exit /b 1
)

:: 清理临时目录
echo [1/3] 清理临时文件...
if exist "%TEMP%\pdf_converter_pro" (
    rmdir /s /q "%TEMP%\pdf_converter_pro" 2>nul
)
mkdir "%TEMP%\pdf_converter_pro\output" 2>nul

:: 设置 CUDA 环境变量
echo [2/3] 配置 GPU 环境...
set "CUDA_PATH=%CD%\.venv311\Lib\site-packages\nvidia\cuda_runtime\bin"
set "PATH=%CUDA_PATH%;%PATH%"

:: 启动服务
echo [3/3] 启动 Web 服务...
echo.
echo 服务启动后，请访问: http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

.venv311\Scripts\python.exe web_server.py

:: 如果服务异常退出，暂停显示错误
if errorlevel 1 (
    echo.
    echo [错误] 服务异常退出
    pause
)
