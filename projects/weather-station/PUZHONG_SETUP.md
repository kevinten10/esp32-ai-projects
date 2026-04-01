# 普中 ESP32 配置总结

## ✅ 已完成的配置调整

### 1. 引脚定义

| 组件 | 原配置 | 普中配置 | 说明 |
|------|--------|----------|------|
| DHT22 | GPIO 4 | GPIO 4 | ✅ 不变，推荐使用 |
| OLED SDA | GPIO 21 | GPIO 21 | ✅ I2C 标准引脚 |
| OLED SCL | GPIO 22 | GPIO 22 | ✅ I2C 标准引脚 |
| LED | - | GPIO 2 | ➕ 新增板载 LED |

### 2. 新增功能

| 功能 | 说明 |
|------|------|
| 🟢 板载 LED | GPIO 2，状态指示 |
| 🔄 双 I2C 地址 | 自动检测 0x3C/0x3D |
| 📶 WiFi 状态灯 | 快闪=未连接，慢闪=已连接 |
| 🌡️ 温度图标 | 高温显示 [H]，低温显示 [C] |

### 3. 文件列表

| 文件 | 说明 |
|------|------|
| `src/main_puzhong.cpp` | 普中 ESP32 主程序 |
| `simulator/weather_station_puzhong.py` | PC 模拟器（普中版） |
| `simulator/run_puzhong.bat` | 模拟器启动脚本 |
| `platformio_puzhong.ini` | PlatformIO 配置 |
| `README_puzhong.md` | 项目说明 |
| `docs/puzhong-esp32-config.md` | 普中 ESP32 配置文档 |

### 4. 模拟器功能

普中版模拟器新增：
- ✅ LED 状态指示（模拟 GPIO 2）
- ✅ LED 控制按钮（点亮/熄灭）
- ✅ 引脚配置显示
- ✅ 普中版本标识

## 🚀 使用方式

### PC 模拟测试（已启动）
```bash
cd simulator
run_puzhong.bat
```

### 上传到开发板
```bash
# 使用普中配置编译上传
pio run -e puzhong-esp32 --target upload

# 或使用默认配置
pio run --target upload
```

## 📋 普中 ESP32 引脚图

```
        普中 ESP32 开发板
    ┌─────────────────────────┐
    │  USB 接口               │
    │                         │
    │  TX0 (GPIO 1)    RX0 (GPIO 3)
    │  GPIO 0        GPIO 2 (LED) 🟢
    │  GPIO 4 (DHT)  GPIO 5 (SS)
    │  GPIO 12       GPIO 13
    │  GPIO 14       GPIO 15
    │  GPIO 16       GPIO 17
    │  GPIO 18 (SCK) GPIO 19 (MISO)
    │  GPIO 21 (SDA) GPIO 22 (SCL) ← I2C
    │  GPIO 23 (MOSI)
    │                         │
    │  [BOOT]  [RESET]        │
    └─────────────────────────┘
```

## ⚙️ PlatformIO 配置

```ini
[env:puzhong-esp32]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
upload_speed = 921600
upload_port = COM3

lib_deps = 
    adafruit/Adafruit SSD1306
    adafruit/DHT sensor library
    ...

build_flags = 
    -D BOARD_NAME=\"PZ-ESP32\"
    -D DHT_PIN=4
    -D OLED_SDA=21
    -D OLED_SCL=22
    -D LED_PIN=2
```

## 📊 对比

| 项目 | 通用版 | 普中版 |
|------|--------|--------|
| 引脚配置 | 标准 | 针对普中优化 |
| LED 指示 | ❌ | ✅ GPIO 2 |
| I2C 地址 | 0x3C | 0x3C/0x3D 自动 |
| 模拟器 | ✅ | ✅ 增强版 |
| 状态显示 | 基本 | 详细 |

---

**配置已完成！模拟器已启动，可以开始测试了！** 🎉
