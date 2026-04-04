/*
 * ESP32 433MHz RF 智能网关
 *
 * 功能：
 * - 接收 433MHz 射频信号（抓码：学习市售遥控器的编码）
 * - 发射 433MHz 射频信号（控制市售射频插座/开关/窗帘）
 * - Web 控制台（添加设备、一键控制）
 * - MQTT 接入 Home Assistant（发现 + 控制）
 * - 支持 ASK/OOK 调制，兼容大多数市售 433MHz 设备
 *
 * 可控制的市售设备：
 * - 433MHz 射频智能插座（淘宝 10-30元/个）
 * - 射频遥控开关面板（墙贴式无线开关）
 * - 射频电动窗帘/卷帘电机
 * - 射频遥控车库门/大门
 * - 射频遥控风扇、灯光等
 *
 * 硬件接线：
 * ────────────────────────────────────────
 *  RF 发射模块（STX882 / XY-FST / FS1000A）：
 *    DATA ──> GPIO 17
 *    VCC  ──> 5V（注意：5V 射程更远）
 *    GND  ──> GND
 *    ANT  ──> 17cm 导线（1/4波长天线）
 *
 *  RF 接收模块（SRX882 / XY-MK-5V / RXB6）：
 *    DATA ──> GPIO 16
 *    VCC  ──> 5V
 *    GND  ──> GND
 *    ANT  ──> 17cm 导线
 *
 *  OLED SSD1306：
 *    SDA  ──> GPIO 21
 *    SCL  ──> GPIO 22
 * ────────────────────────────────────────
 *
 * 使用流程：
 *  1. 上电后打开 Web 控制台
 *  2. 点击「开始学码」，在 5 秒内按下遥控器按钮
 *  3. 看到显示的 433MHz 编码后，填写设备名称保存
 *  4. 点击设备按钮即可控制对应插座/开关
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <RCSwitch.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

// ========== 配置 ==========
const char* WIFI_SSID   = "YOUR_WIFI_SSID";
const char* WIFI_PASS   = "YOUR_WIFI_PASSWORD";
const char* MQTT_SERVER = "192.168.1.20";
const int   MQTT_PORT   = 1883;
const char* MQTT_USER   = "mqtt_user";
const char* MQTT_PASS_  = "mqtt_pass";
const char* DEVICE_ID   = "esp32-rf";

// ========== 引脚定义 ==========
#define RF_TX_PIN   17   // 发射模块 DATA 引脚
#define RF_RX_PIN   16   // 接收模块 DATA 引脚
#define OLED_SDA    21
#define OLED_SCL    22

// ========== RF 设备存储 ==========
#define MAX_RF_DEVICES  16
struct RFDevice {
    char name[24];      // 设备名称
    char room[16];      // 房间
    unsigned long codeOn;   // 开码
    unsigned long codeOff;  // 关码（可与开码相同，用于toggle）
    int protocol;       // RC协议 1-6
    int bits;           // 位数（通常24）
    bool hasOffCode;    // 是否有独立的关码
    bool state;         // 当前状态
    bool valid;
};

RFDevice rfDevices[MAX_RF_DEVICES];
int rfDeviceCount = 0;

// ========== 全局对象 ==========
RCSwitch rfSwitch;
WiFiClient espClient;
PubSubClient mqtt(espClient);
WebServer server(80);
Adafruit_SSD1306 display(128, 64, &Wire, -1);
Preferences prefs;

bool isLearning = false;
String lastAction = "就绪";
unsigned long lastMqttReconnect = 0;
unsigned long lastReceivedCode = 0;

// ========== 持久化存储 ==========
void saveDevices() {
    prefs.begin("rf-gw", false);
    prefs.putInt("count", rfDeviceCount);
    for (int i = 0; i < rfDeviceCount; i++) {
        String key = "dev" + String(i);
        prefs.putBytes(key.c_str(), &rfDevices[i], sizeof(RFDevice));
    }
    prefs.end();
    Serial.printf("[存储] 已保存 %d 个设备\n", rfDeviceCount);
}

void loadDevices() {
    prefs.begin("rf-gw", true);
    rfDeviceCount = prefs.getInt("count", 0);
    for (int i = 0; i < rfDeviceCount; i++) {
        String key = "dev" + String(i);
        prefs.getBytes(key.c_str(), &rfDevices[i], sizeof(RFDevice));
    }
    prefs.end();
    Serial.printf("[存储] 已加载 %d 个设备\n", rfDeviceCount);
}

// ========== 发射 RF 信号 ==========
void rfSend(unsigned long code, int protocol = 1, int bits = 24, int repeat = 5) {
    rfSwitch.setRepeatTransmit(repeat);
    rfSwitch.setProtocol(protocol);
    rfSwitch.send(code, bits);
    Serial.printf("[RF发射] 码:%lu 协议:%d 位:%d\n", code, protocol, bits);
}

void setRFDevice(int idx, bool on, bool publish = true) {
    if (idx < 0 || idx >= rfDeviceCount || !rfDevices[idx].valid) return;
    RFDevice& d = rfDevices[idx];
    d.state = on;

    unsigned long code = on ? d.codeOn : (d.hasOffCode ? d.codeOff : d.codeOn);
    rfSend(code, d.protocol, d.bits);

    lastAction = String(d.name) + ": " + (on ? "开" : "关");
    Serial.printf("[设备] %s -> %s\n", d.name, on ? "ON" : "OFF");
    saveDevices();

    // MQTT 状态反馈
    if (publish && mqtt.connected()) {
        String topic = String("home/") + DEVICE_ID + "/" + String(idx) + "/state";
        mqtt.publish(topic.c_str(), on ? "ON" : "OFF", true);
    }
}

void toggleRFDevice(int idx) {
    if (idx < 0 || idx >= rfDeviceCount) return;
    setRFDevice(idx, !rfDevices[idx].state);
}

// ========== OLED ==========
void updateOled() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.printf("RF GW  Devs:%d", rfDeviceCount);
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    if (isLearning) {
        display.setCursor(0, 14);
        display.println(">>> 学码模式 <<<");
        display.println("请按遥控器按钮...");
    } else {
        // 显示前4个设备状态
        for (int i = 0; i < min(rfDeviceCount, 4); i++) {
            display.setCursor(0, 12 + i * 11);
            display.printf("%-12s %s", rfDevices[i].name, rfDevices[i].state ? "ON" : "OFF");
        }
    }

    display.drawLine(0, 54, 127, 54, SSD1306_WHITE);
    display.setCursor(0, 56);
    display.print(lastAction.substring(0, 21));
    display.display();
}

// ========== MQTT 自动发现 ==========
void publishHADiscovery() {
    for (int i = 0; i < rfDeviceCount; i++) {
        if (!rfDevices[i].valid) continue;
        StaticJsonDocument<512> doc;
        String uid = String(DEVICE_ID) + "-" + String(i);
        doc["name"] = rfDevices[i].name;
        doc["unique_id"] = uid;
        doc["command_topic"] = String("home/") + DEVICE_ID + "/" + i + "/set";
        doc["state_topic"]   = String("home/") + DEVICE_ID + "/" + i + "/state";
        doc["retain"] = true;
        JsonObject dev = doc.createNestedObject("device");
        dev["identifiers"][0] = DEVICE_ID;
        dev["name"] = "ESP32 RF 网关";
        dev["manufacturer"] = "Kevin Ten";
        dev["model"] = "ESP32 RF Gateway";
        String payload, topic;
        serializeJson(doc, payload);
        topic = String("homeassistant/switch/") + uid + "/config";
        mqtt.publish(topic.c_str(), payload.c_str(), true);
        delay(50);
    }
    Serial.println("[MQTT] HA 自动发现已发布");
}

// ========== MQTT 处理 ==========
void onMqttMessage(char* topic, byte* payload, unsigned int len) {
    String msg;
    for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
    String topicStr(topic);

    // home/esp32-rf/{idx}/set → ON/OFF
    int slashPos = topicStr.lastIndexOf('/');
    String parent = topicStr.substring(0, slashPos);
    String action = topicStr.substring(slashPos + 1);

    if (action == "set") {
        int idx = parent.substring(parent.lastIndexOf('/') + 1).toInt();
        bool on = (msg == "ON" || msg == "on" || msg == "1");
        setRFDevice(idx, on);
    }
}

bool connectMqtt() {
    if (mqtt.connected()) return true;
    bool ok = mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASS_,
                           (String("home/") + DEVICE_ID + "/status").c_str(), 0, true, "offline");
    if (ok) {
        mqtt.publish((String("home/") + DEVICE_ID + "/status").c_str(), "online", true);
        for (int i = 0; i < rfDeviceCount; i++) {
            mqtt.subscribe((String("home/") + DEVICE_ID + "/" + i + "/set").c_str());
        }
        publishHADiscovery();
        Serial.println("[MQTT] 已连接并发布发现配置");
    }
    return ok;
}

// ========== Web 页面 ==========
String buildHtml() {
    String devJson = "[";
    for (int i = 0; i < rfDeviceCount; i++) {
        if (!rfDevices[i].valid) continue;
        devJson += "{idx:" + String(i) + ",name:'" + rfDevices[i].name +
                   "',room:'" + rfDevices[i].room +
                   "',state:" + (rfDevices[i].state ? "true" : "false") + "},";
    }
    if (devJson.endsWith(",")) devJson.remove(devJson.length() - 1);
    devJson += "]";

    return String(R"rawliteral(<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>RF 433 网关</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#eee;font-family:sans-serif;padding:16px}
h1{color:#e94560;text-align:center;margin-bottom:16px;font-size:1.4em}
.section{background:#16213e;border-radius:12px;padding:16px;margin-bottom:14px}
h2{color:#4ecca3;font-size:1em;margin-bottom:10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.card{background:#0f3460;border-radius:10px;padding:14px;text-align:center;border:2px solid #1a4a80}
.card.on{border-color:#4ecca3;background:#0d2b22}
.btn{padding:8px 18px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:.85em;margin:3px;transition:all .2s}
.btn-green{background:#4ecca3;color:#111}
.btn-red{background:#e94560;color:#fff}
.btn-blue{background:#2196F3;color:#fff}
.btn-gray{background:#444;color:#eee}
.toggle{padding:7px 20px;border:none;border-radius:16px;cursor:pointer;font-weight:bold;font-size:.85em}
.toggle.on{background:#4ecca3;color:#111}
.toggle.off{background:#444;color:#888}
input[type=text],input[type=number]{background:#111;border:1px solid #333;color:#eee;padding:8px;border-radius:6px;width:100%;font-size:.85em;margin-bottom:6px}
.row{display:flex;gap:8px;align-items:center}
.row label{font-size:.8em;color:#888;white-space:nowrap;min-width:60px}
.log{background:#111;border-radius:8px;padding:10px;font-size:.75em;color:#4ecca3;height:90px;overflow:auto;font-family:monospace}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.7em;margin-left:4px}
.badge-on{background:#4ecca3;color:#111}
.badge-off{background:#333;color:#888}
.room-tag{font-size:.7em;color:#888;margin-bottom:6px}
</style>
</head>
<body>
<h1>📻 433MHz RF 网关</h1>

<div class="section">
  <h2>🏠 设备控制</h2>
  <div class="grid" id="devGrid">加载中...</div>
</div>

<div class="section">
  <h2>🎓 添加新设备（学码）</h2>
  <div class="row"><label>设备名称</label><input type="text" id="newName" placeholder="如：客厅插座1"></div>
  <div class="row"><label>房间</label><input type="text" id="newRoom" placeholder="如：客厅"></div>
  <div style="margin-bottom:8px">
    <button class="btn btn-green" onclick="learnOn()">学习「开」码（5秒内按遥控器开键）</button>
  </div>
  <div id="learnResult" style="font-size:.8em;color:#f5a623;margin-bottom:8px"></div>
  <div style="margin-bottom:8px">
    <button class="btn btn-blue" onclick="learnOff()">学习「关」码（可选）</button>
  </div>
  <button class="btn btn-red" onclick="saveDevice()">保存设备</button>
</div>

<div class="section">
  <h2>📡 手动发射</h2>
  <div class="row"><label>RF 码</label><input type="number" id="manCode" placeholder="如：16711680"></div>
  <div class="row"><label>协议</label><input type="number" id="manProto" value="1" min="1" max="12"></div>
  <div class="row"><label>位数</label><input type="number" id="manBits" value="24" min="8" max="64"></div>
  <button class="btn btn-gray" onclick="manualSend()">发射</button>
</div>

<div class="section">
  <h2>📋 操作日志</h2>
  <div class="log" id="log">就绪...</div>
</div>

<script>
let pendingOnCode=0,pendingOffCode=0;
const devs=)rawliteral") + devJson + R"rawliteral(;

function log(msg){const el=document.getElementById('log');el.innerHTML=new Date().toLocaleTimeString('zh-CN')+' '+msg+'<br>'+el.innerHTML;}

function renderDevs(){
  const g=document.getElementById('devGrid');
  if(!devs.length){g.innerHTML='<p style="color:#888;grid-column:1/-1">暂无设备，请学码添加</p>';return;}
  g.innerHTML=devs.map(d=>`
  <div class="card ${d.state?'on':''}">
    <div class="room-tag">${d.room||'未分类'}</div>
    <div style="margin-bottom:8px;font-weight:bold">${d.name}</div>
    <button class="toggle ${d.state?'on':'off'}" onclick="toggle(${d.idx})">${d.state?'已开启':'已关闭'}</button>
    <div style="margin-top:8px;display:flex;gap:6px;justify-content:center">
      <button class="btn btn-green" style="padding:4px 10px" onclick="ctrl(${d.idx},1)">开</button>
      <button class="btn btn-red" style="padding:4px 10px" onclick="ctrl(${d.idx},0)">关</button>
    </div>
  </div>`).join('');
}

async function toggle(idx){const r=await fetch('/api/toggle?idx='+idx);const j=await r.json();log(j.action);setTimeout(()=>location.reload(),500);}
async function ctrl(idx,state){const r=await fetch('/api/set?idx='+idx+'&state='+state);const j=await r.json();log(j.action);setTimeout(()=>location.reload(),500);}

async function learnOn(){
  document.getElementById('learnResult').textContent='开始学习开码，请按遥控器...';
  const r=await fetch('/api/learn?mode=on');const j=await r.json();
  if(j.ok){pendingOnCode=j.code;document.getElementById('learnResult').textContent='开码学习成功: '+j.code+' (协议'+j.protocol+')';}
  else document.getElementById('learnResult').textContent='学码失败: '+j.msg;
}

async function learnOff(){
  document.getElementById('learnResult').textContent='开始学习关码，请按遥控器...';
  const r=await fetch('/api/learn?mode=off');const j=await r.json();
  if(j.ok){pendingOffCode=j.code;document.getElementById('learnResult').textContent+=' | 关码: '+j.code;}
  else document.getElementById('learnResult').textContent='关码学习失败';
}

async function saveDevice(){
  const name=document.getElementById('newName').value.trim();
  const room=document.getElementById('newRoom').value.trim();
  if(!name||!pendingOnCode){alert('请先填写名称并学习开码');return;}
  const r=await fetch(`/api/addDevice?name=${encodeURIComponent(name)}&room=${encodeURIComponent(room)}&onCode=${pendingOnCode}&offCode=${pendingOffCode}`);
  const j=await r.json();
  log(j.ok?'设备已保存: '+name:'保存失败');
  if(j.ok)setTimeout(()=>location.reload(),500);
}

async function manualSend(){
  const code=document.getElementById('manCode').value;
  const proto=document.getElementById('manProto').value;
  const bits=document.getElementById('manBits').value;
  const r=await fetch(`/api/rawsend?code=${code}&protocol=${proto}&bits=${bits}`);
  const j=await r.json();
  log('手动发射: '+code+' -> '+j.ok);
}

renderDevs();
</script>
</body></html>)rawliteral";
}

// ========== Web API 处理器 ==========
void handleRoot() { server.send(200, "text/html; charset=UTF-8", buildHtml()); }

void handleApiToggle() {
    int idx = server.arg("idx").toInt();
    toggleRFDevice(idx);
    server.send(200, "application/json",
                String("{\"ok\":true,\"action\":\"") + lastAction + "\"}");
}

void handleApiSet() {
    int idx = server.arg("idx").toInt();
    bool state = server.arg("state") == "1";
    setRFDevice(idx, state);
    server.send(200, "application/json",
                String("{\"ok\":true,\"action\":\"") + lastAction + "\"}");
}

void handleApiLearn() {
    String mode = server.arg("mode");
    isLearning = true;
    updateOled();
    Serial.printf("[学码] 等待 433MHz 信号... 模式:%s\n", mode.c_str());

    rfSwitch.resetAvailable();
    unsigned long timeout = millis() + 8000;
    bool received = false;
    unsigned long code = 0;
    int protocol = 1, bits = 24;

    while (millis() < timeout) {
        if (rfSwitch.available()) {
            code = rfSwitch.getReceivedValue();
            protocol = rfSwitch.getReceivedProtocol();
            bits = rfSwitch.getReceivedBitlength();
            if (code != 0) {
                received = true;
                Serial.printf("[学码] 接收到: %lu 协议:%d 位:%d\n", code, protocol, bits);
                rfSwitch.resetAvailable();
                break;
            }
            rfSwitch.resetAvailable();
        }
        delay(50);
    }

    isLearning = false;
    if (received) {
        lastReceivedCode = code;
        lastAction = String("学码: ") + code;
        updateOled();
        server.send(200, "application/json",
                    String("{\"ok\":true,\"code\":") + code +
                    ",\"protocol\":" + protocol + ",\"bits\":" + bits + "}");
    } else {
        updateOled();
        server.send(200, "application/json", "{\"ok\":false,\"msg\":\"timeout\"}");
    }
}

void handleApiAddDevice() {
    if (rfDeviceCount >= MAX_RF_DEVICES) {
        server.send(400, "application/json", "{\"ok\":false,\"msg\":\"max devices\"}");
        return;
    }
    RFDevice& d = rfDevices[rfDeviceCount];
    strncpy(d.name, server.arg("name").c_str(), 23);
    strncpy(d.room, server.arg("room").c_str(), 15);
    d.codeOn = server.arg("onCode").toInt();
    d.codeOff = server.arg("offCode").toInt();
    d.hasOffCode = (d.codeOff != 0 && d.codeOff != d.codeOn);
    d.protocol = 1;
    d.bits = 24;
    d.state = false;
    d.valid = true;
    rfDeviceCount++;
    saveDevices();

    // 如果 MQTT 已连接，更新订阅和发现
    if (mqtt.connected()) {
        mqtt.subscribe((String("home/") + DEVICE_ID + "/" + (rfDeviceCount - 1) + "/set").c_str());
        publishHADiscovery();
    }

    server.send(200, "application/json", "{\"ok\":true}");
}

void handleApiRawSend() {
    unsigned long code = server.arg("code").toInt();
    int protocol = server.arg("protocol").toInt();
    int bits = server.arg("bits").toInt();
    rfSend(code, protocol > 0 ? protocol : 1, bits > 0 ? bits : 24);
    server.send(200, "application/json", "{\"ok\":true}");
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 433MHz RF 智能网关 ===");

    // 加载存储的设备
    loadDevices();

    // RF 模块初始化
    rfSwitch.enableTransmit(RF_TX_PIN);
    rfSwitch.enableReceive(RF_RX_PIN);
    rfSwitch.setProtocol(1);
    rfSwitch.setPulseLength(350);

    // OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("OLED 初始化成功");
    }
    updateOled();

    // WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASS);
    Serial.printf("连接 WiFi: %s\n", WIFI_SSID);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 30) {
        delay(500); Serial.print("."); retry++;
    }
    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\nWiFi OK: %s\n", WiFi.localIP().toString().c_str());
    }

    // MQTT
    mqtt.setServer(MQTT_SERVER, MQTT_PORT);
    mqtt.setCallback(onMqttMessage);
    mqtt.setBufferSize(1024);
    if (WiFi.status() == WL_CONNECTED) connectMqtt();

    // Web 路由
    server.on("/",             handleRoot);
    server.on("/api/toggle",   handleApiToggle);
    server.on("/api/set",      handleApiSet);
    server.on("/api/learn",    handleApiLearn);
    server.on("/api/addDevice",handleApiAddDevice);
    server.on("/api/rawsend",  handleApiRawSend);
    server.begin();

    lastAction = "RF 网关就绪";
    updateOled();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("Web 控制台: http://%s\n", WiFi.localIP().toString().c_str());
    }
    Serial.println("RF 接收器已启用，监听 433MHz...");
}

// ========== 主循环 ==========
void loop() {
    server.handleClient();

    if (mqtt.connected()) {
        mqtt.loop();
    } else if (WiFi.status() == WL_CONNECTED && millis() - lastMqttReconnect > 5000) {
        lastMqttReconnect = millis();
        connectMqtt();
    }

    // 监听 RF 信号（非学码模式下打印日志）
    if (!isLearning && rfSwitch.available()) {
        unsigned long val = rfSwitch.getReceivedValue();
        if (val != 0) {
            Serial.printf("[RF接收] 码:%lu 协议:%d 位:%d\n",
                          val, rfSwitch.getReceivedProtocol(),
                          rfSwitch.getReceivedBitlength());
        }
        rfSwitch.resetAvailable();
    }

    delay(10);
}
