import os
import sys
import threading
from pathlib import Path
import pyttsx3 
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
try:
    from Modules.UI.UI import COLORS
except (ImportError, AttributeError):
    COLORS = {
        "accent": "#b87cff",
        "text": "#e0d0ff"
    }
    
DATA_DIR = Path.home() / "SaturnChat"
DATA_DIR.mkdir(exist_ok=True)
TTS_SETTINGS_FILE = DATA_DIR / "tts_settings.json"


class AdvancedTTS:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.current_settings = self.load_settings()
        self.apply_settings()

    def load_settings(self):
        if TTS_SETTINGS_FILE.exists():
            try:
                with open(TTS_SETTINGS_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
   
        return {
            "voice_id": 0,
            "rate": 165,   
            "volume": 0.85,
            "pitch": 50,     
            "enabled": True
        }

    def save_settings(self):
        with open(TTS_SETTINGS_FILE, "w") as f:
            json.dump(self.current_settings, f)

    def apply_settings(self):
        try:
            self.engine.setProperty('rate', self.current_settings["rate"])
            self.engine.setProperty('volume', self.current_settings["volume"])
            if self.voices:
                self.engine.setProperty('voice', self.voices[self.current_settings["voice_id"]].id)
        except:
            pass

    def speak(self, text: str):
        if not self.current_settings["enabled"] or not text.strip():
            return
        threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()

    def _speak_thread(self, text):
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except:
            pass

    def get_voice_list(self):
        return [f"{i}: {voice.name} ({voice.languages[0] if voice.languages else 'Unknown'})" 
                for i, voice in enumerate(self.voices)]


# ====================== TTS SETTINGS POPUP ======================
def open_tts_popup(parent, saturn_app):
    """Opens the advanced TTS customization window"""
    popup = ctk.CTkToplevel(parent)
    popup.title("🌙 Saturn's Voice Studio")
    popup.geometry("520x620")
    popup.grab_set()
    popup.configure(fg_color=COLORS["bg"])

    tts = AdvancedTTS()

    # Title
    ctk.CTkLabel(popup, text="✨ Saturn Voice Settings ✨", 
                 font=("Segoe UI", 20, "bold"),
                 text_color=COLORS["accent"]).pack(pady=15)

    # Voice selector
    ctk.CTkLabel(popup, text="Voice:", font=("Segoe UI", 14)).pack(anchor="w", padx=30, pady=(10,5))
    voice_var = ctk.StringVar(value=tts.get_voice_list()[tts.current_settings["voice_id"]])
    
    voice_menu = ctk.CTkOptionMenu(
        popup, 
        variable=voice_var,
        values=tts.get_voice_list(),
        width=400,
        command=lambda choice: tts.current_settings.update({"voice_id": int(choice.split(":")[0])})
    )
    voice_menu.pack(padx=30, pady=5)

    # Rate slider
    ctk.CTkLabel(popup, text=f"Speed: {tts.current_settings['rate']} wpm", 
                 font=("Segoe UI", 13)).pack(anchor="w", padx=30, pady=(20,5))
    rate_slider = ctk.CTkSlider(
        popup, from_=80, to=280, number_of_steps=40,
        command=lambda v: (rate_label.configure(text=f"Speed: {int(v)} wpm"),
                          tts.current_settings.update({"rate": int(v)}))
    )
    rate_slider.set(tts.current_settings["rate"])
    rate_slider.pack(padx=30, fill="x")

    rate_label = ctk.CTkLabel(popup, text=f"Speed: {tts.current_settings['rate']} wpm")
    rate_label.pack(anchor="w", padx=30)

    # Volume slider
    ctk.CTkLabel(popup, text=f"Volume: {int(tts.current_settings['volume']*100)}%", 
                 font=("Segoe UI", 13)).pack(anchor="w", padx=30, pady=(15,5))
    vol_slider = ctk.CTkSlider(
        popup, from_=0.1, to=1.0, number_of_steps=18,
        command=lambda v: (vol_label.configure(text=f"Volume: {int(v*100)}%"),
                          tts.current_settings.update({"volume": round(v, 2)}))
    )
    vol_slider.set(tts.current_settings["volume"])
    vol_slider.pack(padx=30, fill="x")
    vol_label = ctk.CTkLabel(popup, text=f"Volume: {int(tts.current_settings['volume']*100)}%")
    vol_label.pack(anchor="w", padx=30)

    # Test button
    def test_voice():
        test_text = "Hello! I am Saturn, your sweet cosmic friend. Do you like my voice? ✨"
        tts.apply_settings()
        tts.speak(test_text)

    ctk.CTkButton(
        popup, 
        text="🎙️ Test Voice",
        font=("Segoe UI", 14),
        height=40,
        fg_color=COLORS["accent"],
        hover_color="#9b5de5",
        command=test_voice
    ).pack(pady=25)

    # Enable/Disable toggle
    enabled_var = ctk.BooleanVar(value=tts.current_settings["enabled"])
    ctk.CTkSwitch(
        popup, 
        text="Enable TTS",
        variable=enabled_var,
        command=lambda: tts.current_settings.update({"enabled": enabled_var.get()})
    ).pack(pady=10)

    # Save & Close
    def save_and_close():
        tts.apply_settings()
        tts.save_settings()
        saturn_app.tts_var.set(tts.current_settings["enabled"])  # sync with main app
        popup.destroy()

    ctk.CTkButton(
        popup, 
        text="💾 Save & Close",
        font=("Segoe UI", 15, "bold"),
        height=45,
        fg_color="#6a1b9a",
        hover_color="#4a2e6e",
        command=save_and_close
    ).pack(pady=20, padx=80, fill="x")

    # Footer note
    ctk.CTkLabel(
        popup, 
        text="Tip: Try different voices and speeds until Saturn sounds just right~",
        font=("Segoe UI", 11),
        text_color="#888"
    ).pack(pady=10)


# ====================== EXPORT ======================
__all__ = ["AdvancedTTS", "open_tts_popup"]