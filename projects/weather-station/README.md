# ESP32 气象站

实时监测环境温湿度，支持 OLED 显示和 Web 查看。

## ✅ 环境已配置

- ✅ Python 3.12.10
- ✅ PlatformIO Core 6.1.19
- ✅ 所有依赖库已安装

## 硬件清单

| 组件 | 数量 | 备注 |
|------|------|------|
| ESP32 开发板 | 1 | 任意型号 |
| DHT22 传感器 | 1 | 温湿度一体 |
| SSD1306 OLED | 1 | 128x64, I2C |
| 10k 电阻 | 1 | DHT22 上拉 |
| 面包板 + 杜邦线 | 若干 | |

## 硬件连接

### DHT22 连接
```
DHT22     ESP32
VCC   ->  3.3V
GND   ->  GND
DATA  ->  GPIO 4 (加 10k 上拉电阻到 VCC)
```

### OLED 连接
```
OLED      ESP32
VCC   ->  3.3V
GND   ->  GND
SCL   ->  GPIO 22
SDA   ->  GPIO 21
```

## 快速开始

### 1. 修改 WiFi 配置

编辑 `src/main.cpp`，修改以下配置：

```cpp
const char* WIFI_SSID = "你的 WiFi 名称";
const char* WIFI_PASSWORD = "你的 WiFi 密码";
```

### 2. 上传到 ESP32

```bash
cd projects/weather-station
pio run --target upload
```

或使用快捷脚本：
```bash
upload.bat
```

### 3. 查看串口输出

```bash
pio device monitor
```

### 4. 访问 Web 界面

1. 打开串口监视器，查看 ESP32 的 IP 地址
2. 在浏览器访问 `http://<ESP32_IP>/`
3. JSON API: `http://<ESP32_IP>/data`

## 功能说明

### OLED 显示
- 实时显示时间
- 温度（°C）
- 湿度（%）
- 体感温度
- WiFi 状态

### Web 界面
- 响应式设计，支持手机/电脑
- 自动刷新（30 秒）
- JSON API 数据接口

### 传感器数据
- 更新频率：2 秒
- 温度范围：-40~80°C (±0.5°C)
- 湿度范围：0~100%RH (±2%)

## 效果预览

```
┌─────────────────────────┐
│ 14:30:25        WiFi:OK │
│                         │
│  25.3    60            │
│  C       %              │
│                         │
│ Heat: 26.1C            │
└─────────────────────────┘
```

## Web 界面预览

```
┌─────────────────────────────────────┐
│     ESP32 Weather Station           │
│                                     │
│  ┌─────────┐  ┌─────────┐          │
│  │ 25.3 C  │  │  60 %   │          │
│  │Temperature│  │Humidity │          │
│  └─────────┘  └─────────┘          │
│                                     │
│  Time: 2026-03-13 14:30:25         │
│  [ Refresh ]                        │
└─────────────────────────────────────┘
```

## 常见问题

### Q: OLED 不显示
A: 检查 I2C 接线，确认 SDA/SCL 是否正确。

### Q: 传感器读数异常
A: 检查 DATA 引脚是否连接 10k 上拉电阻。

### Q: WiFi 连接失败
A: 确认 SSID 和密码正确，ESP32 仅支持 2.4GHz WiFi。

### Q: 找不到 COM 端口
A: 安装 USB 驱动（CP2102 或 CH340）。

## 下一步扩展

可以尝试让 AI 帮你添加：
- 📊 历史数据记录（SPIFFS/SD 卡）
- 📱 MQTT 上报（Home Assistant 集成）
- 🔔 温湿度超标报警
- 🌙 夜间自动关闭显示
- 📈 温度变化曲线图

---
**作者**: Kevin Ten  
**创建日期**: 2026 年 3 月
