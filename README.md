# ESP32 AI 开发项目

使用 AI 辅助开发的 ESP32 创意项目集合，涵盖智能家居、传感器、摄像头等方向。

> **开发板**: 普中 ESP32 (ESP32-WROOM-32)  
> **作者**: Kevin Ten  
> **创建日期**: 2026 年 3 月

---

## 📁 项目结构

```
esp32-ai-projects/
├── projects/              # 具体项目（各自独立）
│   ├── smart-home/        # ✅ 智能家居控制
│   ├── weather-station/   # ✅ 气象站（含模拟器）
│   ├── voice-control/     # ✅ 声音/拍手控制
│   ├── gesture-control/   # ✅ 手势识别控制
│   └── ai-camera/         # ✅ ESP32-CAM 网络摄像头
├── components/            # 可复用组件库
│   ├── pin-config.h       # 普中 ESP32 引脚定义
│   ├── wifi-manager/      # WiFi 管理
│   ├── oled-display/      # OLED 显示
│   ├── sensor-utils/      # 传感器工具（DHT22）
│   └── button-handler/    # 按钮处理
├── docs/                  # 文档与指南
└── .vscode/               # VSCode 配置
```

---

## 🛠️ 项目一览

| 项目 | 难度 | 所需硬件 | 状态 | 核心功能 |
|------|------|----------|------|---------|
| [智能家居控制](projects/smart-home/) | ⭐⭐ | ESP32, 继电器×4, OLED | ✅ 完成 | Web控制台, 4路继电器, **MQTT+HA**, JSON API |
| [气象站](projects/weather-station/) | ⭐⭐ | ESP32, DHT22, OLED | ✅ 完成 | 温湿度, Web展示, NTP时间 |
| [声音/拍手控制](projects/voice-control/) | ⭐⭐ | ESP32, MAX9814麦克风 | ✅ 完成 | 拍手识别, 设备控制, 波形显示 |
| [手势识别控制](projects/gesture-control/) | ⭐⭐⭐ | ESP32, APDS-9960 | ✅ 完成 | 手势方向识别, PWM调光, 设备控制 |
| [AI 摄像头](projects/ai-camera/) | ⭐⭐⭐⭐ | ESP32-CAM | ✅ 完成 | MJPEG视频流, 截图, Web控制 |
| [IR 红外遥控](projects/ir-blaster/) | ⭐⭐ | ESP32, IR LED, VS1838B | ✅ 完成 | 学码/发射, **空调/电视控制**, MQTT |
| [RF 433MHz 网关](projects/rf-gateway/) | ⭐⭐ | ESP32, 433MHz收发模块 | ✅ 完成 | 学码/发射, **接管市售插座**, MQTT+HA |

---

## 🚀 快速开始

### 环境要求

