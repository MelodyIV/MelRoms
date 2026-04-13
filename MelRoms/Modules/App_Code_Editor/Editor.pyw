#!/usr/bin/env python3

import os
import re
import json
import base64
import threading
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Optional, Dict, List, Any
import tempfile
import zipfile
import time
from datetime import datetime, timedelta

# Discord RPC
try:
    from pypresence import Presence
    DISCORD_RPC_AVAILABLE = True
except ImportError:
    DISCORD_RPC_AVAILABLE = False
    print("pypresence not installed. Discord RPC disabled. Run: pip install pypresence")

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Ollama not installed. AI chat disabled.")

try:
    import pygments
    from pygments.lexers import PythonLexer, LuaLexer, get_lexer_for_filename
    from pygments.token import Token
    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False
    print("Pygments not installed. Basic highlighting only.")

CURRENT_FILE = Path(__file__).resolve()
BASE_DIR = CURRENT_FILE.parent
BASE_MODULES_DIR = BASE_DIR.parent
SESSION_FILE = BASE_DIR / "editor_session.json"
THEMES_DIR = BASE_DIR / "Themes"
THEMES_DIR.mkdir(exist_ok=True)

DEFAULT_THEME = {
  "name": "Miku Cyber-Leek",
  "colors": {
    "bg": "#0B0E14",
    "fg": "#E0F7F6",
    "sidebar_bg": "#141921",
    "accent": "#39C5BB",
    "accent_fg": "#000000",
    "gutter_bg": "#080B10",
    "gutter_fg": "#39C5BB",
    "highlight_kw": "#39C5BB",
    "highlight_str": "#FF85B2",
    "highlight_comment": "#2A3B4D",
    "highlight_num": "#FF3D8B",
    "highlight_fn": "#A9D2D0",
    "highlight_class": "#39C5BB",
    "highlight_op": "#FF85B2",
    "chat_bg": "#141921",
    "chat_input_bg": "#06090E",
    "toolbar_bg": "#141921",
    "menu_bg": "#1D2433",
    "menu_fg": "#E0F7F6",
    "menu_active_bg": "#39C5BB",
    "menu_active_fg": "#000000",
    "status_bg": "#080B10",
    "status_fg": "#39C5BB",
    "tree_bg": "#0F131A",
    "tree_fg": "#A9D2D0",
    "tree_selected_bg": "#39C5BB",
    "tree_selected_fg": "#000000",
    "button_bg": "#1D2433",
    "button_fg": "#E0F7F6",
    "button_active_bg": "#39C5BB",
    "select_bg": "#39C5BB",
    "select_fg": "#000000",
    "scrollbar_bg": "#1D2433",
    "scrollbar_trough": "#0A0D12",
    "notebook_bg": "#141921",
    "notebook_tab_bg": "#1D2433",
    "notebook_tab_fg": "#A9D2D0",
    "notebook_tab_selected_bg": "#0B0E14",
    "notebook_tab_selected_fg": "#39C5BB",
    "paned_handle": "#1D2433",
    "find_match_bg": "#FF3D8B",
    "find_match_fg": "#FFFFFF",
    "input_bg": "#06090E",
    "input_fg": "#D1E8E7",
    "checkbutton_bg": "#141921",
    "checkbutton_fg": "#39C5BB",
    "dialog_bg": "#141921",
    "autocomplete_bg": "#1D2433",
    "autocomplete_fg": "#E0F7F6",
    "autocomplete_sel_bg": "#39C5BB",
    "autocomplete_sel_fg": "#000000"
  },
  "fonts": {
    "editor": ["Consolas", 10],
    "ui": ["Segoe UI", 9, "bold"],
    "title": ["Segoe UI", 12, "bold"]
  }
}

SUPPORTED_EXTENSIONS = {'.py', '.pyw', '.lua'}
ZIP_TEXT_EXTENSIONS = {'.py', '.pyw', '.lua', '.txt', '.json', '.md', '.cfg', '.toml', '.yaml', '.yml', '.xml', '.html', '.css', '.js'}

PYTHON_KEYWORDS = [
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield"
]

PYTHON_BUILTINS = [
    "abs", "all", "any", "bin", "bool", "breakpoint", "bytearray", "bytes",
    "callable", "chr", "classmethod", "compile", "complex", "delattr",
    "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter",
    "float", "format", "frozenset", "getattr", "globals", "hasattr",
    "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass",
    "iter", "len", "list", "locals", "map", "max", "memoryview", "min",
    "next", "object", "oct", "open", "ord", "pow", "print", "property",
    "range", "repr", "reversed", "round", "set", "setattr", "slice",
    "sorted", "staticmethod", "str", "sum", "super", "tuple", "type",
    "vars", "zip"
]

LUA_KEYWORDS = [
    "and", "break", "do", "else", "elseif", "end", "false", "for",
    "function", "goto", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "until", "while"
]

LUA_BUILTINS = [
    "assert", "collectgarbage", "dofile", "error", "getmetatable",
    "ipairs", "load", "loadfile", "next", "pairs", "pcall", "print",
    "rawequal", "rawget", "rawlen", "rawset", "require", "select",
    "setmetatable", "tonumber", "tostring", "type", "warn", "xpcall",
    "coroutine", "debug", "io", "math", "os", "package", "string",
    "table", "utf8"
]

