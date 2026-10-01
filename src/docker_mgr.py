"""
docker_mgr.py - Docker Management untuk Termux
Kelola Docker container langsung dari CLI
"""

import subprocess
import json
from typing import Optional

from ui.tui import (
    menu, prompt, confirm, success, error, info, warn,
    Spinner, section_header, print_box, divider
)
from ui.colors import C, colorize


# ============================================================
# DOCKER HELPERS
# ============================================================

def _run_docker(args: list[str], capture: bool = True) -> tuple[int, str, str]:
    """Jalankan perintah docker dan kembalikan (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["docker"] + args,
            capture_output=capture,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return -1, "", "Docker tidak ditemukan. Install dulu: pkg install docker"
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout: Docker tidak merespons"
    except Exception as e:
        return -1, "", str(e)


def is_docker_available() -> bool:
    """Cek apakah Docker tersedia di sistem."""
    code, _, _ = _run_docker(["version", "--format", "{{.Server.Version}}"])
    return code == 0


def list_containers(all_containers: bool = True) -> list[dict]:
    """Dapatkan daftar container sebagai list dict."""
    fmt = '{"id":"{{.ID}}","name":"{{.Names}}","image":"{{.Image}}","status":"{{.Status}}","ports":"{{.Ports}}"}'
    args = ["ps", "--format", fmt]
    if all_containers:
        args.append("-a")
    
    code, out, err = _run_docker(args)
    if code != 0:
        return []
    
    containers = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            try:
                containers.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return containers


def list_images() -> list[dict]:
    """Dapatkan daftar image sebagai list dict."""
    fmt = '{"id":"{{.ID}}","repo":"{{.Repository}}","tag":"{{.Tag}}","size":"{{.Size}}","created":"{{.CreatedSince}}"}'
    code, out, err = _run_docker(["images", "--format", fmt])
    if code != 0:
        return []
    
    images = []
    for line in out.splitlines():
        line = line.strip()
        if line:
            try:
                images.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return images


# ============================================================
# CONTAINER DISPLAY
# ============================================================

def _status_color(status: str) -> str:
    s = status.lower()
    if "up" in s or "running" in s:
        return C.BRIGHT_GREEN
    elif "exited" in s:
        return C.BRIGHT_RED
    elif "paused" in s:
        return C.BRIGHT_YELLOW
    return C.BRIGHT_BLACK


def display_containers(containers: list[dict]):
    """Tampilkan daftar container dalam tabel."""
    if not containers:
        warn("Tidak ada container ditemukan.")
        return
    
    print()
    header = (
        colorize(f"  {'NAME':<25}", C.BOLD, C.BRIGHT_WHITE) +
        colorize(f"{'IMAGE':<30}", C.BOLD, C.BRIGHT_WHITE) +
        colorize(f"{'STATUS':<20}", C.BOLD, C.BRIGHT_WHITE) +
        colorize("PORTS", C.BOLD, C.BRIGHT_WHITE)
    )
    print(header)
    divider()
    
    for c in containers:
        sc = _status_color(c["status"])
        name   = c["name"][:24].ljust(25)
        image  = c["image"][:29].ljust(30)
        status = colorize(c["status"][:19].ljust(20), sc)
        ports  = c["ports"][:30] if c["ports"] else "-"
        print(f"  {name}{image}{status}{ports}")


# ============================================================
# CONTAINER ACTIONS
# ============================================================

def start_container(container_id: str) -> bool:
    code, _, err = _run_docker(["start", container_id])
    if code == 0:
        success(f"Container {container_id} dimulai.")
        return True
    error(f"Gagal memulai container: {err}")
    return False


def stop_container(container_id: str) -> bool:
    code, _, err = _run_docker(["stop", container_id])
    if code == 0:
        success(f"Container {container_id} dihentikan.")
        return True
    error(f"Gagal menghentikan container: {err}")
    return False


def remove_container(container_id: str, force: bool = False) -> bool:
    args = ["rm"]
    if force:
        args.append("-f")
    args.append(container_id)
    code, _, err = _run_docker(args)
    if code == 0:
        success(f"Container {container_id} dihapus.")
        return True
    error(f"Gagal menghapus container: {err}")
    return False


def exec_in_container(container_id: str, cmd: str):
    """Jalankan perintah di dalam container (interactive)."""
    import shlex
    parts = shlex.split(cmd)
    subprocess.run(["docker", "exec", "-it", container_id] + parts)


def run_new_container(image: str, name: str, ports: str = None, volume: str = None):
    """Jalankan container baru dari image."""
    args = ["run", "-d", "--name", name]
    if ports:
        for p in ports.split(","):
            args += ["-p", p.strip()]
    if volume:
        args += ["-v", volume]
    args.append(image)
    
    code, out, err = _run_docker(args)
    if code == 0:
        success(f"Container '{name}' berjalan. ID: {out[:12]}")
    else:
        error(f"Gagal menjalankan container: {err}")


def show_logs(container_id: str, tail: int = 50):
    """Tampilkan log container."""
    subprocess.run(["docker", "logs", "--tail", str(tail), "-f", container_id])


# ============================================================
# INTERACTIVE DOCKER MENU
# ============================================================

def run_docker_manager():
    """Entry point interaktif untuk `actl docker`."""
    section_header("🐳 DOCKER MANAGER", C.BRIGHT_BLUE)
    
    if not is_docker_available():
        error("Docker tidak tersedia!")
        warn("Di Termux, install dengan:")
        info("  pkg install root-repo")
        info("  pkg install docker")
        info("  dockerd &  (jalankan daemon dulu)")
        return
    
    success("Docker tersedia!")
    
    while True:
        choice = menu(
            "Pilih aksi Docker:",
            [
                "Lihat semua container",
                "Lihat semua image",
                "Mulai container",
                "Hentikan container",
                "Hapus container",
                "Lihat log container",
                "Jalankan perintah di container",
                "Jalankan container baru",
                "Kembali ke menu utama",
            ],
            color=C.BRIGHT_BLUE
        )
        
        if choice == -1 or choice == 8:
            break
        
        elif choice == 0:  # Lihat container
            with Spinner("Mengambil daftar container..."):
                containers = list_containers()
            display_containers(containers)
        
        elif choice == 1:  # Lihat image
            with Spinner("Mengambil daftar image..."):
                images = list_images()
            if images:
                print()
                header = (
                    colorize(f"  {'REPOSITORY':<35}", C.BOLD, C.BRIGHT_WHITE) +
                    colorize(f"{'TAG':<15}", C.BOLD, C.BRIGHT_WHITE) +
                    colorize(f"{'SIZE':<12}", C.BOLD, C.BRIGHT_WHITE) +
                    colorize("CREATED", C.BOLD, C.BRIGHT_WHITE)
                )
                print(header)
                divider()
                for img in images:
                    print(f"  {img['repo'][:34]:<35}{img['tag'][:14]:<15}{img['size'][:11]:<12}{img['created']}")
            else:
                warn("Tidak ada image ditemukan.")
        
        elif choice in (2, 3, 4, 5, 6):  # Aksi container
            container_id = prompt("Masukkan nama/ID container")
            if not container_id:
                continue
            
            if choice == 2:
                start_container(container_id)
            elif choice == 3:
                stop_container(container_id)
            elif choice == 4:
                if confirm(f"Hapus container '{container_id}'?", default=False):
                    force = confirm("Force remove (paksa hapus meski sedang berjalan)?", default=False)
                    remove_container(container_id, force)
            elif choice == 5:
                tail = prompt("Berapa baris log terakhir?", default="50")
                show_logs(container_id, int(tail) if tail.isdigit() else 50)
            elif choice == 6:
                cmd = prompt("Perintah yang dijalankan", default="bash")
                exec_in_container(container_id, cmd)
        
        elif choice == 7:  # Jalankan container baru
            image = prompt("Nama image", default="ubuntu:22.04")
            name  = prompt("Nama container", default="my-container")
            ports = prompt("Port mapping (contoh: 8080:80,443:443)", default="")
            vol   = prompt("Volume mount (contoh: /data:/app/data)", default="")
            run_new_container(image, name, ports or None, vol or None)
