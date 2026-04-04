import subprocess
import sys
import os
import json
import math
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import calendar

# Audio Support
try:
    import pygame
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False

CONFIG_FILE = "miku_calendar_config.json"
DATA_FILE = "miku_calendar_data.json"
EVENTS_FOLDER = "Events"

DEFAULT_THEME = {
    "name": "Miku Teal",
    "bg_root": "#0a0f1a",
    "bg_panel": "#111827",
    "bg_anim_frame": "#0a0f1a",
    "btn_bg": "#1e2937",
    "btn_fg": "#67e8f9",
    "btn_active_bg": "#22d3ee",
    "btn_active_fg": "#0f172a",
    "accent_teal": "#22d3ee",
    "accent_pink": "#f472b6",
    "font_main": ["Arial", 10, "bold"],
}

MIKU_TEAL = DEFAULT_THEME["accent_teal"]
MIKU_PINK = DEFAULT_THEME["accent_pink"]
MIKU_DARK = DEFAULT_THEME["bg_root"]

class Miku3DAnimator:
    def __init__(self, parent, width=1250, height=320):
        self.w, self.h = width, height
        self.canvas = tk.Canvas(parent, width=width, height=height,
                                highlightthickness=0, bg=MIKU_DARK)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.time = 0.0
        self.focal_length = 500
        self.distance = 600
        
        self.leek_mode = False
        self.has_event_today = False
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.generate_hair_geometry()
        self.generate_leek_geometry()
        self.generate_decorations()
        self.generate_ribbons()
        self.generate_ascii_background()

        self.frame_count = 0
        self.last_frame = time.time()
        self.animate()

    def on_mouse_move(self, event):
        self.mouse_offset_x = (event.x / self.w) * 2 - 1
        self.mouse_offset_y = (event.y / self.h) * 2 - 1

    def generate_hair_geometry(self):
        self.hair_strands = []
        # Twin-tails (optimized: 6 per side, 12 points each)
        for side in [-1, 1]:
            for s in range(6):
                strand = []
                off_x = (side * 70) + (s * 2 * side)
                off_z = random.uniform(-5, 5)
                for i in range(12):
                    t = i / 11
                    y = -80 + (t * 220)
                    x = off_x + (math.sin(t * 4) * 30 * side)
                    z = off_z + (math.cos(t * 3) * 15)
                    strand.append([x, y, z])
                self.hair_strands.append({'points': strand, 'type': 'tail', 'z_sort': 0})

        # Top/crown hair (optimized: 15 strands, 8 points each)
        for s in range(15):
            strand = []
            angle = (s / 14) * math.pi * 2
            dist = random.uniform(40, 65)
            is_back = math.cos(angle) < 0
            for i in range(8):
                t = i / 7
                x = math.sin(angle) * dist
                y = -110 + (math.cos(angle) * 20) + (t * 80)
                z = math.cos(angle) * dist + (t * 20)
                strand.append([x, y, z])
            self.hair_strands.append({'points': strand, 'type': 'top', 'z_sort': -50 if is_back else 50})

    def generate_leek_geometry(self):
        self.leek_stalk = [[0, 100 - (i * 12), 0] for i in range(10)]
        self.leek_branches = []
        for side in [-1, 1]:
            branch = []
            for i in range(5):
                t = i / 4
                x = side * (t * 45)
                y = -70 - (t * 50)
                z = math.sin(t * math.pi) * 12
                branch.append([x, y, z])
            self.leek_branches.append(branch)

    def generate_ribbons(self):
        self.ribbon_pts = []
        for i in range(10):
            t = (i / 9) * 2 * math.pi
            hx = 16 * math.sin(t)**3
            hy = -(13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t))
            self.ribbon_pts.append([hx * 1.2, hy * 1.2, 0])

    def generate_decorations(self):
        self.deco_elements = []
        types = ['★', '♪', '♫', '★']
        for i in range(10):
            if i % 3 == 0:
                color_key = 'accent_teal'
            elif i % 3 == 1:
                color_key = 'accent_pink'
            else:
                color_key = 'gold'
            self.deco_elements.append({
                'angle': random.uniform(0, math.pi * 2),
                'radius': random.uniform(180, 250),
                'y_off': random.uniform(-80, 80),
                'speed': random.uniform(0.8, 1.5),
                'type': types[i % 4],
                'color_key': color_key
            })

    def generate_ascii_background(self):
        art_lines = [
            r"███╗   ███╗███████╗██╗     ██████╗  ██████╗ ███╗   ███╗███████╗",
            r"████╗ ████║██╔════╝██║     ██╔══██╗██╔═══██╗████╗ ████║██╔════╝",
            r"██╔████╔██║█████╗  ██║     ██████╔╝██║   ██║██╔████╔██║███████╗",
            r"██║╚██╔╝██║██╔══╝  ██║     ██╔══██╗██║   ██║██║╚██╔╝██║╚════██║",
            r"██║ ╚═╝ ██║███████╗███████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║███████║",
            r"╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝"
        ]
        font = ("Courier New", 8, "bold")
        char_w, char_h = 7, 12
        total_w = max(len(line) for line in art_lines) * char_w
        total_h = len(art_lines) * char_h
        start_x = (self.w - total_w) // 2
        start_y = (self.h - total_h) // 2
        
        self.bg_art_items = []
        for row, line in enumerate(art_lines):
            for col, ch in enumerate(line):
                if ch != ' ':
                    x = start_x + col * char_w
                    y = start_y + row * char_h
                    item = self.canvas.create_text(x, y, text=ch, font=font,
                                                   fill="#0f172a", tag="bg_art", anchor="nw")
                    self.bg_art_items.append(item)

    def get_deco_color(self, deco):
        global MIKU_TEAL, MIKU_PINK
        if deco['color_key'] == 'accent_teal':
            return MIKU_TEAL
        elif deco['color_key'] == 'accent_pink':
            return MIKU_PINK
        else:
            return "#fbbf24"

    def rotate_3d(self, x, y, z, angle_y, angle_x):
        cos_y, sin_y = math.cos(angle_y), math.sin(angle_y)
        x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y
        cos_x, sin_x = math.cos(angle_x), math.sin(angle_x)
        y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
        return x, y, z

    def project(self, x, y, z):
        factor = self.focal_length / (z + self.distance)
        sx = x * factor + (self.w / 2)
        sy = y * factor + (self.h / 2)
        return sx, sy, factor

    @staticmethod
    def hsv_to_hex(h, s, v):
        h %= 1.0
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]
        return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'

    def toggle_leek_mode(self):
        self.leek_mode = not self.leek_mode

    def animate(self):
        now = time.time()
        dt = now - self.last_frame
        self.last_frame = now
        self.time += dt

        # Delete only dynamic items
        self.canvas.delete("hair")
        self.canvas.delete("ribbon")
        self.canvas.delete("decoration")
        self.canvas.delete("leek")

        # Update background color every 3 frames
        self.frame_count += 1
        if self.frame_count % 3 == 0:
            bg_hue = (self.time * 0.05) % 1.0
            bg_color = self.hsv_to_hex(bg_hue, 0.6, 0.25)
            for item in self.bg_art_items:
                self.canvas.itemconfig(item, fill=bg_color)

        rot_y = self.time * 0.5 + (self.mouse_offset_x * 0.6)
        rot_x = math.sin(self.time * 0.2) * 0.15 + (self.mouse_offset_y * 0.3)

        if self.leek_mode:
            self.draw_leek(rot_y, rot_x)
        else:
            self.draw_miku(rot_y, rot_x)

        # 30 FPS for better performance
        self.canvas.after(33, self.animate)

    def draw_miku(self, rot_y, rot_x):
        # Background decorations
        for deco in self.deco_elements:
            ang = deco['angle'] + self.time * deco['speed']
            dx = math.sin(ang) * deco['radius']
            dz = math.cos(ang) * deco['radius']
            rx, ry, rz = self.rotate_3d(dx, deco['y_off'], dz, rot_y, rot_x)
            if rz < 0:
                sx, sy, scale = self.project(rx, ry, rz)
                color = self.hsv_to_hex(self.time, 0.6, 1.0) if self.has_event_today else self.get_deco_color(deco)
                self.canvas.create_text(sx, sy, text=deco['type'], fill=color,
                                        font=("Arial", int(12 * scale)), tag="decoration")

        # Back hair
        self.draw_hair_strands(rot_y, rot_x, back_only=True)

        # Heart ribbons
        pulse = 1.0 + math.sin(self.time * 4) * 0.1
        for side in [-1, 1]:
            pts = []
            for p in self.ribbon_pts:
                rx, ry, rz = self.rotate_3d(p[0]*pulse + (side*65), p[1]*pulse - 85, p[2] + 10, rot_y, rot_x)
                pts.append(self.project(rx, ry, rz)[:2])
            self.canvas.create_polygon(pts, fill=MIKU_PINK, outline="#1a0a0a", width=2, tag="ribbon")
            self.canvas.create_text(pts[0][0], pts[0][1], text="♥", fill="white", font=("Arial", 5), tag="ribbon")

        # Front hair
        self.draw_hair_strands(rot_y, rot_x, back_only=False)

        # Foreground decorations
        for deco in self.deco_elements:
            ang = deco['angle'] + self.time * deco['speed']
            dx = math.sin(ang) * deco['radius']
            dz = math.cos(ang) * deco['radius']
            rx, ry, rz = self.rotate_3d(dx, deco['y_off'], dz, rot_y, rot_x)
            if rz >= 0:
                sx, sy, scale = self.project(rx, ry, rz)
                color = self.hsv_to_hex(self.time, 0.6, 1.0) if self.has_event_today else self.get_deco_color(deco)
                self.canvas.create_text(sx, sy, text=deco['type'], fill=color,
                                        font=("Arial", int(14 * scale), "bold"), tag="decoration")

    def draw_hair_strands(self, rot_y, rot_x, back_only=True):
        for strand in self.hair_strands:
            if back_only and strand.get('z_sort', 0) > 0:
                continue
            if not back_only and strand.get('z_sort', 0) <= 0:
                continue

            coords = []
            for i, pt in enumerate(strand['points']):
                sway = math.sin(self.time * 2 + i * 0.5) * (10 if strand['type'] == 'tail' else 3)
                rx, ry, rz = self.rotate_3d(pt[0] + sway, pt[1], pt[2], rot_y, rot_x)
                sx, sy, scale = self.project(rx, ry, rz)
                coords.append((sx, sy))

            if len(coords) > 1:
                if self.has_event_today:
                    color = self.hsv_to_hex(self.time * 0.5, 0.7, 1.0)
                else:
                    color = MIKU_TEAL
                width = 3 if strand['type'] == 'tail' else 2
                self.canvas.create_line(coords, fill=color, width=width,
                                        smooth=True, capstyle=tk.ROUND, tag="hair")

    def draw_leek(self, rot_y, rot_x):
        leek_rot_y = self.time * 3.0
        squash = 1.0 + math.sin(self.time * 4) * 0.05

        stalk_coords = []
        for i, pt in enumerate(self.leek_stalk):
            rx, ry, rz = self.rotate_3d(pt[0]*squash, pt[1], pt[2]*squash, leek_rot_y, rot_x)
            sx, sy, scale = self.project(rx, ry, rz)
            stalk_coords.append((sx, sy, scale, i))

        for i in range(len(stalk_coords)-1):
            p1, p2 = stalk_coords[i], stalk_coords[i+1]
            color = f'#{int(255-p1[3]*10):02x}ff{int(255-p1[3]*10):02x}'
            width = int(20 * p1[2])
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color,
                                    width=width, capstyle=tk.ROUND, tag="leek")

        for branch in self.leek_branches:
            coords = []
            for pt in branch:
                rx, ry, rz = self.rotate_3d(pt[0]*squash, pt[1], pt[2]*squash, leek_rot_y, rot_x)
                coords.append(self.project(rx, ry, rz)[:2])
            self.canvas.create_line(coords, fill="#4ade80", width=12,
                                    smooth=True, capstyle=tk.ROUND, tag="leek")

        for deco in self.deco_elements:
            ang = deco['angle'] + self.time * deco['speed']
            rx, ry, rz = self.rotate_3d(math.sin(ang)*200, deco['y_off'], math.cos(ang)*200, rot_y, rot_x)
            sx, sy, scale = self.project(rx, ry, rz)
            color = self.hsv_to_hex(self.time * 2, 0.8, 1.0)
            self.canvas.create_text(sx, sy, text=deco['type'], fill=color,
                                    font=("Arial", int(9 * scale)), tag="leek")

class MikuCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Calendar")
        self.root.geometry("1280x820")
        self.root.configure(bg=MIKU_DARK)
        self.current_date = datetime.now()
        self.events = self.load_events()
        self.root.iconbitmap(os.path.join(os.path.dirname(__file__), "icon.ico"))
        self.is_muted = False
        self.leek_mode = False

        if not os.path.exists(EVENTS_FOLDER):
            os.makedirs(EVENTS_FOLDER)

        self.init_audio()
        self.load_external_themes()
        print("Available themes:", [t['name'] for t in self.available_themes])
        self.create_widgets()
        self.refresh_calendar()

    def init_audio(self):
        if AUDIO_SUPPORT:
            try: pygame.mixer.init()
            except: pass

    def load_events(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def save_events(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.events, f, indent=2, ensure_ascii=False)
        self.save_upcoming_events_text()

    def save_upcoming_events_text(self):
        if not os.path.exists(EVENTS_FOLDER): os.makedirs(EVENTS_FOLDER)
        today = datetime.now().date()
        upcoming = []
        for date_str, ev_list in sorted(self.events.items()):
            try:
                d = datetime.fromisoformat(date_str).date()
                if d >= today and (d - today).days <= 30:
                    for ev in ev_list:
                        upcoming.append(f"{d} | {ev.get('time', '')} | {ev.get('title', '')}")
            except: continue
        with open(os.path.join(EVENTS_FOLDER, "upcoming_events.txt"), "w", encoding="utf-8") as f:
            f.write("🎀 Miku Calendar 🎀\n\n" + "\n".join(upcoming))
            
    def load_external_themes(self):
        theme_path = os.path.join(os.path.dirname(__file__), "Themes", "theme.json")
        self.available_themes = [DEFAULT_THEME] # Always have the default as backup
        if os.path.exists(theme_path):
            try:
                with open(theme_path, "r", encoding="utf-8") as f:
                    external_data = json.load(f)
                    if isinstance(external_data, list):
                        self.available_themes.extend(external_data)
                    else:
                        self.available_themes.append(external_data)
            except Exception as e:
                print(f"Error loading themes: {e}")
        self.current_theme_index = 0

    def switch_theme(self):
        self.current_theme_index = (self.current_theme_index + 1) % len(self.available_themes)
        new_theme = self.available_themes[self.current_theme_index]
        print(f"Switching to theme: {new_theme['name']}")

        global DEFAULT_THEME, MIKU_TEAL, MIKU_PINK, MIKU_DARK
        DEFAULT_THEME.update(new_theme)
        MIKU_TEAL = DEFAULT_THEME["accent_teal"]
        MIKU_PINK = DEFAULT_THEME["accent_pink"]
        MIKU_DARK = DEFAULT_THEME["bg_root"]

        # Apply to UI
        self.root.configure(bg=MIKU_DARK)
        self.anim_frame.configure(bg=MIKU_DARK)
        self.animator.canvas.configure(bg=MIKU_DARK)

        # Re‑generate decorations so they use the new accent colors
        self.animator.generate_decorations()

        # Update button text
        self.theme_btn.config(text=f"🎭 THEME: {new_theme['name'].upper()}")

        # Refresh calendar to apply new button/panel colors
        self.refresh_calendar()

    def create_widgets(self):
        self.anim_frame = tk.Frame(self.root, height=340, bg=MIKU_DARK)
        self.anim_frame.pack(fill=tk.X, padx=12, pady=(12, 8))
        self.anim_frame.pack_propagate(False)
        self.animator = Miku3DAnimator(self.anim_frame)

        main_container = tk.Frame(self.root, bg=DEFAULT_THEME["bg_panel"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        cal_frame = tk.LabelFrame(main_container, text=" MIKU CALENDAR ", fg=DEFAULT_THEME["btn_fg"], font=("Arial", 12, "bold"), bg=DEFAULT_THEME["bg_panel"])
        cal_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        nav_frame = tk.Frame(cal_frame, bg=DEFAULT_THEME["bg_panel"])
        nav_frame.pack(fill=tk.X, pady=10)

        tk.Button(nav_frame, text="◀ Prev", command=self.prev_month, bg=DEFAULT_THEME["btn_bg"], fg=DEFAULT_THEME["btn_fg"]).pack(side=tk.LEFT, padx=10)
        self.month_label = tk.Label(nav_frame, text="", font=("Arial", 18, "bold"), fg=DEFAULT_THEME["btn_fg"], bg=DEFAULT_THEME["bg_panel"])
        self.month_label.pack(side=tk.LEFT, expand=True)
        tk.Button(nav_frame, text="Next ▶", command=self.next_month, bg=DEFAULT_THEME["btn_bg"], fg=DEFAULT_THEME["btn_fg"]).pack(side=tk.RIGHT, padx=10)

        self.cal_canvas = tk.Canvas(cal_frame, bg=DEFAULT_THEME["btn_bg"], highlightthickness=0)
        self.cal_canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        side_frame = tk.Frame(main_container, width=340, bg=DEFAULT_THEME["bg_panel"])
        side_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        side_frame.pack_propagate(False)

        self.quote_label = tk.Label(side_frame, text="", wraplength=300, fg="#bae6fd", bg=DEFAULT_THEME["btn_bg"], font=("Arial", 10, "italic"), height=5)
        self.quote_label.pack(fill=tk.X, padx=10, pady=10)

        self.events_text = tk.Text(side_frame, bg="#0f172a", fg="#bae6fd", font=("Courier New", 10), wrap="word")
        self.events_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ctrl_frame = tk.Frame(self.root, bg=MIKU_DARK)
        ctrl_frame.pack(fill=tk.X, padx=12, pady=10)
        
        # Add the Theme Switcher Button
        self.theme_btn = tk.Button(ctrl_frame, 
                                   text=f"🎭 THEME: {DEFAULT_THEME['name'].upper()}", 
                                   command=self.switch_theme, 
                                   bg=DEFAULT_THEME["btn_bg"], 
                                   fg=DEFAULT_THEME["btn_fg"])
        self.theme_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(ctrl_frame, text="🗓 TODAY", command=self.go_today, bg=DEFAULT_THEME["btn_bg"], fg=DEFAULT_THEME["btn_fg"]).pack(side=tk.LEFT, padx=5)
        self.leek_btn = tk.Button(ctrl_frame, text="🌱 LEEK MODE", command=self.toggle_leek, bg=DEFAULT_THEME["btn_bg"], fg=MIKU_PINK).pack(side=tk.LEFT, padx=5)
        
        self.update_miku_quote()

    def refresh_calendar(self):
        self.month_label.config(text=self.current_date.strftime("%B %Y"))
        for widget in self.cal_canvas.winfo_children(): widget.destroy()
        
        # Fix for the NameError
        now_dt = datetime.now()
        today = now_dt.date()
        today_iso = today.isoformat()
        
        # Update Rainbow Hair Status
        self.animator.has_event_today = (today_iso in self.events and len(self.events[today_iso]) > 0)
        
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)

        for col, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            tk.Label(self.cal_canvas, text=day, bg=DEFAULT_THEME["btn_bg"], 
                     fg=MIKU_PINK, font=("Arial", 10, "bold")).grid(row=0, column=col, sticky="nsew")

        for r, week in enumerate(cal, 1):
            for c, day_num in enumerate(week):
                if day_num == 0: continue
                d_obj = datetime(self.current_date.year, self.current_date.month, day_num).date()
                
                # Now 'today' is defined, so this line won't crash!
                bg = DEFAULT_THEME["btn_active_bg"] if d_obj == today else DEFAULT_THEME["btn_bg"]
                
                f = tk.Frame(self.cal_canvas, bg=bg, relief=tk.RAISED, bd=1)
                f.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                tk.Label(f, text=str(day_num), bg=bg, fg="white").pack()
                f.bind("<Button-1>", lambda e, d=d_obj: self.open_day_editor(d))

        for i in range(7): self.cal_canvas.grid_columnconfigure(i, weight=1)
        self.refresh_upcoming_events()

    def prev_month(self):
        m, y = (12, self.current_date.year-1) if self.current_date.month == 1 else (self.current_date.month-1, self.current_date.year)
        self.current_date = self.current_date.replace(month=m, year=y)
        self.refresh_calendar()

    def next_month(self):
        m, y = (1, self.current_date.year+1) if self.current_date.month == 12 else (self.current_date.month+1, self.current_date.year)
        self.current_date = self.current_date.replace(month=m, year=y)
        self.refresh_calendar()

    def go_today(self):
        self.current_date = datetime.now()
        self.refresh_calendar()

    def open_day_editor(self, date_obj):
        key = date_obj.isoformat()
        pop = tk.Toplevel(self.root)
        pop.title(f"Event: {key}")
        pop.geometry("320x280")
        pop.configure(bg=DEFAULT_THEME["bg_panel"])
        
        tk.Label(pop, text=f"Manage Event for {key}", fg=MIKU_PINK, bg=DEFAULT_THEME["bg_panel"], font=("Arial", 10, "bold")).pack(pady=10)
        
        tk.Label(pop, text="Event Title:", fg="white", bg=DEFAULT_THEME["bg_panel"]).pack()
        ent = tk.Entry(pop, bg="#1e2937", fg="white", insertbackground="white")
        ent.pack(pady=5, padx=20, fill=tk.X)
        
        if key in self.events:
            ent.insert(0, self.events[key][0]['title'])
        
        # Save Function
        def save():
            title = ent.get().strip()
            if title:
                self.events[key] = [{"title": title, "time": "", "desc": ""}]
                self.save_events()
                self.refresh_calendar()
                pop.destroy()
            else:
                messagebox.showwarning("Empty Title", "Please enter a title or use Delete.")

        # Delete Function
        def delete_ev():
            if key in self.events:
                del self.events[key]
                self.save_events()
                self.refresh_calendar()
                pop.destroy()

        btn_frame = tk.Frame(pop, bg=DEFAULT_THEME["bg_panel"])
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text=" SAVE ", command=save, bg="#059669", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Show delete button only if an event actually exists
        if key in self.events:
            tk.Button(btn_frame, text=" DELETE ", command=delete_ev, bg="#dc2626", fg="white").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="CANCEL", command=pop.destroy, bg="#4b5563", fg="white").pack(side=tk.LEFT, padx=5)

    def refresh_upcoming_events(self):
        self.events_text.delete("1.0", tk.END)
        self.events_text.insert("1.0", "Upcoming:\n" + "\n".join([f"{k}: {v[0]['title']}" for k,v in self.events.items()][:10]))

    def update_miku_quote(self):
        self.quote_label.config(text=random.choice(["Sing with me!", "Leeks are great!", "Let's go!"]))
        self.root.after(10000, self.update_miku_quote)

    def toggle_leek(self):
        self.leek_mode = not self.leek_mode
        self.animator.toggle_leek_mode()

if __name__ == "__main__":
    root = tk.Tk()
    app = MikuCalendarApp(root)
    root.mainloop()