class ThemeManager:
    def __init__(self):
        self.current_theme = DEFAULT_THEME.copy()
        self.registered_widgets = []

    def load_theme(self, theme_name: str):
        theme_path = THEMES_DIR / f"{theme_name}.json"
        if theme_path.exists():
            try:
                with open(theme_path, "r") as f:
                    user_theme = json.load(f)
                    self.current_theme = self._deep_merge(DEFAULT_THEME.copy(), user_theme)
            except Exception as e:
                print(f"Theme load error: {e}")
                self.current_theme = DEFAULT_THEME.copy()
        else:
            self.current_theme = DEFAULT_THEME.copy()
        self._apply_theme_to_widgets()

    def _deep_merge(self, base, update):
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    def get_color(self, key: str) -> str:
        return self.current_theme["colors"].get(key, DEFAULT_THEME["colors"][key])

    def get_font(self, key: str):
        font_spec = self.current_theme["fonts"].get(key, DEFAULT_THEME["fonts"][key])
        return tuple(font_spec)

    def register(self, widget, config_dict: Dict[str, str], is_text=False):
        self.registered_widgets.append((widget, config_dict, is_text))
        self._update_widget(widget, config_dict, is_text)

    def _update_widget(self, widget, config_dict: Dict[str, str], is_text=False):
        colors = self.current_theme["colors"]
        try:
            for prop, color_key in config_dict.items():
                color = colors.get(color_key, DEFAULT_THEME["colors"].get(color_key, "#ffffff"))
                if prop in ("background", "bg"):
                    widget.configure(bg=color)
                elif prop in ("foreground", "fg"):
                    if is_text:
                        widget.configure(foreground=color)
                    else:
                        widget.configure(fg=color)
                elif prop == "insertbackground":
                    widget.configure(insertbackground=color)
                elif prop == "selectbackground":
                    widget.configure(selectbackground=color)
                elif prop == "selectforeground":
                    if is_text:
                        widget.configure(selectforeground=color)
                elif prop == "troughcolor":
                    widget.configure(troughcolor=color)
                elif prop == "activebackground":
                    widget.configure(activebackground=color)
                elif prop == "activeforeground":
                    widget.configure(activeforeground=color)
                else:
                    widget.configure(**{prop: color})
        except Exception:
            pass

    def _apply_theme_to_widgets(self):
        colors = self.current_theme["colors"]
        style = ttk.Style()
        if os.name == 'nt':
            style.theme_use('clam')
        style.configure(".",
            background=colors["bg"],
            foreground=colors["fg"],
            troughcolor=colors["bg"],
            borderwidth=0,
            highlightthickness=0)
        style.configure("TFrame", background=colors["sidebar_bg"])
        style.configure("TPanedwindow", background=colors["bg"], borderwidth=0)
        style.configure("Sash", background=colors["paned_handle"], sashthickness=2)
        style.configure("TLabel", background=colors["sidebar_bg"], foreground=colors["fg"])
        style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
        style.map("TButton", background=[("active", colors["button_active_bg"])])
        style.configure("Treeview",
                        background=colors["tree_bg"],
                        foreground=colors["tree_fg"],
                        fieldbackground=colors["tree_bg"],
                        borderwidth=0)
        style.map("Treeview",
                  background=[("selected", colors["tree_selected_bg"])],
                  foreground=[("selected", colors["tree_selected_fg"])])
        style.configure("Treeview.Heading",
                        background=colors["sidebar_bg"],
                        foreground=colors["fg"],
                        borderwidth=1)
        style.configure("TNotebook", background=colors["notebook_bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=colors["notebook_tab_bg"],
                        foreground=colors["notebook_tab_fg"],
                        padding=[10, 2])
        style.map("TNotebook.Tab",
                  background=[("selected", colors["notebook_tab_selected_bg"])],
                  foreground=[("selected", colors["notebook_tab_selected_fg"])])
        style.configure("TScrollbar",
                        gripcount=0,
                        background=colors["scrollbar_bg"],
                        troughcolor=colors["scrollbar_trough"],
                        arrowcolor=colors["accent"],
                        borderwidth=0,
                        arrowsize=10)
        style.map("TScrollbar", background=[("active", colors["button_active_bg"])])
        style.configure("TEntry",
                        fieldbackground=colors["input_bg"],
                        foreground=colors["input_fg"])
        style.configure("TCheckbutton",
                        background=colors["checkbutton_bg"],
                        foreground=colors["checkbutton_fg"])
        style.map("TCheckbutton",
                  background=[("active", colors["sidebar_bg"])])
        style.configure("TCombobox",
                        fieldbackground=colors["input_bg"],
                        background=colors["button_bg"],
                        foreground=colors["fg"])
        style.map("TCombobox",
                  fieldbackground=[("readonly", colors["input_bg"])],
                  background=[("readonly", colors["button_bg"])],
                  arrowcolor=[("readonly", colors["accent"])])
        if hasattr(self, 'root'):
            self.root.configure(bg=colors["bg"])
        for widget, config_dict, is_text in self.registered_widgets:
            self._update_widget(widget, config_dict, is_text)

theme = ThemeManager()

class AutoCompletePopup(tk.Toplevel):
    def __init__(self, parent, editor, suggestions):
        super().__init__(parent)
        self.editor = editor
        self.suggestions = suggestions
        self.selected_index = 0
        self.overrideredirect(True)
        self.configure(bg=theme.get_color("autocomplete_bg"))
        self.listbox = tk.Listbox(
            self,
            bg=theme.get_color("autocomplete_bg"),
            fg=theme.get_color("autocomplete_fg"),
            selectbackground=theme.get_color("autocomplete_sel_bg"),
            selectforeground=theme.get_color("autocomplete_sel_fg"),
            font=theme.get_font("ui"),
            relief="flat",
            borderwidth=1,
            highlightthickness=0
        )
        self.listbox.pack(fill="both", expand=True)
        for s in suggestions:
            self.listbox.insert("end", s)
        self.listbox.select_set(0)
        self.listbox.focus_set()
        self.listbox.bind("<Up>", self._on_up)
        self.listbox.bind("<Down>", self._on_down)
        self.listbox.bind("<Return>", self._on_select)
        self.listbox.bind("<Tab>", self._on_select)
        self.listbox.bind("<Escape>", lambda e: self.destroy())
        self.listbox.bind("<ButtonRelease-1>", self._on_click)
        x, y, _, height = editor.text.bbox("insert")
        x += editor.text.winfo_rootx() + 10
        y += editor.text.winfo_rooty() + height + 10
        self.geometry(f"+{x}+{y}")

    def _on_up(self, event):
        if self.selected_index > 0:
            self.selected_index -= 1
            self.listbox.select_clear(0, "end")
            self.listbox.select_set(self.selected_index)
            self.listbox.see(self.selected_index)
        return "break"

    def _on_down(self, event):
        if self.selected_index < len(self.suggestions) - 1:
            self.selected_index += 1
            self.listbox.select_clear(0, "end")
            self.listbox.select_set(self.selected_index)
            self.listbox.see(self.selected_index)
        return "break"

    def _on_select(self, event):
        if 0 <= self.selected_index < len(self.suggestions):
            completion = self.suggestions[self.selected_index]
            self.editor.insert_completion(completion)
        self.destroy()
        return "break"

    def _on_click(self, event):
        idx = self.listbox.nearest(event.y)
        if idx >= 0:
            self.selected_index = idx
            self._on_select(event)

class CodeEditor(tk.Frame):
    def __init__(self, master, file_path: Path, on_modified_callback, initial_language=None, **kwargs):
        super().__init__(master, bg=theme.get_color("bg"), **kwargs)
        theme.register(self, {"background": "bg"})
        self.file_path = Path(file_path) if file_path else None
        self.on_modified = on_modified_callback
        self.language = initial_language or (self._detect_language(file_path) if file_path else 'python')
        self._highlight_job = None
        self._modified = False
        self._completion_popup = None
        self._opened_time = time.time()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.gutter = tk.Text(self, width=5, padx=5, takefocus=0, border=0,
                              bg=theme.get_color("gutter_bg"), fg=theme.get_color("gutter_fg"),
                              font=theme.get_font("editor"), state='disabled', wrap='none')
        self.gutter.grid(row=0, column=0, sticky='nsew')
        theme.register(self.gutter, {"background": "gutter_bg", "foreground": "gutter_fg"}, is_text=True)

        self.text = tk.Text(self, undo=True, wrap="none", font=theme.get_font("editor"),
                            bg=theme.get_color("bg"), fg=theme.get_color("fg"),
                            insertbackground=theme.get_color("fg"),
                            selectbackground=theme.get_color("select_bg"),
                            selectforeground=theme.get_color("select_fg"),
                            borderwidth=0, highlightthickness=0)
        self.text.grid(row=0, column=1, sticky='nsew')
        theme.register(self.text, {
            "background": "bg",
            "foreground": "fg",
            "insertbackground": "fg",
            "selectbackground": "select_bg",
            "selectforeground": "select_fg"
        }, is_text=True)

        vsb = ttk.Scrollbar(self, orient="vertical", command=self._on_scroll)
        vsb.grid(row=0, column=2, sticky='ns')
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.text.xview)
        hsb.grid(row=1, column=1, sticky='ew')
        self.text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._setup_tags()
        self._bind_events()

        if self.file_path and self.file_path.exists():
            try:
                content = self.file_path.read_text(encoding='utf-8')
                self.text.insert("1.0", content)
                self.text.edit_modified(False)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")
        self._update_line_numbers()
        self.apply_highlighting(force_full=True)

    def _detect_language(self, path: Path) -> str:
        ext = path.suffix.lower()
        if ext in ('.py', '.pyw'):
            return 'python'
        elif ext == '.lua':
            return 'lua'
        return 'text'

    def set_language(self, language: str):
        self.language = language
        self._setup_tags()
        self.apply_highlighting(force_full=True)

    def _setup_tags(self):
        colors = theme.current_theme["colors"]
        tag_configs = {
            "keyword": {"foreground": colors["highlight_kw"], "font": (theme.get_font("editor")[0], theme.get_font("editor")[1], "bold")},
            "string": {"foreground": colors["highlight_str"]},
            "comment": {"foreground": colors["highlight_comment"]},
            "number": {"foreground": colors["highlight_num"]},
            "function": {"foreground": colors["highlight_fn"]},
            "class": {"foreground": colors["highlight_class"]},
            "operator": {"foreground": colors["highlight_op"]},
            "find_match": {"background": colors["find_match_bg"], "foreground": colors["find_match_fg"]},
        }
        for tag, cfg in tag_configs.items():
            self.text.tag_configure(tag, **cfg)

    def _bind_events(self):
        self.text.bind("<<Modified>>", self._on_modified)
        self.text.bind("<KeyRelease>", self._on_key_release)
        self.text.bind("<Tab>", self._insert_spaces)
        self.text.bind("<Control-f>", lambda e: self.master.master.show_find_dialog(self))
        self.text.bind("<Control-s>", lambda e: self.save())
        self.text.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.text.bind("<F5>", lambda e: self.reload())
        self.text.bind("<Button-3>", self._show_context_menu)
        self.text.bind("<KeyRelease>", self._on_cursor_move, add=True)
        self.text.bind("<ButtonRelease-1>", self._on_cursor_move, add=True)

    def _on_cursor_move(self, event=None):
        if self.master and hasattr(self.master, 'master') and hasattr(self.master.master, 'update_discord_presence'):
            self.master.master.update_discord_presence()

    def _on_scroll(self, *args):
        self.text.yview(*args)
        self._update_line_numbers()

    def _update_line_numbers(self):
        self.gutter.config(state='normal')
        self.gutter.delete('1.0', tk.END)
        count = int(self.text.index('end-1c').split('.')[0])
        self.gutter.insert('1.0', "\n".join(str(i) for i in range(1, count + 1)))
        self.gutter.config(state='disabled')
        self.gutter.yview_moveto(self.text.yview()[0])

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self._update_line_numbers()
            self._modified = True
            self.on_modified(self, True)
        self.text.edit_modified(False)

    def _insert_spaces(self, event):
        self.text.insert(tk.INSERT, "    ")
        return "break"

    def _on_key_release(self, event=None):
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(1000, lambda: self.apply_highlighting(force_full=False))
        if event and event.keysym not in ("Up", "Down", "Left", "Right", "Return", "Tab", "Escape",
                                          "Control_L", "Control_R", "Shift_L", "Shift_R",
                                          "Alt_L", "Alt_R", "BackSpace", "Delete"):
            self._show_autocomplete()

    def _show_autocomplete(self):
        if self._completion_popup and self._completion_popup.winfo_exists():
            self._completion_popup.destroy()
            self._completion_popup = None
        cursor_pos = self.text.index("insert")
        line_start = f"{cursor_pos} linestart"
        line_text = self.text.get(line_start, cursor_pos)
        match = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*$', line_text)
        if not match:
            return
        prefix = match.group()
        if len(prefix) < 2:
            return
        if self.language == 'python':
            all_words = PYTHON_KEYWORDS + PYTHON_BUILTINS
        else:
            all_words = LUA_KEYWORDS + LUA_BUILTINS
        suggestions = [w for w in all_words if w.startswith(prefix)]
        if not suggestions:
            return
        self._completion_popup = AutoCompletePopup(self, self, suggestions)

    def insert_completion(self, completion: str):
        cursor_pos = self.text.index("insert")
        line_start = f"{cursor_pos} linestart"
        line_text = self.text.get(line_start, cursor_pos)
        match = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*$', line_text)
        if match:
            start_idx = f"{line_start}+{match.start()}c"
            self.text.delete(start_idx, cursor_pos)
            self.text.insert(start_idx, completion)
        else:
            self.text.insert(cursor_pos, completion)
        self.text.focus_set()

    def apply_highlighting(self, force_full=False):
        for tag in self.text.tag_names():
            if tag not in ("sel", "find_match"):
                self.text.tag_remove(tag, "1.0", tk.END)

        if force_full:
            content = self.text.get("1.0", "end-1c")
            self._highlight_content(content, "1.0")
        else:
            top = self.text.index("@0,0")
            bottom = self.text.index(f"@0,{self.text.winfo_height()}")
            content = self.text.get(top, bottom)
            self._highlight_content(content, top)

    def _highlight_content(self, content: str, start_index: str):
        if not content.strip():
            return
        if HAS_PYGMENTS:
            self._highlight_pygments(content, start_index)
        else:
            self._highlight_basic(content, start_index)

    def _highlight_pygments(self, content: str, start_index: str):
        try:
            if self.language == 'python':
                lexer = PythonLexer()
            elif self.language == 'lua':
                lexer = LuaLexer()
            else:
                lexer = get_lexer_for_filename(str(self.file_path)) if self.file_path else PythonLexer()
        except:
            return
        token_map = {
            Token.Keyword: "keyword",
            Token.Keyword.Constant: "keyword",
            Token.Keyword.Declaration: "keyword",
            Token.Keyword.Namespace: "keyword",
            Token.Keyword.Reserved: "keyword",
            Token.Keyword.Type: "keyword",
            Token.Name.Function: "function",
            Token.Name.Class: "class",
            Token.String: "string",
            Token.String.Doc: "string",
            Token.String.Single: "string",
            Token.String.Double: "string",
            Token.Comment: "comment",
            Token.Comment.Single: "comment",
            Token.Comment.Multiline: "comment",
            Token.Number: "number",
            Token.Number.Integer: "number",
            Token.Number.Float: "number",
            Token.Operator: "operator",
            Token.Punctuation: "operator",
        }
        last_pos = 0
        for token, value in pygments.lex(content, lexer):
            if not value:
                continue
            start = f"{start_index} + {last_pos} chars"
            end = f"{start_index} + {last_pos + len(value)} chars"
            tag = token_map.get(token)
            if tag:
                self.text.tag_add(tag, start, end)
            last_pos += len(value)

    def _highlight_basic(self, content: str, start_index: str):
        if self.language == 'python':
            keywords = r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b'
        elif self.language == 'lua':
            keywords = r'\b(and|break|do|else|elseif|end|false|for|function|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b'
        else:
            return
        for match in re.finditer(keywords, content):
            start = f"{start_index} + {match.start()} chars"
            end = f"{start_index} + {match.end()} chars"
            self.text.tag_add("keyword", start, end)
        for match in re.finditer(r'"[^"\\]*(\\.[^"\\]*)*"|\'[^\'\\]*(\\.[^\'\\]*)*\'', content):
            start = f"{start_index} + {match.start()} chars"
            end = f"{start_index} + {match.end()} chars"
            self.text.tag_add("string", start, end)
        comment_pattern = r'#[^\n]*|--[^\n]*' if self.language == 'python' else r'--[^\n]*'
        for match in re.finditer(comment_pattern, content):
            start = f"{start_index} + {match.start()} chars"
            end = f"{start_index} + {match.end()} chars"
            self.text.tag_add("comment", start, end)

    def _show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0,
                       bg=theme.get_color("menu_bg"),
                       fg=theme.get_color("menu_fg"),
                       activebackground=theme.get_color("menu_active_bg"),
                       activeforeground=theme.get_color("menu_active_fg"))
        menu.add_command(label="Cut", command=self.cut)
        menu.add_command(label="Copy", command=self.copy)
        menu.add_command(label="Paste", command=self.paste)
        menu.add_separator()
        menu.add_command(label="Select All", command=self.select_all)
        menu.tk_popup(event.x_root, event.y_root)

    def cut(self): self.text.event_generate("<<Cut>>")
    def copy(self): self.text.event_generate("<<Copy>>")
    def paste(self): self.text.event_generate("<<Paste>>")
    def select_all(self): self.text.tag_add("sel", "1.0", "end")

    def get_content(self) -> str:
        return self.text.get("1.0", "end-1c")

    def get_cursor_position(self):
        cursor = self.text.index("insert")
        line, col = cursor.split('.')
        return int(line), int(col)

    def get_total_chars(self):
        return len(self.get_content())

    def save(self) -> bool:
        if not self.file_path or not self.file_path.absolute():
            return self.save_as()
        try:
            self.file_path.write_text(self.get_content(), encoding='utf-8')
            self._modified = False
            self.on_modified(self, False)
            return True
        except Exception as e:
            messagebox.showerror("Save Error", str(e))
            return False

    def save_as(self) -> bool:
        new_path = filedialog.asksaveasfilename(
            defaultextension=".py" if self.language == 'python' else ".lua",
            filetypes=[("Python Files", "*.py;*.pyw"), ("Lua Files", "*.lua"), ("All Files", "*.*")]
        )
        if not new_path:
            return False
        self.file_path = Path(new_path)
        self.language = self._detect_language(self.file_path)
        self._setup_tags()
        return self.save()

    def reload(self):
        if self._modified:
            if not messagebox.askyesno("Reload", "Discard unsaved changes?"):
                return
        if self.file_path and self.file_path.exists():
            try:
                content = self.file_path.read_text(encoding='utf-8')
                self.text.delete("1.0", tk.END)
                self.text.insert("1.0", content)
                self.text.edit_modified(False)
                self._modified = False
                self.on_modified(self, False)
                self.apply_highlighting(force_full=True)
            except Exception as e:
                messagebox.showerror("Reload Error", str(e))

    def is_modified(self) -> bool:
        return self._modified

    def toggle_word_wrap(self):
        current = self.text.cget("wrap")
        self.text.configure(wrap="word" if current == "none" else "none")

    def toggle_line_numbers(self):
        if self.gutter.winfo_ismapped():
            self.gutter.grid_remove()
        else:
            self.gutter.grid()

