# ESP32 AI 开发项目

使用 AI 辅助开发的 ESP32 创意项目集合。

## 📁 项目结构

```
esp32-ai-projects/
├── projects/           # 具体项目
│   ├── smart-home/     # 智能家居控制
│   ├── weather-station/# 气象站
│   ├── voice-control/  # 语音控制
│   ├── gesture-control/# 手势识别
│   └── ai-camera/      # AI 摄像头
├── components/         # 可复用组件
│   ├── wifi-manager/   # WiFi 管理
│   ├── oled-display/   # OLED 显示
│   ├── sensor-utils/   # 传感器工具
│   └── button-handler/ # 按钮处理
├── utils/              # 工具脚本
├── docs/               # 文档
└── .vscode/            # VSCode 配置
```

## 🚀 快速开始

### 环境要求

- **PlatformIO** (推荐) 或 **ESP-IDF**
- **Python 3.8+**
- **VSCode** + PlatformIO 插件

### 开发流程

1. **选择项目**: 从 `projects/` 中选择一个项目开始
2. **配置硬件**: 根据 `docs/guides/hardware-setup.md` 连接硬件
3. **AI 辅助开发**: 使用 AI 生成代码、调试和优化
4. **烧录测试**: 编译并烧录到 ESP32

## 🛠️ 可用项目

| 项目 | 难度 | 所需硬件 | 状态 |
|------|------|----------|------|
| 智能家居控制 | ⭐⭐ | ESP32, 继电器模块 | 📝 待开发 |
| 气象站 | ⭐⭐ | ESP32, DHT22, OLED | 📝 待开发 |
| 语音控制 | ⭐⭐⭐ | ESP32, 麦克风模块 | 📝 待开发 |
| 手势识别 | ⭐⭐⭐ | ESP32, APDS-9960 | 📝 待开发 |
| AI 摄像头 | ⭐⭐⭐⭐ | ESP32-CAM | 📝 待开发 |

## 🤖 AI 开发提示

与 AI 协作时的建议：

1. **明确需求**: 详细描述功能需求和硬件配置
2. **分步开发**: 将大任务拆分为小模块
3. **代码审查**: 让 AI 解释生成的代码
4. **调试协助**: 提供错误日志让 AI 帮助分析

## 📚 资源

- [ESP32 官方文档](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [PlatformIO 文档](https://docs.platformio.org/en/latest/)
- [ESP32 Arduino 核心](https://github.com/espressif/arduino-esp32)

---
**作者**: Kevin Ten  
**创建日期**: 2026 年 3 月
