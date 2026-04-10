import subprocess
import sys
import os
import json
import math
import random
import glob
import hashlib
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import ctypes
from ctypes import wintypes

# Audio Support
try:
    import pygame
    AUDIO_SUPPORT = True
except ImportError:
    AUDIO_SUPPORT = False

CONFIG_FILE = "launcher_config.json"
THEME_DIR = "Themes"
MODULES_DIR = "Modules"
SCAN_CACHE_FILE = "programs_cache.json"
CACHE_TTL = 3600

DEFAULT_THEME = {
    "name": "Dark MelRoms",
    "bg_root": "#111111",
    "bg_panel": "#111111",
    "bg_anim_frame": "#000000",
    "btn_bg": "#222222",
    "btn_fg": "#FFFFFF",
    "btn_active_bg": "#444444",
    "btn_active_fg": "#00FFCC",
    "mute_bg": "#333333",
    "mute_fg": "#FFFFFF",
    "mute_active_bg": "#FF3333",
    "tree_bg": "#151515",
    "tree_fg": "#CCCCCC",
    "tree_header_bg": "#222222",
    "tree_header_fg": "#00FFCC",
    "tree_selected_bg": "#00FFCC",
    "tree_selected_fg": "#000000",
    "info_frame_fg": "#00FFCC",
    "info_text_bg": "#080808",
    "info_text_fg": "#BBBBBB",
    "slider_bg": "#222222",
    "slider_trough": "#333333",
    "slider_slider": "#00FFCC",
    "font_main": ["Arial", 9, "bold"],
    "font_mono": ["Courier New", 9]
}

ASCII_SHADES = " .:-=+*#%@"

def get_pixel_char(val):
    idx = int(val * (len(ASCII_SHADES) - 1))
    idx = max(0, min(idx, len(ASCII_SHADES) - 1))
    return ASCII_SHADES[idx]

def hsv_to_hex(h, s, v):
    h = h % 1.0
    i = int(h * 6); f = h * 6 - i
    p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i % 6]
    return f'#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}'
    
def extract_icon_from_exe(exe_path, size=16):
    if sys.platform != "win32" or not exe_path.lower().endswith('.exe'):
        return None
    try:
        shell32 = ctypes.windll.shell32
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        hicon = ctypes.c_void_p()
        count = shell32.ExtractIconExW(exe_path, 0, ctypes.byref(hicon), None, 1)
        if count == 0 or not hicon.value:
            return None

        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        h_bmp = gdi32.CreateCompatibleBitmap(hdc_screen, size, size)
        h_old_bmp = gdi32.SelectObject(hdc_mem, h_bmp)

        user32.DrawIconEx(hdc_mem, 0, 0, hicon, size, size, 0, None, 0x0003)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [("biSize", ctypes.c_uint32),
                        ("biWidth", ctypes.c_int32),
                        ("biHeight", ctypes.c_int32),
                        ("biPlanes", ctypes.c_uint16),
                        ("biBitCount", ctypes.c_uint16),
                        ("biCompression", ctypes.c_uint32),
                        ("biSizeImage", ctypes.c_uint32),
                        ("biXPelsPerMeter", ctypes.c_int32),
                        ("biYPelsPerMeter", ctypes.c_int32),
                        ("biClrUsed", ctypes.c_uint32),
                        ("biClrImportant", ctypes.c_uint32)]

        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = size
        bmi.biHeight = -size
        bmi.biPlanes = 1
        bmi.biBitCount = 32
        bmi.biCompression = 0

        buffer = ctypes.create_string_buffer(size * size * 4)
        gdi32.GetDIBits(hdc_mem, h_bmp, 0, size, buffer, ctypes.byref(bmi), 0)

        gdi32.SelectObject(hdc_mem, h_old_bmp)
        gdi32.DeleteObject(h_bmp)
        gdi32.DeleteDC(hdc_mem)
        user32.ReleaseDC(0, hdc_screen)
        user32.DestroyIcon(hicon)

        img = Image.frombuffer("RGBA", (size, size), buffer, "raw", "BGRA", 0, 1)
        return img
    except Exception as e:
        print(f"Icon extraction failed: {e}")
        return None
        
class ThemeManager:
    @staticmethod
    def initialize():
        if not os.path.exists(THEME_DIR): os.makedirs(THEME_DIR)
        if not os.path.exists(MODULES_DIR): os.makedirs(MODULES_DIR)
        default_path = os.path.join(THEME_DIR, "default.json")
        if not os.path.exists(default_path):
            with open(default_path, "w") as f: json.dump(DEFAULT_THEME, f, indent=4)
                
    @staticmethod
    def load_theme(filename):
        path = os.path.join(THEME_DIR, filename)
        theme = DEFAULT_THEME.copy()
        if os.path.exists(path):
            try:
                with open(path, "r") as f: theme.update(json.load(f))
            except Exception as e: print(f"Error loading theme {filename}: {e}")
        return theme

    @staticmethod
    def get_available_themes():
        if not os.path.exists(THEME_DIR): return []
        return [os.path.basename(f) for f in glob.glob(os.path.join(THEME_DIR, "*.json"))]

