import os
import base64
import hashlib
import string
import random
import secrets
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, font
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
def spawn_key_cmd(entry_widget=None):
    alphabet = string.ascii_letters + string.digits
    random_key = ''.join(secrets.choice(alphabet) for _ in range(64))
    cmd_command = (
        f"color 0b && "
        f"echo ---------------------------------------------------------------- && "
        f"echo ✨ YOUR SECURE 64-CHARACTER KEY ✨ && "
        f"echo ---------------------------------------------------------------- && "
        f"echo. && "
        f"echo {random_key} && "
        f"echo. && "
        f"echo ---------------------------------------------------------------- && "
        f"echo Highlight the key and press ENTER to copy. && "
        f"pause > nul"
    )
    subprocess.Popen(f'start "✨ Key Generator ✨" cmd /c "{cmd_command}"', shell=True)
    if entry_widget is not None:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, random_key)
class AESCuteObfuscator:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ AES Scrambler ✨")
        self.root.geometry("440x480")
        self.root.configure(bg="#232634")
        self.root.resizable(True, True)

        self.input_path = ""
        self.output_path = ""
        self.obf_method = tk.StringVar(value="1")

        self.colors = {
            "bg": "#181926",
            "card": "#1e2030",
            "mint": "#E0FFF0",
            "pink": "#FFB6C1",
            "lavender": "#24273a",
            "text": "#8839ef",
            "disabled": "#45475a",
            "go_btn": "#a6d189"
        }
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.label_font = font.Font(family="Segoe UI", size=9)
        self.btn_font = font.Font(family="Segoe UI", size=10, weight="bold")
        self.setup_ui()

    def setup_ui(self):
        tk.Label(self.root, text="✨ AES Scrambler ✨", font=self.title_font,
                 bg=self.colors["bg"], fg=self.colors["text"], pady=10).pack()

        self.main_frame = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=15,
                                   highlightbackground=self.colors["lavender"], highlightthickness=2)
        self.main_frame.pack(padx=20, pady=5, fill="both", expand=True)

        self.create_section("Step 1: Pick your file 📁", "Select Python File",
                            self.select_input, "input_label")

        tk.Label(self.main_frame, text="Step 2: Choose Complexity 🧠", font=self.label_font,
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        method_frame = tk.Frame(self.main_frame, bg=self.colors["card"])
        method_frame.pack(fill="x", pady=(3, 10))

        methods = [("Standard", "1"), ("Enhanced", "2"), ("High Complex", "3")]
        for text, val in methods:
            rb = tk.Radiobutton(method_frame, text=text, variable=self.obf_method, value=val,
                                bg=self.colors["card"], fg=self.colors["text"],
                                font=("Segoe UI", 8), selectcolor=self.colors["lavender"])
            rb.pack(side="left", expand=True)

        tk.Label(self.main_frame, text="Step 3: Secret Passphrase 🔑", font=self.label_font,
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        key_frame = tk.Frame(self.main_frame, bg=self.colors["card"])
        key_frame.pack(fill="x", pady=(3, 12))
        self.key_entry = tk.Entry(key_frame, font=("Segoe UI", 10), bg=self.colors["lavender"],
                                  fg="white", insertbackground="white", relief="flat", show="*")
        self.key_entry.pack(side="left", fill="x", expand=True, ipady=3)
        gen_btn = tk.Button(key_frame, text="🔑 Generate", font=self.label_font,
                            bg=self.colors["lavender"], fg=self.colors["text"],
                            relief="flat", command=lambda: spawn_key_cmd(self.key_entry))
        gen_btn.pack(side="left", padx=(4, 0))

        self.key_entry.bind("<KeyRelease>", lambda e: self.check_ready())

        self.create_section("Step 4: Save Result 💾", "Set Output Path",
                            self.select_output_path, "output_label")

        self.start_btn = tk.Button(self.root, text="🚀 Scramble My Code!", font=self.btn_font,
                                   bg=self.colors["disabled"], fg="white", state="disabled",
                                   relief="flat", padx=20, pady=8, command=self.execute_obfuscation)
        self.start_btn.pack(pady=8)

        tk.Button(self.root, text="Clear All", font=self.label_font, bg=self.colors["bg"],
                  fg=self.colors["text"], relief="flat", command=self.clear_all).pack(pady=(0, 8))

    def create_section(self, instruction, btn_text, command, label_attr):
        tk.Label(self.main_frame, text=instruction, font=self.label_font,
                 bg=self.colors["card"], fg=self.colors["text"]).pack(anchor="w")
        btn = tk.Button(self.main_frame, text=btn_text, font=self.btn_font,
                        bg=self.colors["lavender"], fg=self.colors["text"],
                        relief="flat", pady=4, command=command)
        btn.pack(fill="x", pady=(3, 1))
        lbl = tk.Label(self.main_frame, text="No file chosen...", font=("Consolas", 7),
                       bg=self.colors["card"], fg="#AAAAAA", wraplength=320)
        lbl.pack(anchor="w", pady=(0, 8))
        setattr(self, label_attr, lbl)

    def derive_key(self, passphrase: str):
        return hashlib.sha256(passphrase.encode()).digest()

    def encrypt_code(self, code: str, key: bytes):
        cipher = AES.new(key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(code.encode(), AES.block_size))
        iv = base64.b64encode(cipher.iv).decode('utf-8')
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        return iv, ct

    def create_stub(self, iv, ct, method, raw_pass):
        key_ints = [ord(c) for c in raw_pass]
        salt = random.randint(10, 50)
        hidden_key_data = [x + salt for x in key_ints]

        stub = f"""import base64, hashlib, os
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def _internal_data_blob():
    return {hidden_key_data}

def run_payload():
    s = {salt}
    try:
        k_src = "".join(chr(x - s) for x in _internal_data_blob())
        
        iv_b64 = '{iv}'
        ct_b64 = '{ct}'
        m = '{method}'
        k = hashlib.sha256(k_src.encode()).digest()
        cipher = AES.new(k, AES.MODE_CBC, base64.b64decode(iv_b64))
        payload = unpad(cipher.decrypt(base64.b64decode(ct_b64)), AES.block_size).decode('utf-8')
        exec(payload, {{'__name__': '__main__'}})
    except:
        pass

if __name__ == "__main__":
    run_payload()
"""
        return stub

    def select_input(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py *.pyw"), ("All Files", "*.*")])
        if path:
            self.input_path = path
            self.input_label.config(text=os.path.basename(path))
            self.check_ready()

    def select_output_path(self):
        path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python File", "*.py")])
        if path:
            self.output_path = path
            self.output_label.config(text=os.path.basename(path))
            self.check_ready()

    def check_ready(self):
        if self.input_path and self.output_path and self.key_entry.get():
            self.start_btn.config(state="normal", bg=self.colors["go_btn"], fg=self.colors["bg"])
        else:
            self.start_btn.config(state="disabled", bg=self.colors["disabled"])

    def clear_all(self):
        self.input_path = self.output_path = ""
        self.key_entry.delete(0, tk.END)
        self.input_label.config(text="No file chosen...")
        self.output_label.config(text="No file chosen...")
        self.check_ready()

    def execute_obfuscation(self):
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            passphrase = self.key_entry.get()
            key = self.derive_key(passphrase)
            iv, ct = self.encrypt_code(content, key)

            final_code = self.create_stub(iv, ct, self.obf_method.get(), passphrase)

            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(final_code)

            messagebox.showinfo("Success! 🌸", "Standalone obfuscated file created!")
            self.clear_all()
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = AESCuteObfuscator(root)
    root.mainloop()