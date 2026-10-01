"""
main.py - Core CLI Application
Entry point utama untuk Android Controller CLI
"""

import sys
import os
import argparse

# Pastikan src/ ada di path
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from ui.tui import (
    print_banner, menu, info, success, error, warn,
    section_header, confirm, prompt, print_box, divider
)
from ui.colors import C, colorize


# ============================================================
# VERSION INFO
# ============================================================

APP_VERSION = "1.0.0"
APP_NAME    = "Android Controller (actl)"


# ============================================================
# COMMAND HANDLERS
# ============================================================

def cmd_chat(args):
    """Handler: actl chat"""
    print_banner()
    from agent import start_chat
    start_chat()


def cmd_new(args):
    """Handler: actl new"""
    print_banner()
    from scaffold import run_scaffold
    run_scaffold()


def cmd_serve(args):
    """Handler: actl serve"""
    print_banner()
    
    # Jika ada flag --stop
    if hasattr(args, "stop") and args.stop:
        from dev_server import stop_server
        stop_server(args.stop)
        return
    
    from dev_server import run_serve_manager
    run_serve_manager()


def cmd_docker(args):
    """Handler: actl docker"""
    print_banner()
    from docker_mgr import run_docker_manager
    run_docker_manager()


def cmd_ask(args):
    """Handler: actl ask '<pertanyaan>'"""
    if not args.question:
        error("Gunakan: actl ask 'pertanyaan kamu'")
        return
    
    question = " ".join(args.question)
    print()
    info(f"Menanyakan ke Antigravity AI: {question[:60]}...")
    print()
    
    from agent import quick_task
    answer = quick_task(question)
    
    print()
    section_header("💬 JAWABAN AI", C.BRIGHT_MAGENTA)
    print()
    # Print dengan word wrap sederhana
    import textwrap
    for line in answer.splitlines():
        wrapped = textwrap.wrap(line, width=70) or [""]
        for seg in wrapped:
            print(f"  {seg}")
    print()


def cmd_config(args):
    """Handler: actl config"""
    print_banner()
    section_header("⚙️  KONFIGURASI", C.BRIGHT_YELLOW)
    
    config_path = os.path.join(
        os.path.dirname(_SRC_DIR), "config", "settings.json"
    )
    
    import json
    from pathlib import Path
    
    config_file = Path(config_path)
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
        except Exception:
            config = {}
    else:
        config = {}
    
    # Default values
    defaults = {
        "gemini_api_key": "",
        "default_model": "gemini-2.0-flash",
        "default_projects_dir": "~/projects",
        "theme": "dark",
        "language": "id",
    }
    
    for k, v in defaults.items():
        if k not in config:
            config[k] = v
    
    print_box(
        "📋 Konfigurasi Saat Ini",
        "\n".join(
            f"{k:<25}: {('*' * 8) if 'key' in k and v else (v or '(kosong)')}"
            for k, v in config.items()
        ),
        color=C.BRIGHT_YELLOW
    )
    
    if confirm("Ubah konfigurasi?"):
        choice = menu(
            "Pilih pengaturan yang diubah:",
            [
                "GEMINI_API_KEY (wajib untuk fallback mode)",
                "Default model AI",
                "Folder project default",
                "Bahasa (id/en)",
                "Kembali",
            ]
        )
        
        if choice == 0:
            key = prompt("Masukkan GEMINI_API_KEY")
            if key:
                config["gemini_api_key"] = key
                os.environ["GEMINI_API_KEY"] = key
                success("API key tersimpan!")
        elif choice == 1:
            models = [
                "gemini-2.0-flash",
                "gemini-2.0-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
            ]
            m = menu("Pilih model:", models)
            if m != -1:
                config["default_model"] = models[m]
                success(f"Model diubah ke: {models[m]}")
        elif choice == 2:
            d = prompt("Folder default", default=config["default_projects_dir"])
            config["default_projects_dir"] = d
            success(f"Folder default: {d}")
        elif choice == 3:
            l = menu("Pilih bahasa:", ["Indonesia (id)", "English (en)"])
            if l != -1:
                config["language"] = ["id", "en"][l]
        
        if choice != 4:
            config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
            success("Konfigurasi tersimpan!")


