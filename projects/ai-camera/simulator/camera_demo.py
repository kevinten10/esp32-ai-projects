"""
ESP32-CAM AI 摄像头 - 独立模拟器
==================================
模拟 ESP32-CAM 视频流 + Web 控制台。

运行: python camera_demo.py
访问: http://localhost:8085
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import random
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# ── 状态 ──────────────────────────────────────
BG = "#1a1a2e"; BG2 = "#16213e"; BG3 = "#0f3460"
ACCENT = "#e94560"; GREEN = "#4ecca3"; ORANGE = "#f5a623"
TEXT = "#eee"; DIM = "#888"

camera_settings = {
    "quality": 15,
    "brightness": 0,
    "contrast": 0,
    "framesize": 5,  # VGA
    "flash": False,
}

frame_count = 0
start_time = time.time()
log_lines = []

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    log_lines.append(line)
    if len(log_lines) > 200:
        log_lines.pop(0)
    print(line)

# ── 生成模拟视频帧 ──────────────────────────────
def generate_frame():
    """生成模拟的摄像头画面"""
    width, height = 640, 480
    
    # 创建基础图像
    img = Image.new('RGB', (width, height), color='#222')
    draw = ImageDraw.Draw(img)
    
    # 绘制模拟场景 - 房间
    # 地板
    draw.rectangle([0, 350, width, height], fill='#3a3a3a')
    
    # 墙壁
    draw.rectangle([0, 0, width, 350], fill='#4a4a5a')
    
    # 窗户
    draw.rectangle([200, 50, 440, 200], fill='#87CEEB')
    draw.line([200, 50, 440, 200], fill='white', width=3)
    draw.line([440, 50, 200, 200], fill='white', width=3)
    draw.line([320, 50, 320, 200], fill='white', width=3)
    draw.line([200, 125, 440, 125], fill='white', width=3)
    
    # 桌子
    draw.rectangle([150, 280, 490, 350], fill='#8B4513')
    
    # 杯子
    draw.ellipse([280, 240, 320, 280], fill='white')
    draw.rectangle([285, 230, 315, 250], fill='white')
    
    # 时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    draw.text((10, 10), f"ESP32-CAM Simulator", fill=GREEN)
    draw.text((10, 30), timestamp, fill=ACCENT)
    
    # FPS 显示
    elapsed = time.time() - start_time
    fps = frame_count / elapsed if elapsed > 0 else 0
    draw.text((width - 150, 10), f"{fps:.1f} fps", fill=GREEN)
    
    # 闪光灯效果
    if camera_settings["flash"]:
        draw.rectangle([0, 0, width, height], fill=(255, 255, 200, 100))
    
    # 添加随机噪点模拟真实摄像头效果
    import random
    for _ in range(50):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = random.randint(0, 50)
        draw.point((x, y), fill=(color, color, color))
    
    # 应用亮度调整
    if camera_settings["brightness"] != 0:
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Brightness(img)
        brightness_factor = 1.0 + camera_settings["brightness"] * 0.2
        img = enhancer.enhance(brightness_factor)
    
    # 应用对比度调整
    if camera_settings["contrast"] != 0:
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img)
        contrast_factor = 1.0 + camera_settings["contrast"] * 0.2
        img = enhancer.enhance(contrast_factor)
    
    # 转换为 JPEG
    img_byte_arr = io.BytesIO()
    quality = max(4, min(63, camera_settings["quality"]))
    # 转换质量值 (4-63 -> 10-95)
    jpeg_quality = int(95 - (quality - 4) * 1.5)
    img.save(img_byte_arr, format='JPEG', quality=jpeg_quality)
    
    return img_byte_arr.getvalue()

# ── HTTP 服务器 ──────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)

        def json_resp(data, code=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def html_resp(html):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=UTF-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        if p == "/" or p == "/index.html":
            html_resp(INDEX_HTML)
        
        elif p == "/capture":
            global frame_count
            frame_count += 1
            jpeg_data = generate_frame()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(jpeg_data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(jpeg_data)
            add_log("📸 截图已保存")
        
        elif p == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace;boundary=frame")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            try:
                while True:
                    global frame_count
                    frame_count += 1
                    jpeg_data = generate_frame()
                    
                    self.wfile.write(b'--frame\r\n')
                    self.wfile.write(b'Content-Type: image/jpeg\r\n')
                    self.wfile.write(f'Content-Length: {len(jpeg_data)}\r\n\r\n'.encode())
                    self.wfile.write(jpeg_data)
                    self.wfile.write(b'\r\n')
                    
                    time.sleep(0.1)  # 10 FPS
            except:
                pass
        
        elif p == "/status":
            json_resp({
                "status": "running",
                "settings": camera_settings,
                "uptime": int(time.time() - start_time),
            })
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/control":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = parse_qs(post_data.decode())
            
            if "quality" in params:
                camera_settings["quality"] = int(params["quality"][0])
            if "brightness" in params:
                camera_settings["brightness"] = int(params["brightness"][0])
            if "contrast" in params:
                camera_settings["contrast"] = int(params["contrast"][0])
            if "framesize" in params:
                camera_settings["framesize"] = int(params["framesize"][0])
            if "flash" in params:
                camera_settings["flash"] = params["flash"][0] == "1"
            
            add_log(f"⚙️ 参数更新: {params}")
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 静默日志

# ── Web 控制台 HTML ──────────────────────────────
INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32-CAM 摄像头 (模拟器)</title>
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
.simulator-badge{background:#f5a623;color:#111;padding:4px 12px;border-radius:12px;font-size:0.75em;font-weight:bold}
</style>
</head>
<body>
<header>
  <h1>📷 ESP32-CAM 摄像头 <span style="font-size:0.7em;color:#888">(模拟器)</span></h1>
  <span class="simulator-badge">SIMULATOR</span>
</header>

<div class="stream-box">
  <img id="stream" src="/stream" alt="Video Stream" onerror="setTimeout(()=>this.src='/stream',1000)">
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

<div class="status" id="status">ESP32-CAM 模拟器已启动</div>

<script>
let flashOn = false;

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
  a.download = `esp32cam_sim_${Date.now()}.jpg`;
  a.click();
  document.getElementById('status').textContent = '📸 已保存截图';
  setTimeout(() => document.getElementById('status').textContent = 'ESP32-CAM 模拟器已启动', 2000);
}

function toggleFlash() {
  flashOn = !flashOn;
  sendCtrl();
  document.getElementById('status').textContent = `🔦 闪光灯: ${flashOn ? '开启' : '关闭'}`;
}
</script>
</body>
</html>"""

