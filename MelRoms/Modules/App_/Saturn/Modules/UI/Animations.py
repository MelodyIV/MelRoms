import customtkinter as ctk
import tkinter as tk
import time
import random
import math
import sys
import os

# 1. Add current directory to path so it can find UI.py
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 2. Import CURRENT_THEME from UI.py
try:
    from UI import CURRENT_THEME
except (ImportError, AttributeError):
    # Fallback if UI.py is not found or has issues
    CURRENT_THEME = {
        "chat_bg": "#120d22",
        "accent": "#b87cff",
        "text": "#e0d0ff"
    }

# ====================== THINKING ANIMATION ======================
class ThinkingAnimation(ctk.CTkFrame):
    def __init__(self, parent, mode: str = "bouncing_hearts"):
        super().__init__(parent, fg_color="transparent", height=60)
        self.mode = mode
        self.anim_id = None
        self.canvas = tk.Canvas(
            self,
            bg=CURRENT_THEME.get("chat_bg", "#120d22"),
            highlightthickness=0,
            height=55,
            width=280
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=5)
        self._start_animation()

    def _start_animation(self):
        if self.mode == "bouncing_hearts":
            self._bouncing_hearts()
        elif self.mode == "spinning_cat":
            self._spinning_cat()
        elif self.mode == "wiggling_stars":
            self._wiggling_stars()
        elif self.mode == "floating_sparkles":
            self._floating_sparkles()
        else:
            self._bouncing_hearts()  # fallback

    def _bouncing_hearts(self):
        """Classic bouncing hearts animation"""
        hearts = []
        for i in range(7):
            x = 25 + i * 35
            heart = self.canvas.create_text(
                x, 25,
                text="❤️",
                font=("Segoe UI", 22),
                fill="#ff69b4"
            )
            hearts.append((heart, x, random.uniform(0.8, 1.6)))
        
        def bounce():
            for heart, orig_x, speed in hearts:
                y = 25 + 12 * math.sin(time.time() * speed * 3)
                self.canvas.coords(heart, orig_x, y)
            self.anim_id = self.after(40, bounce)
        bounce()

    def _spinning_cat(self):
        """Spinning cat faces - very cute"""
        cat = self.canvas.create_text(140, 28, text="🐱", font=("Segoe UI", 32))
       
        emojis = ["🐱", "😺", "😸", "😹", "😻", "😼", "😽", "🙀"]
       
        def spin():
            idx = int((time.time() * 6) % len(emojis))
            self.canvas.itemconfig(cat, text=emojis[idx])
            self.anim_id = self.after(110, spin)
        spin()

    def _wiggling_stars(self):
        """Wiggling purple and gold stars"""
        stars = []
        for i in range(6):
            x = 30 + i * 38
            size = random.randint(18, 26)
            star = self.canvas.create_text(
                x, 25,
                text="⭐",
                font=("Segoe UI", size),
                fill=CURRENT_THEME.get("accent", "#b87cff")
            )
            stars.append((star, x, random.uniform(0.4, 1.1)))
        
        def wiggle():
            for star, orig_x, speed in stars:
                offset = 6 * math.sin(time.time() * speed * 4)
                self.canvas.coords(star, orig_x + offset, 25)
            self.anim_id = self.after(50, wiggle)
        wiggle()

    def _floating_sparkles(self):
        """Gentle floating sparkles with color shift"""
        particles = []
        colors = [CURRENT_THEME.get("accent", "#b87cff"), "#ff69b4", "#7a5cff", "#ffd700"]
       
        for _ in range(9):
            x = random.randint(20, 260)
            y = random.randint(10, 45)
            size = random.randint(14, 20)
            color = random.choice(colors)
            spark = self.canvas.create_text(
                x, y,
                text="✨",
                font=("Segoe UI", size),
                fill=color
            )
            particles.append((spark, x, y, random.uniform(0.3, 0.9)))
        
        def float_up():
            for p in particles:
                spark, x, start_y, speed = p
                new_y = start_y - (time.time() * speed * 8) % 50
                self.canvas.coords(spark, x, new_y)
            self.anim_id = self.after(60, float_up)
        float_up()

    def stop(self):
        """Stop animation and clean up"""
        if self.anim_id:
            try:
                self.after_cancel(self.anim_id)
            except:
                pass
        self.destroy()


# ====================== CONFETTI BURST ======================
class ConfettiBurst:
    """Confetti explosion when starting new chat or long responses"""
    def __init__(self, parent_frame):
        self.canvas = tk.Canvas(
            parent_frame,
            highlightthickness=0,
            bg=CURRENT_THEME.get("chat_bg", "#120d22")
        )
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.particles = []
        self._create_confetti()

    def _create_confetti(self):
        colors = [
            CURRENT_THEME.get("accent", "#b87cff"),
            "#ff69b4", "#7a5cff", "#ffd700", "#00ffcc"
        ]
       
        for _ in range(80):
            x = random.randint(0, 1280)
            y = random.randint(-50, 100)
            size = random.randint(4, 9)
            color = random.choice(colors)
            angle = random.uniform(-2, 2)
           
            rect = self.canvas.create_rectangle(x, y, x+size, y+size, fill=color, outline="")
            self.particles.append((rect, y, angle, random.uniform(1.5, 4.0)))
        
        self._animate_confetti()

    def _animate_confetti(self):
        still_alive = []
        for rect, start_y, angle, speed in self.particles:
            coords = self.canvas.coords(rect)
            if not coords:
                continue
               
            new_y = coords[1] + speed
            new_x = coords[0] + angle
           
            if new_y < 800:  # still on screen
                self.canvas.move(rect, angle*0.6, speed)
                still_alive.append((rect, start_y, angle, speed))
            else:
                self.canvas.delete(rect)
       
        self.particles = still_alive
       
        if self.particles:
            self.canvas.after(25, self._animate_confetti)
        else:
            self.canvas.destroy()


# ====================== EXPORT ======================
__all__ = ["ThinkingAnimation", "ConfettiBurst"]