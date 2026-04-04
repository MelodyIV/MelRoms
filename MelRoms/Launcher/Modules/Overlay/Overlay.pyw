#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import threading
import subprocess
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Error: Run 'pip install psutil' in terminal.")
    sys.exit(1)

try:
    import tkinter as tk
except ImportError:
    print("Error: tkinter not available.")
    sys.exit(1)

try:
    import pygetwindow as gw
except ImportError:
    print("Warning: 'pip install pygetwindow' for auto‑hide feature.")
    gw = None

try:
    from ping3 import ping
    PING_AVAILABLE = True
except ImportError:
    PING_AVAILABLE = False

# GPU detection
try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

try:
    import pyadl
    PYADL_AVAILABLE = True
except ImportError:
    PYADL_AVAILABLE = False

# ----- Subtle Cyber Colors -----
BG_DARK = "#0a0e17"
FG_CYAN = "#00e5ff"
FG_PURPLE = "#b77cff"
BG_PANEL = "#111520"


def get_gpu_usage():
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=2,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except:
        pass

    if GPUTIL_AVAILABLE:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                return int(gpus[0].load * 100)
        except:
            pass

    if PYADL_AVAILABLE:
        try:
            devices = pyadl.ADLManager.getInstance().getDevices()
            if devices:
                return devices[0].getCurrentUsage()
        except:
            pass

    return None


class MikuOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Miku System Monitor")
        self.root.geometry("280x185")
        self.root.configure(bg=BG_DARK)
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 0.92)

        self.visible = True
        self.target_process = None
        self.ping_target = "8.8.8.8"
        self.last_ping = 0
        self.cpu_count = psutil.cpu_count(logical=True)

        # Network tracking
        self.last_net_sent = 0
        self.last_net_recv = 0
        self.last_net_time = 0

        # GPU availability
        self.gpu_available = get_gpu_usage() is not None
        if self.gpu_available:
            print("GPU detected")
        else:
            print("No compatible GPU found")

        self.create_widgets()
        self.setup_drag()
        self.setup_hotkey()
        self.update_stats()
        self.root.mainloop()

    def create_widgets(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        title_bar = tk.Frame(main, bg=BG_PANEL, height=20)
        title_bar.pack(fill=tk.X, pady=(0, 6))
        title_bar.pack_propagate(False)

        # Left side: draggable area (icon + text)
        drag_area = tk.Frame(title_bar, bg=BG_PANEL)
        drag_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        drag_area.bind("<Button-1>", self.start_move)
        drag_area.bind("<B1-Motion>", self.on_move)

        tk.Label(drag_area, text="⚡", bg=BG_PANEL, fg=FG_CYAN, font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
        tk.Label(drag_area, text="MONITOR", bg=BG_PANEL, fg=FG_PURPLE, font=("Consolas", 8, "bold")).pack(side=tk.LEFT)

        # Right side: close button (kills the overlay)
        close_btn = tk.Label(title_bar, text="✕", bg=BG_PANEL, fg=FG_PURPLE, font=("Consolas", 10, "bold"))
        close_btn.pack(side=tk.RIGHT, padx=5)
        # Bind close without interfering with drag
        close_btn.bind("<Button-1>", lambda e: self.quit())
        # Prevent drag from triggering when clicking close button
        close_btn.bind("<Button-1>", lambda e: None, add="+")  # optional, but fine

        self.cpu_label = tk.Label(main, text="CPU: --%", bg=BG_DARK, fg=FG_CYAN, font=("Consolas", 9), anchor="w")
        self.cpu_label.pack(fill=tk.X, pady=1)

        self.top_cpu_label = tk.Label(main, text="TOP: --", bg=BG_DARK, fg=FG_PURPLE, font=("Consolas", 8), anchor="w")
        self.top_cpu_label.pack(fill=tk.X, pady=1)

        self.ram_label = tk.Label(main, text="RAM: -- / -- GB", bg=BG_DARK, fg=FG_CYAN, font=("Consolas", 9), anchor="w")
        self.ram_label.pack(fill=tk.X, pady=1)

        if self.gpu_available:
            self.gpu_label = tk.Label(main, text="GPU: --%", bg=BG_DARK, fg=FG_CYAN, font=("Consolas", 9), anchor="w")
            self.gpu_label.pack(fill=tk.X, pady=1)

        self.net_label = tk.Label(main, text="NET: ↓-- ↑--", bg=BG_DARK, fg=FG_CYAN, font=("Consolas", 9), anchor="w")
        self.net_label.pack(fill=tk.X, pady=1)

        self.ping_label = tk.Label(main, text="PING: -- ms", bg=BG_DARK, fg=FG_CYAN, font=("Consolas", 9), anchor="w")
        self.ping_label.pack(fill=tk.X, pady=1)

        self.status_label = tk.Label(main, text="● ACTIVE", bg=BG_DARK, fg=FG_PURPLE, font=("Consolas", 8))
        self.status_label.pack(pady=(4, 0))

        self.menu = tk.Menu(self.root, tearoff=0, bg=BG_PANEL, fg=FG_CYAN)
        self.menu.add_command(label="Toggle (Ctrl+H)", command=self.toggle_visibility)
        self.menu.add_command(label="Set Target Game...", command=self.set_target_dialog)
        self.menu.add_separator()
        self.menu.add_command(label="Exit", command=self.quit)
        self.root.bind("<Button-3>", self.show_menu)

    def setup_drag(self):
        self.drag_x = 0
        self.drag_y = 0

    def start_move(self, event):
        self.drag_x = event.x
        self.drag_y = event.y

    def on_move(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")

    def setup_hotkey(self):
        self.root.bind("<Control-h>", lambda e: self.toggle_visibility())

    def toggle_visibility(self):
        if self.visible:
            self.root.withdraw()
            self.visible = False
        else:
            self.root.deiconify()
            self.visible = True

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def set_target_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Target Game")
        dialog.geometry("300x120")
        dialog.configure(bg=BG_DARK)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Window title (partial):", bg=BG_DARK, fg=FG_CYAN).pack(pady=10)
        entry = tk.Entry(dialog, bg="#1a1f2a", fg="white", width=30)
        entry.pack(pady=5)
        if self.target_process:
            entry.insert(0, self.target_process)

        def save():
            self.target_process = entry.get().strip() or None
            dialog.destroy()
            if self.target_process:
                self.status_label.config(text=f"🎯 {self.target_process[:12]}")
            else:
                self.status_label.config(text="● ACTIVE")

        tk.Button(dialog, text="Save", command=save, bg=BG_PANEL, fg=FG_CYAN).pack(pady=10)

    def is_target_running(self):
        if not self.target_process or not gw:
            return True
        windows = gw.getWindowsWithTitle(self.target_process)
        return len(windows) > 0

    def get_top_cpu_process(self):
        """
        Returns (name, cpu_percent_normalized) of the most CPU-hungry process.
        Uses a single sampling over a short period to avoid freezing.
        """
        try:
            # First, get a snapshot of all processes with their current CPU usage
            # psutil.process_iter with cpu_percent(interval=0) returns instantaneous usage (may be 0)
            # Instead, we use a small delay by calling cpu_percent(interval=0.2) on the whole list
            processes = []
            for proc in psutil.process_iter(['name']):
                try:
                    # Get CPU usage over 0.2 seconds (non-blocking aggregate)
                    # Note: This still takes time per process, but we can reduce by limiting to top N
                    cpu = proc.cpu_percent(interval=0)
                    if cpu > 0:
                        normalized = cpu / self.cpu_count
                        processes.append((proc.info['name'] or "Unknown", normalized))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            if processes:
                top = max(processes, key=lambda x: x[1])
                return top[0][:15], max(top[1], 0.1)
            return "System Idle", 0.0
        except Exception:
            return "Error", 0.0

    def get_network_speeds(self):
        net = psutil.net_io_counters()
        now = time.time()
        if self.last_net_time == 0:
            self.last_net_sent = net.bytes_sent
            self.last_net_recv = net.bytes_recv
            self.last_net_time = now
            return 0, 0
        dt = now - self.last_net_time
        if dt < 0.01:
            return 0, 0
        sent_rate = (net.bytes_sent - self.last_net_sent) / dt / 1024
        recv_rate = (net.bytes_recv - self.last_net_recv) / dt / 1024
        self.last_net_sent = net.bytes_sent
        self.last_net_recv = net.bytes_recv
        self.last_net_time = now
        return sent_rate, recv_rate

    def update_stats(self):
        def background_update():
            # For top CPU process, we need a small sampling interval.
            # We'll call get_top_cpu_process every few seconds only.
            last_top_update = 0
            top_name = "Idle"
            top_cpu = 0.0

            while True:
                if not self.visible or not self.is_target_running():
                    time.sleep(1)
                    continue

                # Total CPU usage (normalized)
                raw_cpu = psutil.cpu_percent(interval=0.3)
                cpu_normalized = raw_cpu

                # RAM
                mem = psutil.virtual_memory()
                ram_used = mem.used / (1024**3)
                ram_total = mem.total / (1024**3)

                # Update top process only every 2 seconds to reduce overhead
                now = time.time()
                if now - last_top_update >= 2.0:
                    top_name, top_cpu = self.get_top_cpu_process()
                    last_top_update = now

                # GPU
                gpu_str = ""
                if self.gpu_available:
                    gpu_load = get_gpu_usage()
                    if gpu_load is not None:
                        gpu_str = f"GPU: {gpu_load}%"
                    else:
                        gpu_str = "GPU: N/A"

                # Network speeds
                up_kb, down_kb = self.get_network_speeds()
                net_str = f"NET: ↓{down_kb:.0f} ↑{up_kb:.0f} KB/s"

                # Ping (every 3 seconds)
                if PING_AVAILABLE and int(now) % 3 < 1:
                    ping_ms = ping(self.ping_target, timeout=0.8)
                    self.last_ping = int(ping_ms * 1000) if ping_ms else self.last_ping
                ping_text = f"{self.last_ping} ms" if self.last_ping else "N/A"

                # Update UI
                self.root.after(0, lambda c=cpu_normalized: self.cpu_label.config(text=f"CPU: {c:.1f}%"))
                self.root.after(0, lambda n=top_name, c=top_cpu: self.top_cpu_label.config(text=f"TOP: {n} ({c:.1f}%)"))
                self.root.after(0, lambda u=ram_used, t=ram_total: self.ram_label.config(text=f"RAM: {u:.1f} / {t:.1f} GB"))
                if self.gpu_available:
                    self.root.after(0, lambda g=gpu_str: self.gpu_label.config(text=g))
                self.root.after(0, lambda n=net_str: self.net_label.config(text=n))
                self.root.after(0, lambda p=ping_text: self.ping_label.config(text=f"PING: {p}"))

                time.sleep(0.8)

        thread = threading.Thread(target=background_update, daemon=True)
        thread.start()

    def quit(self):
        self.root.destroy()
        sys.exit(0)


if __name__ == "__main__":
    app = MikuOverlay()