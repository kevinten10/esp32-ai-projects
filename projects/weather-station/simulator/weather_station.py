"""
ESP32 气象站 - PC 模拟器
直接在电脑上运行，模拟 ESP32 气象站功能
"""

import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
from datetime import datetime

# ========== 模拟传感器数据 ==========
class SimulatedSensor:
    def __init__(self):
        self.temperature = 25.0  # 基础温度
        self.humidity = 60.0     # 基础湿度
        self.base_temp = 25.0
        self.base_humidity = 60.0
        
    def read(self):
        # 模拟传感器波动
        self.temperature = self.base_temp + random.uniform(-2, 2)
        self.humidity = self.base_humidity + random.uniform(-5, 5)
        return self.temperature, self.humidity
    
    def set_base(self, temp, humidity):
        self.base_temp = temp
        self.base_humidity = humidity

# ========== 全局变量 ==========
sensor = SimulatedSensor()
wifi_connected = False
start_time = datetime.now()

# ========== Web 服务器 ==========
class WeatherHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_html()
        elif self.path == "/data":
            self.send_json()
        else:
            self.send_error(404)
    
    def send_html(self):
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ESP32 气象站 (模拟器)</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background: #f0f8ff; }}
        h1 {{ color: #333; }}
        .card {{ background: white; border-radius: 10px; padding: 20px; margin: 10px; display: inline-block; min-width: 150px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .value {{ font-size: 2.5em; color: #2196F3; font-weight: bold; }}
        .label {{ color: #666; margin-top: 5px; }}
        .time {{ color: #999; margin-top: 20px; }}
        .status {{ color: #4CAF50; margin-top: 10px; }}
        button {{ background: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 1em; }}
        button:hover {{ background: #1976D2; }}
    </style>
</head>
<body>
    <h1>🌤️ ESP32 气象站 (模拟器)</h1>
    <div class="status">🖥️ PC 模拟模式</div>
    
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
    
    <div class="time">🕐 时间：{current_time}</div>
    
    <div class="refresh">
        <button onclick="location.reload()">🔄 刷新</button>
        <button onclick="adjustTemp()">⬆️ 升温</button>
        <button onclick="adjustHumidity()">💧 加湿</button>
    </div>
    
    <script>
        setTimeout(function() {{ location.reload(); }}, 5000);
        function adjustTemp() {{ 
            fetch('/adjust?temp=up'); 
            setTimeout(() => location.reload(), 500);
        }}
        function adjustHumidity() {{ 
            fetch('/adjust?humidity=up'); 
            setTimeout(() => location.reload(), 500);
        }}
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def do_GET_data(self):
        self.send_json()
    
    def send_json(self):
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data = {
            "temperature": round(temp, 1),
            "humidity": round(humidity, 1),
            "heatindex": round(heat_index, 1),
            "time": current_time,
            "mode": "simulator"
        }
        
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_GET_adjust(self):
        from urllib.parse import parse_qs, urlparse
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'temp' in params:
            sensor.base_temp += 1
        if 'humidity' in params:
            sensor.base_humidity += 5
        
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    
    def log_message(self, format, *args):
        print(f"[Web] {args[0]}")

def compute_heat_index(temp, humidity):
    # 简化体感温度计算
    return temp + (0.55 * (1 - humidity/100) * (temp - 14.5))

# ========== GUI 界面 ==========
class WeatherStationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 气象站模拟器")
        self.root.geometry("400x500")
        self.root.resizable(True, True)
        
        # 样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 标题
        title_frame = ttk.Frame(root)
        title_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = ttk.Label(
            title_frame, 
            text="🌤️ ESP32 气象站",
            font=('Arial', 16, 'bold')
        )
        title_label.pack()
        
        mode_label = ttk.Label(
            title_frame,
            text="🖥️ PC 模拟模式",
            font=('Arial', 10),
            foreground='green'
        )
        mode_label.pack()
        
        # 时间显示
        self.time_label = ttk.Label(
            root,
            text="",
            font=('Consolas', 12)
        )
        self.time_label.pack(pady=5)
        
        # 温度卡片
        temp_frame = ttk.LabelFrame(root, text="温度", padding=20)
        temp_frame.pack(fill='x', padx=20, pady=10)
        
        self.temp_value = ttk.Label(
            temp_frame,
            text="25.0°C",
            font=('Arial', 32, 'bold'),
            foreground='#2196F3'
        )
        self.temp_value.pack()
        
        # 湿度卡片
        humid_frame = ttk.LabelFrame(root, text="湿度", padding=20)
        humid_frame.pack(fill='x', padx=20, pady=10)
        
        self.humid_value = ttk.Label(
            humid_frame,
            text="60.0%",
            font=('Arial', 32, 'bold'),
            foreground='#2196F3'
        )
        self.humid_value.pack()
        
        # 体感温度
        heat_frame = ttk.LabelFrame(root, text="体感温度", padding=20)
        heat_frame.pack(fill='x', padx=20, pady=10)
        
        self.heat_value = ttk.Label(
            heat_frame,
            text="25.5°C",
            font=('Arial', 24, 'bold'),
            foreground='#FF9800'
        )
        self.heat_value.pack()
        
        # 控制按钮
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Button(
            btn_frame,
            text="🌡️ 升温",
            command=self.increase_temp
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        ttk.Button(
            btn_frame,
            text="❄️ 降温",
            command=self.decrease_temp
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        btn_frame2 = ttk.Frame(root)
        btn_frame2.pack(fill='x', padx=20, pady=5)
        
        ttk.Button(
            btn_frame2,
            text="💧 加湿",
            command=self.increase_humidity
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        ttk.Button(
            btn_frame2,
            text="🌬️ 除湿",
            command=self.decrease_humidity
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        # Web 服务器按钮
        web_frame = ttk.LabelFrame(root, text="Web 服务器", padding=10)
        web_frame.pack(fill='x', padx=20, pady=10)
        
        self.web_status = ttk.Label(
            web_frame,
            text="状态：未启动",
            foreground='red'
        )
        self.web_status.pack()
        
        btn_frame3 = ttk.Frame(web_frame)
        btn_frame3.pack(fill='x', pady=5)
        
        ttk.Button(
            btn_frame3,
            text="🌐 启动 Web 服务器",
            command=self.start_web_server
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        ttk.Button(
            btn_frame3,
            text="🔗 打开浏览器",
            command=self.open_browser
        ).pack(side='left', expand=True, fill='x', padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(root, text="日志", padding=5)
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.log_text = tk.Text(log_frame, height=6, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # 启动自动更新
        self.update_data()
        self.log("模拟器已启动")
    
    def update_data(self):
        temp, humidity = sensor.read()
        heat_index = compute_heat_index(temp, humidity)
        
        self.temp_value.config(text=f"{temp:.1f}°C")
        self.humid_value.config(text=f"{humidity:.1f}%")
        self.heat_value.config(text=f"{heat_index:.1f}°C")
        self.time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # 1 秒后再次更新
        self.root.after(1000, self.update_data)
    
    def increase_temp(self):
        sensor.base_temp += 1
        self.log(f"升温 -> 基础温度：{sensor.base_temp:.1f}°C")
    
    def decrease_temp(self):
        sensor.base_temp -= 1
        self.log(f"降温 -> 基础温度：{sensor.base_temp:.1f}°C")
    
    def increase_humidity(self):
        sensor.base_humidity += 5
        self.log(f"加湿 -> 基础湿度：{sensor.base_humidity:.1f}%")
    
    def decrease_humidity(self):
        sensor.base_humidity -= 5
        self.log(f"除湿 -> 基础湿度：{sensor.base_humidity:.1f}%")
    
    def start_web_server(self):
        def run_server():
            try:
                server = HTTPServer(('0.0.0.0', 8080), WeatherHandler)
                self.web_status.config(text="状态：运行中 (端口 8080)", foreground='green')
                self.log("Web 服务器已启动：http://localhost:8080")
                server.serve_forever()
            except Exception as e:
                self.log(f"Web 服务器错误：{e}")
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
    
    def open_browser(self):
        webbrowser.open('http://localhost:8080')
        self.log("已打开浏览器")
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')

# ========== 主程序 ==========
def main():
    root = tk.Tk()
    app = WeatherStationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
