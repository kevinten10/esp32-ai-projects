"""
ESP32 智能家居控制器 - 独立模拟器
==================================
模拟 Web 控制台 + 4 路继电器 + MQTT 状态推送。

运行: python smart_home_demo.py
访问: http://localhost:8081
"""

import tkinter as tk
from tkinter import scrolledtext
import json
import random
import threading
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── 状态 ──────────────────────────────────────
BG = "#1a1a2e"; BG2 = "#16213e"; BG3 = "#0f3460"
ACCENT = "#e94560"; GREEN = "#4ecca3"; ORANGE = "#f5a623"
TEXT = "#eee"; DIM = "#888"

devices = [
    {"id": "light",   "name": "💡 灯光", "pin": 26, "state": False},
    {"id": "fan",     "name": "🌀 风扇", "pin": 27, "state": False},
    {"id": "curtain", "name": "🪟 窗帘", "pin": 14, "state": False},
    {"id": "socket",  "name": "🔌 插座", "pin": 12, "state": False},
]
temp = 25.0
hum  = 60.0
log_lines = []

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    log_lines.append(line)
    if len(log_lines) > 200:
        log_lines.pop(0)
    print(line)

# ── HTTP 服务器 ──────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)

        def json_resp(data, code=200):
            body = json.dumps(data, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def html_resp(html):
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)

        if p == "/":
            html_resp(WEB_HTML)
        elif p == "/api/state":
            json_resp({"states": [d["state"] for d in devices],
                       "ip": "127.0.0.1", "mqtt": True,
                       "temp": round(temp, 1), "hum": round(hum, 1), "motion": False})
        elif p == "/api/toggle":
            idx = int(q.get("id", [0])[0])
            if 0 <= idx < 4:
                devices[idx]["state"] = not devices[idx]["state"]
                add_log(f"切换 {devices[idx]['name']} -> {'ON' if devices[idx]['state'] else 'OFF'}")
            json_resp({"ok": True})
        elif p == "/api/all":
            on = q.get("state", ["0"])[0] == "1"
            for d in devices: d["state"] = on
            add_log(f"全部 -> {'ON' if on else 'OFF'}")
            json_resp({"ok": True})
        else:
            self.send_error(404)

    def log_message(self, *a): pass

