"""
ESP32 433MHz RF 智能网关 - 独立模拟器
======================================
模拟 RF 学码、发射、设备管理，含 HTTP API。

运行: python rf_demo.py
访问: http://localhost:8083
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

BG = "#1a1a2e"; BG2 = "#16213e"; BG3 = "#0f3460"
ACCENT = "#e94560"; GREEN = "#4ecca3"; ORANGE = "#f5a623"; BLUE = "#2196F3"
TEXT = "#eee"; DIM = "#888"

devices = []
log_lines = []

def add_log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    log_lines.append(line)
    if len(log_lines) > 200: log_lines.pop(0)
    print(line)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urlparse(self.path).path
        q = parse_qs(urlparse(self.path).query)
        def get(k, d=None): return q.get(k, [d])[0]
        def ok(d=None):
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(d or {"ok": True}, ensure_ascii=False).encode())

        if p == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(WEB_HTML.encode())
        elif p == "/api/devices":
            ok({"devices": devices})
        elif p == "/api/ctrl":
            idx = int(get("idx", -1))
            on  = get("state", "1") == "1"
            if 0 <= idx < len(devices):
                devices[idx]["state"] = on
                code = devices[idx]["code_on"] if on else devices[idx]["code_off"]
                add_log(f"[RF发射] {devices[idx]['name']} {'开' if on else '关'} code={code}")
            ok()
        elif p == "/api/learn":
            name = get("name", "未命名")
            room = get("room", "未分类")
            code_on  = random.randint(1000000, 16777215)
            code_off = code_on ^ random.randint(0xFF, 0xFFF)
            devices.append({"name": name, "room": room,
                            "code_on": code_on, "code_off": code_off, "state": False})
            add_log(f"[学码成功] {name}({room}) 开={code_on} 关={code_off}")
            ok({"ok": True, "code_on": code_on, "code_off": code_off})
        elif p == "/api/rawsend":
            code = get("code", "0")
            add_log(f"[RF发射] 手动 code={code} protocol=1 bits=24")
            ok()
        else:
            self.send_error(404)
    def log_message(self, *a): pass

WEB_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RF 433MHz 网关 (Simulator)</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#eee;font-family:sans-serif;padding:20px}
h1{color:#e94560;text-align:center;margin-bottom:16px}
.s{background:#16213e;border-radius:12px;padding:16px;margin-bottom:14px}
h2{color:#4ecca3;font-size:1em;margin-bottom:10px}
.b{padding:10px 18px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:.85em;margin:3px}
.bg{background:#4ecca3;color:#111}.br{background:#e94560;color:#fff}
</style></head><body>
<h1>📻 RF 433MHz 网关 (Simulator)</h1>
<div class="s"><h2>添加设备</h2>
<input id="n" placeholder="设备名" style="background:#111;color:#eee;border:1px solid #333;padding:8px;border-radius:4px;width:40%">
<input id="r" placeholder="房间" style="background:#111;color:#eee;border:1px solid #333;padding:8px;border-radius:4px;width:20%">
<button class="b bg" onclick="learn()">学码添加</button>
</div>
<div class="s" id="devs"><h2>设备列表</h2><p style="color:#888">暂无</p></div>
<script>
async function learn(){
  const n=document.getElementById('n').value||'未命名';
  const r=document.getElementById('r').value||'未分类';
  await fetch('/api/learn?name='+encodeURIComponent(n)+'&room='+encodeURIComponent(r));
  load();
}
async function ctrl(i,s){await fetch('/api/ctrl?idx='+i+'&state='+s);load();}
async function load(){
  const j=await (await fetch('/api/devices')).json();
  const el=document.getElementById('devs');
  if(!j.devices.length){el.innerHTML='<h2>设备列表</h2><p style="color:#888">暂无</p>';return;}
  el.innerHTML='<h2>设备列表</h2>'+j.devices.map((d,i)=>
    `<div style="margin:6px 0;padding:8px;background:#0f3460;border-radius:8px">
    [${d.room}] ${d.name} <b>${d.state?'ON':'OFF'}</b>
    <button class="b bg" style="padding:4px 10px" onclick="ctrl(${i},1)">开</button>
    <button class="b br" style="padding:4px 10px" onclick="ctrl(${i},0)">关</button>
    </div>`).join('');
}
load();setInterval(load,2000);
</script></body></html>"""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 RF 433MHz 网关 - 模拟器")
        self.geometry("640x560")
        self.configure(bg=BG)

        tk.Label(self, text="📻 RF 433MHz 智能网关", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(pady=(12, 2))
        tk.Label(self, text="http://localhost:8083", bg=BG, fg=GREEN,
                 font=("Consolas", 10)).pack()

        # 添加设备
        af = tk.Frame(self, bg=BG2)
        af.pack(fill="x", padx=16, pady=8)
        tk.Label(af, text="🎓 添加设备（学码）", bg=BG2, fg=GREEN,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        ar = tk.Frame(af, bg=BG2); ar.pack(pady=(0, 8))
        self.name_e = tk.Entry(ar, bg="#111", fg=TEXT, width=14, relief="flat",
                                font=("Arial", 10), insertbackground=TEXT)
        self.name_e.insert(0, "客厅插座1")
        self.name_e.pack(side="left", padx=4)
        self.room_e = tk.Entry(ar, bg="#111", fg=TEXT, width=10, relief="flat",
                                font=("Arial", 10), insertbackground=TEXT)
        self.room_e.insert(0, "客厅")
        self.room_e.pack(side="left", padx=4)
        tk.Button(ar, text="学码添加", command=self._learn,
                  bg=GREEN, fg="#111", font=("Arial", 9, "bold"), relief="flat"
                  ).pack(side="left", padx=4)
        tk.Button(ar, text="🌐 浏览器", command=lambda: __import__('webbrowser').open("http://localhost:8083"),
                  bg=BG3, fg=TEXT, font=("Arial", 9, "bold"), relief="flat"
                  ).pack(side="left", padx=4)

        self.learn_lbl = tk.Label(af, text="", bg=BG2, fg=ORANGE,
                                   font=("Consolas", 9))
        self.learn_lbl.pack(pady=(0, 8))

        # 设备列表
        df = tk.Frame(self, bg=BG2)
        df.pack(fill="x", padx=16, pady=4)
        tk.Label(df, text="🏠 已添加的 RF 设备", bg=BG2, fg=GREEN,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        self.dev_frame = tk.Frame(df, bg=BG2)
        self.dev_frame.pack(fill="x", padx=10, pady=(0, 10))

        # RF 监听
        rf = tk.Frame(self, bg=BG2)
        rf.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(rf, text="📡 RF 接收监听", bg=BG2, fg=DIM,
                 font=("Arial", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.log = scrolledtext.ScrolledText(rf, height=8, bg="#0a0a0a",
            fg=GREEN, font=("Consolas", 9), state="disabled", relief="flat")
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        # 后台模拟接收
        self._running = True
        threading.Thread(target=self._recv_loop, daemon=True).start()
        self._update_log()

    def _learn(self):
        name = self.name_e.get().strip() or "未命名"
        room = self.room_e.get().strip() or "未分类"
        self.learn_lbl.config(text="学码中... 3秒后完成", fg=ORANGE)

        def do():
            time.sleep(3)
            code_on  = random.randint(1000000, 16777215)
            code_off = code_on ^ random.randint(0xFF, 0xFFF)
            devices.append({"name": name, "room": room,
                            "code_on": code_on, "code_off": code_off, "state": False})
            add_log(f"[学码成功] {name}({room}) 开={code_on} 关={code_off}")
            self.after(0, lambda: self.learn_lbl.config(
                text=f"✅ {name}: 开={code_on}", fg=GREEN))
            self.after(0, self._refresh_devs)
        threading.Thread(target=do, daemon=True).start()

    def _ctrl(self, idx, on):
        devices[idx]["state"] = on
        code = devices[idx]["code_on"] if on else devices[idx]["code_off"]
        add_log(f"[RF发射] {devices[idx]['name']} {'开' if on else '关'} code={code}")
        self._refresh_devs()

    def _refresh_devs(self):
        for w in self.dev_frame.winfo_children(): w.destroy()
        if not devices:
            tk.Label(self.dev_frame, text="（尚未添加设备）", bg=BG2, fg=DIM).pack(pady=8)
            return
        for i, d in enumerate(devices):
            row = tk.Frame(self.dev_frame, bg=BG3 if d["state"] else BG2)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"[{d['room']}] {d['name']}", bg=row["bg"],
                     fg=TEXT, font=("Arial", 10, "bold"), width=20).pack(side="left", padx=8, pady=4)
            tk.Label(row, text="ON" if d["state"] else "OFF", bg=row["bg"],
                     fg=GREEN if d["state"] else DIM,
                     font=("Arial", 10, "bold"), width=4).pack(side="left")
            tk.Button(row, text="开", command=lambda idx=i: self._ctrl(idx, True),
                      bg=GREEN, fg="#111", font=("Arial", 8), relief="flat"
                      ).pack(side="left", padx=2)
            tk.Button(row, text="关", command=lambda idx=i: self._ctrl(idx, False),
                      bg=ACCENT, fg=TEXT, font=("Arial", 8), relief="flat"
                      ).pack(side="left", padx=2)

    def _recv_loop(self):
        protos = ["EV1527", "PT2262", "HX2262"]
        while self._running:
            time.sleep(random.uniform(8, 20))
            code = random.randint(100000, 16777215)
            proto = random.choice(protos)
            add_log(f"[RF接收] code={code} 协议={proto} bits=24")

    def _update_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", "\n".join(log_lines[-40:]))
        self.log.see("end")
        self.log.config(state="disabled")
        self.after(500, self._update_log)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8083), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    add_log("HTTP 服务器已启动: http://localhost:8083")
    add_log("RF 433MHz 网关模拟器就绪")
    app = App()
    app.mainloop()
