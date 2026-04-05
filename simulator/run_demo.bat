@echo off
chcp 65001 >nul
title ESP32 AI Projects - 统一演示平台
echo.
echo   ╔══════════════════════════════════════════════╗
echo   ║   ESP32 AI Projects - 统一演示平台          ║
echo   ║   无需硬件，在 PC 上体验所有项目功能        ║
echo   ╚══════════════════════════════════════════════╝
echo.
echo   启动中...
echo.

cd /d "%~dp0"
python esp32_demo.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo   [错误] Python 未安装或启动失败
    echo   请确保已安装 Python 3.8+ : https://python.org
    pause
)