class FileBrowser(ttk.Frame):
    def __init__(self, master, app, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app
        theme.register(self, {"background": "sidebar_bg"})
        self.tree = ttk.Treeview(self, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewOpen>>", self._on_open_node)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<ButtonPress-1>", self._on_drag_start)
        self.tree.bind("<B1-Motion>", self._on_drag_motion)
        self.tree.bind("<ButtonRelease-1>", self._on_drag_release)
        self._drag_data = {"x": 0, "y": 0, "item": None}
        self._populate_roots()

    def _populate_roots(self):
        if os.name == 'nt':
            import string
            for drive in string.ascii_uppercase:
                path = f"{drive}:\\"
                if os.path.exists(path):
                    iid = f"drive_{path}"
                    node = self.tree.insert("", "end", iid=iid, text=f"💾 {path}", open=False)
                    self.tree.insert(node, "end", text="dummy")
        else:
            root = "/"
            iid = f"root_{root}"
            node = self.tree.insert("", "end", iid=iid, text="/", open=True)
            self._populate_directory(node, root)
        modules_path = str(BASE_MODULES_DIR)
        iid = f"quick_modules_{modules_path}"
        modules_node = self.tree.insert("", "end", iid=iid, text="📁 Modules", open=False)
        self.tree.insert(modules_node, "end", text="dummy")

    def _on_open_node(self, event):
        node = self.tree.focus()
        if not node:
            return
        children = self.tree.get_children(node)
        if len(children) == 1 and self.tree.item(children[0], "text") == "dummy":
            self.tree.delete(children[0])
            if node.startswith("drive_"):
                path_str = node[6:]
            elif node.startswith("quick_modules_"):
                path_str = node[14:]
            elif node.startswith("root_"):
                path_str = node[5:]
            else:
                path_str = node
            self._populate_directory(node, path_str)

    def _populate_directory(self, parent_iid: str, path_str: str):
        path = Path(path_str)
        try:
            items = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            return
        for item in items:
            item_iid = str(item)
            if item.is_dir():
                if not self.tree.exists(item_iid):
                    node = self.tree.insert(parent_iid, "end", iid=item_iid, text=f"📁 {item.name}", open=False)
                    self.tree.insert(node, "end", text="dummy")
            elif item.suffix.lower() in SUPPORTED_EXTENSIONS:
                if not self.tree.exists(item_iid):
                    self.tree.insert(parent_iid, "end", iid=item_iid, text=f"📄 {item.name}")

    def _on_double_click(self, event):
        item = self.tree.focus()
        if item.startswith("drive_"):
            path_str = item[6:]
        elif item.startswith("quick_modules_"):
            path_str = item[14:]
        elif item.startswith("root_"):
            path_str = item[5:]
        else:
            path_str = item
        if os.path.isfile(path_str):
            self.app.open_file(Path(path_str))

    def _on_drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self._drag_data["item"] = item
            self._drag_data["x"] = event.x
            self._drag_data["y"] = event.y

    def _on_drag_motion(self, event):
        pass

    def _on_drag_release(self, event):
        if not self._drag_data["item"]:
            return
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if isinstance(widget, tk.Text) or isinstance(widget, ttk.Notebook):
            item = self._drag_data["item"]
            if item.startswith("drive_"):
                path_str = item[6:]
            elif item.startswith("quick_modules_"):
                path_str = item[14:]
            elif item.startswith("root_"):
                path_str = item[5:]
            else:
                path_str = item
            if os.path.isfile(path_str):
                self.app.open_file(Path(path_str))
        self._drag_data = {"x": 0, "y": 0, "item": None}

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
            if item.startswith("drive_"):
                path_str = item[6:]
            elif item.startswith("quick_modules_"):
                path_str = item[14:]
            elif item.startswith("root_"):
                path_str = item[5:]
            else:
                path_str = item
            path = Path(path_str)
            if path.is_dir():
                menu = tk.Menu(self, tearoff=0,
                               bg=theme.get_color("menu_bg"),
                               fg=theme.get_color("menu_fg"),
                               activebackground=theme.get_color("menu_active_bg"),
                               activeforeground=theme.get_color("menu_active_fg"))
                menu.add_command(label="New File", command=lambda: self._new_file(path))
                menu.add_command(label="New Folder", command=lambda: self._new_folder(path))
                menu.add_separator()
                menu.add_command(label="Refresh", command=self.refresh)
                menu.tk_popup(event.x_root, event.y_root)

    def _new_file(self, parent_dir: Path):
        name = simpledialog.askstring("New File", "Enter file name (with extension):")
        if name:
            file_path = parent_dir / name
            try:
                file_path.touch()
                self.refresh()
                self.app.open_file(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create file: {e}")

    def _new_folder(self, parent_dir: Path):
        name = simpledialog.askstring("New Folder", "Enter folder name:")
        if name:
            folder_path = parent_dir / name
            try:
                folder_path.mkdir()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Could not create folder: {e}")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._populate_roots()

class FindDialog(tk.Toplevel):
    def __init__(self, parent, editor: CodeEditor):
        super().__init__(parent)
        self.editor = editor
        self.title("Find")
        self.geometry("350x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(bg=theme.get_color("dialog_bg"))
        ttk.Label(self, text="Find:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.find_var = tk.StringVar()
        entry = ttk.Entry(self, textvariable=self.find_var, width=30)
        entry.grid(row=0, column=1, padx=5, pady=5)
        entry.focus_set()
        self.case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Match case", variable=self.case_var).grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        self.regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Regular expression", variable=self.regex_var).grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky="w")
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="Find Next", command=self.find_next).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side="left", padx=5)
        self.bind("<Return>", lambda e: self.find_next())
        self.bind("<Escape>", lambda e: self.close())

    def find_next(self):
        text_widget = self.editor.text
        search_str = self.find_var.get()
        if not search_str:
            return
        text_widget.tag_remove("find_match", "1.0", tk.END)
        nocase = not self.case_var.get()
        regexp = self.regex_var.get()
        start_pos = text_widget.index("insert")
        if regexp:
            pos = text_widget.search(search_str, start_pos, stopindex="end", regexp=True, nocase=nocase)
        else:
            pos = text_widget.search(search_str, start_pos, stopindex="end", nocase=nocase)
        if not pos:
            if regexp:
                pos = text_widget.search(search_str, "1.0", stopindex="end", regexp=True, nocase=nocase)
            else:
                pos = text_widget.search(search_str, "1.0", stopindex="end", nocase=nocase)
            if not pos:
                messagebox.showinfo("Find", "Text not found.")
                return
        end_pos = f"{pos}+{len(search_str)}c"
        text_widget.tag_remove("sel", "1.0", tk.END)
        text_widget.tag_add("sel", pos, end_pos)
        text_widget.mark_set("insert", end_pos)
        text_widget.see(pos)
        start = "1.0"
        while True:
            if regexp:
                p = text_widget.search(search_str, start, stopindex="end", regexp=True, nocase=nocase)
            else:
                p = text_widget.search(search_str, start, stopindex="end", nocase=nocase)
            if not p:
                break
            text_widget.tag_add("find_match", p, f"{p}+{len(search_str)}c")
            start = f"{p}+1c"

    def close(self):
        self.editor.text.tag_remove("find_match", "1.0", tk.END)
        self.destroy()

