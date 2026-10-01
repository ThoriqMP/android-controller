"""
tui.py - Terminal UI Components
Komponen TUI (Terminal User Interface) untuk Android Controller
"""

import sys
import time
import textwrap
import shutil
from ui.colors import C, colorize, gradient_text


# ============================================================
# TERMINAL SIZE HELPER
# ============================================================

def get_width() -> int:
    """Dapatkan lebar terminal (default 80 jika tidak bisa detect)."""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


# ============================================================
# BANNER & LOGO
# ============================================================

LOGO_LINES = [
    r"  ___  _   _ ___  ____   ___ ___ ____     ",
    r" / _ \| \ | |   \|  _ \ / _ \_ _|  _ \    ",
    r"| | | |  \| | | | |_) | | | | || | | |   ",
    r"| |_| | |\  | |_| |  _ <| |_| | || |_| |  ",
    r" \___/|_| \_|___/|_| \_\\___/___|____/   ",
]

SUBTITLE = "Android Controller  ×  Antigravity AI"
VERSION  = "v1.0.0"

LOGO_COLORS = [C.BRIGHT_CYAN, C.BRIGHT_BLUE, C.BRIGHT_MAGENTA]


def print_banner():
    """Tampilkan banner aplikasi yang indah di terminal."""
    width = get_width()
    print()
    for line in LOGO_LINES:
        colored = gradient_text(line, LOGO_COLORS)
        print(colored.center(width + len(colored) - len(line)))
    
    subtitle_line = colorize(f"  {SUBTITLE}  ", C.BOLD, C.BRIGHT_WHITE)
    version_line  = colorize(f"  {VERSION}  ", C.DIM, C.BRIGHT_BLACK)
    print(subtitle_line.center(width + len(subtitle_line) - len(f"  {SUBTITLE}  ")))
    print(version_line.center(width + len(version_line) - len(f"  {VERSION}  ")))
    print(colorize("─" * min(width, 60), C.BRIGHT_BLACK).center(width))
    print()


# ============================================================
# KOTAK & PANEL
# ============================================================

def box(title: str, content: str, color: str = C.BRIGHT_CYAN, width: int = None) -> str:
    """Buat kotak border dengan judul dan konten."""
    w = (width or min(get_width() - 2, 70))
    inner_w = w - 2
    
    lines = []
    # Top border
    lines.append(color + "┌" + "─" * (inner_w) + "┐" + C.RESET)
    # Title
    if title:
        title_padded = f" {title} ".center(inner_w)
        lines.append(color + "│" + C.BOLD + C.BRIGHT_WHITE + title_padded + C.RESET + color + "│" + C.RESET)
        lines.append(color + "├" + "─" * inner_w + "┤" + C.RESET)
    # Content
    for raw_line in content.splitlines():
        wrapped = textwrap.wrap(raw_line, width=inner_w - 2) or [""]
        for seg in wrapped:
            padded = f" {seg}".ljust(inner_w)
            lines.append(color + "│" + C.RESET + padded + color + "│" + C.RESET)
    # Bottom border
    lines.append(color + "└" + "─" * inner_w + "┘" + C.RESET)
    return "\n".join(lines)


def print_box(title: str, content: str, color: str = C.BRIGHT_CYAN, width: int = None):
    print(box(title, content, color, width))


# ============================================================
# STATUS MESSAGES
# ============================================================

def success(msg: str):
    print(colorize("  ✓  ", C.BOLD, C.BRIGHT_GREEN) + msg)

def error(msg: str):
    print(colorize("  ✗  ", C.BOLD, C.BRIGHT_RED) + msg)

def warn(msg: str):
    print(colorize("  ⚠  ", C.BOLD, C.BRIGHT_YELLOW) + msg)

def info(msg: str):
    print(colorize("  ℹ  ", C.BOLD, C.BRIGHT_CYAN) + msg)

def step(n: int, total: int, msg: str):
    badge = colorize(f"[{n}/{total}]", C.DIM, C.BRIGHT_BLACK)
    print(f"  {badge} {msg}")


# ============================================================
# SPINNER / LOADING ANIMASI
# ============================================================

