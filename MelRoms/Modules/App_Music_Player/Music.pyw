import pygame
import os
import sys
import logging
import time
import math
import random
import zipfile
import io
import array
import json
import subprocess
import pickle
import mutagen
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE
from mutagen.aiff import AIFF
from collections import defaultdict
import threading
import tkinter as tk
from tkinter import scrolledtext
from pypresence import Presence


try:
    import ctypes
    WIN_MEDIA_KEYS = True
except ImportError:
    WIN_MEDIA_KEYS = False


pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

class DiscordRPC:
    def __init__(self, client_id="1472951903636947150"): #< discord bot id
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        self.start_time = None
        self.current_song = ""
        
    def connect(self):
        try:
            from pypresence import Presence
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            print("✅ Discord connected")
            return True
        except:
            return False
    
    def update(self, song, artist, is_paused=False, position=0, duration=0):
        if not self.connected:
            return
            
        try:
            if not is_paused and (self.start_time is None or song != self.current_song):
                self.start_time = int(time.time()) - int(position)
                self.current_song = song
            
            
            if is_paused:
                details = f"⏸ {song[:128]}" if song else "Paused"
            else:
                details = f"▶ {song[:128]}" if song else "Playing"
                
            state = f"by {artist[:128]}" if artist else "MelRoms"
            
            presence = {
                "details": details,
                "state": state,
                "large_image": "melroms_logo",
                "large_text": "MelRoms Player",
                "small_image": "pause" if is_paused else "play",
                "small_text": "Paused" if is_paused else "Playing",
            }
            
            if not is_paused and self.start_time and duration > 0:
                presence["start"] = self.start_time
                presence["end"] = self.start_time + int(duration)
            
            self.rpc.update(**presence)
            
        except Exception as e:
            print(f"Discord update error: {e}")
            self.connected = False
    
    def run_loop(self):
        while True:
            if not self.connected:
                self.connect()
            time.sleep(15)

THEME = {
    "bg": (10, 10, 15),
    "sidebar": (20, 20, 30),
    "nowplaying": (176,100,250),
    "list_bg": (15, 15, 25),
    "text": (200, 200, 220),
    "text_dim": (100, 100, 120),
    "blurple": (114, 137, 218),
    "purple_dark": (48, 25, 52),
    "accent": (255, 0, 0),
    "accent_green": (10, 255, 75),
    "accent_light": (255, 100, 100),
    "border": (40, 40, 50),
    "header_bg": (30, 30, 40),
    "menu_bg": (25, 25, 35),
    "menu_hover": (200, 0, 0),
    "cmd_bg": (0, 0, 0),
    "skull": (255, 255, 255),
    "search_accent": (80, 25, 110),
    "TRUE_search_accent": (10,255,75),
    "sidebar_accent": (100, 100, 255),
    "button_gradient_start": (85, 57, 204),
    "button_gradient_end": (88, 101, 242),
    "glow": (255, 150, 150, 100)
}


class LyricsWindow:
    def __init__(self, app, tk_root):
        self.app = app
        self.tk_root = tk_root
        self.window = None
        self.text_widget = None
        self.current_line = -1
        self.lyrics = []
        self.running = False
        self.editing_mode = False
        self.edit_buffer = ""
        self.scroll_offset = 0
        self.max_visible_lines = 20
        self.last_update = 0
        self.update_interval = 0.1 
        
    def toggle(self):
        if self.window is None or not self.window.winfo_exists():
            self.open_window()
        else:
            self.close_window()
    
    def open_window(self):
      
        self.window = tk.Toplevel(self.tk_root)
        self.window.title("MelRoms - Lyrics Editor")
        self.window.geometry("600x500")
        self.window.configure(bg='#0a0a0f')
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
        
   
        self.window.attributes('-topmost', True)
        
      
        self.window.bind('<Key>', self.handle_key)
        self.window.bind('<Control-space>', lambda e: self.add_timestamp())
        self.window.bind('<Control-Return>', lambda e: self.insert_new_line())
        self.window.bind('<Control-Delete>', lambda e: self.delete_current_line())
        self.window.bind('<Control-s>', lambda e: self.save_lyrics())
        self.window.bind('<Escape>', lambda e: self.close_window())
        self.window.bind('<Up>', lambda e: self.move_up())
        self.window.bind('<Down>', lambda e: self.move_down())
        self.window.bind('<Tab>', lambda e: self.toggle_edit_mode())
        
      
        title_frame = tk.Frame(self.window, bg='#1a1a1e', height=30)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, 
                               text="🎵 Lyrics Editor", 
                               fg='#b064fa', 
                               bg='#1a1a1e',
                               font=('Courier New', 12, 'bold'))
        title_label.pack(side='left', padx=10)
        
       
        close_btn = tk.Button(title_frame, 
                              text="✕", 
                              command=self.close_window,
                              fg='#ff0000', 
                              bg='#1a1a1e',
                              font=('Courier New', 10, 'bold'),
                              bd=0, 
                              padx=10,
                              activebackground='#ff0000',
                              activeforeground='white')
        close_btn.pack(side='right')
        
     
        inst_frame = tk.Frame(self.window, bg='#1a1a1e', height=25)
        inst_frame.pack(fill='x')
        inst_frame.pack_propagate(False)
        
        inst_text = "Ctrl+Space: Add timestamp | Ctrl+Enter: New line | Ctrl+Delete: Delete | Ctrl+S: Save | Tab: Edit | ↑↓: Navigate"
        inst_label = tk.Label(inst_frame, 
                              text=inst_text,
                              fg='#646478',
                              bg='#1a1a1e',
                              font=('Courier New', 9))
        inst_label.pack(pady=2)
        
      
        self.text_widget = tk.Text(
            self.window,
            wrap='word',
            bg='#0f0f13',
            fg='#dcdce8',
            font=('Courier New', 12),
            insertbackground='#b064fa',
            bd=0,
            padx=20,
            pady=20,
            height=20
        )
        self.text_widget.pack(fill='both', expand=True)
        
        
        self.text_widget.tag_config('current', foreground='#b064fa', font=('Courier New', 12, 'bold'))
        self.text_widget.tag_config('editing', foreground='#ffff64', font=('Courier New', 12, 'bold'))
        self.text_widget.tag_config('normal', foreground='#dcdce8')
        self.text_widget.config(state='disabled')
        self.load_current_lyrics()
        self.running = True
        self.last_update = time.time()
        self.window.focus_set()
    def close_window(self):
        self.running = False
        if self.window:
            self.window.destroy()
            self.window = None
            self.text_widget = None
    def update(self):
        if not self.running or not self.window:
            return
        try:
            self.window.update()
        except:
            self.running = False
            return
        try:
            if self.app.current_track and self.lyrics:
                current_pos = self.app.current_track_position
                new_line = -1
                for i, (timestamp, _) in enumerate(self.lyrics):
                    if timestamp <= current_pos:
                        new_line = i
                    else:
                        break
                if new_line != self.current_line:
                    self.current_line = new_line
                    self.update_display()
                elif new_line >= 0 and new_line < len(self.lyrics) - 1:
                    next_timestamp = self.lyrics[new_line + 1][0]
                    time_to_next = next_timestamp - current_pos
                    if time_to_next < 0.3:
                        self.update_display()
        except Exception as e:
            print(f"Update error: {e}")
    def load_current_lyrics(self):
        if not self.app.current_track:
            self.lyrics = []
            self.update_display()
            return
        track_path = self.app.current_track
        if "::" in track_path:
            self.lyrics = []
            self.update_display()
            return
        track_filename = os.path.basename(track_path)
        player_dir = os.path.dirname(os.path.abspath(__file__))
        lyrics_folder = os.path.join(player_dir, "lyrics")
        if not os.path.exists(lyrics_folder):
            os.makedirs(lyrics_folder)
        base_name = os.path.splitext(track_filename)[0]
        lrc_path = os.path.join(lyrics_folder, base_name + ".lrc")
        if os.path.exists(lrc_path):
            self.parse_lrc_file(lrc_path)
            return
        if " - " in base_name:
            song_part = base_name.split(" - ", 1)[1]
            lrc_path = os.path.join(lyrics_folder, song_part + ".lrc")
            if os.path.exists(lrc_path):
                self.parse_lrc_file(lrc_path)
                return
        if os.path.exists(lyrics_folder):
            import fnmatch
            for file in os.listdir(lyrics_folder):
                if file.endswith(".lrc"):
                    if base_name.lower() in file.lower():
                        self.parse_lrc_file(os.path.join(lyrics_folder, file))
                        return
        
        self.lyrics = []
        self.update_display()
    
    def parse_lrc_file(self, filepath):
        self.lyrics = []
        import re
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    pattern = r'\[(\d+):(\d+\.\d+)\](.*)'
                    match = re.match(pattern, line)
                    if match:
                        minutes = int(match.group(1))
                        seconds = float(match.group(2))
                        timestamp = minutes * 60 + seconds
                        text = match.group(3).strip()
                        self.lyrics.append((timestamp, text))
            self.lyrics.sort(key=lambda x: x[0])
            print(f"✅ Loaded {len(self.lyrics)} lyrics lines")
        except Exception as e:
            print(f"Error loading LRC file: {e}")
            self.lyrics = []
        self.update_display()
    def save_lyrics(self):
        if not self.app.current_track or "::" in self.app.current_track or not self.lyrics:
            return
        track_filename = os.path.basename(self.app.current_track)
        base_name = os.path.splitext(track_filename)[0]
        player_dir = os.path.dirname(os.path.abspath(__file__))
        lyrics_folder = os.path.join(player_dir, "lyrics")
        os.makedirs(lyrics_folder, exist_ok=True)
        lrc_path = os.path.join(lyrics_folder, base_name + ".lrc")
        try:
            with open(lrc_path, 'w', encoding='utf-8') as f:
                for timestamp, text in self.lyrics:
                    minutes = int(timestamp // 60)
                    seconds = timestamp % 60
                    f.write(f"[{minutes:02d}:{seconds:05.2f}] {text}\n")
            print(f"✅ Lyrics saved to {lrc_path}")
        except Exception as e:
            print(f"❌ Error saving lyrics: {e}")
    def update_display(self):
        if not self.text_widget or not self.window:
            return
        try:
            current_scroll = None
            try:
                current_scroll = self.text_widget.yview()
            except:
                pass
            self.text_widget.config(state='normal')
            self.text_widget.delete(1.0, tk.END)
            if not self.lyrics:
                self.text_widget.insert(tk.END, "No lyrics found for this song.\n\nPress Ctrl+Space to add timestamps while playing.", 'normal')
            else:
                start_idx = max(0, self.current_line - 8)
                end_idx = min(len(self.lyrics), self.current_line + 15)
                if self.current_line == -1 and self.lyrics:
                    start_idx = 0
                    end_idx = min(len(self.lyrics), 20)
                for i in range(start_idx, end_idx):
                    timestamp, text = self.lyrics[i]
                    minutes = int(timestamp // 60)
                    seconds = timestamp % 60
                    time_str = f"[{minutes:02d}:{seconds:05.2f}]"
                    if self.editing_mode and i == self.current_line:
                        display_text = f"{time_str} {self.edit_buffer}_"
                        tag = 'editing'
                    elif i == self.current_line:
                        display_text = f"▶ {time_str} {text}"
                        tag = 'current'
                    else:
                        display_text = f"  {time_str} {text}"
                        tag = 'normal'
                    self.text_widget.insert(tk.END, display_text + "\n", tag)
            self.text_widget.config(state='disabled')
            if self.current_line >= 0:
                visible_line = self.current_line - start_idx + 1
                self.text_widget.see(f"{visible_line}.0")
            if current_scroll and not self.editing_mode and self.current_line == -1:
                try:
                    self.text_widget.yview_moveto(current_scroll[0])
                except:
                    pass
        except Exception as e:
            print(f"Display error: {e}")
    def handle_key(self, event):
        if not self.window:
            return
        if self.editing_mode:
            if event.keysym == 'Return':
                if self.current_line >= 0 and self.current_line < len(self.lyrics):
                    timestamp = self.lyrics[self.current_line][0]
                    self.lyrics[self.current_line] = (timestamp, self.edit_buffer)
                self.editing_mode = False
                self.update_display()
            elif event.keysym == 'Escape':
                self.editing_mode = False
                self.edit_buffer = ""
                self.update_display()
            elif event.keysym == 'BackSpace':
                self.edit_buffer = self.edit_buffer[:-1]
                self.update_display()
            elif event.char and event.char.isprintable():
                self.edit_buffer += event.char
                self.update_display()
    def toggle_edit_mode(self):
        if not self.window:
            return
        if not self.editing_mode and self.current_line >= 0 and self.current_line < len(self.lyrics):
            self.editing_mode = True
            self.edit_buffer = self.lyrics[self.current_line][1]
            self.update_display()
        elif self.editing_mode:
            self.editing_mode = False
            self.edit_buffer = ""
            self.update_display()
    def move_up(self):
        if self.current_line > 0:
            self.current_line -= 1
            self.update_display()
    def move_down(self):
        if self.current_line < len(self.lyrics) - 1:
            self.current_line += 1
            self.update_display()
    def add_timestamp(self):
        if not self.app.current_track:
            return
        current_pos = self.app.current_track_position
        
        if self.current_line >= 0 and self.current_line < len(self.lyrics):
            text = self.lyrics[self.current_line][1]
            self.lyrics[self.current_line] = (current_pos, text)
        else:
            self.lyrics.append((current_pos, "New lyric line"))
            self.lyrics.sort(key=lambda x: x[0])
            for i, (ts, _) in enumerate(self.lyrics):
                if ts == current_pos:
                    self.current_line = i
                    break
        self.update_display()
    def insert_new_line(self):
        if self.current_line < 0:
            self.lyrics.append((self.app.current_track_position, ""))
        else:
            new_ts = self.app.current_track_position
            self.lyrics.insert(self.current_line + 1, (new_ts, ""))
        self.lyrics.sort(key=lambda x: x[0])
        self.update_display()
    def delete_current_line(self):
        if 0 <= self.current_line < len(self.lyrics):
            del self.lyrics[self.current_line]
            if self.current_line >= len(self.lyrics):
                self.current_line = len(self.lyrics) - 1
            self.update_display()
class ClickParticle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.size = random.randint(2, 4)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0
    def draw(self, surface):
        alpha = int(255 * self.life)
        s = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))
class ASCIIClickParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.characters = ["*", "#", "@", "&"]
        self.char = random.choice(self.characters)
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-2, -0.5)
        self.life = 1.0
        self.decay = random.uniform(0.03, 0.06)
        self.color = (
            random.randint(150, 255),
            random.randint(50, 150),
            random.randint(50, 150)
        )
        self.size = random.randint(8, 12)
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay
        return self.life > 0
    def draw(self, surface):
        alpha = int(255 * self.life)
        font = pygame.font.SysFont("Courier New", self.size, bold=True)
        text = font.render(self.char, True, (*self.color, alpha))
        surface.blit(text, (int(self.x), int(self.y)), special_flags=pygame.BLEND_ALPHA_SDL2)
class ASCIISparkle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.particles = []
        self.chars = [".", ",", "'", "`"]
        self.colors = [
            (255, 255, 200),
            (200, 255, 200),
        ]
        self.max_particles = 8
        self.last_update = time.time()
        self.update_interval = 0.1

    def update(self):
        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return
        self.last_update = current_time
        if random.random() > 0.85 and len(self.particles) < self.max_particles:
            self.particles.append({
                'x': random.uniform(self.x, self.x + self.width),
                'y': random.uniform(self.y, self.y + self.height),
                'char': random.choice(self.chars),
                'life': 1.0,
                'decay': random.uniform(0.005, 0.02),
                'color': random.choice(self.colors),
                'twinkle_speed': random.uniform(0.05, 0.2)
            })
        for p in self.particles[:]:
            p['life'] -= p['decay']
            p['y'] += random.uniform(-0.2, 0.1)
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            alpha = int(255 * (0.5 + 0.5 * math.sin(time.time() * p['twinkle_speed']))) * p['life']
            font = pygame.font.SysFont("Courier New", 10)
            text = font.render(p['char'], True, (*p['color'], alpha))
            surface.blit(text, (int(p['x']), int(p['y'])), special_flags=pygame.BLEND_ALPHA_SDL2)
def generate_retro_laugh():
    sample_rate = 22050
    duration = 1.8
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        pulse = math.sin(2 * math.pi * 7 * t) 
        if pulse > 0.3:
            pitch = 120 + (math.sin(t * 15) * 40)
            val = (i % 40) * 500 * math.sin(2 * math.pi * pitch * t)
            buf[i] = int(val * pulse)
    return pygame.mixer.Sound(buffer=buf)
def generate_tv_buzz():
    sample_rate = 22050
    duration = 0.6
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [random.randint(-15000, 15000) for _ in range(n_samples)])
    return pygame.mixer.Sound(buffer=buf)
def generate_click_sound():
    sample_rate = 22050
    duration = 0.1
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / sample_rate
        freq = 1000 + (math.sin(t * 50) * 500)
        val = int(2000 * math.sin(2 * math.pi * freq * t) * (1 - t/duration))
        buf[i] = val
    return pygame.mixer.Sound(buffer=buf)