class CompactChatPanel(tk.Frame):
    def __init__(self, master, editor_app, **kwargs):
        super().__init__(master, bg=theme.get_color("chat_bg"), **kwargs)
        self.editor_app = editor_app
        self.attached_image_b64 = None
        self.zip_extract_path = None
        self.zip_file_list = []

        lbl = tk.Label(self, text="🪐 Saturn Chat (Gemma3)", font=theme.get_font("title"),
                       bg=theme.get_color("chat_bg"), fg=theme.get_color("accent"))
        lbl.pack(pady=(5,0))
        theme.register(lbl, {"background": "chat_bg", "foreground": "accent"})

        self.chat_display = tk.Text(self, wrap="word", font=theme.get_font("ui"),
                                    bg=theme.get_color("bg"), fg=theme.get_color("fg"),
                                    state="disabled", height=15, relief="flat")
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        theme.register(self.chat_display, {"background": "bg", "foreground": "fg"}, is_text=True)
        self.chat_display.tag_configure("code", background=theme.get_color("select_bg"), font=("Consolas", 10))

        input_frame = tk.Frame(self, bg=theme.get_color("chat_bg"))
        input_frame.pack(fill="x", padx=5, pady=5)
        theme.register(input_frame, {"background": "chat_bg"})
        input_frame.grid_columnconfigure(0, weight=1)

        self.msg_input = tk.Text(input_frame, wrap="word", font=theme.get_font("ui"),
                                 bg=theme.get_color("chat_input_bg"), fg=theme.get_color("fg"),
                                 insertbackground=theme.get_color("fg"), height=4)
        self.msg_input.grid(row=0, column=0, sticky="ew")
        theme.register(self.msg_input, {"background": "chat_input_bg", "foreground": "fg", "insertbackground": "fg"}, is_text=True)

        input_scroll = ttk.Scrollbar(input_frame, orient="vertical", command=self.msg_input.yview)
        input_scroll.grid(row=0, column=1, sticky="ns")
        self.msg_input.configure(yscrollcommand=input_scroll.set)

        btn_frame = tk.Frame(self, bg=theme.get_color("chat_bg"))
        btn_frame.pack(fill="x", padx=5, pady=(0,5))
        theme.register(btn_frame, {"background": "chat_bg"})

        btn_upload_img = tk.Button(btn_frame, text="🖼️ Upload Image", command=self.upload_image,
                                   bg=theme.get_color("button_bg"), fg=theme.get_color("button_fg"),
                                   activebackground=theme.get_color("button_active_bg"))
        btn_upload_img.pack(side="left", padx=2)
        theme.register(btn_upload_img, {"background": "button_bg", "foreground": "button_fg", "activebackground": "button_active_bg"})

        btn_upload_zip = tk.Button(btn_frame, text="📦 Upload ZIP", command=self.upload_zip,
                                   bg=theme.get_color("button_bg"), fg=theme.get_color("button_fg"),
                                   activebackground=theme.get_color("button_active_bg"))
        btn_upload_zip.pack(side="left", padx=2)
        theme.register(btn_upload_zip, {"background": "button_bg", "foreground": "button_fg", "activebackground": "button_active_bg"})

        btn_clear_zip = tk.Button(btn_frame, text="🗑️ Clear ZIP", command=self.clear_zip,
                                  bg=theme.get_color("button_bg"), fg=theme.get_color("button_fg"),
                                  activebackground=theme.get_color("button_active_bg"))
        btn_clear_zip.pack(side="left", padx=2)
        theme.register(btn_clear_zip, {"background": "button_bg", "foreground": "button_fg", "activebackground": "button_active_bg"})

        btn_send = tk.Button(btn_frame, text="Send", command=self.send_message,
                             bg=theme.get_color("accent"), fg=theme.get_color("accent_fg"),
                             activebackground=theme.get_color("button_active_bg"))
        btn_send.pack(side="left", padx=2)
        theme.register(btn_send, {"background": "accent", "foreground": "accent_fg", "activebackground": "button_active_bg"})

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if file_path:
            with open(file_path, "rb") as f:
                self.attached_image_b64 = base64.b64encode(f.read()).decode('utf-8')
            self.append_text("System", f"📎 Image attached: {Path(file_path).name}")

    def upload_zip(self):
        zip_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if not zip_path:
            return
        try:
            self.clear_zip()
            self.zip_extract_path = Path(tempfile.mkdtemp())
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(self.zip_extract_path)

            self.zip_file_list = []
            for root, dirs, files in os.walk(self.zip_extract_path):
                for f in files:
                    full = Path(root) / f
                    rel = full.relative_to(self.zip_extract_path)
                    if full.suffix.lower() in ZIP_TEXT_EXTENSIONS:
                        self.zip_file_list.append(str(rel))

            summary = f"📦 ZIP loaded: {Path(zip_path).name}\n{len(self.zip_file_list)} text files extracted.\n"
            summary += "You can ask for any file's content naturally (e.g., 'Show me TTS.py').\n"
            summary += "Files:\n" + "\n".join(self.zip_file_list[:30])
            if len(self.zip_file_list) > 30:
                summary += f"\n... and {len(self.zip_file_list)-30} more"
            self.append_text("System", summary)
        except Exception as e:
            messagebox.showerror("ZIP Error", f"Failed to read ZIP:\n{e}")

    def clear_zip(self):
        if self.zip_extract_path and self.zip_extract_path.exists():
            try:
                shutil.rmtree(self.zip_extract_path)
            except:
                pass
        self.zip_extract_path = None
        self.zip_file_list = []
        self.append_text("System", "🗑️ ZIP context cleared.")

    def append_text(self, role, text):
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"{role}: ")
        parts = re.split(r'(```[\s\S]*?```)', text)
        for part in parts:
            if part.startswith('```') and part.endswith('```'):
                code = part[3:-3].strip()
                if code.startswith('python') or code.startswith('lua'):
                    code = code[code.find('\n')+1:] if '\n' in code else code
                self.chat_display.insert("end", code, "code")
                self._add_copy_button(code)
            else:
                self.chat_display.insert("end", part)
        self.chat_display.insert("end", "\n\n")
        self.chat_display.see("end")
        self.chat_display.config(state="disabled")

    def _add_copy_button(self, code):
        btn = tk.Button(self.chat_display, text="📋 Copy", command=lambda: self.copy_code(code),
                        bg=theme.get_color("button_bg"), fg=theme.get_color("button_fg"), relief="flat")
        self.chat_display.window_create("end", window=btn)
        self.chat_display.insert("end", "\n")

    def copy_code(self, code):
        self.clipboard_clear()
        self.clipboard_append(code)

    def _try_auto_read_file(self, text: str) -> bool:
        if not self.zip_extract_path:
            return False
        patterns = [
            r'(?:show|print|display|read|get|open)\s+(?:me\s+)?(?:the\s+)?(?:contents?\s+of\s+)?["\']?([\w\\/. -]+\.\w+)["\']?',
            r'(?:contents?\s+of\s+)([\w\\/. -]+\.\w+)',
            r'([\w\\/. -]+\.\w+)(?:\s+file)?'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                if filename in self.zip_file_list:
                    self._read_and_append_file(filename)
                    return True
                lower_filename = filename.lower()
                for f in self.zip_file_list:
                    if f.lower().endswith(lower_filename) or lower_filename in f.lower():
                        self._read_and_append_file(f)
                        return True
        return False

    def _read_and_append_file(self, filename: str):
        full_path = self.zip_extract_path / filename
        if full_path.exists() and full_path.is_file():
            try:
                content = full_path.read_text(encoding='utf-8', errors='replace')
                display_content = content
                if len(content) > 50000:
                    display_content = content[:25000] + "\n...[TRUNCATED]...\n" + content[-25000:]
                self.append_text("System", f"📄 Content of `{filename}`:\n```\n{display_content}\n```")
                self._last_auto_read_content = content
                self._last_auto_read_filename = filename
            except Exception as e:
                self.append_text("System", f"Error reading file: {e}")
        else:
            self.append_text("System", f"File not found: {filename}")

    def send_message(self):
        user_text = self.msg_input.get("1.0", "end-1c").strip()
        if not user_text and not self.attached_image_b64 and not self.zip_extract_path:
            return
        auto_read = self._try_auto_read_file(user_text)
        if auto_read:
            pass
        self.append_text("You", user_text)
        self.msg_input.delete("1.0", tk.END)
        if not OLLAMA_AVAILABLE:
            self.append_text("System", "Ollama is not installed.")
            return
        threading.Thread(target=self._get_ai_response, args=(user_text,), daemon=True).start()

    def _get_ai_response(self, user_text):
        try:
            editor = self.editor_app.current_editor
            current_code = editor.get_content() if editor else ""

            system_msg = (
                "You are Saturn, a helpful AI coding assistant. "
                "The user has uploaded a ZIP file. You can see the list of files below. "
                "If the user asks for a specific file's content, the system will automatically read it and show it. "
                "If you need to see a file, ask the user to show it. "
                "Provide code in proper markdown code blocks."
            )
            messages = [{"role": "system", "content": system_msg}]

            if current_code:
                messages.append({"role": "user", "content": f"Current code context:\n```\n{current_code}\n```"})
            if self.zip_file_list:
                file_list_str = "\n".join(self.zip_file_list[:50])
                if len(self.zip_file_list) > 50:
                    file_list_str += f"\n... and {len(self.zip_file_list)-50} more"
                messages.append({"role": "user", "content": f"ZIP file contains these text files:\n{file_list_str}"})
            if hasattr(self, '_last_auto_read_content') and self._last_auto_read_content:
                messages.append({"role": "user", "content": f"Here is the content of `{self._last_auto_read_filename}`:\n```\n{self._last_auto_read_content}\n```"})
                delattr(self, '_last_auto_read_content')
                delattr(self, '_last_auto_read_filename')
            msg = {"role": "user", "content": user_text}
            if self.attached_image_b64:
                msg["images"] = [self.attached_image_b64]
                self.attached_image_b64 = None
            messages.append(msg)
            response = ollama.chat(model='gemma3:4b', messages=messages)
            self.after(0, lambda: self.append_text("Saturn", response['message']['content']))
        except Exception as e:
            self.after(0, lambda: self.append_text("Error", str(e)))

class ModuleEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Module Editor - Melroms Launcher")
        self.root.geometry("1400x900")
        self.root.configure(bg=theme.get_color("sidebar_bg"))
        theme.register(self.root, {"background": "sidebar_bg"})
        self.tabs: Dict[str, CodeEditor] = {}
        self.current_editor: Optional[CodeEditor] = None
        self.global_language = tk.StringVar(value="python")
        self._drag_tab_data = None
        self._rpc = None
        self._rpc_running = True
        self._rpc_thread = None
        self._setup_ui()
        self._setup_statusbar()
        self._setup_menu()
        self._setup_toolbar()
        self.load_theme("Miku_Cyber")
        self.load_session()
        try:
            base_dir = os.path.dirname(__file__)
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icon failed to load: {e}")
        self._init_discord_rpc()
        self._start_rpc_updater()

    def _init_discord_rpc(self):
        if not DISCORD_RPC_AVAILABLE:
            return
        try:
            CLIENT_ID = "1472951903636947150"
            self._rpc = Presence(CLIENT_ID)
            self._rpc.connect()
            print("Discord RPC connected")
        except Exception as e:
            print(f"Failed to connect Discord RPC: {e}")
            self._rpc = None

    def _start_rpc_updater(self):
        if not self._rpc:
            return
        def updater():
            while self._rpc_running:
                self.update_discord_presence()
                time.sleep(15)
        self._rpc_thread = threading.Thread(target=updater, daemon=True)
        self._rpc_thread.start()

    def update_discord_presence(self):
        if not self._rpc:
            return
        editor = self.current_editor
        if not editor:
            return
        file_name = editor.file_path.name if editor.file_path else "Untitled"
        language = editor.language.upper()
        if language == 'TEXT':
            language = 'Plain Text'
        line, col = editor.get_cursor_position()
        total_chars = editor.get_total_chars()
        elapsed = time.time() - editor._opened_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        time_str = f"{minutes}m {seconds}s"
        details = f"Working on {file_name}"
        state = f"Line {line}, Col {col} | {total_chars} chars | {language}"
        try:
            self._rpc.update(
                details=details,
                state=state,
                start=int(editor._opened_time),
                large_image="miku_icon",
                large_text="MelRoms Editor",
                small_image="python" if language == "PYTHON" else "lua" if language == "LUA" else "text",
                small_text=language,
                buttons=[{"label": "Get MelRoms", "url": "https://github.com/MelodyIV/MelRoms"}]
            )
        except Exception as e:
            print(f"RPC update error: {e}")

    def _setup_ui(self):
        self.paned = ttk.PanedWindow(self.root, orient="horizontal")
        self.paned.pack(fill="both", expand=True)
        self.paned.configure(style="TPanedwindow")
        self.file_browser = FileBrowser(self.paned, self, width=300)
        self.paned.add(self.file_browser, weight=0)
        self.notebook = ttk.Notebook(self.paned)
        self.paned.add(self.notebook, weight=1)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.notebook.bind("<ButtonPress-1>", self._on_tab_drag_start)
        self.notebook.bind("<B1-Motion>", self._on_tab_drag_motion)
        self.notebook.bind("<ButtonRelease-1>", self._on_tab_drag_release)
        self.chat_panel = CompactChatPanel(self.paned, self, width=350)
        self.paned.add(self.chat_panel)

    def _setup_statusbar(self):
        self.status_var = tk.StringVar(value="Ready")
        status = tk.Label(self.root, textvariable=self.status_var, bg=theme.get_color("status_bg"),
                          fg=theme.get_color("status_fg"), anchor="w")
        status.pack(side="bottom", fill="x")
        theme.register(status, {"background": "status_bg", "foreground": "status_fg"})

    def _setup_menu(self):
        menubar = tk.Menu(self.root,
                          bg=theme.get_color("menu_bg"),
                          fg=theme.get_color("menu_fg"),
                          activebackground=theme.get_color("menu_active_bg"),
                          activeforeground=theme.get_color("menu_active_fg"))
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0,
                            bg=theme.get_color("menu_bg"),
                            fg=theme.get_color("menu_fg"),
                            activebackground=theme.get_color("menu_active_bg"),
                            activeforeground=theme.get_color("menu_active_fg"))
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open...", accelerator="Ctrl+O", command=self.open_file_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_current)
        file_menu.add_command(label="Save As...", accelerator="Ctrl+Shift+S", command=self.save_as_current)
        file_menu.add_command(label="Save All", command=self.save_all)
        file_menu.add_separator()
        file_menu.add_command(label="Execute", accelerator="F5", command=self.execute_current)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_current_tab)
        file_menu.add_command(label="Exit", command=self.root.quit)
        edit_menu = tk.Menu(menubar, tearoff=0,
                            bg=theme.get_color("menu_bg"),
                            fg=theme.get_color("menu_fg"),
                            activebackground=theme.get_color("menu_active_bg"),
                            activeforeground=theme.get_color("menu_active_fg"))
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="Copy", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="Paste", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find...", accelerator="Ctrl+F", command=self.show_find_dialog_current)
        edit_menu.add_command(label="Replace...", accelerator="Ctrl+H", command=self.show_replace_dialog)
        view_menu = tk.Menu(menubar, tearoff=0,
                            bg=theme.get_color("menu_bg"),
                            fg=theme.get_color("menu_fg"),
                            activebackground=theme.get_color("menu_active_bg"),
                            activeforeground=theme.get_color("menu_active_fg"))
        menubar.add_cascade(label="View", menu=view_menu)
        self.word_wrap_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="Word Wrap", variable=self.word_wrap_var, command=self.toggle_word_wrap)
        self.line_num_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label="Line Numbers", variable=self.line_num_var, command=self.toggle_line_numbers)
        view_menu.add_separator()
        view_menu.add_command(label="Refresh File Tree", command=self.file_browser.refresh)
        tools_menu = tk.Menu(menubar, tearoff=0,
                             bg=theme.get_color("menu_bg"),
                             fg=theme.get_color("menu_fg"),
                             activebackground=theme.get_color("menu_active_bg"),
                             activeforeground=theme.get_color("menu_active_fg"))
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Add Module", command=self.create_module)
        tools_menu.add_separator()
        theme_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Theme", menu=theme_menu)
        for theme_file in THEMES_DIR.glob("*.json"):
            name = theme_file.stem
            theme_menu.add_command(label=name, command=lambda n=name: self.load_theme(n))
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.root.bind("<Control-s>", lambda e: self.save_current())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as_current())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-f>", lambda e: self.show_find_dialog_current())
        self.root.bind("<Control-h>", lambda e: self.show_replace_dialog())
        self.root.bind("<F5>", lambda e: self.execute_current())

    def _setup_toolbar(self):
        toolbar = tk.Frame(self.root, bg=theme.get_color("toolbar_bg"), height=36)
        toolbar.pack(side="top", fill="x")
        theme.register(toolbar, {"background": "toolbar_bg"})
        lang_frame = tk.Frame(toolbar, bg=theme.get_color("toolbar_bg"))
        lang_frame.pack(side="left", padx=5)
        theme.register(lang_frame, {"background": "toolbar_bg"})
        lang_label = tk.Label(lang_frame, text="Language:", bg=theme.get_color("toolbar_bg"), fg=theme.get_color("fg"))
        lang_label.pack(side="left")
        theme.register(lang_label, {"background": "toolbar_bg", "foreground": "fg"})
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.global_language,
                                       values=["python", "lua"], state="readonly", width=8)
        self.lang_combo.pack(side="left", padx=5)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_changed)
        buttons = [
            ("New", self.new_file),
            ("Open", self.open_file_dialog),
            ("Save", self.save_current),
            ("Save As", self.save_as_current),
            ("Execute", self.execute_current),
            ("Find", self.show_find_dialog_current),
        ]
        for text, cmd in buttons:
            btn = tk.Button(toolbar, text=text, command=cmd,
                            bg=theme.get_color("button_bg"),
                            fg=theme.get_color("button_fg"),
                            activebackground=theme.get_color("button_active_bg"),
                            relief="flat", padx=8, pady=2)
            btn.pack(side="left", padx=2, pady=2)
            theme.register(btn, {"background": "button_bg", "foreground": "button_fg", "activebackground": "button_active_bg"})

    def _on_tab_drag_start(self, event):
        try:
            index = self.notebook.index(f"@{event.x},{event.y}")
            if index >= 0:
                self._drag_tab_data = {"index": index, "widget": self.notebook.tabs()[index]}
        except:
            pass

    def _on_tab_drag_motion(self, event):
        pass

    def _on_tab_drag_release(self, event):
        if not self._drag_tab_data:
            return
        target_widget = event.widget.winfo_containing(event.x_root, event.y_root)
        if isinstance(target_widget, ttk.Treeview):
            item = target_widget.identify_row(event.y_root - target_widget.winfo_rooty())
            if item:
                if item.startswith("drive_"):
                    folder_str = item[6:]
                elif item.startswith("quick_modules_"):
                    folder_str = item[14:]
                elif item.startswith("root_"):
                    folder_str = item[5:]
                else:
                    folder_str = item
                folder_path = Path(folder_str)
                if folder_path.is_dir():
                    tab_id = self._drag_tab_data["widget"]
                    for editor in self.tabs.values():
                        if str(editor) == tab_id:
                            if editor.file_path:
                                if editor.is_modified():
                                    editor.save()
                                new_path = folder_path / editor.file_path.name
                                try:
                                    shutil.move(str(editor.file_path), str(new_path))
                                    editor.file_path = new_path
                                    self.file_browser.refresh()
                                    self.status_var.set(f"Moved to {new_path}")
                                except Exception as e:
                                    messagebox.showerror("Move Error", str(e))
                            break
        self._drag_tab_data = None

    def _on_language_changed(self, event=None):
        new_lang = self.global_language.get()
        if self.current_editor:
            self.current_editor.set_language(new_lang)
            self.status_var.set(f"Language set to {new_lang}")

    def load_theme(self, theme_name):
        theme.load_theme(theme_name)
        for editor in self.tabs.values():
            editor._setup_tags()
            editor.apply_highlighting(force_full=True)

    def new_file(self):
        editor = CodeEditor(self.notebook, None, self._on_editor_modified, initial_language=self.global_language.get())
        tab_id = f"untitled_{id(editor)}"
        self.tabs[tab_id] = editor
        self.notebook.add(editor, text="Untitled")
        self.notebook.select(editor)

    def open_file_dialog(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Python/Lua", "*.py;*.pyw;*.lua"), ("All Files", "*.*")]
        )
        for p in paths:
            self.open_file(Path(p))

    def open_file(self, path: Path):
        path_str = str(path.absolute())
        if path_str in self.tabs:
            self.notebook.select(self.tabs[path_str])
            return
        editor = CodeEditor(self.notebook, path, self._on_editor_modified)
        self.tabs[path_str] = editor
        self.notebook.add(editor, text=path.name)
        self.notebook.select(editor)
        self._save_session()
        self.update_discord_presence()

    def _on_editor_modified(self, editor: CodeEditor, modified: bool):
        for key, ed in self.tabs.items():
            if ed == editor:
                idx = self.notebook.index(editor)
                title = editor.file_path.name if editor.file_path else "Untitled"
                if modified:
                    title = "*" + title
                self.notebook.tab(idx, text=title)
                break
        if editor == self.current_editor:
            self.update_discord_presence()

    def _on_tab_changed(self, event):
        current = self.notebook.select()
        if current:
            for editor in self.tabs.values():
                if str(editor) == current:
                    self.current_editor = editor
                    name = editor.file_path.name if editor.file_path else "Untitled"
                    self.status_var.set(f"Editing: {name}")
                    self.global_language.set(editor.language)
                    self.update_discord_presence()
                    break
        else:
            self.current_editor = None
            self.status_var.set("Ready")

    def save_current(self):
        if self.current_editor:
            if self.current_editor.save():
                if self.current_editor.file_path:
                    new_key = str(self.current_editor.file_path.absolute())
                    old_key = next((k for k, v in self.tabs.items() if v == self.current_editor), None)
                    if old_key and old_key != new_key:
                        del self.tabs[old_key]
                        self.tabs[new_key] = self.current_editor
                self.status_var.set(f"Saved: {self.current_editor.file_path.name}")
                self._save_session()
                self.update_discord_presence()

    def save_as_current(self):
        if self.current_editor:
            if self.current_editor.save_as():
                new_key = str(self.current_editor.file_path.absolute())
                old_key = next((k for k, v in self.tabs.items() if v == self.current_editor), None)
                if old_key and old_key != new_key:
                    del self.tabs[old_key]
                    self.tabs[new_key] = self.current_editor
                self._on_editor_modified(self.current_editor, False)
                self._save_session()
                self.update_discord_presence()

    def save_all(self):
        for editor in self.tabs.values():
            if editor.is_modified():
                editor.save()
        self._save_session()

    def execute_current(self):
        if not self.current_editor:
            return
        if self.current_editor.is_modified() or not self.current_editor.file_path:
            if not self.current_editor.save():
                return
        script_path = self.current_editor.file_path
        lang = self.current_editor.language
        try:
            if lang == 'python':
                subprocess.Popen(['pythonw', str(script_path)], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            elif lang == 'lua':
                subprocess.Popen(['lua', str(script_path)])
            else:
                messagebox.showwarning("Execute", "Unsupported file type.")
        except Exception as e:
            messagebox.showerror("Execution Error", str(e))

    def close_current_tab(self):
        if not self.current_editor:
            return
        editor = self.current_editor
        if editor.is_modified():
            ans = messagebox.askyesnocancel("Save", "Save changes?")
            if ans is None:
                return
            if ans:
                editor.save()
        key_to_remove = None
        for key, ed in self.tabs.items():
            if ed == editor:
                key_to_remove = key
                break
        if key_to_remove:
            del self.tabs[key_to_remove]
        self.notebook.forget(editor)
        self.current_editor = None
        self._save_session()
        self.update_discord_presence()

    def undo(self):
        if self.current_editor:
            self.current_editor.text.event_generate("<<Undo>>")
    def redo(self):
        if self.current_editor:
            self.current_editor.text.event_generate("<<Redo>>")
    def cut(self):
        if self.current_editor:
            self.current_editor.cut()
    def copy(self):
        if self.current_editor:
            self.current_editor.copy()
    def paste(self):
        if self.current_editor:
            self.current_editor.paste()

    def show_find_dialog_current(self):
        if self.current_editor:
            FindDialog(self.root, self.current_editor)

    def show_replace_dialog(self):
        messagebox.showinfo("Replace", "Replace dialog not yet implemented.")

    def toggle_word_wrap(self):
        if self.current_editor:
            self.current_editor.toggle_word_wrap()

    def toggle_line_numbers(self):
        if self.current_editor:
            self.current_editor.toggle_line_numbers()

    def create_module(self):
        name = simpledialog.askstring("New Module", "Module name:")
        if name and re.match(r'^\w+$', name):
            target = BASE_MODULES_DIR / name
            if target.exists():
                messagebox.showerror("Error", "Module already exists.")
                return
            target.mkdir()
            pyw_file = target / f"{name}.pyw"
            pyw_file.write_text(f"if __name__ == '__main__':\n    print('Module {name} loaded')")
            self.file_browser.refresh()
            self.open_file(pyw_file)

    def _save_session(self):
        tabs_list = [k for k in self.tabs.keys() if not k.startswith("untitled_")]
        with open(SESSION_FILE, "w") as f:
            json.dump({"tabs": tabs_list}, f)

    def load_session(self):
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                for p in data.get("tabs", []):
                    if Path(p).exists():
                        self.open_file(Path(p))
            except Exception:
                pass
    def __del__(self):
        self._rpc_running = False
        if self._rpc:
            try:
                self._rpc.close()
            except:
                pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ModuleEditor(root)
    root.mainloop()