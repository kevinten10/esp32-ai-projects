/*
 * ESP32 声音检测与拍手控制
 *
 * 功能：
 * - MAX9814 麦克风采集音频（模拟信号）
 * - 实时声音电平监测与串口波形输出
 * - 拍手模式识别：
 *     单拍  → 切换灯光
 *     双拍  → 切换风扇
 *     三拍  → 全部关闭
 * - 蜂鸣器反馈提示
 * - OLED 显示声音电平和状态
 *
 * 硬件连接：
 * - MAX9814 OUT  -> GPIO 36 (VP, ADC1_CH0)
 * - MAX9814 VCC  -> 3.3V
 * - MAX9814 GND  -> GND
 * - LED（灯光）  -> GPIO 26
 * - LED（风扇）  -> GPIO 27
 * - 蜂鸣器       -> GPIO 25
 * - OLED SDA    -> GPIO 21
 * - OLED SCL    -> GPIO 22
 *
 * 注意：MAX9814 增益引脚 GAIN 接地 = 40dB，浮空 = 50dB，接 VCC = 60dB
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>

// ========== 引脚定义 ==========
#define MIC_PIN     36    // MAX9814 模拟输出
#define LED_LIGHT   26    // 灯光（继电器）
#define LED_FAN     27    // 风扇（继电器）
#define BUZZER_PIN  25    // 蜂鸣器
#define OLED_SDA    21
#define OLED_SCL    22

// ========== 声音检测参数 ==========
#define SAMPLE_WINDOW_MS  50       // 采样窗口 50ms
#define CLAP_THRESHOLD    600      // 拍手音量阈值（0-4095）
#define CLAP_TIMEOUT_MS   500      // 拍手间隔超时（ms）
#define MIN_CLAP_INTERVAL 100      // 最小拍手间隔（去抖）

// ========== 全局变量 ==========
Adafruit_SSD1306 display(128, 64, &Wire, -1);

bool lightOn = false;
bool fanOn = false;

// 拍手识别
int clapCount = 0;
unsigned long lastClapTime = 0;
unsigned long clapGroupStart = 0;
bool waitingForMore = false;

// 声音电平历史（用于 OLED 波形）
uint8_t levelHistory[64] = {0};
int historyIdx = 0;

// ========== 蜂鸣器短鸣 ==========
void beep(int count, int ms = 80) {
    for (int i = 0; i < count; i++) {
        digitalWrite(BUZZER_PIN, HIGH);
        delay(ms);
        digitalWrite(BUZZER_PIN, LOW);
        if (i < count - 1) delay(60);
    }
}

// ========== 设备控制 ==========
void setLight(bool on) {
    lightOn = on;
    digitalWrite(LED_LIGHT, on ? LOW : HIGH);  // 继电器低有效
    Serial.printf("[控制] 灯光 -> %s\n", on ? "开" : "关");
}

void setFan(bool on) {
    fanOn = on;
    digitalWrite(LED_FAN, on ? LOW : HIGH);
    Serial.printf("[控制] 风扇 -> %s\n", on ? "开" : "关");
}

// ========== 执行拍手命令 ==========
void executeCommand(int claps) {
    Serial.printf("[识别] 检测到 %d 次拍手\n", claps);
    switch (claps) {
        case 1:
            setLight(!lightOn);
            beep(1);
            break;
        case 2:
            setFan(!fanOn);
            beep(2);
            break;
        case 3:
            setLight(false);
            setFan(false);
            beep(3);
            break;
        default:
            beep(1, 20);
            break;
    }
}

// ========== OLED 更新 ==========
void updateOled(int level, int peak) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // 标题
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("Voice Control");

    // 状态
    display.setCursor(0, 10);
    display.printf("Light:%s Fan:%s", lightOn ? "ON " : "OFF", fanOn ? "ON" : "OFF");

    // 拍手计数
    if (waitingForMore) {
        display.setCursor(0, 20);
        display.printf("Claps: %d ...", clapCount);
    }

    // 声音电平条
    display.setCursor(0, 30);
    display.print("Vol:");
    int barLen = map(level, 0, 4095, 0, 90);
    display.fillRect(26, 30, barLen, 6, SSD1306_WHITE);

    // 波形历史
    for (int i = 0; i < 64; i++) {
        int x = i;
        int idx = (historyIdx + i) % 64;
        int barH = map(levelHistory[idx], 0, 4095, 0, 20);
        if (barH > 0) {
            display.drawPixel(x + 32, 63 - barH, SSD1306_WHITE);
        }
    }

    // 阈值线
    int threshY = 63 - map(CLAP_THRESHOLD, 0, 4095, 0, 20);
    for (int x = 32; x < 128; x += 2) {
        display.drawPixel(x, threshY, SSD1306_WHITE);
    }

    display.display();
}

// ========== 声音电平采样 ==========
int sampleSoundLevel() {
    unsigned long startMs = millis();
    int maxVal = 0, minVal = 4095;
    while (millis() - startMs < SAMPLE_WINDOW_MS) {
        int sample = analogRead(MIC_PIN);
        if (sample > maxVal) maxVal = sample;
        if (sample < minVal) minVal = sample;
    }
    return maxVal - minVal;  // 峰峰值
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 声音控制系统 ===");
    Serial.println("操作说明:");
    Serial.println("  单拍 -> 切换灯光");
    Serial.println("  双拍 -> 切换风扇");
    Serial.println("  三拍 -> 全部关闭");

    // 引脚初始化
    pinMode(LED_LIGHT, OUTPUT);
    pinMode(LED_FAN, OUTPUT);
    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(LED_LIGHT, HIGH);  // 继电器断开
    digitalWrite(LED_FAN, HIGH);
    digitalWrite(BUZZER_PIN, LOW);

    // ADC 配置（12位，衰减11dB支持0-3.3V）
    analogReadResolution(12);
    analogSetAttenuation(ADC_11db);

    // OLED 初始化
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setTextSize(1);
        display.setCursor(0, 0);
        display.println("Voice Control");
        display.println("Ready!");
        display.println("");
        display.println("Clap to control:");
        display.println(" 1x = Light");
        display.println(" 2x = Fan");
        display.println(" 3x = All OFF");
        display.display();
        Serial.println("OLED 初始化成功");
    }

    delay(1500);
    beep(1, 100);  // 启动提示音
    Serial.println("系统就绪，等待拍手指令...");
}

// ========== 主循环 ==========
void loop() {
    int level = sampleSoundLevel();

    // 更新波形历史
    levelHistory[historyIdx] = constrain(level, 0, 255);
    historyIdx = (historyIdx + 1) % 64;

    // 串口波形输出（可用 Serial Plotter 查看）
    Serial.printf("Level:%d,Threshold:%d\n", level, CLAP_THRESHOLD);

    unsigned long now = millis();

    // 检测拍手（声音超过阈值）
    if (level > CLAP_THRESHOLD) {
        if (now - lastClapTime > MIN_CLAP_INTERVAL) {
            clapCount++;
            lastClapTime = now;
            if (!waitingForMore) {
                clapGroupStart = now;
                waitingForMore = true;
            }
            Serial.printf("[检测] 第 %d 次拍手，电平: %d\n", clapCount, level);
        }
    }

    // 超时后执行命令
    if (waitingForMore && (now - lastClapTime > CLAP_TIMEOUT_MS)) {
        executeCommand(clapCount);
        clapCount = 0;
        waitingForMore = false;
    }

    // 更新 OLED（每 100ms）
    static unsigned long lastOledUpdate = 0;
    if (now - lastOledUpdate > 100) {
        updateOled(level, CLAP_THRESHOLD);
        lastOledUpdate = now;
    }
}
