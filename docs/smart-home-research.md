# ESP32 控制智能家居 - 全方案调研报告

> **调研日期**: 2026-04  
> **结论速览**: ESP32 可通过 6 种主流方式接入智能家居生态，其中 **MQTT + Home Assistant** 和 **IR 红外** 是当前最实用的方案。

---

## 一、可行性结论

**完全可行**，且有多条成熟路径。ESP32 在智能家居领域已有大量成熟开源项目，生态极为活跃。

---

## 二、六大接入方案对比

| 方案 | 控制范围 | 成本 | 难度 | 云依赖 | 推荐指数 |
|------|---------|------|------|--------|---------|
| **MQTT + Home Assistant** | 自制设备 | 低 | ⭐⭐ | 可本地 | ⭐⭐⭐⭐⭐ |
| **ESPHome** | 自制设备 | 低 | ⭐ | 可本地 | ⭐⭐⭐⭐⭐ |
| **IR 红外万能遥控** | 空调/电视/风扇 | 极低 | ⭐⭐ | 无 | ⭐⭐⭐⭐⭐ |
| **RF 433MHz** | 市售射频插座/开关 | 低 | ⭐⭐ | 无 | ⭐⭐⭐⭐ |
| **Matter 协议** | 跨平台生态设备 | 低 | ⭐⭐⭐ | 无 | ⭐⭐⭐⭐ |
| **BLE 网关（米家）** | 小米蓝牙传感器 | 低 | ⭐⭐⭐ | 部分 | ⭐⭐⭐ |

---

## 三、方案详解

### 方案 1：MQTT + Home Assistant ⭐⭐⭐⭐⭐

**原理**: ESP32 作为 MQTT 客户端，向 MQTT Broker（Mosquitto）发布/订阅消息，Home Assistant 通过 MQTT 集成实现双向控制。

```
ESP32 ←→ WiFi ←→ MQTT Broker ←→ Home Assistant
                  (Mosquitto)
```

**优势**:
- 标准协议，几乎所有智能家居平台都支持
- 完全本地运行，无需云服务
- 实时性好（延迟 < 100ms）
- 支持自动发现（MQTT Discovery）

**典型代码**:
```cpp
#include <PubSubClient.h>

// 订阅控制命令
client.subscribe("home/bedroom/light/set");

// 发布状态反馈
client.publish("home/bedroom/light/state", "ON");
```

**MQTT Topic 规范（推荐）**:
```
home/{房间}/{设备类型}/{操作}
home/bedroom/light/set      ← 控制命令
home/bedroom/light/state    ← 状态反馈
home/bedroom/temp/sensor    ← 传感器数据
```

**硬件需求**: ESP32 + WiFi（无需额外模块）  
**软件需求**: Home Assistant + Mosquitto 插件

---

### 方案 2：ESPHome ⭐⭐⭐⭐⭐

**原理**: 给 ESP32 刷入 ESPHome 固件，通过 YAML 配置声明设备功能，Home Assistant 自动发现。

```yaml
# esphome 配置示例（bedroom_light.yaml）
esphome:
  name: bedroom-light

wifi:
  ssid: "MyWiFi"
  password: "password"

switch:
  - platform: gpio
    name: "卧室灯"
    pin: GPIO26

sensor:
  - platform: dht
    pin: GPIO4
    temperature:
      name: "卧室温度"
    humidity:
      name: "卧室湿度"
```

**优势**:
- **零代码**，只写 YAML
- HA 自动发现，无需手动配置
- OTA 升级（无线更新固件）
- 支持 200+ 种传感器/执行器
- 社区活跃，文档完善

**劣势**:
- 灵活性不如自写代码
- 复杂逻辑需要 Lambda 表达式

**适合场景**: 快速部署传感器节点、简单开关控制

---

### 方案 3：IR 红外万能遥控 ⭐⭐⭐⭐⭐

