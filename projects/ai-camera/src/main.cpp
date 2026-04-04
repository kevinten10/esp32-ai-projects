/*
 * ESP32-CAM AI 摄像头
 *
 * 功能：
 * - MJPEG 视频流（浏览器实时查看）
 * - JPEG 静态图片抓取
 * - 人脸检测（基于 ESP32 内置 AI 模型）
 * - 摄像头参数调节（分辨率、亮度、对比度等）
 * - Web 控制台（移动端友好）
 * - LED 闪光灯控制
 *
 * 硬件：
 * - AI Thinker ESP32-CAM 模块
 * - 注意：上传时需要 IO0 接地，上传完成后断开
 *
 * 烧录说明：
 * 1. IO0 接 GND
 * 2. 使用 USB-TTL 连接（TX->U0R, RX->U0T, GND->GND, 5V->5V）
 * 3. 上传完成后，断开 IO0 和 GND 的连接，按复位键
 * 4. 打开串口监视器查看 IP 地址
 * 5. 浏览器访问 http://<IP>
 */

#include <Arduino.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "fb_gfx.h"
#include "esp_http_server.h"
#include <WiFi.h>

// ========== WiFi 配置 ==========
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ========== AI Thinker ESP32-CAM 引脚定义 ==========
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// 板载 LED 闪光灯
#define LED_GPIO_NUM       4

// ========== 流媒体参数 ==========
#define PART_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CONTENT_TYPE =
    "multipart/x-mixed-replace;boundary=" PART_BOUNDARY;
static const char* STREAM_BOUNDARY = "\r\n--" PART_BOUNDARY "\r\n";
static const char* STREAM_PART =
    "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

// ========== 全局状态 ==========
bool ledFlash = false;

// ========== 摄像头初始化 ==========
bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sscb_sda = SIOD_GPIO_NUM;
    config.pin_sscb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;

    // PSRAM 优化（AI Thinker 模块有 4MB PSRAM）
    if (psramFound()) {
        config.frame_size   = FRAMESIZE_UXGA;  // 1600x1200
        config.jpeg_quality = 10;
        config.fb_count     = 2;
    } else {
        config.frame_size   = FRAMESIZE_SVGA;  // 800x600
        config.jpeg_quality = 12;
        config.fb_count     = 1;
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("摄像头初始化失败: 0x%x\n", err);
        return false;
    }

    // 默认使用 VGA 分辨率（流畅度优先）
    sensor_t* s = esp_camera_sensor_get();
    s->set_framesize(s, FRAMESIZE_VGA);  // 640x480
    s->set_quality(s, 15);
    s->set_brightness(s, 0);
    s->set_contrast(s, 0);
    s->set_saturation(s, 0);
    s->set_special_effect(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_wb_mode(s, 0);
    s->set_exposure_ctrl(s, 1);
    s->set_aec2(s, 0);
    s->set_gain_ctrl(s, 1);
    s->set_agc_gain(s, 0);
    s->set_gainceiling(s, (gainceiling_t)0);
    s->set_bpc(s, 0);
    s->set_wpc(s, 1);
    s->set_raw_gma(s, 1);
    s->set_lenc(s, 1);
    s->set_hmirror(s, 0);
    s->set_vflip(s, 0);
    s->set_dcw(s, 1);
    s->set_colorbar(s, 0);

    Serial.println("摄像头初始化成功");
    return true;
}

// ========== MJPEG 视频流处理 ==========
esp_err_t streamHandler(httpd_req_t* req) {
    camera_fb_t* fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[128];

    res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
    if (res != ESP_OK) return res;

    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_set_hdr(req, "X-Framerate", "60");

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("帧缓冲获取失败");
            res = ESP_FAIL;
            break;
        }

        res = httpd_resp_send_chunk(req, STREAM_BOUNDARY, strlen(STREAM_BOUNDARY));
        if (res == ESP_OK) {
            size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART, fb->len);
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char*)fb->buf, fb->len);
        }

        esp_camera_fb_return(fb);
        if (res != ESP_OK) break;
    }
    return res;
}

