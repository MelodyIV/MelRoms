#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import threading
import queue
import json
import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from datetime import datetime

try:
    from pedalboard import Pedalboard, Reverb, PitchShift, Delay
    from pynput import keyboard
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError as e:
    print(f"Missing dependency: {e}\nRun: pip install pedalboard pynput sounddevice soundfile numpy")
    sys.exit(1)

# ----- Miku Colors -----
BG_DARK = "#0a0e17"
FG_CYAN = "#00e5ff"
FG_PINK = "#f472b6"
BG_PANEL = "#111520"
BTN_BG = "#1e2937"
TEXT_BG = "#0f172a"
TEXT_FG = "#bae6fd"

class MikuSoundboardVoiceChanger:
    def __init__(self, root):
        self.root = root
        self.root.title("MelRoms Soundboard")
        self.root.geometry("1100x750")
        self.root.configure(bg=BG_DARK)
        
        # Audio settings
        self.CHUNK = 1024          # increased from 512 to reduce underruns
        self.SAMPLERATE = 44100
        self.mic_device = None     # will be set from dropdown
        self.output_device = None   # will be set from dropdown
        
        # Queues and state
        self.soundboard_queue = queue.Queue()
        self.voice_enabled = True
        self.pitch_shift = 0.0
        self.reverb_mix = 0.3
        self.echo_delay = 0.2
        self.echo_decay = 0.5
        self.robot_mode = False
        
        # Sound storage: name -> {'path','data','volume','hotkey'}
        self.sounds = {}
        
        # Hotkey listener
        self.listener = None
        self.running = True
        
        # Audio stream
        self.stream = None
        
        self.create_widgets()
        self.refresh_devices()
        self.setup_hotkeys()
        self.start_audio_engine()
        self.load_sounds_config()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def refresh_devices(self):
        """Populate device dropdowns. Output dropdown shows all devices (including inputs) for advanced routing."""
        devices = sd.query_devices()
        self.mic_devices = []
        self.output_devices = []
        for i, dev in enumerate(devices):
            if dev['max_input_channels'] > 0:
                self.mic_devices.append((i, dev['name']))
            # Output dropdown: any device that has output OR input (user wants to route to another mic)
            if dev['max_output_channels'] > 0 or dev['max_input_channels'] > 0:
                self.output_devices.append((i, dev['name']))
        
        self.mic_combo['values'] = [f"{i}: {name}" for i, name in self.mic_devices]
        self.out_combo['values'] = [f"{i}: {name} (IN)" if dev['max_input_channels']>0 and dev['max_output_channels']==0 else f"{i}: {name}" 
                                     for i, name in self.output_devices]
        
        if self.mic_devices:
            self.mic_combo.current(0)
            self.mic_device = self.mic_devices[0][0]
        if self.output_devices:
            # Default to first output-capable device, preferably a virtual cable
            default_out = None
            for idx, (i, name) in enumerate(self.output_devices):
                if "CABLE Input" in name:
                    default_out = idx
                    break
            if default_out is None:
                default_out = 0
            self.out_combo.current(default_out)
            self.output_device = self.output_devices[default_out][0]
                
    def on_mic_change(self, event=None):
        """User selected a new microphone."""
        sel = self.mic_combo.get()
        if sel:
            idx = int(sel.split(":")[0])
            self.mic_device = idx
            self.restart_audio()
            
    def on_output_change(self, event=None):
        """User selected a new output device."""
        sel = self.out_combo.get()
        if sel:
            idx = int(sel.split(":")[0])
            self.output_device = idx
            self.restart_audio()
            
    def restart_audio(self):
        """Restart audio stream with new devices."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.start_audio_engine()
        
    def create_widgets(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(main, text="─── MIKU SOUNDBOARD & VOICE CHANGER ───",
                font=("Courier", 12, "bold"), fg=FG_PINK, bg=BG_DARK).pack()
        
        # Device selection row
        dev_frame = tk.Frame(main, bg=BG_PANEL)
        dev_frame.pack(fill=tk.X, pady=5)

        tk.Label(dev_frame, text="Microphone (Input):", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.mic_combo = ttk.Combobox(dev_frame, state="readonly", width=30)
        self.mic_combo.pack(side=tk.LEFT, padx=5)
        self.mic_combo.bind("<<ComboboxSelected>>", self.on_mic_change)

        tk.Label(dev_frame, text="Output to (Virtual Mic):", bg=BG_PANEL, fg=FG_PINK).pack(side=tk.LEFT, padx=5)
        self.out_combo = ttk.Combobox(dev_frame, state="readonly", width=30)
        self.out_combo.pack(side=tk.LEFT, padx=5)
        self.out_combo.bind("<<ComboboxSelected>>", self.on_output_change)

        # Tooltip / hint
        info_label = tk.Label(dev_frame, text="ℹ️ Select 'CABLE Input' to send audio to VB‑Cable", 
                              bg=BG_PANEL, fg=FG_CYAN, font=("Arial", 7))
        info_label.pack(side=tk.LEFT, padx=10)
                
        # Main content
        content = tk.Frame(main, bg=BG_DARK)
        content.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # LEFT PANEL: Soundboard
        left_panel = tk.Frame(content, bg=BG_PANEL, width=500)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        left_panel.pack_propagate(False)
        tk.Label(left_panel, text="─── SOUNDBOARD ───", font=("Courier", 10, "bold"),
                fg=FG_CYAN, bg=BG_PANEL).pack(pady=5)
        
        # Sound list with scrollbar (now with two columns: name and hotkey)
        list_frame = tk.Frame(left_panel, bg=BG_PANEL)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Use Treeview for two columns
        columns = ("name", "hotkey")
        self.sound_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        self.sound_tree.heading("name", text="Sound Name")
        self.sound_tree.heading("hotkey", text="Hotkey")
        self.sound_tree.column("name", width=200)
        self.sound_tree.column("hotkey", width=80)
        self.sound_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.sound_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sound_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind double-click to play
        self.sound_tree.bind("<Double-1>", lambda e: self.play_selected_sound())
        
        # Sound control buttons
        sound_btn_frame = tk.Frame(left_panel, bg=BG_PANEL)
        sound_btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(sound_btn_frame, text="➕ Add Sound", command=self.add_sound,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(sound_btn_frame, text="❌ Remove Sound", command=self.remove_sound,
                 bg=BTN_BG, fg=FG_PINK, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(sound_btn_frame, text="🔊 Play", command=self.play_selected_sound,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(sound_btn_frame, text="⏹️ Stop All", command=self.stop_all_sounds,
                 bg=BTN_BG, fg=FG_PINK, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # Set hotkey button and entry
        hotkey_frame = tk.Frame(left_panel, bg=BG_PANEL)
        hotkey_frame.pack(fill=tk.X, pady=5)
        tk.Label(hotkey_frame, text="Hotkey for selected sound:", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.hotkey_entry = tk.Entry(hotkey_frame, width=10, bg=TEXT_BG, fg="white")
        self.hotkey_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(hotkey_frame, text="Assign", command=self.assign_hotkey_to_selected,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # RIGHT PANEL: Voice Changer
        right_panel = tk.Frame(content, bg=BG_PANEL, width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        right_panel.pack_propagate(False)
        tk.Label(right_panel, text="─── VOICE CHANGER ───", font=("Courier", 10, "bold"),
                fg=FG_CYAN, bg=BG_PANEL).pack(pady=5)
        
        self.voice_enabled_var = tk.BooleanVar(value=True)
        tk.Checkbutton(right_panel, text="Enable Voice Effects", variable=self.voice_enabled_var,
                      bg=BG_PANEL, fg=FG_CYAN, selectcolor=BG_PANEL,
                      command=self.toggle_voice).pack(pady=5)
        
        preset_frame = tk.Frame(right_panel, bg=BG_PANEL)
        preset_frame.pack(fill=tk.X, pady=5)
        tk.Label(preset_frame, text="Presets:", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        tk.Button(preset_frame, text="Robot", command=self.apply_robot_preset,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Darth Vader", command=self.apply_darth_preset,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Chipmunk", command=self.apply_chipmunk_preset,
                 bg=BTN_BG, fg=FG_CYAN, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        tk.Button(preset_frame, text="Reset", command=self.reset_effects,
                 bg=BTN_BG, fg=FG_PINK, relief=tk.FLAT).pack(side=tk.LEFT, padx=2)
        
        # Sliders
        pitch_frame = tk.Frame(right_panel, bg=BG_PANEL)
        pitch_frame.pack(fill=tk.X, pady=5)
        tk.Label(pitch_frame, text="Pitch Shift (semitones):", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.pitch_slider = tk.Scale(pitch_frame, from_=-12, to=12, orient=tk.HORIZONTAL,
                                     command=self.update_pitch, bg=BG_PANEL, fg=FG_CYAN,
                                     highlightthickness=0, length=200)
        self.pitch_slider.set(0)
        self.pitch_slider.pack(side=tk.LEFT, padx=5)
        
        reverb_frame = tk.Frame(right_panel, bg=BG_PANEL)
        reverb_frame.pack(fill=tk.X, pady=5)
        tk.Label(reverb_frame, text="Reverb Mix:", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.reverb_slider = tk.Scale(reverb_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                     command=self.update_reverb, bg=BG_PANEL, fg=FG_CYAN,
                                     highlightthickness=0, length=200)
        self.reverb_slider.set(30)
        self.reverb_slider.pack(side=tk.LEFT, padx=5)
        
        echo_frame = tk.Frame(right_panel, bg=BG_PANEL)
        echo_frame.pack(fill=tk.X, pady=5)
        tk.Label(echo_frame, text="Echo Delay (s):", bg=BG_PANEL, fg=FG_CYAN).pack(side=tk.LEFT, padx=5)
        self.echo_slider = tk.Scale(echo_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                   command=self.update_echo, bg=BG_PANEL, fg=FG_CYAN,
                                   highlightthickness=0, length=200)
        self.echo_slider.set(20)
        self.echo_slider.pack(side=tk.LEFT, padx=5)
        
        # Log area
        log_frame = tk.LabelFrame(main, text=" STATUS LOG ", font=("Arial", 8, "bold"),
                                  fg=FG_CYAN, bg=BG_PANEL)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area = tk.Text(log_frame, height=6, bg=TEXT_BG, fg=TEXT_FG,
                               font=("Consolas", 8), state=tk.DISABLED, relief=tk.FLAT)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_label = tk.Label(main, text="Ready", bg=BG_DARK, fg=FG_CYAN, anchor="w")
        self.status_label.pack(fill=tk.X, pady=5)
        
    def log(self, msg):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
        
    # --- Soundboard Methods ---
    def add_sound(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Sound Files",
            filetypes=[("Audio files", "*.wav *.mp3 *.ogg *.flac"), ("All files", "*.*")]
        )
        if not file_paths:
            return
        for path in file_paths:
            name = os.path.splitext(os.path.basename(path))[0]
            base_name = name
            counter = 1
            while name in self.sounds:
                name = f"{base_name}_{counter}"
                counter += 1
            try:
                data, samplerate = sf.read(path, dtype='float32')
                if samplerate != self.SAMPLERATE:
                    # Simple resample using scipy (optional, remove if not installed)
                    try:
                        import scipy.signal
                        data = scipy.signal.resample(data, int(len(data) * self.SAMPLERATE / samplerate))
                    except ImportError:
                        self.log("Install scipy for resampling, or use 44.1kHz files.")
                        continue
                self.sounds[name] = {
                    'path': path,
                    'data': data.flatten(),
                    'volume': 0.7,
                    'hotkey': None
                }
                self.sound_tree.insert("", tk.END, iid=name, values=(name, ""))
                self.log(f"Added sound: {name}")
            except Exception as e:
                self.log(f"Error loading {name}: {str(e)}")
        self.save_sounds_config()
        
    def remove_sound(self):
        selected = self.sound_tree.selection()
        if not selected:
            return
        name = selected[0]
        if name in self.sounds:
            del self.sounds[name]
            self.sound_tree.delete(name)
            self.log(f"Removed sound: {name}")
            self.save_sounds_config()
            
    def play_selected_sound(self):
        selected = self.sound_tree.selection()
        if not selected:
            return
        name = selected[0]
        self.play_sound(name)
        
    def play_sound(self, name):
        if name not in self.sounds:
            return
        sound = self.sounds[name]
        self.soundboard_queue.put({
            'name': name,
            'data': sound['data'],
            'volume': sound['volume']
        })
        self.log(f"Playing sound: {name}")
        
    def stop_all_sounds(self):
        while not self.soundboard_queue.empty():
            try:
                self.soundboard_queue.get_nowait()
            except queue.Empty:
                break
        self.log("Stopped all sounds")
        
    def assign_hotkey_to_selected(self):
        selected = self.sound_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a sound first.")
            return
        name = selected[0]
        hotkey_str = self.hotkey_entry.get().strip().lower()
        if not hotkey_str:
            return
        # Remove any existing mapping for this hotkey
        for s in self.sounds.values():
            if s['hotkey'] == hotkey_str:
                s['hotkey'] = None
                # Update tree display
                for item in self.sound_tree.get_children():
                    if self.sound_tree.item(item)['values'][0] == s['name']:
                        self.sound_tree.set(item, "hotkey", "")
                        break
        self.sounds[name]['hotkey'] = hotkey_str
        self.sound_tree.set(selected[0], "hotkey", hotkey_str)
        self.log(f"Assigned hotkey '{hotkey_str}' to '{name}'")
        self.hotkey_entry.delete(0, tk.END)
        self.save_sounds_config()
        
    # --- Voice Changer Methods ---
    def toggle_voice(self):
        self.voice_enabled = self.voice_enabled_var.get()
        status = "enabled" if self.voice_enabled else "disabled"
        self.log(f"Voice effects {status}")
        
    def update_pitch(self, value):
        self.pitch_shift = float(value)
        
    def update_reverb(self, value):
        self.reverb_mix = float(value) / 100.0
        
    def update_echo(self, value):
        self.echo_delay = float(value) / 100.0
        
    def apply_robot_preset(self):
        self.pitch_slider.set(-4)
        self.reverb_slider.set(20)
        self.echo_slider.set(0)
        self.robot_mode = True
        self.log("Applied Robot preset")
        
    def apply_darth_preset(self):
        self.pitch_slider.set(-8)
        self.reverb_slider.set(40)
        self.echo_slider.set(30)
        self.robot_mode = False
        self.log("Applied Darth Vader preset")
        
    def apply_chipmunk_preset(self):
        self.pitch_slider.set(8)
        self.reverb_slider.set(10)
        self.echo_slider.set(0)
        self.robot_mode = False
        self.log("Applied Chipmunk preset")
        
    def reset_effects(self):
        self.pitch_slider.set(0)
        self.reverb_slider.set(0)
        self.echo_slider.set(0)
        self.robot_mode = False
        self.log("Reset all voice effects")
        
    # --- Audio Processing ---
    def apply_voice_effects(self, audio_data):
        if not self.voice_enabled:
            return audio_data
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        effects = []
        if abs(self.pitch_shift) > 0.01:
            effects.append(PitchShift(semitones=self.pitch_shift))
        if self.reverb_mix > 0.01:
            effects.append(Reverb(room_size=0.5, wet_level=self.reverb_mix))
        if self.echo_delay > 0.01:
            effects.append(Delay(delay_seconds=self.echo_delay, feedback=self.echo_decay, mix=0.3))
        if self.robot_mode:
            audio_data = np.round(audio_data * 128) / 128
        if effects:
            board = Pedalboard(effects)
            audio_data = board.process(audio_data, sample_rate=self.SAMPLERATE)
        return audio_data
        
    # --- Audio Callback ---
    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            if not hasattr(self, '_last_status_log') or (datetime.now() - self._last_status_log).total_seconds() > 5:
                self._last_status_log = datetime.now()
                self.log(f"Audio status: {status}")
        
        # Get actual input channels
        input_channels = indata.shape[1] if len(indata.shape) > 1 else 1
        # Use first channel for processing
        if input_channels > 0:
            mic_float = indata[:, 0].astype(np.float32)
        else:
            mic_float = np.zeros(frames, dtype=np.float32)
        
        # Apply voice effects
        processed = self.apply_voice_effects(mic_float)
        
        # Mix in soundboard
        try:
            sound_item = self.soundboard_queue.get_nowait()
            sound_data = sound_item['data']
            sound_data = sound_data * sound_item['volume']
            if len(sound_data) > frames:
                sound_chunk = sound_data[:frames]
            else:
                sound_chunk = np.pad(sound_data, (0, frames - len(sound_data)))
            mixed = processed + sound_chunk
        except queue.Empty:
            mixed = processed
        
        mixed = np.clip(mixed, -1.0, 1.0)
        
        # Handle output channels
        output_channels = outdata.shape[1] if len(outdata.shape) > 1 else 1
        if output_channels == 1:
            outdata[:, 0] = mixed
        else:
            # For stereo, duplicate mono signal to both channels
            outdata[:, 0] = mixed
            outdata[:, 1] = mixed
        
    def start_audio_engine(self):
        """Open stream with selected devices, auto-detecting channel counts."""
        if self.mic_device is None or self.output_device is None:
            self.log("Please select microphone and output devices.")
            return
        
        try:
            # Get device info to determine available channels
            input_info = sd.query_devices(self.mic_device, 'input')
            output_info = sd.query_devices(self.output_device, 'output')
            
            # Get max channels (capped at 2 for safety)
            input_channels = min(input_info['max_input_channels'], 2)
            output_channels = min(output_info['max_output_channels'], 2)
            
            # If output device has no output channels (like a pure microphone input),
            # we need to use it as an input device instead (for virtual cables)
            if output_channels == 0 and input_channels > 0:
                # This device is input-only; use it as the input and route through default?
                self.log(f"Warning: {output_info['name']} is input-only. Using it as input.")
                # Fall back to default output
                self.output_device = sd.default.device[1]
                output_info = sd.query_devices(self.output_device, 'output')
                output_channels = min(output_info['max_output_channels'], 2)
            
            self.log(f"Using {input_channels} input channel(s) and {output_channels} output channel(s)")
            
            self.stream = sd.Stream(
                samplerate=self.SAMPLERATE,
                blocksize=self.CHUNK,
                device=(self.mic_device, self.output_device),
                channels=(input_channels, output_channels),  # Explicitly separate input/output channels
                dtype=np.float32,
                callback=self.audio_callback,
                latency='low'
            )
            self.stream.start()
            self.log(f"Audio engine started (mic:{self.mic_device}, out:{self.output_device})")
        except Exception as e:
            self.log(f"Failed to start audio: {str(e)}")
            messagebox.showerror("Audio Error", f"Cannot open audio device.\n{str(e)}")
            
    # --- Hotkey Listener ---
    def setup_hotkeys(self):
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.lower()
                elif hasattr(key, 'name'):
                    key_str = key.name.lower()
                else:
                    return
                # Find sound with this hotkey
                for name, data in self.sounds.items():
                    if data['hotkey'] == key_str:
                        self.play_sound(name)
                        break
            except:
                pass
        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.daemon = True
        self.listener.start()
        
    # --- Save/Load Config ---
    def save_sounds_config(self):
        config = {
            'sounds': [
                {
                    'name': name,
                    'path': sound['path'],
                    'volume': sound['volume'],
                    'hotkey': sound['hotkey']
                }
                for name, sound in self.sounds.items()
            ]
        }
        try:
            with open('soundboard_config.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.log(f"Error saving config: {str(e)}")
            
    def load_sounds_config(self):
        if not os.path.exists('soundboard_config.json'):
            return
        try:
            with open('soundboard_config.json', 'r') as f:
                config = json.load(f)
            for sound_info in config.get('sounds', []):
                name = sound_info['name']
                path = sound_info['path']
                if os.path.exists(path):
                    try:
                        data, samplerate = sf.read(path, dtype='float32')
                        if samplerate != self.SAMPLERATE:
                            try:
                                import scipy.signal
                                data = scipy.signal.resample(data, int(len(data) * self.SAMPLERATE / samplerate))
                            except ImportError:
                                continue
                        self.sounds[name] = {
                            'path': path,
                            'data': data.flatten(),
                            'volume': sound_info.get('volume', 0.7),
                            'hotkey': sound_info.get('hotkey', None)
                        }
                        hotkey_disp = sound_info.get('hotkey', '')
                        self.sound_tree.insert("", tk.END, iid=name, values=(name, hotkey_disp))
                    except Exception as e:
                        self.log(f"Error loading {name}: {str(e)}")
            self.log(f"Loaded {len(self.sounds)} sounds")
        except Exception as e:
            self.log(f"Error loading config: {str(e)}")
            
    def on_close(self):
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.listener:
            self.listener.stop()
        self.root.destroy()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = MikuSoundboardVoiceChanger(root)
    root.mainloop()