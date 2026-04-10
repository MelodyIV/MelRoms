import json
import threading
import queue
import time
from pathlib import Path
import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import ollama
import pyttsx3

# ====================== PATHS ======================
DATA_DIR = Path.home() / "SaturnAI"
DATA_DIR.mkdir(exist_ok=True)
THEMES_DIR = DATA_DIR / "Themes"
THEMES_DIR.mkdir(exist_ok=True)

HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

# ====================== THEME SYSTEM ======================
def load_theme(theme_name: str = "dark_neon"):
    theme_path = THEMES_DIR / f"{theme_name}.json"
    
    default_theme = {
        "name": "Dark Neon",
        "bg": "#0a0a1a",
        "top_bg": "#1a0f2e",
        "chat_bg": "#120d22",
        "user_bubble": "#6a1b9a",
        "assistant_bubble": "#2a1e4b",
        "accent": "#b87cff",
        "text": "#e0d0ff",
        "text_light": "#b0a0d0",
        "border": "#4a2e6e"
    }
    
    if theme_path.exists():
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                user_theme = json.load(f)
                default_theme.update(user_theme)
        except Exception as e:
            print(f"Theme load error: {e}")
    
    return default_theme


CURRENT_THEME = load_theme("dark_neon")


def apply_theme(app, theme_name=None):
    global CURRENT_THEME
    if theme_name:
        CURRENT_THEME = load_theme(theme_name)
    
    app.configure(fg_color=CURRENT_THEME["bg"])
    ctk.set_appearance_mode("dark")


# ====================== IMPORT ANIMATION ======================
from animations import ThinkingAnimation, ConfettiBurst