class MusicLibrary:
    def __init__(self):
        self.base_path = None
        self.artists = []
        self.track_cache = {}
        self.album_art_cache = {}
        self.metadata_cache = {}
        self.cache_file = Path.home() / ".melroms_cache.pkl"
        self.supported_extensions = {
            '.mp3', '.flac', '.m4a', '.mp4', '.ogg', '.wav', '.aiff', '.aif'
        }
        self.load_cache()
    def get_cache_key(self, path):
        try:
            if "::" in path:
                zp, inner = path.split("::")
                mtime = os.path.getmtime(zp)
                return f"{path}::{mtime}"
            else:
                mtime = os.path.getmtime(path)
                return f"{path}::{mtime}"
        except:
            return path
    def get_folder_cover(self, filepath):
        try:
            if "::" in filepath:
                return None
                
            folder = os.path.dirname(filepath)
            cover_names = ['cover.png', 'cover.jpg', 'folder.png', 'folder.jpg', 
                          'album.png', 'album.jpg', 'art.png', 'art.jpg',
                          'front.png', 'front.jpg', 'Cover.png', 'Cover.jpg',
                          'cover.PNG', 'cover.JPG', 'folder.PNG', 'folder.JPG']
            
            for name in cover_names:
                cover_path = os.path.join(folder, name)
                if os.path.exists(cover_path):
                    img = pygame.image.load(cover_path)
                    self.album_art_cache[filepath] = img
                    return img
                    
            parent_folder = os.path.basename(folder)
            for ext in ['.png', '.jpg', '.PNG', '.JPG']:
                cover_path = os.path.join(folder, parent_folder + ext)
                if os.path.exists(cover_path):
                    img = pygame.image.load(cover_path)
                    self.album_art_cache[filepath] = img
                    return img
        except Exception as e:
            logging.warning(f"Could not load folder cover for {filepath}: {e}")
        return None
    def get_file_metadata(self, filepath):
        cache_key = self.get_cache_key(filepath)
        if cache_key in self.metadata_cache:
            return self.metadata_cache[cache_key]
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'duration': 0,
            'raw_duration': 0,
            'bitrate': 0,
            'sample_rate': 0
        }
        try:
            if "::" in filepath:
                zp, inner = filepath.split("::")
                with zipfile.ZipFile(zp, 'r') as z:
                    with z.open(inner) as f:
                        audio_data = f.read()
                        metadata['duration'] = "??:??"
                        metadata['raw_duration'] = 180
            else:
                ext = os.path.splitext(filepath)[1].lower()
                
                if ext == '.mp3':
                    audio = MP3(filepath)
                    metadata['raw_duration'] = audio.info.length
                    metadata['bitrate'] = audio.info.bitrate
                    metadata['sample_rate'] = audio.info.sample_rate
                    
                    if 'TIT2' in audio.tags:
                        metadata['title'] = str(audio.tags['TIT2'])
                    if 'TPE1' in audio.tags:
                        metadata['artist'] = str(audio.tags['TPE1'])
                    if 'TALB' in audio.tags:
                        metadata['album'] = str(audio.tags['TALB'])
                elif ext == '.flac':
                    audio = FLAC(filepath)
                    metadata['raw_duration'] = audio.info.length
                    metadata['sample_rate'] = audio.info.sample_rate
                    if 'title' in audio.tags:
                        metadata['title'] = audio.tags['title'][0]
                    if 'artist' in audio.tags:
                        metadata['artist'] = audio.tags['artist'][0]
                    if 'album' in audio.tags:
                        metadata['album'] = audio.tags['album'][0]
                elif ext in ['.m4a', '.mp4']:
                    try:
                        audio = MP4(filepath)
                        metadata['raw_duration'] = audio.info.length
                        metadata['bitrate'] = audio.info.bitrate
                        metadata['sample_rate'] = audio.info.sample_rate
                        if '\xa9nam' in audio.tags:
                            metadata['title'] = audio.tags['\xa9nam'][0]
                        if '\xa9ART' in audio.tags:
                            metadata['artist'] = audio.tags['\xa9ART'][0]
                        if '\xa9alb' in audio.tags:
                            metadata['album'] = audio.tags['\xa9alb'][0]
                    except Exception as e:
                        logging.warning(f"Error reading M4A metadata for {filepath}: {e}")
                elif ext == '.ogg':
                    audio = OggVorbis(filepath)
                    metadata['raw_duration'] = audio.info.length
                    if 'title' in audio.tags:
                        metadata['title'] = audio.tags['title'][0]
                    if 'artist' in audio.tags:
                        metadata['artist'] = audio.tags['artist'][0]
                    if 'album' in audio.tags:
                        metadata['album'] = audio.tags['album'][0]
                elif ext in ['.wav', '.aiff', '.aif']:
                    audio = WAVE(filepath) if ext == '.wav' else AIFF(filepath)
                    metadata['raw_duration'] = audio.info.length
                    metadata['sample_rate'] = audio.info.sample_rate
                if metadata['raw_duration'] > 0:
                    minutes = int(metadata['raw_duration'] // 60)
                    seconds = int(metadata['raw_duration'] % 60)
                    metadata['duration'] = f"{minutes:02d}:{seconds:02d}"
                else:
                    metadata['duration'] = "??:??"
        except Exception as e:
            logging.error(f"Error reading metadata from {filepath}: {e}")
            metadata['duration'] = "??:??"
            metadata['raw_duration'] = 0
        if not metadata['title']:
            metadata['title'] = os.path.splitext(os.path.basename(filepath.split("::")[-1]))[0]
        if not metadata['artist']:
            metadata['artist'] = "Unknown Artist"
        if not metadata['album']:
            metadata['album'] = "Unknown Album"
        self.metadata_cache[cache_key] = metadata
        return metadata
    def get_album_art(self, filepath):
        if filepath in self.album_art_cache:
            return self.album_art_cache[filepath]
        folder_cover = self.get_folder_cover(filepath)
        if folder_cover:
            return folder_cover
        try:
            if "::" in filepath:
                return None
            ext = os.path.splitext(filepath)[1].lower()
            if ext == '.mp3':
                audio = MP3(filepath)
                for tag in audio.tags.values():
                    if hasattr(tag, 'FrameID') and tag.FrameID == 'APIC':
                        img_data = tag.data
                        img = pygame.image.load(io.BytesIO(img_data))
                        self.album_art_cache[filepath] = img
                        return img
                    if hasattr(tag, 'desc') and 'cover' in tag.desc.lower():
                        img_data = tag.data
                        img = pygame.image.load(io.BytesIO(img_data))
                        self.album_art_cache[filepath] = img
                        return img
            elif ext == '.flac':
                audio = FLAC(filepath)
                if audio.pictures:
                    img_data = audio.pictures[0].data
                    img = pygame.image.load(io.BytesIO(img_data))
                    self.album_art_cache[filepath] = img
                    return img
            elif ext in ['.m4a', '.mp4']:
                try:
                    audio = MP4(filepath)
                    if 'covr' in audio:
                        img_data = audio['covr'][0]
                        if isinstance(img_data, bytes):
                            img = pygame.image.load(io.BytesIO(img_data))
                            self.album_art_cache[filepath] = img
                            return img
                    if '©art' in audio:
                        img_data = audio['©art'][0]
                        if isinstance(img_data, bytes):
                            img = pygame.image.load(io.BytesIO(img_data))
                            self.album_art_cache[filepath] = img
                            return img
                except Exception as e:
                    logging.warning(f"Error reading M4A album art for {filepath}: {e}")
            elif ext == '.ogg':
                try:
                    audio = OggVorbis(filepath)
                    if 'metadata_block_picture' in audio:
                        import base64
                        img_data = base64.b64decode(audio['metadata_block_picture'][0])
                        try:
                            img = pygame.image.load(io.BytesIO(img_data))
                            self.album_art_cache[filepath] = img
                            return img
                        except:
                            pass
                except Exception as e:
                    logging.warning(f"Error reading OGG album art for {filepath}: {e}")
        except Exception as e:
            logging.warning(f"Could not extract album art from {filepath}: {e}")
        return None
    def scan_directory(self, directory):
        audio_files = []
        total_files = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.lower().endswith(tuple(self.supported_extensions)):
                    total_files += 1
        logging.info(f"Found {total_files} audio files to scan")
        processed = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for file in files:
                if file.lower().endswith(tuple(self.supported_extensions)):
                    full_path = os.path.join(root, file)
                    try:
                        size = os.path.getsize(full_path)
                        if size > 0:
                            audio_files.append({
                                'name': file,
                                'path': full_path,
                                'size': size,
                                'type': 'file'
                            })
                    except:
                        continue
                    processed += 1
                    if processed % 500 == 0:
                        logging.info(f"Scanning progress: {processed}/{total_files}")
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.zip'):
                    try:
                        zip_path = os.path.join(root, file)
                        with zipfile.ZipFile(zip_path, 'r') as z:
                            for file_info in z.infolist():
                                if file_info.filename.lower().endswith(tuple(self.supported_extensions)):
                                    audio_files.append({
                                        'name': os.path.basename(file_info.filename),
                                        'path': f"{zip_path}::{file_info.filename}",
                                        'size': file_info.file_size,
                                        'type': 'zip'
                                    })
                    except:
                        continue
        logging.info(f"Scan complete: {len(audio_files)} total audio files found")
        return audio_files
    def organize_by_artist(self, files):
        artists_dict = {}
        for file_info in files:
            path = file_info['path']
            if self.base_path:
                rel_path = os.path.relpath(path, self.base_path)
                artist_name = rel_path.split(os.sep)[0]
            else:
                artist_name = "Unknown Artist"
            if artist_name == '.' or artist_name == '..':
                continue
            if artist_name not in artists_dict:
                artists_dict[artist_name] = {
                    'name': artist_name,
                    'tracks': []
                }
            artists_dict[artist_name]['tracks'].append({
                'path': path,
                'name': file_info['name'],
                'size': file_info['size'],
                'title': None,
                'artist': artist_name,
                'album': None,
                'duration': "??:??",
                'raw_duration': 0
            })
        artists_list = []
        for artist_name, artist_data in artists_dict.items():
            artists_list.append({
                'name': artist_name,
                'tracks': artist_data['tracks']
            })
        artists_list.sort(key=lambda x: x['name'].lower())
        return artists_list
    def get_file_size(self, path):
        try:
            if "::" in path:
                zp, inner = path.split("::")
                with zipfile.ZipFile(zp, 'r') as z:
                    return z.getinfo(inner).file_size
            else:
                return os.path.getsize(path)
        except:
            return 0
    def get_files_in_artist(self, artist_path):
        for i, artist in enumerate(self.artists):
            if i == artist_path:
                if i not in self.track_cache:
                    if 'tracks' in artist:
                        self.track_cache[i] = artist['tracks']
                    else:
                        tracks = []
                        for album_name, track_paths in artist.get('albums', {}).items():
                            for track in track_paths:
                                if isinstance(track, dict):
                                    tracks.append(track)
                                else:
                                    tracks.append({
                                        'path': track,
                                        'name': os.path.basename(track.split("::")[-1]),
                                        'size': self.get_file_size(track),
                                        'title': None,
                                        'artist': artist['name'],
                                        'album': album_name,
                                        'duration': "??:??",
                                        'raw_duration': 0
                                    })
                        self.track_cache[i] = tracks
                return self.track_cache[i]
        return []
    def lazy_load_metadata(self, track):
        if track['title'] is None:
            metadata = self.get_file_metadata(track['path'])
            track['title'] = metadata['title']
            track['artist'] = metadata['artist']
            track['album'] = metadata['album']
            track['duration'] = metadata['duration']
            track['raw_duration'] = metadata['raw_duration']
        return track
    
    def select_and_update_path(self):
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw()
        
        folder = filedialog.askdirectory(title="Select Music Library Folder")
        root.destroy()
        
        if folder:
            self.base_path = folder
            logging.info(f"Selected library path: {folder}")
            
            self.artists = []
            self.track_cache.clear()
            self.metadata_cache.clear()
            
            files = self.scan_directory(folder)
            self.artists = self.organize_by_artist(files)
            
            self.save_cache()
            
            return True
        return False
    
    def search(self, query):
        if not query or len(query) < 2:
            return []
        
        query = query.lower()
        results = []
        
        for artist in self.artists:
            if 'tracks' in artist:
                for track in artist['tracks']:
                    if query in track['name'].lower():
                        results.append({
                            'path': track['path'],
                            'name': track['name'],
                            'size': track.get('size', self.get_file_size(track['path'])),
                            'title': None,
                            'artist': artist['name'],
                            'album': None,
                            'duration': "??:??",
                            'raw_duration': 0
                        })
    
        return results
    
    def load_cache(self):
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    
                    self.base_path = cache_data.get('base_path')
                    self.artists = cache_data.get('artists', [])
                    self.metadata_cache = cache_data.get('metadata_cache', {})
                    
                    logging.info(f"Loaded cache: {len(self.artists)} artists, {len(self.metadata_cache)} metadata entries")
                    
                    if self.base_path and not os.path.exists(self.base_path):
                        logging.warning(f"Cache path {self.base_path} no longer exists, clearing cache")
                        self.base_path = None
                        self.artists = []
                        self.metadata_cache = {}
                    else:
                        return True
        except Exception as e:
            logging.error(f"Error loading cache: {e}")
        
        return False
    
    def save_cache(self):
        try:
            cache_data = {
                'base_path': self.base_path,
                'artists': self.artists,
                'metadata_cache': self.metadata_cache
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logging.info(f"Saved cache: {len(self.artists)} artists, {len(self.metadata_cache)} metadata entries")
            return True
        except Exception as e:
            logging.error(f"Error saving cache: {e}")
            return False

class LoadingState:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Courier New", 12, bold=True)
        self.small_font = pygame.font.SysFont("Courier New", 10)
        self.start_time = time.time()
        self.laugh_sound = generate_retro_laugh()
        self.buzz_sound = generate_tv_buzz()
        self.played_laugh = False
        self.played_buzz = False
        self.last_search_time = 0
        self.pending_search = None
        
        self.skull_top = [
            r"                 ___-----------___  ",
            r"           __--~~                 ~~--__  ",
            r"       _-~~                             ~~-_  ",
            r"    _-~                                     ~-_  ",
            r"   /                                           \  ",
            r"  |                                             |  ",
            r" |                                               |  ",
            r" |                                               |  ",
            r"|                                                 |  ",
            r"|                                                 |  ",
            r"|                                                 |  ",
            r" |                                               |  ",
            r" |  |    _-------_               _-------_    |  |  ",
            r" |  |  /~         ~\           /~         ~\  |  |  ",
            r"  ||  |             |         |             |  ||  ",
            r"  || |               |       |               | ||  ",
            r"  || |              |         |              | ||  ",
            r"  |   \_           /           \           _/   |  ",
            r" |      ~~--_____-~    /~V~\    ~-_____--~~      |  ",
            r" |                    |     |                    |  ",
            r"|                    |       |                    |  ",
            r"|                    |  /^\  |                    |  ",
            r" |                    ~~   ~~                    |  ",
            r"  \_         _                       _         _/  ",
            r"    ~--____-~ ~\                   /~ ~-____--~  ",
            r"         \     /\                 /\     /  ",
            r"          \    | ( ,           , ) |    /  ",
            r"           |   | (~(__(  |  )__)~) |   |  "
        ]
        
        self.skull_jaw = [
            r"            |   \/ (  (~~|~~)  ) \/   |  ",
            r"             |   |  [ [  |  ] ]  /   |  ",
            r"              |                     |  ",
            r"               \                   /  ",
            r"                ~-_             _-~  ",
            r"                   ~--___-___--~  "
        ]

        self.mini_melroms = [
            r"  __  __      _ ____                    ",
            r" |  \/  | ___| |  _ \ ___  _ __ ___  ___  ",
            r" | |\/| |/ _ \ | |_) / _ \| '_ ` _ \/ __| ",
            r" | |  | |  __/ |  _ < (_) | | | | | \__ \ ",
            r" |_|  |_|\___|_|_| \_\___/|_| |_| |_|___/ "
        ]
        self.planets = [{'x': random.randint(0, 400), 'y': random.randint(20, 280), 
                         'size': random.randint(2, 6), 'speed': random.uniform(0.5, 2.0)} for _ in range(8)]

    def draw(self):
        now = time.time()
        elapsed = now - self.start_time
        w, h = self.screen.get_size()
        cmd_w, cmd_h = 440, 340
        cmd_rect = pygame.Rect((w-cmd_w)//2, (h-cmd_h)//2, cmd_w, cmd_h)

        pygame.draw.rect(self.screen, THEME["cmd_bg"], cmd_rect)
        pygame.draw.rect(self.screen, THEME["accent"], cmd_rect, 1)

        if elapsed < 2.5:
            if elapsed > 0.1 and not self.played_laugh: 
                self.laugh_sound.play()
                self.played_laugh = True
            
            skull_font = pygame.font.SysFont("Courier New", 7, bold=True)
            skull_lines = self.skull_top + self.skull_jaw
            
            line_height = 8
            total_skull_height = len(skull_lines) * line_height
            available_height = cmd_h - 60
            skull_start_y = cmd_rect.y + max(10, (available_height - total_skull_height) // 2)
            
            for i, line in enumerate(skull_lines):
                jitter = random.randint(-1, 1) if random.random() > 0.9 else 0
                color = THEME["accent"] if random.random() > 0.97 else THEME["skull"]
                
                txt = skull_font.render(line, True, color)
                pos_x = cmd_rect.centerx - txt.get_width()//2 + jitter
                pos_y = skull_start_y + (i * line_height)
                
                self.screen.blit(txt, (pos_x, pos_y))
            
            jaw_offset = math.sin(elapsed * 22) * 1.5 + 0.5
            
            for i, line in enumerate(self.skull_jaw):
                color = THEME["accent"] if random.random() > 0.97 else THEME["skull"]
                txt = skull_font.render(line, True, color)
                
                pos_x = cmd_rect.centerx - txt.get_width()//2
                pos_y = skull_start_y + (len(self.skull_top) * line_height) + (i * line_height) + jaw_offset
                
                self.screen.blit(txt, (pos_x, pos_y))

            status = "ACCESSING_CORE_OS..." if int(elapsed*10)%2==0 else ">> ERROR: UNKNOWN_NODE"
            st_txt = self.small_font.render(status, True, THEME["accent"])
            self.screen.blit(st_txt, (cmd_rect.x + 10, cmd_rect.bottom - 25))
            
            title = self.font.render(" MELROMS_INIT.EXE ", True, THEME["cmd_bg"], THEME["accent"])
            self.screen.blit(title, (cmd_rect.x + 10, cmd_rect.y - 10))
            
        elif elapsed < 3.0:
            if not self.played_buzz: 
                self.laugh_sound.stop()
                self.buzz_sound.play()
                self.played_buzz = True
            for _ in range(30):
                rw, rh = random.randint(40, 300), random.randint(1, 5)
                rx, ry = random.randint(cmd_rect.x, cmd_rect.right-rw), random.randint(cmd_rect.y, cmd_rect.bottom-rh)
                pygame.draw.rect(self.screen, THEME["accent"], (rx, ry, rw, rh))
                
        elif elapsed < 5.5:
            for p in self.planets:
                p['x'] = (p['x'] - p['speed']) % cmd_w
                px, py = cmd_rect.x + p['x'], cmd_rect.y + p['y']
                pygame.draw.circle(self.screen, (60, 60, 80), (int(px), int(py)), p['size'])
            
            for i, line in enumerate(self.mini_melroms):
                txt = self.font.render(line, True, (255, 255, 255))
                self.screen.blit(txt, (cmd_rect.centerx - txt.get_width()//2, cmd_rect.centery - 30 + i*16))
            
            progress = (elapsed - 3.0) / 2.5
            p_rect = pygame.Rect(cmd_rect.x + 50, cmd_rect.bottom - 50, cmd_w - 100, 6)
            pygame.draw.rect(self.screen, (30, 30, 40), p_rect)
            pygame.draw.rect(self.screen, THEME["accent"], (p_rect.x, p_rect.y, int(p_rect.width*progress), p_rect.height))
        else: 
            return False
        return True

class WatchdogsVisualizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont("Courier New", 24, bold=True)
        self.small_font = pygame.font.SysFont("Courier New", 12)
        self.ascii_font = pygame.font.SysFont("Courier New", 16, bold=True)
        self.auto_cycle = True
        self.auto_cycle_speed = 10.0
        self.auto_cycle_timer = 1
        self.last_cycle_time = time.time()
        
        self.ascii_variants = [
            [
                r"███╗   ███╗███████╗██╗     ██████╗  ██████╗ ███╗   ███╗███████╗",
                r"████╗ ████║██╔════╝██║     ██╔══██╗██╔═══██╗████╗ ████║██╔════╝",
                r"██╔████╔██║█████╗  ██║     ██████╔╝██║   ██║██╔████╔██║███████╗",
                r"██║╚██╔╝██║██╔══╝  ██║     ██╔══██╗██║   ██║██║╚██╔╝██║╚════██║",
                r"██║ ╚═╝ ██║███████╗███████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║███████║",
                r"╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝"
            ],
            [
                r"  __  ___      __  ____                        ",
                r" /  |/  /__  / / / __ \ ____  __ _   ___       ",
                r" / /|_/ / _ \/ / / /_/ // __ \/  ' \ (_-<       ",
                r"/_/  /_/\___/_/ /_/ \_\\____/_/_/_//___/        "
            ],
            [
                r"M   M EEEEE L   RRRR   OOO  M   M  SSS ",
                r"MM MM E     L   R   R O   O MM MM S    ",
                r"M M M EEEEE L   RRRR  O   O M M M  SSS ",
                r"M   M E     L   R R   O   O M   M      S",
                r"M   M EEEEE LLLLL R   R OOO  M   M  SSS "
            ],
            [
                r" __  __  ____  _      ____    ____    __  __  ____ ",
                r"|  \/  || ___|| |     |  _ \  / __ \ |  \/  |/ ___|",
                r"| \  / ||  _| | |     | |_) | |  | || \  / |\\___ \\",
                r"| |\/| || |__ | |___  |  _ <  |  | || |\/| | ___) |",
                r"|_|  |_||____||_____||_| \_\ \____/ |_|  |_||____/ "
            ],
            [
                r"   __  ___    __    ____                  ",
                r"  /  |/  /__ / /   / __ \ ___  __ _  ___",
                r" / /|_/ / -_) /   / /_/ // _ \/  ' \(_-<",
                r"/_/  /_/\__/_/   /_/ \_\\___/_/_/_/___/"
            ],
            [
                r"  __  __      _ ____                    ",
                r" |  \/  | ___| |  _ \ ___  _ __ ___  ___  ",
                r" | |\/| |/ _ \ | |_) / _ \| '_ ` _ \/ __| ",
                r" | |  | |  __/ |  _ < (_) | | | | | \__ \ ",
                r" |_|  |_|\___|_|_| \_\___/|_| |_| |_|___/ "
            ],
            [
                r"███╗   ███╗███████╗██╗     ██████╗  ██████╗ ███╗   ███╗███████╗",
                r"████╗ ████║██╔════╝██║     ██╔══██╗██╔═══██╗████╗ ████║██╔════╝",
                r"██╔████╔██║█████╗  ██║     ██████╔╝██║   ██║██╔████╔██║███████╗",
                r"██║╚██╔╝██║██╔══╝  ██║     ██╔══██╗██║   ██║██║╚██╔╝██║╚════██║",
                r"██║ ╚═╝ ██║███████╗███████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║███████║",
                r"╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝"
            ],
            [
                r"M   M EEEEE L   RRRR   OOO  M   M  SSS ",
                r"MM MM E     L   R   R O   O MM MM S    ",
                r"M M M EEEEE L   RRRR  O   O M M M  SSS ",
                r"M   M E     L   R R   O   O M   M      S",
                r"M   M EEEEE LLLLL R   R OOO  M   M  SSS "
            ],
            [
                r" __  __  ____  _      ____    ____    __  __  ____ ",
                r"|  \/  || ___|| |     |  _ \  / __ \ |  \/  |/ ___|",
                r"| \  / ||  _| | |     | |_) | |  | || \  / |\\___ \\",
                r"| |\/| || |__ | |___  |  _ <  |  | || |\/| | ___) |",
                r"|_|  |_||____||_____||_| \_\ \____/ |_|  |_||____/ "
            ],
            [
                r"   __  ___    __    ____                  ",
                r"  /  |/  /__ / /   / __ \ ___  __ _  ___",
                r" / /|_/ / -_) /   / /_/ // _ \/  ' \(_-<",
                r"/_/  /_/\__/_/   /_/ \_\\___/_/_/_/___/"
            ],
            [
                r"  __  __      _ ____                    ",
                r" |  \/  | ___| |  _ \ ___  _ __ ___  ___  ",
                r" | |\/| |/ _ \ | |_) / _ \| '_ ` _ \/ __| ",
                r" | |  | |  __/ |  _ < (_) | | | | | \__ \ ",
                r" |_|  |_|\___|_|_| \_\___/|_| |_| |_|___/ "
            ],
            [
                r"███╗   ███╗███████╗██╗     ██████╗  ██████╗ ███╗   ███╗███████╗",
                r"████╗ ████║██╔════╝██║     ██╔══██╗██╔═══██╗████╗ ████║██╔════╝",
                r"██╔████╔██║█████╗  ██║     ██████╔╝██║   ██║██╔████╔██║███████╗",
                r"██║╚██╔╝██║██╔══╝  ██║     ██╔══██╗██║   ██║██║╚██╔╝██║╚════██║",
                r"██║ ╚═╝ ██║███████╗███████╗██║  ██║╚██████╔╝██║ ╚═╝ ██║███████║",
                r"╚═╝     ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝"
            ],
            [
                r"M   M EEEEE L   RRRR   OOO  M   M  SSS ",
                r"MM MM E     L   R   R O   O MM MM S    ",
                r"M M M EEEEE L   RRRR  O   O M M M  SSS ",
                r"M   M E     L   R R   O   O M   M      S",
                r"M   M EEEEE LLLLL R   R OOO  M   M  SSS "
            ],
            [
                r" __  __  ____  _      ____    ____    __  __  ____ ",
                r"|  \/  || ___|| |     |  _ \  / __ \ |  \/  |/ ___|",
                r"| \  / ||  _| | |     | |_) | |  | || \  / |\\___ \\",
                r"| |\/| || |__ | |___  |  _ <  |  | || |\/| | ___) |",
                r"|_|  |_||____||_____||_| \_\ \____/ |_|  |_||____/ "
            ],
            [
                r"   __  ___    __    ____                  ",
                r"  /  |/  /__ / /   / __ \ ___  __ _  ___",
                r" / /|_/ / -_) /   / /_/ // _ \/  ' \(_-<",
                r"/_/  /_/\__/_/   /_/ \_\\___/_/_/_/___/"
            ]
        ]
        
        self.particles = []
        self.flames = []
        self.matrix_drops = []
        self.comets = []
        self.explosions = []
        self.rainbow_particles = []
        self.plasma_particles = []
        self.sparkles = []
        self.lightning = []
        self.starfield = []
        self.vortex = []
        self.supernova = []
        self.glitch_offset = 0
        self.dna_strands = []
        self.meteors = []
        
        self.last_variant = -1
        self.current_variant = 0
        self.click_sound = generate_click_sound()
        self.time = 0
        
        self.moon_arc = [
            r"                 .--------------.",
            r"             .---'  o         .    `---.",
            r"          .-'    .    O  .           .    `-.",
            r"       .-'      @@@@@@        .             `-.",
            r"     .'@@  @@@@@@@@@@@       @@@@@@@   .      `.",
            r"   .'@@@ @@@@@@@@@@@@@@     @@@@@@@@@           `.",
            r"  /@@@  o @@@@@@@@@@@@@@     @@@@@@@@@      O     \ ",
            r" /           @@@@@@@@@@@@@@  @   @@@@@@@@@ @@        .  \ "
        ]
        
        self.buffer = None
        self.buffer_dirty = True
        self.mouse_pos = (0, 0)
        
    def update_auto_cycle(self):
        if self.auto_cycle:
            current_time = time.time()
            if current_time - self.last_cycle_time > self.auto_cycle_speed:
                self.cycle_variant(clicked=False)
                self.last_cycle_time = current_time

    def _reset_particles(self):
        self.particles = []
        self.flames = []
        self.matrix_drops = []
        self.comets = []
        self.explosions = []
        self.rainbow_particles = []
        self.plasma_particles = []
        self.sparkles = []
        self.lightning = []
        self.starfield = []
        self.vortex = []
        self.supernova = []
        self.dna_strands = []
        self.meteors = []
        self.buffer_dirty = True

    def cycle_variant(self, clicked=False):
        self.current_variant = (self.current_variant + 1) % len(self.ascii_variants)
        if clicked:
            self.click_sound.play()
        self._reset_particles()
        if clicked:
            self.last_cycle_time = time.time()
            
    def draw(self, surface, rect):
        if self.buffer is None or self.buffer.get_size() != (rect.width, rect.height):
            self.buffer = pygame.Surface((rect.width, rect.height))
            self.buffer_dirty = True
        
        if self.buffer_dirty:
            self.buffer.fill((5, 5, 8))
            self.time += 0.016
            
            variant_idx = self.current_variant
            
            if variant_idx != self.last_variant:
                self._reset_particles()
                self.last_variant = variant_idx

            current_ascii = self.ascii_variants[variant_idx]

            if variant_idx == 0:
                if len(self.particles) < 100:
                    self.particles.append({'x': random.randint(0, rect.width), 'y': random.randint(0, rect.height), 's': random.uniform(1, 3)})
                for p in self.particles:
                    p['x'] -= p['s']
                    if p['x'] < 0: p['x'] = rect.width
                    size = int(p['s'])
                    pygame.draw.circle(self.buffer, (255, 0, 0), (int(p['x']), int(p['y'])), size)

            elif variant_idx == 1:
                if len(self.particles) < 120:
                    self.particles.append({'x': random.randint(0, rect.width), 'y': random.randint(-50, 0), 's': random.uniform(0.5, 2)})
                for p in self.particles:
                    p['y'] += p['s']
                    p['x'] += p['s'] * 0.3
                    if p['y'] > rect.height: 
                        p['y'] = 0
                        p['x'] = random.randint(-50, rect.width)
                    pygame.draw.circle(self.buffer, (255, 255, 255), (int(p['x']), int(p['y'])), 1)

            elif variant_idx == 2:
                for _ in range(5):
                    self.flames.append({
                        'x': random.randint(0, rect.width),
                        'y': rect.height,
                        'life': 1.0,
                        'v': random.uniform(1, 3)
                    })
                for f in self.flames[:]:
                    f['y'] -= f['v']
                    f['life'] -= 0.02
                    if f['life'] <= 0:
                        self.flames.remove(f)
                        continue
                    r = int(255 * f['life'])
                    g = int(150 * f['life'])
                    b = int(50 * f['life'])
                    size = int(15 * f['life'])
                    pygame.draw.circle(self.buffer, (r, g, b), (int(f['x']), int(f['y'])), size)

            elif variant_idx == 3:
                if len(self.matrix_drops) < 40:
                    self.matrix_drops.append({'x': random.randint(0, rect.width), 'y': random.randint(0, rect.height), 'v': random.uniform(2, 5)})
                for d in self.matrix_drops:
                    d['y'] += d['v']
                    if d['y'] > rect.height: d['y'] = 0
                    char = random.choice("01$#@!%&*")
                    txt = self.small_font.render(char, True, (0, 255, 0))
                    self.buffer.blit(txt, (d['x'], d['y']))

            elif variant_idx == 4:
                moon_color = (40, 60, 120)
                for i, line in enumerate(self.moon_arc):
                    line_surf = self.small_font.render(line, True, moon_color)
                    self.buffer.blit(line_surf, (rect.width - 450, rect.height - 120 + (i * 12)))
                
                if random.random() > 0.94:
                    self.comets.append({
                        'x': random.randint(0, rect.width // 2),
                        'y': -20,
                        'vx': random.uniform(5, 9),
                        'vy': random.uniform(3, 6),
                        'trail': []
                    })
                    
                for c in self.comets[:]:
                    c['x'] += c['vx']
                    c['y'] += c['vy']
                    c['trail'].append({'x': c['x'], 'y': c['y'], 'life': 1.0})
                    if len(c['trail']) > 15: c['trail'].pop(0)

                    for t in c['trail']:
                        t['life'] -= 0.05
                        if t['life'] > 0:
                            size = int(8 * t['life'])
                            color = (0, 100 + int(100*t['life']), 255)
                            pygame.draw.circle(self.buffer, color, (int(t['x']), int(t['y'])), size)

                    core_size = random.randint(6, 10)
                    pygame.draw.circle(self.buffer, (200, 230, 255), (int(c['x']), int(c['y'])), core_size)
                    pygame.draw.circle(self.buffer, (0, 150, 255), (int(c['x']), int(c['y'])), core_size + 4, 2)
                    
                    if c['y'] > rect.height - 60 and c['x'] > rect.width - 400:
                        for _ in range(12):
                            self.explosions.append({
                                'x': c['x'], 'y': c['y'],
                                'vx': random.uniform(-4, 4), 'vy': random.uniform(-4, 4),
                                'life': 1.0, 'color': (100, 200, 255)
                            })
                        self.comets.remove(c)
                    elif c['y'] > rect.height + 50 or c['x'] > rect.width + 50:
                        self.comets.remove(c)

                for e in self.explosions[:]:
                    e['x'] += e['vx']
                    e['y'] += e['vy']
                    e['life'] -= 0.04
                    if e['life'] <= 0: self.explosions.remove(e)
                    else:
                        char = random.choice(["#", " ", "*", "@"])
                        exp_surf = self.small_font.render(char, True, e['color'])
                        self.buffer.blit(exp_surf, (int(e['x']), int(e['y'])))

            elif variant_idx == 5:
                center_x, center_y = rect.width // 2, rect.height // 2
                if len(self.rainbow_particles) < 80:
                    angle = random.uniform(0, math.pi * 2)
                    min_radius = min(rect.width, rect.height) * 0.35
                    max_radius = min(rect.width, rect.height) * 0.48
                    radius = random.uniform(min_radius, max_radius)
                    self.rainbow_particles.append({
                        'angle': angle,
                        'radius': radius,
                        'speed': random.uniform(0.01, 0.03),
                        'radius_speed': random.uniform(-0.3, 0.3),
                        'color': (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)),
                        'size': random.randint(2, 5)
                    })
                
                for p in self.rainbow_particles[:]:
                    p['angle'] += p['speed']
                    p['radius'] += p['radius_speed']
                    
                    min_radius = min(rect.width, rect.height) * 0.35
                    max_radius = min(rect.width, rect.height) * 0.55
                    
                    if p['radius'] < min_radius:
                        p['radius'] = max_radius
                        p['radius_speed'] = random.uniform(-0.3, 0.3)
                    if p['radius'] > max_radius:
                        p['radius'] = min_radius
                        p['radius_speed'] = random.uniform(-0.3, 0.3)
                    
                    x = center_x + math.cos(p['angle']) * p['radius'] * 3
                    y = center_y + math.sin(p['angle']) * p['radius'] * 1
                    
                    pygame.draw.circle(self.buffer, p['color'], (int(x), int(y)), p['size'])

            elif variant_idx == 6:
                if len(self.plasma_particles) < 80:
                    self.plasma_particles.append({
                        'x': random.randint(0, rect.width),
                        'y': random.randint(0, rect.height),
                        'vx': random.uniform(-4, 4),
                        'vy': random.uniform(-4, 4),
                        'life': 1.0,
                        'color': (random.randint(200, 255), 0, random.randint(200, 255)),
                        'size': random.randint(3, 7)
                    })
                
                for p in self.plasma_particles[:]:
                    p['x'] += p['vx']
                    p['y'] += p['vy']
                    p['vx'] += random.uniform(-0.2, 0.2)
                    p['vy'] += random.uniform(-0.2, 0.2)
                    p['life'] -= 0.005
                    
                    if p['x'] < 0 or p['x'] > rect.width or p['y'] < 0 or p['y'] > rect.height or p['life'] <= 0:
                        self.plasma_particles.remove(p)
                    else:
                        pygame.draw.circle(self.buffer, p['color'], (int(p['x']), int(p['y'])), p['size'])
                        
                        for i in range(3):
                            trail_x = p['x'] - p['vx'] * i
                            trail_y = p['y'] - p['vy'] * i
                            trail_size = max(1, p['size'] - i)
                            pygame.draw.circle(self.buffer, p['color'], (int(trail_x), int(trail_y)), trail_size)

            elif variant_idx == 7:
                if len(self.rainbow_particles) < 60:
                    for i in range(60):
                        x_pos = 50 + (i / 60) * (rect.width - 100)
                        
                        color_progress = i / 60
                        
                        if color_progress < 1/7:
                            color = (255, 0, 0)
                        elif color_progress < 2/7:
                            color = (255, 165, 0)
                        elif color_progress < 3/7:
                            color = (255, 255, 0)
                        elif color_progress < 4/7:
                            color = (0, 255, 0)
                        elif color_progress < 5/7:
                            color = (0, 0, 255)
                        elif color_progress < 6/7:
                            color = (75, 0, 130)
                        else:
                            color = (238, 130, 238)
                        
                        y_pos = random.randint(50, rect.height - 50)
                        
                        self.rainbow_particles.append({
                            'x': x_pos,
                            'y': y_pos,
                            'base_x': x_pos,
                            'base_y': y_pos,
                            'home_x': x_pos,
                            'home_y': y_pos,
                            'angle': random.uniform(0, math.pi * 2),
                            'wave_offset': i * 0.1,
                            'speed': random.uniform(0.01, 0.015),
                            'color': color,
                            'size': random.randint(2, 5),
                            'flap_amplitude': random.uniform(30, 50),
                            'twist_amount': random.uniform(0.3, 0.7),
                            'trail': []
                        })
                
                time_val = self.time * 0.25
                
                for p in self.rainbow_particles[:]:
                    p['trail'].append({'x': p['x'], 'y': p['y'], 'life': 1})
                    if len(p['trail']) > 5:
                        p['trail'].pop(0)
                    
                    p['angle'] += p['speed']
                    
                    wave_x = math.sin(time_val * 1.5 + p['wave_offset']) * 20
                    wave_y = math.cos(time_val * 2 + p['wave_offset']) * 15
                    
                    twist_factor = p['twist_amount'] * math.sin(time_val * 1.2 + p['home_x'] * 0.02)
                    
                    p['x'] = p['home_x'] + wave_x + twist_factor * 10
                    p['y'] = p['home_y'] + wave_y + math.sin(p['angle']) * 10
                    
                    if p['x'] < 30: p['x'] = 30
                    if p['x'] > rect.width - 30: p['x'] = rect.width - 30
                    if p['y'] < 30: p['y'] = 30
                    if p['y'] > rect.height - 30: p['y'] = rect.height - 30
                    
                    for i, t in enumerate(p['trail']):
                        t['life'] -= 0.02
                        if t['life'] > 0:
                            fade = t['life']
                            trail_color = (
                                int(p['color'][0] * fade),
                                int(p['color'][1] * fade),
                                int(p['color'][2] * fade)
                            )
                            trail_size = max(1, int(p['size'] * fade * 0.6))
                            pygame.draw.circle(self.buffer, trail_color, 
                                             (int(t['x']), int(t['y'])), trail_size)
                    
                    pygame.draw.circle(self.buffer, p['color'], 
                                     (int(p['x']), int(p['y'])), p['size'])
                
                if random.random() > 0.5:
                    sorted_particles = sorted(self.rainbow_particles, key=lambda p: p['home_x'])
                    
                    for i in range(len(sorted_particles) - 1):
                        p1 = sorted_particles[i]
                        p2 = sorted_particles[i + 1]
                        
                        dist = math.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])
                        if dist < 100:
                            connect_color = (
                                (p1['color'][0] + p2['color'][0]) // 2,
                                (p1['color'][1] + p2['color'][1]) // 2,
                                (p1['color'][2] + p2['color'][2]) // 2
                            )
                            if random.random() > 0.3:
                                pygame.draw.line(self.buffer, connect_color,
                                                (int(p1['x']), int(p1['y'])),
                                                (int(p2['x']), int(p2['y'])), 2)
                
                if len(self.rainbow_particles) < 70 and random.random() > 0.98:
                    new_x = random.randint(50, rect.width - 50)
                    color_progress = (new_x - 50) / (rect.width - 100)
                    
                    if color_progress < 1/7: color = (255, 0, 0)
                    elif color_progress < 2/7: color = (255, 165, 0)
                    elif color_progress < 3/7: color = (255, 255, 0)
                    elif color_progress < 4/7: color = (0, 255, 0)
                    elif color_progress < 5/7: color = (0, 0, 255)
                    elif color_progress < 6/7: color = (75, 0, 130)
                    else: color = (238, 130, 238)
                    
                    self.rainbow_particles.append({
                        'x': new_x,
                        'y': random.randint(50, rect.height - 50),
                        'base_x': new_x,
                        'base_y': random.randint(50, rect.height - 50),
                        'home_x': new_x,
                        'home_y': random.randint(50, rect.height - 50),
                        'angle': random.uniform(0, math.pi * 2),
                        'wave_offset': random.uniform(0, math.pi * 2),
                        'speed': random.uniform(0.01, 0.015),
                        'color': color,
                        'size': random.randint(5, 8),
                        'flap_amplitude': random.uniform(30, 50),
                        'twist_amount': random.uniform(0.3, 0.7),
                        'trail': []
                    })
                
                if random.random() > 0.97:
                    for _ in range(3):
                        spark_progress = random.random()
                        spark_x = 50 + spark_progress * (rect.width - 100)
                        
                        if spark_progress < 1/7: spark_color = (255, 200, 200)
                        elif spark_progress < 2/7: spark_color = (255, 220, 180)
                        elif spark_progress < 3/7: spark_color = (255, 255, 200)
                        elif spark_progress < 4/7: spark_color = (200, 255, 200)
                        elif spark_progress < 5/7: spark_color = (200, 200, 255)
                        elif spark_progress < 6/7: spark_color = (180, 150, 255)
                        else: spark_color = (255, 200, 255)
                        
                        spark_y = random.randint(50, rect.height - 50)
                        pygame.draw.circle(self.buffer, spark_color, 
                                         (int(spark_x), spark_y), 2)

            elif variant_idx == 8:
                if random.random() > 0.92:
                    for _ in range(random.randint(1, 3)):
                        start_x = random.randint(50, rect.width - 50)
                        start_y = 0
                        self.lightning.append({
                            'segments': [(start_x, start_y)],
                            'life': random.uniform(0.8, 1.2),
                            'branches': [],
                            'thickness': random.randint(2, 4),
                            'color': (random.randint(200, 255), random.randint(200, 255), 255)
                        })
                
                if random.random() > 0.98:
                    crash_x = random.randint(50, rect.width - 50)
                    crash_y = random.randint(rect.height // 3, rect.height - 50)
                    for _ in range(random.randint(8, 15)):
                        self.explosions.append({
                            'x': crash_x,
                            'y': crash_y,
                            'vx': random.uniform(-8, 8),
                            'vy': random.uniform(-12, 2),
                            'life': random.uniform(0.5, 0.9),
                            'color': (random.randint(200, 255), random.randint(150, 255), random.randint(0, 100))
                        })
                
                for bolt in self.lightning[:]:
                    bolt['life'] -= 0.015
                    
                    if bolt['life'] > 0.6 and len(bolt['segments']) < random.randint(12, 18):
                        last_x, last_y = bolt['segments'][-1]
                        new_x = last_x + random.randint(-35, 35)
                        new_y = last_y + random.randint(20, 40)
                        bolt['segments'].append((new_x, new_y))
                        
                        if random.random() > 0.6:
                            branch = []
                            bx, by = last_x, last_y
                            for _ in range(random.randint(4, 8)):
                                bx += random.randint(-25, 25)
                                by += random.randint(15, 30)
                                branch.append((bx, by))
                            bolt['branches'].append(branch)
                    
                    thickness = max(1, int(bolt['thickness'] * bolt['life']))
                    for i in range(len(bolt['segments']) - 1):
                        pygame.draw.line(self.buffer, bolt['color'], 
                                        bolt['segments'][i], bolt['segments'][i + 1], thickness)
                        if bolt['life'] > 0.5:
                            pygame.draw.line(self.buffer, (255, 255, 255), 
                                            bolt['segments'][i], bolt['segments'][i + 1], thickness - 1)
                    
                    for branch in bolt['branches']:
                        for i in range(len(branch) - 1):
                            branch_thickness = max(1, thickness - 1)
                            pygame.draw.line(self.buffer, bolt['color'], 
                                            branch[i], branch[i + 1], branch_thickness)
                    
                    if len(bolt['segments']) > 1 and bolt['life'] > 0.7:
                        tip_x, tip_y = bolt['segments'][-1]
                        for _ in range(random.randint(0, 2)):
                            self.explosions.append({
                                'x': tip_x,
                                'y': tip_y,
                                'vx': random.uniform(-3, 3),
                                'vy': random.uniform(-3, 3),
                                'life': random.uniform(0.2, 0.4),
                                'color': (random.randint(200, 255), random.randint(150, 255), random.randint(0, 100))
                            })
                    
                    if bolt['life'] <= 0:
                        self.lightning.remove(bolt)

            elif variant_idx == 9:
                if len(self.starfield) < 150:
                    self.starfield.append({
                        'x': random.randint(0, rect.width),
                        'y': random.randint(0, rect.height),
                        'z': random.uniform(0.1, 1.0),
                        'speed': random.uniform(1, 3)
                    })
                
                for s in self.starfield[:]:
                    s['z'] -= 0.01
                    if s['z'] <= 0:
                        s['x'] = random.randint(0, rect.width)
                        s['y'] = random.randint(0, rect.height)
                        s['z'] = 1.0
                    
                    size = int(4 * s['z'])
                    x = int(s['x'] + (s['x'] - rect.width//2) * s['speed'] * 0.01)
                    y = int(s['y'] + (s['y'] - rect.height//2) * s['speed'] * 0.01)
                    
                    if 0 <= x < rect.width and 0 <= y < rect.height:
                        brightness = int(255 * s['z'])
                        pygame.draw.circle(self.buffer, (brightness, brightness, brightness), (x, y), size)

            elif variant_idx == 10:
                center_x, center_y = rect.width // 2, rect.height // 2
                
                if len(self.vortex) < 80:
                    for _ in range(3):
                        angle = random.uniform(0, math.pi * 2)
                        radius = random.uniform(30, 200)
                        speed = random.uniform(0.03, 0.08)
                        self.vortex.append({
                            'angle': angle,
                            'radius': radius,
                            'speed': speed,
                            'y_offset': random.uniform(-rect.height//4, rect.height//4),
                            'color': (
                                random.randint(50, 150),
                                random.randint(100, 255),
                                random.randint(200, 255)
                            ),
                            'size': random.randint(3, 6),
                            'life': random.uniform(0.7, 1.0)
                        })
                
                if len(self.rainbow_particles) < 30:
                    self.rainbow_particles.append({
                        'x': center_x,
                        'y': center_y,
                        'angle': random.uniform(0, math.pi * 2),
                        'speed': random.uniform(2, 5),
                        'color': (random.randint(100, 255), random.randint(100, 255), 255),
                        'size': random.randint(2, 4),
                        'life': 1.0
                    })
                
                for p in self.vortex[:]:
                    p['angle'] += p['speed']
                    p['radius'] -= 0.1
                    p['life'] -= 0.002
                    
                    if p['radius'] < 20 or p['life'] <= 0:
                        p['radius'] = random.uniform(150, 200)
                        p['life'] = random.uniform(0.7, 1.0)
                        p['y_offset'] = random.uniform(-rect.height//4, rect.height//4)
                    
                    x = center_x + math.cos(p['angle']) * p['radius'] * 3
                    y = center_y + math.sin(p['angle']) * p['radius'] * 0.3 + p['y_offset']
                    
                    brightness = int(200 * (p['radius'] / 100))
                    color = (
                        min(255, p['color'][0] + brightness//2),
                        min(255, p['color'][1]),
                        min(255, p['color'][2])
                    )
                    
                    pygame.draw.circle(self.buffer, color, (int(x), int(y)), p['size'])
                
                for p in self.rainbow_particles[:]:
                    p['x'] += math.cos(p['angle']) * p['speed']
                    p['y'] += math.sin(p['angle']) * p['speed']
                    p['life'] -= 0.01
                    
                    dist = math.sqrt((p['x'] - center_x)**2 + (p['y'] - center_y)**2)
                    if dist > 100 or p['life'] <= 0:
                        p['x'] = center_x
                        p['y'] = center_y
                        p['angle'] = random.uniform(0, math.pi * 2)
                        p['life'] = 1.0
                    
                    pygame.draw.circle(self.buffer, p['color'], 
                                     (int(p['x']), int(p['y'])), p['size'])
                
                pygame.draw.circle(self.buffer, (150, 150, 255), (center_x, center_y), 10)
                pygame.draw.circle(self.buffer, (100, 100, 200), (center_x, center_y), 15, 2)

            elif variant_idx == 11:
                if len(self.supernova) < 1:
                    self.supernova.append({
                        'x': rect.width // 2,
                        'y': rect.height // 2,
                        'shockwave': 10,
                        'particles': [],
                    })
                
                for sn in self.supernova:
                    sn['shockwave'] += 2
                    
                    if sn['shockwave'] < 400:
                        pygame.draw.circle(self.buffer, (255, 200, 100), 
                                         (sn['x'], sn['y']), int(sn['shockwave']), 2)
                    else:
                        sn['shockwave'] = 20
                    
                    if len(sn['particles']) < 200:
                        for _ in range(5):
                            angle = random.uniform(0, math.pi * 2)
                            speed = random.uniform(3, 8)
                            sn['particles'].append({
                                'x': sn['x'],
                                'y': sn['y'],
                                'vx': math.cos(angle) * speed,
                                'vy': math.sin(angle) * speed,
                                'life': random.uniform(0.8, 1.5),
                                'color': (random.randint(200, 255), random.randint(100, 200), 0),
                                'size': random.randint(2, 5)
                            })
                    
                    for p in sn['particles'][:]:
                        p['x'] += p['vx']
                        p['y'] += p['vy']
                        p['life'] -= 0.01
                        if p['x'] < 0 or p['x'] > rect.width or p['y'] < 0 or p['y'] > rect.height or p['life'] <= 0:
                            sn['particles'].remove(p)
                        else:
                            pygame.draw.circle(self.buffer, p['color'], (int(p['x']), int(p['y'])), p['size'])

            elif variant_idx == 12:
                center_x, center_y = rect.width // 2, rect.height // 2
                
                if len(self.supernova) < 1:
                    self.supernova.append({
                        'x': center_x,
                        'y': center_y,
                        'pulse': 0,
                        'core_size': 40,
                        'flames': [],
                        'melt_particles': [],
                        'energy_rings': []
                    })
                
                for fb in self.supernova:
                    fb['pulse'] += 0.1
                    
                    core_pulse = 40 + int(math.sin(fb['pulse']) * 8)
                    
                    pygame.draw.circle(self.buffer, (180, 220, 255), 
                                     (fb['x'], fb['y']), core_pulse - 5)
                    pygame.draw.circle(self.buffer, (100, 180, 255), 
                                     (fb['x'], fb['y']), core_pulse)
                    pygame.draw.circle(self.buffer, (50, 120, 255), 
                                     (fb['x'], fb['y']), core_pulse + 8, 2)
                    
                    if len(fb['flames']) < 35:
                        for _ in range(3):
                            angle = random.uniform(0, math.pi * 2)
                            distance = random.uniform(20, 50)
                            fb['flames'].append({
                                'x': fb['x'] + math.cos(angle) * distance,
                                'y': fb['y'] + math.sin(angle) * distance * 0.6,
                                'vx': math.cos(angle) * random.uniform(-1, 1),
                                'vy': math.sin(angle) * random.uniform(-1, 1) - 0.5,
                                'life': random.uniform(0.7, 1.0),
                                'size': random.randint(6, 12),
                                'color': (
                                    random.randint(50, 150),
                                    random.randint(150, 255),
                                    random.randint(200, 255)
                                )
                            })
                    
                    for flame in fb['flames'][:]:
                        flame['x'] += flame['vx']
                        flame['y'] += flame['vy']
                        flame['life'] -= 0.01
                        flame['vy'] -= 0.02
                        flame['vx'] += random.uniform(-0.1, 0.1)
                        
                        size = int(flame['size'] * flame['life'])
                        
                        if flame['y'] < fb['y'] - 80 or flame['life'] <= 0 or flame['x'] < 0 or flame['x'] > rect.width:
                            fb['flames'].remove(flame)
                        else:
                            gradient = int(255 * flame['life'])
                            color = (
                                int(flame['color'][0] * flame['life']),
                                int(flame['color'][1] * flame['life']),
                                255
                            )
                            pygame.draw.circle(self.buffer, color, 
                                             (int(flame['x']), int(flame['y'])), size)
                    
                    if len(fb['melt_particles']) < 60:
                        for _ in range(4):
                            fb['melt_particles'].append({
                                'x': fb['x'] + random.randint(-30, 30),
                                'y': fb['y'] + random.randint(-20, 20),
                                'vx': random.uniform(-0.5, 0.5),
                                'vy': random.uniform(0.5, 2.0),
                                'life': random.uniform(0.6, 1.0),
                                'size': random.randint(3, 7),
                                'color': (
                                    random.randint(50, 150),
                                    random.randint(150, 255),
                                    random.randint(200, 255)
                                )
                            })
                    
                    for melt in fb['melt_particles'][:]:
                        melt['x'] += melt['vx']
                        melt['y'] += melt['vy']
                        melt['vy'] += 0.05
                        melt['life'] -= 0.005
                        
                        size = int(melt['size'] * melt['life'])
                        if size < 1: size = 1
                        
                        if melt['y'] > rect.height or melt['life'] <= 0:
                            fb['melt_particles'].remove(melt)
                        else:
                            pygame.draw.circle(self.buffer, melt['color'], 
                                             (int(melt['x']), int(melt['y'])), size)
                            
                            if melt['life'] > 0.3:
                                trail_color = (
                                    int(melt['color'][0] * melt['life'] * 0.5),
                                    int(melt['color'][1] * melt['life'] * 0.5),
                                    int(melt['color'][2] * melt['life'] * 0.5)
                                )
                                pygame.draw.circle(self.buffer, trail_color, 
                                                 (int(melt['x'] - melt['vx']), int(melt['y'] - melt['vy'])), 
                                                 max(1, size - 1))
                    
                    if random.random() > 0.85:
                        for _ in range(3):
                            dx = random.randint(-60, 60)
                            dy = random.randint(-40, 40)
                            shimmer_color = (
                                random.randint(150, 255),
                                random.randint(200, 255),
                                255
                            )
                            pygame.draw.circle(self.buffer, shimmer_color, 
                                             (fb['x'] + dx, fb['y'] + dy), 2)
                    
                    for i in range(3):
                        glow_size = core_pulse + 20 + i * 10
                        if i == 0:
                            pygame.draw.circle(self.buffer, (50, 100, 200), 
                                             (fb['x'], fb['y']), glow_size, 1)
                        elif i == 1:
                            pygame.draw.circle(self.buffer, (30, 70, 150), 
                                             (fb['x'], fb['y']), glow_size, 1)
                        else:
                            pygame.draw.circle(self.buffer, (10, 40, 100), 
                                             (fb['x'], fb['y']), glow_size, 1)
                
                t_col = (180, 220, 255)
                line_h = 22
                total_h = len(current_ascii) * line_h
                start_y = rect.height // 2 - (total_h // 2)
                
                for i, line in enumerate(current_ascii):
                    for glow_pass in range(3):
                        offset = glow_pass * 2
                        glow_color = (
                            max(0, t_col[0] - glow_pass * 40),
                            max(0, t_col[1] - glow_pass * 20),
                            255
                        )
                        txt_surf = self.ascii_font.render(line, True, glow_color)
                        pos_x = rect.width // 2 - (txt_surf.get_width() // 2)
                        pos_y = start_y + (i * line_h)
                        
                        wave_offset = int(math.sin(self.time * 5 + i + glow_pass) * 3)
                        
                        if glow_pass == 0:
                            self.buffer.blit(txt_surf, (pos_x + wave_offset, pos_y))
                        else:
                            self.buffer.blit(txt_surf, (pos_x + wave_offset + offset, pos_y))
                            self.buffer.blit(txt_surf, (pos_x + wave_offset - offset, pos_y))
                            self.buffer.blit(txt_surf, (pos_x + wave_offset, pos_y + offset))
                            self.buffer.blit(txt_surf, (pos_x + wave_offset, pos_y - offset))

            elif variant_idx == 13:
                center_x, center_y = rect.width // 2, rect.height // 2
                
                if len(self.supernova) < 1:
                    self.supernova.append({
                        'x': center_x,
                        'y': center_y,
                        'pulse': 0,
                        'rotation': 0,
                        'wormhole_particles': [],
                        'energy_rings': [],
                        'star_streams': [],
                        'dimension_shift': 0
                    })
                
                for portal in self.supernova:
                    portal['pulse'] += 0.05
                    portal['rotation'] += 0.02
                    portal['dimension_shift'] += 0.01
                    
                    core_size = 40 + int(math.sin(portal['pulse']) * 12)
                    pygame.draw.circle(self.buffer, (255, 255, 255), 
                                     (int(portal['x']), int(portal['y'])), core_size - 10)
                    pygame.draw.circle(self.buffer, (180, 220, 255), 
                                     (int(portal['x']), int(portal['y'])), core_size)
                    pygame.draw.circle(self.buffer, (100, 150, 255), 
                                     (int(portal['x']), int(portal['y'])), core_size + 10, 2)
                    
                    for ring_i in range(8):
                        ring_radius = 80 + ring_i * 25 + int(math.sin(portal['pulse'] + ring_i) * 10)
                        ring_speed = portal['rotation'] * (1 + ring_i * 0.2)
                        ring_points = []
                        
                        for i in range(12):
                            angle = ring_speed + (i * math.pi * 2 / 12)
                            x = portal['x'] + math.cos(angle) * ring_radius
                            y = portal['y'] + math.sin(angle) * ring_radius * 0.3 + math.sin(angle * 2) * 10
                            
                            depth = 0.3 + 0.7 * (1 - (ring_i / 8))
                            ring_color = (
                                int(50 + 100 * depth),
                                int(100 + 150 * depth),
                                255
                            )
                            
                            ring_points.append((int(x), int(y)))
                            
                            if i > 0:
                                pygame.draw.line(self.buffer, ring_color,
                                                ring_points[i-1], ring_points[i], 2)
                            if i == 11:
                                pygame.draw.line(self.buffer, ring_color,
                                                ring_points[i], ring_points[0], 2)
                    
                    if len(portal['wormhole_particles']) < 150:
                        for _ in range(5):
                            angle = random.uniform(0, math.pi * 2)
                            distance = random.uniform(150, 300)
                            portal['wormhole_particles'].append({
                                'x': portal['x'] + math.cos(angle) * distance,
                                'y': portal['y'] + math.sin(angle) * distance * 0.5,
                                'z': random.uniform(0, 1),
                                'angle': angle,
                                'speed': random.uniform(2, 5),
                                'spiral': random.uniform(0.02, 0.05),
                                'color': (
                                    random.randint(150, 255),
                                    random.randint(100, 200),
                                    random.randint(200, 255)
                                ),
                                'size': random.randint(3, 7)
                            })
                    
                    for p in portal['wormhole_particles'][:]:
                        p['angle'] += p['spiral']
                        p['z'] -= 0.01
                        
                        dx = portal['x'] - p['x']
                        dy = portal['y'] - p['y']
                        dist = math.hypot(dx, dy)
                        
                        if dist < 20 or p['z'] <= 0:
                            portal['wormhole_particles'].remove(p)
                            continue
                        
                        p['x'] += (dx / dist) * p['speed'] * 0.5
                        p['y'] += (dy / dist) * p['speed'] * 0.5
                        p['x'] += math.cos(p['angle']) * p['speed'] * 0.3
                        p['y'] += math.sin(p['angle']) * p['speed'] * 0.1
                        
                        depth_factor = p['z']
                        size = int(p['size'] * depth_factor)
                        color = (
                            int(p['color'][0] * depth_factor),
                            int(p['color'][1] * depth_factor),
                            int(p['color'][2] * depth_factor)
                        )
                        
                        if size > 0:
                            pygame.draw.circle(self.buffer, color, 
                                             (int(p['x']), int(p['y'])), size)
                            
                            if random.random() > 0.7:
                                pygame.draw.circle(self.buffer, color, 
                                                 (int(p['x'] - p['speed']), int(p['y'] - p['speed'] * 0.5)), 
                                                 max(1, size - 1))
                    
                    if len(portal['star_streams']) < 40:
                        if random.random() > 0.92:
                            side = random.choice(['left', 'right', 'top', 'bottom'])
                            if side == 'left':
                                x, y = 0, random.randint(0, rect.height)
                                vx, vy = random.uniform(8, 15), random.uniform(-2, 2)
                            elif side == 'right':
                                x, y = rect.width, random.randint(0, rect.height)
                                vx, vy = random.uniform(-15, -8), random.uniform(-2, 2)
                            elif side == 'top':
                                x, y = random.randint(0, rect.width), 0
                                vx, vy = random.uniform(-2, 2), random.uniform(8, 15)
                            else:
                                x, y = random.randint(0, rect.width), rect.height
                                vx, vy = random.uniform(-2, 2), random.uniform(-15, -8)
                            
                            portal['star_streams'].append({
                                'x': x, 'y': y,
                                'vx': vx, 'vy': vy,
                                'life': 1.0,
                                'color': (
                                    random.randint(200, 255),
                                    random.randint(200, 255),
                                    255
                                ),
                                'size': random.randint(2, 4),
                                'trail': []
                            })
                    
                    for s in portal['star_streams'][:]:
                        s['x'] += s['vx']
                        s['y'] += s['vy']
                        s['life'] -= 0.01
                        
                        s['trail'].append({'x': s['x'], 'y': s['y'], 'life': 0.3})
                        if len(s['trail']) > 10:
                            s['trail'].pop(0)
                        
                        for t in s['trail']:
                            t['life'] -= 0.02
                            if t['life'] > 0:
                                trail_color = (
                                    int(s['color'][0] * t['life']),
                                    int(s['color'][1] * t['life']),
                                    int(s['color'][2] * t['life'])
                                )
                                trail_size = max(1, int(s['size'] * t['life']))
                                pygame.draw.circle(self.buffer, trail_color,
                                                 (int(t['x']), int(t['y'])), trail_size)
                        
                        if s['life'] > 0 and 0 <= s['x'] <= rect.width and 0 <= s['y'] <= rect.height:
                            pygame.draw.circle(self.buffer, s['color'],
                                             (int(s['x']), int(s['y'])), s['size'])
                        else:
                            portal['star_streams'].remove(s)
                    
                    if random.random() > 0.95:
                        for _ in range(10):
                            angle = random.uniform(0, math.pi * 2)
                            dist = random.uniform(50, 200)
                            x = portal['x'] + math.cos(angle) * dist
                            y = portal['y'] + math.sin(angle) * dist * 0.3
                            
                            quantum_shift = (math.sin(portal['dimension_shift'] + angle) + 1) * 0.5
                            q_color = (
                                int(100 + 155 * quantum_shift),
                                int(50 + 100 * quantum_shift),
                                255
                            )
                            
                            pygame.draw.circle(self.buffer, q_color, (int(x), int(y)), 2)
                    
                    if random.random() > 0.98:
                        rift_x = portal['x'] + random.randint(-100, 100)
                        rift_y = portal['y'] + random.randint(-80, 80)
                        
                        for i in range(5):
                            rift_x2 = rift_x + random.randint(-30, 30)
                            rift_y2 = rift_y + random.randint(-30, 30)
                            rift_color = (
                                random.randint(150, 255),
                                random.randint(100, 200),
                                255
                            )
                            pygame.draw.line(self.buffer, rift_color,
                                           (rift_x, rift_y), (rift_x2, rift_y2), 2)

            elif variant_idx == 14:
                center_x, center_y = rect.width // 2, rect.height // 2
                
                if len(self.supernova) < 1:
                    self.supernova.append({
                        'impact_craters': [],
                        'fire_rings': [],
                        'debris_clouds': [],
                        'shockwaves': [],
                        'meteor_shower_intensity': 1.0
                    })
                
                for apoc in self.supernova:
                    spawn_rate = 0.92 + (apoc['meteor_shower_intensity'] * 0.03)
                    if random.random() > spawn_rate:
                        for _ in range(random.randint(1, 4)):
                            gold_variation = random.randint(0, 2)
                            if gold_variation == 0:
                                color = (255, 215, 0)
                            elif gold_variation == 1:
                                color = (255, 200, 50)
                            else:
                                color = (255, 165, 0)
                            
                            angle_variation = random.uniform(-0.5, 0.5)
                            
                            self.meteors.append({
                                'x': random.randint(rect.width // 4, rect.width),
                                'y': random.randint(-100, -20),
                                'vx': random.uniform(-8, -4) + angle_variation,
                                'vy': random.uniform(5, 9) + abs(angle_variation * 2),
                                'trail': [],
                                'size': random.randint(6, 12),
                                'color': color,
                                'glow_size': random.randint(12, 20),
                                'rotation': random.uniform(0, math.pi * 2),
                                'rotation_speed': random.uniform(-0.1, 0.1),
                                'debris_count': random.randint(3, 7),
                                'has_impacted': False
                            })
                    
                    for m in self.meteors[:]:
                        m['x'] += m['vx']
                        m['y'] += m['vy']
                        m['rotation'] += m['rotation_speed']
                        
                        m['vy'] += 0.05
                        m['vx'] += random.uniform(-0.03, 0.03)
                        
                        for _ in range(2):
                            trail_offset_x = random.uniform(-2, 2)
                            trail_offset_y = random.uniform(-2, 2)
                            m['trail'].append({
                                'x': m['x'] + trail_offset_x,
                                'y': m['y'] + trail_offset_y,
                                'life': random.uniform(0.7, 1.0),
                                'size': m['size'] * random.uniform(0.6, 0.9)
                            })
                        
                        if len(m['trail']) > 30:
                            m['trail'].pop(0)
                        
                        for t in m['trail']:
                            t['life'] -= 0.02
                            if t['life'] > 0:
                                fade = t['life']
                                trail_color = (
                                    max(0, min(255, int(m['color'][0] * fade))),
                                    max(0, min(255, int(m['color'][1] * fade * 0.7))),
                                    max(0, min(255, int(m['color'][2] * fade * 0.3)))
                                )
                                size = int(t['size'] * fade * 0.7)
                                if size > 0:
                                    if random.random() > 0.8:
                                        size += 1
                                    pygame.draw.circle(self.buffer, trail_color,
                                                     (int(t['x']), int(t['y'])), size)
                        
                        glow_color = (
                            max(0, min(255, m['color'][0])),
                            max(0, min(255, int(m['color'][1] * 0.7))),
                            0
                        )
                        pygame.draw.circle(self.buffer, glow_color,
                                         (int(m['x']), int(m['y'])), m['glow_size'])
                        
                        pygame.draw.circle(self.buffer, (255, 255, 200),
                                         (int(m['x']), int(m['y'])), m['size'] - 1)
                        
                        pygame.draw.circle(self.buffer, m['color'],
                                         (int(m['x']), int(m['y'])), m['size'])
                        
                        if m['y'] > rect.height - 50 and not m['has_impacted']:
                            m['has_impacted'] = True
                            
                            for _ in range(m['debris_count'] * 3):
                                angle = random.uniform(0, math.pi * 2)
                                speed = random.uniform(3, 8)
                                apoc['debris_clouds'].append({
                                    'x': m['x'],
                                    'y': m['y'],
                                    'vx': math.cos(angle) * speed,
                                    'vy': math.sin(angle) * speed - 2,
                                    'life': random.uniform(0.8, 1.2),
                                    'color': m['color'],
                                    'size': random.randint(2, 4)
                                })
                            
                            apoc['shockwaves'].append({
                                'x': m['x'],
                                'y': m['y'],
                                'radius': 10,
                                'max_radius': 80,
                                'life': 1.0,
                                'color': (255, 200, 100)
                            })
                            
                            apoc['impact_craters'].append({
                                'x': m['x'],
                                'y': min(m['y'], rect.height - 30),
                                'size': m['size'] * 2,
                                'life': 1.0
                            })
                            
                            apoc['fire_rings'].append({
                                'x': m['x'],
                                'y': min(m['y'], rect.height - 30),
                                'radius': 20,
                                'life': 1.0,
                                'color': (255, 200, 50)
                            })
                        
                        if (m['y'] > rect.height + 100 or 
                            m['x'] < -100 or 
                            m['x'] > rect.width + 100):
                            self.meteors.remove(m)
                    
                    for d in apoc['debris_clouds'][:]:
                        d['x'] += d['vx']
                        d['y'] += d['vy']
                        d['vy'] += 0.1
                        d['vx'] *= 0.98
                        d['vy'] *= 0.98
                        d['life'] -= 0.01
                        
                        if d['life'] <= 0 or d['y'] > rect.height + 50:
                            apoc['debris_clouds'].remove(d)
                        else:
                            fade = d['life']
                            r = d['color'][0]
                            g = d['color'][1]
                            b = d['color'][2]
                            
                            color = (
                                max(0, min(255, int(r * fade))),
                                max(0, min(255, int(g * fade * 0.7))),
                                max(0, min(255, int(b * fade * 0.3)))
                            )
                            size = max(1, int(d['size'] * fade))
                            pygame.draw.circle(self.buffer, color,
                                             (int(d['x']), int(d['y'])), size)
                    
                    for s in apoc['shockwaves'][:]:
                        s['radius'] += 5
                        s['life'] -= 0.02
                        
                        if s['radius'] > s['max_radius'] or s['life'] <= 0:
                            apoc['shockwaves'].remove(s)
                        else:
                            color = (
                                max(0, min(255, s['color'][0])),
                                max(0, min(255, int(s['color'][1] * s['life']))),
                                max(0, min(255, int(s['color'][2] * s['life'] * 0.5)))
                            )
                            pygame.draw.circle(self.buffer, color,
                                             (int(s['x']), int(s['y'])), 
                                             int(s['radius']), 2)
                    
                    for fr in apoc['fire_rings'][:]:
                        fr['radius'] += 3
                        fr['life'] -= 0.02
                        
                        if fr['radius'] > 60 or fr['life'] <= 0:
                            apoc['fire_rings'].remove(fr)
                        else:
                            fade = fr['life']
                            color = (
                                255,
                                max(0, min(255, int(200 * fade))),
                                max(0, min(255, int(50 * fade)))
                            )
                            pygame.draw.circle(self.buffer, color,
                                             (int(fr['x']), int(fr['y'])), 
                                             int(fr['radius']), 2)
                    
                    for c in apoc['impact_craters'][:]:
                        c['life'] -= 0.01
                        if c['life'] <= 0:
                            apoc['impact_craters'].remove(c)
                        else:
                            fade = c['life']
                            crater_color = (
                                max(0, min(255, int(100 * fade))),
                                max(0, min(255, int(70 * fade))),
                                max(0, min(255, int(30 * fade)))
                            )
                            size = int(c['size'] * fade * 0.5)
                            pygame.draw.circle(self.buffer, crater_color,
                                             (int(c['x']), int(c['y'])), size)
                    
                    apoc['meteor_shower_intensity'] += random.uniform(-0.1, 0.1)
                    apoc['meteor_shower_intensity'] = max(0.5, min(1.5, apoc['meteor_shower_intensity']))
                    
                    if random.random() > 0.95:
                        glow_x = random.randint(0, rect.width)
                        glow_y = rect.height - random.randint(0, 100)
                        glow_size = random.randint(30, 80)
                        glow_color = (
                            random.randint(50, 100),
                            random.randint(20, 50),
                            0
                        )
                        pygame.draw.circle(self.buffer, glow_color,
                                         (glow_x, glow_y), glow_size)
                
                for i in range(rect.width // 10):
                    x = i * 10
                    fire_height = rect.height - 20 + int(math.sin(self.time * 5 + i) * 5)
                    fire_color = (
                        random.randint(200, 255),
                        random.randint(100, 150),
                        0
                    )
                    pygame.draw.line(self.buffer, fire_color,
                                   (x, fire_height), (x + 5, fire_height), 2)

            if variant_idx not in [12]:
                t_col = (255, 255, 255)
                if random.random() > 0.97: t_col = (255, 0, 0)
                line_h = 22
                total_h = len(current_ascii) * line_h
                
                if variant_idx == 4:
                    start_y = rect.height - 100
                    t_col = (150, 200, 255)
                else:
                    start_y = rect.height // 2 - (total_h // 2)
                
                for i, line in enumerate(current_ascii):
                    txt_surf = self.ascii_font.render(line, True, t_col)
                    if variant_idx == 4:
                        pos_x = rect.width - txt_surf.get_width() - 50
                    else:
                        pos_x = rect.width // 2 - (txt_surf.get_width() // 2)
                    
                    vib_x = random.randint(-1, 1) if random.random() > 0.8 else 0
                    shadow = self.ascii_font.render(line, True, (0, 0, 0))
                    self.buffer.blit(shadow, (pos_x + 2 + vib_x, start_y + (i * line_h) + 2))
                    self.buffer.blit(txt_surf, (pos_x + vib_x, start_y + (i * line_h)))

            for i in range(0, rect.height, 4):
                pygame.draw.line(self.buffer, (0, 0, 0), (0, i), (rect.width, i))
            
            self.buffer_dirty = False
        
        surface.blit(self.buffer, (rect.x, rect.y))
        self.buffer_dirty = True

class FontManager:
    def __init__(self):
        self.font_cache = {}
        self.system_fonts = ["Malgun Gothic", "Courier New"]
    
    def get_font(self, size=13, bold=False, mono=False):
        cache_key = f"{size}_{bold}_{mono}"
        
        if cache_key in self.font_cache:
            return self.font_cache[cache_key]
        
        if mono:
            font = pygame.font.SysFont("Courier New", size, bold=bold)
        else:
            font = pygame.font.SysFont("Malgun Gothic", size, bold=bold)
        
        self.font_cache[cache_key] = font
        return font
    
    def render_text(self, text, size=13, color=(255, 255, 255), bold=False, max_width=None):
        font = self.get_font(size, bold)
        
        if max_width and font.size(text)[0] > max_width:
            ellipsis = "..."
            while len(text) > 1 and font.size(text + ellipsis)[0] > max_width:
                text = text[:-1]
            text = text + ellipsis if len(text) > 1 else text
        
        return font.render(text, True, color)

class App:
    def __init__(self):
        self.screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
        pygame.display.set_caption("[MelRoms Player]")
        
        
        try:
            icon = pygame.image.load("icon.ico")
            pygame.display.set_icon(icon)
        except pygame.error:
            pass  
        
        
        self.clock = pygame.time.Clock()
        
        self.font_manager = FontManager()
        self.library = MusicLibrary()
        
                # Initialize tkinter root window (hidden)
        self.tk_root = tk.Tk()
        self.tk_root.withdraw()  # Hide the root window
        
        self.lyrics_window = LyricsWindow(self, self.tk_root)  # Pass root to lyrics window
        
        self.last_frame_time = time.time()
        self.frame_times = []
        
        
        # Discord RPC
        self.discord = DiscordRPC()
        self.discord.connect()
        self.discord_thread = threading.Thread(target=self.discord.run_loop, daemon=True)
        self.discord_thread.start()
        
        self.visualizer = WatchdogsVisualizer(850, 200)
        self.visualizer_enabled = True
        self.loader = LoadingState(self.screen)
        self.is_loading = True
        self.selected_artist_idx = 0
        self.current_track = None
        self.current_track_index = -1
        self.track_length = 0
        self.show_search = False
        self.search_query = ""
        self.search_cache = {}
        self.search_results_cache = []
        self.return_to_library = False
        self.scroll_offset = 0
        self.last_click_time = 0
        self.click_target = None
        self.particles = []
        self.ascii_particles = []
        self.show_preferences = False
        
        self.is_paused = False
        self.volume = 0.75
        self.is_muted = False
        self.ctrl_rects = {} 
        self.current_track_position = 0
        
        self.play_queue = []
        self.current_queue_index = -1
        
        self.show_context_menu = False
        self.context_menu_pos = (0, 0)
        self.context_menu_track = None
        self.context_menu_options = [
            ("Add to Queue", "queue"),
            ("Play Next", "next"),
            ("Open File Location", "open")
        ]
        
        self.artist_scroll_offset = 0
        self.max_visible_artists = 0
        
        self.sidebar_sparkle = ASCIISparkle(0, 0, 350, 600)
        self.title_sparkle = ASCIISparkle(400, 30, 400, 50)
        
        self.sort_column = None
        self.sort_reverse = False
        
        self.click_sound = generate_click_sound()
        
        self.menus = [
            ("File", lambda: setattr(self, 'show_preferences', not self.show_preferences)), 
            ("Playback", None), 
            ("Library", lambda: self.toggle_search())
        ]
        
        self.needs_redraw = True
        self.last_particle_update = time.time()
        self.particle_update_interval = 0.033
        self.last_sparkle_update = time.time()
        self.sparkle_update_interval = 0.1
        self.last_full_redraw = time.time()
        self.full_redraw_interval = 0.016
        
        self.last_search_time = 0
        self.pending_search = None
        self.search_delay = 0.3
        self.is_skipping = False 
        
    def toggle_visualizer(self):
        self.visualizer_enabled = not self.visualizer_enabled
        logging.info(f"Visualizer {'enabled' if self.visualizer_enabled else 'disabled'}")
        self.click_sound.play()
        self.needs_redraw = True

    def toggle_search(self):
        self.show_search = not self.show_search
        if not self.show_search:
            if self.search_results_cache and not self.return_to_library:
                self.show_search = True
                self.search_query = self.pending_search or self.search_query
            else:
                self.search_query = ""
                self.search_cache.clear()
                self.pending_search = None
                self.search_results_cache = []
                self.return_to_library = False
                self.scroll_offset = 0
        else:
            self.return_to_library = False
            if self.search_results_cache:
               self.find_and_scroll_to_track(self.current_track)
        self.needs_redraw = True

    def perform_search(self):
        if not self.search_query or len(self.search_query) < 2:
            self.search_cache[self.search_query] = []
            self.search_results_cache = []
            self.needs_redraw = True
            return
        
        if self.search_query in self.search_cache:
            self.search_results_cache = self.search_cache[self.search_query]
            self.needs_redraw = True
            return
        
        logging.info(f"Searching for: {self.search_query}")
        results = self.library.search(self.search_query)
        self.search_cache[self.search_query] = results
        self.search_results_cache = results
        self.scroll_offset = 0
        self.return_to_library = False
        self.needs_redraw = True

    def handle_search_input(self, event):
        if event.key == pygame.K_BACKSPACE:
            self.search_query = self.search_query[:-1]
            self.search_cache.pop(self.search_query, None)
        elif event.key == pygame.K_RETURN:
            self.pending_search = None
            self.perform_search()
            return
        elif event.key not in [pygame.K_LCTRL, pygame.K_RCTRL, pygame.K_LSHIFT, pygame.K_RSHIFT]:
            self.search_query += event.unicode
            self.search_cache.pop(self.search_query, None)
        
        self.scroll_offset = 0
        self.needs_redraw = True
        
        self.last_search_time = time.time()
        self.pending_search = self.search_query

    def check_pending_search(self):
        if self.pending_search is not None:
            if time.time() - self.last_search_time > self.search_delay:
                self.search_query = self.pending_search
                self.perform_search()
                self.pending_search = None
                
    def play_previous_track(self):
        files = self.get_current_files()
        if files and self.current_track_index >= 0:
            prev_index = (self.current_track_index - 1) % len(files)
            self.play_file(files[prev_index], prev_index)

    def check_windows_media_keys(self):
        if not WIN_MEDIA_KEYS:
            return False
        
        if not hasattr(self, 'last_media_key_time'):
            self.last_media_key_time = 0
            self.last_media_key_action = None
        
        current_time = time.time()
        debounce_delay = 0.3
        
        try:
            keys = [
                (0xB3, "playpause"),
                (0xB0, "next"),
                (0xB1, "prev"),
            ]
            
            for vk_code, action in keys:
                if ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000:
                    if (current_time - self.last_media_key_time > debounce_delay or 
                        self.last_media_key_action != action):
                        
                        self.last_media_key_time = current_time
                        self.last_media_key_action = action
                        
                        if action == "playpause":
                            if pygame.mixer.music.get_busy() or self.current_track is not None:
                                if self.is_paused:
                                    pygame.mixer.music.unpause()
                                    self.is_paused = False
                                else:
                                    pygame.mixer.music.pause()
                                    self.is_paused = True
                            else:
                                files = self.get_current_files()
                                if files:
                                    self.play_file(files[0], 0)
                            self.needs_redraw = True
                            return True
                        elif action == "next":
                            self.play_next_track()
                            self.needs_redraw = True
                            return True
                        elif action == "prev":
                            self.play_previous_track()
                            self.needs_redraw = True
                            return True
            return False
        except:
            return False

    def format_size(self, size_bytes):
        if not isinstance(size_bytes, (int, float)) or size_bytes <= 0:
            return "0KB"
        kb = size_bytes / 1024
        if kb < 1024:
            return f"{kb:.1f}KB"
        mb = kb / 1024
        return f"{mb:.1f}MB"

    def draw_text(self, surface, text, pos, color=THEME["text"], bold=False, max_width=None):
        text_surface = self.font_manager.render_text(str(text), size=13, color=color, bold=bold, max_width=max_width)
        surface.blit(text_surface, pos)

    def spawn_click_effect(self, x, y, color=THEME["accent"]):
        for _ in range(8):
            self.particles.append(ClickParticle(x, y, color))
        for _ in range(3):
            self.ascii_particles.append(ASCIIClickParticle(x, y))
        self.needs_redraw = True

    def find_and_scroll_to_track(self, track_path):
        files = self.get_current_files()
        for i, f in enumerate(files):
            if f['path'] == track_path:
                visible_rows = (self.screen.get_height() - 200 - 28 - 30 - 47) // 18
                self.scroll_offset = max(0, i - visible_rows // 2)
                self.needs_redraw = True
                return True
        return False

    def play_file(self, file_dict, index=-1):
        try:
            path = file_dict['path']
            if file_dict in self.play_queue:
                queue_index = self.play_queue.index(file_dict)
                if queue_index <= self.current_queue_index:
                    self.current_queue_index -= 1
                self.play_queue.remove(file_dict)
                logging.info(f"Removed from queue: {file_dict['name']}")
            if file_dict.get('title') is None:
                file_dict = self.library.lazy_load_metadata(file_dict)
            if "::" in path:
                zp, inner = path.split("::")
                with zipfile.ZipFile(zp, 'r') as z:
                    pygame.mixer.music.load(io.BytesIO(z.read(inner)))
            else:
                try:
                    pygame.mixer.music.load(path)
                except pygame.error:
                    logging.warning(f"Pygame can't play {path}, trying alternative method...")
                    raise
            pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
            pygame.mixer.music.play()
            self.current_track = path
            self.current_track_index = index
            self.is_paused = False
            self.current_track_position = 0
            self.track_length = file_dict.get('raw_duration', 0)
            if self.track_length <= 0:
                try:
                    sound = pygame.mixer.Sound(path)
                    self.track_length = sound.get_length()
                except:
                    self.track_length = 180
            self.discord.update(
                song=file_dict.get('title', file_dict['name']),
                artist=file_dict.get('artist', 'Unknown Artist'),
                is_paused=False,
                position=0,
                duration=self.track_length
            )
            if self.show_search or self.search_results_cache:
                search_files = self.search_results_cache.copy()
                current_search_index = self.current_track_index
                self.show_search = False
                self.search_query = ""
                self.pending_search = None
                self.search_results_cache = []
                self.return_to_library = True
                found = False
                for i, artist in enumerate(self.library.artists):
                    for j, track in enumerate(artist['tracks']):
                        if track['path'] == path:
                            self.selected_artist_idx = i
                            self.current_track_index = j 
                            self.find_and_scroll_to_track(path)
                            found = True
                            break
                    if found:
                        break
            logging.info(f"Now playing: {file_dict['name']} (duration: {self.track_length:.1f}s)")
            self.needs_redraw = True
        except Exception as e: 
            logging.error(f"Playback error for {file_dict.get('name', 'unknown')}: {e}")
            self.track_length = 180
            self.play_next_track()

    def play_next_track(self):
        if self.play_queue and self.current_queue_index < len(self.play_queue) - 1:
            self.current_queue_index += 1
            self.play_file(self.play_queue[self.current_queue_index], -2)
            return
        elif self.play_queue and self.current_queue_index == len(self.play_queue) - 1:
            self.play_queue = []
            self.current_queue_index = -1
            files = self.get_current_files()
            if files and self.current_track_index >= 0:
                next_index = (self.current_track_index + 1) % len(files)
                self.play_file(files[next_index], next_index)
            return
        files = self.get_current_files()
        if files and self.current_track_index >= 0:
            next_index = (self.current_track_index + 1) % len(files)
            self.play_file(files[next_index], next_index)

    def skip_seconds(self, seconds):
        try:
            if not pygame.mixer.music.get_busy() and not self.is_paused:
                return
            self.is_skipping = True
            new_pos = self.current_track_position + seconds
            if self.track_length > 0:
                new_pos = max(0, min(self.track_length, new_pos))
            else:
                new_pos = max(0, new_pos)
            logging.info(f"Skipping from {self.current_track_position:.1f}s to {new_pos:.1f}s")
            
            files = self.get_current_files()
            if files and self.current_track_index >= 0:
                file_dict = files[self.current_track_index]
                path = file_dict['path']
                if pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.set_pos(new_pos)
                        self.current_track_position = new_pos
                        logging.info(f"Set position to {new_pos}s using set_pos")
                    except:
                        logging.warning("set_pos failed, falling back to reload")
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        time.sleep(0.1)
                        if "::" in path:
                            zp, inner = path.split("::")
                            with zipfile.ZipFile(zp, 'r') as z:
                                pygame.mixer.music.load(io.BytesIO(z.read(inner)))
                        else:
                            pygame.mixer.music.load(path)
                        
                        pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
                        pygame.mixer.music.play(start=new_pos)
                        self.current_track_position = new_pos
                else:
                    if "::" in path:
                        zp, inner = path.split("::")
                        with zipfile.ZipFile(zp, 'r') as z:
                            pygame.mixer.music.load(io.BytesIO(z.read(inner)))
                    else:
                        pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
                    pygame.mixer.music.play(start=new_pos)
                    self.current_track_position = new_pos
                if hasattr(self, 'lyrics_window'):
                    self.lyrics_window.update_display()
                self.discord.update(
                    song=file_dict.get('title', file_dict['name']),
                    artist=file_dict.get('artist', 'Unknown Artist'),
                    is_paused=False,
                    position=new_pos,
                    duration=self.track_length
                )
                self.click_sound.play()
                mx, my = pygame.mouse.get_pos()
                self.spawn_click_effect(mx, my, THEME["sidebar_accent"])
                self.needs_redraw = True
                self.is_skipping = False
        except Exception as e:
            logging.error(f"Skip error: {e}")
            self.is_skipping = False
    def get_current_files(self):
        if self.search_results_cache and not self.return_to_library:
            return self.search_results_cache
        elif self.show_search:
            if self.search_query in self.search_cache:
                return self.search_cache[self.search_query]
            return []
        elif self.library.artists:
            artist = self.library.artists[self.selected_artist_idx]
            files = self.library.get_files_in_artist(self.selected_artist_idx)
            return files
        return []
    def sort_files(self, files, column, reverse=False):
        if not files:
            return files
        if column == 'name':
            return sorted(files, key=lambda x: (x.get('title') or x['name'] or "").lower(), reverse=reverse)
        elif column == 'duration':
            return sorted(files, key=lambda x: x.get('raw_duration', 0), reverse=reverse)
        elif column == 'size':
            return sorted(files, key=lambda x: x.get('size', 0), reverse=reverse)
        elif column == 'artist':
            return sorted(files, key=lambda x: (x.get('artist') or "").lower(), reverse=reverse)
        elif column == 'album':
            return sorted(files, key=lambda x: (x.get('album') or "").lower(), reverse=reverse)
        else:
            return files
    def draw_menu_bar(self):
        w, _ = self.screen.get_size()
        pygame.draw.rect(self.screen, THEME["header_bg"], (0, 0, w, 28))
        x = 10
        mouse_pos = pygame.mouse.get_pos()
        for m, func in self.menus:
            menu_font = self.font_manager.get_font(13, bold=False)
            rect = pygame.Rect(x, 0, menu_font.size(m)[0] + 15, 28)
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, THEME["sidebar"], rect)
            self.draw_text(self.screen, m, (x + 7, 5))
            x += rect.width
        button_radius = 10
        y_center = 14
        vol_bar_width = 100
        vol_x = w - 130
        vol_rect = pygame.Rect(vol_x, y_center - 4, vol_bar_width, 8)
        pygame.draw.rect(self.screen, THEME["border"], vol_rect, border_radius=4)
        if not self.is_muted:
            vol_fill_rect = pygame.Rect(vol_x, y_center - 4, int(vol_bar_width * self.volume), 8)
            pygame.draw.rect(self.screen, THEME["sidebar_accent"], vol_fill_rect, border_radius=4)
        status_x = w - 280
        vis_status = "" if self.visualizer_enabled else ""
        vis_color = THEME["purple_dark"] if self.visualizer_enabled else THEME["text_dim"]
        vis_text = self.font_manager.get_font(11, bold=True).render(vis_status, True, vis_color)
        self.screen.blit(vis_text, (status_x, 8))
        button_start_x = vol_x - 150
        play_icon = ">" if self.is_paused else "''"
        buttons = [
            ("prev", "«", button_start_x),
            ("play", play_icon, button_start_x + 40),
            ("next", "»", button_start_x + 80)
        ]
        self.ctrl_rects = {}
        for key, label, btn_x in buttons:
            btn_rect = pygame.Rect(btn_x - button_radius, y_center - button_radius, 
                                 button_radius * 2, button_radius * 2)
            self.ctrl_rects[key] = btn_rect
            
            is_hover = btn_rect.collidepoint(mouse_pos)
            
            if is_hover:
                glow_size = button_radius + 5
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, THEME["glow"], (glow_size, glow_size), glow_size)
                self.screen.blit(glow_surf, (btn_x - glow_size, y_center - glow_size))
            
            for i in range(button_radius):
                alpha = 255 - (i * 20)
                color = (
                    THEME["button_gradient_start"][0] + (THEME["button_gradient_end"][0] - THEME["button_gradient_start"][0]) * (i/button_radius),
                    THEME["button_gradient_start"][1] + (THEME["button_gradient_end"][1] - THEME["button_gradient_start"][1]) * (i/button_radius),
                    THEME["button_gradient_start"][2] + (THEME["button_gradient_end"][2] - THEME["button_gradient_start"][2]) * (i/button_radius)
                )
                pygame.draw.circle(self.screen, color, (btn_x, y_center), button_radius - i)
            
            border_color = THEME["purple_dark"] if is_hover else THEME["blurple"]
            pygame.draw.circle(self.screen, border_color, (btn_x, y_center), button_radius, 1)
            
            label_color = THEME["accent"] if is_hover else THEME["text"]
            button_font = self.font_manager.get_font(14, bold=True)
            
            label_surf = button_font.render(label, True, label_color)
            self.screen.blit(label_surf, (btn_x - label_surf.get_width() // 2, 
                                        y_center - label_surf.get_height() // 2))
    
        self.ctrl_rects["vol"] = vol_rect

    def draw_preferences(self):
        if not self.show_preferences: return
        pref_rect = pygame.Rect(50, 50, 400, 200)
        pygame.draw.rect(self.screen, THEME["menu_bg"], pref_rect)
        pygame.draw.rect(self.screen, THEME["accent"], pref_rect, 1)
        
        self.draw_text(self.screen, "PREFERENCES", (pref_rect.x + 20, pref_rect.y + 20), THEME["accent"], bold=True)
        
        path_label = f"LIBRARY_PATH: {self.library.base_path if self.library.base_path else 'NOT_SET'}"
        path_rect = pygame.Rect(pref_rect.x + 20, pref_rect.y + 60, 360, 30)
        
        mouse_pos = pygame.mouse.get_pos()
        hover = path_rect.collidepoint(mouse_pos)
        color = THEME["search_accent"] if hover else THEME["text"]
        
        pygame.draw.rect(self.screen, THEME["bg"], path_rect)
        if hover:
            pygame.draw.rect(self.screen, THEME["accent"], path_rect, 1)
                
        self.draw_text(self.screen, path_label, (path_rect.x + 5, path_rect.y + 5), color)
        self.draw_text(self.screen, "(CLICK TO CHANGE)", (path_rect.x, path_rect.bottom + 5), THEME["text_dim"])
        
        self.draw_text(self.screen, "CLOSE [ESC]", (pref_rect.right - 80, pref_rect.bottom - 25), THEME["text_dim"])

    def draw_artist_sidebar(self, rect):
        pygame.draw.rect(self.screen, THEME["sidebar"], rect)
        pygame.draw.rect(self.screen, THEME["header_bg"], (rect.x, rect.y, rect.width, 22))
        self.draw_text(self.screen, "Artist / Album", (rect.x + 5, rect.y + 3), THEME["sidebar_accent"], bold=True)
        
        self.sidebar_sparkle.x = rect.x
        self.sidebar_sparkle.y = rect.y + 25
        self.sidebar_sparkle.width = rect.width
        self.sidebar_sparkle.height = rect.height - 25
        
        row_height = 18
        content_height = rect.height - 25
        self.max_visible_artists = content_height // row_height
        
        max_scroll = max(0, len(self.library.artists) - self.max_visible_artists)
        self.artist_scroll_offset = max(0, min(self.artist_scroll_offset, max_scroll))
        
        for i in range(self.max_visible_artists):
            artist_idx = i + self.artist_scroll_offset
            if artist_idx >= len(self.library.artists):
                break
                
            row_y = rect.y + 25 + (i * row_height)
            color = THEME["accent"] if artist_idx == self.selected_artist_idx else THEME["text"]
            artist_name = self.library.artists[artist_idx]['name']
            self.draw_text(self.screen, artist_name, (rect.x + 10, row_y), color, max_width=rect.width - 20)
        
        if len(self.library.artists) > self.max_visible_artists:
            scroll_pct = self.artist_scroll_offset / max(1, len(self.library.artists) - self.max_visible_artists)
            scrollbar_height = max(20, self.max_visible_artists * row_height * (self.max_visible_artists / len(self.library.artists)))
            scrollbar_y = rect.y + 25 + (content_height - scrollbar_height) * scroll_pct
            
            pygame.draw.rect(self.screen, THEME["border"], (rect.right - 4, rect.y + 25, 3, content_height))
            pygame.draw.rect(self.screen, THEME["sidebar_accent"], (rect.right - 4, scrollbar_y, 3, scrollbar_height))
        
        self.sidebar_sparkle.draw(self.screen)

    def draw_main_file_list(self, rect):
        actual_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
        if self.show_search:
            actual_rect.y += 40
            actual_rect.height -= 40

        pygame.draw.rect(self.screen, THEME["list_bg"], actual_rect)
        pygame.draw.rect(self.screen, THEME["header_bg"], (actual_rect.x, actual_rect.y, actual_rect.width, 22))
        
        col_t, col_a, col_al, col_d, col_s = (
            actual_rect.x + 35,
            actual_rect.x + 200,
            actual_rect.x + 320,
            actual_rect.right - 140,
            actual_rect.right - 60
        )
        
        mouse_pos = pygame.mouse.get_pos()
        
        title_rect = pygame.Rect(col_t - 5, actual_rect.y, 120, 22)
        title_color = THEME["accent"] if self.sort_column == 'name' else THEME["text_dim"]
        if title_rect.collidepoint(mouse_pos):
            title_color = THEME["search_accent"]
        self.draw_text(self.screen, "Track Title", (col_t, actual_rect.y + 3), title_color, bold=True)
        
        artist_rect = pygame.Rect(col_a - 5, actual_rect.y, 100, 22)
        artist_color = THEME["accent"] if self.sort_column == 'artist' else THEME["text_dim"]
        if artist_rect.collidepoint(mouse_pos):
            artist_color = THEME["search_accent"]
        self.draw_text(self.screen, "Artist", (col_a, actual_rect.y + 3), artist_color, bold=True)
        
        album_rect = pygame.Rect(col_al - 5, actual_rect.y, 120, 22)
        album_color = THEME["accent"] if self.sort_column == 'album' else THEME["text_dim"]
        if album_rect.collidepoint(mouse_pos):
            album_color = THEME["search_accent"]
        self.draw_text(self.screen, "Album", (col_al, actual_rect.y + 3), album_color, bold=True)
        
        duration_rect = pygame.Rect(col_d - 5, actual_rect.y, 70, 22)
        duration_color = THEME["accent"] if self.sort_column == 'duration' else THEME["text_dim"]
        if duration_rect.collidepoint(mouse_pos):
            duration_color = THEME["search_accent"]
        self.draw_text(self.screen, "Duration", (col_d, actual_rect.y + 3), duration_color, bold=True)
        
        size_rect = pygame.Rect(col_s - 5, actual_rect.y, 50, 22)
        size_color = THEME["accent"] if self.sort_column == 'size' else THEME["text_dim"]
        if size_rect.collidepoint(mouse_pos):
            size_color = THEME["search_accent"]
        self.draw_text(self.screen, "Size", (col_s, actual_rect.y + 3), size_color, bold=True)
        
        files = self.get_current_files()
        if self.sort_column:
            files = self.sort_files(files, self.sort_column, self.sort_reverse)
        
        visible_start = self.scroll_offset
        visible_end = min(len(files), visible_start + (actual_rect.height - 47) // 18)
        
        for i in range(visible_start, visible_end):
            row_y = actual_rect.y + 25 + ((i - visible_start) * 18)
            f = files[i]
            
            if f.get('title') is None:
                f = self.library.lazy_load_metadata(f)
            
            active = f['path'] == self.current_track
            queued = any(q['path'] == f['path'] for q in self.play_queue)
            
            if active:
                color = THEME["nowplaying"]
            elif queued:
                color = THEME["search_accent"]
            else:
                color = THEME["text"]
            
            duration_display = f.get('duration', "00:00")
            size_display = self.format_size(f.get('size', 0))
            
            display_title = f.get('title', f['name'])
            display_artist = f.get('artist', '')
            display_album = f.get('album', '')

            prefix = "▶" if active else "Q" if queued else f"{i+1:02d}"
            self.draw_text(self.screen, prefix, (actual_rect.x + 5, row_y), color)
            
            self.draw_text(self.screen, display_title, (col_t, row_y), color, max_width=150)
            self.draw_text(self.screen, display_artist, (col_a, row_y), color, max_width=100)
            self.draw_text(self.screen, display_album, (col_al, row_y), color, max_width=120)
            self.draw_text(self.screen, duration_display, (col_d, row_y), color)
            self.draw_text(self.screen, size_display, (col_s, row_y), color)
            
        pygame.draw.rect(self.screen, THEME["header_bg"], (actual_rect.x, actual_rect.bottom - 22, actual_rect.width, 22))
        queue_info = f" [Q:{len(self.play_queue)}]" if self.play_queue else ""
        self.draw_text(self.screen, f"Total Items: {len(files)}{queue_info}", (actual_rect.x + 10, actual_rect.bottom - 18), THEME["text_dim"])

    def draw_context_menu(self):
        if not self.show_context_menu or not self.context_menu_track:
            return
            
        menu_width = 200
        menu_height = len(self.context_menu_options) * 30 + 10
        x, y = self.context_menu_pos
        
        w, h = self.screen.get_size()
        if x + menu_width > w:
            x = w - menu_width
        if y + menu_height > h:
            y = h - menu_height
        
        menu_rect = pygame.Rect(x, y, menu_width, menu_height)
        
        pygame.draw.rect(self.screen, THEME["menu_bg"], menu_rect)
        pygame.draw.rect(self.screen, THEME["accent"], menu_rect, 1)
        
        mouse_pos = pygame.mouse.get_pos()
        for i, (text, _) in enumerate(self.context_menu_options):
            option_rect = pygame.Rect(x + 5, y + 5 + (i * 30), menu_width - 10, 25)
            
            if option_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, THEME["menu_hover"], option_rect)
            
            self.draw_text(self.screen, text, (x + 10, y + 10 + (i * 30)), THEME["text"])

    def handle_events(self):
        if WIN_MEDIA_KEYS:
            self.check_windows_media_keys()
            
        current_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.running = False
            
            if self.is_loading:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    click_color = THEME["accent"]
                    self.spawn_click_effect(mx, my, click_color)
                    self.click_sound.play()
                continue
            
            if event.type == pygame.MOUSEMOTION:
                self.needs_redraw = True
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                w, h = self.screen.get_size()
                
                if event.button in [4, 5]:
                    if event.button == 4:
                        if mx < 350 and 28 < my < h - 350:
                            self.artist_scroll_offset = max(0, self.artist_scroll_offset - 3)
                        else:
                            self.scroll_offset = max(0, self.scroll_offset - 3)
                    elif event.button == 5:
                        if mx < 350 and 28 < my < h - 350:
                            max_scroll = max(0, len(self.library.artists) - self.max_visible_artists)
                            self.artist_scroll_offset = min(max_scroll, self.artist_scroll_offset + 3)
                        else:
                            self.scroll_offset += 3
                    self.needs_redraw = True
                    continue
                
                if event.button == 1:
                    actual_rect = pygame.Rect(350, 28, w - 350, h - 200 - 28 - 30)
                    if self.show_search:
                        header_y = 68
                    else:
                        header_y = 28
                    
                    if 350 < mx < w and header_y < my < header_y + 22:
                        col_t, col_a, col_al, col_d, col_s = (
                            35, 200, 320, w - 350 - 140, w - 350 - 60
                        )
                        col_t += 350
                        col_a += 350
                        col_al += 350
                        col_d += 350
                        col_s += 350
                        
                        if col_t - 5 < mx < col_t + 115:
                            if self.sort_column == 'name':
                                self.sort_reverse = not self.sort_reverse
                            else:
                                self.sort_column = 'name'
                                self.sort_reverse = False
                            self.click_sound.play()
                            self.needs_redraw = True
                            
                        elif col_a - 5 < mx < col_a + 95:
                            if self.sort_column == 'artist':
                                self.sort_reverse = not self.sort_reverse
                            else:
                                self.sort_column = 'artist'
                                self.sort_reverse = False
                            self.click_sound.play()
                            self.needs_redraw = True
                            
                        elif col_al - 5 < mx < col_al + 115:
                            if self.sort_column == 'album':
                                self.sort_reverse = not self.sort_reverse
                            else:
                                self.sort_column = 'album'
                                self.sort_reverse = False
                            self.click_sound.play()
                            self.needs_redraw = True
                            
                        elif col_d - 5 < mx < col_d + 65:
                            if self.sort_column == 'duration':
                                self.sort_reverse = not self.sort_reverse
                            else:
                                self.sort_column = 'duration'
                                self.sort_reverse = False
                            self.click_sound.play()
                            self.needs_redraw = True
                            
                        elif col_s - 5 < mx < col_s + 45:
                            if self.sort_column == 'size':
                                self.sort_reverse = not self.sort_reverse
                            else:
                                self.sort_column = 'size'
                                self.sort_reverse = False
                            self.click_sound.play()
                            self.needs_redraw = True
                
                if self.show_context_menu:
                    menu_rect = pygame.Rect(self.context_menu_pos[0], self.context_menu_pos[1], 
                                          200, len(self.context_menu_options) * 30 + 10)
                    if not menu_rect.collidepoint(mx, my):
                        self.show_context_menu = False
                        self.needs_redraw = True
                
                visualizer_rect = pygame.Rect(350, h - 200, w - 350, 200)
                if visualizer_rect.collidepoint(mx, my):
                    self.visualizer.cycle_variant(clicked=True)
                    self.spawn_click_effect(mx, my, THEME["search_accent"])
                    continue
                
                if "play" in self.ctrl_rects and self.ctrl_rects["play"].collidepoint(mx, my):
                    if pygame.mixer.music.get_busy() or self.current_track is not None:
                        if self.is_paused:
                            pygame.mixer.music.unpause()
                            self.is_paused = False
                        else:
                            pygame.mixer.music.pause()
                            self.is_paused = True
                        if self.current_track:
                            files = self.get_current_files()
                            for f in files:
                                if f['path'] == self.current_track:
                                    if f.get('title') is None:
                                        f = self.library.lazy_load_metadata(f)
                                    self.discord.update(
                                        song=f.get('title', f['name']),
                                        artist=f.get('artist', 'Unknown Artist'),
                                        is_paused=self.is_paused,
                                        position=self.current_track_position,
                                        duration=self.track_length
                                    )
                                    break
                    else:
                        files = self.get_current_files()
                        if files:
                            self.play_file(files[0], 0)
                    self.click_sound.play()
                    self.spawn_click_effect(mx, my, THEME["blurple"])
                    self.needs_redraw = True
                    continue
                    
                if "prev" in self.ctrl_rects and self.ctrl_rects["prev"].collidepoint(mx, my):
                    self.skip_seconds(-5)
                    continue
                    
                if "next" in self.ctrl_rects and self.ctrl_rects["next"].collidepoint(mx, my):
                    self.skip_seconds(5)
                    continue
                
                if "vol" in self.ctrl_rects and self.ctrl_rects["vol"].collidepoint(mx, my):
                    vol_pct = (mx - self.ctrl_rects["vol"].x) / self.ctrl_rects["vol"].width
                    self.volume = max(0, min(1, vol_pct))
                    pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
                    self.click_sound.play()
                    self.spawn_click_effect(mx, my, THEME["sidebar_accent"])
                    self.needs_redraw = True
                    continue
                
                vol_icon_rect = pygame.Rect(w - 155, 6, 20, 20)
                if vol_icon_rect.collidepoint(mx, my):
                    self.is_muted = not self.is_muted
                    pygame.mixer.music.set_volume(0 if self.is_muted else self.volume)
                    self.click_sound.play()
                    self.spawn_click_effect(mx, my, THEME["sidebar_accent"])
                    self.needs_redraw = True
                    continue
                
                if event.button == 3:
                    files = self.get_current_files()
                    y_start = 53 if not self.show_search else 93
                    
                    if 350 < mx < w and y_start < my < h - 230:
                        idx = ((my - y_start) // 18) + self.scroll_offset
                        if 0 <= idx < len(files):
                            self.context_menu_track = files[idx]
                            self.context_menu_pos = (mx, my)
                            self.show_context_menu = True
                            self.click_sound.play()
                            self.needs_redraw = True
                            continue
                
                click_color = THEME["accent"]
                if mx < 350: 
                    click_color = THEME["accent_green"]
                elif self.show_search and 28 < my < 68: 
                    click_color = THEME["search_accent"]
                
                if not any([
                    "play" in self.ctrl_rects and self.ctrl_rects["play"].collidepoint(mx, my),
                    "prev" in self.ctrl_rects and self.ctrl_rects["prev"].collidepoint(mx, my),
                    "next" in self.ctrl_rects and self.ctrl_rects["next"].collidepoint(mx, my),
                    "vol" in self.ctrl_rects and self.ctrl_rects["vol"].collidepoint(mx, my),
                    vol_icon_rect.collidepoint(mx, my),
                    visualizer_rect.collidepoint(mx, my)
                ]):
                    self.spawn_click_effect(mx, my, click_color)
                    self.click_sound.play()
                    self.needs_redraw = True
                
                if event.button == 1 and self.show_context_menu:
                    menu_rect = pygame.Rect(self.context_menu_pos[0], self.context_menu_pos[1], 
                                          200, len(self.context_menu_options) * 30 + 10)
                    if menu_rect.collidepoint(mx, my):
                        option_index = (my - self.context_menu_pos[1] - 5) // 30
                        if 0 <= option_index < len(self.context_menu_options):
                            _, action = self.context_menu_options[option_index]
                            
                            if action == "queue":
                                if self.context_menu_track not in self.play_queue:
                                    self.play_queue.append(self.context_menu_track)
                                    logging.info(f"Added to queue: {self.context_menu_track['name']}")
                            elif action == "next":
                                self.play_queue.insert(0, self.context_menu_track)
                                logging.info(f"Playing next: {self.context_menu_track['name']}")
                            elif action == "open":
                                path = self.context_menu_track['path']
                                if "::" in path:
                                    zp, _ = path.split("::")
                                    path = zp
                                
                                if os.path.exists(path):
                                    try:
                                        if sys.platform == "win32":
                                            os.startfile(os.path.dirname(path))
                                        elif sys.platform == "darwin":
                                            subprocess.run(["open", os.path.dirname(path)])
                                        else:
                                            subprocess.run(["xdg-open", os.path.dirname(path)])
                                    except Exception as e:
                                        logging.error(f"Failed to open file location: {e}")
                            
                            self.show_context_menu = False
                            self.click_sound.play()
                            self.needs_redraw = True
                            continue
                
                if my < 28:
                    x_offset = 10
                    for m, func in self.menus:
                        menu_font = self.font_manager.get_font(13, bold=False)
                        rect = pygame.Rect(x_offset, 0, menu_font.size(m)[0] + 15, 28)
                        if rect.collidepoint(mx, my):
                            if func: 
                                func()
                                self.click_sound.play()
                                self.needs_redraw = True
                            break
                        x_offset += rect.width
                    continue

                if self.show_preferences:
                    pref_rect = pygame.Rect(50, 50, 400, 200)
                    path_rect = pygame.Rect(pref_rect.x + 20, pref_rect.y + 60, 360, 30)
                    if path_rect.collidepoint(mx, my):
                        self.library.select_and_update_path()
                        self.show_preferences = False
                        self.click_sound.play()
                        self.needs_redraw = True
                    elif not pref_rect.collidepoint(mx, my):
                        self.show_preferences = False
                        self.needs_redraw = True
                    continue
                    
                if mx < 350 and 28 < my < h - 350:
                    row_height = 18
                    idx = ((my - 53) // row_height) + self.artist_scroll_offset
                    if 0 <= idx < len(self.library.artists): 
                        self.selected_artist_idx = idx
                        self.scroll_offset = 0
                        self.return_to_library = True
                        self.click_sound.play()
                        self.needs_redraw = True
                        
                elif 350 < mx < w and (28 if not self.show_search else 68) < my < h - 230:
                    files = self.get_current_files()
                    y_start = 53 if not self.show_search else 93
                    idx = ((my - y_start) // 18) + self.scroll_offset
                    if 0 <= idx < len(files):
                        now = time.time()
                        if now - self.last_click_time < 0.4 and self.click_target == idx: 
                            self.play_file(files[idx], idx)
                            self.click_sound.play()
                            self.needs_redraw = True
                        self.last_click_time, self.click_target = now, idx
            
            if event.type == pygame.KEYDOWN:
                if not hasattr(self, 'last_key_time'):
                    self.last_key_time = 0
                    self.last_key = None
                
                current_time = time.time()
                debounce_delay = 0.25
                
                is_repeat = (event.key == self.last_key and 
                           current_time - self.last_key_time < debounce_delay)
                
                self.last_key_time = current_time
                self.last_key = event.key
                
                if is_repeat:
                    continue
                    
                if event.key == pygame.K_l and (event.mod & pygame.KMOD_CTRL):
                    self.lyrics_window.toggle()
                    self.needs_redraw = True
                
                if event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                    self.toggle_visualizer()
                elif event.key == pygame.K_ESCAPE:
                    if self.show_preferences: 
                        self.show_preferences = False
                        self.click_sound.play()
                        self.needs_redraw = True
                    elif self.show_context_menu:
                        self.show_context_menu = False
                        self.click_sound.play()
                        self.needs_redraw = True
                    elif self.show_search:
                        self.return_to_library = True
                        self.show_search = False
                        self.search_query = ""
                        self.pending_search = None
                        self.click_sound.play()
                        self.needs_redraw = True
                elif event.mod & pygame.KMOD_CTRL and event.key == pygame.K_f: 
                    self.toggle_search()
                elif self.show_search:
                    self.handle_search_input(event)
                elif event.key == pygame.K_SPACE:
                    if pygame.mixer.music.get_busy() or self.current_track is not None:
                        if self.is_paused:
                            pygame.mixer.music.unpause()
                            self.is_paused = False
                        else:
                            pygame.mixer.music.pause()
                            self.is_paused = True
                        
                        # Update Discord with pause state
                        if self.current_track:
                            files = self.get_current_files()
                            for f in files:
                                if f['path'] == self.current_track:
                                    if f.get('title') is None:
                                        f = self.library.lazy_load_metadata(f)
                                    self.discord.update(
                                        song=f.get('title', f['name']),
                                        artist=f.get('artist', 'Unknown Artist'),
                                        is_paused=self.is_paused,
                                        position=self.current_track_position,
                                        duration=self.track_length
                                    )
                                    break
                        
                        self.click_sound.play()
                        self.needs_redraw = True
                        if "play" in self.ctrl_rects:
                            play_rect = self.ctrl_rects["play"]
                            self.spawn_click_effect(play_rect.centerx, play_rect.centery, THEME["accent"])
                    else:
                        files = self.get_current_files()
                        if files:
                            self.play_file(files[0], 0)
                            self.click_sound.play()
                            self.needs_redraw = True
                elif event.key == pygame.K_LEFT:
                    self.skip_seconds(-5)
                elif event.key == pygame.K_RIGHT:
                    self.skip_seconds(5)
                elif event.key == pygame.K_n:
                    self.play_next_track()
        
        self.check_pending_search()
        
        if current_time - self.last_particle_update >= self.particle_update_interval:
            self.last_particle_update = current_time
            
            particles_updated = False
            if self.particles:
                self.particles = [p for p in self.particles if p.update()]
                particles_updated = True
            
            if self.ascii_particles:
                self.ascii_particles = [p for p in self.ascii_particles if p.update()]
                particles_updated = True
            
            if particles_updated:
                self.needs_redraw = True
        
        if current_time - self.last_sparkle_update >= self.sparkle_update_interval:
            self.last_sparkle_update = current_time
            
            self.sidebar_sparkle.update()
            self.title_sparkle.update()
            self.needs_redraw = True

    def run(self):
        self.running = True
        last_check = time.time()
        last_position_update = time.time()
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_check > 0.5:
                last_check = current_time
                if not self.is_paused and not pygame.mixer.music.get_busy() and self.current_track:
                    pygame.time.wait(100)
                    if not pygame.mixer.music.get_busy():
                        self.play_next_track()
            self.handle_events()  
            self.lyrics_window.update() 
            try:
                self.tk_root.update()
            except:
                pass
            if not self.is_paused and pygame.mixer.music.get_busy() and not self.is_skipping:
                pos = pygame.mixer.music.get_pos() / 1000.0
                expected_pos = self.current_track_position + (time.time() - last_position_update)
                if abs(pos - expected_pos) > 2.0:
                    pass
                elif abs(pos - self.current_track_position) > 0.1:
                    self.current_track_position = pos
            last_position_update = time.time()
            if current_time - getattr(self, 'last_discord_update', 0) > 5.0:
                self.last_discord_update = current_time
                if self.current_track:
                    files = self.get_current_files()
                    for f in files:
                        if f['path'] == self.current_track:
                            if f.get('title') is None:
                                f = self.library.lazy_load_metadata(f)
                            self.discord.update(
                                song=f.get('title', f['name']),
                                artist=f.get('artist', 'Unknown Artist'),
                                is_paused=self.is_paused,
                                position=self.current_track_position,
                                duration=self.track_length
                            )
                            break
            if self.is_loading: 
                self.is_loading = self.loader.draw()
            else:
                w, h = self.screen.get_size()
                sidebar_w, menu_h, v_h, art_h = 350, 28, 200, 350
                self.screen.fill(THEME["bg"])
                self.title_sparkle.x = 400
                self.title_sparkle.y = 30
                self.title_sparkle.width = 400
                self.title_sparkle.height = 50
                self.draw_menu_bar()
                self.draw_artist_sidebar(pygame.Rect(0, menu_h, sidebar_w, h - art_h - menu_h))
                self.draw_main_file_list(pygame.Rect(sidebar_w, menu_h, w - sidebar_w, h - v_h - menu_h - 30))
                if self.visualizer_enabled:
                    self.visualizer.update_auto_cycle()
                    self.visualizer.draw(self.screen, pygame.Rect(sidebar_w, h - v_h, w - sidebar_w, v_h))
                else:
                    visualizer_rect = pygame.Rect(sidebar_w, h - v_h, w - sidebar_w, v_h)
                    pygame.draw.rect(self.screen, (0, 0, 0), visualizer_rect)
                    pygame.draw.rect(self.screen, THEME["border"], visualizer_rect, 1)
                    self.draw_text(self.screen, "VISUALIZER DISABLED [CTRL+V TO TOGGLE]", 
                                  (visualizer_rect.centerx - 180, visualizer_rect.centery - 10),
                                  THEME["text_dim"], bold=True)
                if self.show_search:
                    search_rect = pygame.Rect(sidebar_w, menu_h, w - sidebar_w, 40)
                    pygame.draw.rect(self.screen, THEME["menu_bg"], search_rect)
                    pygame.draw.line(self.screen, THEME["blurple"], (sidebar_w, menu_h+39), (w, menu_h+39), 2)
                    display_query = self.search_query if self.search_query else "_"
                    self.draw_text(self.screen, f" SEARCH_NODES: {display_query}_", (sidebar_w + 15, menu_h + 12), THEME["search_accent"], bold=True)
                art_rect = pygame.Rect(0, h - art_h, sidebar_w, art_h)
                pygame.draw.rect(self.screen, (5, 5, 10), art_rect)
                pygame.draw.rect(self.screen, THEME["border"], art_rect, 1)
                if self.current_track:
                    current_file = None
                    files = self.get_current_files()
                    for f in files:
                        if f['path'] == self.current_track:
                            current_file = f
                            break
                    if current_file and current_file.get('title') is None:
                        current_file = self.library.lazy_load_metadata(current_file)
                    art = self.library.get_album_art(self.current_track)
                    if art:
                        r = min(sidebar_w/art.get_width(), art_h/art.get_height())
                        scaled = pygame.transform.smoothscale(art, (int(art.get_width()*r), int(art.get_height()*r)))
                        self.screen.blit(scaled, (art_rect.x + (sidebar_w-scaled.get_width())//2, art_rect.y + (art_h-scaled.get_height())//2))
                    else:
                        pygame.draw.rect(self.screen, THEME["purple_dark"], 
                                       (art_rect.x + 10, art_rect.y + 10, art_rect.width - 20, art_rect.height - 20))
                        pygame.draw.rect(self.screen, THEME["blurple"], 
                                       (art_rect.x + 10, art_rect.y + 10, art_rect.width - 20, art_rect.height - 20), 2)
                        self.draw_text(self.screen, "NO ART", 
                                     (art_rect.centerx - 30, art_rect.centery - 10), 
                                     THEME["text_dim"], bold=True)
                else:
                    self.draw_text(self.screen, "NO_DATA_STREAM", 
                                 (art_rect.centerx - 50, art_rect.centery), 
                                 THEME["text_dim"])
                self.draw_preferences()
                self.draw_context_menu()
                self.title_sparkle.draw(self.screen)
                for p in self.particles: 
                    p.draw(self.screen)
                for p in self.ascii_particles:
                    p.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
        self.library.save_cache()
        self.discord.disconnect()
        pygame.quit()
if __name__ == "__main__":
    try:
        import mutagen
    except ImportError:
        print("Installing mutagen for audio metadata support...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mutagen"])
        import mutagen
    App().run()