from src.interfaces.gpio_driver import GPIODriverInterface


class ESP8266GPIODriver(GPIODriverInterface):
    """Real ESP8266 GPIO driver implementation"""

    def __init__(self):
        from machine import Pin
        import time
        # define the configuration for GPIO pins
        import src.config as config
        self.detect_call_pin = Pin(config.CALL_DETECTOR_PIN, 
                                    mode=config.CALL_DETECTOR_MODE,
                                    pull=Pin.PULL_UP)
        print(f"[{time.time()}] ESP8266GPIODriver: Initialized GPIO {config.CALL_DETECTOR_PIN} in mode {config.CALL_DETECTOR_MODE} with internal pull-up")
        
        self.conversation_pin = Pin(config.CONVERSATION_RELAY_PIN,
                                          mode=config.CONVERSATION_RELAY_MODE,
                                          pull=config.CONVERSATION_RELAY_DEFAULT_VALUE)
        print(f"[{time.time()}] ESP8266GPIODriver: Initialized GPIO {config.CONVERSATION_RELAY_PIN} in mode {config.CONVERSATION_RELAY_MODE}")

        self.unlock_pin = Pin(config.DOOR_RELAY_PIN,
                              mode=config.DOOR_RELAY_MODE,
                              pull=config.DOOR_RELAY_DEFAULT_VALUE)
        print(f"[{time.time()}] ESP8266GPIODriver: Initialized GPIO {config.DOOR_RELAY_PIN} in mode {config.DOOR_RELAY_MODE}")

    def detect_call(self) -> bool:
        import time
        result = self.detect_call_pin.value() == 0
        if result:  # Only log when call is detected to reduce spam
            print(f"[{time.time()}] ESP8266GPIODriver: Call detected (GPIO Pin({self.detect_call_pin}))")
        return result 

    def open_conversation(self) -> None:
        import time
        self.conversation_pin.on()
        print(f"[{time.time()}] ESP8266GPIODriver: Opened conversation (GPIO ON)")

    def close_conversation(self) -> None:
        import time
        self.conversation_pin.off()
        print(f"[{time.time()}] ESP8266GPIODriver: Closed conversation (GPIO OFF)")

    def unlock(self) -> None:
        import time
        self.unlock_pin.on()
        print(f"[{time.time()}] ESP8266GPIODriver: Device unlocked (GPIO ON)")

    def lock(self) -> None:
        import time
        self.unlock_pin.off()
        print(f"[{time.time()}] ESP8266GPIODriver: Device locked (GPIO OFF)")
