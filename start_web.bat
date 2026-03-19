@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo PDF Converter Pro - Web Server
echo ============================================
echo.
echo 正在启动 Web 服务器...
echo.
echo 访问地址：http://localhost:5000
echo.
echo 按 Ctrl+C 停止服务器
echo ============================================
echo.
C:\Python311\python.exe web_server.py
pause
