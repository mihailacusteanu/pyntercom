#!/bin/zsh

# Get the directory where the script is located
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
# Get the parent directory (project root)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC="$ROOT_DIR/src"

echo "🧹 Cleaning __pycache__ and .pyc files..."
find "$SRC" -name '__pycache__' -type d -exec rm -rf {} +
find "$SRC" -name '*.pyc' -delete
