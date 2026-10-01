"""
dev_server.py - Dev Server Launcher
Jalankan, monitor, dan kelola dev server dari HP via Termux
"""

import subprocess
import os
import json
import time
import signal
from pathlib import Path
from typing import Optional

from ui.tui import (
    menu, prompt, confirm, success, error, info, warn,
    Spinner, section_header, print_box, divider, step
)
from ui.colors import C, colorize


# ============================================================
# SERVER PRESETS
# ============================================================

SERVER_PRESETS = {
    "python-http": {
        "label": "Python HTTP Server (built-in)",
        "cmd": "python3 -m http.server {port}",
        "default_port": 8080,
    },
    "uvicorn": {
        "label": "Uvicorn (FastAPI/ASGI)",
        "cmd": "uvicorn main:app --host 0.0.0.0 --port {port} --reload",
        "default_port": 8000,
    },
    "flask": {
        "label": "Flask Dev Server",
        "cmd": "python3 -m flask run --host 0.0.0.0 --port {port}",
        "default_port": 5000,
    },
    "node": {
        "label": "Node.js (npm start)",
        "cmd": "npm start",
        "default_port": 3000,
        "env": {"PORT": "{port}"},
    },
    "vite": {
        "label": "Vite Dev Server (React/Vue)",
        "cmd": "npm run dev -- --host 0.0.0.0 --port {port}",
        "default_port": 5173,
    },
    "nextjs": {
        "label": "Next.js Dev Server",
        "cmd": "npm run dev -- -p {port}",
        "default_port": 3000,
    },
    "custom": {
        "label": "Custom command",
        "cmd": None,
        "default_port": 8080,
    },
}


# ============================================================
# RUNNING SERVER TRACKER
# ============================================================

_PIDS_FILE = Path.home() / ".actl_servers.json"


