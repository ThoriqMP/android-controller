#!/usr/bin/env bash
# ==============================================================
# install.sh — Android Controller Installer untuk Termux
# ==============================================================
# Penggunaan: bash install.sh
# ==============================================================

set -e

# ── WARNA ──────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}  ✓ ${RESET}$*"; }
err()  { echo -e "${RED}  ✗ ${RESET}$*"; }
info() { echo -e "${CYAN}  ℹ ${RESET}$*"; }
warn() { echo -e "${YELLOW}  ⚠ ${RESET}$*"; }
step() { echo -e "\n${BOLD}${MAGENTA}  [$1/$2]${RESET} $3"; }

# ── BANNER ─────────────────────────────────────────────────────
echo -e ""
echo -e "${BOLD}${CYAN}  ┌──────────────────────────────────────────┐${RESET}"
echo -e "${BOLD}${CYAN}  │  Android Controller × Antigravity AI     │${RESET}"
echo -e "${BOLD}${CYAN}  │  Installer v1.0.0                        │${RESET}"
echo -e "${BOLD}${CYAN}  └──────────────────────────────────────────┘${RESET}"
echo ""

# ── DETEKSI LINGKUNGAN ─────────────────────────────────────────
IS_TERMUX=false
IS_DOCKER=false

if [ -d "/data/data/com.termux" ] || [ -n "$TERMUX_VERSION" ]; then
    IS_TERMUX=true
    info "Terdeteksi: Termux di Android"
elif [ -f "/.dockerenv" ]; then
    IS_DOCKER=true
    info "Terdeteksi: Docker container"
else
    info "Terdeteksi: Linux/macOS biasa"
fi

TOTAL_STEPS=6
CURRENT_STEP=0

# ── STEP 1: Update packages ────────────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Update package manager..."

if $IS_TERMUX; then
    pkg update -y 2>/dev/null || warn "pkg update gagal, lanjutkan..."
    pkg upgrade -y 2>/dev/null || true
elif command -v apt &>/dev/null; then
    apt-get update -qq 2>/dev/null || true
elif command -v apk &>/dev/null; then
    apk update 2>/dev/null || true
fi
ok "Package manager diperbarui"

# ── STEP 2: Install system dependencies ───────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Install dependensi sistem..."

if $IS_TERMUX; then
    PKGS="python git curl wget"
    for pkg in $PKGS; do
        if ! command -v $pkg &>/dev/null; then
            pkg install -y $pkg 2>/dev/null || warn "Gagal install $pkg"
        fi
    done
    # Node.js opsional
    if ! command -v node &>/dev/null; then
        info "Menginstall Node.js (opsional)..."
        pkg install -y nodejs 2>/dev/null || warn "Node.js tidak terinstall, fitur React/Next.js tidak tersedia"
    fi
else
    # Linux biasa
    if command -v apt-get &>/dev/null; then
        apt-get install -y python3 python3-pip git curl wget 2>/dev/null || true
    elif command -v apk &>/dev/null; then
        apk add python3 py3-pip git curl wget 2>/dev/null || true
    fi
fi
ok "Dependensi sistem siap"

# ── STEP 3: Install Python dependencies ───────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Install Python dependencies..."

# Pastikan pip tersedia
if ! command -v pip3 &>/dev/null && ! command -v pip &>/dev/null; then
    if $IS_TERMUX; then
        pkg install -y python 2>/dev/null
    else
        curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 2>/dev/null || true
    fi
fi

PIP_CMD="pip3"
command -v pip3 &>/dev/null || PIP_CMD="pip"

# Install wajib
info "Menginstall google-generativeai (fallback API)..."
$PIP_CMD install google-generativeai --quiet 2>/dev/null || warn "google-generativeai gagal, coba manual"

# Install Antigravity SDK (opsional, mungkin tidak tersedia di semua platform)
info "Mencoba install google-antigravity SDK..."
if $PIP_CMD install google-antigravity --quiet 2>/dev/null; then
    ok "Antigravity SDK terinstall!"
else
    warn "google-antigravity tidak tersedia. Akan menggunakan Gemini API langsung."
    info "Install manual: pip install google-antigravity"
fi
ok "Python dependencies siap"

# ── STEP 4: Konfigurasi direktori ─────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Setup direktori..."

INSTALL_DIR="$(pwd)"
CONFIG_DIR="$INSTALL_DIR/config"
mkdir -p "$CONFIG_DIR"
mkdir -p "$INSTALL_DIR/templates"
mkdir -p "$HOME/projects"

