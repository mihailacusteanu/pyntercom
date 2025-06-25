#!/bin/zsh

ROOT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
SRC="$ROOT_DIR/src"

DEVICE=$(ls /dev/cu.usbserial-* 2>/dev/null | head -n 1)

if [ -z "$DEVICE" ]; then
    echo "❌ No device found. Please connect your microcontroller."
    exit 1
fi

echo "📡 Device found: $DEVICE"

# Clean cache files
./clean.sh

echo "🚀 Deploying project to device..."

mpremote connect "$DEVICE" fs cp "$ROOT_DIR/main.py" :main.py
mpremote connect "$DEVICE" fs cp -r "$SRC" :

echo "▶️ Running main.py..."
mpremote connect "$DEVICE" exec "import main"