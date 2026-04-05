"""
ESP32 IR 红外万能遥控 - 独立模拟器
===================================
模拟空调控制、学码/发射全流程，含 HTTP API。

运行: python ir_demo.py
访问: http://localhost:8082
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

ac_power = False
ac_temp  = 26
ac_mode  = "cool"
learned  = []
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
        elif p == "/api/ac":
            ok({"power": ac_power, "temp": ac_temp, "mode": ac_mode})
        elif p == "/api/ac/set":
            global ac_power, ac_temp, ac_mode
            ac_power = get("power", "true") == "true"
            ac_temp  = int(get("temp", 26))
            ac_mode  = get("mode", "cool")
            add_log(f"[IR发射] 美的空调 {'开' if ac_power else '关'} {ac_temp}°C {ac_mode}")
            ok()
        elif p == "/api/learn":
            name = get("name", "未命名")
            code = random.randint(0x100000, 0xFFFFFF)
            proto = random.choice(["NEC", "SAMSUNG", "SONY", "RC5", "MIDEA"])
            learned.append({"name": name, "code": code, "proto": proto})
            add_log(f"[学码成功] {name}: {proto} 0x{code:06X}")
            ok({"ok": True, "code": f"0x{code:06X}", "proto": proto})
        elif p == "/api/send":
            idx = int(get("idx", -1))
            if 0 <= idx < len(learned):
                c = learned[idx]
                add_log(f"[IR发射] {c['name']} code=0x{c['code']:06X}")
                ok()
            else:
                ok({"ok": False, "msg": "invalid idx"})
        else:
            self.send_error(404)
    def log_message(self, *a): pass

WEB_HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IR 万能遥控 (Simulator)</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#1a1a2e;color:#eee;font-family:sans-serif;padding:20px}
h1{color:#e94560;text-align:center;margin-bottom:16px}
.s{background:#16213e;border-radius:12px;padding:16px;margin-bottom:14px}
h2{color:#4ecca3;font-size:1em;margin-bottom:10px}
.b{padding:10px 18px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;font-size:.85em;margin:3px}
.bg{background:#4ecca3;color:#111}.br{background:#e94560;color:#fff}
.bb{background:#2196F3;color:#fff}.bx{background:#444;color:#eee}
</style></head><body>
<h1>📡 IR 万能遥控 (Simulator)</h1>
<div class="s"><h2>🌡️ 空调控制</h2>
<button class="b bg" onclick="ac(true,26,'cool')">开 26°C 制冷</button>
<button class="b bb" onclick="ac(true,28,'heat')">开 28°C 制热</button>
<button class="b br" onclick="ac(false)">关闭</button>
</div>
<script>
async function ac(p,t,m){
  await fetch('/api/ac/set?power='+p+'&temp='+t+'&mode='+m);
}
</script></body></html>"""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 IR 红外遥控 - 模拟器")
        self.geometry("640x560")
        self.configure(bg=BG)

        tk.Label(self, text="📡 IR 红外万能遥控", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(pady=(12, 2))
        tk.Label(self, text="http://localhost:8082", bg=BG, fg=GREEN,
                 font=("Consolas", 10)).pack()

        # 空调面板
        acf = tk.Frame(self, bg=BG2)
        acf.pack(fill="x", padx=16, pady=8)
        tk.Label(acf, text="🌡️ 空调控制（美的协议）", bg=BG2, fg=GREEN,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        r1 = tk.Frame(acf, bg=BG2); r1.pack(pady=4)
        self.pwr_lbl = tk.Label(r1, text="⏻ OFF", bg=BG2, fg=DIM,
                                 font=("Arial", 18, "bold"), width=8)
        self.pwr_lbl.pack(side="left", padx=10)
        tk.Button(r1, text="开机", command=lambda: self._ac(True),
                  bg=GREEN, fg="#111", font=("Arial", 9, "bold"), relief="flat"
                  ).pack(side="left", padx=4)
        tk.Button(r1, text="关机", command=lambda: self._ac(False),
                  bg=ACCENT, fg=TEXT, font=("Arial", 9, "bold"), relief="flat"
                  ).pack(side="left", padx=4)

        r2 = tk.Frame(acf, bg=BG2); r2.pack(pady=4)
        self.temp_lbl = tk.Label(r2, text=f"{ac_temp}°C", bg=BG2, fg=BLUE,
                                  font=("Arial", 28, "bold"))
        self.temp_lbl.pack(side="left", padx=12)
        tk.Button(r2, text="▲", command=lambda: self._temp(+1),
                  bg=BG3, fg=TEXT, font=("Arial", 10), relief="flat"
                  ).pack(side="left", padx=2)
        tk.Button(r2, text="▼", command=lambda: self._temp(-1),
                  bg=BG3, fg=TEXT, font=("Arial", 10), relief="flat"
                  ).pack(side="left", padx=2)

        r3 = tk.Frame(acf, bg=BG2); r3.pack(pady=(4, 8))
        for mode, label in [("cool","❄️制冷"), ("heat","🔥制热"),
                              ("fan_only","💨送风"), ("dry","💧除湿")]:
            tk.Button(r3, text=label, command=lambda m=mode: self._mode(m),
                      bg=BG3, fg=TEXT, font=("Arial", 9), relief="flat"
                      ).pack(side="left", padx=3)

        # 学码
        lf = tk.Frame(self, bg=BG2)
        lf.pack(fill="x", padx=16, pady=4)
        tk.Label(lf, text="🎓 学码", bg=BG2, fg=GREEN,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 4))
        lr = tk.Frame(lf, bg=BG2); lr.pack(pady=(0, 8))
        self.name_entry = tk.Entry(lr, bg="#111", fg=TEXT, font=("Arial", 10),
                                    width=16, relief="flat", insertbackground=TEXT)
        self.name_entry.insert(0, "电视开机")
        self.name_entry.pack(side="left", padx=6)
        tk.Button(lr, text="模拟学码", command=self._learn,
                  bg=GREEN, fg="#111", font=("Arial", 9, "bold"), relief="flat"
                  ).pack(side="left", padx=4)

        # 已学码
        self.codes_frame = tk.Frame(lf, bg=BG2)
        self.codes_frame.pack(fill="x", padx=10, pady=(0, 8))

        # 日志
        logf = tk.Frame(self, bg=BG2)
        logf.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(logf, text="📋 IR 发射日志", bg=BG2, fg=DIM,
                 font=("Arial", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.log = scrolledtext.ScrolledText(logf, height=6, bg="#0a0a0a",
            fg=GREEN, font=("Consolas", 9), state="disabled", relief="flat")
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self._update_log()

    def _ac(self, on):
        global ac_power
        ac_power = on
        self.pwr_lbl.config(text=f"⏻ {'ON' if on else 'OFF'}",
                            fg=GREEN if on else DIM)
        code = random.randint(0x100000, 0xFFFFFF)
        add_log(f"[IR发射] 美的空调 {'开机' if on else '关机'} code=0x{code:06X}")

    def _temp(self, d):
        global ac_temp
        ac_temp = max(16, min(30, ac_temp + d))
        self.temp_lbl.config(text=f"{ac_temp}°C")
        if ac_power:
            code = random.randint(0x100000, 0xFFFFFF)
            add_log(f"[IR发射] 温度 {ac_temp}°C code=0x{code:06X}")

    def _mode(self, m):
        global ac_mode
        ac_mode = m
        code = random.randint(0x100000, 0xFFFFFF)
        add_log(f"[IR发射] 模式 {m} code=0x{code:06X}")

    def _learn(self):
        name = self.name_entry.get().strip() or "未命名"
        code = random.randint(0x100000, 0xFFFFFF)
        proto = random.choice(["NEC", "SAMSUNG", "SONY", "RC5"])
        learned.append({"name": name, "code": code, "proto": proto})
        add_log(f"[学码成功] {name}: {proto} 0x{code:06X}")
        # 添加按钮
        def send(c=learned[-1]):
            add_log(f"[IR发射] {c['name']} code=0x{c['code']:06X}")
        tk.Button(self.codes_frame, text=f"📤 {name}", command=send,
                  bg=BG3, fg=TEXT, font=("Arial", 9), relief="flat"
                  ).pack(side="left", padx=4)

    def _update_log(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("end", "\n".join(log_lines[-40:]))
        self.log.see("end")
        self.log.config(state="disabled")
        self.after(500, self._update_log)

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8082), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    add_log("HTTP 服务器已启动: http://localhost:8082")
    add_log("IR Blaster 模拟器就绪")
    app = App()
    app.mainloop()
