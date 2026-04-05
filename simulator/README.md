# ESP32 项目模拟器

无需任何硬件，在 PC 上体验所有 ESP32 项目的完整功能。

---

## 快速启动

### 方式一：统一演示平台（推荐）

**Windows**：双击 `run_demo.bat` 或运行：

```bash
cd simulator
python esp32_demo.py
```

包含 6 个标签页：气象站、智能家居、语音控制、手势识别、IR遥控、RF网关。

**快捷键**：
- `空格` — 模拟拍手（语音控制 Tab）
- `↑↓←→` — 模拟手势（手势识别 Tab）
- `Ctrl+W` — 退出

**内置 HTTP API**：`http://localhost:8080`

---

### 方式二：独立模拟器

每个项目都有独立的模拟器，可单独运行：

| 项目 | 命令 | Web 控制台 |
|------|------|-----------|
| 气象站 | `python projects/weather-station/simulator/weather_station.py` | — |
| 智能家居 | `python projects/smart-home/simulator/smart_home_demo.py` | http://localhost:8081 |
| 语音控制 | `python projects/voice-control/simulator/voice_demo.py` | — |
| 手势识别 | `python projects/gesture-control/simulator/gesture_demo.py` | — |
| IR 遥控 | `python projects/ir-blaster/simulator/ir_demo.py` | http://localhost:8082 |
| RF 网关 | `python projects/rf-gateway/simulator/rf_demo.py` | http://localhost:8083 |

---

## 依赖

所有模拟器仅使用 Python 标准库（tkinter），无需安装额外依赖。

> 如果系统缺少 tkinter，运行 `pip install tk` 或安装 python3-tk 包。

---

## API 端点

统一演示平台启动后，以下 API 可用：

```
GET http://localhost:8080/weather          → 气象站数据
GET http://localhost:8080/home/state       → 智能家居状态
GET http://localhost:8080/home/toggle?id=0 → 切换继电器
GET http://localhost:8080/voice/state      → 语音控制状态
GET http://localhost:8080/gesture/state    → 手势控制状态
GET http://localhost:8080/ir/ac            → 空调状态
GET http://localhost:8080/rf/devices       → RF 设备列表
```

---

## 功能说明

### 气象站模拟器
- 实时温度/湿度/体感温度显示
- 温度历史折线图
- 手动调节环境参数
- JSON API 输出

### 智能家居模拟器
- 4 路继电器开关控制
- MQTT 发布日志模拟
- DHT22 温湿度数据同步
- PIR 人体感应随机触发
- Web 控制台（浏览器访问）

### 语音控制模拟器
- 空格键模拟拍手
- 实时音量波形绘制
- 1/2/3 次拍手分别控制灯光/风扇/全关
- 蜂鸣器提示反馈

### 手势识别模拟器
- 方向键模拟 APDS-9960 手势
- PWM 亮度条动画
- 继电器设备控制
- 接近传感器模拟

### IR 遥控模拟器
- 美的空调控制面板
- 温度/模式/风速切换
- 红外学码模拟
- 已学码一键发射

### RF 网关模拟器
- 433MHz 学码（模拟3秒）
- 设备管理（按房间分组）
- 手动 RF 码发射
- 后台随机 RF 接收模拟

---

**作者**: Kevin Ten
