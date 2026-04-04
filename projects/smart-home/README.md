# 智能家居控制器

基于 ESP32 的 WiFi 智能家居控制系统，支持 Web 控制台和本地按钮操作。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| Web 控制台 | 手机/电脑浏览器直接控制 |
| 4 路继电器 | 独立控制灯光、风扇、窗帘、插座 |
| OLED 显示 | 实时显示设备状态和 IP 地址 |
| 按钮控制 | GPIO35 按钮轮流切换设备 |
| JSON API | 支持与其他智能家居系统集成 |
| 全局开关 | 一键全开/全关所有设备 |

---

## 硬件清单

| 组件 | 数量 | 说明 |
|------|------|------|
| ESP32 开发板 | 1 | 普中 ESP32 或兼容板 |
| 继电器模块 | 1 | 4路5V继电器，低电平触发 |
| OLED 显示屏 | 1 | SSD1306 0.96寸 I2C接口 |
| 按钮 | 1 | 轻触按钮 |
| 杜邦线 | 若干 | 连接线 |

---

## 引脚连接

```
ESP32          继电器模块
GPIO 26  ----> IN1 (灯光)
GPIO 27  ----> IN2 (风扇)
GPIO 14  ----> IN3 (窗帘)
GPIO 12  ----> IN4 (插座)
3.3V/5V  ----> VCC
GND      ----> GND

ESP32          OLED SSD1306
GPIO 21  ----> SDA
GPIO 22  ----> SCL
3.3V     ----> VCC
GND      ----> GND

ESP32          按钮
GPIO 35  ----> 一端
GND      ----> 另一端（GPIO35 内部上拉）
```

> ⚠️ 继电器模块通常为低电平触发，本代码已处理（ON=LOW, OFF=HIGH）。
> 请确认你的继电器模块触发方式，如需改为高电平触发，修改 `setDevice()` 函数。

---

## 快速开始

### 1. 修改 WiFi 配置

编辑 `src/main.cpp`，修改以下两行：

```cpp
const char* WIFI_SSID = "你的WiFi名称";
const char* WIFI_PASSWORD = "你的WiFi密码";
```

### 2. 编译上传

```bash
# 在 projects/smart-home 目录下
pio run --target upload

# 或指定端口
pio run --target upload --upload-port COM3
```

### 3. 查看 IP 地址

打开串口监视器（115200 波特率），看到如下输出：

```
=== ESP32 智能家居控制器 ===
连接 WiFi: MyWiFi
WiFi 已连接，IP: 192.168.1.100
Web 服务器已启动，端口 80
控制台地址: http://192.168.1.100
```

### 4. 打开控制台

浏览器访问 `http://192.168.1.100`（替换为你的 IP），即可看到控制界面。

---

## Web API 接口

| 接口 | 方法 | 说明 | 示例 |
|------|------|------|------|
| `/` | GET | Web 控制台页面 | 浏览器访问 |
| `/api/state` | GET | 获取所有设备状态 | `curl http://192.168.1.100/api/state` |
| `/api/toggle?id=0` | GET | 切换指定设备 | id: 0-3 |
| `/api/set?id=0&state=1` | GET | 设置指定设备状态 | state: 0/1 |
| `/api/all?state=1` | GET | 全部开/关 | state: 0/1 |

### API 返回示例

```json
// GET /api/state
{
  "states": [true, false, false, true],
  "ip": "192.168.1.100"
}

// GET /api/toggle?id=0
{"ok": true}
```

### 与 Home Assistant 集成示例

```yaml
# configuration.yaml
switch:
  - platform: rest
    name: "ESP32 灯光"
    resource: http://192.168.1.100/api/set?id=0
    method: GET
    body_on: "state=1"
    body_off: "state=0"
    status_template: "{{ value_json.states[0] }}"
    state_resource: http://192.168.1.100/api/state
```

---

## 按钮操作

每次按下 GPIO35 按钮，轮流切换设备：
- 第1次按下 → 切换 **灯光**
- 第2次按下 → 切换 **风扇**
- 第3次按下 → 切换 **窗帘**
- 第4次按下 → 切换 **插座**
- 第5次按下 → 重新从灯光开始

---

## OLED 显示说明

```
┌────────────────┐
│Smart Home WiFi:OK│
├────────────────┤
│灯光    风扇    │
│[  ON  ][  OFF ]│
│窗帘    插座    │
│[  OFF ][  ON  ]│
└────────────────┘
```

- **ON** 状态：白底黑字高亮显示
- **OFF** 状态：正常文字显示

---

## 常见问题

**Q: 继电器模块不响应？**  
A: 检查继电器模块的触发方式。大多数继电器模块为低电平触发（已兼容），部分为高电平触发。修改 `setDevice()` 中的 `LOW`/`HIGH` 即可。

**Q: WiFi 连接失败？**  
A: 确认 SSID 和密码正确。ESP32 仅支持 2.4GHz 频段，不支持 5GHz。

**Q: OLED 没有显示？**  
A: 检查 I2C 地址（默认 0x3C），部分屏幕为 0x3D。用 I2C 扫描器确认地址后修改代码中的 `0x3C`。

**Q: 网页打不开？**  
A: 确保手机/电脑与 ESP32 在同一 WiFi 网络。防火墙可能阻止访问，尝试关闭防火墙。

---

## 扩展开发建议

1. **增加更多继电器**: 修改 `devices` 数组，添加 GPIO 引脚
2. **定时控制**: 引入 NTP 时间同步，实现定时开关
3. **MQTT 集成**: 添加 PubSubClient 库，接入 MQTT broker
4. **密码保护**: 在 Web 路由中添加 HTTP Basic Auth
5. **OTA 升级**: 使用 `AsyncElegantOTA` 实现无线升级

---

**作者**: Kevin Ten  
**最后更新**: 2026-03
