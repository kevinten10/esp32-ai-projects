/*
 * ESP32 气象站
 * 
 * 功能：
 * - DHT22 温湿度传感器读取
 * - OLED 实时显示
 * - WiFi 连接 + NTP 时间同步
 * - Web 服务器查看数据
 * 
 * 硬件连接：
 * - DHT22 DATA -> GPIO 4
 * - OLED SDA -> GPIO 21
 * - OLED SCL -> GPIO 22
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <time.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

// ========== 配置 ==========
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// NTP 时间服务器
const char* NTP_SERVER = "pool.ntp.org";
const long GMT_OFFSET = 8 * 3600;  // 中国时区 UTC+8

// 引脚定义
#define DHT_PIN 4
#define OLED_SDA 21
#define OLED_SCL 22

// OLED 定义
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define SCREEN_ADDRESS 0x3C

// DHT 定义
#define DHT_TYPE DHT22

// ========== 全局对象 ==========
WebServer server(80);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
DHT dht(DHT_PIN, DHT_TYPE);

// 数据缓存
float temperature = 0;
float humidity = 0;
unsigned long lastReadTime = 0;

// ========== 函数声明 ==========
void readSensorData();
void handleRoot();
void handleData();
String getHtmlPage();

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32 Weather Station ===");
    
    // 初始化 I2C
    Wire.begin(OLED_SDA, OLED_SCL);
    
    // 初始化 OLED
    Serial.print("Init OLED... ");
    if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
        Serial.println("Failed");
    } else {
        Serial.println("OK");
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0, 0);
        display.println("Starting...");
        display.display();
    }
    
    // 初始化 DHT 传感器
    Serial.print("Init DHT... ");
    dht.begin();
    Serial.println("OK");
    
    // 连接 WiFi
    Serial.print("Connecting WiFi... ");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 20) {
        delay(500);
        Serial.print(".");
        retry++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nWiFi Connected!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        
        // 配置 NTP 时间
        configTime(GMT_OFFSET, 0, NTP_SERVER);
        Serial.print("Sync NTP... ");
        struct tm timeinfo;
        if (getLocalTime(&timeinfo, 3000)) {
            Serial.println("OK");
        } else {
            Serial.println("Failed");
        }
    } else {
        Serial.println("\nWiFi Failed!");
    }
    
    // 配置 Web 服务器
    server.on("/", handleRoot);
    server.on("/data", handleData);
    server.begin();
    Serial.println("Web server started");
    
    // 显示欢迎信息
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print("WiFi: ");
    display.println(WiFi.status() == WL_CONNECTED ? "OK" : "OFF");
    display.setCursor(0, 16);
    display.print("IP: ");
    display.println(WiFi.localIP());
    display.setCursor(0, 32);
    display.print("Port: 80");
    display.display();
    
    // 首次读取传感器
    readSensorData();
}

// ========== 主循环 ==========
void loop() {
    // 读取传感器数据（每 2 秒）
    if (millis() - lastReadTime >= 2000) {
        readSensorData();
    }
    
    // 处理 Web 请求
    server.handleClient();
    
    delay(100);
}

// ========== 函数实现 ==========
void readSensorData() {
    float t = dht.readTemperature();
    float h = dht.readHumidity();
    
    if (!isnan(t)) temperature = t;
    if (!isnan(h)) humidity = h;
    
    lastReadTime = millis();
    
    Serial.printf("Temp: %.1fC, Humidity: %.1f%%\n", temperature, humidity);
    
    // 更新 OLED 显示
    display.clearDisplay();
    display.setTextSize(1);
    display.setCursor(0, 0);
    
    // 显示时间
    struct tm timeinfo;
    if (getLocalTime(&timeinfo, 100)) {
        char timeStr[20];
        strftime(timeStr, 20, "%H:%M:%S", &timeinfo);
        display.print(timeStr);
    }
    
    display.setCursor(90, 0);
    display.print("WiFi:");
    display.println(WiFi.status() == WL_CONNECTED ? "OK" : "OFF");
    
    // 显示温湿度
    display.setTextSize(2);
    display.setCursor(0, 16);
    display.printf("%.1f", temperature);
    display.setTextSize(1);
    display.print("C");
    
    display.setTextSize(2);
    display.setCursor(75, 16);
    display.printf("%.0f", humidity);
    display.setTextSize(1);
    display.print("%");
    
    // 显示体感温度
    float heatIndex = dht.computeHeatIndex(temperature, humidity, false);
    display.setCursor(0, 40);
    display.setTextSize(1);
    display.print("Heat:");
    display.printf("%.1f", heatIndex);
    display.print("C");
    
    display.display();
}

String getHtmlPage() {
    String html = "<!DOCTYPE html><html><head>";
    html += "<meta charset='UTF-8'>";
    html += "<meta name='viewport' content='width=device-width, initial-scale=1'>";
    html += "<title>ESP32 Weather Station</title>";
    html += "<style>";
    html += "body{font-family:Arial,sans-serif;text-align:center;padding:20px;background:#f0f8ff}";
    html += "h1{color:#333}";
    html += ".card{background:#fff;border-radius:10px;padding:20px;margin:10px;display:inline-block;min-width:150px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}";
    html += ".value{font-size:2.5em;color:#2196F3;font-weight:bold}";
    html += ".label{color:#666;margin-top:5px}";
    html += ".time{color:#999;margin-top:20px}";
    html += "button{background:#2196F3;color:#fff;border:none;padding:10px 20px;border-radius:5px;cursor:pointer;font-size:1em}";
    html += "button:hover{background:#1976D2}";
    html += "</style></head><body>";
    html += "<h1>ESP32 Weather Station</h1>";
    html += "<div class='card'><div class='value'>%TEMP% C</div><div class='label'>Temperature</div></div>";
    html += "<div class='card'><div class='value'>%HUM%%</div><div class='label'>Humidity</div></div>";
    html += "<div class='card'><div class='value'>%HEAT% C</div><div class='label'>Heat Index</div></div>";
    html += "<div class='time'>Time: %TIME%</div>";
    html += "<div><button onclick='location.reload()'>Refresh</button></div>";
    html += "</body></html>";
    return html;
}

void handleRoot() {
    String html = getHtmlPage();
    
    // 计算体感温度
    float heatIndex = dht.computeHeatIndex(temperature, humidity, false);
    
    // 替换占位符
    html.replace("%TEMP%", String(temperature, 1));
    html.replace("%HUM%", String(humidity, 1));
    html.replace("%HEAT%", String(heatIndex, 1));
    
    // 显示时间
    struct tm timeinfo;
    String timeStr = "N/A";
    if (getLocalTime(&timeinfo, 100)) {
        char buf[20];
        strftime(buf, 20, "%Y-%m-%d %H:%M:%S", &timeinfo);
        timeStr = String(buf);
    }
    html.replace("%TIME%", timeStr);
    
    server.send(200, "text/html", html);
}

void handleData() {
    // JSON API
    float heatIndex = dht.computeHeatIndex(temperature, humidity, false);
    
    struct tm timeinfo;
    String timeStr = "N/A";
    if (getLocalTime(&timeinfo, 100)) {
        char buf[20];
        strftime(buf, 20, "%Y-%m-%d %H:%M:%S", &timeinfo);
        timeStr = String(buf);
    }
    
    String json = "{";
    json += "\"temperature\":" + String(temperature, 1) + ",";
    json += "\"humidity\":" + String(humidity, 1) + ",";
    json += "\"heatindex\":" + String(heatIndex, 1) + ",";
    json += "\"time\":\"" + timeStr + "\"";
    json += "}";
    
    server.send(200, "application/json", json);
}
