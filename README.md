✦ M E L R O M S 

any personal workspace built out of necessity eventually turns into a full suite. MelRoms is a modular collection of desktop tools, script editors, low-level network utilities, custom overlays, and mini-games crafted to fill the gaps where existing software falls short or gets bloated.

Everything runs local, strips away unnecessary electron overhead, and emphasizes raw utility, dark aesthetic controls, and heavy customizability.

Preview

![pythonw_D5p2foowkV](https://github.com/user-attachments/assets/e3915127-db8a-4357-ac38-3f5b72bb797f)

![MelRoms Demo](https://r2.e-z.host/c1dfb951-530e-473a-b08b-5bc120684657/wm25gyl7.gif)

✧ 𝑾-𝑯-𝑨-𝑻 '𝑺  𝑰-𝑵-𝑺-𝑰-𝑫-𝑬

✦ Core Systems & Dev Workspace
Module Editor ✧ Multi-tab environment tuned for Python and Lua. Features syntax highlighting, local file tree navigation, instant ZIP payload/project loading, dynamic Discord Rich Presence, and deep integration with Saturn AI.

Saturn AI ✧ Zero-cloud, local coding copilot powered by Ollama (Gemma3). Pulls direct context from your active file tabs or entire uploaded ZIP archives without leaking code to external APIs.

AES Scrambler / Unscrambler ✧ On-the-fly script protection. Obfuscates Python code with AES-256 encryption and executes the decrypted payload directly in memory at runtime.

✦ Monitoring & Network Diagnostics
Miku System Monitor / Overlay ✧ Ultra-lightweight telemetry overlay tracking CPU, RAM, GPU, network I/O, and targeted process latency. Includes target-game auto-hide to stay invisible during borderless fullscreen sessions.

MelRoms Lag Switch ✧ Driver-level packet manipulator utilizing WinDivert. Lets you simulate network latency, artificial drop rates, and packet holds to test netcode resilience under extreme conditions. (Requires Admin privileges)

MikuPinger ✧ Continuous ICMP diagnostic utility supporting custom payload strings, high-rate ping loops, randomized IP target sequences, and colorized console telemetry.

✦ Desk Tools & Aesthetics
Miku Calendar & Event Desk ✧ Event organizer layered over a real-time 3D rendered animated Miku background with theme customization and event schedule exporting.

MelRoms Clock Suite ✧ Circular alarm dial, high-precision lap stopwatch with global hotkey support, countdown timers, integrated calculator.

Color Picker ✧ Desktop pixel sampling tool with continuous magnifying cursor, RGB sliders, hex code auto-formatting, and dynamic color-name matching.

✦ Integrated 3D Mini-Games
Cyber-Pong 3D ✧ Wireframe vector graphics, particle collision engine, audio-reactive screen flashes, and custom paddle physics.

3D Wireframe Tetris ✧ Retrowave-styled Tetris engine utilizing perspective 3D projection, piece hold queues, drop shadows, and visual board shake.

3D Wireframe Pong ✧ Retrowave Pong utilizing perspective 3D projection, enemy AU, particle effects, and auditory cues.

✧ 𝑲-𝑬-𝒀  𝑭-𝑬-𝑨-𝑻-𝑄-𝑑-𝑬-𝑺

˚.✦ 100% Local AI ✧ Zero external API calls. Saturn processes your entire workspace completely offline.
˚.✦ Universal JSON Theming ✧ Every window, UI border, and text element reads color arrays from JSON files. Or so I fucking tried anyway. Swap palates instantly.
˚.✦ Raw Performance ✧ Built directly on top of pygame-ce and CustomTkinter for minimal CPU idle usage. Though multiple windows will fuck your system.
˚.✦ Modular Layouts ✧ Windows launch in compact utility sizes by default so they don't clog up screen real estate alongside your primary work. But they're still pretty huge because I suck.

✧ 𝑻-𝑬-𝑪-𝑯  𝑺-𝑻-𝑨-𝑪-𝑲

Plaintext
Language     : Python 3.12+ (3.14 Recommended)
Platform     : Windows 10 / 11 (Primary), WSL / Linux (Partial)
GUI & Render : Pygame-CE, CustomTkinter, NumPy, Pyrr (3D Projection)
Low-Level    : PyDivert (Packet Capture), PSUtil, GPUtil, PyAudio, PyCryptodome
Integrations : Ollama, PyPresence, Pygments, Rich, PyAutoGUI
✧ 𝑮-𝑬-𝑻-𝑻-𝑰-𝑵-𝑮  𝑺-𝑻-𝑨-𝑝-𝑻-𝑬-𝑫

Option A: Standard Setup (Existing Python Environment)
Clone the repository, install dependencies, and launch:

Bash
git clone https://github.com/MelRoms/MelRoms.git
cd MelRoms
pip install -r requirements.txt
python MelRoms_Launcher.pyw



Option B: Automated Setup (Quick Launch)
Grab the latest archive from the Releases tab.

Run RUN_ME!.bat as Administrator.

Accept the initialization disclaimer (i understand) to automatically fetch standard dependencies and setup execution paths.
