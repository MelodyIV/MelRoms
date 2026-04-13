#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import os
import random
import time
import threading
import re
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime

class MikuTheme:
    TEAL = "#22d3ee"
    PINK = "#f472b6"
    DARK = "#0a0f1a"
    PANEL = "#111827"
    BTN_BG = "#1e2937"
    BTN_FG = "#67e8f9"
    BTN_HOVER = "#22d3ee"
    TEXT_BG = "#0f172a"
    TEXT_FG = "#bae6fd"
    SUCCESS = "#4ade80"
    FAIL = "#f87171"

ASCII_HEADER = r"""
      ███╗   ███╗██╗██╗  ██╗██╗   ██╗     ██████╗ ██╗███╗   ██╗ ██████╗ ███████╗██████╗ 
      ████╗ ████║██║██║ ██╔╝██║   ██║     ██╔══██╗██║████╗  ██║██╔════╝ ██╔════╝██╔══██╗
      ██╔████╔██║██║█████╔╝ ██║   ██║     ██████╔╝██║██╔██╗ ██║██║  ███╗█████╗  ██████╔╝
      ██║╚██╔╝██║██║██╔═██╗ ██║   ██║     ██╔══██╗██║██║╚██╗██║██║   ██║██╔══╝  ██╔══██╗
      ██║ ╚═╝ ██║██║██║  ██╗╚██████╔╝     ██║  ██║██║██║ ╚████║╚██████╔╝███████╗██║  ██║
      ╚═╝     ╚═╝╚═╝╚═╝  ╚═╝ ╚═════╝      ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
"""

