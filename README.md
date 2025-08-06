# Pyntercom: A MicroPython Project Powering My Actual Apartment Intercom

## Overview

Pyntercom is a MicroPython project that enables smart functionality for a standard apartment intercom system. It allows you to remotely answer calls and unlock the door using [Home Assistant](https://www.home-assistant.io/)(MQTT communication). The system runs on ESP8266 hardware(or any other MicroPython compatible device) and bridges the gap between your traditional intercom and smart home ecosystem.

## Features

- 📱 **Smart Call Detection**: Edge-triggered call detection with debouncing to prevent false triggers
- 🔓 **Remote Door Unlock**: Door unlocking via MQTT commands from Home Assistant
- 🔌 **Home Automation Integration**: Seamless integration with home automation systems via MQTT
- 🔄 **Auto-Recovery**: Automatic recovery from WiFi/MQTT disconnections with reconnection logic
- ⚡ **Hardware Optimized**: Internal pull-up resistors for reliable GPIO operation
- 🧪 **Development Support**: Built-in test mode and comprehensive debug logging

## Hardware Requirements

- **ESP8266 board** (NodeMCU, Wemos D1, ESP12F relay board, etc.)
- **Relay module x2** (for controlling door lock and conversation) - *Note: ESP12F relay boards have integrated relays*
- **Appropriate power supply** (3.3V or 5V depending on your board)
- **Connection to intercom system** (depends on your specific intercom model)
- **No external pull-up resistors required** - GPIO 4 has internal pull-up support

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/mihailacusteanu/pyntercom.git
   cd pyntercom
   ```

2. Create your configuration:

   ```bash
   cp src/config/mock_config.py src/config/secret_config.py
   ```

3. Edit `src/config/secret_config.py` with your WiFi and MQTT credentials.

4. Flash MicroPython to your ESP8266 board (if not already done):

   ```bash
   # Install required tools
   pip install esptool rshell
   
   # Flash MicroPython firmware
   esptool.py --port /dev/your_port erase_flash
   esptool.py --port /dev/your_port write_flash -fm dio 0 firmware.bin
   ```

5. Deploy the code to your ESP8266 using the provided script:

   ```bash
   ./scripts/deploy.sh
   ```

   The script will automatically detect your ESP8266 device.

## Configuration

Configure the system by editing the following in `src/config/secret_config.py`:

```python
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
MQTT_USERNAME = "your_mqtt_username" 
MQTT_PASSWORD = "your_mqtt_password"
MQTT_CLIENT_ID = "your_client_id"
MQTT_SERVER = "your_mqtt_server"
```

The GPIO pin configurations are defined in `src/config/core.py` and can be modified if needed:

```python
CALL_DETECTOR_PIN = 4        # GPIO 4 with internal pull-up (recommended for ESP12F)
DOOR_RELAY_PIN = 13          # GPIO 13 for door unlock relay
CONVERSATION_RELAY_PIN = 12  # GPIO 12 for conversation relay
```

### Call Detection Features

The system includes advanced call detection with:

- **Edge Detection**: Only triggers on transition from no-call to call-detected
- **Debouncing**: 5-second cooldown between call notifications to prevent spam
- **Internal Pull-up**: Uses GPIO 4's internal pull-up resistor for reliable operation
- **Active-Low Logic**: Call detected when GPIO 4 is grounded (connected to ground)

## Usage

Once deployed to the ESP8266, the system will:

1. **Connect to WiFi** with automatic retry logic
2. **Connect to MQTT broker** with reconnection handling
3. **Monitor for incoming calls** using edge detection on GPIO 4
4. **Publish call events** to MQTT topic `pyntercom/intercom/call_detected` (with 5s debouncing)
5. **Listen for unlock commands** on MQTT topic `pyntercom/intercom/unlock`
6. **Execute door unlock sequence** when receiving valid commands

### MQTT Topics

- **Publish**: `pyntercom/intercom/call_detected`
  - Message: `"call_detected"` - Published when a new call is detected (edge-triggered)
  - Debounced: 5-second cooldown between messages
- **Subscribe**: `pyntercom/intercom/unlock`
  - Command: `"open"` - Send this message to unlock the door
  - Action: Activates conversation relay → unlocks door → waits 5s → locks door → closes conversation

### Testing

Test mode is available for development:

```python
intercom = Intercom()
intercom.run(test_mode=True, max_iterations=10)  # Will run for 10 iterations only
```

## Wiring

Connect your ESP8266 to the intercom system as follows:

### GPIO Pin Configuration

1. **GPIO 4** - Input for call detection (with internal pull-up resistor)
   - Connect to intercom call signal (ground when call detected)
   - **No external pull-up resistor needed** - uses internal 10kΩ pull-up
   - Active-low: HIGH = no call, LOW = call detected

2. **GPIO 13** - Output for door unlock relay
   - Controls the door unlock mechanism
   - HIGH = door unlocked, LOW = door locked

3. **GPIO 12** - Output for conversation relay
   - Controls the intercom conversation connection
   - HIGH = conversation active, LOW = conversation inactive

### ESP12F Relay Board Compatibility

This configuration is optimized for ESP12F relay boards where:

- GPIO 4 has reliable internal pull-up support
- GPIO 12/13 control onboard relays
- No external components required for basic operation

### Schematic

Below is the wiring schematic for connecting the ESP8266 to your intercom system:

![Intercom Wiring Schematic](docs/images/schematic.png)

## Development

### REPL Access

For interactive development and debugging:

```bash
./scripts/repl.sh
```

This connects to the ESP8266 REPL for real-time debugging and testing.

### Cleaning Cache

Clean Python cache files with:

```bash
./scripts/clean.sh
```

### Local Development

For local development on your computer (uses mock drivers):

```python
from src.app.intercom import Intercom

intercom = Intercom()
intercom.run(test_mode=True, max_iterations=10)  # Runs for 10 iterations
```

### Debug Output

The system provides comprehensive debug logging including:

- GPIO state changes and call detection events
- MQTT connection status and message handling  
- WiFi connection attempts and status
- Edge detection and debouncing logic
- Door unlock sequence execution

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

MIT License permits use, modification, and distribution of this code for both private and commercial purposes, provided the license and copyright notice are included. No warranty is provided.

## Credits

Developed by Mihai Lacusteanu

## Disclaimer

This project involves interfacing with an intercom system and modifying electrical connections. Please ensure you know what you're doing and proceed at your own risk.