WEB_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>智能家居控制台 (Simulator)</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:sans-serif;background:#1a1a2e;color:#eee;padding:20px}
h1{text-align:center;color:#e94560;margin-bottom:4px}
.sub{text-align:center;color:#888;font-size:.8em;margin-bottom:20px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:480px;margin:0 auto 16px}
.card{background:#16213e;border-radius:16px;padding:20px;text-align:center;border:2px solid #0f3460;cursor:pointer;transition:all .2s}
.card.on{border-color:#4ecca3;background:#0d2b22}
.icon{font-size:2.5em;margin-bottom:8px}
.name{font-size:1em;color:#aaa;margin-bottom:12px}
.btn{padding:8px 24px;border:none;border-radius:20px;font-size:.9em;cursor:pointer;font-weight:bold}
.btn.on{background:#4ecca3;color:#0d2b22}
.btn.off{background:#333;color:#888}
.all-ctrl{max-width:480px;margin:0 auto 16px;display:flex;gap:12px;justify-content:center}
.ab{padding:10px 20px;border:none;border-radius:20px;cursor:pointer;font-weight:bold;font-size:.85em}
.info{max-width:480px;margin:0 auto;background:#16213e;border-radius:12px;padding:12px;text-align:center;color:#888;font-size:.8em}
</style></head><body>
<h1>🏠 智能家居</h1><p class="sub">ESP32 模拟器 | Simulator Mode</p>
<div class="all-ctrl">
<button class="ab" style="background:#4ecca3;color:#111" onclick="allOn()">全部开启</button>
<button class="ab" style="background:#e94560;color:#fff" onclick="allOff()">全部关闭</button>
</div>
<div class="grid" id="grid"></div>
<div class="info" id="st">加载中...</div>
<script>
const D=[{n:'灯光',i:'💡'},{n:'风扇',i:'🌀'},{n:'窗帘',i:'🪟'},{n:'插座',i:'🔌'}];
let S=[false,false,false,false];
function render(){
  document.getElementById('grid').innerHTML=D.map((d,i)=>`
  <div class="card ${S[i]?'on':''}" onclick="toggle(${i})">
    <div class="icon">${d.i}</div><div class="name">${d.n}</div>
    <button class="btn ${S[i]?'on':'off'}">${S[i]?'已开启':'已关闭'}</button>
  </div>`).join('');
}
async function load(){
  try{const r=await fetch('/api/state');const j=await r.json();S=j.states;render();
  document.getElementById('st').textContent=`Temp:${j.temp}°C Hum:${j.hum}% | ${new Date().toLocaleTimeString('zh-CN')}`;
  }catch(e){document.getElementById('st').textContent='连接失败';}
}
async function toggle(i){await fetch('/api/toggle?id='+i);load();}
async function allOn(){await fetch('/api/all?state=1');load();}
async function allOff(){await fetch('/api/all?state=0');load();}
load();setInterval(load,2000);
</script></body></html>"""

# ── Tkinter 界面 ──────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 智能家居 - 模拟器")
        self.geometry("640x520")
        self.configure(bg=BG)

        tk.Label(self, text="🏠 智能家居控制器", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(pady=(12, 4))
        tk.Label(self, text="http://localhost:8081", bg=BG, fg=GREEN,
                 font=("Consolas", 10)).pack()

        # 控制按钮
        bf = tk.Frame(self, bg=BG)
        bf.pack(pady=8)
        tk.Button(bf, text="全部开启", command=lambda: self._all(True),
                  bg=GREEN, fg="#111", font=("Arial", 9, "bold"),
                  relief="flat", width=10).pack(side="left", padx=4)
        tk.Button(bf, text="全部关闭", command=lambda: self._all(False),
                  bg=ACCENT, fg=TEXT, font=("Arial", 9, "bold"),
                  relief="flat", width=10).pack(side="left", padx=4)
        tk.Button(bf, text="🌐 浏览器", command=lambda: __import__('webbrowser').open("http://localhost:8081"),
                  bg=BG3, fg=TEXT, font=("Arial", 9, "bold"),
                  relief="flat", width=10).pack(side="left", padx=4)

        # 继电器
        gf = tk.Frame(self, bg=BG)
        gf.pack(padx=16, pady=8)
        self.btns = []
        self.lbls = []
        for i, d in enumerate(devices):
            r, c = divmod(i, 2)
            card = tk.Frame(gf, bg=BG2, relief="flat", bd=1)
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew", ipadx=20, ipady=10)
            gf.columnconfigure(c, weight=1)

            tk.Label(card, text=d["name"], bg=BG2, fg=TEXT,
                     font=("Arial", 12, "bold")).pack(pady=(8, 4))
            lbl = tk.Label(card, text="OFF", bg=BG2, fg=DIM, font=("Arial", 16, "bold"))
            lbl.pack()
            self.lbls.append(lbl)
            b = tk.Button(card, text="切换", command=lambda idx=i: self._toggle(idx),
                          bg=BG3, fg=TEXT, font=("Arial", 9), relief="flat")
            b.pack(pady=(4, 8))
            self.btns.append(b)

        # 日志
        tk.Label(self, text="📋 串口日志", bg=BG, fg=DIM,
                 font=("Arial", 9)).pack(anchor="w", padx=16)
        self.log_txt = scrolledtext.ScrolledText(self, height=8, bg="#0a0a0a",
            fg=GREEN, font=("Consolas", 9), state="disabled", relief="flat")
        self.log_txt.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        self._update()

    def _toggle(self, idx):
        devices[idx]["state"] = not devices[idx]["state"]
        add_log(f"MQTT PUB home/esp32-home/{devices[idx]['id']}/state -> {'ON' if devices[idx]['state'] else 'OFF'}")

    def _all(self, on):
        for d in devices: d["state"] = on
        add_log(f"MQTT PUB home/esp32-home/all -> {'ON' if on else 'OFF'}")

    def _update(self):
        for i, d in enumerate(devices):
            on = d["state"]
            self.lbls[i].config(text="ON" if on else "OFF",
                                fg=GREEN if on else DIM)
            self.btns[i].config(bg=GREEN if on else BG3,
                                fg="#111" if on else TEXT)
        # 更新日志
        if log_lines:
            self.log_txt.config(state="normal")
            self.log_txt.delete("1.0", "end")
            self.log_txt.insert("end", "\n".join(log_lines[-50:]))
            self.log_txt.see("end")
            self.log_txt.config(state="disabled")
        self.after(500, self._update)

if __name__ == "__main__":
    # 启动 HTTP 服务器
    server = HTTPServer(("0.0.0.0", 8081), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    add_log("HTTP 服务器已启动: http://localhost:8081")
    add_log("MQTT 模拟已连接: broker=192.168.1.20:1883")
    add_log("HA MQTT Discovery 已发布 4 个 switch 实体")

    app = App()
    app.mainloop()
