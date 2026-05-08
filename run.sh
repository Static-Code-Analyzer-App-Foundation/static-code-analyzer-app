#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not installed."
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[+] Creating virtual environment..."
  python3 -m venv .venv
fi

echo "[+] Activating virtual environment..."
source .venv/bin/activate

echo "[+] Upgrading pip..."
pip install --upgrade pip >/dev/null

if [ -f requirements.txt ]; then
  echo "[+] Installing dependencies..."
  pip install -r requirements.txt
fi

mkdir -p data uploads extracted reports

if [ ! -f .env ] && [ -f .env.example ]; then
  echo "[+] Creating .env from .env.example..."
  cp .env.example .env
fi

if command -v gunicorn >/dev/null 2>&1; then
  echo "[+] Starting with gunicorn..."
  exec gunicorn -w 2 -b 0.0.0.0:5000 app:app
else
  echo "[+] Starting with Flask dev server..."
  exec python app.py
fi
