"""
ESP32 AI Projects - 统一演示平台
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
无需硬件，在 PC 上演示所有 ESP32 项目功能。

包含：
  Tab1: 气象站    - 温湿度传感器、体感温度、Web API
  Tab2: 智能家居  - 4路继电器、MQTT状态、Web控制台
  Tab3: 语音控制  - 拍手检测（空格键模拟）、音量波形
  Tab4: 手势识别  - 方向手势（方向键）、亮度/设备控制
  Tab5: IR遥控    - 空调控制、学码/发射演示
  Tab6: RF网关    - 433MHz设备管理、抓码/发射

运行方法：
  python esp32_demo.py
  或双击 run_demo.bat
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import random
import math
import threading
import time
import json
import webbrowser
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ═══════════════════════════════════════════════════════════
# 颜色主题（深色）
# ═══════════════════════════════════════════════════════════
BG       = "#1a1a2e"
BG2      = "#16213e"
BG3      = "#0f3460"
ACCENT   = "#e94560"
GREEN    = "#4ecca3"
BLUE     = "#2196F3"
ORANGE   = "#f5a623"
TEXT     = "#eeeeee"
TEXT_DIM = "#888888"
FONT_MONO = ("Consolas", 9)

# ═══════════════════════════════════════════════════════════
# 全局应用状态（所有 Tab 共享）
# ═══════════════════════════════════════════════════════════
class AppState:
    # 气象站
    temperature = 25.0
    humidity    = 60.0
    # 智能家居
    relays      = [False, False, False, False]
    relay_names = ["💡 灯光", "🌀 风扇", "🪟 窗帘", "🔌 插座"]
    # 语音控制
    mic_level   = 0
    clap_count  = 0
    last_clap   = 0
    voice_light = False
    voice_fan   = False
    # 手势控制
    brightness  = 50
    gest_light  = False
    gest_fan    = False
    last_gesture = "---"
    # IR 遥控
    ir_ac_power = False
    ir_ac_temp  = 26
    ir_ac_mode  = "cool"
    ir_learned  = []
    # RF 网关
    rf_devices  = []
    last_rf_recv = ""

state = AppState()

# ═══════════════════════════════════════════════════════════
# 全局日志缓冲
# ═══════════════════════════════════════════════════════════
_log_callbacks = []

def log(msg: str, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    for cb in _log_callbacks:
        try: cb(line + "\n")
        except: pass

# ═══════════════════════════════════════════════════════════
# HTTP 服务器（统一处理所有项目 API）
# ═══════════════════════════════════════════════════════════
class DemoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        def get(k, default=None):
            return params.get(k, [default])[0]

        # ── 路由 ──────────────────────────────────────
        # 气象站
        if path == "/weather":
            hi = self._heat_index(state.temperature, state.humidity)
            self._json({"temperature": round(state.temperature, 1),
                        "humidity":    round(state.humidity, 1),
                        "heatindex":   round(hi, 1),
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "mode": "simulator"})
        # 智能家居
        elif path == "/home/state":
            self._json({"relays": state.relays,
                        "names":  state.relay_names,
                        "ip": "127.0.0.1"})
        elif path == "/home/toggle":
            idx = int(get("id", 0))
            if 0 <= idx < 4:
                state.relays[idx] = not state.relays[idx]
                log(f"继电器 {state.relay_names[idx]} -> {'ON' if state.relays[idx] else 'OFF'}")
            self._json({"ok": True, "states": state.relays})
        elif path == "/home/all":
            on = get("state") == "1"
            state.relays = [on] * 4
            log(f"全部继电器 -> {'ON' if on else 'OFF'}")
            self._json({"ok": True})
        # 语音控制
        elif path == "/voice/state":
            self._json({"light": state.voice_light, "fan": state.voice_fan,
                        "level": state.mic_level})
        # 手势控制
        elif path == "/gesture/state":
            self._json({"brightness": state.brightness,
                        "light": state.gest_light, "fan": state.gest_fan,
                        "last": state.last_gesture})
        # IR
        elif path == "/ir/ac":
            self._json({"power": state.ir_ac_power, "temp": state.ir_ac_temp,
                        "mode": state.ir_ac_mode})
        elif path == "/ir/ac/set":
            state.ir_ac_power = get("power", "true") == "true"
            state.ir_ac_temp  = int(get("temp", 26))
            state.ir_ac_mode  = get("mode", "cool")
            log(f"AC: {'开' if state.ir_ac_power else '关'} {state.ir_ac_temp}°C {state.ir_ac_mode}")
            self._json({"ok": True})
        # RF
        elif path == "/rf/devices":
            self._json({"devices": state.rf_devices})
        # 主页
        elif path == "/" or path == "":
            self._html(self._index_html())
        else:
            self.send_error(404)

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def _heat_index(self, t, h):
        return t + 0.55 * (1 - h / 100) * (t - 14.5)

    def _index_html(self):
        return """<!DOCTYPE html><html lang="zh-CN">
