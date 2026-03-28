@echo off
chcp 65001 >nul
title PDF Converter Pro - 设置开机自启
echo ========================================
echo 设置开机自动启动
echo ========================================
echo.

:: 设置工作目录
cd /d "%~dp0"

:: 创建启动脚本（放在启动文件夹）
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_NAME=PDF-Converter-Pro.lnk"

:: 使用 PowerShell 创建快捷方式
echo 创建开机启动项...
powershell -Command "$
    WshShell = New-Object -ComObject WScript.Shell;
    $Shortcut = $WshShell.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%');
    $Shortcut.TargetPath = '%CD%\start_service.bat';
    $Shortcut.WorkingDirectory = '%CD%';
    $Shortcut.WindowStyle = 7;  # 最小化窗口
    $Shortcut.Save();
    Write-Host '快捷方式创建成功';
"

if errorlevel 1 (
    echo [错误] 创建启动项失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo 开机自启设置完成！
echo ========================================
echo.
echo 下次开机时，服务将自动启动
echo 启动文件夹: %STARTUP_DIR%
echo.
pause
