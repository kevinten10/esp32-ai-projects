#!/bin/bash
# 项目初始化脚本

echo "=== ESP32 AI 项目初始化 ==="

# 检查 PlatformIO
if ! command -v pio &> /dev/null; then
    echo "错误：未找到 PlatformIO，请先安装"
    echo "pip install platformio"
    exit 1
fi

echo "PlatformIO 已安装"

# 初始化项目
PROJECT_DIR=$1
if [ -z "$PROJECT_DIR" ]; then
    echo "用法：./init.sh <项目目录>"
    echo "可用项目:"
    ls -1 projects/
    exit 1
fi

if [ ! -d "projects/$PROJECT_DIR" ]; then
    echo "错误：项目 $PROJECT_DIR 不存在"
    exit 1
fi

echo "初始化项目：$PROJECT_DIR"
cd "projects/$PROJECT_DIR"
pio init
pio lib install

echo "初始化完成!"
echo "运行：cd projects/$PROJECT_DIR && pio run"
