#!/bin/zsh

ROOT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
SRC="$ROOT_DIR/src"

echo "🧹 Cleaning __pycache__ and .pyc files..."
find "$SRC" -name '__pycache__' -type d -exec rm -rf {} +
find "$SRC" -name '*.pyc' -delete
