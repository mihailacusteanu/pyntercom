from src.driver.driver_manager import DriverManager
import src.config as config
from src.helper import sleep

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
            
    def subscribe_to_subscribe_mqtt_topic_for_openning_door(self):
        """Subscribe to MQTT topic for opening the door."""
        self.mqtt_driver.subscribe(config.UNLOCK_TOPIC, self._handle_open_door_message)

    def _handle_open_door_message(self, message):
        """Open the door when a message is received."""
        if message == config.DOOR_UNLOCKED_MESSAGE:
            self.gpio_driver.open_conversation()
            sleep(1)  
            self.gpio_driver.unlock()
            sleep(5)
            self.gpio_driver.close_conversation()
            self.gpio_driver.lock()
            print("Intercom: Door unlocked")
        else:
            print("Intercom: Invalid message for unlocking door")