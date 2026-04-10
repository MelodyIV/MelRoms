import customtkinter as ctk
import tkinter as tk
import math
import time
import random
import sys
import os

# 1. Force the script to look at its own directory for UI.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 2. Robust import for COLORS
try:
    import UI
    COLORS = UI.COLORS
except (ImportError, AttributeError):
    # Fallback to keep the waves purple if UI.py is locked/loading
    COLORS = {
        "chat_bg": "#120d22",
        "accent": "#b87cff",
        "border": "#4a2e6e"
    }

class WavyWireframe(tk.Canvas):
    """
    Animated wavy purple wireframe at the bottom of the chat area.
    Looks like a soft cosmic energy field.
    """
    def __init__(self, parent, height: int = 45):
        super().__init__(
            parent,
            height=height,
            bg=COLORS["chat_bg"],
            highlightthickness=0
        )
        self.offset = 0.0
        self.wave_color = "#9b5de5"      # Main purple
        self.accent_color = "#b87cff"    # Brighter highlight
        self._animate()

    def _animate(self):
        self.delete("wave")
        w = self.winfo_width()
        h = self.winfo_height()

        if w < 50:
            self.after(100, self._animate)
            return

        # Create multiple layered waves for depth
        for layer in range(3):
            points = []
            amplitude = 8 - layer * 2
            frequency = 0.028 + layer * 0.008
            speed = 1.8 - layer * 0.4
            alpha = 0.9 - layer * 0.25

            for x in range(0, w + 20, 12):
                y = h - 12 + amplitude * math.sin((x * frequency) + (self.offset * speed))
                points.append((x, y))

            # Main wave line
            color = self.wave_color if layer == 0 else self.accent_color
            width = 3.5 - layer * 0.8

            for i in range(len(points) - 1):
                self.create_line(
                    points[i][0], points[i][1],
                    points[i+1][0], points[i+1][1],
                    fill=color,
                    width=width,
                    tags="wave"
                )

        self.offset += 0.12
        self.after(45, self._animate)


# ====================== 3D WIRE FRAME DECORATIVE ELEMENTS ======================

class WireframeHeart(tk.Canvas):
    """Small floating 3D-style wireframe heart (can be used as decoration or toy)"""
    def __init__(self, parent, size=60):
        super().__init__(parent, width=size, height=size, bg="transparent", highlightthickness=0)
        self.size = size
        self.angle = 0
        self._draw_heart()
        self._animate()

    def _draw_heart(self):
        self.delete("all")
        cx, cy = self.size//2, self.size//2
        scale = self.size / 100

        # Wireframe heart points (approximate)
        points = [
            (cx-25*scale, cy-10*scale),
            (cx-35*scale, cy-25*scale),
            (cx-20*scale, cy-35*scale),
            (cx, cy-20*scale),
            (cx+20*scale, cy-35*scale),
            (cx+35*scale, cy-25*scale),
            (cx+25*scale, cy-10*scale),
            (cx, cy+15*scale)
        ]

        # Draw wireframe lines
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i+1) % len(points)]
            self.create_line(x1, y1, x2, y2, fill="#b87cff", width=2.5, smooth=True)

        # Inner glow dots
        for i in range(0, len(points), 2):
            self.create_oval(
                points[i][0]-3, points[i][1]-3,
                points[i][0]+3, points[i][1]+3,
                fill="#ff69b4", outline=""
            )

    def _animate(self):
        self.angle += 1.2
        # Gentle floating + rotation effect
        self.place_configure(
            y=int(5 * math.sin(math.radians(self.angle * 2)))
        )
        self.after(60, self._animate)


class WireframeCube(tk.Canvas):
    """Small rotating 3D wireframe cube decoration"""
    def __init__(self, parent, size=70):
        super().__init__(parent, width=size, height=size, bg="transparent", highlightthickness=0)
        self.size = size
        self.rotation = 0
        self._animate()

    def _draw_cube(self):
        self.delete("all")
        s = self.size
        cx, cy = s//2, s//2
        r = self.rotation * 0.8

        # Simple isometric cube projection
        offset = int(12 * math.sin(math.radians(r)))

        # Back face
        self.create_rectangle(cx-22, cy-22+offset, cx+22, cy+22+offset,
                              outline="#6a1b9a", width=2)

        # Front face
        self.create_rectangle(cx-28, cy-28, cx+28, cy+28,
                              outline="#b87cff", width=2.5)

        # Connecting lines
        self.create_line(cx-22, cy-22+offset, cx-28, cy-28, fill="#9b5de5", width=2)
        self.create_line(cx+22, cy-22+offset, cx+28, cy+28, fill="#9b5de5", width=2)
        self.create_line(cx-22, cy+22+offset, cx-28, cy+28, fill="#9b5de5", width=2)
        self.create_line(cx+22, cy+22+offset, cx+28, cy+28, fill="#9b5de5", width=2)

        # Corner highlight dots
        self.create_oval(cx-30, cy-30, cx-24, cy-24, fill="#ffd700", outline="")

    def _animate(self):
        self.rotation += 1.8
        self._draw_cube()
        self.after(70, self._animate)

# ====================== NEW EXPANDED ELEMENTS ======================

class WireframeStar(tk.Canvas):
    """Twinkling 3D-style wireframe star"""
    def __init__(self, parent, size=50):
        super().__init__(parent, width=size, height=size, bg="transparent", highlightthickness=0)
        self.size = size
        self.rotation = 0
        self._animate()

    def _draw_star(self):
        self.delete("all")
        cx, cy = self.size//2, self.size//2
        r = self.size // 2.5
        
        points = []
        for i in range(10):
            angle = math.radians(i * 36 + self.rotation)
            dist = r if i % 2 == 0 else r // 2
            points.append(cx + dist * math.cos(angle))
            points.append(cy + dist * math.sin(angle))
            
        self.create_polygon(points, outline="#00F2FF", fill="", width=2)
        
        # Glow center
        glow = abs(math.sin(math.radians(self.rotation * 2))) * 4
        self.create_oval(cx-glow, cy-glow, cx+glow, cy+glow, fill="#00F2FF", outline="")

    def _animate(self):
        self.rotation += 2
        self._draw_star()
        self.after(50, self._animate)

class WireframePlanet(tk.Canvas):
    """Wireframe planet with a rotating ring"""
    def __init__(self, parent, size=80):
        super().__init__(parent, width=size, height=size, bg="transparent", highlightthickness=0)
        self.size = size
        self.angle = 0
        self._animate()

    def _draw_planet(self):
        self.delete("all")
        cx, cy = self.size//2, self.size//2
        r = self.size // 4
        
        # Planet Sphere
        self.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#b87cff", width=2)
        
        # Rotating Ring (Ellipse)
        ring_w = r * 2.5
        ring_h = r * 0.8 * math.sin(math.radians(self.angle))
        self.create_oval(cx-ring_w/2, cy-ring_h/2, cx+ring_w/2, cy+ring_h/2, outline="#FF007A", width=1.5)

    def _animate(self):
        self.angle += 3
        self._draw_planet()
        self.after(60, self._animate)


# ====================== EXPORT ======================
__all__ = [
    "WavyWireframe",
    "WireframeHeart",
    "WireframeCube",
    "WireframeStar",
    "WireframePlanet"
]