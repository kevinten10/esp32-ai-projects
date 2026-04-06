# ESP32 烧录完全指南 - 从零开始

> 适用于：普中 ESP32 开发板 + Windows 系统

---

## 第一步：确认你的硬件

### 你需要准备的东西

| 序号 | 物品 | 说明 | 已有？ |
|------|------|------|--------|
| 1 | **ESP32 开发板** | 普中 ESP32 或兼容板 | ✅ |
| 2 | **USB 数据线** | Type-A 转 Type-C（或 Micro-USB） | ⚠️ 必须是**数据线**，不是充电线！ |
| 3 | **电脑** | Windows 10/11 | ✅ |

### 检查 USB 线是不是数据线

1. 用这根线连接 ESP32 和电脑
2. 打开 **设备管理器**（Win+X → 设备管理器）
3. 展开 **端口 (COM 和 LPT)**
4. 如果看到新增的 COM 口（如 `COM3`、`COM4`），说明是数据线 ✅
5. 如果什么都没出现 → 换一根线

---

## 第二步：安装 PlatformIO

你有两种方式，**选一种即可**：

### 方式 A：VSCode 插件（推荐，有图形界面）

```
1. 下载安装 VSCode：https://code.visualstudio.com/

2. 打开 VSCode

3. 按 Ctrl+Shift+X 打开扩展商店

4. 搜索 "PlatformIO"

5. 点击 "Install"（安装需要 2-5 分钟）

6. 安装完成后左侧会多一个 "外星人头像" 图标

7. 安装 USB 驱动（二选一或都装）：
   - CH340 驱动：http://www.wch.cn/downloads/CH341SER_EXE.html
   - CP2102 驱动：https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
```

### 方式 B：命令行（快速、轻量）

```powershell
# 打开 PowerShell 或 CMD，执行：
pip install platformio

# 验证安装
pio --version

# 如果提示 pio 不是命令，关闭重开终端再试
```

---

## 第三步：确认 COM 端口

```
1. 用 USB 线连接 ESP32 和电脑

2. 打开设备管理器 → 端口 (COM 和 LPT)

3. 你应该看到类似：
   ├── COM3  Silicon Labs CP210x
   └── COM4  USB-SERIAL CH340

4. 记住这个 COM 口编号（后面要用）
```

### 找不到 COM 口？

- 换一根 USB 线
- 换一个 USB 接口（台式机用背面的接口）
- 安装 CH340 和 CP2102 驱动
- 普中开发板通常用 CH340 芯片

---

## 第四步：修改代码中的 WiFi 配置

烧录前，必须先修改代码中的 WiFi 名称和密码。

以「智能家居」项目为例：

```
1. 打开文件：projects/smart-home/src/main.cpp

2. 找到文件开头这几行（大约第 45 行）：

   const char* WIFI_SSID     = "YOUR_WIFI_SSID";
   const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
   const char* MQTT_SERVER   = "192.168.1.20";

3. 修改为你的实际 WiFi 信息：

   const char* WIFI_SSSID    = "你家WiFi名称";
   const char* WIFI_PASS     = "你家WiFi密码";
   const char* MQTT_SERVER   = "";     ← 暂时不需要MQTT就留空

4. 保存文件（Ctrl+S）
```

每个项目都要改这个配置！位置都在 `src/main.cpp` 文件开头。

---

## 第五步：编译并烧录

### 方式 A：命令行烧录（最直接）

```powershell
# 打开终端，进入项目目录
cd "d:\projects\hardware\esp32-ai-projects\projects\smart-home"

# 第一次烧录会下载 ESP32 工具链（约 200MB，需要几分钟）
pio run --target upload
```

如果自动检测不到 COM 口，手动指定：

```powershell
pio run --target upload --upload-port COM3
#                                      ^^^^
#                          替换为你的实际 COM 口
```

### 方式 B：VSCode 界面烧录

```
1. VSCode 打开项目：
   文件 → 打开文件夹 → 选择 d:\projects\hardware\esp32-ai-projects

2. 底部状态栏找到这些图标：
   ✓ (编译)    → (烧录)    🔌 (串口监视器)

3. 点击 → 箭头图标 开始烧录

4. 底部终端会显示编译和烧录进度
```

### 烧录过程中发生了什么？

```
编译中...                    ← 把 .cpp 编译成 .bin 固件
正在连接...                   ← 通过串口连接 ESP32
写入中...  [=====>    ] 45%   ← 把固件写入 Flash
写入完成 100%                  ← 成功！
Hard resetting via RTS pin... ← ESP32 自动重启
```

---

## 第六步：查看运行日志

烧录完成后，打开串口监视器查看 ESP32 输出：

```powershell
# 命令行方式
pio device monitor

# 或指定波特率
pio device monitor -b 115200
```