class MikuPinger:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Ringer ♪")
        self.root.geometry("470x470")
        self.root.configure(bg=MikuTheme.DARK)
        self.root.resizable(True, True)
        self.ping_thread = None
        self.stop_ping = False
        self.random_mode = False
        self.create_widgets()
        self.setup_logging_tags()
        self.apply_styles()
        try:
            base_dir = os.path.dirname(__file__)
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon failed to load: {e}")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root, bg=MikuTheme.DARK)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        tk.Label(self.main_frame, text=ASCII_HEADER, font=("Courier New", 7, "bold"),
                 fg=MikuTheme.TEAL, bg=MikuTheme.DARK, justify=tk.LEFT).pack(pady=(0, 5))

        target_frame = tk.LabelFrame(self.main_frame, text=" 🎯 TARGET CONFIG ", fg=MikuTheme.PINK,
                                    bg=MikuTheme.PANEL, font=("Arial", 9, "bold"), padx=8, pady=8)
        target_frame.pack(fill=tk.X, pady=4)

        self.target_var = tk.StringVar(value="google.com")
        self.target_entry = tk.Entry(target_frame, textvariable=self.target_var,
                                     bg=MikuTheme.TEXT_BG, fg=MikuTheme.TEXT_FG, 
                                     insertbackground=MikuTheme.TEXT_FG, font=("Consolas", 10), width=30)
        self.target_entry.pack(side=tk.LEFT, padx=4, fill=tk.X, expand=True)

        self.random_check_var = tk.IntVar()
        tk.Checkbutton(target_frame, text="🌐 Randomize IP", variable=self.random_check_var,
                       bg=MikuTheme.PANEL, fg=MikuTheme.TEAL, selectcolor=MikuTheme.DARK,
                       activebackground=MikuTheme.PANEL, activeforeground=MikuTheme.PINK,
                       font=("Arial", 8), command=self.toggle_random_mode).pack(side=tk.LEFT, padx=8)

        msg_frame = tk.LabelFrame(self.main_frame, text=" 💌 CUSTOM PACKET MESSAGE ", fg=MikuTheme.PINK,
                                  bg=MikuTheme.PANEL, font=("Arial", 9, "bold"), padx=8, pady=8)
        msg_frame.pack(fill=tk.X, pady=4)

        self.msg_var = tk.StringVar(value="♪ Miku is reaching out to you!")
        tk.Entry(msg_frame, textvariable=self.msg_var, bg=MikuTheme.TEXT_BG, fg=MikuTheme.TEXT_FG,
                 insertbackground=MikuTheme.TEXT_FG, font=("Arial", 9)).pack(fill=tk.X)

        ctrl_frame = tk.Frame(self.main_frame, bg=MikuTheme.DARK)
        ctrl_frame.pack(fill=tk.X, pady=8)

        self.start_btn = tk.Button(ctrl_frame, text="🎵 START SESSION", command=self.start_pinging,
                                   bg=MikuTheme.BTN_BG, fg=MikuTheme.BTN_FG, font=("Arial", 9, "bold"),
                                   relief=tk.FLAT, padx=15, pady=6)
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.stop_btn = tk.Button(ctrl_frame, text="⏹ STOP", command=self.stop_pinging,
                                  bg=MikuTheme.BTN_BG, fg=MikuTheme.BTN_FG, font=("Arial", 9, "bold"),
                                  relief=tk.FLAT, padx=15, pady=6, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        self.clear_btn = tk.Button(ctrl_frame, text="🧹 CLEAR LOG", command=lambda: self.output_area.delete(1.0, tk.END),
                                   bg=MikuTheme.BTN_BG, fg=MikuTheme.BTN_FG, font=("Arial", 9, "bold"),
                                   relief=tk.FLAT, padx=15, pady=6)
        self.clear_btn.pack(side=tk.RIGHT, padx=4)

        out_frame = tk.LabelFrame(self.main_frame, text=" 📡 TRANSMISSION LOG ", fg=MikuTheme.TEAL,
                                  bg=MikuTheme.PANEL, font=("Arial", 9, "bold"))
        out_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.output_area = scrolledtext.ScrolledText(out_frame, bg=MikuTheme.TEXT_BG, fg=MikuTheme.TEXT_FG,
                                                     font=("Consolas", 9), wrap=tk.WORD, padx=8, pady=8)
        self.output_area.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar(value="Status: Vocaloid Ready")
        tk.Label(self.main_frame, textvariable=self.status_var, bg=MikuTheme.PANEL, fg=MikuTheme.TEAL,
                 anchor=tk.W, font=("Arial", 8), padx=8).pack(fill=tk.X, side=tk.BOTTOM, pady=(4,0))

    def setup_logging_tags(self):
        self.output_area.tag_configure("success", foreground=MikuTheme.SUCCESS)
        self.output_area.tag_configure("fail", foreground=MikuTheme.FAIL)
        self.output_area.tag_configure("info", foreground=MikuTheme.TEAL)
        self.output_area.tag_configure("timestamp", foreground=MikuTheme.PINK)

    def apply_styles(self):
        def on_enter(e): e.widget.config(bg=MikuTheme.BTN_HOVER, fg=MikuTheme.DARK)
        def on_leave(e): e.widget.config(bg=MikuTheme.BTN_BG, fg=MikuTheme.BTN_FG)
        for btn in [self.start_btn, self.stop_btn, self.clear_btn]:
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)

    def toggle_random_mode(self):
        self.random_mode = bool(self.random_check_var.get())
        if self.random_mode:
            self.target_entry.config(state=tk.DISABLED)
            self.status_var.set("Status: Random Transmission Mode Active")
        else:
            self.target_entry.config(state=tk.NORMAL)
            self.status_var.set("Status: Targeted Transmission Mode Active")

    def get_next_target(self):
        if self.random_mode:
            return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        return self.target_var.get().strip()

    def log(self, text, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.output_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.output_area.insert(tk.END, f"{text}\n", tag)
        self.output_area.see(tk.END)

    def ping_target(self, target):
        try:
            param = "-n" if sys.platform == "win32" else "-c"
            cmd = ["ping", param, "1", target]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                time_match = re.search(r"time[=<](\d+(?:\.\d+)?)\s*ms", result.stdout, re.IGNORECASE)
                ping_time = time_match.group(1) if time_match else "?"
                return True, f"✓ Success: {target} | Latency: {ping_time}ms"
            return False, f"✗ Failed: {target} | No response"
        except Exception as e:
            return False, f"⚠ Error: {str(e)}"

    def ping_loop(self):
        self.log("Starting MelRoms Ringer session... ♪", "info")
        while not self.stop_ping:
            target = self.get_next_target()
            if not target:
                self.log("Error: Target is empty!", "fail")
                break
            success, line = self.ping_target(target)
            msg = self.msg_var.get().strip() or "♪"
            tag = "success" if success else "fail"
            self.log(f"{line} | Msg: {msg}", tag)
            for _ in range(10):
                if self.stop_ping: break
                time.sleep(0.1)
        self.root.after(0, self.ping_finished)

    def start_pinging(self):
        self.stop_ping = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Status: Pinging... (Click STOP to end)")
        self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
        self.ping_thread.start()

    def stop_pinging(self):
        self.stop_ping = True
        self.status_var.set("Status: Wrapping up session...")

    def ping_finished(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Status: Vocaloid Ready")
        self.log("Transmission session closed. 🏁", "info")

    def on_closing(self):
        self.stop_ping = True
        self.root.destroy()



if __name__ == "__main__":
    root = tk.Tk()
    app = MikuPinger(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()