class Spinner:
    """Spinner animasi untuk operasi yang lama."""
    
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    def __init__(self, msg: str = "Loading...", color: str = C.BRIGHT_CYAN):
        self.msg   = msg
        self.color = color
        self._running = False
        self._thread  = None
    
    def __enter__(self):
        import threading
        self._running = True
        self._thread  = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self
    
    def __exit__(self, *args):
        self._running = False
        if self._thread:
            self._thread.join()
        sys.stdout.write("\r" + " " * (len(self.msg) + 6) + "\r")
        sys.stdout.flush()
    
    def _spin(self):
        idx = 0
        while self._running:
            frame = self.FRAMES[idx % len(self.FRAMES)]
            sys.stdout.write(f"\r  {self.color}{frame}{C.RESET}  {self.msg}")
            sys.stdout.flush()
            time.sleep(0.08)
            idx += 1
    
    def update(self, msg: str):
        self.msg = msg


# ============================================================
# INPUT HELPERS
# ============================================================

def prompt(text: str, default: str = None) -> str:
    """Prompt input dengan styling."""
    default_hint = f" [{colorize(default, C.DIM)}]" if default else ""
    arrow = colorize("›", C.BRIGHT_CYAN, C.BOLD)
    sys.stdout.write(f"\n  {arrow} {text}{default_hint}: ")
    sys.stdout.flush()
    try:
        val = input().strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default or ""
    return val if val else (default or "")


def confirm(text: str, default: bool = True) -> bool:
    """Prompt konfirmasi Y/N."""
    hint = colorize("[Y/n]" if default else "[y/N]", C.DIM)
    arrow = colorize("›", C.BRIGHT_YELLOW, C.BOLD)
    sys.stdout.write(f"\n  {arrow} {text} {hint}: ")
    sys.stdout.flush()
    try:
        val = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    if not val:
        return default
    return val in ("y", "yes", "ya")


def menu(title: str, options: list[str], color: str = C.BRIGHT_CYAN) -> int:
    """
    Tampilkan menu pilihan dan kembalikan index pilihan (0-based).
    Returns -1 jika user menekan Ctrl+C.
    """
    print(f"\n  {colorize(title, C.BOLD, color)}")
    for i, opt in enumerate(options, 1):
        num = colorize(f"  {i})", C.BRIGHT_BLACK)
        print(f"{num} {opt}")
    
    while True:
        try:
            arrow = colorize("›", C.BRIGHT_CYAN, C.BOLD)
            sys.stdout.write(f"\n  {arrow} Pilih [1-{len(options)}]: ")
            sys.stdout.flush()
            val = input().strip()
            if val.isdigit() and 1 <= int(val) <= len(options):
                return int(val) - 1
            error(f"Masukkan angka antara 1 dan {len(options)}")
        except (EOFError, KeyboardInterrupt):
            print()
            return -1


# ============================================================
# CHAT BUBBLE
# ============================================================

def print_user_bubble(text: str):
    """Tampilkan pesan user dalam bubble."""
    width = min(get_width() - 4, 70)
    lines = textwrap.wrap(text, width - 4) or [text]
    print()
    print(colorize("  YOU", C.BOLD, C.BRIGHT_WHITE))
    for line in lines:
        print(colorize("  │ ", C.BRIGHT_BLUE) + line)


def print_ai_bubble(text: str, streaming: bool = False):
    """Tampilkan respons AI dalam bubble."""
    width = min(get_width() - 4, 70)
    print()
    print(colorize("  🤖 ANTIGRAVITY", C.BOLD, C.BRIGHT_MAGENTA))
    if not streaming:
        lines = textwrap.wrap(text, width - 4) or [text]
        for line in lines:
            print(colorize("  │ ", C.BRIGHT_MAGENTA) + line)
    else:
        # Streaming mode: print langsung
        sys.stdout.write(colorize("  │ ", C.BRIGHT_MAGENTA))
        sys.stdout.flush()


def print_ai_token(token: str):
    """Print single token (streaming mode)."""
    if "\n" in token:
        parts = token.split("\n")
        for i, part in enumerate(parts):
            sys.stdout.write(part)
            if i < len(parts) - 1:
                sys.stdout.write("\n" + colorize("  │ ", C.BRIGHT_MAGENTA))
    else:
        sys.stdout.write(token)
    sys.stdout.flush()


def print_ai_done():
    """Tutup streaming bubble."""
    print()


# ============================================================
# DIVIDER & SEPARATOR
# ============================================================

def divider(color: str = C.BRIGHT_BLACK):
    width = min(get_width(), 70)
    print(colorize("  " + "─" * (width - 2), color))


def section_header(title: str, color: str = C.BRIGHT_CYAN):
    width = min(get_width(), 70)
    line = "─" * ((width - len(title) - 4) // 2)
    print()
    print(colorize(f"  {line} {title} {line}", C.BOLD, color))
    print()