# Buat settings.json default jika belum ada
if [ ! -f "$CONFIG_DIR/settings.json" ]; then
    cat > "$CONFIG_DIR/settings.json" <<'JSON'
{
  "gemini_api_key": "",
  "default_model": "gemini-2.0-flash",
  "default_projects_dir": "~/projects",
  "theme": "dark",
  "language": "id"
}
JSON
    ok "File konfigurasi dibuat: $CONFIG_DIR/settings.json"
fi
ok "Direktori siap"

# ── STEP 5: Setup executable ───────────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Setup CLI executable..."

chmod +x "$INSTALL_DIR/actl"

# Symlink ke PATH
LINK_TARGET=""
for dir in "$HOME/bin" "$HOME/.local/bin" "/usr/local/bin"; do
    if [ -d "$dir" ] || mkdir -p "$dir" 2>/dev/null; then
        # Cek apakah dir ada di PATH
        if echo ":$PATH:" | grep -q ":$dir:"; then
            LINK_TARGET="$dir"
            break
        fi
    fi
done

if $IS_TERMUX; then
    LINK_TARGET="$PREFIX/bin"
fi

if [ -n "$LINK_TARGET" ]; then
    ln -sf "$INSTALL_DIR/actl" "$LINK_TARGET/actl" 2>/dev/null || true
    ok "Symlink dibuat: $LINK_TARGET/actl"
else
    warn "Tidak bisa buat symlink. Tambahkan ke PATH manual:"
    info "  export PATH=\"\$PATH:$INSTALL_DIR\""
    info "  Tambahkan baris itu ke ~/.bashrc atau ~/.zshrc"
fi
ok "CLI executable siap"

# ── STEP 6: Konfigurasi API Key ───────────────────────────────
CURRENT_STEP=$((CURRENT_STEP + 1))
step $CURRENT_STEP $TOTAL_STEPS "Konfigurasi API Key..."

if [ -n "$GEMINI_API_KEY" ]; then
    ok "GEMINI_API_KEY sudah tersedia di environment"
else
    echo ""
    echo -e "  ${YELLOW}Untuk menggunakan AI agent, kamu butuh Gemini API Key.${RESET}"
    echo -e "  Dapatkan gratis di: ${CYAN}https://aistudio.google.com/app/apikey${RESET}"
    echo ""
    printf "  Masukkan API key (atau tekan Enter untuk skip): "
    read -r API_KEY

    if [ -n "$API_KEY" ]; then
        # Simpan ke settings.json
        if command -v python3 &>/dev/null; then
            python3 - <<PYEOF
import json, os
config_path = "$CONFIG_DIR/settings.json"
with open(config_path) as f:
    config = json.load(f)
config['gemini_api_key'] = "$API_KEY"
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print("  Config tersimpan.")
PYEOF
        fi

        # Tambahkan ke shell profile
        SHELL_PROFILE="$HOME/.bashrc"
        [ -f "$HOME/.zshrc" ] && SHELL_PROFILE="$HOME/.zshrc"

        if ! grep -q "GEMINI_API_KEY" "$SHELL_PROFILE" 2>/dev/null; then
            echo "" >> "$SHELL_PROFILE"
            echo "# Android Controller - Antigravity AI" >> "$SHELL_PROFILE"
            echo "export GEMINI_API_KEY=\"$API_KEY\"" >> "$SHELL_PROFILE"
        fi
        ok "API Key tersimpan di $SHELL_PROFILE dan settings.json"
    else
        warn "API Key dilewati. Atur nanti dengan: actl config"
    fi
fi

# ── SELESAI ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}  ╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${GREEN}  ║  ✓ Instalasi Selesai!                   ║${RESET}"
echo -e "${BOLD}${GREEN}  ╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}Cara menggunakan:${RESET}"
echo -e "  ${CYAN}actl${RESET}                — Buka menu utama"
echo -e "  ${CYAN}actl chat${RESET}           — Chat dengan AI agent"
echo -e "  ${CYAN}actl new${RESET}            — Buat project baru"
echo -e "  ${CYAN}actl serve${RESET}          — Kelola dev server"
echo -e "  ${CYAN}actl docker${RESET}         — Kelola Docker"
echo -e "  ${CYAN}actl ask 'pertanyaan'${RESET} — Tanya AI langsung"
echo -e "  ${CYAN}actl status${RESET}         — Cek status sistem"
echo ""

if $IS_TERMUX; then
    echo -e "  ${YELLOW}Di Termux: reload shell dengan${RESET} ${CYAN}source ~/.bashrc${RESET}"
fi

echo ""
echo -e "  ${BOLD}Jalankan sekarang:${RESET} ${CYAN}actl${RESET}"
echo ""
