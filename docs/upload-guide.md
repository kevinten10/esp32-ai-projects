# ESP32 连接和上传指南

## 📌 步骤 1: 连接硬件

### USB 连接
1. 使用 **USB 数据线** 连接 ESP32 和电脑
   - ⚠️ 确保是数据线，不是仅充电线
   - 如果手机能识别该数据线，通常可以使用

2. 检查连接
   - 打开设备管理器（Win+X → 设备管理器）
   - 展开 "端口 (COM 和 LPT)"
   - 应该看到 "Silicon Labs CP210x" 或 "CH340" 类似的设备

### 如果找不到设备

**情况 1: 完全没反应**
- 换一根 USB 线（必须是数据线）
- 换一个 USB 端口

**情况 2: 有未知设备**
- 需要安装 USB 驱动
- CP2102 驱动：https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
- CH340 驱动：http://www.wch.cn/downloads/CH341SER_ZIP.html

---

## 📌 步骤 2: 修改 WiFi 配置

打开 `src/main.cpp`，修改第 22-23 行：

```cpp
const char* WIFI_SSID = "你的 WiFi 名称";      // 改成你的 WiFi 名称
const char* WIFI_PASSWORD = "你的 WiFi 密码";  // 改成你的 WiFi 密码
```

---

## 📌 步骤 3: 上传代码

### 方法 A: 使用快捷脚本（推荐）

在项目目录双击运行：
```
upload.bat
```

### 方法 B: 手动命令

```bash
cd D:\projects\hardware\esp32-ai-projects\projects\weather-station
pio run --target upload
```

---

## 📌 步骤 4: 处理上传失败

### 常见错误：`Failed to connect to ESP32`

**解决方法 1: 手动进入下载模式**

1. 按住 ESP32 上的 **BOOT** 按钮
2. 按一下 **RESET** 按钮（或重新插拔 USB）
3. 松开 **BOOT** 按钮
4. 重新运行上传命令

**解决方法 2: 指定 COM 端口**

编辑 `platformio.ini`，添加上传端口：
```ini
upload_port = COM3
```

---

## 📌 步骤 5: 查看串口输出

上传成功后，打开串口监视器：

```bash
pio device monitor --baud 115200
```

或在上次上传后自动打开。

### 预期输出

```
=== ESP32 Weather Station ===
Init OLED... OK
Init DHT... OK
Connecting WiFi... ....
WiFi Connected!
IP: 192.168.1.100
Sync NTP... OK
Web server started
Temp: 25.3C, Humidity: 60.1%
```

---

## 📌 步骤 6: 访问 Web 界面

1. 从串口输出中记下 IP 地址（如 `192.168.1.100`）
2. 在浏览器访问：`http://192.168.1.100/`
3. 查看实时温湿度数据

---

## 🔧 常见问题

### Q1: 找不到 COM 端口
**解决**: 
1. 打开设备管理器
2. 查看是否有带黄色感叹号的设备
3. 安装对应的 USB 驱动

### Q2: 上传时出现 `Connection refused`
**解决**:
1. 关闭所有占用串口的程序（串口助手等）
2. 重新插拔 USB
3. 重新运行上传

### Q3: 上传成功但没有输出
**解决**:
1. 检查波特率是否正确（115200）
2. 检查接线（DHT22 和 OLED）
3. 按 ESP32 的 RESET 按钮

### Q4: OLED 不显示
**解决**:
1. 检查 I2C 接线（SDA=21, SCL=22）
2. 检查 OLED 供电（3.3V 或 5V）
3. 尝试修改地址（有些 OLED 是 0x3D）

---

## 📞 需要帮助？

在串口监视器中按 `Ctrl+C` 退出，然后：
1. 复制串口输出
2. 让 AI 分析错误原因

---

**祝你开发愉快！** 🚀
