# 🪐 MelRoms

**MelRoms** is a personal collection of tools, editors, games, and utilities that I built because I couldn't find exactly what I wanted elsewhere. Everything is designed to be modular, themeable, and fun to use.

> **Note:** This suite is under active development. Some tools require administrator privileges (e.g., network monitoring, lag switch). Use responsibly.

## 📸 Preview
![pythonw_D5p2foowkV](https://github.com/user-attachments/assets/e3915127-db8a-4357-ac38-3f5b72bb797f)
![MelRoms Demo](https://r2.e-z.host/c1dfb951-530e-473a-b08b-5bc120684657/wm25gyl7.gif)


---

## 📦 What's Inside

| Tool | Description |
|------|-------------|
| **Module Editor** | Multi‑tab code editor with syntax highlighting (Python/Lua), AI chat (Saturn – local Ollama), file browser, ZIP upload, Discord Rich Presence. |
| **Saturn AI** | Local coding assistant using Gemma3 via Ollama. Works with current file + ZIP contents. |
| **AES Scrambler / Unscrambler** | Obfuscate Python scripts with AES‑256 encryption; decrypt and run in memory. |
| **Miku System Monitor** | Lightweight overlay (CPU/RAM/GPU/network/ping) with target process detection. |
| **MelRoms Lag Switch** | Network packet manipulator (delay, drop, hold) for testing game/netcode. *Admin rights required.* |
| **MikuPinger** | Continuous ping tool with random IP mode, custom packet messages, and colourful logs. |
| **MelRoms Clock** | Stopwatch (with lap counter & keybind), countdown timer, alarm (circular setter), calculator, ASCII art. |
| **Miku Calendar** | Event manager with 3D animated Miku background, theme switching, upcoming events export. |
| **Cyber‑Pong 3D** | 3D wireframe Pong with particle effects, screen flashes, and sound. |
| **3D Wireframe Tetris** | Classic Tetris with perspective projection, hold & next pieces, visual effects. |
| **Color Picker** | Screen colour capture, RGB sliders, colour name matching, hex/RGB copy. |
| **Miku Overlay** | Always‑on‑top system monitor (CPU/RAM/GPU/net/ping) with target‑game auto‑hide. |

---

## ✨ Key Features

- **🎨 Custom Theming** – All UI colours are defined in JSON files; switch themes on the fly.
- **🤖 Local AI Assistant** – Saturn chat uses Ollama (Gemma3) – **no data leaves your PC**.
- **📦 ZIP Analysis** – Upload any ZIP, Saturn reads all text files and answers questions about them.
- **🎮 Built‑in Games** – Pong and Tetris with 3D wireframe graphics and synth‑wave audio.
- **🔧 Network Tools** – Lag switch and pinger for debugging (use only on networks you own).
- **💬 Discord Rich Presence** – Shows what file you're editing (optional, no code content).
- **⚡ Compact & Resizable** – All windows are small by default but can be enlarged.

---

## 🛠️ Tech Stack

- **Language:** Python 3.12+ (3.14 recommended)
- **Environment:** Windows 10/11 (most tools), WSL/Ubuntu (partial support)
- **Core Libraries:** `pygame-ce`, `psutil`, `pydivert`, `pypresence`, `ollama`, `pycryptodome`, `pygments`, `Pillow`, `pyautogui`, `GPUtil`, `ping3`, `pygetwindow`, `mutagen`, `yt-dlp`, `python-vlc`, `pynput`, `customtkinter`, `pyttsx3`, `requests`, `numpy`, `pyrr`, `colorama`, `rich`, `pipreqs`, `pyinstaller`

See `requirements.txt` for exact versions.

---

## 🚀 Getting Started

### 1. Download
Grab the latest `.zip` from the [Releases](https://github.com/MelRoms/MelRoms/releases) page.

### 2. Run the installer / launcher
- If you **do not have Python 3.12+** installed, run `RUN_ME!.bat` as **Administrator**.  
  Read the disclaimer carefully and type `i understand` to proceed – this will install Python and dependencies automatically.
- If you already have Python, simply run:
  ```bash
  pip install -r requirements.txt
  python Launcher.py
