import sys
import os
import re
import json
import shutil
import zipfile
import subprocess
import mimetypes
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Optional, List, Dict, Any, Union

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeView, QTableView, QListView, QTabWidget, QPlainTextEdit, QTextEdit,
    QLineEdit, QPushButton, QToolButton, QMenu, QMenuBar, QInputDialog,
    QMessageBox, QFileDialog, QFileSystemModel, QHeaderView, QFrame,
    QStyle, QAbstractItemView, QStatusBar, QLabel, QProgressBar, QToolBar,
    QCompleter, QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox,
    QComboBox, QGroupBox, QListWidget, QListWidgetItem, QStackedWidget,
    QScrollArea, QButtonGroup, QRadioButton, QStyledItemDelegate,
    QProgressDialog, QFontDialog, QColorDialog, QTextBrowser, QDockWidget,
    QMdiArea, QMdiSubWindow, QAbstractScrollArea, QSizePolicy, QFileIconProvider,
    QStyleOptionViewItem
)
from PySide6.QtGui import (
    QAction, QActionGroup, QColor, QTextCharFormat, QSyntaxHighlighter,
    QFont, QFontMetrics, QIcon, QPalette, QBrush, QPixmap, QImage,
    QPainter, QPen, QTextDocument, QTextBlockFormat, QTextCursor,
    QKeySequence, QStandardItem, QStandardItemModel,
    QDragEnterEvent, QDropEvent, QDragMoveEvent, QMouseEvent, QResizeEvent,
    QCloseEvent, QContextMenuEvent, QFocusEvent, QWheelEvent, QPaintEvent,
    QFontDatabase, QTextOption, QTextLayout, QLinearGradient,
    QDesktopServices, QShortcut, QTextFormat 
)
from PySide6.QtCore import (
    Qt, QSize, QDir, QModelIndex, QItemSelectionModel, QFileInfo,
    QProcess, QSettings, QTimer, QThread, Signal, Slot, QUrl, QMimeData,
    QPoint, QRect, QEvent, QCoreApplication, QStandardPaths, QByteArray,
    QFile, QIODevice, QTextStream, QDateTime, QRegularExpression, QLocale,
    QAbstractTableModel, QSortFilterProxyModel, QItemSelection, QEasingCurve,
    QPropertyAnimation, QParallelAnimationGroup, QSequentialAnimationGroup,
    QPauseAnimation, QRectF, QMargins, QVariantAnimation, QAbstractAnimation,
    QStringListModel
)

# Optional imports for Windows features
try:
    import winshell
    HAS_WINSHELL = True
except ImportError:
    HAS_WINSHELL = False

try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

# =============================================================================
# CONSTANTS
# =============================================================================
DK_BG = "#191919"
DK_SIDEBAR = "#202020"
DK_WIDGET = "#2B2B2B"
DK_HOVER = "#323232"
DK_TEXT = "#E0E0E0"
DK_TEXT_SECONDARY = "#A0A0A0"
DK_BORDER = "#3F3F3F"
DK_SELECTION = "#264F78"
ACCENT = "#0078D4"
ACCENT_LIGHT = "#2B88D8"
ACCENT_DARK = "#005A9E"
ERROR_COLOR = "#F48771"
WARNING_COLOR = "#CCA700"
SUCCESS_COLOR = "#89D185"

EDITOR_BG = "#1E1E1E"
EDITOR_TEXT = "#D4D4D4"
EDITOR_GUTTER_BG = "#252526"
EDITOR_GUTTER_FG = "#858585"
EDITOR_SELECTION = "#264F78"
EDITOR_LINE_HIGHLIGHT = "#2A2A2A"
EDITOR_FOLD_MARKER = "#C5C5C5"

FILE_ICONS = {
    ".py": "🐍", ".txt": "📄", ".json": "📦", ".md": "📝",
    ".html": "🌐", ".htm": "🌐", ".css": "🎨", ".js": "📜",
    ".xml": "📋", ".yml": "⚙️", ".yaml": "⚙️", ".toml": "⚙️",
    ".ini": "⚙️", ".cfg": "⚙️", ".conf": "⚙️", ".bat": "⚡",
    ".sh": "🐚", ".ps1": "💻", ".c": "©️", ".cpp": "©️",
    ".h": "©️", ".hpp": "©️", ".java": "☕", ".kt": "☕",
    ".rs": "🦀", ".go": "🐹", ".php": "🐘", ".rb": "💎",
    ".zip": "📦", ".rar": "📦", ".7z": "📦", ".tar": "📦",
    ".gz": "📦", ".bz2": "📦", ".xz": "📦",
    ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️", ".gif": "🖼️",
    ".bmp": "🖼️", ".svg": "🖼️", ".webp": "🖼️",
    ".mp3": "🎵", ".wav": "🎵", ".flac": "🎵", ".mp4": "🎬",
    ".avi": "🎬", ".mkv": "🎬", ".mov": "🎬",
    ".exe": "⚙️", ".msi": "📦", ".dll": "🔧",
}

