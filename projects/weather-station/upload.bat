@echo off
chcp 65001 >nul
echo ========================================
echo    ESP32 气象站 - 一键上传工具
echo ========================================
echo.

REM 检查配置
findstr /C:"YOUR_WIFI_SSID" src\main.cpp >nul
if %errorlevel% equ 0 (
    echo.
    echo [警告] 请先修改 src/main.cpp 中的 WiFi 配置！
    echo.
    echo   打开 src/main.cpp，修改第 22-23 行：
    echo   const char* WIFI_SSID = "你的 WiFi 名称";
    echo   const char* WIFI_PASSWORD = "你的 WiFi 密码";
    echo.
    pause
    exit /b 1
)

echo [1/4] 检查串口设备...
echo ----------------------------------------
pio device list
echo.

echo [2/4] 编译项目...
echo ----------------------------------------
pio run
if %errorlevel% neq 0 (
    echo.
    echo [错误] 编译失败！
    pause
    exit /b 1
)
echo.

echo [3/4] 上传到 ESP32...
echo ----------------------------------------
echo 请确保 ESP32 已通过 USB 连接到电脑
echo.
echo 如果看到 "Failed to connect" 错误：
echo   1. 按住 ESP32 上的 BOOT 按钮
echo   2. 按一下 RESET 按钮（或重新插拔 USB）
echo   3. 松开 BOOT 按钮
echo   4. 按任意键重试
echo.
pause

pio run --target upload
if %errorlevel% neq 0 (
    echo.
    echo [错误] 上传失败！
    echo.
    echo 解决方法：
    echo   1. 按住 ESP32 上的 BOOT 按钮
    echo   2. 按一下 RESET 按钮
    echo   3. 松开 BOOT 按钮
    echo   4. 重新运行此脚本
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    上传成功！
echo ========================================
echo.
echo [4/4] 打开串口监视器...
echo ----------------------------------------
echo 按 Ctrl+C 退出串口监视器
echo 在串口输出中查看 ESP32 的 IP 地址
echo.
echo 正在连接串口...
echo.

pio device monitor --baud 115200
