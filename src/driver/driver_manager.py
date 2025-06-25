from src.driver.wifi_driver.mock_wifi_driver import MockWifiManager
from src.driver.wifi_driver.esp8266_wifi_driver import Esp8266WifiDriver
import sys
class DriverManager:
    def load_wifi_driver(self):
        """Load the Wi-Fi driver."""
        if sys.platform == "esp8266":
            print("Loading ESP8266 Wi-Fi driver")
            return Esp8266WifiDriver()
        else:
            print("Loading Mock Wi-Fi driver for macOS")
            return MockWifiManager()