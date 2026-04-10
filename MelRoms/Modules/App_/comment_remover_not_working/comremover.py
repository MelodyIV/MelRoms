import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import re

class CommentPurgePro:
    def __init__(self, root):
        self.root = root
        self.root.title("Comment Purge Pro")
        self.root.geometry("1000x750")
        self.root.configure(bg="#121212")
        
        self.file_path = tk.StringVar()
        self.setup_ui()

    def setup_ui(self):
        # Header
        tk.Label(self.root, text="Comment Purge Pro", font=("Segoe UI", 20, "bold"),
                 bg="#121212", fg="#00ff88", pady=20).pack()

        # File Selection Area
        frame = tk.Frame(self.root, bg="#121212")
        frame.pack(pady=10, padx=30, fill="x")
        
        self.entry = tk.Entry(frame, textvariable=self.file_path, bg="#1e1e1e", fg="#00ff88", 
                              insertbackground="white", borderwidth=0, font=("Consolas", 11))
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        
        tk.Button(frame, text="BROWSE", command=self.browse, bg="#333", fg="white", 
                  relief="flat", padx=20, font=("Segoe UI", 9, "bold")).pack(side="right")

        # Controls
        ctrl_frame = tk.Frame(self.root, bg="#121212")
        ctrl_frame.pack(pady=10)

        # Ensure these command names match the functions defined below!
        tk.Button(ctrl_frame, text="GENERATE PREVIEW", command=self.run_preview, 
                  bg="#0078d7", fg="white", relief="flat", padx=25, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)
        
        tk.Button(ctrl_frame, text="SAVE CHANGES", command=self.save_file, 
                  bg="#d83b01", fg="white", relief="flat", padx=25, pady=10, font=("Segoe UI", 9, "bold")).pack(side="left", padx=10)

        # Editor/Preview
        tk.Label(self.root, text="Code Preview (Modified):", bg="#121212", fg="#888").pack(anchor="w", padx=30)
        self.text_area = scrolledtext.ScrolledText(self.root, bg="#1e1e1e", fg="#e0e0e0", 
                                                   font=("Consolas", 11), borderwidth=0, padx=10, pady=10)
        self.text_area.pack(pady=(5, 20), padx=30, fill="both", expand=True)

    def browse(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_path.set(path)
            self.run_preview() # Automatically preview when file is selected

    def strip_comments(self, text):
        """
        Regex-Hybrid Logic: Matches strings to preserve them, 
        then finds and removes comment patterns.
        """
        pattern = r"""
            (
                "(?:\\.|[^"\\])*"|              # Double quoted strings
                '(?:\\.|[^'\\])*'|              # Single quoted strings
                (?s:'''(?:\\.|[^']|'(?!''))*''')| # Python triple single quotes
                (?s:\"\"\"(?:\\.|[^"]|"(?!""))*\"\"\")| # Python triple double quotes
                `[^`]*`                         # JS Template Literals
            ) | (
                /\*.*?\*/|                      # Multi-line comments (/* */)
                //.*|                           # Single-line (//)
                \#.*|                           # Single-line (#)
                --.*|                           # SQL/Lua single line (--)
                # HTML comments
            )
        """
        
        def replace_fn(match):
            # If group 1 matched, it's a string—keep it!
            if match.group(1) is not None:
                return match.group(1)
            # Otherwise, it's a comment—strip it!
            else:
                return ""

        regex = re.compile(pattern, re.VERBOSE | re.MULTILINE | re.DOTALL)
        return regex.sub(replace_fn, text)

    def run_preview(self):
        """Calculates the cleaned code and displays it."""
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            return
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            cleaned = self.strip_comments(content)
            
            # Update UI
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, cleaned)
        except Exception as e:
            messagebox.showerror("Error", f"Could not read file: {e}")

    def save_file(self):
        """Writes the text area content back to the file."""
        path = self.file_path.get()
        if not path:
            messagebox.showwarning("Warning", "No file selected!")
            return
            
        confirm = messagebox.askyesno("Confirm", "Are you sure you want to overwrite the original file?")
        if confirm:
            try:
                content = self.text_area.get(1.0, tk.END)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                messagebox.showinfo("Success", "File updated and comments purged!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CommentPurgePro(root)
    root.mainloop()