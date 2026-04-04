# ESP32-CAM AI 摄像头

基于 ESP32-CAM 模块的网络摄像头，支持 MJPEG 视频流、截图和远程参数调节。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| MJPEG 视频流 | 浏览器实时查看，支持多分辨率 |
| 静态截图 | 一键下载 JPEG 图片 |
| Web 控制台 | 调节画质、亮度、对比度、分辨率 |
| LED 闪光灯 | 软件控制板载 LED |
| 双服务器 | 端口80（控制）+ 端口81（视频流）独立运行 |
| PSRAM 优化 | 自动检测 PSRAM 并使用最优缓冲配置 |

---

## 硬件要求

| 组件 | 说明 |
|------|------|
| ESP32-CAM | **AI Thinker** 版本（其他版本需修改引脚） |
| USB-TTL 模块 | 用于烧录（ESP32-CAM 无板载 USB-Serial） |
| 5V 电源 | 需要稳定 5V（摄像头功耗较大，不可用 USB 限流） |
| OV2640 摄像头 | AI Thinker 板通常已附带 |

---

## 烧录说明

ESP32-CAM **没有板载 USB 转串口芯片**，需要外部 USB-TTL 模块。

### 接线（烧录模式）

```
USB-TTL 模块        ESP32-CAM
TX              --> U0R (GPIO3)
RX              --> U0T (GPIO1)
GND             --> GND
5V              --> 5V

ESP32-CAM           跳线
IO0             --> GND  ⚠️ 进入下载模式必须！
```

### 烧录步骤

1. 按上表接好线，**IO0 接 GND**
2. 插入 USB-TTL 到电脑
3. 确认串口号（设备管理器）
4. 修改 `platformio.ini` 中的串口号
5. 执行上传：

```bash
cd projects/ai-camera
pio run --target upload --upload-port COM5
```

6. 上传完成后，**断开 IO0 和 GND 的连线**
7. 按 ESP32-CAM 上的 RST（复位）按钮
8. 打开串口监视器（115200），查看 IP 地址

---

## 快速开始

### 1. 修改 WiFi 配置

编辑 `src/main.cpp`：

```cpp
const char* WIFI_SSID = "你的WiFi名称";
const char* WIFI_PASSWORD = "你的WiFi密码";
```

### 2. 上传固件

```bash
pio run --target upload
```

### 3. 查看串口输出

```
=== ESP32-CAM AI 摄像头 ===
摄像头初始化成功
连接 WiFi: MyWiFi
..........
WiFi 已连接！
==========================================
控制台:   http://192.168.1.105
视频流:   http://192.168.1.105:81/stream
截图:     http://192.168.1.105/capture
==========================================
```

### 4. 访问 Web 控制台

浏览器打开 `http://192.168.1.105`（替换为实际 IP）。

---

## Web 访问接口

| 地址 | 说明 |
|------|------|
| `http://<IP>/` | Web 控制台（视频+参数调节） |
| `http://<IP>:81/stream` | 纯 MJPEG 视频流（可直接嵌入其他页面） |
| `http://<IP>/capture` | 下载当前帧为 JPEG 图片 |
| `http://<IP>/control` | POST 接口，调节摄像头参数 |

### 控制接口参数

```bash
# 设置画质（4=最好, 63=最差）
curl -X POST http://192.168.1.105/control -d "quality=15"

# 设置亮度（-2 到 2）
curl -X POST http://192.168.1.105/control -d "brightness=1"

# 设置分辨率（5=VGA, 6=SVGA, 7=XGA, 9=SXGA, 10=UXGA）
curl -X POST http://192.168.1.105/control -d "framesize=5"

# 开启闪光灯
curl -X POST http://192.168.1.105/control -d "flash=1"

# 组合参数
curl -X POST http://192.168.1.105/control -d "quality=20&brightness=1&framesize=6"
```

---

## 分辨率说明

| 代码 | 分辨率 | 帧率 | 适用场景 |
|------|--------|------|---------|
| VGA (5) | 640×480 | ~15fps | 流畅监控（推荐） |
| SVGA (6) | 800×600 | ~10fps | 较清晰监控 |
| XGA (7) | 1024×768 | ~7fps | 高清监控 |
| SXGA (9) | 1280×1024 | ~4fps | 需要 PSRAM |
| UXGA (10) | 1600×1200 | ~2fps | 静态拍照 |

---

## 嵌入视频流到网页

```html
<!-- 在其他网页中嵌入 ESP32-CAM 视频流 -->
<img src="http://192.168.1.105:81/stream" width="640" height="480">
```

---

## 常见问题

**Q: 上传失败，提示 "Failed to connect to ESP32"？**  
A: 
1. 确认 IO0 已接 GND
2. 确认 USB-TTL 的 TX-RX 是否交叉连接（TX->U0R, RX->U0T）
3. 尝试在上传时按住 RST 按钮直到上传开始
4. 检查串口号是否正确

**Q: 摄像头初始化失败（0x105 错误）？**  
A: 摄像头连接松动，重新插紧摄像头排线。确认使用 AI Thinker 板，其他板型引脚定义不同。

**Q: 视频流卡顿？**  
A: 降低分辨率（改用 VGA），提高 JPEG quality 值（如从10改到20），确保 WiFi 信号强。

**Q: 图像画面颠倒？**  
A: 修改代码中翻转设置：

```cpp
s->set_vflip(s, 1);   // 垂直翻转
s->set_hmirror(s, 1); // 水平镜像
```

**Q: 访问 IP 只能看到一小段时间就断了？**  
A: ESP32-CAM 的 Web 服务器单线程，每次只能服务一个客户端的视频流。打开多个标签页会导致断流，关闭多余标签页即可。

---

## 与 Home Assistant 集成

```yaml
# configuration.yaml - 添加摄像头实体
camera:
  - platform: generic
    name: "ESP32-CAM"
    still_image_url: "http://192.168.1.105/capture"
    stream_source: "http://192.168.1.105:81/stream"
    verify_ssl: false
```

---

## 扩展开发建议

1. **人脸检测**: ESP32-CAM 内置 face_detection 模型（需要足够内存）
2. **二维码识别**: 使用 quirc 库解码 QR Code
3. **运动检测**: 比较连续帧的差异触发报警
4. **SD 卡录制**: AI Thinker 板有 SD 卡槽，可将视频写入 SD 卡
5. **Telegram 推送**: 运动检测时通过 WiFi 发送图片到 Telegram Bot

---

**作者**: Kevin Ten  
**最后更新**: 2026-03