<head><meta charset="UTF-8"><title>ESP32 Demo API</title>
<style>body{font-family:monospace;background:#1a1a2e;color:#4ecca3;padding:20px}
a{color:#e94560}h1{color:#e94560}li{margin:6px 0}</style></head>
<body><h1>📡 ESP32 Demo API</h1>
<p>所有 API 端点：</p><ul>
<li><a href="/weather">GET /weather</a> - 气象站数据</li>
<li><a href="/home/state">GET /home/state</a> - 智能家居状态</li>
<li>GET /home/toggle?id=0 - 切换继电器</li>
<li>GET /home/all?state=1 - 全部开/关</li>
<li><a href="/voice/state">GET /voice/state</a> - 语音控制状态</li>
<li><a href="/gesture/state">GET /gesture/state</a> - 手势控制状态</li>
<li><a href="/ir/ac">GET /ir/ac</a> - 空调状态</li>
<li><a href="/rf/devices">GET /rf/devices</a> - RF 设备列表</li>
</ul></body></html>"""

    def log_message(self, fmt, *args):
        pass  # 禁用默认 HTTP 日志

_http_server = None

def start_http_server(port=8080):
    global _http_server
    try:
        _http_server = HTTPServer(("0.0.0.0", port), DemoHandler)
        log(f"HTTP API 服务器已启动: http://localhost:{port}")
        _http_server.serve_forever()
    except Exception as e:
        log(f"HTTP 服务器启动失败: {e}", "ERROR")

# ═══════════════════════════════════════════════════════════
# 通用 UI 工具
# ═══════════════════════════════════════════════════════════
def make_card(parent, title="", **kwargs):
    """深色圆角卡片"""
    frame = tk.Frame(parent, bg=BG2, relief="flat", bd=0, **kwargs)
    if title:
        tk.Label(frame, text=title, bg=BG2, fg=GREEN,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8,2))
    return frame

def big_label(parent, text, color=GREEN, size=28):
    return tk.Label(parent, text=text, bg=BG2, fg=color,
                    font=("Arial", size, "bold"))

def small_label(parent, text, color=TEXT_DIM):
    return tk.Label(parent, text=text, bg=BG2, fg=color, font=("Arial", 9))

def btn(parent, text, cmd, color=ACCENT, fg=TEXT, width=12):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg=fg, relief="flat",
                     font=("Arial", 9, "bold"), width=width,
                     activebackground=BG3, activeforeground=TEXT,
                     cursor="hand2")

# ═══════════════════════════════════════════════════════════
# Tab 1：气象站
# ═══════════════════════════════════════════════════════════
class WeatherTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()
        self._update()

    def _heat_index(self, t, h):
        return t + 0.55 * (1 - h / 100) * (t - 14.5)

    def _build(self):
        # 顶部标题
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="🌤️  ESP32 气象站", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")
        self.time_lbl = tk.Label(hdr, text="", bg=BG, fg=TEXT_DIM,
                                  font=FONT_MONO)
        self.time_lbl.pack(side="right")

        # 三个数据卡片
        cards = tk.Frame(self, bg=BG)
        cards.pack(fill="x", padx=16, pady=8)
        for col in range(3):
            cards.columnconfigure(col, weight=1)

        def data_card(col, title, unit):
            c = make_card(cards)
            c.grid(row=0, column=col, padx=6, sticky="nsew")
            small_label(c, title).pack(pady=(10, 0))
            lbl = big_label(c, "--", BLUE, 32)
            lbl.pack()
            small_label(c, unit).pack(pady=(0, 10))
            return lbl

        self.temp_lbl = data_card(0, "温度 Temperature", "°C")
        self.hum_lbl  = data_card(1, "湿度 Humidity",    "%")
        self.heat_lbl = data_card(2, "体感温度 HeatIdx", "°C")

        # 历史折线（Canvas 绘制）
        chart_card = make_card(self, "📈 温度历史（最近60秒）")
        chart_card.pack(fill="x", padx=16, pady=8)
        self.canvas = tk.Canvas(chart_card, bg=BG3, height=100,
                                highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=(0, 10))
        self._history = []

        # 控制按钮
        ctrl = make_card(self, "🎛️  环境控制")
        ctrl.pack(fill="x", padx=16, pady=8)
        row = tk.Frame(ctrl, bg=BG2)
        row.pack(pady=10)
        for text, cmd in [("🌡️ +1°C", lambda: self._adj("temp", +1)),
                           ("❄️ -1°C", lambda: self._adj("temp", -1)),
                           ("💧 +5%",  lambda: self._adj("hum",  +5)),
                           ("🌬️ -5%",  lambda: self._adj("hum",  -5))]:
            btn(row, text, cmd, BG3, GREEN, 10).pack(side="left", padx=4)

        # Web API 按钮
        web = make_card(self, "🌐 Web API")
        web.pack(fill="x", padx=16, pady=8)
        wr = tk.Frame(web, bg=BG2)
        wr.pack(pady=8)
        btn(wr, "打开浏览器", lambda: webbrowser.open("http://localhost:8080/weather"),
            GREEN, "#111", 14).pack(side="left", padx=6)
        btn(wr, "查看 JSON", lambda: webbrowser.open("http://localhost:8080/weather"),
            BG3, TEXT, 14).pack(side="left", padx=6)

    def _adj(self, what, delta):
        if what == "temp":
            state.temperature = max(-40, min(85, state.temperature + delta))
            log(f"气象站温度调整: {state.temperature:.1f}°C")
        else:
            state.humidity = max(0, min(100, state.humidity + delta))
            log(f"气象站湿度调整: {state.humidity:.1f}%")

    def _update(self):
        # 随机波动
        state.temperature += random.uniform(-0.2, 0.2)
        state.humidity    += random.uniform(-0.5, 0.5)
        state.humidity     = max(20, min(95, state.humidity))

        t  = state.temperature
        h  = state.humidity
        hi = self._heat_index(t, h)

        self.temp_lbl.config(text=f"{t:.1f}")
        self.hum_lbl.config(text=f"{h:.1f}")
        self.heat_lbl.config(text=f"{hi:.1f}")
        self.time_lbl.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 历史
        self._history.append(t)
        if len(self._history) > 60:
            self._history.pop(0)
        self._draw_chart()

        self.after(1000, self._update)

    def _draw_chart(self):
        c = self.canvas
        w, h = c.winfo_width() or 400, 100
        c.delete("all")
        if len(self._history) < 2:
            return
        mn, mx = min(self._history) - 1, max(self._history) + 1
        span = mx - mn or 1
        pts = []
        for i, v in enumerate(self._history):
            x = int(i / (len(self._history) - 1) * (w - 20)) + 10
            y = int((1 - (v - mn) / span) * (h - 20)) + 10
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(pts, fill=GREEN, width=2, smooth=True)
        # 当前值标签
        c.create_text(w - 6, pts[-1] - 8, text=f"{self._history[-1]:.1f}°C",
                      fill=GREEN, font=FONT_MONO, anchor="e")

# ═══════════════════════════════════════════════════════════
# Tab 2：智能家居
# ═══════════════════════════════════════════════════════════
class SmartHomeTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.relay_btns = []
        self.relay_lbls = []
        self._build()
        self._update()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="🏠  ESP32 智能家居控制器", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")

        # 全部开/关
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(pady=6)
        btn(ctrl, "全部开启", lambda: self._all(True), GREEN, "#111", 12).pack(side="left", padx=6)
        btn(ctrl, "全部关闭", lambda: self._all(False), ACCENT, TEXT, 12).pack(side="left", padx=6)

        # 4 个继电器卡片（2×2）
        grid = tk.Frame(self, bg=BG)
        grid.pack(padx=16, pady=8)
        for i in range(4):
            r, c = divmod(i, 2)
            card = make_card(grid)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew",
                      ipadx=16, ipady=10)
            grid.columnconfigure(c, weight=1)

            tk.Label(card, text=state.relay_names[i], bg=BG2, fg=TEXT,
                     font=("Arial", 13, "bold")).pack(pady=(10, 6))
            lbl = tk.Label(card, text="OFF", bg=BG2, fg=TEXT_DIM,
                           font=("Arial", 18, "bold"))
            lbl.pack()
            self.relay_lbls.append(lbl)
            b = btn(card, "切换", lambda idx=i: self._toggle(idx), BG3, TEXT, 10)
            b.pack(pady=(6, 12))
            self.relay_btns.append(b)

        # 传感器区
        sens = make_card(self, "🌡️  环境传感器（DHT22）")
        sens.pack(fill="x", padx=16, pady=8)
        row = tk.Frame(sens, bg=BG2)
        row.pack(pady=10)
        self.sh_temp = big_label(row, "--°C", ORANGE, 20)
        self.sh_temp.pack(side="left", padx=20)
        self.sh_hum  = big_label(row, "--%", BLUE, 20)
        self.sh_hum.pack(side="left", padx=20)
        self.sh_pir  = tk.Label(row, text="PIR: 无人", bg=BG2, fg=TEXT_DIM,
                                 font=("Arial", 11))
        self.sh_pir.pack(side="left", padx=20)

        # MQTT 状态
        mqtt_card = make_card(self, "📡  MQTT 状态（模拟）")
        mqtt_card.pack(fill="x", padx=16, pady=8)
        self.mqtt_log = scrolledtext.ScrolledText(mqtt_card, height=5,
            bg="#111", fg=GREEN, font=FONT_MONO, state="disabled",
            relief="flat")
        self.mqtt_log.pack(fill="x", padx=10, pady=(0, 10))

        # Web 按钮
        wb = tk.Frame(self, bg=BG)
        wb.pack(pady=4)
        btn(wb, "🌐 Web 控制台", lambda: webbrowser.open("http://localhost:8080/home/state"),
            GREEN, "#111", 14).pack(side="left", padx=6)

    def _toggle(self, idx):
        state.relays[idx] = not state.relays[idx]
        self._mqtt_pub(f"home/esp32-home/{['light','fan','curtain','socket'][idx]}/state",
                       "ON" if state.relays[idx] else "OFF")
        log(f"智能家居 继电器{idx} -> {'ON' if state.relays[idx] else 'OFF'}")

    def _all(self, on):
        state.relays = [on] * 4
        self._mqtt_pub("home/esp32-home/all/state", "ON" if on else "OFF")
        log(f"智能家居 全部 -> {'ON' if on else 'OFF'}")

    def _mqtt_pub(self, topic, payload):
        msg = f"↑ PUB {topic}: {payload}"
        self.mqtt_log.config(state="normal")
        self.mqtt_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.mqtt_log.see("end")
        self.mqtt_log.config(state="disabled")

    def _update(self):
        for i, on in enumerate(state.relays):
            self.relay_lbls[i].config(
                text="ON" if on else "OFF",
                fg=GREEN if on else TEXT_DIM,
                bg=BG3 if on else BG2)
            self.relay_btns[i].config(
                bg=GREEN if on else BG3,
                fg="#111" if on else TEXT)
        self.relay_btns[0].master.config(bg=BG3 if state.relays[0] else BG2)
        self.sh_temp.config(text=f"{state.temperature:.1f}°C")
        self.sh_hum.config(text=f"{state.humidity:.1f}%")
        pir = random.random() < 0.15
        self.sh_pir.config(text="PIR: 有人" if pir else "PIR: 无人",
                           fg=ORANGE if pir else TEXT_DIM)
        self.after(800, self._update)

# ═══════════════════════════════════════════════════════════
# Tab 3：语音控制（空格键模拟拍手）
# ═══════════════════════════════════════════════════════════
class VoiceTab(tk.Frame):
    THRESHOLD = 600

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._wave_data   = [0] * 80
        self._clap_count  = 0
        self._last_clap_t = 0
        self._clap_timer  = None
        self._build()
        self._update()
        # 绑定空格键模拟拍手
        self.bind_all("<space>", self._on_clap)

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="🎙️  ESP32 声音/拍手控制", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")

        # 提示
        tk.Label(self, text="按  空格键  模拟拍手   |   1次=灯光  2次=风扇  3次=全关",
                 bg=BG, fg=GREEN, font=("Arial", 11)).pack(pady=6)

        # 音量波形
        wave_card = make_card(self, "📊 音量波形（实时）")
        wave_card.pack(fill="x", padx=16, pady=8)
        self.wave_canvas = tk.Canvas(wave_card, bg=BG3, height=120,
                                     highlightthickness=0)
        self.wave_canvas.pack(fill="x", padx=10, pady=(0, 6))

        info = tk.Frame(wave_card, bg=BG2)
        info.pack(fill="x", padx=10, pady=(0, 10))
        self.level_lbl = tk.Label(info, text="Level: 0", bg=BG2, fg=TEXT, font=FONT_MONO)
        self.level_lbl.pack(side="left")
        tk.Label(info, text="  阈值: 600", bg=BG2, fg=ORANGE, font=FONT_MONO).pack(side="left")
        self.clap_cnt_lbl = tk.Label(info, text="  拍手: 0次...", bg=BG2, fg=ACCENT,
                                      font=("Arial", 10, "bold"))
        self.clap_cnt_lbl.pack(side="left")

        # 设备状态
        dev_card = make_card(self, "💡 设备状态")
        dev_card.pack(fill="x", padx=16, pady=8)
        row = tk.Frame(dev_card, bg=BG2)
        row.pack(pady=12)
        self.light_lbl = tk.Label(row, text="💡 灯光\n OFF", bg=BG2, fg=TEXT_DIM,
                                   font=("Arial", 14, "bold"), width=12,
                                   relief="groove", padx=10, pady=10)
        self.light_lbl.pack(side="left", padx=12)
        self.fan_lbl = tk.Label(row, text="🌀 风扇\n OFF", bg=BG2, fg=TEXT_DIM,
                                  font=("Arial", 14, "bold"), width=12,
                                  relief="groove", padx=10, pady=10)
        self.fan_lbl.pack(side="left", padx=12)

        # 操作日志
        log_card = make_card(self, "📋 操作日志")
        log_card.pack(fill="both", expand=True, padx=16, pady=8)
        self.voice_log = scrolledtext.ScrolledText(log_card, height=6,
            bg="#111", fg=GREEN, font=FONT_MONO, state="disabled", relief="flat")
        self.voice_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_clap(self, event=None):
        now = time.time()
        if now - self._last_clap_t < 0.15:  # 消抖
            return
        self._last_clap_t = now
        self._clap_count  += 1
        state.mic_level    = random.randint(1200, 2800)
        self._wave_data.append(state.mic_level)
        self._vlog(f"[检测] 第 {self._clap_count} 次拍手，Level: {state.mic_level}")

        # 重置超时定时器
        if self._clap_timer:
            self.after_cancel(self._clap_timer)
        self._clap_timer = self.after(600, self._execute_clap)

    def _execute_clap(self):
        n = self._clap_count
        self._clap_count = 0
        self._clap_timer = None
        if n == 1:
            state.voice_light = not state.voice_light
            self._vlog(f"[命令] 1拍 → 灯光 {'ON' if state.voice_light else 'OFF'}")
        elif n == 2:
            state.voice_fan = not state.voice_fan
            self._vlog(f"[命令] 2拍 → 风扇 {'ON' if state.voice_fan else 'OFF'}")
        elif n >= 3:
            state.voice_light = state.voice_fan = False
            self._vlog(f"[命令] {n}拍 → 全部关闭")

    def _vlog(self, msg):
        self.voice_log.config(state="normal")
        self.voice_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.voice_log.see("end")
        self.voice_log.config(state="disabled")

    def _update(self):
        # 环境噪声模拟
        noise = random.randint(30, 120)
        if state.mic_level > 0:
            state.mic_level = max(0, state.mic_level - random.randint(80, 200))
        level = noise if state.mic_level == 0 else state.mic_level
        self._wave_data.append(level)
        if len(self._wave_data) > 80:
            self._wave_data.pop(0)

        # 绘制波形
        c = self.wave_canvas
        w = c.winfo_width() or 400
        h_c = 120
        c.delete("all")
        # 阈值线
        ty = int((1 - self.THRESHOLD / 4096) * h_c)
        c.create_line(0, ty, w, ty, fill=ORANGE, dash=(4, 4))
        c.create_text(w - 4, ty - 8, text="阈值", fill=ORANGE, font=FONT_MONO, anchor="e")
        # 波形
        pts = []
        for i, v in enumerate(self._wave_data):
            x = int(i / len(self._wave_data) * w)
            y = int((1 - min(v, 4096) / 4096) * h_c)
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(pts, fill=GREEN, width=2)

        # 更新标签
        self.level_lbl.config(text=f"Level: {level}")
        cnt_txt = f"  拍手: {self._clap_count}次..." if self._clap_count > 0 else "  等待拍手..."
        self.clap_cnt_lbl.config(text=cnt_txt)

        # 设备状态
        for lbl, on, icon, name in [
            (self.light_lbl, state.voice_light, "💡", "灯光"),
            (self.fan_lbl,   state.voice_fan,   "🌀", "风扇")]:
            lbl.config(text=f"{icon} {name}\n {'ON' if on else 'OFF'}",
                       fg=GREEN if on else TEXT_DIM,
                       bg=BG3 if on else BG2)

        self.after(80, self._update)

# ═══════════════════════════════════════════════════════════
# Tab 4：手势控制（方向键模拟）
# ═══════════════════════════════════════════════════════════
class GestureTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._last_gest_t = 0
        self._build()
        self._update()
        self.bind_all("<Up>",    lambda e: self._gesture("UP"))
        self.bind_all("<Down>",  lambda e: self._gesture("DOWN"))
        self.bind_all("<Left>",  lambda e: self._gesture("LEFT"))
        self.bind_all("<Right>", lambda e: self._gesture("RIGHT"))

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="✋  ESP32 手势识别控制", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")

        tk.Label(self,
            text="方向键 ↑↓←→ 模拟手势   |   ↑↓=亮度   ←=灯光   →=风扇",
            bg=BG, fg=GREEN, font=("Arial", 11)).pack(pady=6)

        # 手势显示
        gest_card = make_card(self, "👋 当前手势")
        gest_card.pack(fill="x", padx=16, pady=8)
        row = tk.Frame(gest_card, bg=BG2)
        row.pack(pady=14)

        self.gest_lbl = tk.Label(row, text="---", bg=BG2, fg=GREEN,
                                  font=("Arial", 36, "bold"), width=8)
        self.gest_lbl.pack(side="left", padx=20)

        self.gest_action = tk.Label(row, text="等待手势...", bg=BG2, fg=TEXT_DIM,
                                     font=("Arial", 12))
        self.gest_action.pack(side="left", padx=10)

        # 亮度控制
        bri_card = make_card(self, "☀️ 亮度控制（↑↓ 手势）")
        bri_card.pack(fill="x", padx=16, pady=8)
        bri_row = tk.Frame(bri_card, bg=BG2)
        bri_row.pack(pady=12)
        self.bri_bar = tk.Canvas(bri_row, bg=BG3, width=300, height=20,
                                  highlightthickness=0)
        self.bri_bar.pack(side="left", padx=10)
        self.bri_lbl = tk.Label(bri_row, text="50%", bg=BG2, fg=ORANGE,
                                 font=("Arial", 14, "bold"), width=5)
        self.bri_lbl.pack(side="left")

        # 设备状态
        dev_card = make_card(self, "🏠 设备状态（←→ 手势）")
        dev_card.pack(fill="x", padx=16, pady=8)
        dev_row = tk.Frame(dev_card, bg=BG2)
        dev_row.pack(pady=12)
        self.gest_light = tk.Label(dev_row, text="💡 灯光\n OFF", bg=BG2, fg=TEXT_DIM,
                                    font=("Arial", 13, "bold"), width=12,
                                    relief="groove", padx=12, pady=12)
        self.gest_light.pack(side="left", padx=12)
        self.gest_fan = tk.Label(dev_row, text="🌀 风扇\n OFF", bg=BG2, fg=TEXT_DIM,
                                  font=("Arial", 13, "bold"), width=12,
                                  relief="groove", padx=12, pady=12)
        self.gest_fan.pack(side="left", padx=12)

        # 手势历史
        hist_card = make_card(self, "📋 手势历史")
        hist_card.pack(fill="both", expand=True, padx=16, pady=8)
        self.gest_log = scrolledtext.ScrolledText(hist_card, height=5,
            bg="#111", fg=GREEN, font=FONT_MONO, state="disabled", relief="flat")
        self.gest_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _gesture(self, direction):
        now = time.time()
        if now - self._last_gest_t < 0.3:
            return
        self._last_gest_t = now
        state.last_gesture = direction

        icons = {"UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→"}
        icon = icons.get(direction, "?")

        if direction == "UP":
            state.brightness = min(100, state.brightness + 12)
            action = f"亮度 +12% → {state.brightness}%"
        elif direction == "DOWN":
            state.brightness = max(0, state.brightness - 12)
            action = f"亮度 -12% → {state.brightness}%"
        elif direction == "LEFT":
            state.gest_light = not state.gest_light
            action = f"灯光 → {'ON' if state.gest_light else 'OFF'}"
        elif direction == "RIGHT":
            state.gest_fan = not state.gest_fan
            action = f"风扇 → {'ON' if state.gest_fan else 'OFF'}"
        else:
            action = ""

        self.gest_lbl.config(text=icon)
        self.gest_action.config(text=action, fg=GREEN)
        self._glog(f"[{icon}] {direction}: {action}")
        log(f"手势识别 {direction}: {action}")
        self.after(2000, lambda: self.gest_action.config(fg=TEXT_DIM))

    def _glog(self, msg):
        self.gest_log.config(state="normal")
        self.gest_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.gest_log.see("end")
        self.gest_log.config(state="disabled")

    def _update(self):
        # 亮度条
        c = self.bri_bar
        w = c.winfo_width() or 300
        c.delete("all")
        bw = int(state.brightness / 100 * (w - 4))
        c.create_rectangle(2, 2, bw + 2, 18,
                            fill=ORANGE if state.brightness > 60 else GREEN,
                            outline="")
        self.bri_lbl.config(text=f"{state.brightness}%")

        # 设备标签
        for lbl, on, icon, name in [
            (self.gest_light, state.gest_light, "💡", "灯光"),
            (self.gest_fan,   state.gest_fan,   "🌀", "风扇")]:
            lbl.config(text=f"{icon} {name}\n {'ON' if on else 'OFF'}",
                       fg=GREEN if on else TEXT_DIM,
                       bg=BG3 if on else BG2)

        self.after(200, self._update)

# ═══════════════════════════════════════════════════════════
# Tab 5：IR 红外遥控
# ═══════════════════════════════════════════════════════════
class IRTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="📡  ESP32 IR 红外遥控器", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")

        # 空调控制面板
        ac = make_card(self, "🌡️ 空调控制（美的协议 Demo）")
        ac.pack(fill="x", padx=16, pady=8)

        # 电源 + 温度
        row1 = tk.Frame(ac, bg=BG2)
        row1.pack(pady=10)
        self.ac_power_lbl = tk.Label(row1, text="⏻  OFF", bg=BG2, fg=TEXT_DIM,
                                      font=("Arial", 20, "bold"), width=8)
        self.ac_power_lbl.pack(side="left", padx=12)
        btn(row1, "开机", lambda: self._ac(True), GREEN, "#111", 8).pack(side="left", padx=4)
        btn(row1, "关机", lambda: self._ac(False), ACCENT, TEXT, 8).pack(side="left", padx=4)

        # 温度调节
        row2 = tk.Frame(ac, bg=BG2)
        row2.pack(pady=8)
        self.temp_lbl = tk.Label(row2, text=f"{state.ir_ac_temp}°C", bg=BG2, fg=BLUE,
                                  font=("Arial", 28, "bold"))
        self.temp_lbl.pack(side="left", padx=12)
        btn(row2, "▲", lambda: self._set_temp(+1), BG3, TEXT, 4).pack(side="left", padx=2)
        btn(row2, "▼", lambda: self._set_temp(-1), BG3, TEXT, 4).pack(side="left", padx=2)

        # 模式
        row3 = tk.Frame(ac, bg=BG2)
        row3.pack(pady=8)
        for mode, label in [("cool","❄️ 制冷"), ("heat","🔥 制热"),
                              ("fan_only","💨 送风"), ("dry","💧 除湿")]:
            btn(row3, label, lambda m=mode: self._set_mode(m),
                BLUE if state.ir_ac_mode == mode else BG3, TEXT, 9
                ).pack(side="left", padx=4)
        self.mode_btns_row = row3

        # 发射状态
        self.ir_status = tk.Label(ac, text="就绪", bg=BG2, fg=TEXT_DIM,
                                   font=FONT_MONO)
        self.ir_status.pack(pady=(0, 10))

        # 学码区
        learn = make_card(self, "🎓 学习遥控码（演示）")
        learn.pack(fill="x", padx=16, pady=8)
        lr = tk.Frame(learn, bg=BG2)
        lr.pack(pady=8)
        self.learn_name = tk.Entry(lr, bg="#111", fg=TEXT, font=("Arial", 10),
                                    width=20, relief="flat", insertbackground=TEXT)
        self.learn_name.insert(0, "电视开机")
        self.learn_name.pack(side="left", padx=6)
        btn(lr, "模拟学码", self._learn_code, GREEN, "#111", 10).pack(side="left", padx=4)

        # 已学码列表
        self.learned_frame = tk.Frame(learn, bg=BG2)
        self.learned_frame.pack(fill="x", padx=10, pady=(0, 10))

        # IR 日志
        log_card = make_card(self, "📋 IR 发射日志")
        log_card.pack(fill="both", expand=True, padx=16, pady=8)
        self.ir_log = scrolledtext.ScrolledText(log_card, height=5,
            bg="#111", fg=GREEN, font=FONT_MONO, state="disabled", relief="flat")
        self.ir_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _ilog(self, msg):
        self.ir_log.config(state="normal")
        self.ir_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.ir_log.see("end")
        self.ir_log.config(state="disabled")

    def _ac(self, on):
        state.ir_ac_power = on
        self.ac_power_lbl.config(
            text=f"⏻  {'ON' if on else 'OFF'}",
            fg=GREEN if on else TEXT_DIM)
        code = random.randint(0x100000, 0xFFFFFF)
        msg = f"[IR发射] 美的空调 {'开机' if on else '关机'} code=0x{code:06X}"
        self.ir_status.config(text=msg, fg=GREEN if on else ACCENT)
        self._ilog(msg)
        log(f"IR 空调 {'开' if on else '关'}")

    def _set_temp(self, delta):
        state.ir_ac_temp = max(16, min(30, state.ir_ac_temp + delta))
        self.temp_lbl.config(text=f"{state.ir_ac_temp}°C")
        if state.ir_ac_power:
            code = random.randint(0x100000, 0xFFFFFF)
            self._ilog(f"[IR发射] 温度 {state.ir_ac_temp}°C code=0x{code:06X}")

    def _set_mode(self, mode):
        state.ir_ac_mode = mode
        code = random.randint(0x100000, 0xFFFFFF)
        self._ilog(f"[IR发射] 模式切换 {mode} code=0x{code:06X}")

    def _learn_code(self):
        name = self.learn_name.get().strip() or "未命名"
        code = random.randint(0x100000, 0xFFFFFF)
        proto = random.choice(["NEC", "SAMSUNG", "SONY", "RC5"])
        state.ir_learned.append({"name": name, "code": code, "proto": proto})
        self._ilog(f"[学码成功] {name}: 协议={proto} 码=0x{code:06X}")

        # 刷新已学码按钮
        for w in self.learned_frame.winfo_children():
            w.destroy()
        for item in state.ir_learned:
            btn(self.learned_frame, f"📤 {item['name']}",
                lambda c=item: self._ilog(f"[IR发射] {c['name']} code=0x{c['code']:06X}"),
                BG3, TEXT, 14).pack(side="left", padx=4, pady=4)

# ═══════════════════════════════════════════════════════════
# Tab 6：RF 433MHz 网关
# ═══════════════════════════════════════════════════════════
class RFTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()
        self._recv_running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _build(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(hdr, text="📻  ESP32 433MHz RF 网关", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(side="left")

        # 设备管理
        dev_card = make_card(self, "🏠 已添加的 RF 设备")
        dev_card.pack(fill="x", padx=16, pady=8)
        self.dev_frame = tk.Frame(dev_card, bg=BG2)
        self.dev_frame.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(self.dev_frame, text="（尚未添加设备，请学码添加）",
                 bg=BG2, fg=TEXT_DIM, font=("Arial", 10)).pack(pady=8)

        # 添加设备（学码）
        add_card = make_card(self, "🎓 添加设备（学码）")
        add_card.pack(fill="x", padx=16, pady=8)
        row = tk.Frame(add_card, bg=BG2)
        row.pack(pady=8)
        self.dev_name = tk.Entry(row, bg="#111", fg=TEXT, font=("Arial", 10),
                                  width=16, relief="flat", insertbackground=TEXT)
        self.dev_name.insert(0, "客厅插座1")
        self.dev_name.pack(side="left", padx=6)
        self.dev_room = tk.Entry(row, bg="#111", fg=TEXT, font=("Arial", 10),
                                  width=10, relief="flat", insertbackground=TEXT)
        self.dev_room.insert(0, "客厅")
        self.dev_room.pack(side="left", padx=6)
        btn(row, "开始学码", self._learn_rf, GREEN, "#111", 10).pack(side="left", padx=4)

        self.learn_status = tk.Label(add_card, text="就绪", bg=BG2, fg=TEXT_DIM,
                                      font=FONT_MONO)
        self.learn_status.pack(pady=(0, 8))

        # 手动发射
        manual = make_card(self, "📡 手动发射测试")
        manual.pack(fill="x", padx=16, pady=8)
        mr = tk.Frame(manual, bg=BG2)
        mr.pack(pady=8)
        self.manual_code = tk.Entry(mr, bg="#111", fg=TEXT, font=("Arial", 10),
                                     width=14, relief="flat", insertbackground=TEXT)
        self.manual_code.insert(0, "16711680")
        self.manual_code.pack(side="left", padx=6)
        btn(mr, "发射", self._manual_send, ACCENT, TEXT, 8).pack(side="left", padx=4)

        # RF 接收日志
        log_card = make_card(self, "📡 RF 接收监听（模拟）")
        log_card.pack(fill="both", expand=True, padx=16, pady=8)
        self.rf_log = scrolledtext.ScrolledText(log_card, height=6,
            bg="#111", fg=GREEN, font=FONT_MONO, state="disabled", relief="flat")
        self.rf_log.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _rlog(self, msg):
        self.rf_log.config(state="normal")
        self.rf_log.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.rf_log.see("end")
        self.rf_log.config(state="disabled")

    def _learn_rf(self):
        name = self.dev_name.get().strip() or "未命名"
        room = self.dev_room.get().strip() or "未分类"
        self.learn_status.config(text="学码中... 请按遥控器（模拟3秒后完成）", fg=ORANGE)

        def do_learn():
            time.sleep(3)
            code_on  = random.randint(1000000, 16777215)
            code_off = code_on ^ random.randint(0xFF, 0xFFF)
            dev = {"name": name, "room": room,
                   "code_on": code_on, "code_off": code_off, "state": False}
            state.rf_devices.append(dev)
            self.after(0, lambda: self.learn_status.config(
                text=f"✅ 学码成功: {name}  开={code_on}  关={code_off}", fg=GREEN))
            self.after(0, lambda: self._rlog(
                f"[学码] {name}({room}) 开={code_on} 关={code_off}"))
            self.after(0, self._refresh_devices)

        threading.Thread(target=do_learn, daemon=True).start()

    def _refresh_devices(self):
        for w in self.dev_frame.winfo_children():
            w.destroy()
        if not state.rf_devices:
            tk.Label(self.dev_frame, text="（尚未添加设备）",
                     bg=BG2, fg=TEXT_DIM).pack(pady=8)
            return
        for i, d in enumerate(state.rf_devices):
            row = tk.Frame(self.dev_frame, bg=BG3 if d["state"] else BG2)
            row.pack(fill="x", padx=4, pady=3)
            tk.Label(row, text=f"[{d['room']}] {d['name']}",
                     bg=row["bg"], fg=TEXT, font=("Arial", 10, "bold"),
                     width=20).pack(side="left", padx=8, pady=6)
            state_lbl = tk.Label(row, text="ON" if d["state"] else "OFF",
                                  bg=row["bg"], fg=GREEN if d["state"] else TEXT_DIM,
                                  font=("Arial", 10, "bold"), width=4)
            state_lbl.pack(side="left")
            btn(row, "开", lambda idx=i: self._ctrl(idx, True), GREEN, "#111", 4
                ).pack(side="left", padx=2)
            btn(row, "关", lambda idx=i: self._ctrl(idx, False), ACCENT, TEXT, 4
                ).pack(side="left", padx=2)

    def _ctrl(self, idx, on):
        d = state.rf_devices[idx]
        d["state"] = on
        code = d["code_on"] if on else d["code_off"]
        self._rlog(f"[RF发射] {d['name']} {'开' if on else '关'} code={code}")
        log(f"RF 发射 {d['name']} {'ON' if on else 'OFF'}")
        self._refresh_devices()

    def _manual_send(self):
        code = self.manual_code.get().strip()
        self._rlog(f"[RF发射] 手动 code={code} protocol=1 bits=24")

    def _recv_loop(self):
        protos = ["EV1527", "PT2262", "HX2262"]
        while self._recv_running:
            time.sleep(random.uniform(8, 20))
            code = random.randint(100000, 16777215)
            proto = random.choice(protos)
            msg = f"[RF接收] code={code} 协议={proto} bits=24"
            state.last_rf_recv = msg
            self.after(0, lambda m=msg: self._rlog(m))

# ═══════════════════════════════════════════════════════════
# 全局日志 Tab
# ═══════════════════════════════════════════════════════════
class LogTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build()

    def _build(self):
        tk.Label(self, text="📋  全局系统日志", bg=BG, fg=ACCENT,
                 font=("Arial", 14, "bold")).pack(padx=16, pady=12, anchor="w")

        info = tk.Frame(self, bg=BG)
        info.pack(fill="x", padx=16, pady=4)
        tk.Label(info, text=f"HTTP API: http://localhost:8080",
                 bg=BG, fg=GREEN, font=FONT_MONO).pack(side="left")
        btn(info, "打开 API 文档", lambda: webbrowser.open("http://localhost:8080"),
            BG3, TEXT, 14).pack(side="right", padx=4)

        self.log_txt = scrolledtext.ScrolledText(
            self, height=30, bg="#0a0a0a", fg=GREEN,
            font=FONT_MONO, state="disabled", relief="flat")
        self.log_txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        def append(line):
            self.log_txt.config(state="normal")
            self.log_txt.insert("end", line)
            self.log_txt.see("end")
            self.log_txt.config(state="disabled")

        _log_callbacks.append(append)

# ═══════════════════════════════════════════════════════════
# 主窗口
# ═══════════════════════════════════════════════════════════
class ESP32DemoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 AI Projects - 统一演示平台")
        self.geometry("820x680")
        self.minsize(720, 600)
        self.configure(bg=BG)

        # 顶部 banner
        banner = tk.Frame(self, bg=ACCENT, height=4)
        banner.pack(fill="x")

        # Notebook（标签页）
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",      background=BG,  borderwidth=0)
        style.configure("TNotebook.Tab",  background=BG2, foreground=TEXT,
                         padding=[12, 6], font=("Arial", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", BG3)],
                  foreground=[("selected", GREEN)])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("🌤 气象站",   WeatherTab),
            ("🏠 智能家居", SmartHomeTab),
            ("🎙 语音控制", VoiceTab),
            ("✋ 手势识别", GestureTab),
            ("📡 IR 遥控",  IRTab),
            ("📻 RF 网关",  RFTab),
            ("📋 系统日志", LogTab),
        ]
        for name, cls in tabs:
            tab = cls(nb)
            nb.add(tab, text=name)

        # 状态栏
        bar = tk.Frame(self, bg=BG2, height=28)
        bar.pack(fill="x", side="bottom")
        self.status_lbl = tk.Label(bar, text="⚡ ESP32 Demo 已就绪",
                                    bg=BG2, fg=GREEN, font=FONT_MONO)
        self.status_lbl.pack(side="left", padx=12, pady=4)
        tk.Label(bar, text="http://localhost:8080",
                 bg=BG2, fg=TEXT_DIM, font=FONT_MONO).pack(side="right", padx=12)

        # 启动 HTTP 服务器（后台线程）
        threading.Thread(target=start_http_server, daemon=True).start()
        log("ESP32 统一演示平台已启动")
        log("快捷键：空格=拍手  方向键=手势  Ctrl+W=退出")

    def run(self):
        self.mainloop()

# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ESP32DemoApp()
    app.run()
