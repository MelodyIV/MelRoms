import subprocess
import os
import sys
import json
import tkinter as tk
from tkinter import filedialog

# Configuration file name
CONFIG_FILE = "launcher_config.json"

def get_target_path():
    """Opens a file picker to select the target Python script."""
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    
    target = filedialog.askopenfilename(
        title="INITIAL SETUP: Select the Python script to auto-launch",
        filetypes=[("Python Files", "*.py *.pyw"), ("All Files", "*.*")]
    )
    root.destroy()
    return target

def main():
    # 1. Check if we already have a saved target
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            target_path = config.get("target")
    else:
        # 2. First-time setup: Pick the file
        target_path = get_target_path()
        
        if target_path:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({"target": target_path}, f)
        else:
            print("No file selected. Exiting.")
            sys.exit()

    # 3. Launch the target file silently
    if target_path and os.path.exists(target_path):
        # 'pythonw' runs the script without opening a new CMD/Terminal window
        # We use Popen so this script can finish while the other keeps running
        subprocess.Popen([sys.executable.replace("python.exe", "pythonw.exe"), target_path], 
                         creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    else:
        print(f"Error: Target file not found at {target_path}")
        # Optional: Delete config so the user can re-pick next time
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

if __name__ == "__main__":
    main()