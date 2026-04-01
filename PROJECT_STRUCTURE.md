# ESP32 AI 开发项目 - 结构说明

> **作者**: Kevin Ten  
> **开发板**: 普中 ESP32 (ESP32-WROOM-32)  
> **PlatformIO 环境**: `esp32dev`

---

## 📁 完整目录结构

```
esp32-ai-projects/
│
├── 📄 platformio.ini          # PlatformIO 配置 (所有项目共享)
├── 📄 README.md               # 项目说明
│
├── 📂 components/             # 🔧 可复用组件库
│   ├── 📄 README.md           # 组件使用说明
│   ├── 📄 pin-config.h        # ⭐ 引脚配置文件 (普中 ESP32)
│   │
│   ├── 📂 oled-display/       # OLED 显示组件 (SSD1306)
│   │   ├── oled_display.h
│   │   └── oled_display.cpp
│   │
│   ├── 📂 button-handler/     # 按钮处理组件
│   │   ├── button_handler.h
│   │   └── button_handler.cpp
│   │
│   ├── 📂 sensor-utils/       # 传感器工具组件 (DHT22)
│   │   ├── sensor_utils.h
│   │   └── sensor_utils.cpp
│   │
│   └── 📂 wifi-manager/       # WiFi 连接管理
│       ├── wifi_manager.h
│       └── wifi_manager.cpp
│
├── 📂 projects/               # 📝 具体项目
│   ├── 📂 ai-camera/          # AI 摄像头项目
│   ├── 📂 gesture-control/    # 手势识别项目
│   ├── 📂 smart-home/         # 智能家居项目
│   ├── 📂 voice-control/      # 语音控制项目
│   └── 📂 weather-station/    # 气象站项目
│
├── 📂 docs/                   # 📚 文档
│   ├── 📄 setup-guide.md      # 环境搭建指南
│   ├── 📄 upload-guide.md     # 固件烧录指南
│   ├── 📄 prompt-cheatsheet.md # AI 开发提示词
│   │
│   └── 📂 guides/             # 详细指南
│       ├── 📄 hardware-setup.md  # ⭐ 硬件连接指南
│       └── 📄 ai-development.md  # AI 辅助开发流程
│
├── 📂 utils/                  # 🔨 工具脚本
│   └── (待添加)
│
└── 📂 .vscode/                # VSCode 配置
    ├── 📄 launch.json         # 调试配置
    └── 📄 settings.json       # 工作区设置
```

---

## 🔑 核心文件说明

### 配置文件

| 文件 | 作用 | 说明 |
|------|------|------|
| `platformio.ini` | 构建配置 | 定义开发板、上传速度、依赖库 |
| `components/pin-config.h` | 引脚定义 | ⭐ 普中 ESP32 引脚配置总表 |

### 组件库

| 组件 | 功能 | 默认引脚 |
|------|------|---------|
| `oled-display` | OLED 显示 | SDA:21, SCL:22 |
| `button-handler` | 按钮检测 | 35 |
| `sensor-utils` | 温湿度传感器 | 4 |
| `wifi-manager` | WiFi 连接 | 无 |

### 文档

| 文档 | 内容 |
|------|------|
| `docs/guides/hardware-setup.md` | 硬件连接图、引脚分配 |
| `docs/setup-guide.md` | PlatformIO 环境搭建 |
| `docs/upload-guide.md` | 固件上传/烧录方法 |
| `components/README.md` | 组件使用示例 |

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装 PlatformIO (VSCode 扩展)
# 或访问 https://platformio.org/
```

### 2. 连接硬件

参考 `docs/guides/hardware-setup.md` 连接传感器和模块。

### 3. 选择项目

在 `projects/` 中选择一个项目开始开发。

### 4. 编译上传

```bash
# 在项目目录下执行
pio run --target upload
```

---

## 📋 开发规范

### 引脚使用原则

1. **优先使用预定义引脚**: 引用 `pin-config.h` 中的宏
2. **避免冲突引脚**: GPIO 6-11 (Flash), ADC2 (WiFi 冲突)
3. **输入专用引脚**: GPIO 34-39 仅支持输入

### 组件开发原则

1. **可复用**: 组件应独立、可移植
2. **默认配置**: 提供合理的默认引脚
3. **可覆盖**: 允许通过构造函数自定义引脚

---

## 🔗 相关资源

- [ESP32 官方文档](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [PlatformIO 文档](https://docs.platformio.org/en/latest/)
- [ESP32 Arduino 核心](https://github.com/espressif/arduino-esp32)

---

**最后更新**: 2026 年 3 月  
**作者**: Kevin Ten
