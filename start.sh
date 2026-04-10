#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo bash run.sh"
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "venv not found. Run install.sh first."
    exit 1
fi

venv/bin/python main.py
