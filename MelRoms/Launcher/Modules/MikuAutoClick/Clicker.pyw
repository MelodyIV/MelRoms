#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
import random
import math
import pyautogui
from datetime import datetime
from collections import deque

# --- CRITICAL SPEED OVERRIDES ---
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

try:
    import tkinter as tk
    from tkinter import scrolledtext, ttk, messagebox
except ImportError:
    print("Error: tkinter not available or not installed.")
    sys.exit(1)

try:
    from pynput.mouse import Button, Controller as MouseController
    from pynput.keyboard import Key, Listener as KeyListener, KeyCode, Controller as KeyboardController
except ImportError:
    print("Error: Run 'pip install pynput' in terminal.")
    sys.exit(1)

# ---------- Theme Colors ----------
MIKU_TEAL = "#22d3ee"
MIKU_PINK = "#f472b6"
MIKU_DARK = "#0a0f1a"
BG_PANEL = "#111827"
BTN_BG = "#1e2937"
TEXT_BG = "#0f172a"
TEXT_FG = "#bae6fd"
PROGRESS_BG = "#1e2937"
PROGRESS_FG = "#22d3ee"

# ---------- Mouse Presets ----------
PRESETS = {
    "Standard 6 CPS": {"mode": "standard", "cps": 6, "variance": 0, "burst_speed_ms": 10, "burst_amount": 5, "burst_interval_s": 2.0, "shake_intensity": 0, "jitter_intensity": 0},
    "Standard 12 CPS": {"mode": "standard", "cps": 12, "variance": 0, "burst_speed_ms": 8, "burst_amount": 8, "burst_interval_s": 1.5, "shake_intensity": 0, "jitter_intensity": 0},
    "Butterfly 15-20 CPS": {"mode": "random_butterfly", "cps": 17.5, "variance": 2.5, "burst_speed_ms": 10, "burst_amount": 5, "burst_interval_s": 2.0, "shake_intensity": 2, "jitter_intensity": 0},
    "Supersonic 100+": {"mode": "standard", "cps": 150, "variance": 0, "burst_speed_ms": 1, "burst_amount": 10, "burst_interval_s": 0.5, "shake_intensity": 0, "jitter_intensity": 0},
    "Drag Burst (fast)": {"mode": "drag_burst", "cps": 10, "variance": 0, "burst_speed_ms": 5, "burst_amount": 20, "burst_interval_s": 0.5, "shake_intensity": 0, "jitter_intensity": 0},
}

