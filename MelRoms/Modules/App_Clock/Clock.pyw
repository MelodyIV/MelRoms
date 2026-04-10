#!/usr/bin/env python3
import sys, time, threading, math, random, os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

def play_alarm():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    alarm_path = os.path.join(script_dir, "alarm.mp3")
    if HAS_PYGAME and os.path.exists(alarm_path):
        try:
            pygame.mixer.music.load(alarm_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing mp3: {e}")
    else:
        root.bell()

THEME = {
    "bg": "#0a0e17", "panel": "#111520", "btn": "#1e2937",
    "cyan": "#00e5ff", "pink": "#f472b6", "text": "#bae6fd", "dark_text": "#0f172a"
}

class NeonButton(tk.Button):
    def __init__(self, master, **kw):
        super().__init__(master, bg=THEME["btn"], fg=THEME["cyan"], 
                         relief="flat", activebackground=THEME["cyan"], 
                         font=("Arial", 8, "bold"), **kw)

class CircularClockPopup:
    def __init__(self, parent, callback):
        self.callback = callback
        self.hr, self.min, self.ampm = 12, 0, "AM"
        self.win = tk.Toplevel(parent, bg=THEME["bg"])
        self.win.title("Set Alarm Time")
        self.win.geometry("320x460")
        self.win.resizable(False, False)
        self.win.grab_set() 

        self.time_lbl = tk.Label(self.win, text="12:00 AM", font=("Courier", 20, "bold"), 
                                 bg=THEME["bg"], fg=THEME["pink"], pady=8)
        self.time_lbl.pack()

        self.canvas = tk.Canvas(self.win, width=260, height=260, bg=THEME["bg"], highlightthickness=0)
        self.canvas.pack(pady=5)

        self.draw_clock()
        self.canvas.bind("<B1-Motion>", self.handle_click)
        self.canvas.bind("<Button-1>", self.handle_click)

        ctrl_f = tk.Frame(self.win, bg=THEME["bg"])
        ctrl_f.pack(fill="x", padx=15, pady=8)

        ampm_f = tk.Frame(ctrl_f, bg=THEME["bg"])
        ampm_f.pack(side="top", pady=3)
        NeonButton(ampm_f, text="AM", command=lambda: self.set_ap("AM"), width=5).pack(side="left", padx=4)
        NeonButton(ampm_f, text="PM", command=lambda: self.set_ap("PM"), width=5).pack(side="left", padx=4)

        self.conf_btn = tk.Button(self.win, text="CONFIRM ALARM", bg=THEME["cyan"], fg=THEME["bg"],
                                 font=("Arial", 10, "bold"), relief="flat", height=1,
                                 command=self.confirm)
        self.conf_btn.pack(side="bottom", fill="x", padx=15, pady=10)

    def draw_clock(self):
        self.canvas.delete("all")
        cx, cy = 130, 130
        self.canvas.create_oval(cx-95, cy-95, cx+95, cy+95, outline=THEME["cyan"], width=2)
        self.canvas.create_oval(cx-50, cy-50, cx+50, cy+50, outline=THEME["pink"], width=2)
        for i in range(60):
            ang = math.radians(i * 6 - 90)
            r = 95 if i % 5 == 0 else 90
            self.canvas.create_line(cx+95*math.cos(ang), cy+95*math.sin(ang),
                                    cx+r*math.cos(ang), cy+r*math.sin(ang), fill=THEME["cyan"])
        self.update_ui()

    def handle_click(self, e):
        cx, cy = 130, 130
        dist = math.hypot(e.x-cx, e.y-cy)
        ang = math.degrees(math.atan2(e.y-cy, e.x-cx)) + 90
        if 35 < dist < 75:
            self.hr = int(round(ang/30)) % 12
            if self.hr == 0: self.hr = 12
        elif 75 <= dist < 120:
            self.min = int(round(ang/6)) % 60
        self.update_ui()

    def set_ap(self, val): 
        self.ampm = val
        self.update_ui()
    
    def update_ui(self):
        self.time_lbl.config(text=f"{self.hr:02d}:{self.min:02d} {self.ampm}")
        self.canvas.delete("ptr")
        cx, cy = 130, 130
        ha = math.radians((self.hr % 12) * 30 - 90)
        self.canvas.create_line(cx, cy, cx+45*math.cos(ha), cy+45*math.sin(ha), 
                                fill=THEME["pink"], width=4, tags="ptr")
        ma = math.radians(self.min * 6 - 90)
        self.canvas.create_line(cx, cy, cx+80*math.cos(ma), cy+80*math.sin(ma), 
                                fill=THEME["cyan"], width=2, tags="ptr")

    def confirm(self):
        h24 = (self.hr % 12) + (12 if self.ampm == "PM" else 0)
        self.callback(h24, self.min)
        self.win.destroy()

class MelRomsClock:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Clock")
        self.root.geometry("600x360")
        self.root.configure(bg=THEME["bg"])
        self.root.resizable(True, True)
        
        self.sw_running, self.sw_val = False, 0.0
        self.cd_running, self.cd_val = False, 0
        self.alarm_time = None
        self.lap_counter = 0
        self.lap_key = None

        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        left = tk.Frame(self.root, bg=THEME["bg"])
        left.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        cd_f = tk.LabelFrame(left, text=" COUNTDOWN ", bg=THEME["panel"], fg=THEME["cyan"], font=("Arial", 7, "bold"))
        cd_f.pack(fill="x", pady=4)
        entry_f = tk.Frame(cd_f, bg=THEME["panel"])
        entry_f.pack(pady=3)
        self.m_var, self.s_var = tk.StringVar(value="0"), tk.StringVar(value="0")
        tk.Spinbox(entry_f, from_=0, to=59, width=3, textvariable=self.m_var, bg=THEME["bg"], fg="white", bd=0, font=("Arial", 9)).pack(side="left")
        tk.Label(entry_f, text="m", bg=THEME["panel"], fg=THEME["cyan"], font=("Arial", 8)).pack(side="left", padx=1)
        tk.Spinbox(entry_f, from_=0, to=59, width=3, textvariable=self.s_var, bg=THEME["bg"], fg="white", bd=0, font=("Arial", 9)).pack(side="left")
        tk.Label(entry_f, text="s", bg=THEME["panel"], fg=THEME["cyan"], font=("Arial", 8)).pack(side="left", padx=1)
        self.cd_disp = tk.Label(cd_f, text="00:00", font=("Courier", 18, "bold"), bg=THEME["panel"], fg=THEME["pink"])
        self.cd_disp.pack()
        btn_cd = tk.Frame(cd_f, bg=THEME["panel"])
        btn_cd.pack(pady=3)
        NeonButton(btn_cd, text="START", command=self.toggle_cd).pack(side="left", padx=2)
        NeonButton(btn_cd, text="STOP", command=lambda: setattr(self, 'cd_running', False)).pack(side="left", padx=2)
        sw_f = tk.LabelFrame(left, text=" STOPWATCH ", bg=THEME["panel"], fg=THEME["cyan"], font=("Arial", 7, "bold"))
        sw_f.pack(fill="x", pady=4)
        self.sw_disp = tk.Label(sw_f, text="00:00:00.0", font=("Courier", 16), bg=THEME["panel"], fg=THEME["cyan"])
        self.sw_disp.pack()
        btn_sw = tk.Frame(sw_f, bg=THEME["panel"])
        btn_sw.pack(pady=3)
        NeonButton(btn_sw, text="S/P", command=self.toggle_sw).pack(side="left", padx=2)
        NeonButton(btn_sw, text="LAP", command=self.lap_sw).pack(side="left", padx=2)
        NeonButton(btn_sw, text="CLR", command=self.reset_sw).pack(side="left", padx=2)
        lap_frame = tk.LabelFrame(sw_f, text=" LAP COUNTER ", bg=THEME["panel"], fg=THEME["pink"], font=("Arial", 7, "bold"))
        lap_frame.pack(fill="x", pady=4, padx=5)
        self.lap_count_label = tk.Label(lap_frame, text="Laps: 0", font=("Courier", 9, "bold"),
                                        bg=THEME["panel"], fg=THEME["cyan"])
        self.lap_count_label.pack(side="top", pady=2)
        self.laps = tk.Listbox(lap_frame, height=4, bg=THEME["bg"], fg=THEME["text"], bd=0, font=("Consolas", 8))
        self.laps.pack(fill="both", expand=True, padx=5, pady=2)
        bind_frame = tk.Frame(sw_f, bg=THEME["panel"])
        bind_frame.pack(pady=2)
        self.bind_btn = NeonButton(bind_frame, text="Set Lap Keybind", command=self.set_lap_keybind)
        self.bind_btn.pack(side="left", padx=2)
        self.keybind_label = tk.Label(bind_frame, text="(none)", bg=THEME["panel"], fg=THEME["text"], font=("Arial", 7))
        self.keybind_label.pack(side="left", padx=5)
        right = tk.Frame(self.root, bg=THEME["panel"], width=200)
        right.pack(side="right", fill="y", padx=5, pady=8)
        right.pack_propagate(False)

        tk.Label(right, text="ALARM STATUS", bg=THEME["panel"], fg=THEME["pink"], font=("Arial", 7, "bold")).pack(pady=3)
        self.al_lbl = tk.Label(right, text="NOT SET", bg=THEME["panel"], fg=THEME["text"], font=("Courier", 12, "bold"))
        self.al_lbl.pack()
        NeonButton(right, text="SET", command=lambda: CircularClockPopup(self.root, self.set_al)).pack(pady=5)

        calc_f = tk.Frame(right, bg=THEME["panel"])
        calc_f.pack(pady=8)
        self.calc_e = tk.Entry(calc_f, width=12, font=("Consolas", 10), bg=THEME["bg"], fg="white", bd=0, justify="right")
        self.calc_e.grid(row=0, column=0, columnspan=4, pady=3)
        btns = ['7','8','9','/','4','5','6','*','1','2','3','-','C','0','=','+']
        for i, b in enumerate(btns):
            NeonButton(calc_f, text=b, width=2, command=lambda x=b: self.calc_press(x)).grid(row=(i//4)+1, column=i%4, padx=1, pady=1)

        miku_art = r"""
          ／＞   フ
         |  _  _|  
        ／` ミ＿xノ
       /      |
      /   ヽ   ﾉ
     │　　| | |
    ／￣|　| | |
   | (￣ヽ＿ヽ)__)
    ＼二つ
        """
        self.ascii_label = tk.Label(right, text=miku_art, font=("Courier", 7), bg=THEME["panel"], fg=THEME["cyan"], justify="left")
        self.ascii_label.pack(side="bottom", pady=5)

    def set_lap_keybind(self):
        # Capture a key press
        popup = tk.Toplevel(self.root)
        popup.title("Set Lap Key")
        popup.geometry("250x100")
        popup.configure(bg=THEME["bg"])
        popup.resizable(False, False)
        popup.grab_set()
        label = tk.Label(popup, text="Press any key to set as lap button", 
                         bg=THEME["bg"], fg=THEME["cyan"], font=("Arial", 9))
        label.pack(pady=20)
        def on_key(event):
            self.lap_key = event.keysym
            self.keybind_label.config(text=self.lap_key)
            # Bind the key globally to lap_sw
            self.root.unbind_all(f"<{self.lap_key}>")
            self.root.bind(f"<{self.lap_key}>", lambda e: self.lap_sw())
            popup.destroy()
        popup.bind("<Key>", on_key)
        popup.focus_set()

    def update_loop(self):
        now = datetime.now()
        self.root.title(f"MelRoms Clock - {now.strftime('%H:%M:%S')}")
        if self.sw_running:
            self.sw_val += 0.1
            m, s = divmod(self.sw_val, 60); h, m = divmod(m, 60)
            self.sw_disp.config(text=f"{int(h):02d}:{int(m):02d}:{s:04.1f}")
        
        if self.alarm_time and now >= self.alarm_time:
            self.alarm_time = None
            self.al_lbl.config(text="NOT SET", fg=THEME["text"])
            play_alarm() 
            messagebox.showinfo("ALARM", "Ding Ding! Time is up!")
        
        self.root.after(100, self.update_loop)

    def toggle_cd(self):
        if not self.cd_running:
            try:
                self.cd_val = int(self.m_var.get())*60 + int(self.s_var.get())
                if self.cd_val > 0: 
                    self.cd_running = True
                    self.run_cd()
            except: pass
    
    def run_cd(self):
        if self.cd_running and self.cd_val > 0:
            self.cd_val -= 1
            m, s = divmod(self.cd_val, 60)
            self.cd_disp.config(text=f"{m:02d}:{s:02d}")
            self.root.after(1000, self.run_cd)
        elif self.cd_val == 0 and self.cd_running:
            self.cd_running = False
            play_alarm() 
            messagebox.showinfo("Timer", "Countdown Finished!")

    def set_al(self, h, m):
        at = datetime.now().replace(hour=h, minute=m, second=0, microsecond=0)
        if at <= datetime.now(): 
            at += timedelta(days=1)
        self.alarm_time = at
        self.al_lbl.config(text=at.strftime("%I:%M %p"), fg=THEME["cyan"])
        messagebox.showinfo("Success", f"Alarm set for {at.strftime('%I:%M %p')}")

    def toggle_sw(self): 
        self.sw_running = not self.sw_running

    def reset_sw(self): 
        self.sw_val = 0
        self.sw_disp.config(text="00:00:00.0")
        self.laps.delete(0, 'end')
        self.lap_counter = 0
        self.lap_count_label.config(text="Laps: 0")

    def lap_sw(self):
        if self.sw_val > 0 or self.sw_running:  # allow lap even if stopped
            self.lap_counter += 1
            self.lap_count_label.config(text=f"Laps: {self.lap_counter}")
            current = self.sw_disp.cget("text")
            self.laps.insert(0, f"{self.lap_counter:02d}  {current}")

    def calc_press(self, key):
        if key == '=':
            try: 
                res = eval(self.calc_e.get())
                self.calc_e.delete(0, 'end')
                self.calc_e.insert('end', str(res))
            except: 
                self.calc_e.delete(0, 'end')
                self.calc_e.insert(0, "Error")
        elif key == 'C': 
            self.calc_e.delete(0, 'end')
        else: 
            self.calc_e.insert('end', key)

if __name__ == "__main__":
    root = tk.Tk()
    app = MelRomsClock(root)
    root.mainloop()