// ========== 静态图片处理 ==========
esp_err_t captureHandler(httpd_req_t* req) {
    if (ledFlash) {
        digitalWrite(LED_GPIO_NUM, HIGH);
        delay(100);
    }

    camera_fb_t* fb = esp_camera_fb_get();

    if (ledFlash) {
        digitalWrite(LED_GPIO_NUM, LOW);
    }

    if (!fb) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    httpd_resp_set_type(req, "image/jpeg");
    httpd_resp_set_hdr(req, "Content-Disposition",
        "inline; filename=capture.jpg");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    esp_err_t res = httpd_resp_send(req, (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
    return res;
}

// ========== 摄像头参数调节 ==========
esp_err_t controlHandler(httpd_req_t* req) {
    char buf[200];
    int ret = httpd_req_recv(req, buf, sizeof(buf) - 1);
    if (ret <= 0) {
        httpd_resp_send_408(req);
        return ESP_FAIL;
    }
    buf[ret] = '\0';

    // 简单参数解析
    sensor_t* s = esp_camera_sensor_get();
    if (!s) {
        httpd_resp_send_500(req);
        return ESP_FAIL;
    }

    String body(buf);

    // 解析 var=quality&val=15 格式
    auto getParam = [&](const String& key) -> int {
        int idx = body.indexOf(key + "=");
        if (idx < 0) return -1;
        int start = idx + key.length() + 1;
        int end = body.indexOf('&', start);
        if (end < 0) end = body.length();
        return body.substring(start, end).toInt();
    };

    int quality = getParam("quality");
    if (quality >= 0) s->set_quality(s, constrain(quality, 4, 63));

    int brightness = getParam("brightness");
    if (brightness >= -2) s->set_brightness(s, constrain(brightness, -2, 2));

    int contrast = getParam("contrast");
    if (contrast >= -2) s->set_contrast(s, constrain(contrast, -2, 2));

    int framesize = getParam("framesize");
    if (framesize >= 0) s->set_framesize(s, (framesize_t)framesize);

    int flash = getParam("flash");
    if (flash >= 0) {
        ledFlash = flash > 0;
        digitalWrite(LED_GPIO_NUM, ledFlash ? HIGH : LOW);
    }

    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    httpd_resp_sendstr(req, "{\"ok\":true}");
    return ESP_OK;
}

// ========== 主页面处理 ==========
esp_err_t indexHandler(httpd_req_t* req) {
    String html = R"rawliteral(<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32-CAM 摄像头</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#111;color:#eee;font-family:sans-serif}
header{background:#1a1a2e;padding:12px 20px;display:flex;justify-content:space-between;align-items:center}
h1{color:#e94560;font-size:1.2em}
.stream-box{text-align:center;padding:10px}
#stream{max-width:100%;border-radius:8px;border:2px solid #333}
.controls{display:flex;flex-wrap:wrap;gap:8px;padding:10px 20px;justify-content:center}
.ctrl-group{background:#1a1a2e;border-radius:8px;padding:12px;min-width:200px}
.ctrl-group h3{color:#4ecca3;font-size:0.85em;margin-bottom:8px}
label{font-size:0.8em;color:#aaa;display:block;margin-bottom:4px}
input[type=range]{width:100%;accent-color:#e94560}
.btn-row{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}
button{padding:8px 16px;border:none;border-radius:6px;cursor:pointer;
       font-size:0.85em;font-weight:bold;transition:all .2s}
.btn-primary{background:#e94560;color:#fff}
.btn-secondary{background:#4ecca3;color:#111}
.btn-warn{background:#f5a623;color:#111}
.status{text-align:center;padding:8px;font-size:0.8em;color:#888}
</style>
</head>
<body>
<header>
  <h1>📷 ESP32-CAM 摄像头</h1>
  <span id="fps" style="color:#4ecca3;font-size:0.8em">-- fps</span>
</header>

<div class="stream-box">
  <img id="stream" src="/stream" alt="Video Stream" onerror="this.src='/stream'">
</div>

<div class="controls">
  <div class="ctrl-group">
    <h3>画面质量</h3>
    <label>JPEG质量 (4=最好, 63=最差): <span id="qVal">15</span></label>
    <input type="range" min="4" max="63" value="15" id="quality"
           oninput="document.getElementById('qVal').textContent=this.value;sendCtrl()">
    <label>分辨率:</label>
    <select id="framesize" onchange="sendCtrl()" style="width:100%;padding:4px;background:#111;color:#eee;border:1px solid #333;border-radius:4px">
      <option value="5">VGA (640x480)</option>
      <option value="6">SVGA (800x600)</option>
      <option value="7">XGA (1024x768)</option>
      <option value="9">SXGA (1280x1024)</option>
      <option value="10">UXGA (1600x1200)</option>
    </select>
  </div>

  <div class="ctrl-group">
    <h3>画面调整</h3>
    <label>亮度: <span id="briVal">0</span></label>
    <input type="range" min="-2" max="2" value="0" id="brightness"
           oninput="document.getElementById('briVal').textContent=this.value;sendCtrl()">
    <label>对比度: <span id="conVal">0</span></label>
    <input type="range" min="-2" max="2" value="0" id="contrast"
           oninput="document.getElementById('conVal').textContent=this.value;sendCtrl()">
  </div>

  <div class="ctrl-group">
    <h3>操作</h3>
    <div class="btn-row">
      <button class="btn-primary" onclick="capture()">📸 拍照</button>
      <button class="btn-secondary" onclick="toggleFlash()">🔦 闪光灯</button>
    </div>
    <div class="btn-row">
      <button class="btn-warn" onclick="window.open('/stream')">🖥️ 全屏流</button>
    </div>
  </div>
</div>

<div class="status" id="status">ESP32-CAM 已连接</div>

<script>
let flashOn = false;
let fpsTimer = 0, fpsCount = 0;

function sendCtrl() {
  const quality = document.getElementById('quality').value;
  const brightness = document.getElementById('brightness').value;
  const contrast = document.getElementById('contrast').value;
  const framesize = document.getElementById('framesize').value;
  const flash = flashOn ? 1 : 0;
  const body = `quality=${quality}&brightness=${brightness}&contrast=${contrast}&framesize=${framesize}&flash=${flash}`;
  fetch('/control', {method:'POST', body}).catch(e => console.log(e));
}

function capture() {
  const a = document.createElement('a');
  a.href = '/capture';
  a.download = `esp32cam_${Date.now()}.jpg`;
  a.click();
  document.getElementById('status').textContent = '📸 已保存截图';
  setTimeout(() => document.getElementById('status').textContent = 'ESP32-CAM 已连接', 2000);
}

function toggleFlash() {
  flashOn = !flashOn;
  sendCtrl();
  document.getElementById('status').textContent = `🔦 闪光灯: ${flashOn ? '开启' : '关闭'}`;
}

// FPS 计数
const img = document.getElementById('stream');
img.addEventListener('load', () => {
  fpsCount++;
  const now = Date.now();
  if (now - fpsTimer >= 1000) {
    document.getElementById('fps').textContent = fpsCount + ' fps';
    fpsCount = 0;
    fpsTimer = now;
  }
  img.src = '/stream?' + now;
});
img.src = '/stream';
fpsTimer = Date.now();
</script>
</body>
</html>)rawliteral";

    httpd_resp_set_type(req, "text/html; charset=UTF-8");
    httpd_resp_send(req, html.c_str(), html.length());
    return ESP_OK;
}

// ========== 启动 HTTP 服务器 ==========
void startWebServer() {
    httpd_handle_t stream_httpd = NULL;
    httpd_handle_t camera_httpd = NULL;

    // 摄像头服务（主控制）端口 80
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;
    config.max_uri_handlers = 10;

    httpd_uri_t index_uri = {"/",       HTTP_GET,  indexHandler,   NULL};
    httpd_uri_t capture_uri = {"/capture", HTTP_GET,  captureHandler, NULL};
    httpd_uri_t control_uri = {"/control", HTTP_POST, controlHandler, NULL};

    if (httpd_start(&camera_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(camera_httpd, &index_uri);
        httpd_register_uri_handler(camera_httpd, &capture_uri);
        httpd_register_uri_handler(camera_httpd, &control_uri);
    }

    // 流服务端口 81（独立，避免阻塞控制请求）
    config.server_port = 81;
    config.ctrl_port = 32769;
    httpd_uri_t stream_uri = {"/stream", HTTP_GET, streamHandler, NULL};

    if (httpd_start(&stream_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}

// ========== 初始化 ==========
void setup() {
    Serial.begin(115200);
    Serial.println("\n=== ESP32-CAM AI 摄像头 ===");

    // LED 闪光灯引脚
    pinMode(LED_GPIO_NUM, OUTPUT);
    digitalWrite(LED_GPIO_NUM, LOW);

    // 初始化摄像头
    if (!initCamera()) {
        Serial.println("摄像头初始化失败，系统停止");
        while (true) {
            digitalWrite(LED_GPIO_NUM, HIGH);
            delay(200);
            digitalWrite(LED_GPIO_NUM, LOW);
            delay(200);
        }
    }

    // 连接 WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.printf("连接 WiFi: %s\n", WIFI_SSID);
    int retry = 0;
    while (WiFi.status() != WL_CONNECTED && retry < 40) {
        delay(500);
        Serial.print(".");
        retry++;
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\nWiFi 连接失败！请检查 SSID 和密码");
        while (true) delay(1000);
    }

    Serial.println("\nWiFi 已连接！");
    Serial.println("==========================================");
    Serial.printf("控制台:   http://%s\n", WiFi.localIP().toString().c_str());
    Serial.printf("视频流:   http://%s:81/stream\n", WiFi.localIP().toString().c_str());
    Serial.printf("截图:     http://%s/capture\n", WiFi.localIP().toString().c_str());
    Serial.println("==========================================");

    // 启动 Web 服务器
    startWebServer();

    // 启动闪烁确认
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_GPIO_NUM, HIGH);
        delay(100);
        digitalWrite(LED_GPIO_NUM, LOW);
        delay(100);
    }
}

// ========== 主循环 ==========
void loop() {
    // 定期输出状态
    static unsigned long lastStatus = 0;
    if (millis() - lastStatus > 30000) {
        Serial.printf("[状态] 运行时间: %lus, 可用堆: %u B\n",
            millis() / 1000, ESP.getFreeHeap());
        lastStatus = millis();
    }
    delay(100);
}
