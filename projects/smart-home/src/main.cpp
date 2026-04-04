/*
 * ESP32 智能家居控制器（MQTT + Home Assistant 版）
 *
 * 功能：
 * - WiFi 连接 + 本地 Web 控制台（端口 80）
 * - MQTT 接入 Home Assistant（自动发现）
 * - 4 路继电器独立控制（灯、风扇、窗帘、插座）
 * - DHT22 温湿度传感器上报
 * - PIR 人体感应上报（可选）
 * - OLED 实时状态显示
 * - 按钮本地切换（GPIO35）
 * - 断线自动重连（WiFi + MQTT）
 *
 * 接线：
 * - 继电器1 (灯)    -> GPIO 26
 * - 继电器2 (风扇)  -> GPIO 27
 * - 继电器3 (窗帘)  -> GPIO 14
 * - 继电器4 (插座)  -> GPIO 12
 * - DHT22 DATA     -> GPIO 4
 * - PIR 传感器     -> GPIO 34（可选）
 * - OLED SDA       -> GPIO 21
 * - OLED SCL       -> GPIO 22
 * - 按钮           -> GPIO 35
 * - 板载 LED       -> GPIO 2
 *
 * MQTT Topic 规范（设备ID: esp32-home）：
 * 订阅（控制）：home/esp32-home/{relay}/set  → "ON"/"OFF"
 * 发布（状态）：home/esp32-home/{relay}/state → "ON"/"OFF"
 * 发布（传感）：home/esp32-home/sensor/temperature
 *              home/esp32-home/sensor/humidity
 *              home/esp32-home/sensor/motion
 *
 * Home Assistant MQTT Discovery Topic：
 * homeassistant/switch/esp32-home-{relay}/config → JSON
 * homeassistant/sensor/esp32-home-temp/config    → JSON
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ========== 配置区（必须修改） ==========
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASS     = "YOUR_WIFI_PASSWORD";
const char* MQTT_SERVER   = "192.168.1.20";   // Home Assistant / Mosquitto IP
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "mqtt_user";       // HA MQTT 用户名
const char* MQTT_PASS_    = "mqtt_pass";       // HA MQTT 密码
const char* DEVICE_ID     = "esp32-home";      // 设备唯一ID（不含空格）
const char* DEVICE_NAME   = "ESP32 智能家居";  // HA 显示名称

// ========== 引脚定义 ==========
#define RELAY_1     26
#define RELAY_2     27
#define RELAY_3     14
#define RELAY_4     12
#define DHT_PIN     4
#define PIR_PIN     34   // 人体传感器（可选）
#define BUTTON_PIN  35
#define LED_PIN     2
#define OLED_SDA    21
#define OLED_SCL    22

// ========== 设备定义 ==========
struct Device {
    const char* id;      // 英文ID（Topic用）
    const char* name;    // 中文名（HA显示）
    int pin;
    bool state;
};

Device devices[4] = {
    {"light",   "灯光",  RELAY_1, false},
    {"fan",     "风扇",  RELAY_2, false},
    {"curtain", "窗帘",  RELAY_3, false},
    {"socket",  "插座",  RELAY_4, false},
};

// ========== 全局对象 ==========
WiFiClient espClient;
PubSubClient mqtt(espClient);
WebServer server(80);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
DHT dht(DHT_PIN, DHT22);

// ========== 状态变量 ==========
bool wifiOk = false;
bool mqttOk = false;
float temperature = 0, humidity = 0;
bool motionDetected = false;
unsigned long lastSensorRead = 0;
unsigned long lastMqttReconnect = 0;
unsigned long lastButtonTime = 0;
int buttonTarget = 0;

// ========== Topic 构建工具 ==========
String topicCmd(int idx) {
    return String("home/") + DEVICE_ID + "/" + devices[idx].id + "/set";
}
String topicState(int idx) {
    return String("home/") + DEVICE_ID + "/" + devices[idx].id + "/state";
}
String topicSensor(const char* type) {
    return String("home/") + DEVICE_ID + "/sensor/" + type;
}

// ========== 设备控制 ==========
void setDevice(int idx, bool on, bool publishMqtt = true) {
    devices[idx].state = on;
    digitalWrite(devices[idx].pin, on ? LOW : HIGH);
    Serial.printf("[设备] %s -> %s\n", devices[idx].name, on ? "ON" : "OFF");
    if (publishMqtt && mqttOk) {
        mqtt.publish(topicState(idx).c_str(), on ? "ON" : "OFF", true);
    }
}

void toggleDevice(int idx) { setDevice(idx, !devices[idx].state); }

// ========== Home Assistant MQTT 自动发现 ==========
void publishHADiscovery() {
    Serial.println("[MQTT] 发布 HA 自动发现配置...");

    // 开关设备
    for (int i = 0; i < 4; i++) {
        StaticJsonDocument<512> doc;
        String uid = String(DEVICE_ID) + "-" + devices[i].id;
        doc["name"] = (String(DEVICE_NAME) + " " + devices[i].name).c_str();
        doc["unique_id"] = uid;
        doc["command_topic"] = topicCmd(i);
        doc["state_topic"] = topicState(i);
        doc["payload_on"] = "ON";
        doc["payload_off"] = "OFF";
        doc["optimistic"] = false;
        doc["retain"] = true;
        // 设备信息（HA设备注册）
        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = DEVICE_ID;
        dev["name"] = DEVICE_NAME;
        dev["manufacturer"] = "Kevin Ten";
        dev["model"] = "ESP32 Smart Home";

        String payload;
        serializeJson(doc, payload);
        String topic = String("homeassistant/switch/") + uid + "/config";
        mqtt.publish(topic.c_str(), payload.c_str(), true);
        delay(50);
    }

    // 温度传感器
    {
        StaticJsonDocument<512> doc;
        doc["name"] = (String(DEVICE_NAME) + " 温度").c_str();
        doc["unique_id"] = String(DEVICE_ID) + "-temp";
        doc["state_topic"] = topicSensor("temperature");
        doc["unit_of_measurement"] = "°C";
        doc["device_class"] = "temperature";
        doc["value_template"] = "{{ value | float }}";
        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = DEVICE_ID;
        dev["name"] = DEVICE_NAME;
        String payload;
        serializeJson(doc, payload);
        mqtt.publish(("homeassistant/sensor/" + String(DEVICE_ID) + "-temp/config").c_str(),
                     payload.c_str(), true);
    }

    // 湿度传感器
    {
        StaticJsonDocument<512> doc;
        doc["name"] = (String(DEVICE_NAME) + " 湿度").c_str();
        doc["unique_id"] = String(DEVICE_ID) + "-hum";
        doc["state_topic"] = topicSensor("humidity");
        doc["unit_of_measurement"] = "%";
        doc["device_class"] = "humidity";
        doc["value_template"] = "{{ value | float }}";
        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = DEVICE_ID;
        dev["name"] = DEVICE_NAME;
        String payload;
        serializeJson(doc, payload);
        mqtt.publish(("homeassistant/sensor/" + String(DEVICE_ID) + "-hum/config").c_str(),
                     payload.c_str(), true);
    }

    // 人体传感器
    {
        StaticJsonDocument<512> doc;
        doc["name"] = (String(DEVICE_NAME) + " 人体感应").c_str();
        doc["unique_id"] = String(DEVICE_ID) + "-motion";
        doc["state_topic"] = topicSensor("motion");
        doc["device_class"] = "motion";
        doc["payload_on"] = "ON";
        doc["payload_off"] = "OFF";
        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = DEVICE_ID;
        dev["name"] = DEVICE_NAME;
        String payload;
        serializeJson(doc, payload);
        mqtt.publish(("homeassistant/binary_sensor/" + String(DEVICE_ID) + "-motion/config").c_str(),
                     payload.c_str(), true);
    }

    Serial.println("[MQTT] HA 自动发现配置已发布");
}

// ========== MQTT 消息回调 ==========
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
    String topicStr(topic);
    String msg;
    for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];
    Serial.printf("[MQTT] 收到 %s: %s\n", topic, msg.c_str());

    for (int i = 0; i < 4; i++) {
        if (topicStr == topicCmd(i)) {
            bool on = (msg == "ON" || msg == "on" || msg == "1" || msg == "true");
            setDevice(i, on);
            return;
        }
    }
    // 全部控制
    if (topicStr == String("home/") + DEVICE_ID + "/all/set") {
        bool on = (msg == "ON");
        for (int i = 0; i < 4; i++) setDevice(i, on);
    }
}

// ========== MQTT 连接 ==========
bool connectMqtt() {
    if (mqtt.connected()) return true;
    Serial.print("[MQTT] 连接到 ");
    Serial.print(MQTT_SERVER);
    Serial.print("... ");

    // 遗嘱消息（断线时通知 HA）
    String willTopic = String("home/") + DEVICE_ID + "/status";
    bool connected = mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASS_,
                                  willTopic.c_str(), 0, true, "offline");
    if (connected) {
        mqttOk = true;
        Serial.println("成功");
        mqtt.publish(willTopic.c_str(), "online", true);

        // 订阅所有设备控制 Topic
        for (int i = 0; i < 4; i++) {
            mqtt.subscribe(topicCmd(i).c_str());
            Serial.printf("[MQTT] 订阅: %s\n", topicCmd(i).c_str());
        }
        mqtt.subscribe((String("home/") + DEVICE_ID + "/all/set").c_str());

        // 发布 HA 自动发现
        publishHADiscovery();

        // 发布当前状态
        for (int i = 0; i < 4; i++) {
            mqtt.publish(topicState(i).c_str(), devices[i].state ? "ON" : "OFF", true);
        }
    } else {
        mqttOk = false;
        Serial.printf("失败，错误码: %d\n", mqtt.state());
    }
    return connected;
}

// ========== 传感器读取 ==========
void readAndPublishSensors() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();

    if (!isnan(t)) {
        temperature = t;
        if (mqttOk) {
            mqtt.publish(topicSensor("temperature").c_str(),
                         String(temperature, 1).c_str());
        }
    }
    if (!isnan(h)) {
        humidity = h;
        if (mqttOk) {
            mqtt.publish(topicSensor("humidity").c_str(),
                         String(humidity, 1).c_str());
        }
    }

    // 人体传感器
    bool pir = digitalRead(PIR_PIN) == HIGH;
    if (pir != motionDetected) {
        motionDetected = pir;
        if (mqttOk) {
            mqtt.publish(topicSensor("motion").c_str(), pir ? "ON" : "OFF");
        }
        Serial.printf("[传感] 人体感应: %s\n", pir ? "有人" : "无人");
    }

    Serial.printf("[传感] 温度: %.1f°C 湿度: %.1f%%\n", temperature, humidity);
    lastSensorRead = millis();
}

// ========== OLED 更新 ==========
void updateOled() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);

    // 第一行：连接状态
    display.setCursor(0, 0);
    display.printf("WiFi:%s MQTT:%s",
        wifiOk ? "OK" : "--",
        mqttOk ? "OK" : "--");
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // 继电器状态（4格布局）
    for (int i = 0; i < 4; i++) {
        int col = (i % 2) * 64;
        int row = 12 + (i / 2) * 22;
        display.setCursor(col, row);
        display.print(devices[i].name);
        display.setCursor(col, row + 11);
        if (devices[i].state) {
            display.fillRect(col, row + 10, 58, 10, SSD1306_WHITE);
            display.setTextColor(SSD1306_BLACK);
            display.print("[ ON ]");
            display.setTextColor(SSD1306_WHITE);
        } else {
            display.print("[OFF  ]");
        }
    }

    // 底部：温湿度
    display.drawLine(0, 54, 127, 54, SSD1306_WHITE);
    display.setCursor(0, 56);
    display.printf("%.1fC  %.0f%%  %s",
        temperature, humidity,
        motionDetected ? "PIR:ON" : "");

    display.display();
}

// ========== Web 控制台 ==========
String buildHtml() {
    String html = R"rawliteral(<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>智能家居 - MQTT</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:16px}
h1{color:#e94560;text-align:center;margin-bottom:4px;font-size:1.4em}
.sub{text-align:center;color:#888;font-size:.8em;margin-bottom:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;max-width:480px;margin:0 auto 16px}
.card{background:#16213e;border-radius:12px;padding:16px;text-align:center;border:2px solid #0f3460;cursor:pointer;transition:all .2s}
.card.on{border-color:#4ecca3;background:#0d2b22}
.card:hover{transform:translateY(-2px)}
.cn{font-size:.85em;color:#aaa;margin-bottom:8px}
.btn{padding:6px 20px;border:none;border-radius:16px;font-size:.85em;font-weight:bold;cursor:pointer}
.btn.on{background:#4ecca3;color:#0d2b22}
.btn.off{background:#333;color:#888}
.info{max-width:480px;margin:0 auto;background:#16213e;border-radius:12px;padding:12px;display:grid;grid-template-columns:1fr 1fr 1fr;text-align:center;gap:8px}
.info-item label{font-size:.7em;color:#888}
.info-item .val{font-size:1.3em;color:#4ecca3;font-weight:bold}
.ctrls{max-width:480px;margin:12px auto;display:flex;gap:8px;justify-content:center}
.abtn{padding:8px 18px;border:none;border-radius:16px;cursor:pointer;font-weight:bold;font-size:.85em}
.abtn.on{background:#4ecca3;color:#111}
.abtn.off{background:#e94560;color:#fff}
.status{text-align:center;color:#666;font-size:.75em;margin-top:12px}
</style>
</head>
<body>
<h1>🏠 智能家居</h1>
<p class="sub" id="mqttStatus">MQTT: 加载中...</p>
<div class="ctrls">
  <button class="abtn on" onclick="allOn()">全部开启</button>
  <button class="abtn off" onclick="allOff()">全部关闭</button>
</div>
<div class="grid" id="grid"></div>
<div class="info">
  <div class="info-item"><label>温度</label><div class="val" id="temp">--</div></div>
  <div class="info-item"><label>湿度</label><div class="val" id="hum">--</div></div>
  <div class="info-item"><label>人体</label><div class="val" id="pir">--</div></div>
</div>
<p class="status" id="st">正在加载...</p>
<script>
const devs=[{id:'light',name:'💡 灯光'},{id:'fan',name:'🌀 风扇'},{id:'curtain',name:'🪟 窗帘'},{id:'socket',name:'🔌 插座'}];
let states=[false,false,false,false];

function render(){
  document.getElementById('grid').innerHTML=devs.map((d,i)=>`
  <div class="card ${states[i]?'on':''}" onclick="toggle(${i})">
    <div class="cn">${d.name}</div>
    <button class="btn ${states[i]?'on':'off'}">${states[i]?'已开启':'已关闭'}</button>
  </div>`).join('');
}

async function load(){
  try{
    const r=await fetch('/api/state');const j=await r.json();
    states=j.states;
    document.getElementById('temp').textContent=j.temp+'°C';
    document.getElementById('hum').textContent=j.hum+'%';
    document.getElementById('pir').textContent=j.motion?'有人':'无人';
    document.getElementById('mqttStatus').textContent='MQTT: '+(j.mqtt?'已连接':'未连接');
    document.getElementById('st').textContent='IP: '+j.ip+' | '+new Date().toLocaleTimeString('zh-CN');
    render();
  }catch(e){document.getElementById('st').textContent='连接失败';}
}

async function toggle(i){await fetch('/api/toggle?id='+i);load();}
async function allOn(){await fetch('/api/all?state=1');load();}
async function allOff(){await fetch('/api/all?state=0');load();}

load();setInterval(load,3000);
</script>
</body></html>)rawliteral";
    return html;
}

void handleRoot() { server.send(200, "text/html; charset=UTF-8", buildHtml()); }

void handleApiState() {
    StaticJsonDocument<256> doc;
    JsonArray arr = doc.createNestedArray("states");
    for (int i = 0; i < 4; i++) arr.add(devices[i].state);
    doc["ip"] = WiFi.localIP().toString();
    doc["mqtt"] = mqttOk;
    doc["temp"] = String(temperature, 1);
    doc["hum"] = String(humidity, 1);
    doc["motion"] = motionDetected;
    String out;
    serializeJson(doc, out);
    server.send(200, "application/json", out);
}

void handleApiToggle() {
    if (server.hasArg("id")) toggleDevice(server.arg("id").toInt());
    server.send(200, "application/json", "{\"ok\":true}");
}

void handleApiAll() {
    bool on = server.hasArg("state") && server.arg("state") == "1";
    for (int i = 0; i < 4; i++) setDevice(i, on);
    server.send(200, "application/json", "{\"ok\":true}");
}

// ========== 按钮处理 ==========
void checkButton() {
    static bool last = HIGH;
    bool cur = digitalRead(BUTTON_PIN);
    if (last == HIGH && cur == LOW && millis() - lastButtonTime > 200) {
        toggleDevice(buttonTarget);
        buttonTarget = (buttonTarget + 1) % 4;
        lastButtonTime = millis();
    }
    last = cur;
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 智能家居 MQTT 版 ===");

    // 引脚初始化
    for (int i = 0; i < 4; i++) {
        pinMode(devices[i].pin, OUTPUT);
        digitalWrite(devices[i].pin, HIGH);
    }
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(PIR_PIN, INPUT);
    pinMode(LED_PIN, OUTPUT);

    // I2C + OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        display.clearDisplay();
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 0);
        display.println("Smart Home MQTT");
        display.println("Connecting...");
        display.display();
    }

    // DHT22
    dht.begin();

    // WiFi
    Serial.printf("连接 WiFi: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 30) {
        delay(500); Serial.print("."); retry++;
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    }
    wifiOk = (WiFi.status() == WL_CONNECTED);
    digitalWrite(LED_PIN, wifiOk ? HIGH : LOW);
    if (wifiOk) {
        Serial.printf("\nWiFi OK, IP: %s\n", WiFi.localIP().toString().c_str());
    }

    // MQTT
    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onMqttMessage);
    mqtt.setBufferSize(1024);
    if (wifiOk) connectMqtt();

    // Web 服务器
    server.on("/",           handleRoot);
    server.on("/api/state",  handleApiState);
    server.on("/api/toggle", handleApiToggle);
    server.on("/api/all",    handleApiAll);
    server.begin();

    // 初次读取传感器
    readAndPublishSensors();
    updateOled();

    if (wifiOk) {
        Serial.printf("Web 控制台: http://%s\n", WiFi.localIP().toString().c_str());
        Serial.printf("MQTT Broker: %s:%d\n", MQTT_SERVER, MQTT_PORT);
        Serial.println("Home Assistant MQTT Discovery: 已启用");
    }
}

// ========== 主循环 ==========
void loop() {
    // WiFi 断线重连
    if (WiFi.status() != WL_CONNECTED) {
        wifiOk = false;
        mqttOk = false;
        WiFi.reconnect();
        delay(500);
        return;
    }
    wifiOk = true;

    // MQTT 断线重连（每5秒尝试一次）
    if (!mqtt.connected() && millis() - lastMqttReconnect > 5000) {
        lastMqttReconnect = millis();
        connectMqtt();
    }

    mqtt.loop();
    server.handleClient();
    checkButton();

    // 每 30 秒读取并上报传感器
    if (millis() - lastSensorRead > 30000) {
        readAndPublishSensors();
        updateOled();
    }
}
