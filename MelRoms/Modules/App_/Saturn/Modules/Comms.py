import customtkinter as ctk
import tkinter as tk
import threading
import ollama
import random
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Robust import for COLORS
try:
    from Modules.UI.UI import COLORS
except (ImportError, AttributeError):
    # Fallback to keep the Comms panel pretty if UI.py is busy
    COLORS = {
        "top_bg": "#1a0f2e",
        "accent": "#b87cff",
        "border": "#4a2e6e",
        "text": "#e0d0ff",
        "text_light": "#b0a0d0",
        "user_bubble": "#6a1b9a",
        "assistant_bubble": "#2a1e4b"
    }

class CommsPanel(ctk.CTkFrame):
    """
    Small compact panel that analyzes Saturn's last message and suggests cute replies.
    Improved with better text wrapping and UI scaling.
    """
    def __init__(self, parent, saturn_app):
        super().__init__(
            parent,
            width=230,   # Slightly wider for better readability
            height=160,  # Slightly taller
            fg_color=COLORS["top_bg"],
            corner_radius=16,
            border_width=2,
            border_color=COLORS["border"] # Using UI.py border color
        )
        self.saturn_app = saturn_app
        self.suggestions = []
        self.is_analyzing = False

        self.pack_propagate(False)
        self._build_ui()

    def _build_ui(self):
        # Header with a small glow effect color
        self.header = ctk.CTkLabel(
            self,
            text="📡 COSMIC COMMS",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["accent"]
        )
        self.header.pack(pady=(10, 5))

        # Scrollable area - customized to hide scrollbar until needed
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["user_bubble"],
            scrollbar_button_hover_color=COLORS["accent"],
            height=100
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Initial Status
        self.status_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Waiting for Saturn to speak...",
            font=("Segoe UI", 11, "italic"),
            text_color=COLORS["text_light"],
            wraplength=180
        )
        self.status_label.pack(pady=20)

    def analyze_last_message(self):
        """Triggered by the main app when Saturn finishes a message"""
        if self.is_analyzing:
            return

        # Check if history exists and last message is from assistant
        history = getattr(self.saturn_app, "chat_history", [])
        if not history or history[-1]["role"] != "assistant":
            return

        last_message = history[-1]["content"]
        self.is_analyzing = True
        
        # Clear UI for loading state
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        loading_text = random.choice(["Decoding stardust...", "Reading tea leaves...", "Thinking of cute things..."])
        self.status_label = ctk.CTkLabel(
            self.scroll_frame,
            text=loading_text,
            font=("Segoe UI", 11),
            text_color=COLORS["accent"]
        )
        self.status_label.pack(pady=20)

        threading.Thread(
            target=self._generate_suggestions,
            args=(last_message,),
            daemon=True
        ).start()

    def _generate_suggestions(self, last_message: str):
        try:
            # We use a very low token limit and high temp for variety
            prompt = f"Saturn said: '{last_message}'. Give me 3 ultra-short, cute, 1-sentence replies the user can say back. Use emojis. No numbers, no quotes, just the lines."

            response = ollama.chat(
                model=getattr(self.saturn_app, "model_var").get(),
                messages=[{"role": "user", "content": prompt}]
            )

            raw = response["message"]["content"].strip()
            # Split by lines and clean up any AI artifacts (like 1. or -)
            lines = [l.strip().lstrip('123456789.- ') for l in raw.split("\n") if len(l.strip()) > 2]
            
            self.suggestions = lines[:3]
            
            # Fallback if AI fails
            if not self.suggestions:
                self.suggestions = ["That's amazing! ✨", "Tell me more, Saturn! 🪐", "I love that idea! 💜"]

            self.after(0, self._display_suggestions)
        except Exception as e:
            print(f"Comms Error: {e}")
            self.after(0, self._show_error)
        finally:
            self.is_analyzing = False

    def _display_suggestions(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        for suggestion in self.suggestions:
            btn = ctk.CTkButton(
                self.scroll_frame,
                text=suggestion,
                font=("Segoe UI", 11),
                text_color=COLORS["text"],
                fg_color=COLORS["assistant_bubble"],
                hover_color=COLORS["user_bubble"],
                border_width=1,
                border_color=COLORS["border"],
                height=35,
                anchor="w", # Align text to left
                wraplength=170, # CRITICAL: This fixes the "unreadable" issue
                command=lambda s=suggestion: self._send_suggestion(s)
            )
            btn.pack(fill="x", pady=2)

        # Refresh button
        refresh = ctk.CTkButton(
            self.scroll_frame,
            text="🔄 Refresh",
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=COLORS["text_light"],
            hover_color=COLORS["top_bg"],
            height=20,
            command=self.analyze_last_message
        )
        refresh.pack(pady=(5, 0))

    def _send_suggestion(self, text: str):
        """Inject the text into the main app's entry and send it"""
        if self.saturn_app.generating:
            return
            
        # 1. Put text in the entry box
        self.saturn_app.entry.delete(0, tk.END)
        self.saturn_app.entry.insert(0, text)
        
        # 2. Trigger the send function
        self.saturn_app.send_message()

    def _show_error(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.scroll_frame, text="Comms Offline 🌌", text_color="gray").pack(pady=20)

__all__ = ["CommsPanel"]