from src.driver.driver_manager import DriverManager
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