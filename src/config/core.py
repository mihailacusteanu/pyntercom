import sys


MOCK_SLEEP = True


IN = 0
OUT = 1
PULL_UP = 2
PULL_DOWN = 3
    
CALL_DETECTOR_PIN=14
CALL_DETECTOR_DEFAULT_VALUE=0
CALL_DETECTOR_MODE=IN

DOOR_RELAY_PIN=13
DOOR_RELAY_DEFAULT_VALUE=0
DOOR_RELAY_MODE=OUT

CONVERSATION_RELAY_PIN=12
CONVERSATION_RELAY_DEFAULT_VALUE=0
CONVERSATION_RELAY_MODE=OUT

# MQTT topics

CALL_DETECTED_TOPIC = "pyntercom/intercom/call_detected"
ALLOW_CONVERSATION_TOPIC = "pyntercom/intercom/allow_conversation"
UNLOCK_TOPIC = "pyntercom/intercom/unlock"
CALL_DETECTED_MESSAGE = "call_detected"
DOOR_UNLOCKED_MESSAGE = "open"

if sys.platform == "esp8266":
    from .esp8266_config import *
else:
    from .mock_config import *
