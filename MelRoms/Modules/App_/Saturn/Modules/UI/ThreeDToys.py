import customtkinter as ctk
import tkinter as tk
import math
import random
import time
import sys
import os

# 1. Force the script to look at its own directory for UI.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 2. Robust import for COLORS to prevent circular dependency crashes
try:
    import UI
    COLORS = UI.COLORS
except (ImportError, AttributeError):
    # Fallback to keep the toys visible if UI.py is currently loading elsewhere
    COLORS = {
        "chat_bg": "#120d22",
        "accent": "#b87cff",
        "border": "#4a2e6e",
        "user_bubble": "#6a1b9a",
        "assistant_bubble": "#2a1e4b",
        "text": "#e0d0ff"
    }


class ToyObject:
    """Base class for interactive wireframe objects (heart, cube, star, or planet)"""
    def __init__(self, canvas, x, y, obj_type="heart"):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = random.uniform(-2.5, 2.5)
        self.vy = random.uniform(-2.5, 2.5)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-3, 3)
        self.obj_type = obj_type
        self.radius = 35
        self.id = None
        self._create()

    def _create(self):
        # Map types to cute cosmic emojis/symbols
        look = {
            "heart": ("❤️", "#ff69b4", 42),
            "cube": ("🧊", "#b87cff", 38),
            "star": ("⭐", "#ffd700", 40),
            "planet": ("🪐", "#9b5de5", 45)
        }
        text, color, size = look.get(self.obj_type, ("✨", "#ffffff", 38))
        
        self.id = self.canvas.create_text(
            self.x, self.y,
            text=text,
            font=("Segoe UI", size),
            fill=color,
            tags="toy"
        )

    def update(self):
        # Physics
        self.x += self.vx
        self.y += self.vy
        self.rotation += self.rot_speed

        # Gentle friction (Space vacuum isn't perfect here!)
        self.vx *= 0.985
        self.vy *= 0.985
        self.rot_speed *= 0.99

        # Bounce off edges with a bit of energy loss
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # Ensure we have valid dimensions
        if w <= 1: w = 190
        if h <= 1: h = 150

        if self.x < 30:
            self.x = 30
            self.vx = abs(self.vx) * 0.7
        elif self.x > w - 30:
            self.x = w - 30
            self.vx = -abs(self.vx) * 0.7
            
        if self.y < 30:
            self.y = 30
            self.vy = abs(self.vy) * 0.7
        elif self.y > h - 30:
            self.y = h - 30
            self.vy = -abs(self.vy) * 0.7

        # Pulsing animation effect based on rotation
        base_size = 40 if self.obj_type != "cube" else 35
        pulse = 1 + 0.1 * math.sin(math.radians(self.rotation * 2))
        self.canvas.itemconfig(self.id, font=("Segoe UI", int(base_size * pulse)))

        self.canvas.coords(self.id, self.x, self.y)


class Particle:
    """Pretty explosion or trail particle"""
    def __init__(self, canvas, x, y, color=None, speed=6):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.vx = random.uniform(-speed, speed)
        self.vy = random.uniform(-speed, speed)
        self.life = random.randint(15, 35)
        colors = ["#b87cff", "#ff69b4", "#7a5cff", "#ffd700", "#00ffcc"]
        self.color = color if color else random.choice(colors)
        self.size = random.randint(2, 5)
        self.id = self.canvas.create_oval(
            x, y, x+self.size, y+self.size,
            fill=self.color, outline=""
        )

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1  # slight gravity
        self.life -= 1
        
        if self.life > 0:
            self.canvas.coords(self.id, self.x, self.y, self.x+self.size, self.y+self.size)
            return True
        else:
            self.canvas.delete(self.id)
            return False


class ThreeDToys(tk.Canvas):
    """Interactive 3D wireframe toy panel"""
    def __init__(self, parent, width=190, height=150):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS["chat_bg"],
            highlightthickness=2,
            highlightbackground="#4a2e6e",
            highlightcolor="#b87cff"
        )
        self.objects = []
        self.particles = []
        self.mouse_x = width // 2
        self.mouse_y = height // 2
        self.is_pressing = False
        
        # Initial wait to let UI render before spawning
        self.after(100, self._spawn_initial_toys)
        self._bind_events()
        self._animate()

    def _spawn_initial_toys(self):
        for _ in range(3):
            self._spawn_single_toy()

    def _spawn_single_toy(self):
        w = self.winfo_width()
        h = self.winfo_height()
        if w <= 1: w = 190 
        if h <= 1: h = 150  
        
        x = random.randint(40, max(41, w - 40))
        y = random.randint(40, max(41, h - 40))
        obj_type = random.choice(["heart", "cube", "star", "planet"])
        self.objects.append(ToyObject(self, x, y, obj_type))

    def _bind_events(self):
        self.bind("<Motion>", self._update_mouse)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<B1-Motion>", self._update_mouse)
        self.bind("<Button-3>", self._on_right_click)

    def _update_mouse(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _on_press(self, event):
        self.is_pressing = True

    def _on_release(self, event):
        self.is_pressing = False
        # Fling logic: give toys a boost when you let go
        for obj in self.objects:
            dist = math.hypot(obj.x - event.x, obj.y - event.y)
            if dist < 100:
                obj.vx += random.uniform(-5, 5)
                obj.vy += random.uniform(-5, 5)

    def _on_right_click(self, event):
        """Right click = Pop the toy and spawn a new one elsewhere"""
        for i, obj in enumerate(self.objects):
            dist = math.hypot(obj.x - event.x, obj.y - event.y)
            if dist < 50:
                self._explode(obj.x, obj.y)
                self.delete(obj.id)
                del self.objects[i]
                self.after(1000, self._spawn_single_toy)
                break

    def _explode(self, x, y):
        for _ in range(25):
            self.particles.append(Particle(self, x, y))

    def _animate(self):
        # Update objects
        for obj in self.objects:
            dx = obj.x - self.mouse_x
            dy = obj.y - self.mouse_y
            dist = math.hypot(dx, dy)
            
            if dist < 150 and dist > 1:
                if self.is_pressing:
                    # GRAVITY WELL: Suck objects toward mouse
                    obj.vx -= (dx / dist) * 0.8
                    obj.vy -= (dy / dist) * 0.8
                else:
                    # REPULSION: Gently push away
                    force = (150 - dist) / 150
                    obj.vx += (dx / dist) * force * 1.5
                    obj.vy += (dy / dist) * force * 1.5

            # Trail particles for fast moving objects
            if math.hypot(obj.vx, obj.vy) > 4:
                if random.random() > 0.7:
                    self.particles.append(Particle(self, obj.x, obj.y, color="#b87cff", speed=1))

            obj.update()

        # Update particles
        self.particles = [p for p in self.particles if p.update()]

        self.after(30, self._animate)

    def reset_toys(self):
        for obj in self.objects:
            self.delete(obj.id)
        self.objects.clear()
        self._spawn_initial_toys()

# ====================== EXPORT ======================
__all__ = ["ThreeDToys"]