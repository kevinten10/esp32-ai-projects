# 普中 ESP32 开发板配置说明

## 普中 ESP32 开发板特点

普中 ESP32 开发板（Practical Electronics ESP32）是一款常用的 ESP32 开发板，具有以下特点：

### 主要规格
- **芯片**: ESP32-WROOM-32
- **Flash**: 4MB
- **USB 转串口**: CP2102
- **工作电压**: 3.3V
- **输入电压**: 5V (通过 USB 或 VIN 引脚)

### 引脚定义

#### 电源引脚
| 引脚 | 功能 | 说明 |
|------|------|------|
| VIN | 5V 输入 | 外部电源输入 |
| 3V3 | 3.3V 输出 | 最大输出 500mA |
| GND | 地 | 接地 |

#### GPIO 引脚
| GPIO | 功能 | 注意事项 |
|------|------|----------|
| GPIO 0 | BOOT 模式 | 下拉进入下载模式 |
| GPIO 1 | TX0 | 调试串口 |
| GPIO 3 | RX0 | 调试串口 |
| GPIO 4 | ADC/DAC | 推荐用于传感器 |
| GPIO 5 | SS/ADC | SPI 片选 |
| GPIO 12 | ADC | |
| GPIO 13 | ADC | |
| GPIO 14 | ADC/DAC | |
| GPIO 15 | ADC | |
| GPIO 16 | RX2 | |
| GPIO 17 | TX2 | |
| GPIO 18 | SCK | SPI 时钟 |
| GPIO 19 | MISO | SPI 数据输入 |
| GPIO 21 | SDA | I2C 数据 |
| GPIO 22 | SCL | I2C 时钟 |
| GPIO 23 | MOSI | SPI 数据输出 |
| GPIO 25 | DAC1 | |
| GPIO 26 | DAC2 | |
| GPIO 32 | ADC | |
| GPIO 33 | ADC | |
| GPIO 34 | ADC ONLY | 仅输入 |
| GPIO 35 | ADC ONLY | 仅输入 |
| GPIO 36 | ADC ONLY | 仅输入 |
| GPIO 39 | ADC ONLY | 仅输入 |

#### 板载 LED
- **GPIO 2**: 板载 LED（部分型号）

### I2C 接口
普中 ESP32 的 I2C 默认引脚：
- **SDA**: GPIO 21
- **SCL**: GPIO 22

### SPI 接口
普中 ESP32 的 SPI 默认引脚：
- **SCK**: GPIO 18
- **MISO**: GPIO 19
- **MOSI**: GPIO 23
- **CS**: GPIO 5

---

## 气象站项目 - 普中 ESP32 配置

### 硬件连接

#### DHT22 传感器
```
DHT22     普中 ESP32
VCC   ->  3V3
GND   ->  GND
DATA  ->  GPIO 4 (加 10k 上拉电阻)
```

#### OLED 显示屏 (SSD1306)
```
OLED      普中 ESP32
VCC   ->  3V3 (或 5V)
GND   ->  GND
SCL   ->  GPIO 22
SDA   ->  GPIO 21
```

#### 按键（可选）
```
按键      普中 ESP32
一端  ->  GPIO 15
另一端 ->  GND
```

---

## 注意事项

### 1. 下载模式
如果上传失败，需要进入下载模式：
1. 按住 **BOOT** 按钮
2. 按 **EN/RESET** 按钮
3. 松开 **BOOT** 按钮
4. 上传代码

### 2. GPIO 限制
- **GPIO 34-39**: 仅可用作输入（无内部上拉）
- **GPIO 6-11**: 连接内部 Flash，不建议使用
- **GPIO 1**: 启动时会输出调试信息

### 3. 电源考虑
- 传感器使用 3.3V 供电
- OLED 可使用 3.3V 或 5V（根据模块规格）
- 大电流设备使用外部电源

### 4. ADC 特性
- 输入范围：0-3.3V
- 分辨率：12 位（0-4095）
- 使用衰减可扩展范围

---

## PlatformIO 配置

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
upload_speed = 921600
upload_port = COM3
```

---

## 常见问题

### Q1: 无法上传代码
**解决**: 进入下载模式（按住 BOOT 后按 RESET）

### Q2: OLED 不显示
**解决**: 
- 检查 I2C 引脚（21=SDA, 22=SCL）
- 尝试地址 0x3D（有些 OLED 是 0x3D 而非 0x3C）

### Q3: DHT22 读数不稳定
**解决**:
- 确保 DATA 引脚有 10k 上拉电阻
- 使用较短的连接线
- 避免靠近干扰源
