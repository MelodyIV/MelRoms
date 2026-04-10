import os
import base64
import hashlib
import tkinter as tk
from tkinter import filedialog, messagebox, font
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

class AESCuteRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ AES Unscrambler ✨")
        self.root.geometry("400x350")
        self.root.configure(bg="#181926")
        self.root.resizable(True, True)

        self.target_path = ""
        
        self.colors = {
            "bg": "#181926",
            "card": "#1e2030",
            "mint": "#BDFCC9",
            "lavender": "#24273a",
            "text": "#8839ef",
            "disabled": "#45475a",
            "run_btn": "#a6d189" 
        }
        
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=9)
        self.btn_font = font.Font(family="Segoe UI", size=10, weight="bold")

        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="✨ AES Unscrambler ✨", font=self.title_font, bg=self.colors["bg"], fg=self.colors["text"], pady=12).pack()
        self.main_frame = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=15, highlightbackground=self.colors["mint"], highlightthickness=2)
        self.main_frame.pack(padx=20, pady=8, fill="both", expand=True)

        tk.Label(self.main_frame, text="Step 1: Select Scrambled File 📁", font=self.label_font, bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        tk.Button(self.main_frame, text="Open Protected File", font=self.btn_font, bg=self.colors["lavender"], fg=self.colors["text"], relief="flat", pady=5, command=self.select_file, cursor="hand2").pack(fill="x", pady=(3, 1))
        
        self.file_label = tk.Label(self.main_frame, text="No file selected...", font=("Consolas", 7), bg=self.colors["card"], fg="#AAAAAA", wraplength=320)
        self.file_label.pack(anchor="w", pady=(0, 12))

        tk.Label(self.main_frame, text="Step 2: Enter Secret Key 🔑", font=self.label_font, bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        self.key_entry = tk.Entry(self.main_frame, font=("Segoe UI", 10), bg=self.colors["bg"], fg="white", insertbackground="white", relief="flat", show="*")
        self.key_entry.pack(fill="x", pady=(3, 15), ipady=3)
        self.key_entry.bind("<KeyRelease>", lambda e: self.check_ready())

        self.run_btn = tk.Button(self.root, text="🚀 Decrypt & Run in Memory", font=self.btn_font, bg=self.colors["disabled"], fg="white", state="disabled", relief="flat", padx=20, pady=8, command=self.execute_deobfuscation)
        self.run_btn.pack(pady=6)

        self.save_btn = tk.Button(self.root, text="💾 Just Save Decrypted File", font=self.label_font, bg=self.colors["bg"], fg=self.colors["text"], state="disabled", relief="flat", command=self.save_decrypted)
        self.save_btn.pack(pady=(0, 8))

    def derive_key(self, passphrase: str):
        return hashlib.sha256(passphrase.encode()).digest()

    def decrypt_code(self, iv_b64, ct_b64, key):
        try:
            iv = base64.b64decode(iv_b64)
            ct = base64.b64decode(ct_b64)
            cipher = AES.new(key, AES.MODE_CBC, iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except Exception:
            return None

    def get_decrypted_content(self):
        key_input = self.key_entry.get()
        key = self.derive_key(key_input)
        
        try:
            with open(self.target_path, 'r', encoding='utf-8') as f:
                full_content = f.read()
            locs = {}
            exec(full_content, {}, locs)
            import re
            iv_match = re.search(r"iv_b64 = '(.+?)'", full_content)
            ct_match = re.search(r"ct_b64 = '(.+?)'", full_content)
            method_match = re.search(r"m = '(\d)'", full_content)
            if not (iv_match and ct_match):
                iv_match = re.search(r"iv='(.+?)'", full_content)
                ct_match = re.search(r"ct='(.+?)'", full_content)

            iv = iv_match.group(1)
            ct = ct_match.group(1)
            method = method_match.group(1) if method_match else "1"
            if method == "2":
                data_match = re.search(r"base64\.b64decode\('(.+?)'\)", full_content)
                if data_match:
                    raw = base64.b64decode(data_match.group(1)).decode()
                    iv, ct = raw.split('|')
            elif method == "3":
                shifted_match = re.search(r"shifted = r'''(.+?)'''", full_content, re.DOTALL)
                if shifted_match:
                    shifted = shifted_match.group(1)
                    raw = "".join(chr(ord(c) - 5) for c in shifted)
                    iv, ct = raw.split('|')
            return self.decrypt_code(iv, ct, key)
        except Exception as e:
            print(f"Extraction Error: {e}")
            return None

    def select_file(self):
        path = filedialog.askopenfilename(title="Select Obfuscated File", filetypes=[("Python Files", "*.py")])
        if path:
            self.target_path = path
            self.file_label.config(text=os.path.basename(path), fg="#555555")
            self.check_ready()

    def check_ready(self):
        if self.target_path and len(self.key_entry.get()) > 0:
            self.run_btn.config(state="normal", bg=self.colors["run_btn"], fg=self.colors["bg"])
            self.save_btn.config(state="normal")
        else:
            self.run_btn.config(state="disabled", bg=self.colors["disabled"], fg="white")
            self.save_btn.config(state="disabled")

    def execute_deobfuscation(self):
        code = self.get_decrypted_content()
        if code:
            messagebox.showinfo("Success! ✨", "Code decrypted! Running now...")
            self.root.iconify()
            try:
                exec(code, {'__name__': '__main__'})
            except Exception as e:
                messagebox.showerror("Runtime Error 🌸", f"The script crashed:\n{e}")
            self.root.deiconify()
        else:
            messagebox.showerror("Wrong Key! 🎀", "Could not decrypt. Is the key correct?")

    def save_decrypted(self):
        code = self.get_decrypted_content()
        if code:
            save_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                messagebox.showinfo("Saved! 🌸", "Decrypted source saved successfully.")
        else:
            messagebox.showerror("Error 🎀", "Could not decrypt code to save it.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AESCuteRunner(root)
    root.mainloop()