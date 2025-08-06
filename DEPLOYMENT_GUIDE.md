# PyNtercom ESP8266 Intercom System - Complete Guide

## 🚀 Deployment Process

### Prerequisites
```bash
# Required tools
- ESP8266 microcontroller connected via USB
- Conda environment named 'micropython'
- mpremote tool installed
- Serial port: /dev/cu.usbserial-110
```

### Step-by-Step Deployment
```bash
# 1. Activate Python environment
conda activate micropython

# 2. Deploy all code to ESP8266
./scripts/deploy.sh

# 3. Monitor live system output
./scripts/repl.sh
```

## 📡 How to Run & Monitor

### Deployment Script (`./scripts/deploy.sh`)
- Finds ESP8266 device automatically
- Cleans `__pycache__` files
- Copies all source files to device
- Executes `main.py` automatically

### REPL Monitoring (`./scripts/repl.sh`)
- Connects to ESP8266 serial console
- Shows real-time system output
- Use `Ctrl-]` to exit
- Displays WiFi connection, MQTT status, GPIO events

### Manual Commands
```bash
# Kill existing connections if needed
pkill -f "mpremote.*repl"

# Direct mpremote access
mpremote a0 fs ls    # List files on device
mpremote a0 exec -   # Execute commands
```

## 🏗️ System Architecture

### Hardware Configuration
```
ESP8266 GPIO Pins:
├── Pin 14: Call detector (INPUT, pull-up resistor, active-low)
├── Pin 12: Conversation relay (OUTPUT)
└── Pin 13: Door unlock relay (OUTPUT)

Network Setup:
├── WiFi: TP-Link_4FD0
└── MQTT: 192.168.0.172:1883 (client: esp8266_pyntercom)
```

### Software Stack
```
main.py
└── Intercom (src/app/intercom.py)
    └── DriverManager (src/driver/driver_manager.py)
        ├── WiFiDriver: esp8266_wifi_driver.py
        ├── MQTTDriver: esp8266_mqtt_driver.py
        └── GPIODriver: esp8266_gpio_driver.py
```

### Configuration Files
```
src/config/
├── core.py           # GPIO pins, MQTT topics
├── secret_config.py  # WiFi/MQTT credentials
└── mock_config.py    # Development settings
```

## 🎯 Expected Behavior

### Successful Boot Sequence
```
Loading ESP8266 Wi-Fi driver
WiFi interfaces initialized
Loading ESP8266 MQTT driver
Loading ESP8266 GPIO driver
ESP8266GPIODriver: Initialized GPIO 14 in mode 0
ESP8266GPIODriver: Initialized GPIO 12 in mode 1
ESP8266GPIODriver: Initialized GPIO 13 in mode 1
Intercom: Drivers loaded successfully
🚪 Intercom system starting...
📡 Starting main intercom loop...
📶 WiFi not connected, attempting to connect...
⏳ Connecting to TP-Link_4FD0...
✓ Connected successfully!
  IP: 192.168.0.141
🔗 MQTT not connected, attempting to connect...
✓ MQTT connected to 192.168.0.172:1883
ESP8266GPIODriver: Call detected: False (GPIO Pin(14))
```

### Runtime Operations
- **Call Detection**: GPIO pin 14 monitors for incoming calls
- **MQTT Publishing**: Publishes call events to `pyntercom/intercom/call_detected`
- **Door Unlock**: Subscribes to `pyntercom/intercom/unlock` for remote commands
- **Auto-Reconnection**: Handles WiFi/MQTT disconnections automatically

## 🚨 Current Issues

### Problem 1: MQTT Subscription Timing
**File**: `src/app/intercom.py:167`
**Issue**: Subscribes to MQTT topics before connection established
**Error**: `Exception: Not connected to MQTT broker`

### Problem 2: Sleep Function Import
**Files**: Multiple driver files
**Issue**: `from src.helper import sleep` causes `'module' object isn't callable`
**Affected**: WiFi connection fails, system startup blocked

### Problem 3: WiFi Connection Failure
**File**: `src/driver/wifi_driver/esp8266_wifi_driver.py`
**Issue**: Sleep calls fail during WiFi connection sequence
**Result**: Cannot establish network connectivity

## 📊 System Status
```
✅ GPIO configuration (pull-up resistor on pin 14)
✅ Driver loading and initialization
✅ MQTT broker configuration (192.168.0.172:1883)
✅ Project structure and interfaces
❌ WiFi connection (sleep function errors)
❌ MQTT subscription (timing issue)
❌ Main loop execution (blocked at WiFi)
```

## 🔧 Development Environment
```bash
# File structure
pyntercom/
├── main.py                    # Entry point
├── scripts/
│   ├── deploy.sh             # Deployment script
│   └── repl.sh              # REPL connection
├── src/
│   ├── app/intercom.py       # Main controller
│   ├── config/               # Configuration
│   ├── driver/               # Hardware drivers
│   └── interfaces/           # Abstract interfaces
└── tests/                    # Unit tests
```

## 🛠️ Troubleshooting

### Common Issues
1. **Device in use**: Kill existing connections with `pkill -f "mpremote.*repl"`
2. **Serial port not found**: Check USB connection and device path
3. **Import errors**: Verify all dependencies installed in conda environment
4. **Connection timeouts**: Check WiFi credentials and MQTT broker availability

### Debug Commands
```bash
# Check device connection
mpremote a0 fs ls

# Manual file upload
mpremote a0 cp main.py :main.py

# Execute specific commands
mpremote a0 exec "import network; print(network.WLAN().scan())"
```

The system is well-architected but currently blocked by import/timing issues preventing successful startup.
