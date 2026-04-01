# ESP32 气象站 - 普中 ESP32 版本

针对普中 ESP32 开发板优化的气象站项目。

## 📋 硬件配置

### 普中 ESP32 开发板
- **芯片**: ESP32-WROOM-32
- **Flash**: 4MB
- **USB 转串口**: CP2102
- **板载 LED**: GPIO 2

### 引脚配置

| 组件 | 引脚 | GPIO |
|------|------|------|
| DHT22 传感器 | DATA | GPIO 4 |
| OLED 显示屏 | SDA | GPIO 21 |
| OLED 显示屏 | SCL | GPIO 22 |
| 板载 LED | LED | GPIO 2 |

### 硬件连接图

```
普中 ESP32          DHT22
3V3        ----->   VCC
GND        ----->   GND
GPIO 4     ----->   DATA (加 10k 上拉电阻)

普中 ESP32          OLED
3V3        ----->   VCC
GND        ----->   GND
GPIO 22    ----->   SCL
GPIO 21    ----->   SDA
```

## 🚀 快速开始

### 方法 1: PC 模拟器（推荐先试用）

双击运行：
```
simulator/run_puzhong.bat
```

或命令行：
```bash
cd simulator
python weather_station_puzhong.py
```

### 方法 2: 上传到开发板

1. 修改 WiFi 配置（`src/main_puzhong.cpp` 第 28-29 行）
2. 连接 ESP32 到电脑
3. 编译上传：
```bash
pio run -e puzhong-esp32 --target upload
```

## 📊 功能特性

### 板载 LED 状态指示

| LED 状态 | 含义 |
|----------|------|
| 快闪 (0.5s) | WiFi 未连接 |
| 慢闪 (3s) | WiFi 已连接，正常运行 |
| 常亮 | 手动开启 |
| 常灭 | 手动关闭 |

### OLED 显示

- 实时时间显示
- 温度（大字体）
- 湿度（大字体）
- 体感温度
- WiFi 状态
- 温度状态图标（H=高温，C=低温）

### Web 服务器

访问 `http://<ESP32_IP>/` 查看：
- 实时温湿度
- 体感温度
- 时间戳
- 开发板信息

JSON API: `http://<ESP32_IP>/data`

```json
{
    "temperature": 25.3,
    "humidity": 60.5,
    "heatindex": 26.1,
    "time": "2026-03-13 14:30:25",
    "board": "PZ-ESP32",
    "wifi": true
}
```

## 🔧 编译选项

### PlatformIO 环境

| 环境 | 说明 |
|------|------|
| `puzhong-esp32` | 普中 ESP32（默认） |
| `esp32dev` | 通用 ESP32 |

### 使用不同环境

```bash
# 使用普中配置
pio run -e puzhong-esp32

# 使用通用配置
pio run -e esp32dev
```

## ⚠️ 注意事项

### 1. 下载模式
如果上传失败，需要进入下载模式：
1. 按住 **BOOT** 按钮
2. 按 **EN/RESET** 按钮
3. 松开 **BOOT** 按钮
4. 重新上传

### 2. OLED 地址
如果 OLED 不显示，尝试修改地址：
- 默认：`0x3C`
- 备用：`0x3D`

代码会自动尝试两个地址。

### 3. GPIO 限制
- **GPIO 34-39**: 仅可用作输入
- **GPIO 6-11**: 连接内部 Flash，不建议使用

## 📸 效果预览

### OLED 显示
```
┌─────────────────────────┐
│ 14:30:25      WiFi:OK   │
│                         │
│  25.3      60          │
│  C         %            │
│                         │
│ Heat: 26.1C       [H]  │
└─────────────────────────┘
```

### LED 状态
- 正常：🟢 慢闪（3 秒周期）
- 异常：🟢 快闪（0.5 秒周期）

## 🔍 串口输出

```
=== ESP32 气象站 (普中版) ===
Init OLED... OK (0x3C)
Init DHT... OK
Connecting WiFi... ....
WiFi Connected!
IP: 192.168.1.100
Sync NTP... OK
Web server started

=== Setup Complete ===

Temp: 25.3C, Humidity: 60.1%
Temp: 25.4C, Humidity: 59.8%
...
```

## 📁 文件结构

```
weather-station/
├── src/
│   ├── main.cpp              # 通用版本
│   └── main_puzhong.cpp      # 普中 ESP32 版本
├── simulator/
│   ├── weather_station.py    # 通用模拟器
│   ├── weather_station_puzhong.py  # 普中模拟器
│   └── run_puzhong.bat       # 启动脚本
├── platformio.ini            # 通用配置
├── platformio_puzhong.ini    # 普中配置
└── README_puzhong.md         # 本文档
```

## 🛠️ 故障排除

### 问题 1: 编译失败
**解决**: 确保使用正确的环境
```bash
pio run -e puzhong-esp32
```

### 问题 2: 上传失败
**解决**: 进入下载模式（按住 BOOT 后按 RESET）

### 问题 3: OLED 不显示
**解决**: 
- 检查接线（SDA=21, SCL=22）
- 尝试修改地址为 0x3D

### 问题 4: DHT22 读数 NaN
**解决**:
- 检查 DATA 引脚是否有 10k 上拉
- 检查供电电压（3.3V）

---

**普中 ESP32 版本 - 专为普中开发板优化！** 🎉
