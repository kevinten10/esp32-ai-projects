/*
 * ESP32 红外万能遥控器（IR Blaster）
 *
 * 功能：
 * - 学习任意遥控器的红外码（按钮模式抓取）
 * - 发射学到的红外信号，控制空调/电视/风扇
 * - Web 控制台（手机/电脑访问）
 * - MQTT 接入（Home Assistant 控制）
 * - 内置 10 个常用空调品牌协议支持
 * - NEC / SONY / Samsung / RC5 等通用协议
 * - 信号强度：三极管驱动，有效距离 ~8米
 *
 * 硬件接线：
 * ─────────────────────────────────────────
 *  IR 发射电路（必须用三极管，否则距离不足）：
 *    GPIO 19 ─── 1kΩ ─── S8050(基极 B)
 *                         S8050(集电极 C) ─── IR LED(+) ─── 100Ω ─── 3.3V
 *                         S8050(发射极 E) ─── GND
 *
 *  IR 接收模块（学码用）：
 *    VS1838B OUT ─── GPIO 18
 *    VS1838B VCC ─── 3.3V
 *    VS1838B GND ─── GND
 *
 *  OLED SSD1306：
 *    SDA ─── GPIO 21
 *    SCL ─── GPIO 22
 * ─────────────────────────────────────────
 *
 * 支持的空调品牌（IRremoteESP8266 库内置）：
 *   美的(Midea)、格力(Gree)、海尔(Haier)、海信(Hisense)
 *   志高(Chigo)、奥克斯(Aux)、科龙(Kelon)
 *   大金(Daikin)、松下(Panasonic)、三星(Samsung)
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <IRremoteESP8266.h>
#include <IRsend.h>
#include <IRrecv.h>
#include <IRutils.h>
#include <PubSubClient.h>

// 美的空调驱动（可按需改为其他品牌）
#include <ir_Midea.h>

// ========== 配置 ==========
const char* WIFI_SSID   = "YOUR_WIFI_SSID";
const char* WIFI_PASS   = "YOUR_WIFI_PASSWORD";
const char* MQTT_SERVER = "192.168.1.20";
const int   MQTT_PORT   = 1883;
const char* MQTT_USER   = "mqtt_user";
const char* MQTT_PASS_  = "mqtt_pass";
const char* DEVICE_ID   = "esp32-ir";

// ========== 引脚定义 ==========
#define IR_SEND_PIN   19   // 红外发射（接三极管基极）
#define IR_RECV_PIN   18   // 红外接收（VS1838B）
#define OLED_SDA      21
#define OLED_SCL      22

// ========== 学码存储 ==========
#define MAX_LEARNED_CODES 16
struct IRCode {
    char name[20];       // 自定义名称
    decode_type_t type;  // 协议类型
    uint64_t code;       // 编码值
    uint16_t bits;       // 位数
    bool valid;
};

IRCode learnedCodes[MAX_LEARNED_CODES];
int learnCount = 0;

// ========== 全局对象 ==========
IRsend irsend(IR_SEND_PIN);
IRrecv irrecv(IR_RECV_PIN, 1024, 50, true);
decode_results irResult;

WiFiClient espClient;
PubSubClient mqtt(espClient);
WebServer server(80);
Adafruit_SSD1306 display(128, 64, &Wire, -1);

// 美的空调控制器
IRMideaAC ac(IR_SEND_PIN);

bool learning = false;
String lastAction = "就绪";
unsigned long lastMqttReconnect = 0;

// ========== OLED 更新 ==========
void updateOled(const String& line1, const String& line2 = "", const String& line3 = "") {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);

    display.setCursor(0, 0);
    display.print("IR Blaster");
    display.setCursor(72, 0);
    display.print(WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "No WiFi");
    display.drawLine(0, 9, 127, 9, SSD1306_WHITE);

    display.setCursor(0, 12);
    display.print(line1);
    if (line2.length()) { display.setCursor(0, 26); display.print(line2); }
    if (line3.length()) { display.setCursor(0, 40); display.print(line3); }

    display.drawLine(0, 54, 127, 54, SSD1306_WHITE);
    display.setCursor(0, 56);
    display.printf("Codes:%d  %s", learnCount, learning ? "[LEARNING]" : "");
    display.display();
}

// ========== 发送原始学到的码 ==========
bool sendLearnedCode(int idx) {
    if (idx < 0 || idx >= learnCount || !learnedCodes[idx].valid) return false;
    IRCode& c = learnedCodes[idx];
    Serial.printf("[IR发射] 发送: %s (协议:%s 码:0x%llX)\n",
                  c.name, typeToString(c.type).c_str(), c.code);
    irsend.send(c.type, c.code, c.bits);
    lastAction = String("发射: ") + c.name;
    updateOled("发射 " + String(c.name), typeToString(c.type));
    return true;
}

// ========== 空调控制（美的示例） ==========
void sendAcCommand(bool power, uint8_t temp = 26, uint8_t mode = kMideaCool, uint8_t fan = kMideaFanAuto) {
    ac.setPower(power);
    if (power) {
        ac.setTemp(temp);
        ac.setMode(mode);
        ac.setFan(fan);
    }
    ac.send();
    Serial.printf("[AC] 电源:%s 温度:%d° 模式:%d 风速:%d\n",
                  power ? "开" : "关", temp, mode, fan);
    lastAction = power ? String("空调开 ") + temp + "°C" : "空调关";
    updateOled(lastAction, power ? "模式:制冷" : "");
}

// ========== 学码模式 ==========
void startLearning(const char* codeName, int idx) {
    if (idx >= MAX_LEARNED_CODES) return;
    learning = true;
    Serial.printf("[学码] 请将遥控器对准接收头按下按钮... (%s)\n", codeName);
    updateOled("[学码模式]", "请按遥控器按钮", codeName);

    unsigned long timeout = millis() + 10000;  // 10秒超时
    while (millis() < timeout) {
        if (irrecv.decode(&irResult)) {
            if (irResult.decode_type != UNKNOWN) {
                strncpy(learnedCodes[idx].name, codeName, 19);
                learnedCodes[idx].type = irResult.decode_type;
                learnedCodes[idx].code = irResult.value;
                learnedCodes[idx].bits = irResult.bits;
                learnedCodes[idx].valid = true;
                if (idx >= learnCount) learnCount = idx + 1;

                Serial.printf("[学码] 成功! 协议:%s 码:0x%llX 位:%d\n",
                              typeToString(irResult.decode_type).c_str(),
                              irResult.value, irResult.bits);
                updateOled("[学码成功]",
                           String("协议: ") + typeToString(irResult.decode_type),
                           String("码: 0x") + String((uint32_t)irResult.value, HEX));
                irrecv.resume();
                learning = false;
                return;
            }
            irrecv.resume();
        }
        delay(100);
    }

    learning = false;
    Serial.println("[学码] 超时，未接收到信号");
    updateOled("[学码超时]", "未收到信号", "请检查接收头");
}

// ========== MQTT 消息处理 ==========
void onMqttMessage(char* topic, byte* payload, unsigned int len) {
    String msg;
    for (unsigned int i = 0; i < len; i++) msg += (char)payload[i];
    String topicStr(topic);
    Serial.printf("[MQTT] %s: %s\n", topic, msg.c_str());

    // 通用发射: home/esp32-ir/send {"idx": 0}
    if (topicStr.endsWith("/send")) {
        int idx = msg.toInt();
        sendLearnedCode(idx);
    }

    // 空调控制: home/esp32-ir/ac {"power":true,"temp":26,"mode":"cool"}
    if (topicStr.endsWith("/ac")) {
        // 简单解析 JSON
        bool power = msg.indexOf("\"power\":true") >= 0 || msg.indexOf("true") >= 0;
        int temp = 26;
        int ti = msg.indexOf("\"temp\":");
        if (ti >= 0) temp = msg.substring(ti + 7, ti + 9).toInt();
        sendAcCommand(power, temp);
    }
}

bool connectMqtt() {
    if (mqtt.connected()) return true;
    bool ok = mqtt.connect(DEVICE_ID, MQTT_USER, MQTT_PASS_);
    if (ok) {
        mqtt.subscribe((String("home/") + DEVICE_ID + "/send").c_str());
        mqtt.subscribe((String("home/") + DEVICE_ID + "/ac").c_str());
        Serial.println("[MQTT] 已连接");
    }
    return ok;
}

// ========== Web 页面 ==========
String buildHtml() {
    String codes_js = "[";
    for (int i = 0; i < learnCount; i++) {
        if (learnedCodes[i].valid) {
            codes_js += "{idx:" + String(i) + ",name:'" + learnedCodes[i].name + "'},";
        }
    }
    if (codes_js.endsWith(",")) codes_js.remove(codes_js.length() - 1);
    codes_js += "]";

    return R"rawliteral(<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IR 万能遥控</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#eee;font-family:sans-serif;padding:16px}
h1{color:#e94560;text-align:center;margin-bottom:16px}
.section{background:#16213e;border-radius:12px;padding:16px;margin-bottom:16px}
h2{color:#4ecca3;font-size:1em;margin-bottom:12px}
.btn{padding:10px 18px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:.85em;margin:4px;transition:all .2s}
.btn-red{background:#e94560;color:#fff}
.btn-blue{background:#2196F3;color:#fff}
.btn-green{background:#4ecca3;color:#111}
.btn-gray{background:#444;color:#eee}
.ac-ctrl{display:grid;grid-template-columns:1fr 1fr;gap:8px}
input[type=text]{background:#111;border:1px solid #333;color:#eee;padding:8px;border-radius:6px;width:100%;font-size:.9em}
.learned-list{display:flex;flex-wrap:wrap;gap:8px}
.log{background:#111;border-radius:8px;padding:10px;font-size:.75em;color:#4ecca3;height:80px;overflow:auto;font-family:monospace}
</style>
</head>
<body>
<h1>📡 IR 万能遥控</h1>

<div class="section">
  <h2>🌡️ 空调控制（美的协议）</h2>
  <div class="ac-ctrl">
    <button class="btn btn-red" onclick="acCmd(true,26)">开 26°C 制冷</button>
    <button class="btn btn-blue" onclick="acCmd(true,28,'heat')">开 28°C 制热</button>
    <button class="btn btn-gray" onclick="acCmd(true,24)">开 24°C</button>
    <button class="btn btn-gray" onclick="acCmd(false)">关闭空调</button>
  </div>
  <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
    <span style="font-size:.8em;color:#888">自定义温度:</span>
    <input type="number" id="acTemp" value="26" min="16" max="30" style="width:60px">
    <button class="btn btn-green" onclick="acCmd(true,+document.getElementById('acTemp').value)">发送</button>
  </div>
</div>

<div class="section">
  <h2>📚 已学习的遥控码</h2>
  <div class="learned-list" id="learnedList">加载中...</div>
</div>

<div class="section">
  <h2>🎓 学习新遥控码</h2>
  <div style="display:flex;gap:8px;margin-bottom:8px">
    <input type="text" id="newName" placeholder="按钮名称（如：电视开机）" maxlength="18">
  </div>
  <button class="btn btn-green" onclick="startLearn()">开始学码（10秒内按遥控器）</button>
</div>

<div class="section">
  <h2>📋 操作日志</h2>
  <div class="log" id="log">就绪...</div>
</div>

<script>
const codes=)rawliteral" + codes_js + R"rawliteral(;

function log(msg){
  const el=document.getElementById('log');
  el.innerHTML=new Date().toLocaleTimeString('zh-CN')+' '+msg+'<br>'+el.innerHTML;
}

function renderLearned(){
  const el=document.getElementById('learnedList');
  if(codes.length===0){el.textContent='暂无学习到的遥控码，请先学码';return;}
  el.innerHTML=codes.map(c=>`<button class="btn btn-blue" onclick="sendCode(${c.idx})">${c.name}</button>`).join('');
}

async function acCmd(power,temp,mode='cool'){
  const body={power,temp,mode};
  const r=await fetch('/api/ac',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const j=await r.json();
  log(j.action||'命令已发送');
}

async function sendCode(idx){
  const r=await fetch('/api/send?idx='+idx);
  const j=await r.json();
  log(j.action||'已发射');
}

async function startLearn(){
  const name=document.getElementById('newName').value.trim();
  if(!name){alert('请输入遥控按钮名称');return;}
  log('开始学码: '+name+' (请在10秒内按下遥控器)');
  const r=await fetch('/api/learn?name='+encodeURIComponent(name)+'&idx='+codes.length);
  const j=await r.json();
  log(j.ok?'学码成功: '+j.code:'学码失败: '+j.msg);
  if(j.ok)setTimeout(()=>location.reload(),1000);
}

renderLearned();
</script>
</body></html>)rawliteral";
}

void handleRoot() { server.send(200, "text/html; charset=UTF-8", buildHtml()); }

void handleApiAc() {
    if (server.method() != HTTP_POST) {
        server.send(405, "text/plain", "POST only");
        return;
    }
    String body = server.arg("plain");
    bool power = body.indexOf("\"power\":true") >= 0;
    int temp = 26;
    int ti = body.indexOf("\"temp\":");
    if (ti >= 0) temp = body.substring(ti + 7, ti + 9).toInt();
    bool heat = body.indexOf("heat") >= 0;
    sendAcCommand(power, temp, heat ? kMideaHeat : kMideaCool);
    server.send(200, "application/json",
                String("{\"ok\":true,\"action\":\"") + lastAction + "\"}");
}

void handleApiSend() {
    int idx = server.arg("idx").toInt();
    bool ok = sendLearnedCode(idx);
    server.send(200, "application/json",
                ok ? ("{\"ok\":true,\"action\":\"" + lastAction + "\"}") :
                     "{\"ok\":false,\"msg\":\"index invalid\"}");
}

void handleApiLearn() {
    String name = server.arg("name");
    int idx = server.arg("idx").toInt();
    if (name.length() == 0 || idx >= MAX_LEARNED_CODES) {
        server.send(400, "application/json", "{\"ok\":false,\"msg\":\"bad params\"}");
        return;
    }

    // 异步学码（Web 端会等待 HTTP 响应，因此需要先回复再执行）
    // 简化：直接阻塞学码（最多10秒）
    learning = true;
    updateOled("[学码]", "按遥控器按钮...", name);

    unsigned long timeout = millis() + 10000;
    bool success = false;
    while (millis() < timeout) {
        if (irrecv.decode(&irResult)) {
            if (irResult.decode_type != UNKNOWN && irResult.value != 0) {
                strncpy(learnedCodes[idx].name, name.c_str(), 19);
                learnedCodes[idx].type = irResult.decode_type;
                learnedCodes[idx].code = irResult.value;
                learnedCodes[idx].bits = irResult.bits;
                learnedCodes[idx].valid = true;
                if (idx >= learnCount) learnCount = idx + 1;
                success = true;
                irrecv.resume();
                break;
            }
            irrecv.resume();
        }
        delay(50);
    }
    learning = false;

    if (success) {
        updateOled("[学码成功]", name, String("0x") + String((uint32_t)learnedCodes[idx].code, HEX));
        server.send(200, "application/json",
                    String("{\"ok\":true,\"code\":\"0x") +
                    String((uint32_t)learnedCodes[idx].code, HEX) + "\"}");
    } else {
        updateOled("[学码超时]", "请重试", "");
        server.send(200, "application/json", "{\"ok\":false,\"msg\":\"timeout\"}");
    }
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 IR 万能遥控器 ===");

    // IR 初始化
    irsend.begin();
    irrecv.enableIRIn();
    ac.begin();
    // 美的空调初始默认设置
    ac.setPower(false);
    ac.setMode(kMideaCool);
    ac.setTemp(26);
    ac.setFan(kMideaFanAuto);

    // OLED
    Wire.begin(OLED_SDA, OLED_SCL);
    if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
        Serial.println("OLED 初始化成功");
    }
    updateOled("IR Blaster", "Connecting WiFi...");

    // WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASS);
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
    if (WiFi.status() == WL_CONNECTED) connectMqtt();

    // Web 路由
    server.on("/",          handleRoot);
    server.on("/api/ac",    handleApiAc);
    server.on("/api/send",  handleApiSend);
    server.on("/api/learn", handleApiLearn);
    server.begin();

    updateOled("IR Blaster 就绪",
               WiFi.status() == WL_CONNECTED ? WiFi.localIP().toString() : "No WiFi",
               "学码/发射 Ready");

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("Web 控制台: http://%s\n", WiFi.localIP().toString().c_str());
    }
    Serial.println("IR 接收器已启动，等待遥控信号...");
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

    // 监听 IR 信号（学码模式下由 API 处理，这里仅打印）
    if (!learning && irrecv.decode(&irResult)) {
        if (irResult.decode_type != UNKNOWN) {
            Serial.printf("[IR接收] 协议:%s 码:0x%llX 位:%d\n",
                          typeToString(irResult.decode_type).c_str(),
                          irResult.value, irResult.bits);
        }
        irrecv.resume();
    }

    delay(10);
}
