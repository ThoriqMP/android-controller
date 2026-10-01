"""
setup.py - First-Run Setup Wizard
TUI interaktif untuk konfigurasi awal aplikasi (API key, dll)
Dipanggil otomatis saat pertama kali aplikasi dijalankan.
"""

import os
import sys
import json
import time
import asyncio
from pathlib import Path

from ui.tui import (
    divider, info, success, error, warn,
    prompt, confirm, Spinner, section_header, print_box
)
from ui.colors import C, colorize


# ============================================================
# KONSTANTA
# ============================================================

_SRC_DIR    = Path(__file__).parent
_CONFIG_DIR = _SRC_DIR.parent / "config"
_CONFIG_FILE = _CONFIG_DIR / "settings.json"
_SETUP_DONE_MARKER = _CONFIG_DIR / ".setup_done"


# ============================================================
# DETEKSI FIRST RUN
# ============================================================

def is_first_run() -> bool:
    """
    Kembalikan True jika aplikasi belum pernah dikonfigurasi.
    Ditandai dengan ada/tidaknya file .setup_done dan API key.
    """
    if not _SETUP_DONE_MARKER.exists():
        return True
    
    # Cek juga apakah API key sudah diisi
    config = _load_config_raw()
    api_key = (
        config.get("gemini_api_key")
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    return not bool(api_key)


def mark_setup_done():
    """Tandai setup sudah selesai."""
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _SETUP_DONE_MARKER.write_text("done")


def _load_config_raw() -> dict:
    if _CONFIG_FILE.exists():
        try:
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_config(config: dict):
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


# ============================================================
# API KEY VALIDATOR
# ============================================================

async def _test_api_key(api_key: str) -> tuple[bool, str]:
    """
    Test apakah API key valid dengan mengirim prompt sederhana.
    Returns: (is_valid, message)
    """
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content("Balas dengan satu kata: OK")
        text = response.text.strip()
        return True, f"API key valid! Respons: '{text}'"
    except ImportError:
        return False, "google-generativeai belum terinstall (pip install google-generativeai)"
    except Exception as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "invalid" in msg.lower():
            return False, "API key tidak valid. Cek kembali di aistudio.google.com"
        if "QUOTA" in msg or "quota" in msg.lower():
            return True, "API key valid (quota limit, tapi key OK)"
        return False, f"Error: {msg[:120]}"


def test_api_key_sync(api_key: str) -> tuple[bool, str]:
    return asyncio.run(_test_api_key(api_key))


# ============================================================
# LAYAR SETUP WIZARD
# ============================================================

def _print_welcome_screen():
    """Tampilkan layar selamat datang setup wizard."""
    width = 60

    lines_top = [
        colorize("  ╔" + "═" * (width - 2) + "╗", C.BRIGHT_CYAN),
        colorize("  ║", C.BRIGHT_CYAN) + colorize(
            " 🤖  SELAMAT DATANG DI ANDROID CONTROLLER".center(width - 2),
            C.BOLD, C.BRIGHT_WHITE
        ) + colorize("║", C.BRIGHT_CYAN),
        colorize("  ║", C.BRIGHT_CYAN) + colorize(
            " Termux × Antigravity AI Agent".center(width - 2),
            C.DIM, C.BRIGHT_CYAN
        ) + colorize("║", C.BRIGHT_CYAN),
        colorize("  ╚" + "═" * (width - 2) + "╝", C.BRIGHT_CYAN),
    ]
    print()
    for line in lines_top:
        print(line)
    print()


def _print_step_header(step: int, total: int, title: str, color: str = C.BRIGHT_CYAN):
    """Tampilkan header langkah setup."""
    badge = colorize(f" LANGKAH {step}/{total} ", C.BOLD, C.BG_CYAN, C.BLACK)
    print(f"\n  {badge}  {colorize(title, C.BOLD, color)}\n")


# ============================================================
# LANGKAH-LANGKAH SETUP
# ============================================================

TOTAL_STEPS = 4


def _step_intro() -> bool:
    """Langkah 1: Penjelasan singkat."""
    _print_step_header(1, TOTAL_STEPS, "Pengenalan", C.BRIGHT_CYAN)
    
    print_box(
        "ℹ️  Apa itu Android Controller?",
        "Aplikasi CLI untuk full developer workflow dari HP Android.\n\n"
        "Fitur utama:\n"
        "  • Chat dengan Antigravity AI agent\n"
        "  • Scaffold project (Python, Node, React, dll)\n"
        "  • Jalankan dev server dari terminal\n"
        "  • Kelola Docker container\n\n"
        "Setup ini hanya perlu dilakukan SEKALI.",
        color=C.BRIGHT_CYAN
    )
    
    return confirm("Lanjutkan setup?", default=True)


def _step_api_key() -> str | None:
    """
    Langkah 2: Input dan validasi API key.
    Returns: API key string jika valid, None jika skip.
    """
    _print_step_header(2, TOTAL_STEPS, "Konfigurasi API Key", C.BRIGHT_YELLOW)
    
    print_box(
        "🔑 Mengapa perlu API Key?",
        "Android Controller menggunakan Gemini AI (Google) untuk:\n"
        "  • Menjawab pertanyaan koding kamu\n"
        "  • Membuat & menjelaskan kode\n"
        "  • Membantu scaffold project\n\n"
        "API Key GRATIS tersedia di:\n"
        "  → https://aistudio.google.com/app/apikey",
        color=C.BRIGHT_YELLOW
    )
    
    # Cek apakah sudah ada di environment
    env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if env_key:
        masked = env_key[:8] + "*" * (len(env_key) - 8)
        info(f"Ditemukan API key di environment: {masked}")
        if confirm("Gunakan API key dari environment ini?", default=True):
            return env_key
    
    # Input API key
    while True:
        print()
        arrow = colorize("›", C.BRIGHT_YELLOW, C.BOLD)
        sys.stdout.write(f"  {arrow} Masukkan Gemini API Key: ")
        sys.stdout.flush()
        
        try:
            # Sembunyikan input seperti password
            try:
                import getpass
                api_key = getpass.getpass(prompt="")
            except Exception:
                api_key = input().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        
        api_key = api_key.strip()
        
        if not api_key:
            if confirm("Skip konfigurasi API key? (fitur AI tidak akan berfungsi)", default=False):
                warn("API key dilewati. Atur nanti dengan: actl config")
                return None
            continue
        
        # Validasi format minimal
        if not api_key.startswith("AIza") or len(api_key) < 30:
            error("Format API key tidak valid. Harus diawali 'AIza' dan minimal 30 karakter.")
            info("Cek kembali di: https://aistudio.google.com/app/apikey")
            continue
        
        # Test koneksi
        print()
        with Spinner("Memvalidasi API key ke server Google..."):
            is_valid, msg = test_api_key_sync(api_key)
        
        if is_valid:
            success(msg)
            return api_key
        else:
            error(msg)
            if not confirm("Coba masukkan API key lagi?", default=True):
                return None


def _step_preferences() -> dict:
    """
    Langkah 3: Preferensi opsional.
    Returns: dict preferensi.
    """
    _print_step_header(3, TOTAL_STEPS, "Preferensi (Opsional)", C.BRIGHT_MAGENTA)
    
    config = {}
    
    # Model AI
    print(f"  {colorize('Model AI yang digunakan:', C.BRIGHT_WHITE)}")
    models = [
        ("gemini-2.0-flash",    "Gemini 2.0 Flash — Cepat & hemat (Recommended)"),
        ("gemini-2.0-pro",      "Gemini 2.0 Pro — Lebih pintar, lebih lambat"),
        ("gemini-1.5-flash",    "Gemini 1.5 Flash — Stabil & andal"),
    ]
    for i, (_, label) in enumerate(models, 1):
        num = colorize(f"  {i})", C.BRIGHT_BLACK)
        print(f"{num} {label}")
    
    sys.stdout.write(f"\n  {colorize('›', C.BRIGHT_CYAN, C.BOLD)} Pilih model [1-{len(models)}, default=1]: ")
    sys.stdout.flush()
    try:
        val = input().strip()
        idx = (int(val) - 1) if val.isdigit() and 1 <= int(val) <= len(models) else 0
    except (EOFError, KeyboardInterrupt):
        idx = 0
    
    config["default_model"] = models[idx][0]
    success(f"Model dipilih: {models[idx][1]}")
    
    # Folder projects
    print()
    default_dir = "~/projects"
    arrow = colorize("›", C.BRIGHT_CYAN, C.BOLD)
    sys.stdout.write(f"  {arrow} Folder default untuk project baru [{default_dir}]: ")
    sys.stdout.flush()
    try:
        folder = input().strip()
    except (EOFError, KeyboardInterrupt):
        folder = ""
    
    config["default_projects_dir"] = folder if folder else default_dir
    
    # Buat folder jika belum ada
    projects_path = Path(config["default_projects_dir"]).expanduser()
    projects_path.mkdir(parents=True, exist_ok=True)
    success(f"Folder project: {projects_path}")
    
    return config


def _step_save_and_finish(api_key: str | None, prefs: dict):
    """Langkah 4: Simpan konfigurasi dan tampilkan ringkasan."""
    _print_step_header(4, TOTAL_STEPS, "Menyimpan Konfigurasi", C.BRIGHT_GREEN)
    
    with Spinner("Menyimpan konfigurasi..."):
        # Load existing config
        config = _load_config_raw()
        
        # Update dengan nilai baru
        if api_key:
            config["gemini_api_key"] = api_key
            os.environ["GEMINI_API_KEY"] = api_key
        
        config.update({
            "default_model": prefs.get("default_model", "gemini-2.0-flash"),
            "default_projects_dir": prefs.get("default_projects_dir", "~/projects"),
            "theme": "dark",
            "language": "id",
        })
        
        _save_config(config)
        
        # Simpan ke shell profile untuk persistensi
        if api_key:
            _append_to_shell_profile(api_key)
        
        # Tandai setup selesai
        mark_setup_done()
        time.sleep(0.5)
    
    # Ringkasan
    api_status = (
        colorize("✓ Terkonfigurasi", C.BRIGHT_GREEN)
        if api_key
        else colorize("✗ Tidak diset (atur nanti: actl config)", C.BRIGHT_RED)
    )
    
    print_box(
        "✅ Setup Selesai!",
        f"API Key      : {api_status}\n"
        f"Model AI     : {config.get('default_model', '-')}\n"
        f"Folder project: {config.get('default_projects_dir', '-')}\n"
        f"Config file  : {_CONFIG_FILE}",
        color=C.BRIGHT_GREEN
    )
    
    print()
    print(colorize("  Perintah yang tersedia:", C.BOLD, C.BRIGHT_WHITE))
    cmds = [
        ("actl",         "Menu utama interaktif"),
        ("actl chat",    "Chat dengan Antigravity AI"),
        ("actl new",     "Buat project baru"),
        ("actl serve",   "Kelola dev server"),
        ("actl docker",  "Kelola Docker"),
        ("actl config",  "Ubah konfigurasi kapan saja"),
    ]
    for cmd, desc in cmds:
        print(f"  {colorize(cmd, C.BRIGHT_CYAN):<30} {colorize(desc, C.DIM)}")
    print()
    
    input(colorize("  Tekan Enter untuk mulai menggunakan actl...", C.BRIGHT_BLACK))


def _append_to_shell_profile(api_key: str):
    """Tambahkan API key ke ~/.bashrc atau ~/.zshrc."""
    for profile in ["~/.zshrc", "~/.bashrc"]:
        profile_path = Path(profile).expanduser()
        if profile_path.exists():
            content = profile_path.read_text(encoding="utf-8")
            if "GEMINI_API_KEY" not in content:
                with profile_path.open("a", encoding="utf-8") as f:
                    f.write(f'\n# Android Controller — Antigravity AI\n')
                    f.write(f'export GEMINI_API_KEY="{api_key}"\n')
            break


# ============================================================
# ENTRY POINT SETUP WIZARD
# ============================================================

def run_setup_wizard():
    """
    Jalankan setup wizard lengkap.
    Dipanggil dari main.py saat first run terdeteksi.
    """
    _print_welcome_screen()
    
    # Langkah 1: Intro
    if not _step_intro():
        info("Setup dibatalkan. Jalankan ulang dengan: actl config")
        sys.exit(0)
    
    # Langkah 2: API Key
    api_key = _step_api_key()
    
    # Langkah 3: Preferensi
    divider(C.BRIGHT_BLACK)
    prefs = _step_preferences()
    
    # Langkah 4: Simpan & Selesai
    divider(C.BRIGHT_BLACK)
    _step_save_and_finish(api_key, prefs)