# ---------- Enhanced Auto Key Presser ----------
class AdvancedKeyPresser:
    def __init__(self, log_callback):
        self.log = log_callback
        self.kb = KeyboardController()
        self.slots = {
            i: {
                'key': ['f', 'g', 'h', 'j', 'k'][i-1], 'active': False, 'cps': 10.0, 'mode': 'Spam', 'capturing': False,
                'variance': 0.05, 'hold_ms': 20, 'burst_count': 3, 'release_delay': 5,
                'pattern': 'Static', 'multi_tap': 0, 'humanize': 0, 'cooldown': 0, 'freq': 2.0,
                'pattern_amplitude': 0.4, 'pattern_waveform': 'sine',
                'random_walk_step': 0.0, 'press_duration_variance': 0.0, 'repeat_delay': 0.0
            } for i in range(1, 6)
        }
        self.running = True
        self.first_press_flag = {i: False for i in range(1, 6)}
        self._start_threads()

    def _press_loop(self, slot_id):
        while self.running:
            s = self.slots[slot_id]
            if s['active'] and not s['capturing']:
                if self.first_press_flag.get(slot_id, False) and s['repeat_delay'] > 0:
                    time.sleep(s['repeat_delay'])
                    self.first_press_flag[slot_id] = False

                eff_cps = s['cps']
                t = time.time()
                if s['pattern'] != 'Static':
                    waveform = s['pattern_waveform']
                    amp = s['pattern_amplitude'] * s['cps']
                    if waveform == 'sine':
                        mod = math.sin(t * s['freq']) * amp
                    elif waveform == 'square':
                        mod = amp if (math.sin(t * s['freq']) >= 0) else -amp
                    elif waveform == 'triangle':
                        mod = (2.0 / math.pi) * math.asin(math.sin(t * s['freq'])) * amp * 2
                    elif waveform == 'sawtooth':
                        mod = ((t * s['freq']) % 1.0) * 2 * amp - amp
                    else:
                        mod = 0
                    eff_cps += mod

                if s['random_walk_step'] > 0:
                    eff_cps += random.uniform(-s['random_walk_step'], s['random_walk_step'])
                    eff_cps = max(0.5, eff_cps)

                if s['humanize'] > 0:
                    time.sleep(random.uniform(0, s['humanize'] / 1000))

                try:
                    taps = 2 if random.random() < (s['multi_tap']/100) else 1
                    for _ in range(taps):
                        actual_hold = s['hold_ms'] / 1000.0
                        if s['press_duration_variance'] > 0:
                            actual_hold += random.uniform(-s['press_duration_variance'], s['press_duration_variance'])
                            actual_hold = max(0.001, actual_hold)
                        self.kb.press(s['key'])
                        time.sleep(actual_hold)
                        self.kb.release(s['key'])
                        time.sleep(s['release_delay'] / 1000)
                except:
                    pass

                interval = 1.0 / max(eff_cps, 0.1)
                var = random.uniform(-s['variance'], s['variance'])
                time.sleep(max(0.001, interval + var + s['cooldown']))
            else:
                time.sleep(0.01)

    def _start_threads(self):
        for sid in self.slots:
            threading.Thread(target=self._press_loop, args=(sid,), daemon=True).start()

    def toggle_slot(self, slot_id):
        self.slots[slot_id]['active'] = not self.slots[slot_id]['active']
        if self.slots[slot_id]['active']:
            self.first_press_flag[slot_id] = True
        self.log(f"Slot {slot_id} ({self.slots[slot_id]['key'].upper()}) {'ON' if self.slots[slot_id]['active'] else 'OFF'}")

    def emergency_stop(self):
        for sid in self.slots:
            self.slots[sid]['active'] = False
        self.log("Emergency stop: all key slots deactivated")

    def set_key(self, slot_id, new_key):
        self.slots[slot_id]['key'] = new_key
    def set_cps(self, slot_id, cps):
        try:
            self.slots[slot_id]['cps'] = float(cps)
        except:
            pass
    def set_mode(self, slot_id, mode):
        self.slots[slot_id]['mode'] = mode
    def start_capture(self, slot_id):
        for s in self.slots.values():
            s['capturing'] = False
        self.slots[slot_id]['capturing'] = True
    def stop_capture(self, slot_id):
        self.slots[slot_id]['capturing'] = False

