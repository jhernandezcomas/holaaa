#!/usr/bin/env bash
set -e

echo "=== Zoom Interview Assistant - Setup ==="

# System deps (Linux)
if command -v apt-get &>/dev/null; then
  echo "[1/3] Instalando dependencias del sistema..."
  sudo apt-get install -y portaudio19-dev libsndfile1-dev
fi

# Python deps
echo "[2/3] Instalando dependencias de Python..."
pip install -r requirements.txt

# .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[3/3] Creado .env — EDITA el archivo y añade tu ANTHROPIC_API_KEY"
else
  echo "[3/3] .env ya existe."
fi

echo ""
echo "Siguiente paso: edita profile.md con tu información profesional"
echo "Luego ejecuta: python main.py"
