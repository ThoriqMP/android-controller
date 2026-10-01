# Android Controller — Termux Docker Image
# Base: Ubuntu minimal (ringan untuk HP)
# ==========================================

FROM ubuntu:22.04

LABEL maintainer="Android Controller"
LABEL description="Termux-compatible development environment with Antigravity AI"

# ── ENVIRONMENT ────────────────────────────────────────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ── SYSTEM DEPENDENCIES ────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    nano \
    vim \
    htop \
    tree \
    unzip \
    zip \
    build-essential \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip3 install --upgrade pip

# ── PYTHON DEPENDENCIES ────────────────────────────────────────
RUN pip3 install \
    google-generativeai \
    fastapi \
    uvicorn[standard] \
    flask \
    requests \
    httpx \
    python-dotenv \
    rich \
    typer

# Coba install Antigravity SDK (opsional)
RUN pip3 install google-antigravity || echo "google-antigravity tidak tersedia, skip"

# ── NPM GLOBAL TOOLS ───────────────────────────────────────────
RUN npm install -g \
    nodemon \
    pm2 \
    serve \
    create-react-app

# ── SETUP APP ─────────────────────────────────────────────────
WORKDIR /app
COPY . /app/

RUN chmod +x /app/actl
RUN ln -s /app/actl /usr/local/bin/actl

# Buat direktori projects
RUN mkdir -p /root/projects

# ── CONFIG DIREKTORI ───────────────────────────────────────────
RUN mkdir -p /app/config
RUN if [ ! -f /app/config/settings.json ]; then \
    echo '{"gemini_api_key":"","default_model":"gemini-2.0-flash","default_projects_dir":"~/projects","theme":"dark","language":"id"}' \
    > /app/config/settings.json; \
    fi

# ── ENVIRONMENT VARIABLES ──────────────────────────────────────
# Isi API key saat run dengan: -e GEMINI_API_KEY=your_key
ENV GEMINI_API_KEY=""
ENV GOOGLE_API_KEY=""

# ── EXPOSE PORTS ───────────────────────────────────────────────
# Port umum untuk dev server
EXPOSE 3000 5000 5173 8000 8080

# ── ENTRYPOINT ────────────────────────────────────────────────
CMD ["python3", "/app/src/main.py"]