# ====================== MESSAGE BUBBLE ======================
class MessageBubble(ctk.CTkFrame):
    def __init__(self, parent, role, content):
        bubble_color = CURRENT_THEME["user_bubble"] if role == "user" else CURRENT_THEME["assistant_bubble"]
        align_side = "right" if role == "user" else "left"
        
        super().__init__(parent, fg_color="transparent")
        
        self.bubble = ctk.CTkFrame(self, fg_color=bubble_color, corner_radius=15)
        self.bubble.pack(side=align_side, padx=10, pady=5)
        
        self.textbox = ctk.CTkTextbox(
            self.bubble,
            fg_color="transparent",
            text_color=CURRENT_THEME["text"],
            font=("Segoe UI", 14),
            width=600,
            activate_scrollbars=False,
            wrap="word"
        )
        self.textbox.insert("1.0", content)
        self.textbox.configure(state="disabled")
        self.textbox.pack(padx=10, pady=10)
        
        self._adjust_height(content)

    def _adjust_height(self, text):
        lines = text.count('\n') + (len(text) // 60) + 1
        new_height = max(40, lines * 22)
        self.textbox.configure(height=new_height)

    def update_content(self, new_text):
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", new_text)
        self._adjust_height(new_text)
        self.textbox.configure(state="disabled")


# ====================== MAIN APP ======================
class SaturnApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Saturn - Your Cosmic Friend")
        self.geometry("950x780")
        
        apply_theme(self)
        
        self.chat_history = self.load_history()
        self.settings = self.load_settings()
        self.generating = False
        self.tts_engine = pyttsx3.init()
        self.msg_queue = queue.Queue()
        self.current_thinking_anim = None   # For animation control
        
        self.sound_enabled = tk.BooleanVar(value=self.settings.get("sound", True))
        self.tts_enabled = tk.BooleanVar(value=self.settings.get("tts", False))
        
        self._build_ui()
        self._load_initial_history()
        self.check_queue()

    def _build_ui(self):
        # ==================== TOP BAR ====================
        self.top_bar = ctk.CTkFrame(self, fg_color=CURRENT_THEME["top_bg"], height=60, corner_radius=0)
        self.top_bar.pack(side="top", fill="x")

        # Model Selector
        self.model_var = ctk.StringVar(value="gemma3:4b")
        self.model_menu = ctk.CTkOptionMenu(
            self.top_bar, 
            variable=self.model_var,
            values=["gemma3:4b"],
            fg_color=CURRENT_THEME["assistant_bubble"],
            button_color=CURRENT_THEME["user_bubble"],
            text_color=CURRENT_THEME["text"]
        )
        self.model_menu.pack(side="left", padx=15, pady=10)

        # Theme Selector
        theme_names = [f.stem for f in THEMES_DIR.glob("*.json")]
        if not theme_names:
            theme_names = ["dark_neon"]
        
        self.theme_var = ctk.StringVar(value="dark_neon")
        self.theme_menu = ctk.CTkOptionMenu(
            self.top_bar,
            variable=self.theme_var,
            values=theme_names,
            command=self.change_theme,
            fg_color=CURRENT_THEME["assistant_bubble"],
            button_color=CURRENT_THEME["accent"],
            text_color=CURRENT_THEME["text"]
        )
        self.theme_menu.pack(side="left", padx=10)

        # New Chat Button
        self.new_chat_btn = ctk.CTkButton(
            self.top_bar, 
            text="✨ New Chat", 
            width=110,
            fg_color=CURRENT_THEME["user_bubble"],
            hover_color=CURRENT_THEME["accent"],
            text_color=CURRENT_THEME["text"],
            command=self.clear_chat
        )
        self.new_chat_btn.pack(side="left", padx=5)

        # Toggles
        self.tts_toggle = ctk.CTkCheckBox(
            self.top_bar, 
            text="🗣️ TTS", 
            variable=self.tts_enabled, 
            text_color=CURRENT_THEME["text"]
        )
        self.tts_toggle.pack(side="right", padx=10)

        self.sound_toggle = ctk.CTkCheckBox(
            self.top_bar, 
            text="🔊 Sound", 
            variable=self.sound_enabled, 
            text_color=CURRENT_THEME["text"]
        )
        self.sound_toggle.pack(side="right", padx=10)

        # ==================== CHAT AREA ====================
        self.chat_frame = ctk.CTkFrame(self, fg_color=CURRENT_THEME["chat_bg"], corner_radius=15)
        self.chat_frame.pack(expand=True, fill="both", padx=15, pady=(15, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self.chat_frame, fg_color="transparent")
        self.scroll_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # ==================== INPUT AREA ====================
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.pack(fill="x", padx=20, pady=20)

        self.entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Ask Saturn something magical...",
            height=50,
            fg_color=CURRENT_THEME["assistant_bubble"],
            border_color=CURRENT_THEME["border"],
            text_color=CURRENT_THEME["text"]
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.send_message())
        self.entry.bind("<Control-Return>", lambda e: self.send_message())

        self.send_btn = ctk.CTkButton(
            self.input_frame, 
            text="🚀", 
            width=60, 
            height=50,
            fg_color=CURRENT_THEME["accent"],
            text_color="black",
            font=("Arial", 20, "bold"),
            command=self.send_message
        )
        self.send_btn.pack(side="right")

    # ====================== THEME CHANGE ======================
    def change_theme(self, theme_name: str):
        apply_theme(self, theme_name)
        
        self.top_bar.configure(fg_color=CURRENT_THEME["top_bg"])
        self.chat_frame.configure(fg_color=CURRENT_THEME["chat_bg"])
        self.entry.configure(
            fg_color=CURRENT_THEME["assistant_bubble"],
            border_color=CURRENT_THEME["border"],
            text_color=CURRENT_THEME["text"]
        )
        
        self._rebuild_chat_area()
        
        print(f"✅ Theme changed to: {CURRENT_THEME['name']}")

    def _rebuild_chat_area(self):
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        
        for msg in self.chat_history:
            self.add_bubble(msg["role"], msg["content"])
        
        self.scroll_frame._parent_canvas.yview_moveto(1.0)

    # ====================== CHAT FUNCTIONS ======================
    def send_message(self):
        text = self.entry.get().strip()
        if not text or self.generating:
            return
        self.entry.delete(0, tk.END)
        self.add_bubble("user", text)
        self.chat_history.append({"role": "user", "content": text})
        
        threading.Thread(target=self.generate_response, args=(text,), daemon=True).start()

    def generate_response(self, prompt):
        self.generating = True
        
        # Start thinking animation
        self.msg_queue.put({"type": "start_thinking"})
        
        full_response = ""
        
        try:
            system_prompt = self.settings.get("system_prompt", 
                "You are Saturn, a friendly cosmic creature who loves space and magic.")
            
            messages = [{"role": "system", "content": system_prompt}] + self.chat_history
            stream = ollama.chat(model=self.model_var.get(), messages=messages, stream=True)
            
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                self.msg_queue.put({"type": "update_response", "content": full_response})
                time.sleep(0.015)
            
            self.chat_history.append({"role": "assistant", "content": full_response})
            self.save_history()
            
            if self.sound_enabled.get():
                self.msg_queue.put({"type": "play_sound"})
            if self.tts_enabled.get():
                self.tts_engine.say(full_response)
                self.tts_engine.runAndWait()
        except Exception as e:
            self.msg_queue.put({"type": "update_response", 
                              "content": f"Oh no! My stardust got tangled: {str(e)}"})
        
        self.msg_queue.put({"type": "end_generation"})

    def check_queue(self):
        while not self.msg_queue.empty():
            msg = self.msg_queue.get()
            
            if msg["type"] == "start_thinking":
                # Remove any previous animation and show new one
                if self.current_thinking_anim:
                    self.current_thinking_anim.stop()
                self.current_thinking_anim = ThinkingAnimation(self.scroll_frame, mode="bouncing_hearts")
                self.current_thinking_anim.pack(fill="x", pady=8)
                self.scroll_frame._parent_canvas.yview_moveto(1.0)
                
            elif msg["type"] == "update_response":
                if hasattr(self, 'current_bubble'):
                    self.current_bubble.update_content(msg["content"])
                else:
                    # First update - replace animation with real bubble
                    if self.current_thinking_anim:
                        self.current_thinking_anim.stop()
                        self.current_thinking_anim = None
                    
                    self.current_bubble = MessageBubble(self.scroll_frame, "assistant", msg["content"])
                    self.current_bubble.pack(fill="x", pady=5)
                self.scroll_frame._parent_canvas.yview_moveto(1.0)
                
            elif msg["type"] == "play_sound":
                self.bell()
                
            elif msg["type"] == "end_generation":
                self.generating = False
                self.current_bubble = None  # reset for next message
        
        self.after(80, self.check_queue)

    def add_bubble(self, role, content):
        bubble = MessageBubble(self.scroll_frame, role, content)
        bubble.pack(fill="x", pady=5)
        self.scroll_frame._parent_canvas.yview_moveto(1.0)

    def clear_chat(self):
        self.chat_history = []
        for child in self.scroll_frame.winfo_children():
            child.destroy()
        self.save_history()
        
        # Optional: Add confetti on new chat
        # ConfettiBurst(self.scroll_frame)

    # ====================== FILE I/O ======================
    def load_history(self):
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except:
                return []
        return []

    def save_history(self):
        HISTORY_FILE.write_text(json.dumps(self.chat_history, ensure_ascii=False, indent=2))

    def load_settings(self):
        if SETTINGS_FILE.exists():
            try:
                return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except:
                return {}
        return {}

    def _load_initial_history(self):
        for msg in self.chat_history:
            self.add_bubble(msg["role"], msg["content"])


if __name__ == "__main__":
    app = SaturnApp()
    app.mainloop()