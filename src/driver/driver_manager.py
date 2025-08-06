from src.driver.wifi_driver.mock_wifi_driver import MockWifiDriver
from src.driver.wifi_driver.esp8266_wifi_driver import Esp8266WifiDriver
from src.driver.mqtt_driver.mock_mqtt_driver import MockMqttDriver
from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
import src.config as config
import sys

class DriverManager:
    """Manages hardware drivers for the intercom system.
    
    This class is responsible for loading the appropriate hardware drivers
    based on the current platform. It dynamically selects between ESP8266
    drivers for production use and mock drivers for development/testing.
    
    The driver manager abstracts hardware dependencies, making the main
    application code platform-independent and easier to test.
    """
    def load_wifi_driver(self):
        """Load the appropriate Wi-Fi driver based on the platform.
        
        Returns an instance of a Wi-Fi driver compatible with the current platform.
        On ESP8266, returns a hardware driver. On other platforms (development),
        returns a mock driver for testing.
        
        Returns:
            An instance of either Esp8266WifiDriver or MockWifiDriver
        """
        if sys.platform == "esp8266":
            print("Loading ESP8266 Wi-Fi driver")
            return Esp8266WifiDriver()
        else:
            print("Loading Mock Wi-Fi driver for macOS")
            return MockWifiDriver()
    def load_mqtt_driver(self):
        """Load the appropriate MQTT driver based on the platform.
        
        Returns an instance of an MQTT driver compatible with the current platform.
        On ESP8266, returns a hardware driver configured with the necessary MQTT
        connection parameters. On other platforms (development), returns a mock
        driver for testing.
        
        Returns:
            An instance of either Esp8266MQTTDriver or MockMqttDriver
        """
        if sys.platform == "esp8266":
            print("Loading ESP8266 MQTT driver")
            return Esp8266MQTTDriver(client_id=config.MQTT_CLIENT_ID,
                                      server=config.MQTT_SERVER,
                                      port=1883,
                                      call_detected_topic="call/detected",
                                      allow_conversation_topic="conversation/allow",
                                      unlock_topic="device/unlock",
                                      mqtt_username=config.MQTT_USERNAME,
                                      mqtt_password=config.MQTT_PASSWORD)
        else:
            print("Loading Mock MQTT driver for macOS")
            return MockMqttDriver()
    def load_gpio_driver(self):
        """Load the appropriate GPIO driver based on the platform.
        
        Returns an instance of a GPIO driver compatible with the current platform.
        On ESP8266, returns a hardware driver that can control actual GPIO pins.
        On other platforms (development), returns a mock driver that simulates
        GPIO functionality for testing purposes.
        
        The GPIO driver handles call detection and door unlock operations.
        
        Returns:
            An instance of either ESP8266GPIODriver or MockGpioDriver
        """
        if sys.platform == "esp8266":
            print("Loading ESP8266 GPIO driver")
            from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
            return ESP8266GPIODriver()
        else:
            from src.driver.gpio_driver.mock_gpio_driver import MockGpioDriver
            print("Loading Mock GPIO driver for macOS")
            return MockGpioDriver()
        