**原理**: ESP32 + IR 发射 LED + 接收头，学习现有遥控器的红外码，再通过 WiFi/MQTT 触发发射。

```
手机/HA ──WiFi──> ESP32 ──红外LED──> 空调/电视/风扇
                  (发射 38kHz 调制红外信号)
```

**可控制的设备**:
- 空调（所有品牌，美的/格力/海尔等）
- 电视（所有品牌，小米/创维/TCL等）
- 风扇、台灯、投影仪等带遥控器的设备

**硬件成本**: ESP32（已有）+ IR LED（≈0.5元）+ NPN 三极管（≈0.2元）+ IR 接收头（≈1元）

**关键库**: `IRremoteESP8266`（支持 100+ 空调品牌协议）

**接线**:
```
GPIO 19 ── 1kΩ ── NPN基极(S8050)
           NPN集电极 ── 100Ω ── IR LED 正极 ── 5V
           NPN发射极 ── GND
```

**2026 新动态**: Home Assistant 2026.4 已内置 IR 支持，ESP32 作为 IR 发射器可直接在 HA 界面学码和控制。

---

### 方案 4：RF 433MHz 射频 ⭐⭐⭐⭐

**原理**: ESP32 + 433MHz 收发模块，兼容市售的射频智能插座、开关、窗帘电机。

```
ESP32 ──> RF 发射模块 ──无线──> 射频智能插座/开关
ESP32 <── RF 接收模块 ──无线──> 射频遥控器（学习码）
```

**可控制的设备**:
- 433MHz 射频智能插座（淘宝/拼多多大量有售，10-30元/个）
- 射频遥控开关面板
- 射频电动窗帘电机
- 射频车库门、大门控制器

**硬件成本**: RF 发射模块（≈2元）+ RF 接收模块（≈3元）

**关键库**: `RCSwitch`（自动识别大多数 433MHz 协议）

**注意**: 需先用接收模块抓取原遥控器的 RF 码，再用发射模块重放。

---

### 方案 5：Matter 协议 ⭐⭐⭐⭐

**原理**: Matter 是苹果/谷歌/亚马逊/小米联合推出的物联网统一标准，ESP32 原生支持。

```
ESP32 (Matter设备)
    ↕ WiFi
Apple HomeKit / Google Home / Amazon Alexa / 小米家庭
（同一设备，多平台同时控制）
```

**优势**:
- 一套固件，接入所有主流平台
- 完全本地控制，无需云
- 官方 Espressif SDK（`esp-matter`）完善
- Arduino ESP32 内置 Matter 库（ESP32-C3/S3）

**适用芯片**:
- ESP32-C3 / ESP32-S3（WiFi + Thread 双模）
- ESP32-H2（Thread Only，低功耗传感器）
- 普通 ESP32-WROOM 也支持（仅 WiFi Matter）

**劣势**:
- 开发复杂度较高
- 需要 Matter Controller 设备（Apple TV/Google Nest/Echo）

**示例代码（Arduino Matter 库）**:
```cpp
#include <Matter.h>
MatterOnOffLight light;

void setup() {
  Matter.begin();
  light.begin();
  light.onChangeOnOff([](bool state) {
    digitalWrite(LED, state);
  });
}
```

---

### 方案 6：BLE 网关（小米蓝牙传感器）⭐⭐⭐

**原理**: ESP32 作为蓝牙代理（Bluetooth Proxy），扫描周围的小米蓝牙传感器广播数据，转发给 Home Assistant。

**可接入的设备**:
- 小米/青萍温湿度计（蓝牙版）
- 小米门窗传感器
- 小米人体传感器
- 青萍 CO₂ 传感器

**实现方法**:
1. 刷入 ESPHome 固件并启用 `bluetooth_proxy`
2. HA 中安装 `Xiaomi BLE` 集成
3. 输入设备 BindKey（从小米账号获取）

**成本**: 替代小米官方 349 元蓝牙网关，ESP32 成本约 15 元

---

