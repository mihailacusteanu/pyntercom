#!/bin/zsh

DEVICE=$(ls /dev/cu.usbserial-* 2>/dev/null | head -n 1)

if [ -z "$DEVICE" ]; then
    echo "❌ No ESP8266 device found. Please connect your microcontroller."
    echo "💡 Make sure the ESP8266 is connected via USB and drivers are installed."
    exit 1
fi

echo "📡 ESP8266 device found: $DEVICE"
echo "🔌 Connecting to REPL..."
echo "💡 Use `Ctrl` + `]` to exit REPL"
echo ""

mpremote connect "$DEVICE" repl