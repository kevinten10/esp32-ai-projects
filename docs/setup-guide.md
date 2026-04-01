# ESP32 开发环境配置清单

## ✅ 必需软件

### 1. Python 3.8+
- [ ] 已安装
- [ ] 已添加到 PATH
- 验证：`python --version`

### 2. PlatformIO
- [ ] 已安装（VSCode 插件 或 pip）
- 验证：`pio --version`

### 3. USB 转串口驱动
- [ ] CP2102 或 CH340 驱动已安装
- 验证：插入 ESP32 后，设备管理器中出现 COM 端口

### 4. VSCode（推荐）
- [ ] 已安装
- [ ] PlatformIO IDE 插件已安装

---

## 🔧 安装命令（Windows）

### 安装 Python
从 https://www.python.org/downloads/ 下载安装

### 安装 PlatformIO
```bash
pip install platformio
```

### 安装 VSCode 插件（命令行方式）
```bash
code --install-extension platformio.platformio-ide
```

---

## 📋 验证步骤

### 1. 检查 Python
```bash
python --version
# 输出：Python 3.x.x
```

### 2. 检查 PlatformIO
```bash
pio --version
# 输出：PlatformIO Core, version x.x.x
```

### 3. 检查串口设备
插入 ESP32 后：
```bash
pio device list
```
应显示类似：
```
COM3 - Silicon Labs CP210x USB to UART Bridge
```

### 4. 首次编译测试
```bash
cd projects/weather-station
pio run
```

---

## ⚠️ 常见问题

### Q1: `pio` 命令找不到
**解决**：重新安装 PlatformIO，或手动添加路径到环境变量：
```
C:\Users\你的用户名\.platformio\penv\Scripts
```

### Q2: 上传失败 - 找不到 COM 端口
**解决**：
1. 检查 USB 线是否支持数据传输（有些仅充电）
2. 重新安装 USB 驱动
3. 在 Device Manager 中查看 COM 端口号

### Q3: 编译慢
**解决**：首次编译会下载工具链和库，耐心等待。后续编译会快很多。

### Q4: VSCode 中 PlatformIO 插件加载失败
**解决**：
1. 卸载插件
2. 删除 `C:\Users\你的用户名\.platformio`
3. 重新安装插件

---

## 📦 项目依赖库

无需手动下载！PlatformIO 会在首次编译时自动安装：

- `bblanchon/ArduinoJson@^6.21.3`
- `adafruit/Adafruit SSD1306@^2.5.7`
- `adafruit/DHT sensor library@^2.1.5`
- 等

---

## 🚀 快速开始

完成上述配置后：

1. 修改 `projects/weather-station/src/main.cpp` 中的 WiFi 配置
2. 连接 ESP32 到电脑
3. 运行：`cd projects/weather-station && pio run --target upload`
4. 打开串口监视器：`pio device monitor`
