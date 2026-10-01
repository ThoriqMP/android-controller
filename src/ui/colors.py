"""
colors.py - Terminal color & styling definitions
Menggunakan ANSI escape codes untuk tampilan TUI yang indah
"""

# ============================================================
# ANSI ESCAPE CODES
# ============================================================

class Colors:
    """Warna & format terminal menggunakan ANSI codes."""
    
    RESET      = "\033[0m"
    BOLD       = "\033[1m"
    DIM        = "\033[2m"
    ITALIC     = "\033[3m"
    UNDERLINE  = "\033[4m"
    BLINK      = "\033[5m"
    REVERSE    = "\033[7m"

    # Foreground
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"
    
    # Bright foreground
    BRIGHT_BLACK   = "\033[90m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

    # Background
    BG_BLACK   = "\033[40m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"

C = Colors  # Alias pendek


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def colorize(text: str, *styles: str) -> str:
    """Wrap teks dengan satu atau lebih style ANSI."""
    return "".join(styles) + text + C.RESET


def gradient_text(text: str, colors: list[str]) -> str:
    """Beri warna berbeda per karakter (simulasi gradient)."""
    result = ""
    n = len(colors)
    for i, char in enumerate(text):
        result += colors[i % n] + char
    return result + C.RESET


def strip_ansi(text: str) -> str:
    """Hapus semua ANSI escape codes dari string."""
    import re
    return re.sub(r"\033\[[0-9;]*m", "", text)
