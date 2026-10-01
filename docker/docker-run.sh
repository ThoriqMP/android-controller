#!/usr/bin/env bash
# docker-run.sh — Jalankan Android Controller di Docker
# =====================================================
# Cara pakai:
#   bash docker/docker-run.sh
#   GEMINI_API_KEY=xxx bash docker/docker-run.sh
# =====================================================

set -e

IMAGE_NAME="android-controller"
CONTAINER_NAME="actl-dev"
PROJECTS_DIR="$HOME/projects"

# Buat folder projects jika belum ada
mkdir -p "$PROJECTS_DIR"

echo ""
echo "  🐳 Android Controller Docker Launcher"
echo "  ─────────────────────────────────────"
echo ""

# Build image jika belum ada
if ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "  📦 Membangun Docker image..."
    docker build -t "$IMAGE_NAME" -f "$(dirname "$0")/Dockerfile" "$(dirname "$0")/.."
    echo "  ✓ Image siap"
fi

# Hapus container lama jika ada
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

echo "  🚀 Menjalankan container..."
echo ""

# Jalankan container interaktif
docker run -it --rm \
    --name "$CONTAINER_NAME" \
    -e GEMINI_API_KEY="${GEMINI_API_KEY:-}" \
    -e GOOGLE_API_KEY="${GOOGLE_API_KEY:-}" \
    -v "$PROJECTS_DIR:/root/projects" \
    -v "$(dirname "$0")/../config:/app/config" \
    -p 3000:3000 \
    -p 5000:5000 \
    -p 5173:5173 \
    -p 8000:8000 \
    -p 8080:8080 \
    "$IMAGE_NAME" \
    python3 /app/src/main.py
