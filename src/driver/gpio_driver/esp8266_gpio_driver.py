from src.interfaces.gpio_driver import GPIODriverInterface


class ESP8266GPIODriver(GPIODriverInterface):
    """Real ESP8266 GPIO driver implementation"""

    def __init__(self):
        from machine import Pin
        # define the configuration for GPIO pins
        import src.config as config
        self.detect_call_pin = Pin(config.CALL_DETECTOR_PIN, 
                                    mode=config.CALL_DETECTOR_MODE, 
                                    pull=config.CALL_DETECTOR_DEFAULT_VALUE)
        print(f"ESP8266GPIODriver: Initialized GPIO {config.CALL_DETECTOR_PIN} in mode {config.CALL_DETECTOR_MODE}")
        
        self.conversation_pin = Pin(config.CONVERSATION_RELAY_PIN,
                                          mode=config.CONVERSATION_RELAY_MODE,
                                          pull=config.CONVERSATION_RELAY_DEFAULT_VALUE)
        print(f"ESP8266GPIODriver: Initialized GPIO {config.CONVERSATION_RELAY_PIN} in mode {config.CONVERSATION_RELAY_MODE}")

        self.unlock_pin = Pin(config.DOOR_RELAY_PIN,
                              mode=config.DOOR_RELAY_MODE,
                              pull=config.DOOR_RELAY_DEFAULT_VALUE)
        print(f"ESP8266GPIODriver: Initialized GPIO {config.DOOR_RELAY_PIN} in mode {config.DOOR_RELAY_MODE}")

    def detect_call(self) -> bool:
        call_detected = self.detect_call_pin.value() == 0  # Active-low: 0 = call detected (grounded)
        print(f"ESP8266GPIODriver: Call detected: {call_detected} (GPIO {self.detect_call_pin})")
        return call_detected

    def open_conversation(self) -> None:
        self.conversation_pin.on()
        print("ESP8266GPIODriver: Opened conversation (GPIO ON)")

    def close_conversation(self) -> None:
        self.conversation_pin.off()
        print("ESP8266GPIODriver: Closed conversation (GPIO OFF)")

    def unlock(self) -> None:
        self.unlock_pin.on()
        print("ESP8266GPIODriver: Device unlocked (GPIO ON)")

    def lock(self) -> None:
        self.unlock_pin.off()
        print("ESP8266GPIODriver: Device locked (GPIO OFF)")