LANGUAGE_PATTERNS = {
    "python": {
        "extensions": [".py", ".pyw", ".pyi"],
        "keywords": ["False", "None", "True", "and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try", "while", "with", "yield"],
        "builtins": ["abs", "all", "any", "bin", "bool", "bytearray", "bytes", "callable", "chr", "classmethod", "compile", "complex", "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter", "float", "format", "frozenset", "getattr", "globals", "hasattr", "hash", "help", "hex", "id", "input", "int", "isinstance", "issubclass", "iter", "len", "list", "locals", "map", "max", "memoryview", "min", "next", "object", "oct", "open", "ord", "pow", "print", "property", "range", "repr", "reversed", "round", "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip"],
    },
    "markdown": {"extensions": [".md", ".markdown"]},
    "json": {"extensions": [".json", ".jsonc"]},
    "html": {"extensions": [".html", ".htm", ".xhtml"], "tags": ["a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo", "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data", "datalist", "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hr", "html", "i", "iframe", "img", "input", "ins", "kbd", "label", "legend", "li", "link", "main", "map", "mark", "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option", "output", "p", "param", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "section", "select", "small", "source", "span", "strong", "style", "sub", "summary", "sup", "svg", "table", "tbody", "td", "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "u", "ul", "var", "video", "wbr"]},
    "css": {"extensions": [".css", ".scss", ".sass", ".less"], "properties": ["align", "all", "animation", "backface", "background", "border", "bottom", "box", "break", "caption", "caret", "clear", "clip", "color", "column", "content", "counter", "cursor", "direction", "display", "empty", "filter", "flex", "float", "font", "gap", "grid", "height", "hyphens", "image", "inline", "inset", "isolation", "justify", "left", "letter", "line", "list", "margin", "mask", "max", "min", "mix", "object", "opacity", "order", "orphans", "outline", "overflow", "padding", "page", "perspective", "pointer", "position", "quotes", "resize", "right", "row", "scroll", "tab", "table", "text", "top", "transform", "transition", "unicode", "user", "vertical", "visibility", "white", "widows", "width", "word", "writing", "z"]},
    "javascript": {"extensions": [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"], "keywords": ["break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete", "do", "else", "export", "extends", "finally", "for", "function", "if", "import", "in", "instanceof", "new", "return", "super", "switch", "this", "throw", "try", "typeof", "var", "void", "while", "with", "yield", "let", "static", "await", "async", "of"]},
    "xml": {"extensions": [".xml", ".xsl", ".xslt", ".xsd", ".svg"]},
    "yaml": {"extensions": [".yml", ".yaml"]},
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================
def get_file_icon(path: Path) -> str:
    if path.is_dir():
        return "📁"
    ext = path.suffix.lower()
    return FILE_ICONS.get(ext, "📄")

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_timestamp(ts: float) -> str:
    if ts == 0:
        return ""
    dt = datetime.fromtimestamp(ts)
    now = datetime.now()
    if dt.date() == now.date():
        return dt.strftime("%I:%M %p")
    elif dt.year == now.year:
        return dt.strftime("%b %d")
    else:
        return dt.strftime("%m/%d/%Y")

def detect_language(file_path: Union[str, Path]) -> str:
    ext = Path(file_path).suffix.lower()
    for lang, info in LANGUAGE_PATTERNS.items():
        if ext in info.get("extensions", []):
            return lang
    return "text"

def is_text_file(file_path: Union[str, Path]) -> bool:
    text_exts = {".txt", ".py", ".js", ".html", ".css", ".json", ".xml", ".md", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".sh", ".bat", ".ps1", ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb", ".php", ".sql", ".log", ".csv"}
    return Path(file_path).suffix.lower() in text_exts

def is_image_file(file_path: Union[str, Path]) -> bool:
    return Path(file_path).suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"}

def is_archive_file(file_path: Union[str, Path]) -> bool:
    return Path(file_path).suffix.lower() in {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}

def safe_path(path: str) -> Path:
    return Path(path).resolve()

# =============================================================================
# SETTINGS MANAGER
# =============================================================================
class SettingsManager:
    def __init__(self):
        self.settings = QSettings("MelRoms", "Explorer")
        self._associations_file = Path.home() / ".melroms_associations.json"
        self._associations = self.load_associations()
        self._recent_files: List[str] = []
        self._bookmarks: List[str] = []
        self._quick_access: List[str] = []
        self.load_lists()
    
    def load_associations(self) -> Dict[str, str]:
        if self._associations_file.exists():
            try:
                with open(self._associations_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_associations(self):
        with open(self._associations_file, 'w') as f:
            json.dump(self._associations, f, indent=2)
    
    def get_association(self, ext: str) -> str:
        return self._associations.get(ext.lower(), "system")
    
    def set_association(self, ext: str, value: str):
        self._associations[ext.lower()] = value
        self.save_associations()
    
    def load_lists(self):
        self._recent_files = self.settings.value("recentFiles", []) or []
        self._bookmarks = self.settings.value("bookmarks", []) or []
        self._quick_access = self.settings.value("quickAccess", []) or []
    
    def save_lists(self):
        self.settings.setValue("recentFiles", self._recent_files)
        self.settings.setValue("bookmarks", self._bookmarks)
        self.settings.setValue("quickAccess", self._quick_access)
    
    def add_recent_file(self, path: str):
        if path in self._recent_files:
            self._recent_files.remove(path)
        self._recent_files.insert(0, path)
        self._recent_files = self._recent_files[:20]
        self.save_lists()
    
    def add_bookmark(self, path: str):
        if path not in self._bookmarks:
            self._bookmarks.append(path)
            self.save_lists()
    
    def remove_bookmark(self, path: str):
        if path in self._bookmarks:
            self._bookmarks.remove(path)
            self.save_lists()
    
    def add_quick_access(self, path: str):
        if path not in self._quick_access:
            self._quick_access.append(path)
            self.save_lists()
    
    def remove_quick_access(self, path: str):
        if path in self._quick_access:
            self._quick_access.remove(path)
            self.save_lists()
    
    @property
    def recent_files(self) -> List[str]:
        return self._recent_files.copy()
    
    @property
    def bookmarks(self) -> List[str]:
        return self._bookmarks.copy()
    
    @property
    def quick_access(self) -> List[str]:
        return self._quick_access.copy()
    
    def get_editor_font(self) -> QFont:
        family = self.settings.value("editor/fontFamily", "Consolas")
        size = int(self.settings.value("editor/fontSize", 10))
        return QFont(family, size)
    
    def set_editor_font(self, font: QFont):
        self.settings.setValue("editor/fontFamily", font.family())
        self.settings.setValue("editor/fontSize", font.pointSize())
    
    def get_tab_size(self) -> int:
        return int(self.settings.value("editor/tabSize", 4))
    
    def set_tab_size(self, size: int):
        self.settings.setValue("editor/tabSize", size)
    
    def get_word_wrap(self) -> bool:
        return bool(self.settings.value("editor/wordWrap", False))
    
    def set_word_wrap(self, wrap: bool):
        self.settings.setValue("editor/wordWrap", wrap)

# =============================================================================
# ADVANCED SYNTAX HIGHLIGHTER
# =============================================================================
class AdvancedSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument, language: str = "text"):
        super().__init__(document)
        self.language = language
        self.rules = []
        self.setup_rules()
    
    def setup_rules(self):
        self.rules.clear()
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#C586C0"))
        self.keyword_format.setFontWeight(QFont.Bold)
        self.builtin_format = QTextCharFormat()
        self.builtin_format.setForeground(QColor("#4EC9B0"))
        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#CE9178"))
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#6A9955"))
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#B5CEA8"))
        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#DCDCAA"))
        self.class_format = QTextCharFormat()
        self.class_format.setForeground(QColor("#4EC9B0"))
        self.tag_format = QTextCharFormat()
        self.tag_format.setForeground(QColor("#569CD6"))
        self.attribute_format = QTextCharFormat()
        self.attribute_format.setForeground(QColor("#9CDCFE"))
        
        if self.language == "python":
            self.setup_python_rules()
        elif self.language == "markdown":
            self.setup_markdown_rules()
        elif self.language == "json":
            self.setup_json_rules()
        elif self.language in ("html", "xml"):
            self.setup_html_xml_rules()
        elif self.language == "css":
            self.setup_css_rules()
        elif self.language == "javascript":
            self.setup_javascript_rules()
        elif self.language == "yaml":
            self.setup_yaml_rules()
    
    def setup_python_rules(self):
        keywords = LANGUAGE_PATTERNS["python"]["keywords"]
        builtins = LANGUAGE_PATTERNS["python"]["builtins"]
        for word in keywords:
            pattern = rf"\b{word}\b"
            self.rules.append((QRegularExpression(pattern), self.keyword_format))
        for word in builtins:
            pattern = rf"\b{word}\b"
            self.rules.append((QRegularExpression(pattern), self.builtin_format))
        self.rules.append((QRegularExpression(r"\bdef\s+(\w+)"), self.function_format))
        self.rules.append((QRegularExpression(r"\bclass\s+(\w+)"), self.class_format))
        self.rules.append((QRegularExpression(r"@\w+"), self.function_format))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        self.rules.append((QRegularExpression(r'"""[^"\\]*(\\.[^"\\]*)*"""'), self.string_format))
        self.rules.append((QRegularExpression(r"'''[^'\\]*(\\.[^'\\]*)*'''"), self.string_format))
        self.rules.append((QRegularExpression(r"#[^\n]*"), self.comment_format))
        self.rules.append((QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), self.number_format))
    
    def setup_markdown_rules(self):
        header_fmt = QTextCharFormat()
        header_fmt.setForeground(QColor("#569CD6"))
        header_fmt.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"^#{1,6}\s.*$"), header_fmt))
        bold_fmt = QTextCharFormat()
        bold_fmt.setFontWeight(QFont.Bold)
        self.rules.append((QRegularExpression(r"\*\*[^*]+\*\*"), bold_fmt))
        italic_fmt = QTextCharFormat()
        italic_fmt.setFontItalic(True)
        self.rules.append((QRegularExpression(r"\*[^*]+\*"), italic_fmt))
        code_fmt = QTextCharFormat()
        code_fmt.setBackground(QColor("#2D2D2D"))
        self.rules.append((QRegularExpression(r"`[^`]+`"), code_fmt))
        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor("#4EC9B0"))
        self.rules.append((QRegularExpression(r"\[.*?\]\(.*?\)"), link_fmt))
    
    def setup_json_rules(self):
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#9CDCFE"))
        self.rules.append((QRegularExpression(r'"[^"]*"\s*:'), key_fmt))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), self.number_format))
        bool_fmt = QTextCharFormat()
        bool_fmt.setForeground(QColor("#569CD6"))
        self.rules.append((QRegularExpression(r"\b(true|false|null)\b"), bool_fmt))
    
    def setup_html_xml_rules(self):
        self.rules.append((QRegularExpression(r"</?[a-zA-Z0-9_-]+"), self.tag_format))
        self.rules.append((QRegularExpression(r'\b[a-zA-Z-]+="[^"]*"'), self.attribute_format))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"<!--.*?-->"), self.comment_format))
    
    def setup_css_rules(self):
        selector_fmt = QTextCharFormat()
        selector_fmt.setForeground(QColor("#D7BA7D"))
        self.rules.append((QRegularExpression(r"^[.#]?[a-zA-Z0-9_-]+\s*\{"), selector_fmt))
        for prop in LANGUAGE_PATTERNS["css"]["properties"]:
            self.rules.append((QRegularExpression(rf"\b{prop}\b"), self.keyword_format))
        self.rules.append((QRegularExpression(r":\s*[^;]+"), self.string_format))
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?(px|em|rem|%|vh|vw)?\b"), self.number_format))
    
    def setup_javascript_rules(self):
        keywords = LANGUAGE_PATTERNS["javascript"]["keywords"]
        for word in keywords:
            pattern = rf"\b{word}\b"
            self.rules.append((QRegularExpression(pattern), self.keyword_format))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), self.string_format))
        self.rules.append((QRegularExpression(r"`[^`\\]*(\\.[^`\\]*)*`"), self.string_format))
        self.rules.append((QRegularExpression(r"//[^\n]*"), self.comment_format))
        self.rules.append((QRegularExpression(r"/\*.*?\*/"), self.comment_format))
        self.rules.append((QRegularExpression(r"\bfunction\s+(\w+)"), self.function_format))
        self.rules.append((QRegularExpression(r"\b\d+(\.\d+)?\b"), self.number_format))
    
    def setup_yaml_rules(self):
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#9CDCFE"))
        self.rules.append((QRegularExpression(r"^[a-zA-Z0-9_-]+:"), key_fmt))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), self.string_format))
        self.rules.append((QRegularExpression(r"#[^\n]*"), self.comment_format))
    
    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)

