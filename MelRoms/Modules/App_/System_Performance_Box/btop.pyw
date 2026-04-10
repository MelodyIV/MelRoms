import sys
import psutil
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime

# ---------- THEME: Black + Neon Orange ----------
COLORS = {
    "bg": "#000000",
    "top_bg": "#0a0a0a",
    "chat_bg": "#080808",
    "user_bubble": "#cc5500",
    "assistant_bubble": "#1a1a1a",
    "accent": "#ff8c00",      # neon orange
    "text": "#ffaa44",
    "text_light": "#ffcc88",
    "border": "#ff8c00",
    "good": "#44ff66",
    "warn": "#ffaa44",
    "bad": "#ff5555",
}

def apply_theme(app):
    app.configure(fg_color=COLORS["bg"])
    ctk.set_appearance_mode("dark")

class Baltop(ctk.CTk):
    def __init__(self):
        super().__init__()
        apply_theme(self)
        self.title("⚡ Baltop – System Monitor")
        self.geometry("1000x600")          # more compact
        self.minsize(800, 500)

        self.running = True
        self._build_ui()
        self._start_updater()

    def _build_ui(self):
        # ----- Top bar (thin) -----
        top = ctk.CTkFrame(self, height=35, fg_color=COLORS["top_bg"])
        top.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(top, text="⚡ System Monitor", font=("Segoe UI", 14, "bold"), text_color=COLORS["accent"]).pack(side="left", padx=10)
        self.time_label = ctk.CTkLabel(top, text="", font=("Segoe UI", 11))
        self.time_label.pack(side="right", padx=10)

        ctk.CTkButton(top, text="⟳", width=30, height=25, command=self._force_refresh).pack(side="right", padx=5)

        # ----- Main scrollable area (tight) -----
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color=COLORS["chat_bg"])
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ---- CPU section (horizontal) ----
        cpu_frame = self._make_section("🖥️ CPU")
        self.cpu_bar = ctk.CTkProgressBar(cpu_frame, width=250, height=12, corner_radius=4, progress_color=COLORS["accent"])
        self.cpu_bar.pack(side="left", padx=5)
        self.cpu_percent_label = ctk.CTkLabel(cpu_frame, text="0%", width=40, font=("Segoe UI", 12))
        self.cpu_percent_label.pack(side="left", padx=5)
        self.cpu_freq_label = ctk.CTkLabel(cpu_frame, text="", font=("Segoe UI", 10))
        self.cpu_freq_label.pack(side="left", padx=5)

        # Per‑core (inline)
        self.core_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.core_frame.pack(fill="x", pady=2)
        self.core_widgets = []   # list of (label, bar)

        # ---- RAM (horizontal) ----
        ram_frame = self._make_section("💾 RAM")
        self.ram_bar = ctk.CTkProgressBar(ram_frame, width=250, height=12, corner_radius=4, progress_color=COLORS["accent"])
        self.ram_bar.pack(side="left", padx=5)
        self.ram_label = ctk.CTkLabel(ram_frame, text="0/0 GB (0%)", font=("Segoe UI", 12))
        self.ram_label.pack(side="left", padx=5)

        # ---- Swap (horizontal) ----
        swap_frame = self._make_section("💿 Swap")
        self.swap_bar = ctk.CTkProgressBar(swap_frame, width=250, height=12, corner_radius=4, progress_color=COLORS["warn"])
        self.swap_bar.pack(side="left", padx=5)
        self.swap_label = ctk.CTkLabel(swap_frame, text="0/0 GB (0%)", font=("Segoe UI", 12))
        self.swap_label.pack(side="left", padx=5)

        # ---- Disk (horizontal) ----
        disk_frame = self._make_section("💽 Disk")
        self.disk_bar = ctk.CTkProgressBar(disk_frame, width=250, height=12, corner_radius=4, progress_color=COLORS["good"])
        self.disk_bar.pack(side="left", padx=5)
        self.disk_label = ctk.CTkLabel(disk_frame, text="0/0 GB (0%)", font=("Segoe UI", 12))
        self.disk_label.pack(side="left", padx=5)

        # ---- Network (horizontal) ----
        net_frame = self._make_section("🌐 Network")
        self.net_down_label = ctk.CTkLabel(net_frame, text="⬇️ 0 KB/s", font=("Segoe UI", 12), text_color=COLORS["good"])
        self.net_down_label.pack(side="left", padx=5)
        self.net_up_label = ctk.CTkLabel(net_frame, text="⬆️ 0 KB/s", font=("Segoe UI", 12), text_color=COLORS["warn"])
        self.net_up_label.pack(side="left", padx=5)
        self.net_total_label = ctk.CTkLabel(net_frame, text="⬇⬆ 0/0 MB", font=("Segoe UI", 10))
        self.net_total_label.pack(side="left", padx=5)

        # ---- Process list (compact) ----
        proc_frame = self._make_section("📋 Top Processes")
        # Use a smaller treeview
        self.tree = ttk.Treeview(proc_frame, columns=("PID", "Name", "CPU%", "MEM%"), show="headings", height=12)
        self.tree.heading("PID", text="PID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("CPU%", text="CPU%")
        self.tree.heading("MEM%", text="MEM%")
        self.tree.column("PID", width=50)
        self.tree.column("Name", width=220)
        self.tree.column("CPU%", width=60)
        self.tree.column("MEM%", width=60)
        self.tree.pack(fill="both", expand=True, padx=2, pady=2)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#080808", foreground="#ffaa44", fieldbackground="#080808", borderwidth=0)
        style.configure("Treeview.Heading", background="#0a0a0a", foreground="#ff8c00", borderwidth=0)
        style.map("Treeview", background=[("selected", "#ff8c00")], foreground=[("selected", "#000000")])

    def _make_section(self, title):
        frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame.pack(fill="x", pady=4)
        lbl = ctk.CTkLabel(frame, text=title, font=("Segoe UI", 12, "bold"), text_color=COLORS["accent"])
        lbl.pack(anchor="w")
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", pady=2)
        return content

    def _force_refresh(self):
        threading.Thread(target=self._update_all, daemon=True).start()

    def _start_updater(self):
        def update_loop():
            while self.running:
                self._update_all()
                time.sleep(1)
        threading.Thread(target=update_loop, daemon=True).start()

    def _update_all(self):
        # Time
        self.after(0, lambda: self.time_label.configure(text=datetime.now().strftime("%H:%M:%S")))

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_freq = psutil.cpu_freq()
        self.after(0, lambda: self.cpu_bar.set(cpu_percent / 100))
        self.after(0, lambda: self.cpu_percent_label.configure(text=f"{cpu_percent:.0f}%"))
        if cpu_freq:
            self.after(0, lambda: self.cpu_freq_label.configure(text=f"{cpu_freq.current:.0f}MHz"))

        # Per‑core
        per_core = psutil.cpu_percent(percpu=True, interval=0.1)
        if len(self.core_widgets) != len(per_core):
            self.after(0, self._rebuild_core_ui, per_core)
        else:
            for i, (lbl, bar) in enumerate(self.core_widgets):
                val = per_core[i]
                self.after(0, lambda l=lbl, b=bar, v=val: (l.configure(text=f"Core{i}:{v:.0f}%"), b.set(v/100)))

        # RAM
        mem = psutil.virtual_memory()
        ram_used_gb = mem.used / (1024**3)
        ram_total_gb = mem.total / (1024**3)
        ram_percent = mem.percent
        self.after(0, lambda: self.ram_bar.set(ram_percent / 100))
        self.after(0, lambda: self.ram_label.configure(text=f"{ram_used_gb:.1f}/{ram_total_gb:.1f}GB ({ram_percent:.0f}%)"))

        # Swap
        swap = psutil.swap_memory()
        swap_used_gb = swap.used / (1024**3)
        swap_total_gb = swap.total / (1024**3) if swap.total else 0
        swap_percent = swap.percent if swap.total else 0
        self.after(0, lambda: self.swap_bar.set(swap_percent / 100))
        self.after(0, lambda: self.swap_label.configure(text=f"{swap_used_gb:.1f}/{swap_total_gb:.1f}GB ({swap_percent:.0f}%)"))

        # Disk
        disk = psutil.disk_usage("/")
        disk_used_gb = disk.used / (1024**3)
        disk_total_gb = disk.total / (1024**3)
        disk_percent = disk.percent
        self.after(0, lambda: self.disk_bar.set(disk_percent / 100))
        self.after(0, lambda: self.disk_label.configure(text=f"{disk_used_gb:.1f}/{disk_total_gb:.1f}GB ({disk_percent:.0f}%)"))

        # Network
        net_io = psutil.net_io_counters()
        if not hasattr(self, '_prev_net'):
            self._prev_net = net_io
            down_speed = up_speed = 0
        else:
            down_speed = (net_io.bytes_recv - self._prev_net.bytes_recv) / 1024
            up_speed = (net_io.bytes_sent - self._prev_net.bytes_sent) / 1024
        self._prev_net = net_io
        down_mb = net_io.bytes_recv / (1024**2)
        up_mb = net_io.bytes_sent / (1024**2)
        self.after(0, lambda: self.net_down_label.configure(text=f"⬇️ {down_speed:.0f}KB/s"))
        self.after(0, lambda: self.net_up_label.configure(text=f"⬆️ {up_speed:.0f}KB/s"))
        self.after(0, lambda: self.net_total_label.configure(text=f"⬇{down_mb:.0f} ⬆{up_mb:.0f}MB"))

        # Processes
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        processes.sort(key=lambda p: p['cpu_percent'] or 0, reverse=True)
        top_procs = processes[:15]

        def _update_tree():
            for row in self.tree.get_children():
                self.tree.delete(row)
            for p in top_procs:
                self.tree.insert("", "end", values=(
                    p['pid'], (p['name'] or '?')[:35], f"{p['cpu_percent']:.1f}", f"{p['memory_percent']:.1f}"
                ))
        self.after(0, _update_tree)

    def _rebuild_core_ui(self, per_core_list):
        for w in self.core_frame.winfo_children():
            w.destroy()
        self.core_widgets = []
        for i in range(len(per_core_list)):
            row = ctk.CTkFrame(self.core_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            lbl = ctk.CTkLabel(row, text=f"Core{i}:0%", width=55, font=("Segoe UI", 10))
            lbl.pack(side="left")
            bar = ctk.CTkProgressBar(row, width=150, height=8, corner_radius=2, progress_color=COLORS["accent"])
            bar.pack(side="left", padx=4)
            self.core_widgets.append((lbl, bar))
        # Force update
        self._update_all()

    def on_closing(self):
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = Baltop()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()