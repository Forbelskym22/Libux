#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./install.sh"
    exit 1
fi

python3 -m venv venv
venv/bin/pip install -r requirements.txt
echo "Installation complete. Run with: sudo ./start.sh"
