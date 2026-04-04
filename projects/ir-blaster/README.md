# ESP32 IR 红外万能遥控器

将 ESP32 变成可学习任意遥控器信号的智能 IR Blaster，通过 WiFi/MQTT 控制空调、电视、风扇等所有带遥控器的家电。

---

## 功能特性

| 功能 | 说明 |
|------|------|
| 学码 | 学习任意遥控器的红外码（10秒内按键） |
| 发射 | 发射已学到的红外信号，替代原遥控器 |
| 空调控制 | 内置美的空调协议，支持温度/模式/风速 |
| Web 控制台 | 手机/电脑浏览器操作 |
| MQTT 接入 | 接入 Home Assistant 实现语音/自动化控制 |
| 有效距离 | ~8米（三极管驱动） |

### 支持的空调品牌（内置协议）
美的、格力、海尔、海信、志高、奥克斯、科龙、大金、松下、三星 等 100+ 品牌

---

## 硬件清单

| 组件 | 数量 | 规格 | 参考价 |
|------|------|------|--------|
| ESP32 开发板 | 1 | 普中/NodeMCU-32 | — |
| IR LED | 2 | 940nm 红外发射管 | 0.5元/个 |
| S8050 三极管 | 1 | NPN 三极管 | 0.2元 |
| VS1838B | 1 | 红外接收头 | 1元 |
| 电阻 1kΩ | 1 | 三极管基极限流 | — |
| 电阻 100Ω | 1 | IR LED 限流 | — |
| OLED SSD1306 | 1 | 0.96寸 I2C | — |

> 💡 **为什么要用三极管？**  
> ESP32 GPIO 最大电流 12mA，直接驱动 IR LED 有效距离只有约 1 米。  
> 使用 S8050 三极管放大电流后，IR LED 电流可达 50-100mA，距离提升至 8+ 米。

---

## 电路接线

### IR 发射电路（重要！）

```
                    3.3V 或 5V
                       |
                     100Ω
                       |
ESP32            IR LED (+)   ← 两颗 IR LED 可串联增大功率
GPIO 19 ──1kΩ──> S8050(B)
                 S8050(C) ──> IR LED (-)
                 S8050(E) ──> GND
```

简化图：
```
GPIO19 ──[1kΩ]──[S8050 B]  S8050 C ──[100Ω]──[IR LED]── VCC
                            S8050 E ── GND
```

### IR 接收（学码用）

```
ESP32            VS1838B
GPIO 18 <──────  OUT
3.3V    ──────>  VCC
GND     ──────>  GND
```

### OLED

```
ESP32 GPIO21 -> SDA
ESP32 GPIO22 -> SCL
3.3V -> VCC, GND -> GND
```

---

## 快速开始

### 1. 修改配置

编辑 `src/main.cpp`，修改 WiFi 和 MQTT 配置：

```cpp
const char* WIFI_SSID   = "你的WiFi";
const char* WIFI_PASS   = "你的密码";
const char* MQTT_SERVER = "192.168.1.20";  // HA 的 IP
```

如果不使用 MQTT，只用本地 Web 控制，可以将 MQTT_SERVER 设为空字符串。

### 2. 修改空调品牌（可选）

代码中默认使用美的空调协议。如果你是格力空调，修改以下内容：

```cpp
// 将
#include <ir_Midea.h>
IRMideaAC ac(IR_SEND_PIN);
// 改为
#include <ir_Gree.h>
IRGreeAC ac(IR_SEND_PIN);
```

支持的头文件列表见 [IRremoteESP8266 文档](https://github.com/crankyoldgit/IRremoteESP8266/blob/master/SupportedProtocols.md)

### 3. 编译上传

```bash
cd projects/ir-blaster
pio run --target upload
```

### 4. 学习遥控器按键

1. 浏览器访问 `http://<ESP32-IP>`
2. 在「学习新遥控码」区域输入按钮名称（如"电视开机"）
3. 点击「开始学码」
4. **在 10 秒内**将遥控器对准 VS1838B，按下对应按钮
5. 成功后按钮出现在「已学习的遥控码」列表中
6. 点击按钮即可发射该信号

### 5. 空调控制

Web 控制台上直接点击空调按钮：
- **开 26°C 制冷**：标准夏天模式
- **开 28°C 制热**：冬天取暖
- **关闭空调**：发送关机命令

---

## MQTT 接口

```bash
# 控制空调（发布到 MQTT topic）
# 开启制冷 26°C
mosquitto_pub -h 192.168.1.20 -t "home/esp32-ir/ac" \
  -m '{"power":true,"temp":26,"mode":"cool"}'

# 关闭空调
mosquitto_pub -h 192.168.1.20 -t "home/esp32-ir/ac" \
  -m '{"power":false}'

# 发射学到的第 0 号遥控码
mosquitto_pub -h 192.168.1.20 -t "home/esp32-ir/send" -m "0"
```

### Home Assistant 配置示例

```yaml
# configuration.yaml

# 空调控制（美的）
climate:
  - platform: mqtt
    name: "卧室空调"
    modes: ["off", "cool", "heat", "fan_only"]
    fan_modes: ["auto", "low", "medium", "high"]
    min_temp: 16
    max_temp: 30
    # 发布控制命令
    mode_command_topic: "home/esp32-ir/ac"
    mode_command_template: >
      {"power":{{ "true" if value != "off" else "false" }},
       "temp":{{ states('input_number.ac_temp') | int }},
       "mode":"{{ value }}"}

# 学到的遥控码（如电视）
script:
  tv_power:
    alias: "电视开机"
    sequence:
      - service: mqtt.publish
        data:
          topic: "home/esp32-ir/send"
          payload: "0"  # 第0个学到的码
```

---

## 常见问题

**Q: 发射了但空调没反应？**  
A: 
1. 检查空调品牌，修改对应的驱动文件（`ir_Midea.h` → `ir_Gree.h` 等）
2. 用手机摄像头对准 IR LED，发射时应能看到白色闪光
3. 检查三极管接线，测量 IR LED 两端是否有压降变化

**Q: 学码超时，VS1838B 没反应？**  
A:
1. 检查 VS1838B 的 OUT 引脚是否连接到 GPIO18
2. 确认 VS1838B 供电为 3.3V
3. 遥控器电池是否有电
4. 接收头对准遥控器，距离 5-15cm 为佳

**Q: Web 页面里的学到的码刷新后消失了？**  
A: 当前版本学到的码存储在内存中，重启后丢失。可添加 SPIFFS/Preferences 库将码持久化到 Flash 存储。

**Q: 如何控制电视（非空调）？**  
A: 使用学码功能：学习电视遥控器的每个按键（开机、换台、音量等），然后通过 Web 按钮或 MQTT 发射。

---

## 扩展开发建议

1. **SPIFFS 持久化存储**: 将学到的码保存到 Flash，重启后不丢失
2. **更多空调品牌**: 修改 `#include <ir_XXX.h>` 支持其他品牌完整协议
3. **红外转发**: 同时接收和发射，实现遥控器信号"中继"（穿墙控制）
4. **场景联动**: 结合 HA 自动化，如"下班回家"自动开空调

---

**作者**: Kevin Ten  
**最后更新**: 2026-04
