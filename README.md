# 📱 Android Controller — Termux × Antigravity AI

> Full developer workflow dari HP Android via Termux + Docker, terintegrasi dengan Antigravity AI agent.

---

## ✨ Fitur

- 🤖 **Chat interaktif** dengan Antigravity AI agent langsung dari terminal
- 🏗️ **Scaffold project** otomatis (pilih bahasa & framework dari menu)
- 🚀 **Dev server launcher** — jalankan & monitor proyek dari HP
- 📦 **Docker manager** — kelola container Termux-Docker dengan mudah
- 🎨 **TUI (Terminal UI)** yang indah dengan warna dan animasi

---

## 🛠️ Persyaratan

- Android dengan [Termux](https://termux.dev) terinstall
- Docker di dalam Termux (via `pkg install root-repo && pkg install docker`)
- Python 3.10+
- Koneksi internet (untuk Antigravity API)

---

## 🚀 Instalasi Cepat

```bash
# Di Termux, jalankan:
bash install.sh
```

---

## 📁 Struktur Project

```
android-controller/
├── install.sh          # Script instalasi otomatis
├── actl                # Entry point CLI utama (executable)
├── src/
│   ├── main.py         # Core CLI application
│   ├── agent.py        # Integrasi Antigravity SDK
│   ├── scaffold.py     # Project scaffolding engine
│   ├── docker_mgr.py   # Docker management
│   ├── dev_server.py   # Dev server launcher
│   └── ui/
│       ├── tui.py      # Terminal UI components
│       └── colors.py   # Color & styling definitions
├── templates/          # Project templates
│   ├── python/
│   ├── nodejs/
│   ├── react/
│   └── fastapi/
├── config/
│   └── settings.json   # Konfigurasi aplikasi
└── docker/
    └── Dockerfile      # Docker image untuk Termux
```

---

## 📖 Penggunaan

```bash
# Mulai chat dengan AI agent
actl chat

# Buat project baru (interactive)
actl new

# Jalankan dev server
actl serve

# Kelola Docker container
actl docker

# Lihat semua perintah
actl --help
```