# ── Tkinter GUI ──────────────────────────────────
class CameraSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32-CAM AI 摄像头模拟器")
        self.root.geometry("800x600")
        self.root.configure(bg=BG)
        
        # 标题
        title = tk.Label(root, text="📷 ESP32-CAM 摄像头模拟器", 
                        font=("Arial", 16, "bold"), bg=BG, fg=ACCENT)
        title.pack(pady=10)
        
        # 状态框架
        status_frame = tk.Frame(root, bg=BG2, padx=15, pady=10)
        status_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(status_frame, text="摄像头状态:", bg=BG2, fg=DIM, font=("Arial", 9)).pack(anchor="w")
        self.status_label = tk.Label(status_frame, text="✅ 摄像头已初始化 | 闪光灯: OFF", 
                                    bg=BG2, fg=GREEN, font=("Arial", 10, "bold"))
        self.status_label.pack(anchor="w", pady=5)
        
        # 控制面板
        ctrl_frame = tk.Frame(root, bg=BG)
        ctrl_frame.pack(fill="x", padx=20, pady=10)
        
        # 质量滑块
        self.add_slider(ctrl_frame, "JPEG质量:", 4, 63, 15, "quality")
        
        # 亮度滑块
        self.add_slider(ctrl_frame, "亮度:", -2, 2, 0, "brightness")
        
        # 对比度滑块
        self.add_slider(ctrl_frame, "对比度:", -2, 2, 0, "contrast")
        
        # 按钮
        btn_frame = tk.Frame(root, bg=BG)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="📸 拍照", command=self.capture, 
                 bg=ACCENT, fg="white", font=("Arial", 10, "bold"), 
                 padx=20, pady=8).pack(side="left", padx=5)
        
        tk.Button(btn_frame, text="🔦 闪光灯", command=self.toggle_flash, 
                 bg=GREEN, fg="#111", font=("Arial", 10, "bold"), 
                 padx=20, pady=8).pack(side="left", padx=5)
        
        # 日志区域
        log_frame = tk.Frame(root, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(log_frame, text="操作日志:", bg=BG, fg=DIM).pack(anchor="w")
        
        self.log_text = tk.Text(log_frame, height=10, bg=BG2, fg=TEXT, 
                               font=("Consolas", 9), state="disabled")
        self.log_text.pack(fill="both", expand=True, pady=5)
        
        # 启动信息
        add_log("ESP32-CAM 摄像头模拟器已启动")
        add_log("访问 http://localhost:8085 查看 Web 控制台")
        add_log("摄像头初始化成功 (AI Thinker 配置)")
        self.update_log()
    
    def add_slider(self, parent, label_text, min_val, max_val, default, key):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", pady=5)
        
        tk.Label(frame, text=label_text, bg=BG, fg=DIM, font=("Arial", 9)).pack(anchor="w")
        
        var = tk.IntVar(value=default)
        slider = tk.Scale(frame, from_=min_val, to=max_val, orient="horizontal", 
                         variable=var, bg=BG2, fg=TEXT, highlightthickness=0,
                         command=lambda v: self.update_setting(key, var.get()))
        slider.pack(fill="x", pady=2)
        
        return var
    
    def update_setting(self, key, value):
        camera_settings[key] = value
        add_log(f"⚙️ {key} = {value}")
        self.update_log()
        
        if key == "flash":
            self.status_label.config(text=f"✅ 摄像头已初始化 | 闪光灯: {'ON' if value else 'OFF'}")
    
    def capture(self):
        add_log("📸 截图已保存")
        self.update_log()
    
    def toggle_flash(self):
        camera_settings["flash"] = not camera_settings["flash"]
        add_log(f"🔦 闪光灯: {'开启' if camera_settings['flash'] else '关闭'}")
        self.status_label.config(text=f"✅ 摄像头已初始化 | 闪光灯: {'ON' if camera_settings['flash'] else 'OFF'}")
        self.update_log()
    
    def update_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(log_lines[-50:]))
        self.log_text.see("end")
        self.log_text.config(state="disabled")

# ── 主函数 ──────────────────────────────────────
def run_server():
    server = HTTPServer(("0.0.0.0", 8085), Handler)
    add_log("HTTP 服务器已启动在端口 8085")
    server.serve_forever()

def main():
    root = tk.Tk()
    app = CameraSimulatorGUI(root)
    
    # 在后台线程启动 HTTP 服务器
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    add_log("Web 控制台: http://localhost:8085")
    add_log("视频流: http://localhost:8085/stream")
    add_log("截图: http://localhost:8085/capture")
    app.update_log()
    
    root.mainloop()

if __name__ == "__main__":
    main()
