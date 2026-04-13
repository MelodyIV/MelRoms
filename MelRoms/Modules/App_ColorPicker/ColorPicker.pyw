import tkinter as tk
import os
from tkinter import messagebox
import pyautogui
from PIL import Image, ImageTk
import colorsys

COLOR_NAMES = {
    (255, 0, 0): "Red", (220, 20, 60): "Crimson", (178, 34, 34): "Firebrick",
    (139, 0, 0): "Dark Red", (128, 0, 0): "Maroon",
    (255, 105, 180): "Hot Pink", (255, 192, 203): "Pink",
    (165, 42, 42): "Brown", (139, 69, 19): "Saddle Brown",
    (255, 140, 0): "Dark Orange", (255, 165, 0): "Orange",
    (255, 255, 0): "Yellow", (0, 255, 0): "Lime", (0, 128, 0): "Green",
    (0, 255, 255): "Cyan", (0, 0, 255): "Blue", (75, 0, 130): "Indigo",
    (128, 0, 128): "Purple", (255, 0, 255): "Magenta",
    (255, 255, 255): "White", (0, 0, 0): "Black", (128, 128, 128): "Gray",
    (105, 105, 105): "Dim Gray"
}

BG_DARK = "#050514"        
BG_CARD = "#0A0A1A"        
ACCENT_TEAL = "#39C5BB"    
ACCENT_PINK = "#FF6AAA"       
TEXT_WHITE = "#C8FFFA"        
TEXT_MUTED = "#6B8A8E"        
BUTTON_BG = "#141424"
BUTTON_ACTIVE = "#1F1F35"
SLIDER_TROUGH = "#1A1A2E"
HIGHLIGHT = "#39C5BB"

class ColorPickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Melody's Color Picker")
        self.root.geometry("430x620")
        self.root.minsize(400, 580)
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        self.current_rgb = (255, 255, 255)
        try:
            base_dir = os.path.dirname(__file__)
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon failed to load: {e}")

        self._setup_ui()

    def _setup_ui(self):
        title_frame = tk.Frame(self.root, bg=BG_CARD, height=45)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="✦ MELODY'S COLOR PICKER ✦",
                 font=("Consolas", 14, "bold"),
                 bg=BG_CARD, fg=ACCENT_TEAL).pack(expand=True)

        main = tk.Frame(self.root, bg=BG_DARK, padx=20, pady=15)
        main.pack(fill="both", expand=True)

        card = tk.Frame(main, bg=BG_CARD, highlightbackground=ACCENT_TEAL,
                        highlightthickness=1, padx=20, pady=20)
        card.pack(fill="both", expand=True)

        tk.Label(card, text="🔍 SCREEN PICKER",
                 font=("Consolas", 11, "bold"),
                 bg=BG_CARD, fg=ACCENT_TEAL).pack(anchor="w")
        tk.Label(card, text="Click the button, then click anywhere on your screen",
                 font=("Segoe UI", 8), bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 8))

        self.btn_pick = tk.Button(card, text="CAPTURE COLOR FROM SCREEN",
                                  command=self.start_screen_pick,
                                  bg=BUTTON_BG, fg=ACCENT_PINK,
                                  activebackground=BUTTON_ACTIVE, activeforeground=ACCENT_PINK,
                                  font=("Consolas", 10, "bold"),
                                  relief="flat", bd=0, highlightthickness=0,
                                  padx=15, pady=8, cursor="hand2")
        self.btn_pick.pack()

        preview_frame = tk.Frame(card, bg=BG_CARD)
        preview_frame.pack(pady=18)
        self.preview_canvas = tk.Canvas(preview_frame, width=160, height=100,
                                        bg="#FFFFFF", highlightthickness=2,
                                        highlightbackground=ACCENT_TEAL)
        self.preview_canvas.pack()

        slider_frame = tk.Frame(card, bg=BG_CARD)
        slider_frame.pack(fill="x", pady=8)

        self.r_var = tk.IntVar(value=255)
        self.g_var = tk.IntVar(value=255)
        self.b_var = tk.IntVar(value=255)

        self._create_slider(slider_frame, "R", self.r_var, ACCENT_PINK)
        self._create_slider(slider_frame, "G", self.g_var, ACCENT_TEAL)
        self._create_slider(slider_frame, "B", self.b_var, ACCENT_TEAL)

        info_frame = tk.Frame(card, bg=BG_CARD)
        info_frame.pack(fill="x", pady=(10, 4))

        self.name_label = tk.Label(info_frame, text="COLOR NAME: WHITE",
                                   font=("Consolas", 10, "bold"),
                                   bg=BG_CARD, fg=TEXT_WHITE)
        self.name_label.pack(anchor="w")

        self.hex_label = tk.Label(info_frame, text="#FFFFFF",
                                  font=("Consolas", 16, "bold"),
                                  bg=BG_CARD, fg=ACCENT_TEAL)
        self.hex_label.pack(anchor="w", pady=(3, 0))

        btn_frame = tk.Frame(card, bg=BG_CARD)
        btn_frame.pack(fill="x", pady=(12, 0))

        copy_hex_btn = tk.Button(btn_frame, text="📋 COPY HEX",
                                 command=self.copy_hex,
                                 bg=BUTTON_BG, fg=ACCENT_TEAL,
                                 activebackground=BUTTON_ACTIVE, activeforeground=ACCENT_TEAL,
                                 font=("Consolas", 9, "bold"),
                                 relief="flat", bd=0, highlightthickness=0,
                                 padx=10, pady=5)
        copy_hex_btn.pack(side="left", padx=(0, 8))

        copy_rgb_btn = tk.Button(btn_frame, text="📋 COPY RGB",
                                 command=self.copy_rgb,
                                 bg=BUTTON_BG, fg=ACCENT_PINK,
                                 activebackground=BUTTON_ACTIVE, activeforeground=ACCENT_PINK,
                                 font=("Consolas", 9, "bold"),
                                 relief="flat", bd=0, highlightthickness=0,
                                 padx=10, pady=5)
        copy_rgb_btn.pack(side="left")

        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(main, textvariable=self.status_var,
                          font=("Consolas", 8), bg=BG_DARK, fg=TEXT_MUTED)
        status.pack(pady=(8, 0))

        self._update_display()

    def _create_slider(self, parent, label, var, color):
        frame = tk.Frame(parent, bg=BG_CARD)
        frame.pack(fill="x", pady=4)
        lbl = tk.Label(frame, text=label, font=("Consolas", 10, "bold"),
                       bg=BG_CARD, fg=color, width=3, anchor="e")
        lbl.pack(side="left", padx=(0, 8))
        scale = tk.Scale(frame, from_=0, to=255, orient="horizontal",
                         variable=var, command=lambda _: self._on_slider_change(),
                         bg=BG_CARD, fg=TEXT_WHITE, highlightthickness=0,
                         troughcolor=SLIDER_TROUGH, activebackground=color,
                         length=240, borderwidth=0)
        scale.pack(side="left", fill="x", expand=True)
        val_label = tk.Label(frame, textvariable=var, font=("Consolas", 8),
                             bg=BG_CARD, fg=TEXT_MUTED, width=4)
        val_label.pack(side="left", padx=(8, 0))

    def _on_slider_change(self):
        r = self.r_var.get()
        g = self.g_var.get()
        b = self.b_var.get()
        self.current_rgb = (r, g, b)
        self._update_display()

    def _update_display(self):
        r, g, b = self.current_rgb
        hex_color = f"#{r:02X}{g:02X}{b:02X}"
        self.preview_canvas.configure(bg=hex_color)
        self.hex_label.config(text=hex_color)
        self.name_label.config(text=f"COLOR NAME: {self._get_color_name(r, g, b)}")
        if self.r_var.get() != r:
            self.r_var.set(r)
        if self.g_var.get() != g:
            self.g_var.set(g)
        if self.b_var.get() != b:
            self.b_var.set(b)
        self.status_var.set(f"RGB({r}, {g}, {b})")

    def _get_color_name(self, r, g, b):
        min_dist = float('inf')
        closest_name = "Custom"
        for (cr, cg, cb), name in COLOR_NAMES.items():
            dist = (r - cr)**2 + (g - cg)**2 + (b - cb)**2
            if dist < min_dist:
                min_dist = dist
                closest_name = name
        return closest_name

    def start_screen_pick(self):
        self.status_var.set("Click anywhere on screen...")
        self.root.withdraw()
        self.root.after(300, self._capture_pixel)

    def _capture_pixel(self):
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-alpha", 0.01)
        overlay.config(cursor="crosshair")
        overlay.overrideredirect(True)

        def on_click(event):
            try:
                x, y = pyautogui.position()
                screenshot = pyautogui.screenshot(region=(x, y, 1, 1))
                pix = screenshot.getpixel((0, 0))
                self.current_rgb = pix
            except Exception as e:
                messagebox.showerror("Error", f"Failed to capture color:\n{str(e)}")
            finally:
                overlay.destroy()
                self.root.deiconify()
                self._update_display()
                self.status_var.set("Color captured!")

        overlay.bind("<Button-1>", on_click)
        overlay.bind("<Escape>", lambda e: [overlay.destroy(), self.root.deiconify(), 
                                            self.status_var.set("Cancelled")])

    def copy_hex(self):
        r, g, b = self.current_rgb
        hex_val = f"#{r:02X}{g:02X}{b:02X}"
        self.root.clipboard_clear()
        self.root.clipboard_append(hex_val)
        self.status_var.set(f"Copied {hex_val} to clipboard")

    def copy_rgb(self):
        r, g, b = self.current_rgb
        rgb_val = f"{r}, {g}, {b}"
        self.root.clipboard_clear()
        self.root.clipboard_append(rgb_val)
        self.status_var.set(f"Copied RGB({rgb_val}) to clipboard")

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()