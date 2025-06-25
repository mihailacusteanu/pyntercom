#!/bin/zsh

# Get the directory where the script is located
SCRIPT_DIR="$(cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P)"
# Get the parent directory (project root)
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC="$ROOT_DIR/src"

DEVICE=$(ls /dev/cu.usbserial-* 2>/dev/null | head -n 1)

if [ -z "$DEVICE" ]; then
    echo "❌ No device found. Please connect your microcontroller."
    exit 1
fi

echo "📡 Device found: $DEVICE"

# Clean cache files
"$SCRIPT_DIR/clean.sh"

echo "🚀 Deploying project to device..."

mpremote connect "$DEVICE" fs cp "$ROOT_DIR/main.py" :main.py
mpremote connect "$DEVICE" fs cp -r "$SRC" :

echo "▶️ Running main.py..."
mpremote connect "$DEVICE" exec "import main"