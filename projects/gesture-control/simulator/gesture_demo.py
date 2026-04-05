"""
ESP32 手势识别控制 - 独立模拟器
=================================
用方向键模拟手势，观察亮度变化和设备控制。

运行: python gesture_demo.py
"""

import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

BG = "#1a1a2e"; BG2 = "#16213e"; BG3 = "#0f3460"
ACCENT = "#e94560"; GREEN = "#4ecca3"; ORANGE = "#f5a623"
TEXT = "#eee"; DIM = "#888"

class GestureDemo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 手势识别控制 - 模拟器")
        self.geometry("660x540")
        self.configure(bg=BG)

        self.brightness = 50
        self.light = False
        self.fan = False
        self.last_gest = "---"

        tk.Label(self, text="✋ 手势识别控制", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(pady=(12, 2))
        tk.Label(self, text="方向键 ↑↓=亮度  ←=灯光  →=风扇",
                 bg=BG, fg=GREEN, font=("Arial", 10)).pack(pady=4)

        # 手势显示
        gf = tk.Frame(self, bg=BG2)
        gf.pack(fill="x", padx=16, pady=8)
        self.gest_lbl = tk.Label(gf, text="---", bg=BG2, fg=GREEN,
                                  font=("Arial", 42, "bold"), width=6)
        self.gest_lbl.pack(pady=8)
        self.action_lbl = tk.Label(gf, text="等待手势...", bg=BG2, fg=DIM,
                                    font=("Arial", 11))
        self.action_lbl.pack(pady=(0, 8))

        # APDS-9960 模拟面板
        pf = tk.Frame(self, bg=BG2)
        pf.pack(fill="x", padx=16, pady=4)
        tk.Label(pf, text="APDS-9960 传感器（模拟）", bg=BG2, fg=DIM,
                 font=("Arial", 9)).pack(pady=(8, 4))

        # 亮度条
        bf = tk.Frame(self, bg=BG2)
        bf.pack(fill="x", padx=16, pady=4)
        tk.Label(bf, text="☀️ PWM 亮度", bg=BG2, fg=ORANGE,
                 font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        self.bri_canvas = tk.Canvas(bf, bg=BG3, height=24, highlightthickness=0)
        self.bri_canvas.pack(fill="x", padx=10, pady=(4, 4))
        self.bri_lbl = tk.Label(bf, text="50%", bg=BG2, fg=ORANGE,
                                 font=("Arial", 12, "bold"))
        self.bri_lbl.pack(pady=(0, 8))

        # 设备
        df = tk.Frame(self, bg=BG2)
        df.pack(fill="x", padx=16, pady=4)
        row = tk.Frame(df, bg=BG2)
        row.pack(pady=10)
        self.light_lbl = tk.Label(row, text="💡 灯光\nOFF", bg=BG2, fg=DIM,
                                   font=("Arial", 13, "bold"), width=14,
                                   relief="groove", padx=10, pady=10)
        self.light_lbl.pack(side="left", padx=12)
        self.fan_lbl = tk.Label(row, text="🌀 风扇\nOFF", bg=BG2, fg=DIM,
                                 font=("Arial", 13, "bold"), width=14,
                                 relief="groove", padx=10, pady=10)
        self.fan_lbl.pack(side="left", padx=12)

        # 接近值
        self.prox_lbl = tk.Label(df, text="接近值: 0 (无物体)", bg=BG2, fg=DIM,
                                  font=("Consolas", 9))
        self.prox_lbl.pack(pady=(0, 8))

        # 日志
        lf = tk.Frame(self, bg=BG2)
        lf.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(lf, text="📋 手势识别日志", bg=BG2, fg=DIM,
                 font=("Arial", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.log = scrolledtext.ScrolledText(lf, height=6, bg="#0a0a0a",
            fg=GREEN, font=("Consolas", 9), state="disabled", relief="flat")
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self.bind_all("<Up>",    lambda e: self._gesture("UP", "↑"))
        self.bind_all("<Down>",  lambda e: self._gesture("DOWN", "↓"))
        self.bind_all("<Left>",  lambda e: self._gesture("LEFT", "←"))
        self.bind_all("<Right>", lambda e: self._gesture("RIGHT", "→"))

        self._tick()

    def _glog(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _gesture(self, direction, icon):
        self.last_gest = direction
        self.gest_lbl.config(text=icon)

        if direction == "UP":
            self.brightness = min(100, self.brightness + 12)
            act = f"亮度 +12% → {self.brightness}%"
            self._glog(f"[{icon}] UP -> 亮度 {self.brightness}%")
        elif direction == "DOWN":
            self.brightness = max(0, self.brightness - 12)
            act = f"亮度 -12% → {self.brightness}%"
            self._glog(f"[{icon}] DOWN -> 亮度 {self.brightness}%")
        elif direction == "LEFT":
            self.light = not self.light
            act = f"灯光 → {'ON' if self.light else 'OFF'}"
            self._glog(f"[{icon}] LEFT -> 灯光 {'ON' if self.light else 'OFF'}")
        elif direction == "RIGHT":
            self.fan = not self.fan
            act = f"风扇 → {'ON' if self.fan else 'OFF'}"
            self._glog(f"[{icon}] RIGHT -> 风扇 {'ON' if self.fan else 'OFF'}")

        self.action_lbl.config(text=act, fg=GREEN)
        self.after(2000, lambda: self.action_lbl.config(fg=DIM))

    def _tick(self):
        # 亮度条
        c = self.bri_canvas
        w = c.winfo_width() or 300
        c.delete("all")
        bw = int(self.brightness / 100 * (w - 4))
        color = ORANGE if self.brightness > 60 else GREEN
        c.create_rectangle(2, 2, bw + 2, 22, fill=color, outline="")
        self.bri_lbl.config(text=f"{self.brightness}%")

        # 设备
        for lbl, on, nm in [(self.light_lbl, self.light, "灯光"),
                              (self.fan_lbl, self.fan, "风扇")]:
            lbl.config(text=f"{'💡' if nm=='灯光' else '🌀'} {nm}\n{'ON' if on else 'OFF'}",
                       fg=GREEN if on else DIM, bg=BG3 if on else BG2)

        # 模拟接近值
        import random
        prox = random.randint(0, 50) if self.last_gest == "---" else random.randint(150, 255)
        self.prox_lbl.config(text=f"接近值: {prox} {'(手靠近!)' if prox > 100 else ''}")

        self.after(300, self._tick)

if __name__ == "__main__":
    app = GestureDemo()
    app.mainloop()
