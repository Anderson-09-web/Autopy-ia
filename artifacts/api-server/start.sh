#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${HOME}/workspace/.pythonlibs/bin/python3"
PIP="${HOME}/workspace/.pythonlibs/bin/pip3"

cd "$SCRIPT_DIR"
echo "Installing Python dependencies..."
"$PIP" install -r requirements.txt -q --disable-pip-version-check 2>&1 | grep -v "already satisfied" || true
echo "Starting Autopy AI API server on port ${PORT:-8080}..."
exec "$PYTHON" -m uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}" --reload --log-level info