def cmd_status(args):
    """Handler: actl status — tampilkan status sistem"""
    print_banner()
    section_header("📊 STATUS SISTEM", C.BRIGHT_CYAN)
    
    checks = []
    
    # Python version
    pv = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    checks.append(("Python", pv, True))
    
    # Status Antigravity lengkap via get_auth_status()
    from agent import get_auth_status
    auth = get_auth_status()
    
    checks.append((
        "Antigravity SDK",
        "Terinstall ✓" if auth["sdk_installed"] else "Tidak terinstall → pip install google-antigravity",
        auth["sdk_installed"]
    ))
    checks.append((
        "agy CLI login",
        "Terautentikasi ✓ (Full Mode aktif!)" if auth["agy_authenticated"] else "Belum login → jalankan: agy",
        auth["agy_authenticated"]
    ))
    checks.append((
        "google-generativeai",
        "Terinstall ✓" if auth["genai_installed"] else "Tidak terinstall → pip install google-generativeai",
        auth["genai_installed"]
    ))
    checks.append((
        "API Key (fallback)",
        f"Tersedia ({auth['api_key'][:8]}...)" if auth["api_key"] else "Tidak ditemukan → actl config",
        bool(auth["api_key"])
    ))
    
    # Mode aktif
    if auth["full_mode"]:
        mode_str = "⚡ ANTIGRAVITY FULL (via agy)"
        mode_ok  = True
    elif auth["fallback_mode"]:
        mode_str = "⭗ GEMINI FALLBACK (via API key)"
        mode_ok  = True
    else:
        mode_str = "✗ TIDAK ADA KONEKSI AI"
        mode_ok  = False
    checks.append(("Mode aktif", mode_str, mode_ok))

    
    # Docker
    import subprocess
    docker_result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True, text=True, timeout=5
    )
    if docker_result.returncode == 0:
        checks.append(("Docker", f"v{docker_result.stdout.strip()} ✓", True))
    else:
        checks.append(("Docker", "Tidak tersedia", False))
    
    # Node.js
    node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=5)
    if node_result.returncode == 0:
        checks.append(("Node.js", node_result.stdout.strip() + " ✓", True))
    else:
        checks.append(("Node.js", "Tidak terinstall", False))
    
    # npm
    npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=5)
    if npm_result.returncode == 0:
        checks.append(("npm", f"v{npm_result.stdout.strip()} ✓", True))
    else:
        checks.append(("npm", "Tidak terinstall", False))
    
    # Running servers
    try:
        from dev_server import get_running_servers
        servers = get_running_servers()
        checks.append(("Server aktif", str(len(servers)), len(servers) >= 0))
    except Exception:
        pass
    
    print()
    for label, value, ok in checks:
        icon = colorize("  ✓", C.BRIGHT_GREEN, C.BOLD) if ok else colorize("  ✗", C.BRIGHT_RED, C.BOLD)
        label_str = colorize(f"{label:<25}", C.BRIGHT_WHITE)
        value_str = (colorize(value, C.BRIGHT_GREEN) if ok else colorize(value, C.BRIGHT_RED))
        print(f"{icon} {label_str} {value_str}")
    print()


# ============================================================
# MAIN INTERACTIVE MENU
# ============================================================

