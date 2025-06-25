from src.driver.wifi_driver.mock_wifi_driver import MockWifiManager
from src.driver.wifi_driver.esp8266_wifi_driver import Esp8266WifiDriver
from src.driver.mqtt_driver.mock_mqtt_driver import MockMqttDriver
from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
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
    def load_mqtt_driver(self):
        """Load the MQTT driver."""
        if sys.platform == "esp8266":
            print("Loading ESP8266 MQTT driver")
            return Esp8266MQTTDriver(client_id="esp8266_client",
                                      server="mqtt.example.com",
                                      port=1883,
                                      call_detected_topic="call/detected",
                                      allow_conversation_topic="conversation/allow",
                                      unlock_topic="device/unlock",
                                      mqtt_username="user",
                                      mqtt_password="password")
        else:
            print("Loading Mock MQTT driver for macOS")
            return MockMqttDriver()
        