def _load_pids() -> dict:
    if _PIDS_FILE.exists():
        try:
            return json.loads(_PIDS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_pids(pids: dict):
    _PIDS_FILE.write_text(json.dumps(pids, indent=2))


def _is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def get_running_servers() -> dict:
    """Dapatkan daftar server yang sedang berjalan."""
    pids = _load_pids()
    active = {}
    for name, info_dict in pids.items():
        pid = info_dict.get("pid")
        if pid and _is_running(pid):
            active[name] = info_dict
    
    # Update file jika ada yang mati
    if len(active) != len(pids):
        _save_pids(active)
    
    return active


def stop_server(name: str) -> bool:
    """Hentikan server berdasarkan nama."""
    pids = _load_pids()
    if name not in pids:
        warn(f"Server '{name}' tidak ditemukan.")
        return False
    
    pid = pids[name].get("pid")
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            if _is_running(pid):
                os.kill(pid, signal.SIGKILL)
            success(f"Server '{name}' dihentikan (PID {pid}).")
        except ProcessLookupError:
            warn(f"Proses sudah tidak ada (PID {pid}).")
        except Exception as e:
            error(f"Gagal menghentikan: {e}")
            return False
    
    del pids[name]
    _save_pids(pids)
    return True


# ============================================================
# AUTO-DETECT SERVER TYPE
# ============================================================

def detect_server_type(project_dir: Path) -> Optional[str]:
    """Deteksi tipe server berdasarkan file di project."""
    checks = [
        (project_dir / "package.json", _detect_npm_type),
        (project_dir / "main.py",      _detect_python_type),
        (project_dir / "app.py",       lambda d: "flask"),
    ]
    
    for path, detector in checks:
        if path.exists():
            result = detector(project_dir)
            if result:
                return result
    return None


def _detect_npm_type(project_dir: Path) -> Optional[str]:
    pkg = project_dir / "package.json"
    try:
        data = json.loads(pkg.read_text())
        scripts = data.get("scripts", {})
        deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        
        if "next" in deps:
            return "nextjs"
        if "vite" in deps:
            return "vite"
        if "dev" in scripts or "start" in scripts:
            return "node"
    except Exception:
        pass
    return None


def _detect_python_type(project_dir: Path) -> Optional[str]:
    req = project_dir / "requirements.txt"
    if req.exists():
        content = req.read_text().lower()
        if "fastapi" in content or "uvicorn" in content:
            return "uvicorn"
        if "flask" in content:
            return "flask"
    main_py = project_dir / "main.py"
    if main_py.exists():
        content = main_py.read_text().lower()
        if "fastapi" in content:
            return "uvicorn"
        if "flask" in content:
            return "flask"
    return "python-http"


# ============================================================
# LAUNCH SERVER
# ============================================================

def launch_server(
    preset_key: str,
    project_dir: str,
    port: int,
    name: str,
    custom_cmd: str = None,
    foreground: bool = False
):
    """Luncurkan dev server."""
    preset = SERVER_PRESETS.get(preset_key, SERVER_PRESETS["custom"])
    cwd = Path(project_dir).expanduser().resolve()
    
    if not cwd.exists():
        error(f"Direktori tidak ditemukan: {cwd}")
        return
    
    # Build command
    if preset_key == "custom" or custom_cmd:
        cmd_str = custom_cmd or prompt("Masukkan perintah server")
        if not cmd_str:
            return
    else:
        cmd_str = preset["cmd"].format(port=port)
    
    # Env vars
    env = os.environ.copy()
    if preset.get("env"):
        for k, v in preset["env"].items():
            env[k] = v.format(port=port)
    
    print()
    print_box(
        "🚀 Menjalankan Server",
        f"Nama    : {name}\n"
        f"Command : {cmd_str}\n"
        f"Folder  : {cwd}\n"
        f"Port    : {port}\n"
        f"URL     : http://localhost:{port}",
        color=C.BRIGHT_GREEN
    )
    print()
    
    if foreground:
        info("Menjalankan di foreground (Ctrl+C untuk berhenti)...")
        info(f"URL: http://localhost:{port}")
        print()
        try:
            subprocess.run(cmd_str, shell=True, cwd=cwd, env=env)
        except KeyboardInterrupt:
            info("Server dihentikan.")
    else:
        info("Menjalankan di background...")
        proc = subprocess.Popen(
            cmd_str,
            shell=True,
            cwd=cwd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Simpan PID
        pids = _load_pids()
        pids[name] = {
            "pid": proc.pid,
            "port": port,
            "cmd": cmd_str,
            "dir": str(cwd),
            "type": preset_key,
        }
        _save_pids(pids)
        
        time.sleep(1.5)
        if _is_running(proc.pid):
            success(f"Server '{name}' berjalan! PID: {proc.pid}")
            info(f"URL: http://localhost:{port}")
            info(f"Hentikan dengan: actl serve --stop {name}")
        else:
            error("Server gagal dijalankan. Coba jalankan di foreground untuk melihat error.")


# ============================================================
# INTERACTIVE DEV SERVER MENU
# ============================================================

def run_serve_manager():
    """Entry point interaktif untuk `actl serve`."""
    section_header("🚀 DEV SERVER MANAGER", C.BRIGHT_GREEN)
    
    while True:
        # Tampilkan server aktif
        active = get_running_servers()
        if active:
            print()
            info(f"{len(active)} server aktif:")
            for name, srv in active.items():
                pid_badge  = colorize(f"PID:{srv['pid']}", C.DIM, C.BRIGHT_BLACK)
                port_badge = colorize(f":{srv['port']}", C.BRIGHT_CYAN)
                print(f"    {colorize('●', C.BRIGHT_GREEN)} {name} {port_badge} {pid_badge}")
        else:
            info("Belum ada server aktif.")
        
        choice = menu(
            "Pilih aksi:",
            [
                "Jalankan server baru",
                "Hentikan server",
                "Lihat server aktif",
                "Kembali ke menu utama",
            ],
            color=C.BRIGHT_GREEN
        )
        
        if choice == -1 or choice == 3:
            break
        
        elif choice == 0:  # Jalankan server baru
            preset_keys  = list(SERVER_PRESETS.keys())
            preset_labels = [SERVER_PRESETS[k]["label"] for k in preset_keys]
            
            p_choice = menu("Pilih tipe server:", preset_labels, C.BRIGHT_GREEN)
            if p_choice == -1:
                continue
            
            preset_key = preset_keys[p_choice]
            default_port = SERVER_PRESETS[preset_key]["default_port"]
            
            project_dir = prompt("Folder project", default=".")
            
            # Auto-detect
            detected = detect_server_type(Path(project_dir))
            if detected and detected != preset_key:
                if confirm(f"Terdeteksi tipe '{detected}'. Gunakan ini?"):
                    preset_key = detected
            
            port_str = prompt("Port", default=str(default_port))
            port = int(port_str) if port_str.isdigit() else default_port
            
            name = prompt("Nama server (untuk identifikasi)", default=f"server-{port}")
            
            mode = menu("Mode jalankan:", ["Background (lanjutkan pakai terminal)", "Foreground (tahan terminal)"])
            
            launch_server(
                preset_key=preset_key,
                project_dir=project_dir,
                port=port,
                name=name,
                foreground=(mode == 1)
            )
        
        elif choice == 1:  # Hentikan server
            if not active:
                warn("Tidak ada server aktif untuk dihentikan.")
                continue
            
            names = list(active.keys())
            s_choice = menu("Pilih server yang dihentikan:", names, C.BRIGHT_RED)
            if s_choice != -1:
                stop_server(names[s_choice])
        
        elif choice == 2:  # Lihat server aktif
            if active:
                print()
                for name, srv in active.items():
                    print_box(
                        f"● {name}",
                        f"PID     : {srv['pid']}\n"
                        f"Port    : {srv['port']}\n"
                        f"Command : {srv['cmd']}\n"
                        f"Folder  : {srv['dir']}",
                        color=C.BRIGHT_GREEN
                    )
            else:
                warn("Tidak ada server aktif.")