- **VSCode** + [PlatformIO 插件](https://platformio.org/install/ide?install=vscode)
- **Python 3.8+**（PlatformIO 依赖）
- **USB 驱动**：CH340/CP2102（根据你的 ESP32 板）

### 开发流程

```bash
# 1. 克隆项目
git clone <仓库地址>
cd esp32-ai-projects

# 2. 进入要开发的项目
cd projects/smart-home

# 3. 修改 WiFi 配置（编辑 src/main.cpp）
# 将 YOUR_WIFI_SSID 和 YOUR_WIFI_PASSWORD 改为你的网络

# 4. 编译并上传
pio run --target upload

# 5. 查看串口日志（115200 波特率）
pio device monitor
```

---

## 📡 项目详情

### 智能家居控制 (`projects/smart-home/`)

**功能**: 通过 WiFi Web 控制台管理家中的灯光、风扇、窗帘、插座。

- 手机/电脑浏览器直接控制，无需 App
- 4 路继电器独立开关
- OLED 实时显示设备状态
- GPIO35 按钮本地切换
- RESTful JSON API（可接入 HomeAssistant）

**访问方式**: 上传后在串口查看 IP，浏览器访问 `http://<IP>`

---

### 气象站 (`projects/weather-station/`)

**功能**: 实时采集温湿度并展示。

- DHT22 传感器采集温度、湿度、体感温度
- OLED 本地显示 + NTP 时间同步
- Web 仪表盘，支持 `/data` JSON 接口
- Python 模拟器（无硬件也可测试）

**普中专用版**: 使用 `platformio_puzhong.ini` 配置

---

### 声音/拍手控制 (`projects/voice-control/`)

**功能**: 通过拍手次数控制家电。

- MAX9814 麦克风采集环境声音
- 拍手模式识别（1次=灯光, 2次=风扇, 3次=全关）
- OLED 实时音量波形显示
- 蜂鸣器操作确认

**调试技巧**: 用 PlatformIO 的 Serial Plotter 可视化音量波形

---

### 手势识别控制 (`projects/gesture-control/`)

**功能**: 在空中挥手控制设备。

- APDS-9960 传感器，识别上/下/左/右手势
- 向上/向下：LED 亮度渐增/渐减（256级 PWM）
- 向左/向右：切换灯光/风扇继电器
- OLED 显示识别结果

**注意**: APDS-9960 仅接 3.3V，不可接 5V！

---

### AI 摄像头 (`projects/ai-camera/`)

**功能**: 将 ESP32-CAM 变成 WiFi 网络摄像头。

- MJPEG 视频流（VGA ~15fps）
- Web 控制台：调节分辨率、画质、亮度
- 一键截图下载
- LED 闪光灯控制
- 可嵌入其他网页的视频流 URL

**烧录注意**: IO0 必须接 GND 才能进入下载模式！

---

## 🔧 通用组件库

所有项目可复用的组件（`components/` 目录）：

| 组件 | 说明 | 默认引脚 |
|------|------|---------|
| `pin-config.h` | 普中 ESP32 引脚总定义 | — |
| `wifi-manager` | WiFi 连接管理 | — |
| `oled-display` | SSD1306 OLED 封装 | SDA:21, SCL:22 |
| `sensor-utils` | DHT22 传感器封装 | GPIO4 |
| `button-handler` | 按钮消抖+单双击长按 | GPIO35 |

---

## 📚 文档

| 文档 | 内容 |
|------|------|
| [**智能家居调研报告**](docs/smart-home-research.md) | ESP32接入智能家居6大方案对比、选型指南 |
| [硬件连接指南](docs/guides/hardware-setup.md) | 引脚图、接线说明 |
| [环境搭建指南](docs/setup-guide.md) | PlatformIO 安装配置 |
| [固件烧录指南](docs/upload-guide.md) | 上传方法与常见问题 |
| [AI 开发流程](docs/guides/ai-development.md) | 使用 AI 辅助开发的最佳实践 |
| [引脚配置文档](docs/puzhong-esp32-config.md) | 普中 ESP32 专用说明 |

---

## ⚡ 引脚快查表

```
普中 ESP32 常用引脚分配：

I2C:     SDA=21, SCL=22
OLED:    SDA=21, SCL=22 (I2C地址 0x3C)
DHT22:   DATA=4
按钮:    GPIO35（仅输入）
继电器:  GPIO26, 27, 14, 12
PWM LED: GPIO13
蜂鸣器:  GPIO25
板载LED: GPIO2

⚠️ 禁用引脚：GPIO6-11（Flash）
⚠️ WiFi时避免：ADC2引脚（GPIO0,2,4,12-15）
⚠️ 仅输入：GPIO34-39
```

---

## 🤖 AI 开发提示

与 AI 协作开发 ESP32 的建议：

1. **描述硬件**: 说明你使用的具体模块型号和引脚连接
2. **分步实现**: 先实现基础功能（点灯），再添加复杂功能（网络）
3. **提供错误**: 把编译错误或串口报错完整提供给 AI 分析
4. **代码审查**: 让 AI 解释生成代码的每个部分
5. **测试验证**: 每完成一个模块立即测试

---

## 📎 参考资源

- [ESP32 官方文档](https://docs.espressif.com/projects/esp-idf/en/latest/)
- [PlatformIO 文档](https://docs.platformio.org/en/latest/)
- [ESP32 Arduino 核心](https://github.com/espressif/arduino-esp32)
- [Adafruit SSD1306 库](https://github.com/adafruit/Adafruit_SSD1306)
- [SparkFun APDS-9960 库](https://github.com/sparkfun/SparkFun_APDS-9960_Sensor_Arduino_Library)

---

**作者**: Kevin Ten  
**最后更新**: 2026 年 3 月
