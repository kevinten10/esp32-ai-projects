@echo off
REM 项目初始化脚本 (Windows)

echo === ESP32 AI 项目初始化 ===

REM 检查 PlatformIO
where pio >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误：未找到 PlatformIO，请先安装
    echo pip install platformio
    pause
    exit /b 1
)

echo PlatformIO 已安装

REM 初始化项目
set PROJECT_DIR=%1
if "%PROJECT_DIR%"=="" (
    echo 用法：init.bat ^<项目目录^>
    echo 可用项目:
    dir /b projects\
    pause
    exit /b 1
)

if not exist "projects\%PROJECT_DIR%" (
    echo 错误：项目 %PROJECT_DIR% 不存在
    pause
    exit /b 1
)

echo 初始化项目：%PROJECT_DIR%
cd /d "projects\%PROJECT_DIR%"
pio init
pio lib install

echo 初始化完成!
echo 运行：cd projects\%PROJECT_DIR% ^&^& pio run
pause
