#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
import random
import ctypes
from collections import deque
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Error: Run 'pip install psutil' in terminal.")
    sys.exit(1)

import tkinter as tk
from tkinter import scrolledtext

try:
    import pydivert
except ImportError:
    print("Error: Run 'pip install pydivert' in terminal.")
    sys.exit(1)
MIKU_TEAL = "#22d3ee"
MIKU_PINK = "#f472b6"
MIKU_DARK = "#0a0f1a"
BG_PANEL = "#111827"
BTN_BG = "#1e2937"
TEXT_BG = "#0f172a"
TEXT_FG = "#bae6fd"

PRESETS = {
    "Custom": (0, 0, 0),
    "🌸 Minor Jitter": (45, 0.1, 2),
    "🍵 Cafe Wi-Fi": (180, 0.2, 8),
    "📉 Severe Packet Loss": (60, 0.1, 30),
    "🧊 Frozen (2s)": (0, 2.0, 0),
    "🚫 Dead Zone": (0, 5.0, 90),
}


class MelRomsLagSwitch:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Lag Switch")
        self.root.geometry("520x820")
        self.root.configure(bg=MIKU_DARK)
        self.root.resizable(False, False)

        self.running = False
        self.stats = {"intercepted": 0, "dropped": 0, "held": 0}
        self.pid_cache = {}
        self.pid_cache_time = {}

        self.create_widgets()
        self.update_loop()

    def create_widgets(self):
        main = tk.Frame(self.root, bg=MIKU_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(main, text="─── MELROMS MIKU SYSTEM v4.0 ───",
                font=("Courier", 12, "bold"), fg=MIKU_PINK, bg=MIKU_DARK).pack()
        self.stat_frame = tk.Frame(main, bg=MIKU_DARK)
        self.stat_frame.pack(fill=tk.X, pady=10)
        self.stat_labels = {}
        for key in ["intercepted", "held", "dropped"]:
            lbl = tk.Label(self.stat_frame, text=f"{key.upper()}: 0",
                           font=("Courier", 9), fg=MIKU_TEAL, bg=MIKU_DARK, width=15)
            lbl.pack(side=tk.LEFT, expand=True)
            self.stat_labels[key] = lbl
        f_app = tk.LabelFrame(main, text=" [ TARGET ] ",
                              font=("Arial", 8, "bold"), fg=MIKU_PINK, bg=BG_PANEL, padx=10, pady=8)
        f_app.pack(fill=tk.X, pady=5)

        target_frame = tk.Frame(f_app, bg=BG_PANEL)
        target_frame.pack(fill=tk.X)

        self.app_var = tk.StringVar(value="RobloxPlayerBeta.exe")
        tk.Entry(target_frame, textvariable=self.app_var, bg=TEXT_BG, fg="#fff",
                 font=("Consolas", 10), relief=tk.FLAT, insertbackground="white",
                 width=25).pack(side=tk.LEFT, padx=(0, 10))

        self.system_wide = tk.BooleanVar(value=False)
        tk.Checkbutton(target_frame, text="🌐 System‑wide (all processes)",
                       variable=self.system_wide, command=self.toggle_system_wide,
                       bg=BG_PANEL, fg=MIKU_TEAL, selectcolor=BG_PANEL,
                       activebackground=BG_PANEL).pack(side=tk.LEFT)
        self.warning_label = tk.Label(f_app, text="⚠️ System‑wide can affect ALL apps!",
                                      fg="orange", bg=BG_PANEL, font=("Arial", 8))
        self.warning_label.pack(fill=tk.X, pady=(5, 0))
        self.warning_label.pack_forget()
        f_pre = tk.LabelFrame(main, text=" [ LAG PRESETS ] ",
                              font=("Arial", 8, "bold"), fg=MIKU_TEAL, bg=BG_PANEL, padx=10, pady=8)
        f_pre.pack(fill=tk.X, pady=5)
        self.preset_var = tk.StringVar(value="Custom")
        pre_opt = tk.OptionMenu(f_pre, self.preset_var, *PRESETS.keys(), command=self.apply_preset)
        pre_opt.config(bg=BTN_BG, fg=MIKU_TEAL, activebackground=MIKU_TEAL,
                       relief=tk.FLAT, highlightthickness=0)
        pre_opt["menu"].config(bg=BTN_BG, fg=MIKU_TEAL)
        pre_opt.pack(fill=tk.X)
        tk.Label(main, text="DIRECTIONAL FILTER:", bg=MIKU_DARK,
                 fg=MIKU_PINK, font=("Courier", 9)).pack(pady=(10, 0))
        self.dir_var = tk.StringVar(value="Both")
        dir_frame = tk.Frame(main, bg=MIKU_DARK)
        dir_frame.pack(pady=5)
        for d in ["Both", "Outbound", "Inbound"]:
            tk.Radiobutton(dir_frame, text=d, variable=self.dir_var, value=d,
                           bg=MIKU_DARK, fg="#ccc", selectcolor=BTN_BG,
                           activebackground=MIKU_DARK).pack(side=tk.LEFT, padx=10)
        pf = tk.Frame(main, bg=BG_PANEL, pady=10)
        pf.pack(fill=tk.X, pady=10)
        self.delay_v, self.hold_v, self.loss_v = tk.StringVar(value="0"), tk.StringVar(value="0"), tk.StringVar(value="0")

        for label, var in [("DELAY (ms)", self.delay_v), ("HOLD (s)", self.hold_v), ("LOSS (%)", self.loss_v)]:
            row = tk.Frame(pf, bg=BG_PANEL)
            row.pack(fill=tk.X, padx=25, pady=4)
            tk.Label(row, text=label, bg=BG_PANEL, fg=MIKU_TEAL,
                     width=15, anchor="w", font=("Courier", 10)).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=var, bg=TEXT_BG, fg="#fff",
                     width=8, justify="center", relief=tk.FLAT).pack(side=tk.RIGHT)
        self.start_btn = tk.Button(main, text="ACTIVATE SYSTEM", command=self.toggle_system,
                                   bg=BTN_BG, fg=MIKU_TEAL, font=("Courier", 12, "bold"),
                                   relief=tk.RAISED, height=2, bd=2)
        self.start_btn.pack(fill=tk.X, pady=10)
        self.log_area = scrolledtext.ScrolledText(main, bg=TEXT_BG, fg=TEXT_FG, height=12,
                                                  font=("Consolas", 8), state=tk.DISABLED, relief=tk.FLAT)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def toggle_system_wide(self):
        if self.system_wide.get():
            self.app_var.set("")
            self.warning_label.pack(fill=tk.X, pady=(5, 0))
        else:
            self.warning_label.pack_forget()

    def apply_preset(self, val):
        d, h, l = PRESETS[val]
        self.delay_v.set(str(d))
        self.hold_v.set(str(h))
        self.loss_v.set(str(l))

    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def update_loop(self):
        for key, val in self.stats.items():
            self.stat_labels[key].config(text=f"{key.upper()}: {val}")
        self.root.after(500, self.update_loop)

    def is_target_process(self, pid, target_name):
        if self.system_wide.get():
            return True   

        if not target_name or pid is None:
            return False

        now = time.time()
        if pid in self.pid_cache and (now - self.pid_cache_time.get(pid, 0)) < 2.0:
            return self.pid_cache[pid]
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            match = target_name.lower() in name.lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            match = False
        self.pid_cache[pid] = match
        self.pid_cache_time[pid] = now
        return match
    def packet_handler(self, target_name):
        filter_str = "tcp or udp"
        try:
            with pydivert.WinDivert(filter_str) as w:
                self.log("Driver engine ready")
                if self.system_wide.get():
                    self.log("⚠️ SYSTEM‑WIDE MODE ACTIVE")
                else:
                    self.log(f"Targeting: {target_name}")
                hold_queue = deque()
                while self.running:
                    while hold_queue and hold_queue[0][1] <= time.time():
                        p, _ = hold_queue.popleft()
                        try: w.send(p)
                        except: pass

                    try:
                        p = w.recv()
                    except: continue

                    if p is None: continue

                    self.stats["intercepted"] += 1
                    try:
                        packet_pid = p.interface.pid
                    except AttributeError:
                        packet_pid = None

                    is_target = self.is_target_process(packet_pid, target_name)

                    if is_target:
                        mode = self.dir_var.get()
                        is_out = p.is_outbound
                        should_lag = ((mode == "Both") or
                                      (mode == "Outbound" and is_out) or
                                      (mode == "Inbound" and not is_out))
                        if should_lag:
                            loss_pct = float(self.loss_v.get() or 0)
                            if loss_pct > 0 and random.random() * 100 < loss_pct:
                                self.stats["dropped"] += 1
                                continue
                            delay_ms = float(self.delay_v.get() or 0)
                            hold_sec = float(self.hold_v.get() or 0)

                            if hold_sec > 0:
                                release_time = time.time() + hold_sec
                                hold_queue.append((p, release_time))
                                self.stats["held"] += 1
                                continue 
                            elif delay_ms > 0:
                                def s_delayed(pkt, d_ms):
                                    time.sleep(d_ms / 1000.0)
                                    try: w.send(pkt)
                                    except: pass
                                threading.Thread(target=s_delayed, args=(p, delay_ms), daemon=True).start()
                                continue
                    try:
                        w.send(p)
                    except: pass

        except Exception as e:
            self.log(f"FATAL ENGINE ERROR: {e}")
        finally:
            self.running = False
            self.root.after(0, self.update_ui_state)

    def toggle_system(self):
        if not self.running:
            if not self.system_wide.get() and not self.app_var.get().strip():
                self.log("ERROR: Enter a process name or enable System‑wide mode")
                return

            self.running = True
            self.stats = {"intercepted": 0, "dropped": 0, "held": 0}
            self.pid_cache.clear()

            target = self.app_var.get().strip() if not self.system_wide.get() else ""
            threading.Thread(target=self.packet_handler, args=(target,), daemon=True).start()
            self.log("🚀 MIKU SYSTEM INITIALIZED")
        else:
            self.running = False
            self.log("⏹ SYSTEM DEACTIVATED")
        self.update_ui_state()

    def update_ui_state(self):
        if self.running:
            self.start_btn.config(text="SYSTEM ACTIVE", bg=MIKU_PINK, fg=MIKU_DARK)
        else:
            self.start_btn.config(text="ACTIVATE SYSTEM", bg=BTN_BG, fg=MIKU_TEAL)


if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit(0)
    else:
        root = tk.Tk()
        app = MelRomsLagSwitch(root)
        root.mainloop()