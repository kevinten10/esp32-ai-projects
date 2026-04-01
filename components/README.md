# ESP32 AI 项目组件库

> 可复用的 ESP32 组件集合，所有组件默认引脚配置见 `components/pin-config.h`

---

## 📦 可用组件

| 组件 | 功能 | 默认引脚 | 依赖库 |
|------|------|---------|--------|
| **oled-display** | OLED 显示 (SSD1306) | SDA:21, SCL:22 | Adafruit_SSD1306 |
| **button-handler** | 按钮事件检测 | 35 | 无 |
| **sensor-utils** | DHT 温湿度传感器 | 4 | DHT sensor library |
| **wifi-manager** | WiFi 连接管理 | 无 | 无 |

---

## 🔧 使用方法

### 1. OLED 显示组件

```cpp
#include <oled_display.h>

OLEDDisplay display;  // 使用默认引脚 (21, 22)

void setup() {
    display.begin();
    display.showStatus("Hello");
}
```

**自定义引脚**:
```cpp
OLEDDisplay display(26, 25);  // 使用备用 I2C 引脚
```

---

### 2. 按钮处理组件

```cpp
#include <button_handler.h>

void onButtonEvent(ButtonEvent event) {
    switch (event) {
        case BUTTON_EVENT_CLICK:
            Serial.println("单击");
            break;
        case BUTTON_EVENT_DOUBLE_CLICK:
            Serial.println("双击");
            break;
        case BUTTON_EVENT_LONG_PRESS:
            Serial.println("长按");
            break;
    }
}

ButtonHandler button(BUTTON_1, onButtonEvent);  // 默认 GPIO 35

void setup() {
    button.begin();
}

void loop() {
    button.loop();  // 在循环中调用
}
```

---

### 3. 传感器工具组件

```cpp
#include <sensor_utils.h>

SensorUtils sensor;  // 使用默认引脚 (GPIO 4)

void setup() {
    sensor.begin();
}

void loop() {
    float temp = sensor.readTemperature();
    float hum = sensor.readHumidity();
    
    Serial.printf("温度：%.1f°C, 湿度：%.1f%%\n", temp, hum);
    delay(2000);
}
```

**单位转换**:
```cpp
float f = SensorUtils::celsiusToFahrenheit(25.0);  // 77.0
```

---

### 4. WiFi 管理器组件

```cpp
#include <wifi_manager.h>

WiFiManager wifi("your_ssid", "your_password");

void setup() {
    Serial.begin(115200);
    
    if (wifi.connect()) {
        Serial.println("WiFi 连接成功");
        Serial.println(wifi.getIPAddress());
    }
}
```

---

## 📁 引脚配置

所有组件的默认引脚定义在 `components/pin-config.h`：

```cpp
#include <pin-config.h>

// I2C
#define I2C_SDA_PIN     21
#define I2C_SCL_PIN     22

// 按钮 (仅输入引脚)
#define BUTTON_1        35
#define BUTTON_2        34

// 传感器
#define DHT_PIN         4

// 继电器
#define RELAY_1         26
#define RELAY_2         27
```

---

## ⚠️ 注意事项

1. **引脚冲突**: 使用 ADC2 引脚 (0, 2, 4, 12-15) 时，WiFi 可能影响读数
2. **输入引脚**: GPIO 34-39 仅支持输入，无内部上拉
3. **Flash 引脚**: GPIO 6-11 不可使用
4. **组件依赖**: 确保 `platformio.ini` 中已添加所需库

---

## 🛠️ 添加新组件

1. 在 `components/` 创建新目录
2. 创建 `.h` 和 `.cpp` 文件
3. 在 `pin-config.h` 添加默认引脚定义
4. 更新本文档

---

**最后更新**: 2026 年 3 月  
**作者**: Kevin Ten
