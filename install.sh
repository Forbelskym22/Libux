#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

echo "Installing dependencies..."
apt install -y python3-venv python3-pip || { echo "apt install failed."; exit 1; }

echo "Creating virtual environment..."
python3 -m venv venv || { echo "Failed to create venv."; exit 1; }

echo "Installing Python packages..."
venv/bin/pip install -r requirements.txt || { echo "pip install failed."; exit 1; }

echo "Installation complete. Run with: sudo ./start.sh"
