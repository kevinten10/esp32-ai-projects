"""
ESP32 气象站 - PC 模拟器 (普中 ESP32 版)
修复版 - 确保 Web 服务器正常工作
"""

import tkinter as tk
from tkinter import ttk
import random
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import socketserver

# ========== 模拟传感器数据 ==========
class SimulatedSensor:
    def __init__(self):
        self.temperature = 25.0
        self.humidity = 60.0
        self.base_temp = 25.0
        self.base_humidity = 60.0
        
    def read(self):
        self.temperature = self.base_temp + random.uniform(-2, 2)
        self.humidity = self.base_humidity + random.uniform(-5, 5)
        return self.temperature, self.humidity

# ========== 全局变量 ==========
sensor = SimulatedSensor()
wifi_connected = True
led_state = False
led_mode = "slow_blink"
server_running = False
httpd = None

# ========== 体感温度计算 ==========
def compute_heat_index(temp, humidity):
    return temp + (0.55 * (1 - humidity/100) * (temp - 14.5))

# ========== Web 服务器 ==========
class WeatherHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[Web] {args[0]}")
    
    def do_GET(self):
        try:
            if self.path == "/":
                self.send_html()
            elif self.path == "/data":
                self.send_json()
            elif self.path.startswith("/adjust"):
                self.handle_adjust()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"Error: {e}")
    
    def send_html(self):
        global sensor, led_state
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        led_text = "闪烁中" if led_state else "熄灭"
        led_class = "led-on" if led_state else "led-off"
        
        html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ESP32 气象站</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background: #f0f8ff; }}
        h1 {{ color: #333; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin: 10px; display: inline-block; min-width: 150px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .value {{ font-size: 2.5em; color: #2196F3; font-weight: bold; }}
        .label {{ color: #666; margin-top: 5px; }}
        .time {{ color: #999; margin-top: 20px; }}
        .status {{ color: #4CAF50; margin-top: 10px; font-weight: bold; }}
        button {{ background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1em; margin: 5px; }}
        button:hover {{ background: #1976D2; }}
        .led {{ width: 20px; height: 20px; border-radius: 50%%; display: inline-block; margin: 5px; }}
        .led-on {{ background: #4CAF50; box-shadow: 0 0 10px #4CAF50; }}
        .led-off {{ background: #333; }}
    </style>
</head>
<body>
    <h1>ESP32 气象站</h1>
    <div class="status">🖥️ PC 模拟模式 | 普中 ESP32</div>
    
    <div>
        LED: <span class="led {led_class}"></span> {led_text}
    </div>
    
    <div class="card">
        <div class="value">{temp:.1f}°C</div>
        <div class="label">温度</div>
    </div>
    
    <div class="card">
        <div class="value">{humidity:.1f}%</div>
        <div class="label">湿度</div>
    </div>
    
    <div class="card">
        <div class="value">{heat_index:.1f}°C</div>
        <div class="label">体感温度</div>
    </div>
    
    <div class="time">时间：{current_time}</div>
    
    <div>
        <button onclick="location.reload()">刷新</button>
        <button onclick="fetch('/adjust?type=temp&dir=up').then(()=>location.reload())">升温</button>
        <button onclick="fetch('/adjust?type=temp&dir=down').then(()=>location.reload())">降温</button>
        <button onclick="fetch('/adjust?type=humidity&dir=up').then(()=>location.reload())">加湿</button>
        <button onclick="fetch('/adjust?type=humidity&dir=down').then(()=>location.reload())">除湿</button>
    </div>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json(self):
        global sensor, wifi_connected, led_state
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        
        data = {
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "heatindex": round(heat_index, 1),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "simulator",
            "board": "PZ-ESP32",
            "wifi": wifi_connected,
            "led": led_state
        }
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def handle_adjust(self):
        global sensor
        from urllib.parse import parse_qs, urlparse
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if params.get('type') == ['temp']:
            if params.get('dir') == ['up']:
                sensor.base_temp += 1
            else:
                sensor.base_temp -= 1
        elif params.get('type') == ['humidity']:
            if params.get('dir') == ['up']:
                sensor.base_humidity += 5
            else:
                sensor.base_humidity -= 5
        
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

# ========== GUI 界面 ==========
class WeatherStationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 气象站模拟器 - 普中 ESP32")
        self.root.geometry("450x600")
        
        global led_state, led_mode
        self.led_state = False
        self.led_mode = "slow_blink"
        self.server_running = False
        
        self.setup_ui()
        self.update_data()
        self.update_led()
        self.log("模拟器已启动 (普中 ESP32 版)")
    
    def setup_ui(self):
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(title_frame, text="🌤️ ESP32 气象站", font=('Arial', 16, 'bold')).pack()
        ttk.Label(title_frame, text="🖥️ PC 模拟模式 | 普中 ESP32 版", font=('Arial', 10), foreground='green').pack()
        
        # LED 指示
        led_frame = ttk.Frame(self.root)
        led_frame.pack(fill='x', padx=20, pady=5)
        
        self.led_canvas = tk.Canvas(led_frame, width=30, height=30, bg='white', highlightthickness=0)
        self.led_canvas.pack(side='left', padx=10)
        self.led_label = ttk.Label(led_frame, text="LED: 闪烁中", font=('Arial', 10))
        self.led_label.pack(side='left')
        
        # 时间
        self.time_label = ttk.Label(self.root, text="", font=('Consolas', 12))
        self.time_label.pack(pady=5)
        
        # 温度
        temp_frame = ttk.LabelFrame(self.root, text="温度 (GPIO4)", padding=20)
        temp_frame.pack(fill='x', padx=20, pady=10)
        self.temp_value = ttk.Label(temp_frame, text="25.0°C", font=('Arial', 32, 'bold'), foreground='#2196F3')
        self.temp_value.pack()
        
        # 湿度
        humid_frame = ttk.LabelFrame(self.root, text="湿度 (GPIO4)", padding=20)
        humid_frame.pack(fill='x', padx=20, pady=10)
        self.humid_value = ttk.Label(humid_frame, text="60.0%", font=('Arial', 32, 'bold'), foreground='#2196F3')
        self.humid_value.pack()
        
        # 体感温度
        heat_frame = ttk.LabelFrame(self.root, text="体感温度", padding=20)
        heat_frame.pack(fill='x', padx=20, pady=10)
        self.heat_value = ttk.Label(heat_frame, text="25.5°C", font=('Arial', 24, 'bold'), foreground='#FF9800')
        self.heat_value.pack()
        
        # 控制按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill='x', padx=20, pady=10)
        ttk.Button(btn_frame, text="🌡️ 升温", command=lambda: self.adjust_temp(1)).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(btn_frame, text="❄️ 降温", command=lambda: self.adjust_temp(-1)).pack(side='left', expand=True, fill='x', padx=5)
        
        btn_frame2 = ttk.Frame(self.root)
        btn_frame2.pack(fill='x', padx=20, pady=5)
        ttk.Button(btn_frame2, text="💧 加湿", command=lambda: self.adjust_humidity(5)).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(btn_frame2, text="🌬️ 除湿", command=lambda: self.adjust_humidity(-5)).pack(side='left', expand=True, fill='x', padx=5)
        
        # LED 控制
        led_ctrl_frame = ttk.LabelFrame(self.root, text="LED 控制 (GPIO2)", padding=10)
        led_ctrl_frame.pack(fill='x', padx=20, pady=10)
        ttk.Button(led_ctrl_frame, text="💡 点亮", command=self.led_on).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(led_ctrl_frame, text="🌑 熄灭", command=self.led_off).pack(side='left', expand=True, fill='x', padx=5)
        
        # Web 服务器
        web_frame = ttk.LabelFrame(self.root, text="Web 服务器", padding=10)
        web_frame.pack(fill='x', padx=20, pady=10)
        
        self.web_status = ttk.Label(web_frame, text="状态：未启动", foreground='red')
        self.web_status.pack()
        
        btn_frame3 = ttk.Frame(web_frame)
        btn_frame3.pack(fill='x', pady=5)
        ttk.Button(btn_frame3, text="🌐 启动 Web", command=self.start_web_server).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(btn_frame3, text="🔗 打开浏览器", command=self.open_browser).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(btn_frame3, text="⏹️ 停止", command=self.stop_web_server).pack(side='left', expand=True, fill='x', padx=5)
        
        # 引脚信息
        pin_frame = ttk.LabelFrame(self.root, text="引脚配置", padding=10)
        pin_frame.pack(fill='x', padx=20, pady=10)
        ttk.Label(pin_frame, text="DHT: GPIO4 | OLED: SDA=21, SCL=22 | LED: GPIO2", font=('Consolas', 9)).pack()
        
        # 日志
        log_frame = ttk.LabelFrame(self.root, text="日志", padding=5)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        self.log_text = tk.Text(log_frame, height=6, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
    
    def draw_led(self, on):
        self.led_canvas.delete("all")
        if on:
            self.led_canvas.create_oval(2, 2, 28, 28, fill='#4CAF50', outline='#2E7D32')
            self.led_canvas.create_oval(8, 8, 22, 22, fill='#81C784', outline='')
        else:
            self.led_canvas.create_oval(2, 2, 28, 28, fill='#333333', outline='#111111')
    
    def update_data(self):
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        
        self.temp_value.config(text=f"{temp:.1f}°C")
        self.humid_value.config(text=f"{humidity:.1f}%")
        self.heat_value.config(text=f"{heat_index:.1f}°C")
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        self.root.after(1000, self.update_data)
    
    def update_led(self):
        if self.led_mode in ["slow_blink", "fast_blink"]:
            self.led_state = not self.led_state
        elif self.led_mode == "on":
            self.led_state = True
        else:
            self.led_state = False
        
        self.draw_led(self.led_state)
        self.root.after(500, self.update_led)
    
    def adjust_temp(self, delta):
        sensor.base_temp += delta
        self.log(f"温度：{sensor.base_temp:.1f}°C")
    
    def adjust_humidity(self, delta):
        sensor.base_humidity += delta
        self.log(f"湿度：{sensor.base_humidity:.1f}%")
    
    def led_on(self):
        self.led_mode = "on"
        self.log("LED: 点亮")
    
    def led_off(self):
        self.led_mode = "off"
        self.log("LED: 熄灭")
    
    def start_web_server(self):
        global server_running, httpd
        if server_running:
            self.log("Web 服务器已在运行")
            return
        
        try:
            httpd = socketserver.TCPServer(("", 8080), WeatherHandler)
            server_running = True
            self.web_status.config(text="状态：运行中 (端口 8080)", foreground='green')
            self.log("Web 服务器已启动：http://localhost:8080")
            
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
        except OSError as e:
            self.log(f"启动失败：端口 8080 可能被占用")
            self.web_status.config(text="状态：启动失败", foreground='red')
    
    def stop_web_server(self):
        global server_running, httpd
        if httpd:
            httpd.shutdown()
            server_running = False
            self.web_status.config(text="状态：已停止", foreground='red')
            self.log("Web 服务器已停止")
    
    def open_browser(self):
        webbrowser.open('http://localhost:8080')
        self.log("已打开浏览器 http://localhost:8080")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')

# ========== 主程序 ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherStationGUI(root)
    root.mainloop()
