/*
 * ESP32 智能家居控制器
 *
 * 功能：
 * - WiFi 连接 + Web 控制台
 * - 4 路继电器独立控制（灯、风扇、窗帘、插座）
 * - OLED 实时状态显示
 * - 按钮本地切换（GPIO35）
 * - JSON API 接口（自动化集成）
 *
 * 硬件连接：
 * - 继电器1 (灯)    -> GPIO 26
 * - 继电器2 (风扇)  -> GPIO 27
 * - 继电器3 (窗帘)  -> GPIO 14
 * - 继电器4 (插座)  -> GPIO 12
 * - OLED SDA       -> GPIO 21
 * - OLED SCL       -> GPIO 22
 * - 按钮           -> GPIO 35
 * - 板载 LED       -> GPIO 2
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>

// ========== WiFi 配置（请修改为你的网络） ==========
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ========== 引脚定义 ==========
#define RELAY_1     26    // 灯光
#define RELAY_2     27    // 风扇
#define RELAY_3     14    // 窗帘
#define RELAY_4     12    // 插座
#define BUTTON_PIN  35    // 本地控制按钮
#define LED_PIN     2     // 板载 LED（WiFi 状态指示）

// OLED
#define OLED_SDA    21
#define OLED_SCL    22
#define SCREEN_W    128
#define SCREEN_H    64

// ========== 全局对象 ==========
WebServer server(80);
Adafruit_SSD1306 display(SCREEN_W, SCREEN_H, &Wire, -1);

// ========== 设备状态 ==========
struct Device {
    const char* name;
    const char* icon;
    int pin;
    bool state;
};

Device devices[4] = {
    {"灯光",   "💡", RELAY_1, false},
    {"风扇",   "🌀", RELAY_2, false},
    {"窗帘",   "🪟", RELAY_3, false},
    {"插座",   "🔌", RELAY_4, false},
};

bool wifiConnected = false;
unsigned long lastButtonTime = 0;
int buttonPressTarget = 0;   // 按钮轮流切换目标设备
unsigned long lastOledUpdate = 0;
int oledPage = 0;

// ========== OLED 显示 ==========
void updateOled() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // 标题行
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("Smart Home");
    display.setCursor(72, 0);
    display.print(wifiConnected ? "WiFi:OK" : "WiFi:OFF");

    // 分割线
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    // 设备状态（2×2 网格）
    for (int i = 0; i < 4; i++) {
        int col = (i % 2) * 64;
        int row = 13 + (i / 2) * 24;
        display.setCursor(col, row);
        display.setTextSize(1);
        display.print(devices[i].name);
        display.setCursor(col, row + 12);
        display.setTextSize(1);
        if (devices[i].state) {
            display.fillRect(col, row + 11, 58, 11, SSD1306_WHITE);
            display.setTextColor(SSD1306_BLACK);
            display.print("  [  ON  ]");
            display.setTextColor(SSD1306_WHITE);
        } else {
            display.print("  [ OFF  ]");
        }
    }

    display.display();
}

// ========== 继电器控制 ==========
void setDevice(int idx, bool state) {
    if (idx < 0 || idx >= 4) return;
    devices[idx].state = state;
    // 继电器低电平有效（常见模块），取反控制
    digitalWrite(devices[idx].pin, state ? LOW : HIGH);
    Serial.printf("[设备] %s -> %s\n", devices[idx].name, state ? "开" : "关");
    updateOled();
}

void toggleDevice(int idx) {
    setDevice(idx, !devices[idx].state);
}

// ========== Web 页面 ==========
String buildHtml() {
    String html = R"rawliteral(<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>智能家居控制台</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'PingFang SC',sans-serif;background:#1a1a2e;color:#eee;min-height:100vh;padding:20px}
h1{text-align:center;font-size:1.6em;margin-bottom:8px;color:#e94560}
.subtitle{text-align:center;color:#888;font-size:0.85em;margin-bottom:24px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:480px;margin:0 auto}
.card{background:#16213e;border-radius:16px;padding:20px;text-align:center;
      border:2px solid #0f3460;transition:all .2s;cursor:pointer}
.card:hover{border-color:#e94560;transform:translateY(-2px)}
.card.on{border-color:#4ecca3;background:#0d2b22}
.icon{font-size:2.5em;margin-bottom:8px}
.name{font-size:1em;color:#aaa;margin-bottom:12px}
.btn{padding:8px 24px;border:none;border-radius:20px;font-size:0.9em;
     cursor:pointer;transition:all .2s;font-weight:bold}
.btn.on{background:#4ecca3;color:#0d2b22}
.btn.off{background:#333;color:#888}
.status-bar{max-width:480px;margin:16px auto;background:#16213e;
            border-radius:12px;padding:12px;text-align:center;color:#888;font-size:0.8em}
.all-ctrl{max-width:480px;margin:0 auto 16px;display:flex;gap:12px;justify-content:center}
.btn-all{padding:10px 20px;border:none;border-radius:20px;cursor:pointer;
         font-size:0.85em;font-weight:bold;transition:all .2s}
.btn-on-all{background:#4ecca3;color:#0d2b22}
.btn-off-all{background:#e94560;color:#fff}
</style>
</head>
<body>
<h1>🏠 智能家居</h1>
<p class="subtitle">ESP32 智能家居控制台</p>
<div class="all-ctrl">
  <button class="btn-all btn-on-all" onclick="allOn()">全部开启</button>
  <button class="btn-all btn-off-all" onclick="allOff()">全部关闭</button>
</div>
<div class="grid" id="grid"></div>
<div class="status-bar" id="statusBar">正在加载...</div>
<script>
const devices=[
  {id:0,name:'灯光',icon:'💡'},
  {id:1,name:'风扇',icon:'🌀'},
  {id:2,name:'窗帘',icon:'🪟'},
  {id:3,name:'插座',icon:'🔌'}
];
let states=[false,false,false,false];

function renderGrid(){
  const g=document.getElementById('grid');
  g.innerHTML=devices.map(d=>`
  <div class="card ${states[d.id]?'on':''}" onclick="toggle(${d.id})">
    <div class="icon">${d.icon}</div>
    <div class="name">${d.name}</div>
    <button class="btn ${states[d.id]?'on':'off'}">${states[d.id]?'已开启':'已关闭'}</button>
  </div>`).join('');
}

async function fetchState(){
  try{
    const r=await fetch('/api/state');
    const j=await r.json();
    states=j.states;
    renderGrid();
    document.getElementById('statusBar').textContent=`IP: ${j.ip} | 最后更新: ${new Date().toLocaleTimeString('zh-CN')}`;
  }catch(e){document.getElementById('statusBar').textContent='连接失败';}
}

async function toggle(id){
  await fetch(`/api/toggle?id=${id}`);
  fetchState();
}

async function allOn(){
  await fetch('/api/all?state=1');
  fetchState();
}

async function allOff(){
  await fetch('/api/all?state=0');
  fetchState();
}

fetchState();
setInterval(fetchState, 3000);
</script>
</body>
</html>)rawliteral";
    return html;
}

// ========== Web 路由 ==========
void handleRoot() {
    server.send(200, "text/html; charset=UTF-8", buildHtml());
}

void handleApiState() {
    String json = "{\"states\":[";
    for (int i = 0; i < 4; i++) {
        json += devices[i].state ? "true" : "false";
        if (i < 3) json += ",";
    }
    json += "],\"ip\":\"" + WiFi.localIP().toString() + "\"}";
    server.send(200, "application/json", json);
}

void handleApiToggle() {
    if (server.hasArg("id")) {
        int id = server.arg("id").toInt();
        toggleDevice(id);
    }
    server.send(200, "application/json", "{\"ok\":true}");
}

void handleApiAll() {
    bool state = server.hasArg("state") && server.arg("state") == "1";
    for (int i = 0; i < 4; i++) setDevice(i, state);
    server.send(200, "application/json", "{\"ok\":true}");
}

void handleApiSet() {
    if (server.hasArg("id") && server.hasArg("state")) {
        int id = server.arg("id").toInt();
        bool state = server.arg("state") == "1";
        setDevice(id, state);
    }
    server.send(200, "application/json", "{\"ok\":true}");
}

// ========== 按钮处理 ==========
void checkButton() {
    static bool lastState = HIGH;
    bool current = digitalRead(BUTTON_PIN);
    if (lastState == HIGH && current == LOW) {
        unsigned long now = millis();
        if (now - lastButtonTime > 200) {
            toggleDevice(buttonPressTarget);
            buttonPressTarget = (buttonPressTarget + 1) % 4;
            lastButtonTime = now;
        }
    }
    lastState = current;
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 智能家居控制器 ===");

    // 初始化引脚
    for (int i = 0; i < 4; i++) {
        pinMode(devices[i].pin, OUTPUT);
        digitalWrite(devices[i].pin, HIGH);  // 继电器初始断开
    }
    pinMode(BUTTON_PIN, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // 初始化 I2C & OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("OLED 初始化成功");
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 0);
        display.println("Smart Home");
        display.println("Connecting WiFi...");
        display.display();
    } else {
        Serial.println("OLED 初始化失败（可忽略）");
    }

    // 连接 WiFi
    Serial.printf("连接 WiFi: %s\n", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 30) {
        delay(500);
        Serial.print(".");
        digitalWrite(LED_PIN, !digitalRead(LED_PIN));
        retry++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        digitalWrite(LED_PIN, HIGH);
        Serial.printf("\nWiFi 已连接，IP: %s\n", WiFi.localIP().toString().c_str());
    } else {
        Serial.println("\nWiFi 连接失败，进入离线模式");
        digitalWrite(LED_PIN, LOW);
    }

    // 注册 Web 路由
    server.on("/",           handleRoot);
    server.on("/api/state",  handleApiState);
    server.on("/api/toggle", handleApiToggle);
    server.on("/api/all",    handleApiAll);
    server.on("/api/set",    handleApiSet);
    server.begin();
    Serial.println("Web 服务器已启动，端口 80");

    if (wifiConnected) {
        Serial.printf("控制台地址: http://%s\n", WiFi.localIP().toString().c_str());
    }

    updateOled();
}

// ========== 主循环 ==========
void loop() {
    server.handleClient();
    checkButton();

    // 每 2 秒刷新 OLED
    if (millis() - lastOledUpdate > 2000) {
        updateOled();
        lastOledUpdate = millis();
    }

    delay(10);
}
