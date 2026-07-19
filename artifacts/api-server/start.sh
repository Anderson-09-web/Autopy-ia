#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${HOME}/workspace/.venv"
PYTHON="${VENV}/bin/python3"

# Create the virtualenv on first run (Nix Python is immutable, must use venv)
if [ ! -f "$PYTHON" ]; then
    echo "Creating Python virtual environment..."
    uv venv "$VENV" --python python3.11
fi

cd "$SCRIPT_DIR"
echo "Installing Python dependencies..."
uv pip install --python "$PYTHON" -r requirements.txt -q 2>&1 | grep -v "already satisfied" || true
echo "Starting Autopy AI API server on port ${PORT:-8080}..."
exec "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --reload --log-level info