# ---------- Tooltip helper ----------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind('<Enter>', self.show_tip)
        widget.bind('<Leave>', self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Arial", 8))
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ---------- Main Application ----------
class MelRomsUltimateAC:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Ultimate AC")
        self.root.geometry("540x1080")
        self.root.configure(bg=MIKU_DARK)
        self.root.resizable(False, False)

        self.running = False
        self.mouse = MouseController()
        self.mode_var = tk.StringVar(value="standard")
        self.cps_var = tk.StringVar(value="10")
        self.mouse_button_var = tk.StringVar(value="left")
        self.hotkey_var = tk.StringVar(value="F6")

        self.m_ext = {
            'variance': 2.0, 'burst_amt': 5, 'burst_int': 2.0, 'hold_ms': 15,
            'pattern': 'Static', 'jitter': 0.0, 'shake': 0.0, 'fatigue': 0, 'dbl_chance': 0, 'freq': 2.0,
            'fatigue_rate': 0.0, 'miss_chance': 0.0, 'triple_chance': 0.0,
            'jitter_intensity': 0.0, 'click_hold_variance': 0.0,
            'distribution_type': 'uniform', 'normal_sigma': 0.01,
            'cps_max': 999.0, 'cps_min': 0.1
        }

        self.click_count = 0
        self.click_start_time = None
        self.last_click_time = None
        self.cps_history = deque(maxlen=20)
        self.current_cps = 0.0
        self.click_goal = 1000
        self.runtime_seconds = 0
        self.runtime_timer_id = None

        self.key_presser = AdvancedKeyPresser(self.log)
        self.create_widgets()
        self.setup_hotkey()
        self.update_cps_display()

    def create_widgets(self):
        main = tk.Frame(self.root, bg=MIKU_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(main, text="─── MelRoms Ultimate AC ───", font=("Courier", 12, "bold"), fg=MIKU_PINK, bg=MIKU_DARK).pack()

        self.stat_frame = tk.Frame(main, bg=MIKU_DARK)
        self.stat_frame.pack(fill=tk.X, pady=5)
        self.click_count_label = tk.Label(self.stat_frame, text="CLICKS: 0", font=("Courier", 10), fg=MIKU_TEAL, bg=MIKU_DARK)
        self.click_count_label.pack(side=tk.LEFT, padx=5)
        self.cps_label = tk.Label(self.stat_frame, text="CPS: 0.0", font=("Courier", 10), fg=MIKU_PINK, bg=MIKU_DARK)
        self.cps_label.pack(side=tk.LEFT, padx=10)
        self.runtime_label = tk.Label(self.stat_frame, text="TIME: 0s", font=("Courier", 10), fg=TEXT_FG, bg=MIKU_DARK)
        self.runtime_label.pack(side=tk.RIGHT, padx=5)

        goal_frame = tk.Frame(main, bg=BG_PANEL, pady=5)
        goal_frame.pack(fill=tk.X, pady=5)
        tk.Label(goal_frame, text="Click Goal:", bg=BG_PANEL, fg=MIKU_TEAL, font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        self.goal_entry = tk.Entry(goal_frame, width=8, bg=TEXT_BG, fg="#fff", relief=tk.FLAT)
        self.goal_entry.insert(0, "1000")
        self.goal_entry.pack(side=tk.LEFT, padx=5)
        ToolTip(self.goal_entry, "Set target clicks. Progress bar fills as you click.")
        self.set_goal_btn = tk.Button(goal_frame, text="Set", command=self.set_click_goal, bg=BTN_BG, fg=MIKU_TEAL, relief=tk.FLAT, font=("Arial", 7))
        self.set_goal_btn.pack(side=tk.LEFT, padx=2)
        self.progress_bar = ttk.Progressbar(goal_frame, length=200, mode='determinate', style="green.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)
        style = ttk.Style()
        style.theme_use('default')
        style.configure("green.Horizontal.TProgressbar", background=PROGRESS_FG, troughcolor=PROGRESS_BG)

        f_pre = tk.LabelFrame(main, text=" [ PRESETS ] ", font=("Arial", 8, "bold"), fg=MIKU_PINK, bg=BG_PANEL, padx=10, pady=5)
        f_pre.pack(fill=tk.X, pady=5)
        self.preset_var = tk.StringVar(value="Custom")
        preset_menu = ttk.Combobox(f_pre, textvariable=self.preset_var, values=["Custom"] + list(PRESETS.keys()), state="readonly", width=30)
        preset_menu.pack(pady=5)
        preset_menu.bind("<<ComboboxSelected>>", self.apply_preset)

        f_mode = tk.LabelFrame(main, text=" [ CLICKING MODE ] ", font=("Arial", 8, "bold"), fg=MIKU_PINK, bg=BG_PANEL, padx=10, pady=5)
        f_mode.pack(fill=tk.X, pady=5)
        f_mode.bind("<Button-3>", lambda e: self.open_ext_mouse_settings())

        mode_frame = tk.Frame(f_mode, bg=BG_PANEL)
        mode_frame.pack()
        modes = [("Standard", "standard"), ("Butterfly", "random_butterfly"), ("Jitter", "jitter"), ("Burst", "drag_burst")]
        for text, val in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, value=val, bg=BG_PANEL, fg=MIKU_TEAL, selectcolor=BG_PANEL, command=self.update_mouse_ui).pack(side=tk.LEFT, padx=5)

        self.params_frame = tk.Frame(main, bg=BG_PANEL, pady=5)
        self.params_frame.pack(fill=tk.X, pady=5)

        f_btnhk = tk.Frame(main, bg=MIKU_DARK)
        f_btnhk.pack(fill=tk.X)

        f_btn = tk.LabelFrame(f_btnhk, text=" [ BUTTON ] ", fg=MIKU_TEAL, bg=BG_PANEL, padx=10, pady=5)
        f_btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,5))
        for b in ["left", "right"]:
            tk.Radiobutton(f_btn, text=b.upper(), variable=self.mouse_button_var, value=b, bg=BG_PANEL, fg=MIKU_TEAL, selectcolor=BG_PANEL).pack(side=tk.LEFT, padx=10)

        f_hk = tk.LabelFrame(f_btnhk, text=" [ HOTKEY ] ", fg=MIKU_PINK, bg=BG_PANEL, padx=10, pady=5)
        f_hk.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.hotkey_entry = tk.Entry(f_hk, textvariable=self.hotkey_var, bg=TEXT_BG, fg="#fff", width=5, justify="center", relief=tk.FLAT)
        self.hotkey_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(f_hk, text="Set", command=self.set_hotkey, bg=BTN_BG, fg=MIKU_TEAL, relief=tk.FLAT, font=("Arial", 7)).pack(side=tk.LEFT)

        btn_row = tk.Frame(main, bg=MIKU_DARK)
        btn_row.pack(fill=tk.X, pady=10)
        self.start_btn = tk.Button(btn_row, text="START CLICKING", command=self.toggle_mouse, bg=BTN_BG, fg=MIKU_TEAL, font=("Courier", 12, "bold"), relief=tk.RAISED, height=2)
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.reset_stats_btn = tk.Button(btn_row, text="RESET STATS", command=self.reset_stats, bg=BTN_BG, fg=MIKU_PINK, font=("Courier", 9), relief=tk.FLAT)
        self.reset_stats_btn.pack(side=tk.RIGHT, padx=(5,0))
        ToolTip(self.reset_stats_btn, "Reset click count, runtime, and goal progress")

        graph_frame = tk.LabelFrame(main, text=" [ LIVE CPS GRAPH ] ", font=("Arial", 8, "bold"), fg=MIKU_TEAL, bg=BG_PANEL)
        graph_frame.pack(fill=tk.X, pady=5)
        self.graph_canvas = tk.Canvas(graph_frame, width=500, height=80, bg=TEXT_BG, highlightthickness=0)
        self.graph_canvas.pack(padx=5, pady=5)

        tk.Label(main, text="── KEY SLOTS (NUMPAD 1‑5) ──", font=("Courier", 10, "bold"), fg=MIKU_PINK, bg=MIKU_DARK).pack(pady=5)
        self.slot_ui = {}
        for sid in range(1, 6):
            slot = self.key_presser.slots[sid]
            row = tk.Frame(main, bg=BG_PANEL, pady=2)
            row.pack(fill=tk.X, pady=1)
            row.bind("<Button-3>", lambda e, s=sid: self.open_ext_key_settings(s))

            cap_btn = tk.Button(row, text=f"[{slot['key'].upper()}]", width=8, command=lambda s=sid: self.start_key_capture(s), bg=BTN_BG, fg=MIKU_TEAL, font=("Courier", 9, "bold"), relief=tk.FLAT)
            cap_btn.pack(side=tk.LEFT, padx=5)
            tk.Label(row, text="CPS:", bg=BG_PANEL, fg=TEXT_FG, font=("Arial", 7)).pack(side=tk.LEFT)
            cps_entry = tk.Entry(row, width=5, bg=TEXT_BG, fg="#fff", relief=tk.FLAT)
            cps_entry.insert(0, str(slot['cps']))
            cps_entry.pack(side=tk.LEFT, padx=2)
            cps_entry.bind("<FocusOut>", lambda e, s=sid, ent=cps_entry: self.update_key_cps(s, ent.get()))

            mode_combo = ttk.Combobox(row, values=["Spam", "Burst", "Hold"], state="readonly", width=6)
            mode_combo.set(slot['mode'])
            mode_combo.pack(side=tk.LEFT, padx=5)
            mode_combo.bind("<<ComboboxSelected>>", lambda e, s=sid, cb=mode_combo: self.update_key_mode(s, cb.get()))

            status = tk.Label(row, text="●", fg="#333", bg=BG_PANEL, font=("Arial", 12))
            status.pack(side=tk.RIGHT, padx=10)
            self.slot_ui[sid] = {"btn": cap_btn, "status": status, "cps_entry": cps_entry}

        log_header = tk.Frame(main, bg=MIKU_DARK)
        log_header.pack(fill=tk.X, pady=(10,0))
        tk.Label(log_header, text="── EVENT LOG ──", font=("Courier", 9, "bold"), fg=MIKU_PINK, bg=MIKU_DARK).pack(side=tk.LEFT)
        clear_log_btn = tk.Button(log_header, text="Clear Log", command=self.clear_log, bg=BTN_BG, fg=MIKU_TEAL, relief=tk.FLAT, font=("Arial", 7))
        clear_log_btn.pack(side=tk.RIGHT)
        ToolTip(clear_log_btn, "Remove all messages from the log area")

        self.log_area = scrolledtext.ScrolledText(main, bg=TEXT_BG, fg=TEXT_FG, height=6, font=("Consolas", 8), relief=tk.FLAT)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=5)
        self.update_mouse_ui()

    def set_click_goal(self):
        try:
            self.click_goal = int(self.goal_entry.get())
            if self.click_goal <= 0:
                raise ValueError
            self.update_progress()
            self.log(f"Click goal set to {self.click_goal}")
        except:
            self.log("Invalid goal, using 1000")
            self.click_goal = 1000
            self.goal_entry.delete(0, tk.END)
            self.goal_entry.insert(0, "1000")

    def update_progress(self):
        if self.click_goal > 0:
            percent = min(100, int((self.click_count / self.click_goal) * 100))
            self.progress_bar['value'] = percent
        else:
            self.progress_bar['value'] = 0

    def reset_stats(self):
        self.click_count = 0
        self.click_start_time = time.time() if self.running else None
        self.runtime_seconds = 0
        self.cps_history.clear()
        self.current_cps = 0.0
        self.update_click_stats()
        self.update_cps_display()
        self.update_progress()
        self.log("Stats reset")

    def clear_log(self):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)

    def update_runtime(self):
        if self.running and self.click_start_time:
            self.runtime_seconds = int(time.time() - self.click_start_time)
            self.runtime_label.config(text=f"TIME: {self.runtime_seconds}s")
        elif not self.running and self.runtime_seconds == 0:
            self.runtime_label.config(text="TIME: 0s")
        if self.running:
            self.runtime_timer_id = self.root.after(1000, self.update_runtime)

    def update_cps_display(self):
        if self.running and len(self.cps_history) > 0:
            self.current_cps = sum(self.cps_history) / len(self.cps_history)
            self.cps_label.config(text=f"CPS: {self.current_cps:.1f}")
            self.draw_cps_graph()
        elif not self.running:
            self.cps_label.config(text="CPS: 0.0")
            self.graph_canvas.delete("all")
        self.root.after(500, self.update_cps_display)

    def draw_cps_graph(self):
        self.graph_canvas.delete("all")
        if not self.cps_history:
            return
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        if w < 50:
            w = 500
        max_cps = max(self.cps_history) if self.cps_history else 1
        max_cps = max(max_cps, 1)
        points = []
        n = len(self.cps_history)
        for i, cps in enumerate(self.cps_history):
            x = i * (w / max(n, 20))
            y = h - (cps / max_cps) * h * 0.8 - 5
            points.append((x, y))
        if len(points) > 1:
            for i in range(len(points)-1):
                self.graph_canvas.create_line(points[i][0], points[i][1],
                                              points[i+1][0], points[i+1][1],
                                              fill=MIKU_TEAL, width=2)
        self.graph_canvas.create_line(0, h-5, w, h-5, fill="#334155", width=1)

    def record_cps_sample(self):
        if self.last_click_time:
            now = time.time()
            delta = now - self.last_click_time
            if delta > 0:
                inst_cps = 1.0 / delta
                self.cps_history.append(inst_cps)
        self.last_click_time = time.time()

    def update_mouse_ui(self):
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        mode = self.mode_var.get()
        row = tk.Frame(self.params_frame, bg=BG_PANEL)
        row.pack(fill=tk.X, padx=25, pady=2)
        if mode in ["standard", "random_butterfly", "jitter"]:
            tk.Label(row, text="CPS (High = Fast):", bg=BG_PANEL, fg=MIKU_TEAL).pack(side=tk.LEFT)
            tk.Entry(row, textvariable=self.cps_var, bg=TEXT_BG, fg="#fff", width=8, justify="center", relief=tk.FLAT).pack(side=tk.RIGHT)
        elif mode == "drag_burst":
            tk.Label(row, text="Clicks/Burst:", bg=BG_PANEL, fg=MIKU_TEAL).pack(side=tk.LEFT)
            ent = tk.Entry(row, bg=TEXT_BG, fg="#fff", width=8, justify="center", relief=tk.FLAT)
            ent.insert(0, str(self.m_ext['burst_amt']))
            ent.pack(side=tk.RIGHT)
            ent.bind("<FocusOut>", lambda e: self.m_ext.update({'burst_amt': int(ent.get())}))

    def open_ext_mouse_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Advanced Mouse Engine")
        top.geometry("320x550")
        top.configure(bg=BG_PANEL)

        canvas = tk.Canvas(top, bg=BG_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_PANEL)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        param_list = [
            ('variance', 'Delay variance (%)', float),
            ('burst_amt', 'Burst amount', int),
            ('burst_int', 'Burst interval (s)', float),
            ('hold_ms', 'Hold duration (ms)', float),
            ('pattern', 'CPS pattern', str, ['Static', 'Sine']),
            ('jitter', 'Jitter intensity (px)', float),
            ('shake', 'Shake intensity (px)', float),
            ('fatigue', 'Fatigue factor', float),
            ('dbl_chance', 'Double-click chance (%)', float),
            ('freq', 'Pattern frequency (Hz)', float),
            ('fatigue_rate', 'Fatigue rate (CPS/min)', float),
            ('miss_chance', 'Miss chance (%)', float),
            ('triple_chance', 'Triple-click chance (%)', float),
            ('jitter_intensity', 'Jitter movement (px)', float),
            ('click_hold_variance', 'Hold variance (s)', float),
            ('distribution_type', 'Delay distribution', str, ['uniform', 'normal']),
            ('normal_sigma', 'Normal sigma (s)', float),
            ('cps_max', 'Maximum CPS', float),
            ('cps_min', 'Minimum CPS', float),
        ]

        for key, label, typ, *extra in param_list:
            f = tk.Frame(scrollable_frame, bg=BG_PANEL)
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=label, bg=BG_PANEL, fg=TEXT_FG, font=("Arial", 8), width=20, anchor='w').pack(side=tk.LEFT)
            if typ == str and extra and isinstance(extra[0], list):
                var = tk.StringVar(value=str(self.m_ext[key]))
                cb = ttk.Combobox(f, textvariable=var, values=extra[0], state="readonly", width=10)
                cb.pack(side=tk.RIGHT)
                cb.bind("<<ComboboxSelected>>", lambda e, k=key, v=var: self.m_ext.update({k: v.get()}))
            else:
                e = tk.Entry(f, width=10, bg=TEXT_BG, fg="#fff")
                e.insert(0, str(self.m_ext[key]))
                e.pack(side=tk.RIGHT)
                e.bind("<FocusOut>", lambda ev, k=key, ent=e, t=typ: self.m_ext.update({k: t(ent.get()) if t != str else ent.get()}))

    def open_ext_key_settings(self, sid):
        top = tk.Toplevel(self.root)
        top.title(f"Slot {sid} God-Mode")
        top.geometry("320x550")
        top.configure(bg=BG_PANEL)

        canvas = tk.Canvas(top, bg=BG_PANEL, highlightthickness=0)
        scrollbar = tk.Scrollbar(top, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG_PANEL)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        s = self.key_presser.slots[sid]
        param_list = [
            ('variance', 'Delay variance (s)', float),
            ('hold_ms', 'Hold duration (ms)', float),
            ('burst_count', 'Burst count', int),
            ('release_delay', 'Release delay (ms)', float),
            ('pattern', 'CPS pattern', str, ['Static', 'Sine']),
            ('multi_tap', 'Multi-tap chance (%)', float),
            ('humanize', 'Humanize delay (ms)', float),
            ('cooldown', 'Cooldown after press (s)', float),
            ('freq', 'Pattern frequency (Hz)', float),
            ('pattern_amplitude', 'Pattern amplitude (factor)', float),
            ('pattern_waveform', 'Waveform', str, ['sine', 'square', 'triangle', 'sawtooth']),
            ('random_walk_step', 'Random walk step (CPS)', float),
            ('press_duration_variance', 'Press duration variance (s)', float),
            ('repeat_delay', 'Initial repeat delay (s)', float),
        ]

        for key, label, typ, *extra in param_list:
            f = tk.Frame(scrollable_frame, bg=BG_PANEL)
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=label, bg=BG_PANEL, fg=MIKU_PINK, font=("Arial", 8), width=22, anchor='w').pack(side=tk.LEFT)
            if typ == str and extra and isinstance(extra[0], list):
                var = tk.StringVar(value=str(s[key]))
                cb = ttk.Combobox(f, textvariable=var, values=extra[0], state="readonly", width=10)
                cb.pack(side=tk.RIGHT)
                cb.bind("<<ComboboxSelected>>", lambda e, k=key, v=var: s.update({k: v.get()}))
            else:
                e = tk.Entry(f, width=10, bg=TEXT_BG, fg="#fff")
                e.insert(0, str(s[key]))
                e.pack(side=tk.RIGHT)
                e.bind("<FocusOut>", lambda ev, k=key, ent=e, t=typ: s.update({k: t(ent.get()) if t != str else ent.get()}))

    def apply_preset(self, event=None):
        name = self.preset_var.get()
        if name in PRESETS:
            p = PRESETS[name]
            self.mode_var.set(p["mode"])
            self.cps_var.set(str(p["cps"]))
            self.m_ext['burst_amt'] = p["burst_amount"]
            self.update_mouse_ui()
            self.log(f"Loaded preset: {name}")

    def toggle_mouse(self):
        self.running = not self.running
        if self.running:
            self.click_start_time = time.time()
            self.last_click_time = None
            self.update_runtime()
            self.start_btn.config(bg=MIKU_PINK)
            self.log("Mouse clicking STARTED")
            # Give a tiny delay before starting the thread to avoid race
            threading.Thread(target=self._mouse_loop, daemon=True).start()
        else:
            self.start_btn.config(bg=BTN_BG)
            if self.runtime_timer_id:
                self.root.after_cancel(self.runtime_timer_id)
            self.log("Mouse clicking STOPPED")
        self.update_mouse_button()

    def update_mouse_button(self):
        self.start_btn.config(text="STOP CLICKING" if self.running else "START CLICKING")

    def _mouse_loop(self):
        """Robust mouse clicking loop with error logging"""
        btn = Button.left if self.mouse_button_var.get() == "left" else Button.right
        self.log(f"Mouse loop started, button={btn}")
        while self.running:
            try:
                mode = self.mode_var.get()
                base_cps = float(self.cps_var.get())
                eff_cps = base_cps
                if self.m_ext['pattern'] == 'Sine':
                    eff_cps += math.sin(time.time() * self.m_ext['freq']) * (base_cps * 0.4)

                if self.m_ext['fatigue_rate'] > 0 and self.click_start_time is not None:
                    elapsed_min = (time.time() - self.click_start_time) / 60.0
                    fatigue_factor = max(0.2, 1.0 - (self.m_ext['fatigue_rate'] * elapsed_min))
                    eff_cps *= fatigue_factor

                eff_cps = max(self.m_ext['cps_min'], min(self.m_ext['cps_max'], eff_cps))

                if random.random() < (self.m_ext['miss_chance'] / 100.0):
                    delay = 1.0 / max(eff_cps, 0.1)
                    time.sleep(delay)
                    continue

                hold_duration = self.m_ext['hold_ms'] / 1000.0
                if self.m_ext['click_hold_variance'] > 0:
                    hold_duration += random.uniform(-self.m_ext['click_hold_variance'], self.m_ext['click_hold_variance'])
                    hold_duration = max(0.001, hold_duration)

                # Perform click
                self.mouse.press(btn)
                time.sleep(hold_duration)
                self.mouse.release(btn)
                self.click_count += 1
                self.record_cps_sample()
                self.root.after(0, self.update_click_stats)
                self.root.after(0, self.update_progress)

                # Double-click
                if random.random() < (self.m_ext['dbl_chance'] / 100.0):
                    self.mouse.press(btn)
                    time.sleep(hold_duration)
                    self.mouse.release(btn)
                    self.click_count += 1
                    self.record_cps_sample()
                    self.root.after(0, self.update_click_stats)
                    self.root.after(0, self.update_progress)

                # Triple-click
                if random.random() < (self.m_ext['triple_chance'] / 100.0):
                    self.mouse.press(btn)
                    time.sleep(hold_duration)
                    self.mouse.release(btn)
                    self.click_count += 1
                    self.record_cps_sample()
                    self.root.after(0, self.update_click_stats)
                    self.root.after(0, self.update_progress)

                # Jitter movement
                if self.m_ext['jitter_intensity'] > 0:
                    dx = random.uniform(-self.m_ext['jitter_intensity'], self.m_ext['jitter_intensity'])
                    dy = random.uniform(-self.m_ext['jitter_intensity'], self.m_ext['jitter_intensity'])
                    self.mouse.move(dx, dy)

                # Shake
                if self.m_ext['shake'] > 0:
                    self.mouse.move(random.uniform(-self.m_ext['shake'], self.m_ext['shake']),
                                    random.uniform(-self.m_ext['shake'], self.m_ext['shake']))

                # Delay calculation
                mean_delay = 1.0 / max(eff_cps, 0.1)
                if self.m_ext['distribution_type'] == 'normal':
                    sigma = self.m_ext['normal_sigma']
                    delay = random.gauss(mean_delay, sigma)
                    delay = max(0.001, delay)
                else:
                    var_ms = self.m_ext['variance'] / 100.0
                    delay = mean_delay + random.uniform(-var_ms, var_ms)
                    delay = max(0.001, delay)

                if mode == "random_butterfly":
                    delay += random.uniform(-0.02, 0.02)
                elif mode == "drag_burst":
                    for _ in range(self.m_ext['burst_amt'] - 1):
                        self.mouse.press(btn)
                        time.sleep(hold_duration)
                        self.mouse.release(btn)
                        self.click_count += 1
                        self.record_cps_sample()
                        self.root.after(0, self.update_click_stats)
                        self.root.after(0, self.update_progress)
                    delay = self.m_ext['burst_int']

                time.sleep(delay)
            except Exception as e:
                self.log(f"ERROR in mouse loop: {type(e).__name__}: {e}")
                # Stop clicking to avoid spam, but keep the thread alive for next toggle
                self.running = False
                self.root.after(0, lambda: self.start_btn.config(bg=BTN_BG))
                self.root.after(0, lambda: self.start_btn.config(text="START CLICKING"))
                break

    def update_click_stats(self):
        self.click_count_label.config(text=f"CLICKS: {self.click_count}")

    def start_key_capture(self, slot_id):
        self.key_presser.start_capture(slot_id)
        self.slot_ui[slot_id]["btn"].config(text="...", fg=MIKU_PINK)

    def update_key_cps(self, slot_id, value):
        self.key_presser.set_cps(slot_id, value)

    def update_key_mode(self, slot_id, mode):
        self.key_presser.set_mode(slot_id, mode)

    def setup_hotkey(self):
        def on_press(key):
            cap_slot = next((sid for sid, s in self.key_presser.slots.items() if s['capturing']), None)
            if cap_slot:
                new_key = key.char if isinstance(key, KeyCode) else key.name
                self.key_presser.set_key(cap_slot, new_key)
                self.key_presser.stop_capture(cap_slot)
                self.root.after(0, lambda: self.slot_ui[cap_slot]["btn"].config(text=f"[{new_key.upper()}]", fg=MIKU_TEAL))
                return
            try:
                k_name = (key.name if hasattr(key, 'name') else key.char).lower()
                if k_name == self.hotkey_var.get().lower():
                    self.root.after(0, self.toggle_mouse)
            except:
                pass
            vk = getattr(key, 'vk', None)
            if vk and 96 <= vk <= 105:
                num = vk - 96
                if 1 <= num <= 5:
                    self.key_presser.toggle_slot(num)
                    color = MIKU_TEAL if self.key_presser.slots[num]['active'] else "#333"
                    self.root.after(0, lambda n=num, c=color: self.slot_ui[n]["status"].config(fg=c))
                elif num == 0:
                    self.key_presser.emergency_stop()

        self.listener = KeyListener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()

    def set_hotkey(self):
        self.log(f"Hotkey set to: {self.hotkey_var.get()}")

    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def on_closing(self):
        self.running = False
        self.key_presser.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MelRomsUltimateAC(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()