class UniversalPixel:
    __slots__ = ('canvas', 'x', 'y', 'vx', 'vy', 'seed', 'item', 'last_color', 'target_x', 'target_y', 'orig_x', 'orig_y')
    def __init__(self, canvas, x, y, size=10):
        self.canvas = canvas
        self.x, self.y = x, y
        self.vx, self.vy = 0.0, 0.0
        self.seed = random.uniform(0, 100)
        p_size = max(7, size + random.randint(-1, 1))
        self.item = canvas.create_text(x, y, text=".", fill="white", font=("Courier", p_size, "bold"), tag="p")
        self.last_color = ""
        self.target_x = x
        self.target_y = y
        self.orig_x = x
        self.orig_y = y

    def physics_update(self, dt, target_x, target_y, hue, sat, val, mouse_x, mouse_y, mouse_active, mouse_vx, mouse_vy):
        k_spring = 4.0
        fx = (target_x - self.x) * k_spring
        fy = (target_y - self.y) * k_spring
        
        if mouse_active and mouse_x is not None and mouse_y is not None:
            dx = self.x - mouse_x
            dy = self.y - mouse_y
            dist = math.hypot(dx, dy)
            radius = 100.0
            if dist < radius and dist > 0.01:
                cursor_speed = math.hypot(mouse_vx, mouse_vy)
                base_force = 1.0
                speed_factor = max(1.0, cursor_speed * 3.0)
                force = (base_force * speed_factor) / (dist * dist + 10.0)
                fx += (dx / dist) * force
                fy += (dy / dist) * force
                transfer = min(1.0, cursor_speed * 3.0)
                self.vx += mouse_vx * transfer * dt
                self.vy += mouse_vy * transfer * dt
        
        damping = 3.0
        fx -= self.vx * damping
        fy -= self.vy * damping
        
        self.vx += fx * dt
        self.vy += fy * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        self.canvas.coords(self.item, self.x, self.y)
        
        char = get_pixel_char(val)
        color = hsv_to_hex(hue, sat, val)
        if color != self.last_color:
            self.canvas.itemconfig(self.item, text=char, fill=color)
            self.last_color = color

