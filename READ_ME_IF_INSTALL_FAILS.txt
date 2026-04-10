Just as the script mentions at the beginning, this suite utilizes AI-generated code. While it runs perfectly for the creator, AI code can occasionally have unexpected bugs that might interact with your data. By proceeding with these manual steps, you acknowledge you are running the software at your own risk.

Step 1: Install MSVC Redistributable
The script installs the Microsoft Visual C++ Redistributable (x64). This is required for several of the Python modules (like pydivert and pycryptodome) to function properly.

Download the installer directly from Microsoft: vc_redist.x64.exe

Run the downloaded file and follow the standard installation prompts. (If your system says it's already installed, you can just close it and move on).

Step 2: Verify or Install Python
The script checks if you have Python installed. If you are already running your usual Python 3.14 environment, you can actually skip this step entirely! The script is designed to bypass the installation if it detects an existing Python setup.

If you do need to install the exact fallback version the script uses (3.12.2):

Download the installer: Python 3.12.2 (64-bit)

Crucial Step: When you run the installer, look at the bottom of the first window and check the box that says "Add python.exe to PATH" before clicking Install.

Step 3: Install Python Dependencies
This is where the script fetches all the libraries MelRoms needs to run.

Open your Command Prompt (make sure you do this in standard Windows rather than your WSL terminal, since libraries like pygetwindow and pyautogui need to interact with the Windows GUI).

Run this command to ensure your package manager is up to date:

DOS
python -m pip install --upgrade pip
Copy and paste this single command to install all the required modules at once:

DOS
python -m pip install pygame-ce psutil pygetwindow ping3 GPUtil pycryptodome yt-dlp python-vlc Pillow mutagen pyautogui pynput pydivert pypresence ollama customtkinter pyttsx3 requests pygments discord.py
Step 4: Install the WinDivert Binaries
The script downloads a specific networking tool (WinDivert) and extracts its core driver files directly into the launcher's directory.

Download the WinDivert zip file: WinDivert-2.2.2-A.zip

Extract the .zip file somewhere convenient on your PC.

Open the extracted folder and navigate to the 64-bit directory: WinDivert-2.2.2-A\x64\

Copy the following two files:

WinDivert.dll

WinDivert64.sys

Paste those two files directly into the same folder where your MelRoms_Launcher.pyw file is located.

Step 5: Launch the Suite
Once all the above is complete, your environment is fully prepared. Simply double-click MelRoms_Launcher.pyw to start the program.