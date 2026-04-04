import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import yt_dlp
import vlc
from PIL import Image, ImageTk
import requests
from io import BytesIO
import re
import json
import os
import time

class YouTubePlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom YouTube Player")
        self.root.geometry("1400x800")
        self.root.minsize(1000, 600)

        # VLC instance and player
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.is_playing = False
        self.current_video_id = None
        self.current_stream_url = None
        self.volume = 70
        self.player.audio_set_volume(self.volume)

        # Queue list
        self.queue = []  # list of dicts {'id': video_id, 'title': title}
        self.queue_index = 0  # not used; we pop from front

        # Search data
        self.search_results = []
        self.current_search_cancel = False
        self.thumbnail_threads = []

        # Load theme
        self.current_theme = "default"
        self.theme_colors = {}
        self.theme_fonts = {}
        self.load_theme()

        # Build UI
        self.create_widgets()
        self.setup_controls()

        # Start with a default search
        self.root.after(100, lambda: self.search_videos("Python programming"))

        # Update seek bar periodically
        self.update_seek_bar()

    # ------------------- Theming -------------------
    def load_theme(self, theme_name="default"):
        theme_path = os.path.join("Theme", f"{theme_name}.json")
        if not os.path.exists(theme_path):
            theme_path = os.path.join("Theme", "default.json")
        try:
            with open(theme_path, "r") as f:
                theme = json.load(f)
            self.theme_colors = theme["colors"]
            self.theme_fonts = theme["fonts"]
        except:
            # Fallback hardcoded theme
            self.theme_colors = {
                "bg": "#0f0f0f", "fg": "#ffffff", "accent": "#3ea6ff",
                "button_bg": "#3ea6ff", "button_fg": "#000000",
                "entry_bg": "#121212", "entry_fg": "#ffffff",
                "listbox_bg": "#121212", "listbox_fg": "#ffffff",
                "error_fg": "#ff4444", "status_bg": "#121212", "status_fg": "#aaaaaa"
            }
            self.theme_fonts = {"default": "Arial 10", "title": "Arial 12 bold", "comment": "Arial 9"}
        self.apply_theme()

    def apply_theme(self):
        self.root.configure(bg=self.theme_colors["bg"])
        # Recursively apply to existing widgets (simplified: just set on main frames)
        # We'll set colors when creating widgets; this is for dynamic switching later
        # For now, we just set at creation time.

    # ------------------- UI Creation -------------------
    def create_widgets(self):
        # Top search bar
        top_frame = tk.Frame(self.root, bg=self.theme_colors["bg"])
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.search_entry = tk.Entry(top_frame, font=self.theme_fonts["default"], 
                                     bg=self.theme_colors["entry_bg"], fg=self.theme_colors["entry_fg"],
                                     insertbackground=self.theme_colors["entry_fg"])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.search_entry.bind("<Return>", lambda e: self.search_videos())

        self.search_btn = tk.Button(top_frame, text="Search", command=self.search_videos,
                                    bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"],
                                    font=("Arial",10,"bold"))
        self.search_btn.pack(side=tk.RIGHT)

        # Main paned window: left (video+comments) and right (thumbnails)
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=self.theme_colors["bg"],
                                   sashrelief=tk.RAISED, sashwidth=5)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left side: Video area + controls + comments
        left_frame = tk.Frame(main_pane, bg=self.theme_colors["bg"])
        main_pane.add(left_frame, width=800)

        # Video player frame
        self.video_frame = tk.Frame(left_frame, bg="black", width=800, height=450)
        self.video_frame.pack(fill=tk.BOTH, expand=False, pady=(0,5))
        self.video_frame.pack_propagate(False)

        # Control bar (buttons, sliders)
        self.controls_frame = tk.Frame(left_frame, bg=self.theme_colors["bg"])
        self.controls_frame.pack(fill=tk.X, pady=5)

        # Comments area
        comments_label = tk.Label(left_frame, text="Comments", font=self.theme_fonts["title"],
                                  bg=self.theme_colors["bg"], fg=self.theme_colors["fg"], anchor="w")
        comments_label.pack(fill=tk.X, pady=(5,5))

        self.comments_text = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD,
                                                       bg=self.theme_colors["entry_bg"],
                                                       fg=self.theme_colors["entry_fg"],
                                                       font=self.theme_fonts["comment"])
        self.comments_text.pack(fill=tk.BOTH, expand=True)

        # Right side: Thumbnail grid + Queue
        right_frame = tk.Frame(main_pane, bg=self.theme_colors["bg"])
        main_pane.add(right_frame, width=450)

        # Notebook (tabs) for Search Results and Queue
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Search Results (thumbnails)
        self.search_tab = tk.Frame(self.notebook, bg=self.theme_colors["bg"])
        self.notebook.add(self.search_tab, text="Search Results")

        # Scrollable canvas for thumbnails
        self.canvas = tk.Canvas(self.search_tab, bg=self.theme_colors["bg"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.search_tab, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.theme_colors["bg"])
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Tab 2: Queue
        self.queue_tab = tk.Frame(self.notebook, bg=self.theme_colors["bg"])
        self.notebook.add(self.queue_tab, text="Queue")

        self.queue_listbox = tk.Listbox(self.queue_tab, bg=self.theme_colors["listbox_bg"],
                                        fg=self.theme_colors["listbox_fg"],
                                        font=self.theme_fonts["default"])
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        queue_scroll = tk.Scrollbar(self.queue_tab, command=self.queue_listbox.yview)
        queue_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=queue_scroll.set)
        self.queue_listbox.bind("<Double-Button-1>", self.play_from_queue)

        # Queue control buttons
        queue_btn_frame = tk.Frame(self.queue_tab, bg=self.theme_colors["bg"])
        queue_btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        tk.Button(queue_btn_frame, text="Remove Selected", command=self.remove_from_queue,
                  bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"]).pack(side=tk.LEFT, padx=2)
        tk.Button(queue_btn_frame, text="Play Next", command=self.play_next_from_queue,
                  bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"]).pack(side=tk.LEFT, padx=2)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
                              anchor=tk.W, bg=self.theme_colors["status_bg"], fg=self.theme_colors["status_fg"])
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_controls(self):
        # Play/Pause button
        self.play_pause_btn = tk.Button(self.controls_frame, text="⏸" if self.is_playing else "▶",
                                        command=self.toggle_play_pause, width=3,
                                        bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"])
        self.play_pause_btn.pack(side=tk.LEFT, padx=2)

        # Seek bar (Scale)
        self.seek_var = tk.DoubleVar()
        self.seek_bar = tk.Scale(self.controls_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                 variable=self.seek_var, command=self.seek, length=400,
                                 bg=self.theme_colors["bg"], highlightthickness=0)
        self.seek_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        # Time label
        self.time_label = tk.Label(self.controls_frame, text="00:00 / 00:00",
                                   bg=self.theme_colors["bg"], fg=self.theme_colors["fg"])
        self.time_label.pack(side=tk.LEFT, padx=5)

        # Volume label and slider
        vol_label = tk.Label(self.controls_frame, text="Vol", bg=self.theme_colors["bg"], fg=self.theme_colors["fg"])
        vol_label.pack(side=tk.LEFT, padx=(10,2))
        self.volume_var = tk.IntVar(value=self.volume)
        self.volume_slider = tk.Scale(self.controls_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      variable=self.volume_var, command=self.change_volume, length=100,
                                      bg=self.theme_colors["bg"], highlightthickness=0)
        self.volume_slider.pack(side=tk.LEFT, padx=2)

        # Fullscreen button
        self.fullscreen_btn = tk.Button(self.controls_frame, text="⛶", command=self.toggle_fullscreen,
                                        width=3, bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"])
        self.fullscreen_btn.pack(side=tk.RIGHT, padx=2)

    # ------------------- Queue Functions -------------------
    def add_to_queue(self, video_id, title):
        self.queue.append({"id": video_id, "title": title})
        self.queue_listbox.insert(tk.END, title)
        self.status_var.set(f"Added to queue: {title[:50]}")

    def remove_from_queue(self):
        selected = self.queue_listbox.curselection()
        if selected:
            idx = selected[0]
            self.queue.pop(idx)
            self.queue_listbox.delete(idx)

    def play_next_from_queue(self):
        if self.queue:
            next_video = self.queue.pop(0)
            self.queue_listbox.delete(0)
            self.load_video(next_video["id"])
            self.status_var.set(f"Playing next from queue: {next_video['title'][:50]}")
        else:
            self.status_var.set("Queue is empty")

    def play_from_queue(self, event):
        selected = self.queue_listbox.curselection()
        if selected:
            idx = selected[0]
            video = self.queue[idx]
            # Remove from queue if you want (or keep)
            self.queue.pop(idx)
            self.queue_listbox.delete(idx)
            self.load_video(video["id"])

    # ------------------- Video Playback Controls -------------------
    def toggle_play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.is_playing = False
            self.play_pause_btn.config(text="▶")
        else:
            self.player.play()
            self.is_playing = True
            self.play_pause_btn.config(text="⏸")

    def change_volume(self, val):
        self.volume = int(val)
        self.player.audio_set_volume(self.volume)

    def seek(self, value):
        if self.player.get_length() > 0:
            pos = int(float(value) / 100 * self.player.get_length())
            self.player.set_time(pos)

    def update_seek_bar(self):
        if self.player.is_playing():
            length = self.player.get_length()
            if length > 0:
                current = self.player.get_time()
                percent = (current / length) * 100
                self.seek_var.set(percent)
                # Update time labels
                cur_str = time.strftime('%M:%S', time.gmtime(current//1000))
                tot_str = time.strftime('%M:%S', time.gmtime(length//1000))
                self.time_label.config(text=f"{cur_str} / {tot_str}")
        self.root.after(1000, self.update_seek_bar)

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))
        # Adjust video frame size? VLC handles it if we set window size
        # Just force a resize event
        self.video_frame.update_idletasks()
        # Re-embed player (optional)
        self.player.set_hwnd(self.video_frame.winfo_id())

    # ------------------- Thumbnail Grid -------------------
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def search_videos(self, query=None):
        if query is None:
            query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("No query", "Please enter a search term.")
            return

        self.current_search_cancel = True
        self.root.after(50, lambda: self._do_search(query))

    def _do_search(self, query):
        self.status_var.set(f"Searching for '{query}'...")
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.search_results = []
        self.current_search_cancel = False

        def do_search():
            try:
                ydl_opts = {'quiet': True, 'extract_flat': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_query = f"ytsearch20:{query}"
                    info = ydl.extract_info(search_query, download=False)
                    entries = info.get('entries', [])
                    for entry in entries:
                        video_id = entry.get('id')
                        title = entry.get('title', 'No title')
                        thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
                        self.search_results.append({
                            'id': video_id,
                            'title': title,
                            'thumb_url': thumb_url,
                        })
                    self.root.after(0, lambda: self.display_thumbnails())
                    self.root.after(0, lambda: self.status_var.set(f"Found {len(self.search_results)} videos."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Search Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Search failed."))

        threading.Thread(target=do_search, daemon=True).start()

    def display_thumbnails(self):
        cols = 2
        for idx, video in enumerate(self.search_results):
            if self.current_search_cancel:
                break
            row = idx // cols
            col = idx % cols

            item_frame = tk.Frame(self.scrollable_frame, bg=self.theme_colors["bg"], cursor="hand2")
            item_frame.grid(row=row, column=col, padx=5, pady=5, sticky="n")
            video['frame'] = item_frame

            # Placeholder
            loading_label = tk.Label(item_frame, text="Loading...", bg=self.theme_colors["bg"], fg="gray")
            loading_label.pack()

            # Thread to load thumbnail
            def load_thumb(vid, frame, lbl):
                if self.current_search_cancel:
                    return
                try:
                    response = requests.get(vid['thumb_url'], timeout=5)
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((180, 100), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.root.after(0, lambda: self._safe_add_thumbnail(vid, frame, lbl, photo))
                except Exception:
                    self.root.after(0, lambda: self._safe_add_error(frame, lbl))

            t = threading.Thread(target=load_thumb, args=(video, item_frame, loading_label), daemon=True)
            t.start()
            self.thumbnail_threads.append(t)

            # Title label (under thumbnail)
            title_text = video['title']
            if len(title_text) > 50:
                title_text = title_text[:47] + "..."
            title_label = tk.Label(item_frame, text=title_text, bg=self.theme_colors["bg"],
                                   fg=self.theme_colors["fg"], wraplength=180, justify="center",
                                   font=("Arial",9))
            title_label.pack()
            title_label.bind("<Button-1>", lambda e, vid_id=video['id']: self.on_thumbnail_click(vid_id))

            # "Add to Queue" button below title
            add_btn = tk.Button(item_frame, text="+ Queue", command=lambda vid_id=video['id'], ttl=video['title']: self.add_to_queue(vid_id, ttl),
                                bg=self.theme_colors["button_bg"], fg=self.theme_colors["button_fg"],
                                font=("Arial",8))
            add_btn.pack(pady=2)

    def _safe_add_thumbnail(self, video, frame, loading_label, photo):
        if self.current_search_cancel:
            return
        try:
            if frame.winfo_exists():
                loading_label.destroy()
                thumb_label = tk.Label(frame, image=photo, bg=self.theme_colors["bg"])
                thumb_label.image = photo
                thumb_label.pack()
                thumb_label.bind("<Button-1>", lambda e, vid_id=video['id']: self.on_thumbnail_click(vid_id))
                video['thumbnail_image'] = photo
        except tk.TclError:
            pass

    def _safe_add_error(self, frame, loading_label):
        if self.current_search_cancel:
            return
        try:
            if frame.winfo_exists():
                loading_label.destroy()
                error_label = tk.Label(frame, text="[Error]", bg=self.theme_colors["bg"], fg=self.theme_colors["error_fg"])
                error_label.pack()
        except tk.TclError:
            pass

    def on_thumbnail_click(self, video_id):
        video = next((v for v in self.search_results if v['id'] == video_id), None)
        title = video['title'] if video else "video"
        self.status_var.set(f"Loading video: {title}")
        self.load_video(video_id)
        self.load_comments(video_id)

    # ------------------- Video Loading & Playback -------------------
    def load_video(self, video_id):
        self.current_video_id = video_id
        def get_stream():
            try:
                ydl_opts = {
                    'format': 'best[ext=mp4]/best',
                    'quiet': True,
                    'no_warnings': True,
                    'sponsorblock_remove': 'all',
                    'extractor_args': {
                        'youtube': {
                            'skip': ['hls', 'dash'],   # <-- Try adding this line first
                            'player_client': ['android', 'web'],
                            'remote_components': ['ejs:github']  # <-- This tells it to fetch the solver
                        }
                    },
                }
                url = f"https://www.youtube.com/watch?v={video_id}"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    stream_url = info['url']
                    title = info.get('title', 'YouTube Video')
                    self.root.after(0, lambda: self.play_stream(stream_url, title))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Playback Error", str(e)))
                self.root.after(0, lambda: self.status_var.set("Playback failed."))

        threading.Thread(target=get_stream, daemon=True).start()

    def play_stream(self, stream_url, title):
        self.player.stop()
        media = self.vlc_instance.media_new(stream_url)
        self.player.set_media(media)
        self.player.set_hwnd(self.video_frame.winfo_id())
        self.player.play()
        self.is_playing = True
        self.play_pause_btn.config(text="⏸")
        self.status_var.set(f"Now playing: {title}")
        # Reset seek bar
        self.seek_var.set(0)

    # ------------------- Comments -------------------
    def load_comments(self, video_id):
        self.comments_text.delete(1.0, tk.END)
        self.comments_text.insert(tk.END, "Loading comments...\n")
        self.status_var.set("Fetching comments...")

        def fetch_comments():
            try:
                url = f"https://www.youtube.com/watch?v={video_id}"
                ydl_opts = {'quiet': True, 'getcomments': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    comments = info.get('comments', [])
                    if not comments:
                        self.root.after(0, lambda: self.comments_text.delete(1.0, tk.END))
                        self.root.after(0, lambda: self.comments_text.insert(tk.END, "No comments found.\n"))
                        return
                    self.root.after(0, lambda: self.comments_text.delete(1.0, tk.END))
                    for comment in comments[:50]:
                        author = comment.get('author', 'Anonymous')
                        text = comment.get('text', '')
                        text = re.sub(r'<.*?>', '', text)
                        self.root.after(0, lambda a=author, t=text: self.comments_text.insert(tk.END, f"{a}:\n{t}\n\n"))
                    self.root.after(0, lambda: self.status_var.set(f"Loaded {len(comments[:50])} comments."))
            except Exception as e:
                self.root.after(0, lambda: self.comments_text.delete(1.0, tk.END))
                self.root.after(0, lambda: self.comments_text.insert(tk.END, f"Error loading comments: {str(e)}\n"))
                self.root.after(0, lambda: self.status_var.set("Comment fetch failed."))

        threading.Thread(target=fetch_comments, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubePlayer(root)
    root.mainloop()