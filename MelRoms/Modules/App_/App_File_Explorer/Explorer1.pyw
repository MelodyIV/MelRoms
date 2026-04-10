#!/usr/bin/env python3
"""
Module Editor - Melroms Launcher
=============================================
Author: Expert Python GUI Developer
Version: 1.0
Requirements: 
    - Python 3.10+
    - pip install pygments (optional but highly recommended for syntax highlighting)

File Structure Assumption:
    Melroms/Launcher/
        ├── module_editor.py (This script)
        └── Modules/ (Created automatically if missing)
=============================================
"""

import os
import re
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path

# Try to import Pygments for advanced syntax highlighting
try:
    import pygments
    from pygments.lexers import Python3Lexer, LuaLexer
    from pygments.styles import get_style_by_name
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

# --- CONFIGURATION & THEME ---
BASE_MODULES_DIR = Path(__file__).parent / "Modules"
LAST_TABS_FILE = Path(__file__).parent / "editor_session.json"

COLORS = {
    "bg": "#282a36",
    "fg": "#f8f8f2",
    "sidebar_bg": "#1e1f29",
    "accent": "#bd93f9",
    "gutter_bg": "#21222c",
    "gutter_fg": "#6272a4",
    "highlight_kw": "#ff79c6",
    "highlight_str": "#f1fa8c",
    "highlight_comment": "#6272a4",
    "highlight_num": "#bd93f9",
    "highlight_fn": "#50fa7b",
}

# Ensure Modules directory exists
BASE_MODULES_DIR.mkdir(exist_ok=True)

class CodeEditor(tk.Frame):
    """A high-performance text editor widget with line numbers and syntax highlighting."""
    def __init__(self, master, file_path, on_modified_callback, **kwargs):
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.file_path = Path(file_path)
        self.on_modified = on_modified_callback
        self.language = self._get_language()
        self._highlight_job = None

        # Container for Gutter + Text
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Line Number Gutter
        self.gutter = tk.Text(self, width=4, padx=5, takefocus=0, border=0,
                             background=COLORS["gutter_bg"], foreground=COLORS["gutter_fg"],
                             font=("Consolas", 11), state='disabled', wrap='none')
        self.gutter.grid(row=0, column=0, sticky='nsew')

        # Main Text Widget
        self.text = tk.Text(self, undo=True, wrap="none", font=("Consolas", 11),
                            background=COLORS["bg"], foreground=COLORS["fg"],
                            insertbackground=COLORS["fg"], selectbackground="#44475a",
                            borderwidth=0, highlightthickness=0)
        self.text.grid(row=0, column=1, sticky='nsew')

        # Scrollbars
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self._sync_scroll)
        self.vsb.grid(row=0, column=2, sticky='ns')
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        self.hsb.grid(row=1, column=1, sticky='ew')
        
        self.text.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)
        
        # Setup Tags
        self._setup_tags()
        
        # Bindings
        self.text.bind("<<Modified>>", self._on_text_modified)
        self.text.bind("<KeyRelease>", self._schedule_highlight)
        self.text.bind("<Tab>", self._handle_tab)
        self.text.bind("<Control-f>", lambda e: self.master.master.master.open_search()) # Bubbling up to app
        
        self._update_line_numbers()

    def _setup_tags(self):
        # Pygments/Theme tags
        tag_colors = {
            "Token.Keyword": COLORS["highlight_kw"],
            "Token.Literal.String": COLORS["highlight_str"],
            "Token.Comment": COLORS["highlight_comment"],
            "Token.Literal.Number": COLORS["highlight_num"],
            "Token.Name.Function": COLORS["highlight_fn"],
            "Token.Operator": "#ffb86c",
            "find_match": "#ffb86c", # Search highlight
        }
        for tag, color in tag_colors.items():
            self.text.tag_configure(tag, foreground=color)
        self.text.tag_configure("find_match", background="#44475a", foreground="#ffffff")

    def _get_language(self):
        ext = self.file_path.suffix.lower()
        if ext in ['.py', '.pyw']: return "Python"
        if ext == '.lua': return "Lua"
        return "Plain Text"

    def _handle_tab(self, event):
        self.text.insert(tk.INSERT, "    ")
        return "break"

    def _sync_scroll(self, *args):
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _update_line_numbers(self):
        self.gutter.config(state='normal')
        self.gutter.delete('1.0', tk.END)
        line_count = self.text.index('end-1c').split('.')[0]
        lines = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        self.gutter.insert('1.0', lines)
        self.gutter.config(state='disabled')
        self.gutter.yview_moveto(self.text.yview()[0])

    def _on_text_modified(self, event=None):
        if self.text.edit_modified():
            self._update_line_numbers()
            self.on_modified(True)
        self.text.edit_modified(False)

    def _schedule_highlight(self, event=None):
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(800, self.apply_highlighting)

    def apply_highlighting(self):
        if not HAS_PYGMENTS:
            self._basic_highlight()
            return

        lexer = Python3Lexer() if self.language == "Python" else LuaLexer()
        code = self.text.get("1.0", "end-1c")
        
        # Clear existing tags except search
        for tag in self.text.tag_names():
            if tag != "find_match":
                self.text.tag_remove(tag, "1.0", tk.END)

        last_pos = 0
        for token, value in pygments.lex(code, lexer):
            start = f"1.0 + {last_pos} chars"
            end = f"1.0 + {last_pos + len(value)} chars"
            tag_name = str(token)
            self.text.tag_add(tag_name, start, end)
            last_pos += len(value)

    def _basic_highlight(self):
        """Fallback if pygments is missing."""
        if self.language != "Python": return
        self.text.tag_remove("Token.Keyword", "1.0", tk.END)
        content = self.text.get("1.0", tk.END)
        keywords = r'\b(def|class|if|else|elif|return|import|from|while|for|in|try|except|with|as|print)\b'
        for match in re.finditer(keywords, content):
            start = f"1.0 + {match.start()} chars"
            end = f"1.0 + {match.end()} chars"
            self.text.tag_add("Token.Keyword", start, end)

class ModuleEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Module Editor - Melroms Launcher")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["bg"])
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_styles()

        self.tabs = {} # path: CodeEditor instance
        
        self._build_ui()
        self._load_session()
        
        # Global Bindings
        self.root.bind("<Control-s>", lambda e: self.save_current_tab())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.root.bind("<F5>", lambda e: self.reload_current_file())

    def _setup_styles(self):
        self.style.configure("Treeview", background=COLORS["sidebar_bg"], 
                             foreground=COLORS["fg"], fieldbackground=COLORS["sidebar_bg"], borderwidth=0)
        self.style.map("Treeview", background=[('selected', COLORS["accent"])])
        self.style.configure("TPanedwindow", background=COLORS["bg"])
        self.style.configure("TNotebook", background=COLORS["sidebar_bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=COLORS["sidebar_bg"], foreground=COLORS["fg"], padding=[10, 2])
        self.style.map("TNotebook.Tab", background=[("selected", COLORS["bg"])])

    def _build_ui(self):
        # Toolbar
        toolbar = tk.Frame(self.root, bg=COLORS["sidebar_bg"], height=40)
        toolbar.pack(side="top", fill="x")
        
        btn_add = tk.Button(toolbar, text="➕ Add Module", command=self.create_new_module, 
                           bg=COLORS["accent"], fg="white", relief="flat", padx=10)
        btn_add.pack(side="left", padx=5, pady=5)
        
        btn_refresh = tk.Button(toolbar, text="🔄 Rehighlight", command=self.force_rehighlight,
                               bg="#44475a", fg="white", relief="flat", padx=10)
        btn_refresh.pack(side="left", padx=5, pady=5)

        # Main Paned Window
        self.paned = ttk.PanedWindow(self.root, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # Left Sidebar
        sidebar = tk.Frame(self.paned, bg=COLORS["sidebar_bg"], width=280)
        sidebar.pack_propagate(False)
        self.paned.add(sidebar, weight=0)

        tk.Label(sidebar, text="MODULES", bg=COLORS["sidebar_bg"], fg=COLORS["accent"], 
                 font=("Segoe UI", 10, "bold")).pack(pady=5)
        
        self.tree = ttk.Treeview(sidebar, show="tree")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        
        tk.Button(sidebar, text="Refresh Tree", command=self.refresh_tree,
                  bg="#44475a", fg="white", relief="flat").pack(fill="x", pady=2)

        # Right Main Area
        right_pane = tk.Frame(self.paned, bg=COLORS["bg"])
        self.paned.add(right_pane, weight=1)

        self.notebook = ttk.Notebook(right_pane)
        self.notebook.pack(fill="both", expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, 
                                  relief="sunken", anchor="w", bg=COLORS["sidebar_bg"], fg="#8be9fd")
        self.status_bar.pack(side="bottom", fill="x")

        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self._populate_tree(BASE_MODULES_DIR, "")

    def _populate_tree(self, parent_path, parent_node):
        try:
            for item in sorted(parent_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    node = self.tree.insert(parent_node, "end", iid=str(item.absolute()), text=f"📁 {item.name}", open=False)
                    self._populate_tree(item, node)
                elif item.suffix.lower() in ['.py', '.pyw', '.lua']:
                    self.tree.insert(parent_node, "end", iid=str(item.absolute()), text=f"📄 {item.name}")
        except Exception as e:
            print(f"Error scanning directory: {e}")

    def create_new_module(self):
        name = simpledialog.askstring("New Module", "Enter module name (alphanumeric + underscore):")
        if not name or not re.match(r'^\w+$', name):
            if name: messagebox.showerror("Error", "Invalid name format.")
            return

        module_dir = BASE_MODULES_DIR / name
        module_file = module_dir / f"{name}.pyw"
        
        try:
            module_dir.mkdir(exist_ok=True)
            content = f"""# =============================================
# New Module: {name}
# =============================================
if __name__ == "__main__":
    print("Module '{name}' started successfully!")
"""
            module_file.write_text(content)
            self.refresh_tree()
            self.open_file(module_file)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create module: {e}")

    def open_file(self, path):
        path = Path(path).absolute()
        if str(path) in self.tabs:
            self.notebook.select(self.tabs[str(path)])
            return

        try:
            content = path.read_text(encoding='utf-8', errors='replace')
            editor = CodeEditor(self.notebook, path, lambda mod: self._set_modified_state(path, mod))
            editor.text.insert("1.0", content)
            editor.text.edit_modified(False)
            editor.apply_highlighting()
            
            self.notebook.add(editor, text=path.name)
            self.tabs[str(path)] = editor
            self.notebook.select(editor)
            self._save_session()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def _on_tree_double_click(self, event):
        item_id = self.tree.focus()
        if item_id and Path(item_id).is_file():
            self.open_file(item_id)

    def _on_tab_change(self, event):
        self.update_status()

    def update_status(self):
        curr = self.notebook.select()
        if not curr: return
        editor = self.root.nametowidget(curr)
        
        pos = editor.text.index(tk.INSERT).split('.')
        line_count = int(editor.text.index('end-1c').split('.')[0])
        
        stat = f"Line: {pos[0]} Col: {pos[1]} | Total Lines: {line_count} | Path: {editor.file_path} | Lang: {editor.language}"
        if not HAS_PYGMENTS: stat += " [Pygments Missing]"
        self.status_var.set(stat)

    def _set_modified_state(self, path, is_modified):
        path_str = str(path)
        if path_str in self.tabs:
            idx = self.notebook.index(self.tabs[path_str])
            title = Path(path).name
            if is_modified:
                self.notebook.tab(idx, text=f"*{title}")
            else:
                self.notebook.tab(idx, text=title)

    def save_current_tab(self):
        curr = self.notebook.select()
        if not curr: return
        editor = self.root.nametowidget(curr)
        try:
            content = editor.text.get("1.0", "end-1c")
            editor.file_path.write_text(content, encoding='utf-8')
            editor.text.edit_modified(False)
            self._set_modified_state(editor.file_path, False)
            self.status_var.set(f"Saved: {editor.file_path.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")

    def close_current_tab(self):
        curr = self.notebook.select()
        if not curr: return
        editor = self.root.nametowidget(curr)
        
        if editor.text.edit_modified():
            res = messagebox.askyesnocancel("Unsaved Changes", f"Save changes to {editor.file_path.name}?")
            if res is True: self.save_current_tab()
            elif res is None: return # Cancel

        path_str = str(editor.file_path)
        self.notebook.forget(editor)
        if path_str in self.tabs:
            del self.tabs[path_str]
        self._save_session()

    def reload_current_file(self):
        curr = self.notebook.select()
        if not curr: return
        editor = self.root.nametowidget(curr)
        if messagebox.askokcancel("Reload", "Discard changes and reload from disk?"):
            self.notebook.forget(editor)
            del self.tabs[str(editor.file_path)]
            self.open_file(editor.file_path)

    def open_file_dialog(self):
        f = filedialog.askopenfilename(filetypes=[("Scripts", "*.py *.pyw *.lua"), ("All Files", "*.*")])
        if f: self.open_file(f)

    def force_rehighlight(self):
        curr = self.notebook.select()
        if curr:
            editor = self.root.nametowidget(curr)
            editor.apply_highlighting()

    def open_search(self):
        search_win = tk.Toplevel(self.root)
        search_win.title("Find")
        search_win.geometry("300x120")
        search_win.attributes("-topmost", True)
        
        tk.Label(search_win, text="Find:").grid(row=0, column=0, padx=5, pady=5)
        entry = tk.Entry(search_win, width=30)
        entry.grid(row=0, column=1, padx=5, pady=5)
        entry.focus_set()

        def do_search():
            curr = self.notebook.select()
            if not curr: return
            editor = self.root.nametowidget(curr)
            editor.text.tag_remove("find_match", "1.0", tk.END)
            
            pattern = entry.get()
            if not pattern: return
            
            start_pos = "1.0"
            while True:
                start_pos = editor.text.search(pattern, start_pos, stopindex=tk.END)
                if not start_pos: break
                end_pos = f"{start_pos}+{len(pattern)}c"
                editor.text.tag_add("find_match", start_pos, end_pos)
                start_pos = end_pos

        tk.Button(search_win, text="Find All", command=do_search).grid(row=1, column=1, sticky='e', padx=5)

    def _save_session(self):
        try:
            session = {"open_tabs": list(self.tabs.keys())}
            LAST_TABS_FILE.write_text(json.dumps(session))
        except: pass

    def _load_session(self):
        if LAST_TABS_FILE.exists():
            try:
                session = json.loads(LAST_TABS_FILE.read_text())
                for path in session.get("open_tabs", []):
                    if Path(path).exists():
                        self.open_file(path)
            except: pass

if __name__ == "__main__":
    root = tk.Tk()
    # Simple icon fallback if not provided
    app = ModuleEditor(root)
    root.mainloop()