### 正常输出示例

```
=== ESP32 智能家居 MQTT 版 ===
OLED 初始化成功
连接 WiFi: MyWiFi
.......
WiFi OK, IP: 192.168.1.100
Web 服务器已启动，端口 80
Web 控制台: http://192.168.1.100
```

**看到 IP 地址后，用手机浏览器打开这个 IP 就能控制了！**

---

## 常见问题排查

### ❌ 编译报错 "Unknown board ID 'esp32dev'"

```powershell
# 需要先安装 ESP32 平台
pio platform install espressif32
```

### ❌ 烧录报错 "Failed to connect to ESP32"

```
1. 按住板子上的 BOOT 键不放
2. 点击烧录按钮
3. 看到 "Connecting..." 后松开 BOOT
4. 如果还不行，按一下 EN/RST 键后重试
```

### ❌ "No serial device found"

```
1. 确认 USB 线已连接
2. 确认设备管理器中有 COM 端口
3. 手动指定端口：pio run --target upload --upload-port COM3
4. 安装 CH340 驱动
```

### ❌ 编译报错找不到库（如 PubSubClient、IRremoteESP8266）

```powershell
# 先安装依赖库
pio pkg install -l "knolleary/PubSubClient@^2.8"

# 或者让 PlatformIO 自动安装
pio run
# 第一次编译会自动下载 platformio.ini 中声明的库
```

### ❌ WiFi 连接失败

```
1. 确认 WiFi 名称密码正确
2. ESP32 只支持 2.4GHz WiFi，不支持 5GHz！
3. 路由器不要设置 MAC 过滤
4. 公司/学校 WiFi 可能需要认证页面，换家用 WiFi
```

### ❌ OLED 没有显示

```
1. 检查接线：SDA→GPIO21, SCL→GPIO22
2. 部分屏幕地址是 0x3D 不是 0x3C
3. 用 I2C 扫描器确认地址
```

---

## 各项目烧录命令速查

```powershell
# 气象站（最简单，推荐第一个烧）
cd "d:\projects\hardware\esp32-ai-projects\projects\weather-station"
pio run --target upload

# 智能家居
cd "d:\projects\hardware\esp32-ai-projects\projects\smart-home"
pio run --target upload

# 语音/拍手控制
cd "d:\projects\hardware\esp32-ai-projects\projects\voice-control"
pio run --target upload

# 手势识别
cd "d:\projects\hardware\esp32-ai-projects\projects\gesture-control"
pio run --target upload

# IR 红外遥控
cd "d:\projects\hardware\esp32-ai-projects\projects\ir-blaster"
pio run --target upload

# RF 433MHz 网关
cd "d:\projects\hardware\esp32-ai-projects\projects\rf-gateway"
pio run --target upload

# AI 摄像头（ESP32-CAM，需要 USB-TTL 模块，见下方说明）
cd "d:\projects\hardware\esp32-ai-projects\projects\ai-camera"
pio run --target upload
```

---

## ⚠️ ESP32-CAM 烧录方法（不同于普通 ESP32）

如果你用的是 ESP32-CAM（AI Thinker 版），**它没有板载 USB 转串口芯片**，需要额外的 USB-TTL 模块：

### 需要的额外硬件

| 物品 | 价格 |
|------|------|
| USB-TTL 模块（CH340/CP2102） | 5-10 元 |

### 接线

```
USB-TTL          ESP32-CAM
TX    ────────>  U0R (GPIO3)
RX    <────────  U0T (GPIO1)
5V    ────────>  5V
GND   ────────>  GND

⚠️ 额外跳线（烧录模式必须）：
IO0   ────────>  GND
```

### 烧录步骤

```
1. 按上表接好线（IO0 必须接 GND）
2. 插入 USB-TTL 到电脑
3. cd projects/ai-camera
4. pio run --target upload --upload-port COM5
5. 等待烧录完成
6. 断开 IO0 和 GND 的连线
7. 按 ESP32-CAM 上的 RST 按钮
8. pio device monitor 查看输出
```

---

## 推荐的首次烧录顺序

| 顺序 | 项目 | 原因 |
|------|------|------|
| **1** | weather-station | 最简单，只需 ESP32 + DHT22 |
| **2** | smart-home | 核心项目，验证继电器 + Web |
| **3** | voice-control | 仅需麦克风模块 |
| **4** | gesture-control | 需要 APDS-9960 传感器 |
| **5** | ir-blaster | 需要 IR LED + 接收头 |
| **6** | rf-gateway | 需要 433MHz 模块 |
| **7** | ai-camera | 需要独立 ESP32-CAM + USB-TTL |

---

**作者**: Kevin Ten  
**最后更新**: 2026-04
