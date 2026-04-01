# ESP32 硬件连接指南

> **适用开发板**: 普中 ESP32 (ESP32-WROOM-32) / ESP32 DevKit V1  
> **PlatformIO 环境**: `esp32dev`

---

## 📌 引脚分配总览

### 核心引脚配置

| 功能类别 | 引脚 | 说明 |
|---------|------|------|
| **I2C** | SDA: 21, SCL: 22 | OLED、传感器默认总线 |
| **SPI (VSPI)** | MOSI: 23, MISO: 19, SCK: 18, CS: 5 | 显示屏、Flash 等 |
| **UART1** | TX: 17, RX: 16 | 串口通信 |
| **ADC1** | 32-39 | ✅ 推荐，不受 WiFi 影响 |
| **PWM** | 2, 4, 12-15 | LED、舵机控制 |

### ⚠️ 引脚使用注意事项

| 引脚 | 限制 | 建议 |
|------|------|------|
| GPIO 6-11 | ❌ 连接内部 Flash，不可用 | 避免使用 |
| GPIO 34-39 | ⚠️ 仅输入，无内部上拉 | 适合按钮、传感器输入 |
| GPIO 0, 2, 4, 12-15 | ⚠️ ADC2，WiFi 启用时冲突 | WiFi+ADC 同时使用时避免 |
| GPIO 0 | ⚠️ 启动模式选择 | 下拉电阻进入下载模式 |
| GPIO 2 | ⚠️ 板载 LED | 启动时需浮空 |

---

## 🔌 常用模块连接

### OLED (SSD1306 I2C)

```
OLED      ESP32
────      ─────
VCC   ->  3.3V
GND   ->  GND
SCL   ->  GPIO 22
SDA   ->  GPIO 21
```

**代码使用**:
```cpp
#include <oled_display.h>
OLEDDisplay display(OLED_SDA, OLED_SCL);  // 默认 21, 22
```

### DHT22 温湿度传感器

```
DHT22   ESP32
────    ─────
VCC   ->  3.3V
GND   ->  GND
DATA  ->  GPIO 4 (加 10k 上拉电阻)
```

**代码使用**:
```cpp
#include <sensor_utils.h>
SensorUtils sensor(4);  // DHT 默认引脚
```

### 按钮

```
按钮      ESP32
────    ─────
一端  ->  GPIO 35 (或 34)
另一端 ->  GND
```

**代码使用**:
```cpp
#include <button_handler.h>
ButtonHandler button(35);  // 使用仅输入引脚
```

### 继电器模块

```
继电器   ESP32
────    ─────
VCC   ->  5V 或 3.3V
GND   ->  GND
IN    ->  GPIO 26 (或其他 GPIO)
```

### 蜂鸣器

```
蜂鸣器    ESP32
────    ─────
VCC   ->  3.3V
GND   ->  GND
IO    ->  GPIO 2 (通过三极管驱动)
```

### APDS-9960 手势传感器

```
APDS-9960  ESP32
────────   ─────
VCC   ->  3.3V
GND   ->  GND
SCL   ->  GPIO 22
SDA   ->  GPIO 21
INT   ->  GPIO 23 (可选)
```

### 麦克风 (MAX9814)

```
MAX9814  ESP32
───────  ─────
VCC   ->  3.3V
GND   ->  GND
OUT   ->  GPIO 36 (VP, ADC1_CH0)
GAIN  ->  根据需求配置
```

---

## ⚡ 电源注意事项

1. **逻辑电平**: ESP32 GPIO 是 **3.3V** 电平，不兼容 5V
2. **电流限制**: 
   - 每个 GPIO 最大 **40mA**
   - 总电流不超过 **1200mA**
3. **外部供电**: 继电器、电机等大功率模块使用外部电源
4. **ADC 输入范围**: 0-3.3V，超过会损坏芯片

---

## 🔧 调试接口

### USB 转 TTL 调试

```
ESP32       USB-TTL
────        ───────
TX0 (GPIO 1) -> RX
RX0 (GPIO 3) -> TX
GND       -> GND
```

### 下载模式

按住 **BOOT 按钮**，然后按 **RST 按钮**，进入固件下载模式。

---

## 📋 开发板对比

| 型号 | 核心 | GPIO 数量 | 特点 | 推荐项目 |
|------|------|----------|------|---------|
| **ESP32 DevKit V1** | dual-core Tensilica | 30+ | 通用型，性价比高 | 所有项目 |
| ESP32-CAM | dual-core | 16 | 带摄像头接口 | AI 摄像头 |
| ESP32-S3 | dual-core Xtenso | 45 | AI 指令集，更多 GPIO | 语音/手势识别 |
| ESP32-C3 | single-core RISC-V | 22 | 低功耗，成本低 | 电池供电项目 |

---

## 📁 项目组件引用

所有组件的默认引脚配置见：
```
components/pin-config.h
```

在代码中引用：
```cpp
#include <pin-config.h>

// 使用预定义引脚
pinMode(OLED_SDA, OUTPUT);
pinMode(BUTTON_1, INPUT);
```

---

**最后更新**: 2026 年 3 月  
**作者**: Kevin Ten
