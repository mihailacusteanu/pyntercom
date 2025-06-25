from src.driver.driver_manager import DriverManager
import src.config as config

class Intercom:
    def __init__(self):
        self.driver_manager = DriverManager()
        self._load_drivers()
        
    def _load_drivers(self):
        """Load all drivers needed for the intercom system."""
        self.wifi_driver = self.driver_manager.load_wifi_driver()
        self.mqtt_driver = self.driver_manager.load_mqtt_driver()
        self.gpio_driver = self.driver_manager.load_gpio_driver()
        
        print("Intercom: Drivers loaded successfully")
        
    def detect_call_and_send_message(self):
        """Detect a call and send a message via MQTT."""
        if self.gpio_driver.detect_call():
            self.mqtt_driver.publish(config.CALL_DETECTED_TOPIC, "call_detected")