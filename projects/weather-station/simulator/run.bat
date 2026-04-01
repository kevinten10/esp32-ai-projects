@echo off
chcp 65001 >nul
echo ========================================
echo    ESP32 气象站 - PC 模拟器
echo ========================================
echo.
echo 正在启动模拟器...
echo.

python weather_station.py

if %errorlevel% neq 0 (
    echo.
    echo [错误] 启动失败！
    echo.
    echo 请确保已安装 Python
    echo 运行：pip install tkinter
    echo.
    pause
)