class AsciiAnimator:
    def __init__(self, parent, width=300, height=600):
        self.w, self.h = width, height
        self.canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.fg_pool = [UniversalPixel(self.canvas, width/2, height/2, random.randint(9, 13)) for _ in range(120)]
        self.brand_pixels = []
        self.setup_stacked_branding()
        self.time, self.mode = 0, 0
        self.current_hue = 0.0
        
        self.mouse_x = None
        self.mouse_y = None
        self.prev_mouse_x = None
        self.prev_mouse_y = None
        self.last_mouse_time = 0
        self.mouse_vx = 0.0
        self.mouse_vy = 0.0
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.next_mode)
        self.update_animation()

    def on_mouse_move(self, event):
        now = time.time()
        dt = max(0.001, now - self.last_mouse_time) if self.last_mouse_time else 0.016
        if self.prev_mouse_x is not None and dt > 0:
            self.mouse_vx = (event.x - self.prev_mouse_x) / dt
            self.mouse_vy = (event.y - self.prev_mouse_y) / dt
            max_speed = 2000.0
            self.mouse_vx = max(-max_speed, min(max_speed, self.mouse_vx))
            self.mouse_vy = max(-max_speed, min(max_speed, self.mouse_vy))
        self.prev_mouse_x = event.x
        self.prev_mouse_y = event.y
        self.mouse_x = event.x
        self.mouse_y = event.y
        self.last_mouse_time = now

    def set_bg_color(self, hex_color):
        self.canvas.config(bg=hex_color)

    def setup_stacked_branding(self):
        letters = {
            "M": ["M   M", "MM MM", "M M M", "M   M", "M   M"],
            "E": ["EEEE", "E   ", "EEE ", "E   ", "EEEE"],
            "L": ["L   ", "L   ", "L   ", "L   ", "LLLL"],
            "R": ["RRRR", "R  R", "RRRR", "R R ", "R  R"],
            "O": [" OOO ", "O  O", "O  O", "O  O", " OOO "],
            "S": [" SSS ", "S    ", " SSS ", "    S", " SSS "]
        }
        word = "MELROMS"
        char_spacing, pixel_spacing = 65, 7
        start_y = (self.h // 2) - (len(word) * char_spacing // 2)
        for i, char in enumerate(word):
            grid = letters.get(char, [])
            char_y_offset = start_y + (i * char_spacing)
            char_x_offset = (self.w // 2) - (len(grid[0]) * pixel_spacing // 2)
            for r, line in enumerate(grid):
                for c, p_char in enumerate(line):
                    if p_char != " ":
                        px = UniversalPixel(self.canvas, char_x_offset + (c * pixel_spacing), char_y_offset + (r * pixel_spacing), 9)
                        self.brand_pixels.append(px)

    def next_mode(self, event=None):
        self.mode = (self.mode + 1) % 7
        self.time = 0

    def layered_star(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2
        outer_r, inner_r = self.w * 0.35, self.w * 0.14
        edges, layers = 10, 3
        layer_id = i % layers
        p_per_layer = count / layers
        depth_scale = 1.0 - (layer_id * 0.25); rot_speed = 0.5 - (layer_id * 0.2)
        edge_idx = int((i % p_per_layer / p_per_layer) * edges)
        pct = ((i % p_per_layer / p_per_layer) * edges) % 1.0 
        a1, a2 = (edge_idx / edges) * 6.28 - 1.57, ((edge_idx + 1) / edges) * 6.28 - 1.57
        r1, r2 = (outer_r if edge_idx % 2 == 0 else inner_r) * depth_scale, (inner_r if edge_idx % 2 == 0 else outer_r) * depth_scale
        gx = math.cos(a1)*r1 + (math.cos(a2)*r2 - math.cos(a1)*r1)*pct
        gy = math.sin(a1)*r1 + (math.sin(a2)*r2 - math.sin(a1)*r1)*pct
        final_rot = t * rot_speed
        return cx + gx*math.cos(final_rot) - gy*math.sin(final_rot), cy + gx*math.sin(final_rot) + gy*math.cos(final_rot), layer_id

    def layered_heart(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2
        layers = 4; layer_id = i % layers
        angle = (i / count) * 6.28
        beat = math.pow(math.sin(t * 4), 8) * 0.2
        s = (7.0 + beat) * (1.0 - layer_id * 0.15)
        tx = 16 * math.sin(angle)**3
        ty = -(13 * math.cos(angle) - 5 * math.cos(2*angle) - 2 * math.cos(3*angle) - math.cos(4*angle))
        return cx + tx * s, cy + ty * s, layer_id

    def inf_loop_neon(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2
        angle = (i / count) * 6.28 + (t * 2.0); scale = self.w * 0.4
        den = math.sin(angle)**2 + 1
        gx = scale * 1.414 * math.cos(angle) / den
        gy = scale * 1.414 * math.cos(angle) * math.sin(angle) / den
        return cx + gx, cy + gy

    def hypernova_collapse(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2
        cycle_t = t % 8.0
        angle_offset = i * 0.1 + t * 2
        MAX_RADIUS = min(self.w, self.h) * 0.7
        if cycle_t < 2.0:
            pct = cycle_t / 2.0
            seed = i * 13.57
            expansion = math.sin(pct * math.pi)
            dist = (i % 10) * 8 + (expansion * MAX_RADIUS * 0.3)
            angle = (i / count) * 6.283 + (t * 0.5)
            tx = cx + math.cos(angle) * dist
            ty = cy + math.sin(angle) * dist
            hue = 0.12 + (math.sin(seed) * 0.02)
            val = 0.3 + pct * 0.7
        elif cycle_t < 5.0:
            pct = (cycle_t - 2.0) / 3.0
            rad = (MAX_RADIUS * pct) + (i % 10) * 8
            rot = angle_offset + pct * 12
            tx = cx + math.cos(rot) * rad
            ty = cy + math.sin(rot) * rad
            val = max(0.1, 1.0 - pct)
            hue = (0.05 + pct * 0.4) % 1.0
        else:
            pct = (cycle_t - 5.0) / 3.0
            max_rad = MAX_RADIUS + (i % 10) * 8
            pull_pct = math.pow(1.0 - pct, 2)
            current_rad = max_rad * pull_pct
            current_rot = angle_offset + 12.0 + (pct * 2.0)
            tx = cx + math.cos(current_rot) * current_rad
            ty = cy + math.sin(current_rot) * current_rad
            val = max(0.1, pct)
            hue = (0.95 + pct * 0.05) % 1.0
        return tx, ty, hue, val

    def sine_ripple(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2
        y_pos = (i / count) * (self.h * 0.8) - (self.h * 0.4)
        wave = math.sin(y_pos * 0.03 + t * 5) * 50
        return cx + wave, cy + y_pos

    def sideways_falling_stars(self, t, i, count):
        num_stars = 5; p_per_star = count // num_stars
        s_id, idx = i // p_per_star, i % p_per_star
        speed = 45.0 + (s_id * 10); virtual_width = self.w + 1200 
        raw_x = ((t * speed) + (s_id * 300)) % virtual_width
        cx, cy = raw_x - 600, (s_id * (self.h / num_stars)) + 60 + math.sin(t * 1.3 + s_id) * 25
        fade_zone = 100
        edge_fade = max(0, cx / fade_zone) if cx < fade_zone else (max(0, (self.w - cx) / fade_zone) if cx > self.w - fade_zone else 1.0)
        head_pixels = int(p_per_star * 0.45)
        if idx < head_pixels:
            outer_r, inner_r, edges = 40, 17, 10
            prog = (idx / head_pixels) * edges; e_idx, pct = int(prog), prog % 1.0
            a1, a2 = (e_idx/edges)*6.283-1.57, ((e_idx+1)/edges)*6.283-1.57
            r1, r2 = (outer_r if e_idx%2==0 else inner_r), (inner_r if e_idx%2==0 else outer_r)
            gx, gy = math.cos(a1)*r1 + (math.cos(a2)*r2-math.cos(a1)*r1)*pct, math.sin(a1)*r1 + (math.sin(a2)*r2-math.sin(a1)*r1)*pct
            rot = t * 2.2
            tx, ty = cx + gx*math.cos(rot)-gy*math.sin(rot), cy + gx*math.sin(rot)+gy*math.cos(rot)
            return tx, ty, 0.13, 0.4, 1.0 * edge_fade, 0.0
        else:
            rel_pos = (idx - head_pixels) / (p_per_star - head_pixels)
            seed = (s_id * 500) + (idx - head_pixels)
            dist_back = 42 + (rel_pos * 180); spread = math.sin(seed * 1.23) * (8 + dist_back * 0.12)
            tx, ty = cx - dist_back, cy + (spread * math.pow(rel_pos, 0.5)) + math.sin(t * 15 + seed) * 4
            return tx, ty, (0.13 - rel_pos * 0.12) % 1.0, 1.0, max(0, 1.0 - rel_pos) * edge_fade, 2.0

    def rainbow_spiral_ribbon(self, t, i, count):
        cx, cy = self.w / 2, self.h / 2; t_slow = t * 0.8
        ease = lambda v: v * v * (3.0 - 2.0 * v)
        layers = 8; p_per_layer = max(1, count // 8)
        layer_idx, pos_idx = i // p_per_layer, (i % p_per_layer) / p_per_layer
        px1, py1 = 30 + pos_idx * (self.w - 60), cy + math.sin(pos_idx * 6.28 + t_slow) * 50 + (layer_idx - 4) * 6
        hue1 = (pos_idx + t_slow * 0.2) % 1.0
        radius, theta = 20 + (i/count)*80, (i/count)*15.0 - t_slow*2.0 + ((i%2)*math.pi)
        px2, py2 = cx + math.cos(theta)*radius + ((i%2)-0.5)*100, 50 + (i/count)*(self.h-100) + math.sin(theta)*radius*0.3
        px3, py3 = 10 + (i/count)*(self.w-20), cy + math.sin((10+(i/count)*(self.w-20))*0.01)*10 + (i%3)*4
        cycle = t_slow % 24.0
        if cycle < 4: return px1, py1, hue1
        elif cycle < 8: b = ease((cycle-4)/4.0); return px1*(1-b)+px2*b, py1*(1-b)+py2*b, hue1*(1-b)+0.0*b
        elif cycle < 12: return px2, py2, 0.0
        elif cycle < 16: b = ease((cycle-12)/4.0); return px2*(1-b)+px3*b, py2*(1-b)+py3*b, 0.0*(1-b)+0.6*b
        elif cycle < 20: return px3, py3, 0.6
        else: b = ease((cycle-20)/4.0); return px3*(1-b)+px1*b, py3*(1-b)+py1*b, 0.6*(1-b)+hue1*b

    def update_animation(self):
        dt = 0.016
        self.time += dt
        if self.time > {0:10, 1:8, 2:12, 3:8, 4:10, 5:15, 6:30}.get(self.mode, 15):
            self.next_mode()
        
        count = len(self.fg_pool)
        current_time = time.time()
        mouse_active = (current_time - self.last_mouse_time) < 0.3 if self.last_mouse_time != 0 else False
        
        for i, p in enumerate(self.fg_pool):
            if self.mode == 0:
                tx, ty, lyr = self.layered_star(self.time, i, count)
                hue, val = 0.13, (0.7 + lyr * 0.1)
                sat = 1.0
            elif self.mode == 1:
                tx, ty, lyr = self.layered_heart(self.time, i, count)
                hue, val = 0.0, 0.5+0.5*(1.0-lyr/4)
                sat = 1.0
            elif self.mode == 2:
                tx, ty = self.inf_loop_neon(self.time, i, count)
                hue, sat, val = (self.time*0.3+i*0.002)%1.0, 0.7, 0.8
            elif self.mode == 3:
                tx, ty, hue, val = self.hypernova_collapse(self.time, i, count)
                sat = 0.9
            elif self.mode == 4:
                tx, ty = self.sine_ripple(self.time, i, count)
                hue, sat, val = 0.5, 0.8, 0.5+0.5*math.cos((i/count)*10-self.time*3)
            elif self.mode == 5:
                tx, ty, hue, sat, val, _ = self.sideways_falling_stars(self.time, i, count)
            elif self.mode == 6:
                tx, ty, hue = self.rainbow_spiral_ribbon(self.time, i, count)
                sat, val = 0.85, 0.9
            
            self.current_hue = hue
            p.physics_update(dt, tx, ty, hue, sat, val, self.mouse_x, self.mouse_y, mouse_active, self.mouse_vx, self.mouse_vy)
        
        for bp in self.brand_pixels:
            min_d = min((bp.x - fp.x)**2 + (bp.y - fp.y)**2 for fp in self.fg_pool[::6]) if self.fg_pool else 0
            boost = max(0, 1.0 - (math.sqrt(min_d) / 70))
            val = (0.3 + 0.7 * boost) * (0.8 + 0.2 * math.sin(self.time * 12))
            bp.physics_update(dt, bp.orig_x, bp.orig_y, self.current_hue, 0.7, val, self.mouse_x, self.mouse_y, mouse_active, self.mouse_vx, self.mouse_vy)
        
        self.canvas.after(16, self.update_animation)

class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Launcher")
        self.root.geometry("1150x750")
        ThemeManager.initialize()
        self.load_launcher_config()
        self.is_muted = False
        self.volume = self.config.get("volume", 0.3)  
        self.init_music()
        self.programs = []
        self.custom_programs = []
        self.module_icons = []
        self.program_icons = {}
        self.load_custom_programs()
        self.create_widgets()
        self.apply_theme(self.current_theme_file)
        self.setup_notes_autosave()   # <--- FIXED: load and autosave scratchpad

    def load_programs_and_modules_threaded(self):
        self.scan_local_py_files()   
        self.scan_modules_for_buttons_data()
        self.root.after(0, self.refresh_list)
        self.root.after(0, self.rebuild_module_grid)

    def get_desc_filepath(self, program):
        desc_dir = "Desc"
        if not os.path.exists(desc_dir):
            os.makedirs(desc_dir)
        path_hash = hashlib.md5(program["path"].encode()).hexdigest()
        return os.path.join(desc_dir, f"{path_hash}.txt")

    def load_description(self, program):
        desc_file = self.get_desc_filepath(program)
        if os.path.exists(desc_file):
            try:
                with open(desc_file, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                return ""
        return ""

    def save_description(self, program, text):
        desc_file = self.get_desc_filepath(program)
        try:
            with open(desc_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Error saving description: {e}")

    def load_launcher_config(self):
        self.config = {"theme": "default.json", "volume": 0.3}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: self.config.update(json.load(f))
            except: pass
        self.current_theme_file = self.config["theme"]
        self.volume = self.config.get("volume", 0.3)

    def save_launcher_config(self):
        with open(CONFIG_FILE, "w") as f: json.dump(self.config, f)

    def init_music(self):
        if not AUDIO_SUPPORT:
            return
        def load():
            pygame.mixer.init()
            base = os.path.dirname(os.path.abspath(__file__))
            for ext in ['.mp3', '.flac', '.wav']:
                path = os.path.join(base, f"song{ext}")
                if os.path.exists(path):
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_volume(self.volume)
                    break
        threading.Thread(target=load, daemon=True).start()

    def set_volume(self, val):
        try:
            vol = float(val) / 100.0
        except:
            vol = 0.5
        self.volume = vol
        if AUDIO_SUPPORT and pygame.mixer.get_init() is not None:
            pygame.mixer.music.set_volume(vol)
        self.config["volume"] = vol
        self.save_launcher_config()

    def toggle_mute(self):
        if not AUDIO_SUPPORT: return
        self.is_muted = not self.is_muted
        t = getattr(self, 'current_theme_data', DEFAULT_THEME)
        if self.is_muted:
            pygame.mixer.music.pause()
            self.mute_btn.config(bg=t.get("mute_active_bg", "red"))
        else:
            pygame.mixer.music.unpause()
            self.mute_btn.config(bg=t.get("mute_bg", "#333"))

    def load_custom_programs(self):
        custom_file = "custom_programs.json"
        if os.path.exists(custom_file):
            try:
                with open(custom_file, "r", encoding="utf-8") as f:
                    self.custom_programs = json.load(f)
            except:
                self.custom_programs = []
        else:
            self.custom_programs = []

    def save_custom_programs(self):
        custom_file = "custom_programs.json"
        try:
            with open(custom_file, "w", encoding="utf-8") as f:
                json.dump(self.custom_programs, f, indent=2)
        except Exception as e:
            print(f"Error saving custom programs: {e}")

    def load_program_icon(self, program):
        path = program["path"]
        if path in self.program_icons:
            return self.program_icons[path]
        
        name = program["name"]
        folder = os.path.dirname(path)
        icon = None
        
        if path.lower().endswith('.exe') and sys.platform == "win32":
            try:
                img = extract_icon_from_exe(path, size=16)
                if img:
                    icon = ImageTk.PhotoImage(img)
            except:
                pass
        
        if not icon:
            for ico in [os.path.join(folder, "icon.ico"), os.path.join(folder, f"{name}.ico")]:
                if os.path.exists(ico):
                    try:
                        img = Image.open(ico).resize((16, 16), Image.Resampling.LANCZOS)
                        icon = ImageTk.PhotoImage(img)
                    except:
                        pass
                    break
        
        if not icon:
            try:
                img = Image.new("RGBA", (16, 16), color="#666666")
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, 15, 15], outline="#FFFFFF")
                draw.text((5, 2), name[0].upper(), fill="#FFFFFF")
                icon = ImageTk.PhotoImage(img)
            except:
                img = Image.new("RGBA", (16, 16), color="#666666")
                icon = ImageTk.PhotoImage(img)
        
        self.program_icons[path] = icon
        return icon

    def add_program(self):
        file_path = filedialog.askopenfilename(
            title="Select Program to Add",
            filetypes=[
                ("Executable files", "*.exe *.bat *.cmd"),
                ("Python scripts", "*.py *.pyw"),
                ("All files", "*.*")
        ]
        )
        if not file_path:
            return
        name = os.path.splitext(os.path.basename(file_path))[0]
        if any(p["path"] == file_path for p in self.programs):
            messagebox.showinfo("Already Exists", f"{name} is already in the list.")
            return
        new_prog = {
            "name": name,
            "path": file_path,
            "info": "Manually added program.\nDouble‑click or select and press LAUNCH."
        }
        self.programs.append(new_prog)
        self.custom_programs.append(new_prog)
        self.save_description(new_prog, "")
        self.save_custom_programs()
        self.refresh_list()
        messagebox.showinfo("Added", f"{name} has been added to the launcher.")

    def remove_program(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a program to remove.")
            return
        item = selected[0]
        prog_name = self.tree.item(item)["text"].strip()
        prog_path = self.tree.item(item)["values"][0]
        
        prog_to_remove = None
        for p in self.programs:
            if p["name"] == prog_name and p["path"] == prog_path:
                prog_to_remove = p
                break
        if prog_to_remove is None:
            return
        if not messagebox.askyesno("Confirm Remove", f"Remove '{prog_name}' from the launcher?"):
            return
        self.programs.remove(prog_to_remove)
        if prog_to_remove in self.custom_programs:
            self.custom_programs.remove(prog_to_remove)
            self.save_custom_programs()
        
        desc_file = self.get_desc_filepath(prog_to_remove)
        if os.path.exists(desc_file):
            try:
                os.remove(desc_file)
            except:
                pass

        self.refresh_list() 
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.config(state=tk.DISABLED)
        messagebox.showinfo("Removed", f"{prog_name} has been removed.")

    def create_widgets(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.btn_launch = tk.Button(self.left_frame, text="🚀 LAUNCH", command=self.launch_program, relief=tk.FLAT)
        self.btn_launch.pack(fill=tk.X, pady=5)

        self.btn_refresh = tk.Button(self.left_frame, text="🔄 REFRESH", command=self.refresh_list, relief=tk.FLAT)
        self.btn_refresh.pack(fill=tk.X, pady=5)

        self.btn_settings = tk.Button(self.left_frame, text="⚙️ THEMES", command=self.open_theme_settings, relief=tk.FLAT)
        self.btn_settings.pack(fill=tk.X, pady=5)

        self.btn_add = tk.Button(self.left_frame, text="➕ ADD", command=self.add_program, relief=tk.FLAT)
        self.btn_add.pack(fill=tk.X, pady=5)

        self.btn_remove = tk.Button(self.left_frame, text="❌ REMOVE", command=self.remove_program, relief=tk.FLAT)
        self.btn_remove.pack(fill=tk.X, pady=5)
        self.volume_slider = tk.Scale(self.left_frame, from_=0, to=100, orient=tk.VERTICAL,
                                      command=self.set_volume, relief=tk.FLAT,
                                      length=80, width=12, sliderlength=15)
        self.volume_slider.set(self.volume * 100)
        self.volume_slider.pack(side=tk.BOTTOM, pady=2)
        self.mute_btn = tk.Button(self.left_frame, text="🔇 MUTE", command=self.toggle_mute, relief=tk.FLAT)
        self.mute_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=2)

        self.middle_frame = tk.Frame(self.main_frame)
        self.middle_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.top_rect = tk.Frame(self.middle_frame)
        self.top_rect.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(self.top_rect, columns=("path",), show="tree headings")
        self.tree.heading("#0", text="Application")
        self.tree.heading("path", text="Full System Path")
        self.tree.column("#0", width=250)
        self.tree.column("path", width=500)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.show_info)

        self.bottom_container = tk.Frame(self.middle_frame)
        self.bottom_container.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.info_frame = tk.LabelFrame(self.bottom_container, text=" DESCRIPTION ")
        self.info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.info_text = tk.Text(self.info_frame, height=12, width=20, relief=tk.FLAT, padx=10, pady=10)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        self.apps_frame = tk.LabelFrame(self.bottom_container, text=" MODULES ")
        self.apps_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        self.btn_grid = tk.Frame(self.apps_frame)
        self.btn_grid.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.notes_frame = tk.LabelFrame(self.bottom_container, text=" SCRATCHPAD ")
        self.notes_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.notes_text = tk.Text(self.notes_frame, height=12, width=20, relief=tk.FLAT, padx=10, pady=10, undo=True)
        self.notes_text.pack(fill=tk.BOTH, expand=True)

        self.anim_container = tk.Frame(self.main_frame, width=300, height=600)
        self.anim_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.anim_container.pack_propagate(False)
        self.animator = AsciiAnimator(self.anim_container, width=300, height=600)
        threading.Thread(target=self.load_programs_and_modules_threaded, daemon=True).start()

    def apply_theme(self, theme_filename):
        t = ThemeManager.load_theme(theme_filename)
        self.current_theme_data = t
        self.current_theme_file = theme_filename
        f_main = tuple(t["font_main"])
        f_mono = tuple(t["font_mono"])
        self.root.configure(bg=t["bg_root"])
        for frame in [self.main_frame, self.left_frame, self.middle_frame, self.top_rect,
                      self.bottom_container, self.info_frame, self.apps_frame,
                      self.notes_frame, self.btn_grid]:
            if frame:
                frame.configure(bg=t["bg_panel"])
        for btn in [self.btn_launch, self.btn_refresh, self.btn_settings, 
                    self.btn_add, self.btn_remove]:
            btn.configure(bg=t["btn_bg"], fg=t["btn_fg"], 
                          activebackground=t["btn_active_bg"], 
                          activeforeground=t["btn_active_fg"], 
                          font=f_main, relief=tk.FLAT)
        
        if hasattr(self, 'mute_btn'):
            bg = t["mute_active_bg"] if self.is_muted else t["mute_bg"]
            self.mute_btn.configure(bg=bg, fg=t["mute_fg"], 
                                    activebackground=t["mute_active_bg"],
                                    activeforeground=t["mute_fg"],
                                    font=f_main, relief=tk.FLAT)
        if hasattr(self, 'volume_slider'):
            self.volume_slider.configure(bg=t["slider_bg"], troughcolor=t["slider_trough"],
                                         activebackground=t["slider_slider"], 
                                         highlightthickness=0, relief=tk.FLAT)
            self.volume_slider.configure(sliderrelief=tk.FLAT)
        self.info_text.configure(bg=t["info_text_bg"], fg=t["info_text_fg"], font=f_mono, relief=tk.FLAT)
        self.notes_text.configure(bg=t["info_text_bg"], fg=t["info_text_fg"], font=f_mono, relief=tk.FLAT)
        self.info_frame.configure(fg=t["info_frame_fg"], font=f_main, bg=t["bg_panel"])
        self.apps_frame.configure(fg=t["info_frame_fg"], font=f_main, bg=t["bg_panel"])
        self.notes_frame.configure(fg=t["info_frame_fg"], font=f_main, bg=t["bg_panel"])
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=t["tree_bg"], foreground=t["tree_fg"], 
                        fieldbackground=t["tree_bg"], font=f_mono)
        style.map("Treeview", background=[('selected', t["tree_selected_bg"])], 
                  foreground=[('selected', t["tree_selected_fg"])])
        style.configure("Treeview.Heading", background=t["tree_header_bg"], 
                        foreground=t["tree_header_fg"], font=f_main)
        if hasattr(self, 'animator'):
            self.animator.set_bg_color(t["bg_anim_frame"])
        if hasattr(self, 'btn_grid'):
            for widget in self.btn_grid.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(bg=t["btn_bg"], fg=t["btn_fg"],
                                    activebackground=t["btn_active_bg"],
                                    activeforeground=t["btn_active_fg"],
                                    font=f_main, relief=tk.FLAT)

    def scan_modules_for_buttons_data(self):
        self.pending_modules = []
        base_path = os.path.dirname(os.path.abspath(__file__))
        modules_path = os.path.join(base_path, MODULES_DIR)
        if not os.path.exists(modules_path): return

        subdirs = [d for d in os.listdir(modules_path) if os.path.isdir(os.path.join(modules_path, d))]
        for folder in subdirs:
            folder_full = os.path.join(modules_path, folder)
            py_files = glob.glob(os.path.join(folder_full, "*.py")) + glob.glob(os.path.join(folder_full, "*.pyw"))
            if py_files:
                target_py = sorted(py_files)[0]
                icon_path = os.path.join(folder_full, "icon.ico")
                self.pending_modules.append({
                    "path": target_py,
                    "name": os.path.splitext(os.path.basename(target_py))[0].upper(),
                    "icon": icon_path if os.path.exists(icon_path) else None
                })
                
    def rebuild_module_grid(self):
        for widget in self.btn_grid.winfo_children():
            widget.destroy()
        
        num_columns = 3
        t = self.current_theme_data  
        
        for i, mod in enumerate(self.pending_modules):
            img = None
            if mod["icon"]:
                try:
                    raw_img = Image.open(mod["icon"]).resize((32, 32), Image.Resampling.LANCZOS)
                    img = ImageTk.PhotoImage(raw_img)
                    self.module_icons.append(img)
                except: pass

            btn = tk.Button(self.btn_grid, text=mod["name"], image=img, compound=tk.TOP, 
                            relief=tk.FLAT, command=lambda p=mod["path"]: self.direct_launch(p))
            btn.grid(row=i // num_columns, column=i % num_columns, padx=5, pady=5, sticky="nsew")
            btn.configure(bg=t["btn_bg"], fg=t["btn_fg"], 
                          activebackground=t["btn_active_bg"],
                          activeforeground=t["btn_active_fg"], 
                          font=tuple(t["font_main"]))

    def direct_launch(self, path):
        if os.path.exists(path):
            try:
                if sys.platform == "win32" and path.lower().endswith('.pyw'):
                    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
                    if not os.path.exists(pythonw):
                        pythonw = sys.executable
                    subprocess.Popen([pythonw, path], cwd=os.path.dirname(path))
                else:
                    subprocess.Popen([sys.executable, path], cwd=os.path.dirname(path),
                                     creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
            except Exception as e:
                messagebox.showerror("Launch Error", f"Failed to launch:\n{e}")
        else:
            messagebox.showerror("Error", f"File not found: {path}")

    def launch_program(self):
        sel = self.tree.selection()
        if sel:
            path = self.tree.item(sel[0])["values"][0]
            self.direct_launch(path)

    def open_theme_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Themes")
        top.geometry("300x150")
        themes = ThemeManager.get_available_themes()
        combo = ttk.Combobox(top, values=themes, state="readonly")
        combo.pack(pady=20)
        def apply_sel():
            self.config["theme"] = combo.get()
            self.save_launcher_config()
            self.apply_theme(combo.get())
            top.destroy()
        tk.Button(top, text="APPLY", command=apply_sel).pack()

    def scan_local_py_files(self):
        if os.path.exists(SCAN_CACHE_FILE):
            cache_mtime = os.path.getmtime(SCAN_CACHE_FILE)
            if time.time() - cache_mtime < CACHE_TTL:
                try:
                    with open(SCAN_CACHE_FILE, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        self.programs = cached
                        return
                except:
                    pass

        self.programs = []
        base_dir = os.path.dirname(os.path.abspath(__file__))
        for file in os.listdir(base_dir):
            if file.endswith((".py", ".pyw")) and file != os.path.basename(__file__):
                path = os.path.join(base_dir, file)
                self.programs.append({
                    "name": os.path.splitext(file)[0],
                    "path": path,
                    "info": ""
                })

        try:
            with open(SCAN_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.programs, f, indent=2)
        except Exception as e:
            print(f"Failed to write scan cache: {e}")

    def show_info(self, event):
        sel = self.tree.selection()
        if sel:
            item = sel[0]
            name = self.tree.item(item)["text"]
            path = self.tree.item(item)["values"][0]
            prog = next((p for p in self.programs if p["name"] == name and p["path"] == path), None)
            if prog:
                if hasattr(self, 'desc_save_timer') and self.desc_save_timer:
                    self.root.after_cancel(self.desc_save_timer)
                self.info_text.config(state=tk.NORMAL)
                self.info_text.delete(1.0, tk.END)
                
                is_custom = prog in self.custom_programs
                if is_custom:
                    desc = self.load_description(prog)
                    self.info_text.insert(tk.END, desc if desc else "Add a description for this program...")
                    self.info_text.config(state=tk.NORMAL)
                    self.info_text.bind("<KeyRelease>", lambda e, p=prog: self.on_desc_typed(p))
                else:
                    nfo_path = os.path.splitext(prog["path"])[0] + ".nfo"
                    if os.path.exists(nfo_path):
                        try:
                            with open(nfo_path, 'r', errors='ignore') as f:
                                info_text = f.read()
                        except:
                            info_text = "Could not read .nfo file."
                    else:
                        info_text = "No .nfo file found for this program."
                    prog["info"] = info_text
                    self.info_text.insert(tk.END, info_text)
                    self.info_text.config(state=tk.DISABLED)
                    self.info_text.unbind("<KeyRelease>")
    
    def on_desc_typed(self, program):
        if hasattr(self, 'desc_save_timer') and self.desc_save_timer:
            self.root.after_cancel(self.desc_save_timer)
        self.desc_save_timer = self.root.after(500, lambda: self.save_desc_to_file(program))

    def save_desc_to_file(self, program):
        content = self.info_text.get("1.0", tk.END).rstrip("\n")
        self.save_description(program, content)
        self.desc_save_timer = None

    def refresh_list(self):
        existing_paths = {p["path"] for p in self.programs}
        for custom in self.custom_programs:
            if custom["path"] not in existing_paths:
                self.programs.append(custom)
        for r in self.tree.get_children():
            self.tree.delete(r)
        for prog in self.programs:
            icon = self.load_program_icon(prog)
            if icon:
                self.program_icons[prog["path"]] = icon
            self.tree.insert("", tk.END, text=prog["name"], values=(prog["path"],), image=icon)
        self.scan_modules_for_buttons_data()
        self.rebuild_module_grid()

    def setup_notes_autosave(self):
        self.notes_save_timer = None
        self.notes_text.bind("<KeyRelease>", self.on_notes_typed)
        notes_dir = "Notes"
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir)
        notes_file = os.path.join(notes_dir, "scratchpad.txt")
        if os.path.exists(notes_file):
            try:
                with open(notes_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.notes_text.insert("1.0", content)
            except Exception as e:
                print(f"Error loading scratchpad: {e}")

    def on_notes_typed(self, event=None):
        if self.notes_save_timer:
            self.root.after_cancel(self.notes_save_timer)
        self.notes_save_timer = self.root.after(500, self.save_notes_to_file)

    def save_notes_to_file(self):
        notes_dir = "Notes"
        if not os.path.exists(notes_dir):
            os.makedirs(notes_dir)
        notes_file = os.path.join(notes_dir, "scratchpad.txt")
        try:
            content = self.notes_text.get("1.0", tk.END)
            with open(notes_file, "w", encoding="utf-8") as f:
                f.write(content.rstrip("\n"))
        except Exception as e:
            print(f"Error saving scratchpad: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not set icon: {e}")
    app = LauncherApp(root)
    root.mainloop()