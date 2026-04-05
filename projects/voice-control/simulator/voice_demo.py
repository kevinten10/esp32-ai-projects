"""
ESP32 声音/拍手控制 - 独立模拟器
=================================
用空格键模拟拍手，观察声音波形和设备响应。

运行: python voice_demo.py
"""

import tkinter as tk
from tkinter import scrolledtext
import random
import time
from datetime import datetime

BG = "#1a1a2e"; BG2 = "#16213e"; BG3 = "#0f3460"
ACCENT = "#e94560"; GREEN = "#4ecca3"; ORANGE = "#f5a623"
TEXT = "#eee"; DIM = "#888"

class VoiceDemo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ESP32 声音/拍手控制 - 模拟器")
        self.geometry("680x580")
        self.configure(bg=BG)

        self._wave = [0] * 100
        self._clap_n = 0
        self._last_clap = 0
        self._clap_job = None
        self.light = False
        self.fan = False
        self.level = 0

        # UI
        tk.Label(self, text="🎙️ 声音/拍手控制", bg=BG, fg=ACCENT,
                 font=("Arial", 16, "bold")).pack(pady=(12, 2))
        tk.Label(self, text="按 空格键 模拟拍手  |  1次=灯光  2次=风扇  3次=全关",
                 bg=BG, fg=GREEN, font=("Arial", 10)).pack(pady=4)

        # 波形
        cf = tk.Frame(self, bg=BG2)
        cf.pack(fill="x", padx=16, pady=8)
        tk.Label(cf, text="📊 音量波形", bg=BG2, fg=GREEN,
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 0))
        self.canvas = tk.Canvas(cf, bg=BG3, height=100, highlightthickness=0)
        self.canvas.pack(fill="x", padx=10, pady=(2, 4))
        info = tk.Frame(cf, bg=BG2)
        info.pack(fill="x", padx=10, pady=(0, 8))
        self.lvl_lbl = tk.Label(info, text="Level: 0", bg=BG2, fg=TEXT,
                                 font=("Consolas", 9))
        self.lvl_lbl.pack(side="left")
        tk.Label(info, text="  阈值: 600", bg=BG2, fg=ORANGE,
                 font=("Consolas", 9)).pack(side="left")
        self.clap_lbl = tk.Label(info, text="  等待拍手...", bg=BG2, fg=ACCENT,
                                  font=("Arial", 10, "bold"))
        self.clap_lbl.pack(side="left")

        # 设备
        df = tk.Frame(self, bg=BG)
        df.pack(pady=8)
        self.light_lbl = tk.Label(df, text="💡 灯光\nOFF", bg=BG2, fg=DIM,
                                   font=("Arial", 14, "bold"), width=14,
                                   relief="groove", padx=10, pady=10)
        self.light_lbl.pack(side="left", padx=16)
        self.fan_lbl = tk.Label(df, text="🌀 风扇\nOFF", bg=BG2, fg=DIM,
                                 font=("Arial", 14, "bold"), width=14,
                                 relief="groove", padx=10, pady=10)
        self.fan_lbl.pack(side="left", padx=16)

        # 蜂鸣器模拟
        self.beep_lbl = tk.Label(self, text="", bg=BG, fg=ORANGE,
                                  font=("Arial", 10))
        self.beep_lbl.pack(pady=2)

        # 日志
        lf = tk.Frame(self, bg=BG2)
        lf.pack(fill="both", expand=True, padx=16, pady=(4, 12))
        tk.Label(lf, text="📋 串口日志", bg=BG2, fg=DIM,
                 font=("Arial", 9)).pack(anchor="w", padx=10, pady=(8, 0))
        self.log = scrolledtext.ScrolledText(lf, height=8, bg="#0a0a0a",
            fg=GREEN, font=("Consolas", 9), state="disabled", relief="flat")
        self.log.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        self.bind_all("<space>", self._on_space)
        self._tick()

    def _vlog(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log.config(state="normal")
        self.log.insert("end", f"[{ts}] {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _on_space(self, event=None):
        now = time.time()
        if now - self._last_clap < 0.15:
            return
        self._last_clap = now
        self._clap_n += 1
        self.level = random.randint(1200, 2800)
        self._wave.append(self.level)
        self._vlog(f"[检测] 第 {self._clap_n} 次拍手，电平: {self.level}")
        # 蜂鸣器提示
        self.beep_lbl.config(text="🔊 嘀！")

        if self._clap_job:
            self.after_cancel(self._clap_job)
        self._clap_job = self.after(500, self._exec_clap)

    def _exec_clap(self):
        n = self._clap_n
        self._clap_n = 0
        self._clap_job = None
        if n == 1:
            self.light = not self.light
            self._vlog(f"[命令] 单拍 → 灯光 {'ON' if self.light else 'OFF'}")
            self.beep_lbl.config(text="🔊 嘀！(1)")
        elif n == 2:
            self.fan = not self.fan
            self._vlog(f"[命令] 双拍 → 风扇 {'ON' if self.fan else 'OFF'}")
            self.beep_lbl.config(text="🔊 嘀！嘀！(2)")
        elif n >= 3:
            self.light = self.fan = False
            self._vlog(f"[命令] 三拍 → 全部关闭")
            self.beep_lbl.config(text="🔊 嘀！嘀！嘀！(3)")
        self.after(600, lambda: self.beep_lbl.config(text=""))

    def _tick(self):
        # 环境噪声
        noise = random.randint(20, 100)
        if self.level > 0:
            self.level = max(0, self.level - random.randint(100, 300))
        lvl = noise if self.level == 0 else self.level
        self._wave.append(lvl)
        if len(self._wave) > 100:
            self._wave.pop(0)

        # 绘制波形
        c = self.canvas
        w = c.winfo_width() or 500
        c.delete("all")
        # 阈值线
        ty = int((1 - 600 / 4096) * 100)
        c.create_line(0, ty, w, ty, fill=ORANGE, dash=(4, 4))
        # 波形线
        pts = []
        for i, v in enumerate(self._wave):
            x = int(i / len(self._wave) * w)
            y = int((1 - min(v, 4096) / 4096) * 100)
            pts.extend([x, y])
        if len(pts) >= 4:
            c.create_line(pts, fill=GREEN, width=2)

        self.lvl_lbl.config(text=f"Level: {lvl}")
        cnt = f"  拍手: {self._clap_n}次..." if self._clap_n > 0 else "  等待拍手..."
        self.clap_lbl.config(text=cnt)

        # 设备
        for lbl, on, nm in [(self.light_lbl, self.light, "灯光"),
                              (self.fan_lbl, self.fan, "风扇")]:
            lbl.config(text=f"{'💡' if nm=='灯光' else '🌀'} {nm}\n{'ON' if on else 'OFF'}",
                       fg=GREEN if on else DIM, bg=BG3 if on else BG2)

        self.after(60, self._tick)

if __name__ == "__main__":
    app = VoiceDemo()
    app.mainloop()
