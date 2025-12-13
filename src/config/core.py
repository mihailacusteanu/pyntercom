import sys


MOCK_SLEEP = False

# Timing configuration
CALL_DEBOUNCE_SECONDS = 10  # Minimum seconds between processing consecutive calls
CONVERSATION_OPEN_DELAY_SECONDS = 1  # Delay between opening conversation and unlocking door
DOOR_UNLOCK_DURATION_SECONDS = 5  # How long the door stays unlocked for entry

IN = 0
OUT = 1
PULL_UP = 2
PULL_DOWN = 3

CALL_DETECTOR_PIN = 4
CALL_DETECTOR_DEFAULT_VALUE = PULL_UP
CALL_DETECTOR_MODE = IN

DOOR_RELAY_PIN = 13
DOOR_RELAY_DEFAULT_VALUE = 0
DOOR_RELAY_MODE = OUT

CONVERSATION_RELAY_PIN = 12
CONVERSATION_RELAY_DEFAULT_VALUE = 0
CONVERSATION_RELAY_MODE = OUT

# MQTT topics


CONFIGS_TOPIC = "pyntercon/config"
AUTO_UNLOCK_TOPIC = "pyntercom/auto_unlock"
LOGS_TOPIC = "pyntercom/logs"
CALL_DETECTED_TOPIC = "pyntercom/intercom/call_detected"
ALLOW_CONVERSATION_TOPIC = "pyntercom/intercom/allow_conversation"
UNLOCK_TOPIC = "pyntercom/intercom/unlock"
CALL_DETECTED_MESSAGE = "call_detected"
DOOR_UNLOCKED_MESSAGE = "open"

if sys.platform == "esp8266":
    from .secret_config import *
else:
    from .mock_config import *