def main_menu():
    """Tampilkan menu utama interaktif."""
    print_banner()
    
    while True:
        choice = menu(
            "Pilih fitur:",
            [
                "💬  Chat dengan Antigravity AI",
                "🏗️   Buat project baru",
                "🚀  Dev server manager",
                "🐳  Docker manager",
                "❓  Tanya AI sesuatu",
                "📊  Status sistem",
                "⚙️   Konfigurasi",
                "🚪  Keluar",
            ],
            color=C.BRIGHT_CYAN
        )
        
        if choice == -1 or choice == 7:
            info("Sampai jumpa! 👋")
            break
        elif choice == 0:
            from agent import start_chat
            start_chat()
            print_banner()
        elif choice == 1:
            from scaffold import run_scaffold
            run_scaffold()
        elif choice == 2:
            from dev_server import run_serve_manager
            run_serve_manager()
        elif choice == 3:
            from docker_mgr import run_docker_manager
            run_docker_manager()
        elif choice == 4:
            q = prompt("Pertanyaan untuk AI")
            if q:
                class FakeArgs:
                    question = [q]
                cmd_ask(FakeArgs())
        elif choice == 5:
            cmd_status(None)
        elif choice == 6:
            cmd_config(None)


# ============================================================
# CLI ARGUMENT PARSER
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="actl",
        description=(
            f"{APP_NAME} v{APP_VERSION}\n"
            "Full developer workflow dari HP Android via Termux + Antigravity AI"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Contoh penggunaan:\n"
            "  actl                    — Buka menu utama interaktif\n"
            "  actl chat               — Mulai sesi chat AI\n"
            "  actl new                — Buat project baru\n"
            "  actl serve              — Kelola dev server\n"
            "  actl serve --stop nama  — Hentikan server\n"
            "  actl docker             — Kelola Docker container\n"
            "  actl ask 'pertanyaan'   — Tanya AI langsung\n"
            "  actl status             — Cek status sistem\n"
            "  actl config             — Ubah konfigurasi\n"
        )
    )
    
    parser.add_argument("--version", "-v", action="version", version=f"%(prog)s {APP_VERSION}")
    
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    
    # chat
    subparsers.add_parser("chat", help="Mulai sesi chat interaktif dengan Antigravity AI")
    
    # new
    subparsers.add_parser("new", help="Buat project baru dengan template & AI assistance")
    
    # serve
    serve_p = subparsers.add_parser("serve", help="Kelola dev server (jalankan, hentikan, monitor)")
    serve_p.add_argument("--stop", metavar="NAMA", help="Hentikan server dengan nama tertentu")
    
    # docker
    subparsers.add_parser("docker", help="Kelola Docker container di Termux")
    
    # ask
    ask_p = subparsers.add_parser("ask", help="Tanya AI satu pertanyaan tanpa membuka sesi chat")
    ask_p.add_argument("question", nargs="*", help="Pertanyaan untuk AI")
    
    # status
    subparsers.add_parser("status", help="Tampilkan status sistem dan dependensi")
    
    # config
    subparsers.add_parser("config", help="Konfigurasi aplikasi (API key, model, dll)")
    
    return parser


# ============================================================
# CLI ENTRY POINT
# ============================================================

def cli():
    """Main entry point yang dipanggil dari file `actl`."""
    # ── FIRST RUN: Jalankan setup wizard jika belum pernah setup ──
    from setup import is_first_run, run_setup_wizard
    if is_first_run():
        run_setup_wizard()
    
    # Load config (API key, model, dll)
    _load_config()
    
    parser = build_parser()
    args   = parser.parse_args()
    
    COMMAND_MAP = {
        "chat":   cmd_chat,
        "new":    cmd_new,
        "serve":  cmd_serve,
        "docker": cmd_docker,
        "ask":    cmd_ask,
        "status": cmd_status,
        "config": cmd_config,
    }
    
    if args.command and args.command in COMMAND_MAP:
        COMMAND_MAP[args.command](args)
    else:
        # Tidak ada subcommand → tampilkan menu utama
        main_menu()


def _load_config():
    """Muat konfigurasi dari file settings.json."""
    import json
    from pathlib import Path
    
    config_path = Path(_SRC_DIR).parent / "config" / "settings.json"
    if not config_path.exists():
        return
    
    try:
        config = json.loads(config_path.read_text())
        
        # Set API key ke env jika belum ada
        if config.get("gemini_api_key") and not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = config["gemini_api_key"]
    except Exception:
        pass


if __name__ == "__main__":
    cli()
