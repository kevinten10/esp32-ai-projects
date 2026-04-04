/*
 * ESP32 手势识别控制器
 *
 * 功能：
 * - APDS-9960 手势传感器（I2C）
 * - 识别 上/下/左/右 四方向手势
 * - 手势命令映射：
 *     向上   → 亮度增加（PWM 渐亮）
 *     向下   → 亮度降低（PWM 渐暗）
 *     向左   → 切换设备1（灯）
 *     向右   → 切换设备2（风扇）
 * - OLED 显示当前手势和设备状态
 * - 蜂鸣器确认提示音
 * - 接近检测（手靠近 -> 显示亮度）
 *
 * 硬件连接：
 * - APDS-9960 VCC -> 3.3V
 * - APDS-9960 GND -> GND
 * - APDS-9960 SDA -> GPIO 21
 * - APDS-9960 SCL -> GPIO 22
 * - APDS-9960 INT -> GPIO 4（中断，可选）
 * - PWM LED（亮度） -> GPIO 13
 * - 继电器1（灯）   -> GPIO 26
 * - 继电器2（风扇） -> GPIO 27
 * - 蜂鸣器         -> GPIO 25
 * - OLED SDA      -> GPIO 21
 * - OLED SCL      -> GPIO 22
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <SparkFun_APDS9960.h>

// ========== 引脚定义 ==========
#define APDS_INT    4     // APDS-9960 中断引脚（可选）
#define PWM_LED     13    // PWM 调光 LED
#define RELAY_LIGHT 26    // 灯光继电器
#define RELAY_FAN   27    // 风扇继电器
#define BUZZER_PIN  25    // 蜂鸣器
#define OLED_SDA    21
#define OLED_SCL    22

// ========== PWM 配置 ==========
#define PWM_CHANNEL 0
#define PWM_FREQ    5000
#define PWM_RES     8

// ========== 全局对象 ==========
SparkFun_APDS9960 apds;
Adafruit_SSD1306 display(128, 64, &Wire, -1);

// ========== 状态变量 ==========
int brightness = 128;   // PWM 亮度 0-255
bool lightOn = false;
bool fanOn = false;
String lastGesture = "---";
String lastAction = "";
unsigned long lastGestureTime = 0;

// ========== 蜂鸣器 ==========
void beep(int freq = 1000, int ms = 60) {
    tone(BUZZER_PIN, freq, ms);
    delay(ms + 10);
}

// ========== 设备控制 ==========
void setLight(bool on) {
    lightOn = on;
    digitalWrite(RELAY_LIGHT, on ? LOW : HIGH);
}

void setFan(bool on) {
    fanOn = on;
    digitalWrite(RELAY_FAN, on ? LOW : HIGH);
}

void setBrightness(int val) {
    brightness = constrain(val, 0, 255);
    ledcWrite(PWM_CHANNEL, brightness);
}

// ========== OLED 更新 ==========
void updateOled() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // 标题
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("Gesture Control");
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // 最后手势
    display.setCursor(0, 12);
    display.print("Gesture: ");
    display.setTextSize(2);
    display.setCursor(0, 21);
    display.print(lastGesture);

    // 操作结果
    display.setTextSize(1);
    display.setCursor(0, 40);
    display.print(lastAction);

    // 状态栏
    display.drawLine(0, 51, 127, 51, SSD1306_WHITE);
    display.setCursor(0, 54);
    display.printf("Light:%s Fan:%s Bri:%d%%",
        lightOn ? "ON" : "OFF",
        fanOn ? "ON" : "OFF",
        map(brightness, 0, 255, 0, 100));

    display.display();
}

// ========== 处理手势 ==========
void handleGesture(int gesture) {
    lastGestureTime = millis();
    switch (gesture) {
        case DIR_UP:
            lastGesture = "UP";
            setBrightness(brightness + 30);
            lastAction = "Brightness +" + String(map(brightness, 0, 255, 0, 100)) + "%";
            beep(1200, 60);
            Serial.printf("[手势] 向上 -> 亮度 %d%%\n", map(brightness, 0, 255, 0, 100));
            break;

        case DIR_DOWN:
            lastGesture = "DOWN";
            setBrightness(brightness - 30);
            lastAction = "Brightness " + String(map(brightness, 0, 255, 0, 100)) + "%";
            beep(800, 60);
            Serial.printf("[手势] 向下 -> 亮度 %d%%\n", map(brightness, 0, 255, 0, 100));
            break;

        case DIR_LEFT:
            lastGesture = "LEFT";
            setLight(!lightOn);
            lastAction = String("Light: ") + (lightOn ? "ON" : "OFF");
            beep(1000, 80);
            Serial.printf("[手势] 向左 -> 灯光 %s\n", lightOn ? "ON" : "OFF");
            break;

        case DIR_RIGHT:
            lastGesture = "RIGHT";
            setFan(!fanOn);
            lastAction = String("Fan: ") + (fanOn ? "ON" : "OFF");
            beep(1000, 80);
            Serial.printf("[手势] 向右 -> 风扇 %s\n", fanOn ? "ON" : "OFF");
            break;

        case DIR_NEAR:
            lastGesture = "NEAR";
            lastAction = "Prox detected";
            Serial.println("[手势] 接近检测");
            break;

        case DIR_FAR:
            lastGesture = "FAR";
            lastAction = "Object far";
            Serial.println("[手势] 远离检测");
            break;

        default:
            return;
    }
    updateOled();
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 手势识别控制器 ===");

    // 引脚初始化
    pinMode(RELAY_LIGHT, OUTPUT);
    pinMode(RELAY_FAN, OUTPUT);
    digitalWrite(RELAY_LIGHT, HIGH);
    digitalWrite(RELAY_FAN, HIGH);

    // PWM 初始化
    ledcSetup(PWM_CHANNEL, PWM_FREQ, PWM_RES);
    ledcAttachPin(PWM_LED, PWM_CHANNEL);
    ledcWrite(PWM_CHANNEL, brightness);

    // 蜂鸣器
    pinMode(BUZZER_PIN, OUTPUT);

    // I2C 初始化
    Wire.begin(OLED_SDA, OLED_SCL);
    Wire.setClock(400000);  // 400kHz

    // OLED 初始化
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("OLED 初始化成功");
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setTextSize(1);
        display.setCursor(0, 0);
        display.println("Gesture Control");
        display.println("Initializing...");
        display.display();
    }

    // APDS-9960 初始化
    Serial.print("APDS-9960 初始化... ");
    if (apds.init()) {
        Serial.println("成功");
        if (apds.enableGestureSensor(true)) {
            Serial.println("手势识别已启用");
        } else {
            Serial.println("手势识别启用失败！");
        }
        if (apds.enableProximitySensor(false)) {
            Serial.println("接近传感器已启用");
        }
    } else {
        Serial.println("APDS-9960 初始化失败！");
        Serial.println("请检查：1. 接线是否正确 2. I2C地址是否为 0x39");
        display.clearDisplay();
        display.println("APDS-9960");
        display.println("INIT FAILED!");
        display.println("Check wiring:");
        display.println("SDA->GPIO21");
        display.println("SCL->GPIO22");
        display.display();
    }

    delay(500);
    beep(1200, 80);
    delay(100);
    beep(1500, 80);
    Serial.println("系统就绪！");
    Serial.println("  向上滑动 -> 增加亮度");
    Serial.println("  向下滑动 -> 降低亮度");
    Serial.println("  向左滑动 -> 切换灯光");
    Serial.println("  向右滑动 -> 切换风扇");

    lastGesture = "Ready";
    lastAction = "Swipe to control";
    updateOled();
}

// ========== 主循环 ==========
void loop() {
    if (apds.isGestureAvailable()) {
        int gesture = apds.readGesture();
        handleGesture(gesture);
    }

    // 接近传感器读取
    static unsigned long lastProxTime = 0;
    if (millis() - lastProxTime > 500) {
        uint8_t proximity = 0;
        if (apds.readProximity(proximity)) {
            // proximity > 200 代表手靠近
            if (proximity > 200) {
                Serial.printf("[接近] 距离值: %d\n", proximity);
            }
        }
        lastProxTime = millis();
    }

    // 超时后清除手势显示
    if (lastGestureTime > 0 && millis() - lastGestureTime > 3000) {
        lastGesture = "---";
        lastAction = "Waiting...";
        lastGestureTime = 0;
        updateOled();
    }

    delay(10);
}
