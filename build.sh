#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root: sudo ./build.sh"
    exit 1
fi

VERSION=$(grep -oP "Libux v\K[0-9]+\.[0-9]+\.[0-9]+" main.py | head -1)

if [ -z "$VERSION" ]; then
    echo "Could not detect version from main.py."
    exit 1
fi

BINARY_NAME="libuxv${VERSION}"

echo "Building $BINARY_NAME..."

if ! venv/bin/python -c "import PyInstaller" 2>/dev/null; then
    venv/bin/pip install pyinstaller -q || { echo "Failed to install PyInstaller."; exit 1; }
fi

venv/bin/pyinstaller --onefile --name "$BINARY_NAME" main.py || { echo "Build failed."; exit 1; }

mv "dist/$BINARY_NAME" "./$BINARY_NAME"
rm -rf dist build __pycache__ "${BINARY_NAME}.spec"

echo "Done: ./$BINARY_NAME"