## 四、推荐技术栈

### 场景 A：从零搭建个人智能家居

```
树莓派/NAS ──── Home Assistant (核心)
                 │
           ┌─────┼─────┐
           │     │     │
        ESP32  ESP32  ESP32
       (温湿度) (继电器) (IR遥控)
           │
        MQTT Broker (Mosquitto)
```

1. 树莓派/NUC 安装 **Home Assistant OS**
2. 安装 **Mosquitto** MQTT Broker 插件
3. ESP32 刷入 **ESPHome** 或自写 MQTT 代码
4. 在 HA 中创建自动化（定时/传感器联动）

---

### 场景 B：接入现有小米生态

```
小米网关/路由器 ──── 小米云
ESP32 ──────── BLE 网关 ──── Home Assistant
小米插座/空调 ──── WiFi ──── Miot 集成
```

1. HA 安装 **Xiaomi Miot Auto** 集成（接入小米 WiFi 设备）
2. ESP32 刷 ESPHome 做 **BLE Proxy**（接入蓝牙传感器）
3. HA 安装 **Midea AC** 集成（接入美的空调）

---

### 场景 C：控制传统家电（无智能功能）

```
ESP32 IR Blaster ──红外──> 空调/电视（任意品牌）
ESP32 RF Gateway ──433MHz──> 射频插座/开关
```

1. 制作 **IR Blaster**（见本仓库 `projects/ir-blaster`）
2. 制作 **RF Gateway**（见本仓库 `projects/rf-gateway`）
3. 接入 Home Assistant MQTT，统一控制

---

## 五、硬件购买清单

### 控制类（ESP32 本身）

| 硬件 | 用途 | 参考价格 |
|------|------|---------|
| 普中 ESP32（已有） | WiFi/BLE 核心 | — |
| 4路继电器模块 | 控制灯/风扇/插座 | 15元 |
| 双向继电器模块 | 高压设备控制 | 8元 |

### 感知类

| 硬件 | 用途 | 参考价格 |
|------|------|---------|
| DHT22 | 温湿度（已有） | — |
| PIR 人体传感器 | 人体存在检测 | 5元 |
| MQ-135 | 空气质量（CO₂/VOC） | 8元 |
| 光敏电阻 | 环境光感 | 0.5元 |

### IR/RF 类

| 硬件 | 用途 | 参考价格 |
|------|------|---------|
| IR LED（5mm） | 红外发射 | 0.5元/个 |
| VS1838B 接收头 | 红外学码 | 1元 |
| S8050 三极管 | IR LED 功率放大 | 0.2元 |
| SRX882 RF接收 | 433MHz 抓码 | 3元 |
| STX882 RF发射 | 433MHz 发射 | 2元 |

### 总计（基础套装）：约 40-60 元

---

## 六、下一步行动计划

| 优先级 | 项目 | 目标 |
|--------|------|------|
| 🔥 高 | `projects/smart-home` MQTT升级 | 接入 Home Assistant |
| 🔥 高 | `projects/ir-blaster` | 控制空调/电视 |
| 🌟 中 | `projects/rf-gateway` | 接入射频插座 |
| 💡 低 | Matter 协议实验 | 研究 ESP32-C3 Matter |
| 💡 低 | BLE 网关 | 接入小米蓝牙传感器 |

---

## 七、参考资源

- [ESPHome 官方文档](https://esphome.io/)
- [Home Assistant 官方文档](https://www.home-assistant.io/)
- [IRremoteESP8266 库（空调控制）](https://github.com/crankyoldgit/IRremoteESP8266)
- [RCSwitch 库（433MHz）](https://github.com/sui77/rc-switch)
- [ESP Matter SDK](https://github.com/espressif/esp-matter)
- [Mosquitto MQTT Broker](https://mosquitto.org/)
- [HACS 社区插件](https://hacs.xyz/)

---

**作者**: Kevin Ten  
**最后更新**: 2026-04
