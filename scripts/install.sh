#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

echo "Updating Raspberry Pi OS packages..."
sudo apt update

echo "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-picamera2

echo "Creating PiPrints virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv --system-site-packages "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
python -m pip install --upgrade pip

echo "Installing PiPrints..."
python -m pip install -e "$PROJECT_ROOT[dev]"

echo "Validating Picamera2..."
python -c "from picamera2 import Picamera2; print('Picamera2 OK')"

echo "PiPrints setup complete."