# =============================================================================
# CODE EDITOR
# =============================================================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor
    
    def sizeHint(self) -> QSize:
        return QSize(self.editor.line_number_area_width(), 0)
    
    def paintEvent(self, event: QPaintEvent):
        self.editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.is_modified = False
        self.language = "text"
        self.highlighter: Optional[AdvancedSyntaxHighlighter] = None
        self.line_number_area = LineNumberArea(self)
        self.setFrameStyle(QFrame.NoFrame)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFont(QFont("Consolas", 10))
        self.setTabStopDistance(QFontMetrics(self.font()).horizontalAdvance(' ') * 4)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self.on_text_changed)
        if file_path:
            self.language = detect_language(file_path)
        self.highlighter = AdvancedSyntaxHighlighter(self.document(), self.language)
        self.apply_theme()
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.bracket_positions = []
        self.completer = None
        self.setup_completer()
    
    def apply_theme(self):
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDITOR_BG};
                color: {EDITOR_TEXT};
                selection-background-color: {EDITOR_SELECTION};
                border: none;
            }}
        """)
    
    def setup_completer(self):
        if self.language == "python":
            words = LANGUAGE_PATTERNS["python"]["keywords"] + LANGUAGE_PATTERNS["python"]["builtins"]
            model = QStringListModel(words, self)
            self.completer = QCompleter(model, self)
            self.completer.setWidget(self)
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.activated.connect(self.insert_completion)
    
    def insert_completion(self, completion: str):
        cursor = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        cursor.movePosition(QTextCursor.Left)
        cursor.movePosition(QTextCursor.EndOfWord)
        cursor.insertText(completion[-extra:])
        self.setTextCursor(cursor)
    
    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab):
                event.ignore()
                return
        if event.key() == Qt.Key_Tab and not event.modifiers():
            self.auto_indent()
            return
        if event.text() in ('"', "'", '(', '[', '{'):
            self.insert_closing_bracket(event.text())
            return
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.auto_indent_newline()
            return
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Slash:
            self.toggle_comment()
            return
        super().keyPressEvent(event)
        if self.completer and event.text().isalnum():
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfWord, QTextCursor.KeepAnchor)
            prefix = cursor.selectedText()
            if len(prefix) >= 2:
                self.completer.setCompletionPrefix(prefix)
                rect = self.cursorRect()
                rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 
                              self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(rect)
    
    def insert_closing_bracket(self, open_char: str):
        pairs = {'"': '"', "'": "'", '(': ')', '[': ']', '{': '}'}
        close_char = pairs[open_char]
        cursor = self.textCursor()
        cursor.insertText(open_char + close_char)
        cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)
    
    def auto_indent(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            self.indent_selection(True)
        else:
            cursor.insertText("    ")
    
    def auto_indent_newline(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.insertBlock()
        cursor.movePosition(QTextCursor.PreviousBlock)
        text = cursor.block().text()
        indent = re.match(r'^\s*', text).group()
        cursor.movePosition(QTextCursor.NextBlock)
        cursor.insertText(indent)
        cursor.endEditBlock()
        self.setTextCursor(cursor)
    
    def toggle_comment(self):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.LineUnderCursor)
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        lines = cursor.selection().toPlainText().split('\n')
        commented = all(line.lstrip().startswith('#') if line.strip() else True for line in lines)
        cursor.beginEditBlock()
        for line in lines:
            if not line.strip():
                cursor.movePosition(QTextCursor.Down)
                continue
            cursor.movePosition(QTextCursor.StartOfLine)
            if commented:
                idx = line.find('#')
                if idx != -1:
                    cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, idx)
                    cursor.deleteChar()
            else:
                cursor.insertText('# ')
            cursor.movePosition(QTextCursor.Down)
        cursor.endEditBlock()
    
    def indent_selection(self, indent: bool = True):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            return
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        lines = cursor.selection().toPlainText().split('\n')
        cursor.beginEditBlock()
        for _ in lines:
            cursor.movePosition(QTextCursor.StartOfLine)
            if indent:
                cursor.insertText("    ")
            else:
                text = cursor.block().text()
                if text.startswith("    "):
                    cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 4)
                    cursor.removeSelectedText()
                elif text.startswith("\t"):
                    cursor.deleteChar()
            cursor.movePosition(QTextCursor.Down)
        cursor.endEditBlock()
    
    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space
    
    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
    
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    
    def line_number_area_paint_event(self, event: QPaintEvent):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(EDITOR_GUTTER_BG))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(EDITOR_GUTTER_FG))
                painter.drawText(0, int(top), self.line_number_area.width() - 2, 
                                 self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1
    
    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(EDITOR_LINE_HIGHLIGHT))
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.highlight_matching_brackets(extra_selections)
        self.setExtraSelections(extra_selections)
    
    def highlight_matching_brackets(self, extra_selections: list):
        cursor = self.textCursor()
        text = self.toPlainText()
        pos = cursor.position()
        if pos > 0 and pos <= len(text):
            char_before = text[pos-1] if pos > 0 else ''
            char_after = text[pos] if pos < len(text) else ''
            bracket = None
            if char_before in '()[]{}':
                bracket = char_before
                pos = pos - 1
            elif char_after in '()[]{}':
                bracket = char_after
            else:
                return
            match = self.find_matching_bracket(text, pos, bracket)
            if match is not None:
                sel = QTextEdit.ExtraSelection()
                sel.format.setBackground(QColor(EDITOR_SELECTION))
                sel.format.setForeground(QColor(Qt.white))
                sel.cursor = QTextCursor(self.document())
                sel.cursor.setPosition(pos)
                sel.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                extra_selections.append(sel)
                sel2 = QTextEdit.ExtraSelection()
                sel2.format.setBackground(QColor(EDITOR_SELECTION))
                sel2.format.setForeground(QColor(Qt.white))
                sel2.cursor = QTextCursor(self.document())
                sel2.cursor.setPosition(match)
                sel2.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
                extra_selections.append(sel2)
    
    def find_matching_bracket(self, text: str, pos: int, bracket: str) -> Optional[int]:
        pairs = {'(': ')', '[': ']', '{': '}'}
        reverse_pairs = {')': '(', ']': '[', '}': '{'}
        if bracket in pairs:
            open_char = bracket
            close_char = pairs[bracket]
            direction = 1
            start = pos + 1
            end = len(text)
        else:
            open_char = reverse_pairs[bracket]
            close_char = bracket
            direction = -1
            start = pos - 1
            end = -1
        count = 1
        i = start
        while 0 <= i < len(text) and count > 0:
            ch = text[i]
            if ch == open_char:
                count += 1
            elif ch == close_char:
                count -= 1
            i += direction
        return i - direction if count == 0 else None
    
    def on_text_changed(self):
        self.is_modified = True
    
    def set_modified(self, modified: bool):
        self.is_modified = modified
    
    def go_to_line(self):
        line, ok = QInputDialog.getInt(self, "Go to Line", "Line number:", min=1, max=self.blockCount())
        if ok:
            cursor = QTextCursor(self.document().findBlockByLineNumber(line - 1))
            self.setTextCursor(cursor)
            self.centerCursor()
    
    def set_language(self, language: str):
        self.language = language
        if self.highlighter:
            self.highlighter.deleteLater()
        self.highlighter = AdvancedSyntaxHighlighter(self.document(), language)
        self.setup_completer()

# =============================================================================
# TERMINAL WIDGET
# =============================================================================
class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 9))
        self.output.setStyleSheet(f"background-color: {EDITOR_BG}; color: {EDITOR_TEXT}; border: none;")
        self.input_line = QLineEdit()
        self.input_line.setFont(QFont("Consolas", 9))
        self.input_line.setStyleSheet(f"background-color: {DK_WIDGET}; color: {DK_TEXT}; border: 1px solid {DK_BORDER}; padding: 4px;")
        self.input_line.returnPressed.connect(self.send_command)
        layout.addWidget(self.output)
        layout.addWidget(self.input_line)
        self.process.readyRead.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        self.start_shell()
    
    def start_shell(self):
        if sys.platform == "win32":
            self.process.start("cmd.exe")
        else:
            self.process.start("bash")
    
    def send_command(self):
        cmd = self.input_line.text()
        if cmd:
            self.output.appendPlainText(f"> {cmd}")
            self.process.write((cmd + "\n").encode())
            self.input_line.clear()
    
    def read_output(self):
        data = self.process.readAll().data().decode('utf-8', errors='replace')
        self.output.insertPlainText(data)
        self.output.ensureCursorVisible()
    
    def process_finished(self):
        self.output.appendPlainText("\n[Process finished]")
    
    def run_command(self, command: str):
        self.output.appendPlainText(f"> {command}")
        self.process.write((command + "\n").encode())
    
    def closeEvent(self, event):
        self.process.terminate()
        self.process.waitForFinished(1000)
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()
        super().closeEvent(event)

# =============================================================================
# FILE SYSTEM MODEL
# =============================================================================
class FileSystemModel(QFileSystemModel):
    def __init__(self):
        super().__init__()
        self.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden | QDir.System)
        self.setNameFilterDisables(False)
        self.thumbnail_cache = {}
        self.icon_provider = QFileIconProvider()
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if role == Qt.DecorationRole and index.column() == 0:
            file_info = self.fileInfo(index)
            if file_info.isDir():
                return QApplication.style().standardIcon(QStyle.SP_DirIcon)
            elif file_info.isRoot():
                return QApplication.style().standardIcon(QStyle.SP_DriveHDIcon)
            else:
                return None
        
        if role == Qt.DisplayRole and index.column() == 0:
            file_info = self.fileInfo(index)
            if file_info.isRoot():
                path = file_info.filePath()
                try:
                    import win32api
                    volume_name = win32api.GetVolumeInformation(path)[0]
                    return f"{path} ({volume_name})" if volume_name else path
                except:
                    return path
            return super().data(index, role)
        
        return super().data(index, role)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 4
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ["Name", "Size", "Type", "Date Modified"][section]
        return super().headerData(section, orientation, role)

# =============================================================================
# CUSTOM DELEGATE
# =============================================================================
class FileListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if index.column() == 0:
            model = index.model()
            file_info = model.fileInfo(index)
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            elif option.state & QStyle.State_MouseOver:
                painter.fillRect(option.rect, QColor(DK_HOVER))
            else:
                painter.fillRect(option.rect, option.palette.base())
            icon_text = get_file_icon(Path(file_info.filePath()))
            painter.setFont(QFont("Segoe UI", 10))
            painter.setPen(QColor(DK_TEXT) if not (option.state & QStyle.State_Selected) else QColor(Qt.white))
            icon_rect = QRect(option.rect.left() + 4, option.rect.top() + 2, 20, option.rect.height() - 4)
            painter.drawText(icon_rect, Qt.AlignCenter, icon_text)
            text_rect = QRect(option.rect.left() + 28, option.rect.top(), option.rect.width() - 32, option.rect.height())
            name = file_info.fileName()
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, name)
        else:
            super().paint(painter, option, index)
    
    def displayText(self, value: Any, locale: QLocale) -> str:
        if isinstance(value, (int, float)) and value > 0:
            if value > 10000000000:
                dt = QDateTime.fromMSecsSinceEpoch(value // 1000000)
                return dt.toString("yyyy-MM-dd hh:mm")
            else:
                return format_size(value)
        return super().displayText(value, locale)

# =============================================================================
# FILE VIEW WIDGET
# =============================================================================
class FileViewWidget(QWidget):
    navigation_requested = Signal(str)
    open_file_requested = Signal(str)
    context_menu_requested = Signal(object, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = FileSystemModel()
        self.current_path = ""
        self.stack = QStackedWidget()
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setRootIndex(self.model.index(""))
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setShowGrid(False)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionsClickable(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setItemDelegate(FileListDelegate())
        self.table_view.doubleClicked.connect(self.item_double_clicked)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.context_menu)
        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(""))
        self.list_view.setViewMode(QListView.ListMode)
        self.list_view.setResizeMode(QListView.Adjust)
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_view.doubleClicked.connect(self.item_double_clicked)
        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.context_menu)
        self.icon_view = QListView()
        self.icon_view.setModel(self.model)
        self.icon_view.setRootIndex(self.model.index(""))
        self.icon_view.setViewMode(QListView.IconMode)
        self.icon_view.setResizeMode(QListView.Adjust)
        self.icon_view.setIconSize(QSize(64, 64))
        self.icon_view.setGridSize(QSize(100, 100))
        self.icon_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.icon_view.doubleClicked.connect(self.item_double_clicked)
        self.icon_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.icon_view.customContextMenuRequested.connect(self.context_menu)
        self.stack.addWidget(self.table_view)
        self.stack.addWidget(self.list_view)
        self.stack.addWidget(self.icon_view)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)
        self.current_view = self.table_view
        self.view_mode = "details"
    
    def set_view_mode(self, mode: str):
        self.view_mode = mode
        if mode == "details":
            self.stack.setCurrentWidget(self.table_view)
            self.current_view = self.table_view
        elif mode == "list":
            self.stack.setCurrentWidget(self.list_view)
            self.current_view = self.list_view
        elif mode == "icons":
            self.stack.setCurrentWidget(self.icon_view)
            self.current_view = self.icon_view
        else:
            self.stack.setCurrentWidget(self.table_view)
            self.current_view = self.table_view
    
    def set_root_path(self, path: str):
        self.current_path = path
        self.model.setRootPath(path)
        index = self.model.index(path) if path else self.model.index("")
        self.table_view.setRootIndex(index)
        self.list_view.setRootIndex(index)
        self.icon_view.setRootIndex(index)
    
    def current_index(self) -> QModelIndex:
        if isinstance(self.current_view, QTableView):
            return self.current_view.currentIndex()
        elif isinstance(self.current_view, QListView):
            return self.current_view.currentIndex()
        return QModelIndex()
    
    def selected_indexes(self) -> List[QModelIndex]:
        if isinstance(self.current_view, QAbstractItemView):
            return self.current_view.selectedIndexes()
        return []
    
    def selected_paths(self) -> List[str]:
        paths = []
        for index in self.selected_indexes():
            if index.column() == 0:
                paths.append(self.model.filePath(index))
        return paths
    
    def item_double_clicked(self, index: QModelIndex):
        idx = index.siblingAtColumn(0)
        path = self.model.filePath(idx)
        if self.model.isDir(idx):
            self.set_root_path(path)
            self.navigation_requested.emit(path)
        else:
            self.open_file_requested.emit(path)
    
    def context_menu(self, pos):
        self.context_menu_requested.emit(pos, self)
    
    def refresh(self):
        self.model.setRootPath(self.current_path)

# =============================================================================
# SIDEBAR WIDGET
# =============================================================================
class SidebarWidget(QWidget):
    navigation_requested = Signal(str)
    context_menu_requested = Signal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = parent.settings if hasattr(parent, 'settings') else None
        self.tree_model = QFileSystemModel()
        self.tree_model.setRootPath("")
        self.tree_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot | QDir.Drives)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setDocumentMode(True)
        self.quick_access_widget = QWidget()
        qa_layout = QVBoxLayout(self.quick_access_widget)
        qa_layout.setContentsMargins(4, 4, 4, 4)
        self.qa_list = QListWidget()
        self.qa_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.qa_list.itemActivated.connect(self.qa_item_activated)
        self.qa_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.qa_list.customContextMenuRequested.connect(self.qa_context_menu)
        qa_layout.addWidget(self.qa_list)
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.tree_model)
        self.tree_view.setHeaderHidden(True)
        for i in range(1, self.tree_model.columnCount()):
            self.tree_view.setColumnHidden(i, True)
        self.tree_view.setRootIndex(self.tree_model.index(""))
        self.tree_view.clicked.connect(self.tree_clicked)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.tree_context_menu)
        self.tab_widget.addTab(self.quick_access_widget, "Quick Access")
        self.tab_widget.addTab(self.tree_view, "Tree")
        layout.addWidget(self.tab_widget)
        self.populate_quick_access()
    
    def populate_quick_access(self):
        self.qa_list.clear()
        for name, path in [
            ("Desktop", QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)),
            ("Documents", QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)),
            ("Downloads", QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)),
            ("Music", QStandardPaths.writableLocation(QStandardPaths.MusicLocation)),
            ("Pictures", QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)),
            ("Videos", QStandardPaths.writableLocation(QStandardPaths.MoviesLocation)),
        ]:
            if path and os.path.exists(path):
                item = QListWidgetItem(f"📁 {name}")
                item.setData(Qt.UserRole, path)
                self.qa_list.addItem(item)
        if self.settings:
            for path in self.settings.quick_access:
                if os.path.exists(path):
                    item = QListWidgetItem(f"📌 {os.path.basename(path)}")
                    item.setData(Qt.UserRole, path)
                    self.qa_list.addItem(item)
    
    def qa_item_activated(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            self.navigation_requested.emit(path)
    
    def qa_context_menu(self, pos):
        item = self.qa_list.itemAt(pos)
        if not item:
            return
        path = item.data(Qt.UserRole)
        menu = QMenu(self)
        remove_action = menu.addAction("Remove from Quick Access")
        action = menu.exec(self.qa_list.mapToGlobal(pos))
        if action == remove_action:
            if self.settings:
                self.settings.remove_quick_access(path)
            self.populate_quick_access()
    
    def tree_clicked(self, index: QModelIndex):
        path = self.tree_model.filePath(index)
        if self.tree_model.isDir(index):
            self.navigation_requested.emit(path)
        else:
            # It's a drive root
            self.navigation_requested.emit(path)
    
    def tree_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            return
        path = self.tree_model.filePath(index)
        self.context_menu_requested.emit(path, self.tree_view.mapToGlobal(pos))

# =============================================================================
# ADDRESS BAR
# =============================================================================
class AddressBar(QWidget):
    path_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(2)
        layout.addLayout(self.buttons_layout)
        layout.addStretch()
        self.set_path("")
    
    def set_path(self, path: str):
        while self.buttons_layout.count():
            item = self.buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not path or path == "":
            btn = QToolButton()
            btn.setText("This PC")
            btn.setToolTip("This PC")
            btn.clicked.connect(lambda: self.path_changed.emit(""))
            self.buttons_layout.addWidget(btn)
            return
        p = Path(path)
        parts = []
        if p.drive:
            parts.append(p.drive.rstrip('\\'))
        parts.extend([part for part in p.parts if part not in ('/', '\\') and part != p.drive.rstrip('\\')])
        pc_btn = QToolButton()
        pc_btn.setText("This PC")
        pc_btn.setToolTip("This PC")
        pc_btn.clicked.connect(lambda: self.path_changed.emit(""))
        self.buttons_layout.addWidget(pc_btn)
        sep = QLabel(">")
        sep.setStyleSheet("color: #666; padding: 0 2px;")
        self.buttons_layout.addWidget(sep)
        accum = ""
        for i, part in enumerate(parts):
            if i == 0 and p.drive:
                accum = part + "\\"
            else:
                if accum and not accum.endswith(('\\', '/')):
                    accum = os.path.join(accum, part)
                else:
                    accum += part
            btn = QToolButton()
            btn.setText(part if part else "/")
            btn.setToolTip(accum)
            btn.clicked.connect(lambda checked, p=accum: self.path_changed.emit(p))
            self.buttons_layout.addWidget(btn)
            if i < len(parts) - 1:
                sep = QLabel(">")
                sep.setStyleSheet("color: #666; padding: 0 2px;")
                self.buttons_layout.addWidget(sep)

# =============================================================================
# PROPERTIES DIALOG
# =============================================================================
class PropertiesDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.path = Path(path)
        self.setWindowTitle(f"Properties - {self.path.name}")
        self.setMinimumWidth(400)
        self.setup_ui()
        self.load_info()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        general_widget = QWidget()
        general_layout = QFormLayout(general_widget)
        self.name_label = QLabel()
        general_layout.addRow("Name:", self.name_label)
        self.type_label = QLabel()
        general_layout.addRow("Type:", self.type_label)
        self.location_label = QLabel()
        general_layout.addRow("Location:", self.location_label)
        self.size_label = QLabel()
        general_layout.addRow("Size:", self.size_label)
        self.contains_label = QLabel()
        general_layout.addRow("Contains:", self.contains_label)
        self.created_label = QLabel()
        general_layout.addRow("Created:", self.created_label)
        self.modified_label = QLabel()
        general_layout.addRow("Modified:", self.modified_label)
        self.accessed_label = QLabel()
        general_layout.addRow("Accessed:", self.accessed_label)
        self.attributes_label = QLabel()
        general_layout.addRow("Attributes:", self.attributes_label)
        tabs.addTab(general_widget, "General")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_info(self):
        stat = self.path.stat()
        self.name_label.setText(self.path.name)
        if self.path.is_dir():
            self.type_label.setText("File folder")
            try:
                items = list(self.path.iterdir())
                self.contains_label.setText(f"{len(items)} items")
            except:
                self.contains_label.setText("Unknown")
        else:
            mime, _ = mimetypes.guess_type(str(self.path))
            self.type_label.setText(mime or "Unknown type")
            self.contains_label.setText("Not applicable")
        self.location_label.setText(str(self.path.parent))
        if self.path.is_dir():
            size = self.get_folder_size(self.path)
            self.size_label.setText(f"{format_size(size)} ({size:,} bytes)")
        else:
            size = stat.st_size
            self.size_label.setText(f"{format_size(size)} ({size:,} bytes)")
        self.created_label.setText(datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"))
        self.modified_label.setText(datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
        self.accessed_label.setText(datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"))
        attrs = []
        if self.path.is_dir():
            attrs.append("D")
        if not os.access(self.path, os.W_OK):
            attrs.append("R")
        if self.path.is_file() and self.path.suffix.lower() == ".exe":
            attrs.append("X")
        self.attributes_label.setText(" ".join(attrs) if attrs else "Normal")
    
    def get_folder_size(self, folder: Path) -> int:
        total = 0
        try:
            for item in folder.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except:
            pass
        return total

# =============================================================================
# FIND/REPLACE DIALOG
# =============================================================================
class FindReplaceDialog(QDialog):
    def __init__(self, editor: CodeEditor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setWindowTitle("Find and Replace")
        self.setMinimumWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText("Search text...")
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_edit = QLineEdit()
        self.replace_edit.setPlaceholderText("Replace with...")
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)
        options_layout = QHBoxLayout()
        self.case_check = QCheckBox("Case sensitive")
        self.regex_check = QCheckBox("Regular expression")
        self.whole_word_check = QCheckBox("Whole words only")
        options_layout.addWidget(self.case_check)
        options_layout.addWidget(self.regex_check)
        options_layout.addWidget(self.whole_word_check)
        layout.addLayout(options_layout)
        button_layout = QHBoxLayout()
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_next)
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace)
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(find_btn)
        button_layout.addWidget(replace_btn)
        button_layout.addWidget(replace_all_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
    
    def find_next(self):
        text = self.find_edit.text()
        if not text:
            return
        flags = QTextDocument.FindFlags()
        if self.case_check.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_check.isChecked():
            flags |= QTextDocument.FindWholeWords
        if self.regex_check.isChecked():
            cursor = self.editor.textCursor()
            regex = QRegularExpression(text)
            if not self.case_check.isChecked():
                regex.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            match = regex.match(self.editor.toPlainText(), cursor.position())
            if match.hasMatch():
                cursor.setPosition(match.capturedStart())
                cursor.setPosition(match.capturedEnd(), QTextCursor.KeepAnchor)
                self.editor.setTextCursor(cursor)
        else:
            found = self.editor.find(text, flags)
            if not found:
                cursor = self.editor.textCursor()
                cursor.movePosition(QTextCursor.Start)
                self.editor.setTextCursor(cursor)
                self.editor.find(text, flags)
    
    def replace(self):
        if self.editor.textCursor().hasSelection():
            self.editor.textCursor().insertText(self.replace_edit.text())
        self.find_next()
    
    def replace_all(self):
        text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        if not text:
            return
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.Start)
        self.editor.setTextCursor(cursor)
        flags = QTextDocument.FindFlags()
        if self.case_check.isChecked():
            flags |= QTextDocument.FindCaseSensitively
        if self.whole_word_check.isChecked():
            flags |= QTextDocument.FindWholeWords
        count = 0
        if self.regex_check.isChecked():
            content = self.editor.toPlainText()
            regex = QRegularExpression(text)
            if not self.case_check.isChecked():
                regex.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
            matches = []
            iterator = regex.globalMatch(content)
            while iterator.hasNext():
                match = iterator.next()
                matches.append((match.capturedStart(), match.capturedEnd()))
            for start, end in reversed(matches):
                cursor.setPosition(start)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                cursor.insertText(replace_text)
                count += 1
        else:
            while self.editor.find(text, flags):
                self.editor.textCursor().insertText(replace_text)
                count += 1
        cursor.endEditBlock()
        QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences.")

# =============================================================================
# SETTINGS DIALOG
# =============================================================================
class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        editor_widget = QWidget()
        editor_layout = QFormLayout(editor_widget)
        self.font_btn = QPushButton("Change Font...")
        self.font_btn.clicked.connect(self.change_font)
        editor_layout.addRow("Font:", self.font_btn)
        self.font_label = QLabel()
        editor_layout.addRow("", self.font_label)
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        editor_layout.addRow("Tab size:", self.tab_size_spin)
        self.word_wrap_check = QCheckBox("Enable word wrap")
        editor_layout.addRow("", self.word_wrap_check)
        tabs.addTab(editor_widget, "Editor")
        assoc_widget = QWidget()
        assoc_layout = QVBoxLayout(assoc_widget)
        self.assoc_list = QListWidget()
        assoc_layout.addWidget(QLabel("File Associations:"))
        assoc_layout.addWidget(self.assoc_list)
        add_btn = QPushButton("Add/Edit Association")
        add_btn.clicked.connect(self.edit_association)
        assoc_layout.addWidget(add_btn)
        tabs.addTab(assoc_widget, "Associations")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def change_font(self):
        font, ok = QFontDialog.getFont(self.settings.get_editor_font(), self)
        if ok:
            self.settings.set_editor_font(font)
            self.update_font_label()
    
    def update_font_label(self):
        font = self.settings.get_editor_font()
        self.font_label.setText(f"{font.family()} {font.pointSize()}pt")
    
    def load_settings(self):
        self.update_font_label()
        self.tab_size_spin.setValue(self.settings.get_tab_size())
        self.word_wrap_check.setChecked(self.settings.get_word_wrap())
        self.assoc_list.clear()
        for ext, assoc in self.settings._associations.items():
            self.assoc_list.addItem(f"{ext}: {assoc}")
    
    def edit_association(self):
        ext, ok = QInputDialog.getText(self, "Extension", "Enter file extension (e.g., .py):")
        if not ok or not ext:
            return
        items = ["system", "builtin", "custom..."]
        choice, ok = QInputDialog.getItem(self, "Association", "Choose how to open:", items, 0, False)
        if not ok:
            return
        if choice == "custom...":
            exe, _ = QFileDialog.getOpenFileName(self, "Select Application", "", "Executables (*.exe);;All Files (*.*)")
            if exe:
                self.settings.set_association(ext, exe)
        else:
            self.settings.set_association(ext, choice)
        self.load_settings()
    
    def save_settings(self):
        self.settings.set_tab_size(self.tab_size_spin.value())
        self.settings.set_word_wrap(self.word_wrap_check.isChecked())
        self.accept()

# =============================================================================
# MAIN WINDOW
# =============================================================================
class MelRomsExplorer(QMainWindow):
    open_file_requested = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.setWindowTitle("MelRoms Explorer")
        self.resize(1600, 1000)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DriveHDIcon))
        self.setAcceptDrops(True)
        self.history = []
        self.history_index = -1
        self.closed_tabs = deque(maxlen=10)
        self.setup_menu_bar()
        self.setup_toolbar()
        self.setup_ui()
        self.apply_theme()
        self.setup_shortcuts()
        self.setup_status_bar()
        self.restore_session()
        self.navigate_to("")
    
    def setup_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        new_file_action = QAction("New File", self)
        new_file_action.setShortcut(QKeySequence.New)
        new_file_action.triggered.connect(self.new_file)
        file_menu.addAction(new_file_action)
        new_folder_action = QAction("New Folder", self)
        new_folder_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        new_folder_action.triggered.connect(self.new_folder)
        file_menu.addAction(new_folder_action)
        file_menu.addSeparator()
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file_dialog)
        file_menu.addAction(open_action)
        self.recent_menu = file_menu.addMenu("Recent Files")
        self.update_recent_menu()
        file_menu.addSeparator()
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_current_file)
        file_menu.addAction(save_action)
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as_current_file)
        file_menu.addAction(save_as_action)
        save_all_action = QAction("Save All", self)
        save_all_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_all_action.triggered.connect(self.save_all_files)
        file_menu.addAction(save_all_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        edit_menu = menubar.addMenu("&Edit")
        cut_action = QAction("Cut", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        copy_action = QAction("Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        paste_action = QAction("Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        edit_menu.addSeparator()
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        edit_menu.addSeparator()
        find_action = QAction("Find...", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        replace_action = QAction("Replace...", self)
        replace_action.setShortcut(QKeySequence.Replace)
        replace_action.triggered.connect(self.show_replace_dialog)
        edit_menu.addAction(replace_action)
        goto_action = QAction("Go to Line...", self)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.go_to_line)
        edit_menu.addAction(goto_action)
        view_menu = menubar.addMenu("&View")
        self.view_mode_group = QActionGroup(self)
        details_action = QAction("Details", self)
        details_action.setCheckable(True)
        details_action.setChecked(True)
        details_action.triggered.connect(lambda: self.set_view_mode("details"))
        self.view_mode_group.addAction(details_action)
        view_menu.addAction(details_action)
        list_action = QAction("List", self)
        list_action.setCheckable(True)
        list_action.triggered.connect(lambda: self.set_view_mode("list"))
        self.view_mode_group.addAction(list_action)
        view_menu.addAction(list_action)
        icons_action = QAction("Icons", self)
        icons_action.setCheckable(True)
        icons_action.triggered.connect(lambda: self.set_view_mode("icons"))
        self.view_mode_group.addAction(icons_action)
        view_menu.addAction(icons_action)
        tiles_action = QAction("Tiles", self)
        tiles_action.setCheckable(True)
        tiles_action.triggered.connect(lambda: self.set_view_mode("tiles"))
        self.view_mode_group.addAction(tiles_action)
        view_menu.addAction(tiles_action)
        view_menu.addSeparator()
        refresh_action = QAction("Refresh", self)
        refresh_action.setShortcut(QKeySequence.Refresh)
        refresh_action.triggered.connect(self.refresh_view)
        view_menu.addAction(refresh_action)
        go_menu = menubar.addMenu("&Go")
        back_action = QAction("Back", self)
        back_action.setShortcut(QKeySequence.Back)
        back_action.triggered.connect(self.go_back)
        go_menu.addAction(back_action)
        forward_action = QAction("Forward", self)
        forward_action.setShortcut(QKeySequence.Forward)
        forward_action.triggered.connect(self.go_forward)
        go_menu.addAction(forward_action)
        up_action = QAction("Up", self)
        up_action.setShortcut(QKeySequence("Alt+Up"))
        up_action.triggered.connect(self.go_up)
        go_menu.addAction(up_action)
        tools_menu = menubar.addMenu("&Tools")
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        help_menu = menubar.addMenu("&Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        self.back_btn = QToolButton()
        self.back_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(self.back_btn)
        self.forward_btn = QToolButton()
        self.forward_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.forward_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(self.forward_btn)
        up_btn = QToolButton()
        up_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        up_btn.clicked.connect(self.go_up)
        toolbar.addWidget(up_btn)
        refresh_btn = QToolButton()
        refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        refresh_btn.clicked.connect(self.refresh_view)
        toolbar.addWidget(refresh_btn)
        toolbar.addSeparator()
        new_file_btn = QToolButton()
        new_file_btn.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        new_file_btn.setToolTip("New File")
        new_file_btn.clicked.connect(self.new_file)
        toolbar.addWidget(new_file_btn)
        new_folder_btn = QToolButton()
        new_folder_btn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        new_folder_btn.setToolTip("New Folder")
        new_folder_btn.clicked.connect(self.new_folder)
        toolbar.addWidget(new_folder_btn)
        toolbar.addSeparator()
        self.view_combo = QComboBox()
        self.view_combo.addItems(["Details", "List", "Icons", "Tiles"])
        self.view_combo.currentTextChanged.connect(lambda t: self.set_view_mode(t.lower()))
        toolbar.addWidget(self.view_combo)
        toolbar.addSeparator()
        self.address_bar = AddressBar()
        self.address_bar.path_changed.connect(self.navigate_to)
        toolbar.addWidget(self.address_bar)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setMaximumWidth(200)
        self.search_bar.textChanged.connect(self.filter_files)
        toolbar.addWidget(self.search_bar)
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.sidebar = SidebarWidget(self)
        self.main_splitter.addWidget(self.sidebar)
        self.file_view = FileViewWidget(self)
        self.file_view.set_root_path("")
        self.main_splitter.addWidget(self.file_view)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.setMovable(True)
        self.main_splitter.addWidget(self.tab_widget)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 2)
        self.main_splitter.setStretchFactor(2, 3)
        layout.addWidget(self.main_splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.file_view.navigation_requested.connect(self.navigate_to)
        self.file_view.open_file_requested.connect(self.open_file)
        self.file_view.context_menu_requested.connect(self.show_file_context_menu)
        self.sidebar.navigation_requested.connect(self.navigate_to)
        self.sidebar.context_menu_requested.connect(self.show_file_context_menu_at_path)
    
    def setup_shortcuts(self):
        QShortcut(QKeySequence("F2"), self, self.rename_selected)
        QShortcut(QKeySequence.Delete, self, self.delete_selected)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self, self.reopen_closed_tab)
        QShortcut(QKeySequence("Ctrl+Tab"), self, self.next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self, self.prev_tab)
        QShortcut(QKeySequence("Ctrl+W"), self, lambda: self.close_tab(self.tab_widget.currentIndex()))
        QShortcut(QKeySequence("F5"), self, self.run_current_file)
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
    
    def apply_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background-color: {DK_BG}; color: {DK_TEXT}; }}
            QMenuBar {{ background-color: {DK_SIDEBAR}; border-bottom: 1px solid {DK_BORDER}; }}
            QMenuBar::item {{ background-color: transparent; padding: 4px 8px; }}
            QMenuBar::item:selected {{ background-color: {DK_HOVER}; }}
            QMenu {{ background-color: {DK_SIDEBAR}; border: 1px solid {DK_BORDER}; }}
            QMenu::item {{ padding: 4px 20px; }}
            QMenu::item:selected {{ background-color: {ACCENT}; }}
            QToolBar {{ background-color: {DK_SIDEBAR}; border: none; spacing: 3px; padding: 2px; }}
            QToolButton {{ background-color: transparent; border: none; padding: 4px; }}
            QToolButton:hover {{ background-color: {DK_HOVER}; border-radius: 3px; }}
            QLineEdit {{ background-color: {DK_WIDGET}; border: 1px solid {DK_BORDER}; padding: 4px 8px; border-radius: 3px; color: {DK_TEXT}; }}
            QTreeView, QListView, QTableView {{ background-color: {DK_BG}; alternate-background-color: #1D1D1D; selection-background-color: {ACCENT}; border: none; outline: none; }}
            QTreeView::item, QListView::item, QTableView::item {{ padding: 2px; }}
            QTreeView::item:hover, QListView::item:hover, QTableView::item:hover {{ background-color: {DK_HOVER}; }}
            QHeaderView::section {{ background-color: {DK_SIDEBAR}; color: {DK_TEXT_SECONDARY}; padding: 6px; border: none; border-right: 1px solid {DK_BORDER}; }}
            QTabWidget::pane {{ border: none; background-color: {DK_BG}; }}
            QTabBar::tab {{ background-color: {DK_SIDEBAR}; color: {DK_TEXT_SECONDARY}; padding: 8px 16px; margin-right: 2px; }}
            QTabBar::tab:selected {{ background-color: {EDITOR_BG}; color: {DK_TEXT}; border-bottom: 2px solid {ACCENT}; }}
            QTabBar::tab:hover {{ background-color: {DK_HOVER}; }}
            QStatusBar {{ background-color: {DK_SIDEBAR}; color: {DK_TEXT_SECONDARY}; border-top: 1px solid {DK_BORDER}; }}
            QSplitter::handle {{ background-color: {DK_BORDER}; width: 2px; }}
            QScrollBar:vertical {{ background-color: {DK_BG}; width: 12px; }}
            QScrollBar::handle:vertical {{ background-color: {DK_WIDGET}; min-height: 20px; border-radius: 6px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {DK_HOVER}; }}
            QScrollBar:horizontal {{ background-color: {DK_BG}; height: 12px; }}
            QScrollBar::handle:horizontal {{ background-color: {DK_WIDGET}; min-width: 20px; border-radius: 6px; }}
            QScrollBar::handle:horizontal:hover {{ background-color: {DK_HOVER}; }}
            QProgressBar {{ border: 1px solid {DK_BORDER}; border-radius: 3px; text-align: center; }}
            QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 3px; }}
        """)
    
    def setup_status_bar(self):
        self.status_path_label = QLabel()
        self.status_count_label = QLabel()
        self.status_bar.addPermanentWidget(self.status_path_label)
        self.status_bar.addPermanentWidget(self.status_count_label)
        self.update_status_bar()
    
    def update_status_bar(self):
        path = self.file_view.current_path
        if not path or path == "":
            self.status_path_label.setText(" This PC ")
            self.status_count_label.setText("")
        else:
            self.status_path_label.setText(f" {path} ")
            try:
                items = list(Path(path).iterdir())
                count = len(items)
                self.status_count_label.setText(f" {count} items ")
            except:
                self.status_count_label.setText("")
    
    def navigate_to(self, path: str):
        if not path or path == "":
            self.file_view.set_root_path("")
            self.address_bar.set_path("")
            self.update_status_bar()
            if self.history_index == -1 or self.history[self.history_index] != "":
                self.history = self.history[:self.history_index+1]
                self.history.append("")
                self.history_index += 1
            self.update_navigation_buttons()
            return
        if os.path.exists(path):
            if self.history_index == -1 or self.history[self.history_index] != path:
                self.history = self.history[:self.history_index+1]
                self.history.append(path)
                self.history_index += 1
            self.file_view.set_root_path(path)
            self.address_bar.set_path(path)
            self.update_status_bar()
            self.update_navigation_buttons()
    
    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            path = self.history[self.history_index]
            if not path or path == "":
                self.file_view.set_root_path("")
                self.address_bar.set_path("")
            else:
                self.file_view.set_root_path(path)
                self.address_bar.set_path(path)
            self.update_status_bar()
            self.update_navigation_buttons()
    
    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            path = self.history[self.history_index]
            if not path or path == "":
                self.file_view.set_root_path("")
                self.address_bar.set_path("")
            else:
                self.file_view.set_root_path(path)
                self.address_bar.set_path(path)
            self.update_status_bar()
            self.update_navigation_buttons()
    
    def go_up(self):
        current = self.file_view.current_path
        if not current or current == "":
            return
        parent = str(Path(current).parent)
        if parent == current:
            self.navigate_to("")
        elif os.path.exists(parent):
            self.navigate_to(parent)
        else:
            self.navigate_to("")
    
    def update_navigation_buttons(self):
        self.back_btn.setEnabled(self.history_index > 0)
        self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)
    
    def refresh_view(self):
        self.file_view.refresh()
        self.update_status_bar()
    
    def set_view_mode(self, mode: str):
        self.file_view.set_view_mode(mode)
    
    def filter_files(self, text: str):
        if text:
            self.file_view.model.setNameFilters([f"*{text}*"])
        else:
            self.file_view.model.setNameFilters([])
    
    def new_file(self):
        if not self.file_view.current_path or self.file_view.current_path == "":
            QMessageBox.warning(self, "New File", "Please navigate to a folder first.")
            return
        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            path = os.path.join(self.file_view.current_path, name)
            try:
                Path(path).touch()
                self.refresh_view()
                self.open_file(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {e}")
    
    def new_folder(self):
        if not self.file_view.current_path or self.file_view.current_path == "":
            QMessageBox.warning(self, "New Folder", "Please navigate to a folder first.")
            return
        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            path = os.path.join(self.file_view.current_path, name)
            try:
                Path(path).mkdir()
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {e}")
    
    def rename_selected(self):
        paths = self.file_view.selected_paths()
        if not paths:
            return
        path = paths[0]
        name, ok = QInputDialog.getText(self, "Rename", "New name:", text=os.path.basename(path))
        if ok and name:
            new_path = os.path.join(os.path.dirname(path), name)
            try:
                os.rename(path, new_path)
                self.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not rename: {e}")
    
    def delete_selected(self):
        paths = self.file_view.selected_paths()
        if not paths:
            return
        msg = f"Are you sure you want to delete {len(paths)} item(s)?"
        if QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for path in paths:
                try:
                    if HAS_WINSHELL:
                        winshell.delete_file(path, allow_undo=True)
                    else:
                        if os.path.isdir(path):
                            shutil.rmtree(path)
                        else:
                            os.remove(path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not delete {path}: {e}")
            self.refresh_view()
    
    def cut(self):
        paths = self.file_view.selected_paths()
        if paths:
            data = QMimeData()
            data.setUrls([QUrl.fromLocalFile(p) for p in paths])
            data.setData("application/x-melroms-cut", b"1")
            QApplication.clipboard().setMimeData(data)
    
    def copy(self):
        paths = self.file_view.selected_paths()
        if paths:
            data = QMimeData()
            data.setUrls([QUrl.fromLocalFile(p) for p in paths])
            QApplication.clipboard().setMimeData(data)
    
    def paste(self):
        if not self.file_view.current_path or self.file_view.current_path == "":
            QMessageBox.warning(self, "Paste", "Please navigate to a folder first.")
            return
        mime = QApplication.clipboard().mimeData()
        if mime.hasUrls():
            urls = mime.urls()
            is_cut = mime.data("application/x-melroms-cut") == b"1"
            dest = self.file_view.current_path
            progress = QProgressDialog("Processing...", "Cancel", 0, len(urls), self)
            progress.setWindowModality(Qt.WindowModal)
            for i, url in enumerate(urls):
                if progress.wasCanceled():
                    break
                progress.setValue(i)
                src = url.toLocalFile()
                dst = os.path.join(dest, os.path.basename(src))
                try:
                    if is_cut:
                        shutil.move(src, dst)
                    else:
                        if os.path.isdir(src):
                            shutil.copytree(src, dst)
                        else:
                            shutil.copy2(src, dst)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not paste {src}: {e}")
            progress.setValue(len(urls))
            self.refresh_view()
            if is_cut:
                QApplication.clipboard().clear()
    
    def undo(self):
        editor = self.get_current_editor()
        if editor:
            editor.undo()
    
    def redo(self):
        editor = self.get_current_editor()
        if editor:
            editor.redo()
    
    def open_file(self, path: str):
        """Open file using associated application or built-in editor."""
        ext = Path(path).suffix.lower()
        assoc = self.settings.get_association(ext)
        
        if assoc == "builtin":
            if is_text_file(path):
                self.open_in_editor(path)
            else:
                # Fallback to system
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif assoc == "system":
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif assoc and os.path.exists(assoc):
            # Custom executable
            subprocess.Popen([assoc, path])
        else:
            # Default: text files in editor, others system
            if is_text_file(path):
                self.open_in_editor(path)
            else:
                QDesktopServices.openUrl(QUrl.fromLocalFile(path))
                
    def open_in_editor(self, path: str):
        """Open text file in built-in editor tab."""
        for i in range(self.tab_widget.count()):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, CodeEditor) and widget.file_path == path:
                self.tab_widget.setCurrentIndex(i)
                return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            editor = CodeEditor(path)
            editor.setPlainText(content)
            editor.set_modified(False)
            index = self.tab_widget.addTab(editor, os.path.basename(path))
            self.tab_widget.setCurrentIndex(index)
            self.settings.add_recent_file(path)
            self.update_recent_menu()
            editor.textChanged.connect(lambda e=editor: self.on_editor_modified(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")
    
    def open_file_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "All Files (*.*)")
        for path in paths:
            self.open_file(path)
    
    def save_current_file(self):
        editor = self.get_current_editor()
        if editor:
            if editor.file_path:
                self.save_editor_to_path(editor, editor.file_path)
            else:
                self.save_as_current_file()
    
    def save_as_current_file(self):
        editor = self.get_current_editor()
        if editor:
            path, _ = QFileDialog.getSaveFileName(self, "Save As", "", "All Files (*.*)")
            if path:
                self.save_editor_to_path(editor, path)
                editor.file_path = path
                self.tab_widget.setTabText(self.tab_widget.currentIndex(), os.path.basename(path))
                editor.set_language(detect_language(path))
    
    def save_all_files(self):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, CodeEditor) and editor.is_modified:
                if editor.file_path:
                    self.save_editor_to_path(editor, editor.file_path)
                else:
                    self.tab_widget.setCurrentIndex(i)
                    self.save_as_current_file()
    
    def save_editor_to_path(self, editor: CodeEditor, path: str):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            editor.set_modified(False)
            self.update_tab_title(editor)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {e}")
    
    def on_editor_modified(self, editor: CodeEditor):
        if not editor.is_modified:
            editor.is_modified = True
            self.update_tab_title(editor)
    
    def update_tab_title(self, editor: CodeEditor):
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == editor:
                name = os.path.basename(editor.file_path) if editor.file_path else "Untitled"
                if editor.is_modified:
                    name += " *"
                self.tab_widget.setTabText(i, name)
                break
    
    def get_current_editor(self) -> Optional[CodeEditor]:
        widget = self.tab_widget.currentWidget()
        if isinstance(widget, CodeEditor):
            return widget
        return None
    
    def close_tab(self, index: int):
        widget = self.tab_widget.widget(index)
        if isinstance(widget, CodeEditor):
            if widget.is_modified:
                name = os.path.basename(widget.file_path) if widget.file_path else "Untitled"
                reply = QMessageBox.question(self, "Unsaved Changes", 
                                             f"Save changes to {name}?",
                                             QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                if reply == QMessageBox.Save:
                    if widget.file_path:
                        self.save_editor_to_path(widget, widget.file_path)
                    else:
                        self.tab_widget.setCurrentIndex(index)
                        self.save_as_current_file()
                        if not widget.file_path:
                            return
                elif reply == QMessageBox.Cancel:
                    return
            if widget.file_path:
                self.closed_tabs.append({
                    'path': widget.file_path,
                    'content': widget.toPlainText(),
                    'cursor': (widget.textCursor().position(), widget.textCursor().anchor())
                })
        self.tab_widget.removeTab(index)
    
    def reopen_closed_tab(self):
        if self.closed_tabs:
            data = self.closed_tabs.pop()
            editor = CodeEditor(data['path'])
            editor.setPlainText(data['content'])
            editor.set_modified(False)
            cursor = editor.textCursor()
            cursor.setPosition(data['cursor'][0])
            cursor.setPosition(data['cursor'][1], QTextCursor.KeepAnchor)
            editor.setTextCursor(cursor)
            index = self.tab_widget.addTab(editor, os.path.basename(data['path']))
            self.tab_widget.setCurrentIndex(index)
    
    def next_tab(self):
        count = self.tab_widget.count()
        if count > 0:
            self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() + 1) % count)
    
    def prev_tab(self):
        count = self.tab_widget.count()
        if count > 0:
            self.tab_widget.setCurrentIndex((self.tab_widget.currentIndex() - 1) % count)
    
    def on_tab_changed(self, index: int):
        editor = self.get_current_editor()
        if editor:
            editor.setFocus()
    
    def show_find_dialog(self):
        editor = self.get_current_editor()
        if editor:
            dialog = FindReplaceDialog(editor, self)
            dialog.show()
    
    def show_replace_dialog(self):
        editor = self.get_current_editor()
        if editor:
            dialog = FindReplaceDialog(editor, self)
            dialog.show()
    
    def go_to_line(self):
        editor = self.get_current_editor()
        if editor:
            editor.go_to_line()
    
    def run_current_file(self):
        editor = self.get_current_editor()
        if editor and editor.file_path and editor.file_path.endswith('.py'):
            terminal = TerminalWidget()
            index = self.tab_widget.addTab(terminal, "Terminal")
            self.tab_widget.setCurrentIndex(index)
            terminal.run_command(f'python "{editor.file_path}"')
    
    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
    
    def show_file_context_menu(self, pos, view):
        paths = self.file_view.selected_paths()
        if not paths:
            menu = QMenu(self)
            new_file = menu.addAction("New File")
            new_file.triggered.connect(self.new_file)
            new_folder = menu.addAction("New Folder")
            new_folder.triggered.connect(self.new_folder)
            menu.addSeparator()
            paste = menu.addAction("Paste")
            paste.triggered.connect(self.paste)
            paste.setEnabled(QApplication.clipboard().mimeData().hasUrls())
            menu.addSeparator()
            refresh = menu.addAction("Refresh")
            refresh.triggered.connect(self.refresh_view)
            if self.file_view.current_path and self.file_view.current_path != "":
                properties = menu.addAction("Properties")
                properties.triggered.connect(lambda: self.show_properties(self.file_view.current_path))
            menu.exec(view.mapToGlobal(pos))
        else:
            self.show_file_context_menu_at_path(paths[0], view.mapToGlobal(pos))
    
    def show_file_context_menu_at_path(self, path: str, global_pos):
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        open_action.triggered.connect(lambda: self.open_file(path))
        open_with_menu = menu.addMenu("Open with")
        builtin_action = open_with_menu.addAction("Built-in Editor")
        builtin_action.triggered.connect(lambda: self.open_file(path))
        system_action = open_with_menu.addAction("System Default")
        system_action.triggered.connect(lambda: self.open_with_system(path))
        choose_action = open_with_menu.addAction("Choose another app...")
        choose_action.triggered.connect(lambda: self.open_with_dialog(path))
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.open_file(path))
        if path.endswith('.py'):
            run_action = menu.addAction("Run")
            run_action.triggered.connect(lambda: self.run_script(path))
        menu.addSeparator()
        cut_action = menu.addAction("Cut")
        cut_action.triggered.connect(self.cut)
        copy_action = menu.addAction("Copy")
        copy_action.triggered.connect(self.copy)
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self.delete_selected)
        rename_action = menu.addAction("Rename")
        rename_action.triggered.connect(self.rename_selected)
        menu.addSeparator()
        add_qa = menu.addAction("Add to Quick Access")
        add_qa.triggered.connect(lambda: self.settings.add_quick_access(path))
        if Path(path).suffix.lower() == '.zip':
            extract_here = menu.addAction("Extract Here")
            extract_here.triggered.connect(lambda: self.extract_archive(path, self.file_view.current_path))
            extract_to = menu.addAction("Extract to...")
            extract_to.triggered.connect(lambda: self.extract_archive_dialog(path))
        compress = menu.addAction("Compress to ZIP")
        compress.triggered.connect(lambda: self.compress_to_zip([path]))
        menu.addSeparator()
        copy_path = menu.addAction("Copy path")
        copy_path.triggered.connect(lambda: QApplication.clipboard().setText(path))
        open_folder = menu.addAction("Open containing folder")
        open_folder.triggered.connect(lambda: self.navigate_to(str(Path(path).parent)))
        properties = menu.addAction("Properties")
        properties.triggered.connect(lambda: self.show_properties(path))
        menu.exec(global_pos)
    
    def open_with_dialog(self, path: str):
        """Open file with chosen application and optionally save association."""
        exe, _ = QFileDialog.getOpenFileName(self, "Choose Application", "", "Executables (*.exe);;All Files (*.*)")
        if exe:
            subprocess.Popen([exe, path])
            ext = Path(path).suffix.lower()
            # Automatically save this association for future double-clicks
            self.settings.set_association(ext, exe)
            QMessageBox.information(self, "Association Saved", 
                                    f"{ext} files will now open with {os.path.basename(exe)} by default.")
                                    
    def open_with_system(self, path: str):
        """Open with system default and set association."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        ext = Path(path).suffix.lower()
        self.settings.set_association(ext, "system")
    
    def run_script(self, path: str):
        terminal = TerminalWidget()
        index = self.tab_widget.addTab(terminal, "Terminal")
        self.tab_widget.setCurrentIndex(index)
        terminal.run_command(f'python "{path}"')
    
    def extract_archive(self, archive_path: str, dest_dir: str):
        try:
            with zipfile.ZipFile(archive_path, 'r') as zf:
                zf.extractall(dest_dir)
            self.refresh_view()
            QMessageBox.information(self, "Extract", "Extraction completed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Extraction failed: {e}")
    
    def extract_archive_dialog(self, archive_path: str):
        dest = QFileDialog.getExistingDirectory(self, "Extract to...", self.file_view.current_path)
        if dest:
            self.extract_archive(archive_path, dest)
    
    def compress_to_zip(self, paths: List[str]):
        if not paths:
            return
        name = os.path.basename(paths[0]) + ".zip"
        zip_path, _ = QFileDialog.getSaveFileName(self, "Create ZIP", os.path.join(self.file_view.current_path, name), "ZIP Files (*.zip)")
        if zip_path:
            try:
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for path in paths:
                        if os.path.isdir(path):
                            for root, _, files in os.walk(path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, os.path.dirname(path))
                                    zf.write(file_path, arcname)
                        else:
                            zf.write(path, os.path.basename(path))
                self.refresh_view()
                QMessageBox.information(self, "Compress", "Compression completed.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Compression failed: {e}")
    
    def show_properties(self, path: str):
        dialog = PropertiesDialog(path, self)
        dialog.exec()
    
    def show_settings(self):
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()
    
    def show_about(self):
        QMessageBox.about(self, "About MelRoms Explorer",
                          "MelRoms Explorer\n\n"
                          "A powerful file explorer and code editor.\n"
                          "Version 1.0.0\n\n"
                          "Features:\n"
                          "- Multi-tab code editor with syntax highlighting\n"
                          "- File operations with drag & drop\n"
                          "- Quick access and tree navigation\n"
                          "- Built-in terminal\n"
                          "- Archive support (ZIP)\n"
                          "- Dark theme")
    
    def update_recent_menu(self):
        self.recent_menu.clear()
        for path in self.settings.recent_files[:10]:
            if os.path.exists(path):
                action = QAction(os.path.basename(path), self)
                action.setToolTip(path)
                action.triggered.connect(lambda checked, p=path: self.open_file(p))
                self.recent_menu.addAction(action)
        if self.settings.recent_files:
            self.recent_menu.addSeparator()
            clear_action = QAction("Clear Recent", self)
            clear_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_action)
    
    def clear_recent_files(self):
        self.settings._recent_files = []
        self.settings.save_lists()
        self.update_recent_menu()
    
    def restore_session(self):
        pass
    
    def closeEvent(self, event: QCloseEvent):
        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, CodeEditor) and editor.is_modified:
                self.tab_widget.setCurrentIndex(i)
                name = os.path.basename(editor.file_path) if editor.file_path else "Untitled"
                reply = QMessageBox.question(self, "Unsaved Changes",
                                             f"Save changes to {name}?",
                                             QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                if reply == QMessageBox.Save:
                    if editor.file_path:
                        self.save_editor_to_path(editor, editor.file_path)
                    else:
                        self.save_as_current_file()
                        if not editor.file_path:
                            event.ignore()
                            return
                elif reply == QMessageBox.Cancel:
                    event.ignore()
                    return
        self.settings.save_lists()
        event.accept()

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MelRomsExplorer()
    window.show()
    sys.exit(app.exec())