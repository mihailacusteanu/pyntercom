from src.interfaces.wifi_driver import WifiDriverInterface
from src.helper.sleep import sleep
import time


class Esp8266WifiDriver(WifiDriverInterface):
    def __init__(self):
        self.sta_if = None
        self.ap_if = None
        self._setup_interfaces()

    def _setup_interfaces(self):
        """Initialize WiFi interfaces"""
        try:
            import network
            self.sta_if = network.WLAN(network.STA_IF)
            self.ap_if = network.WLAN(network.AP_IF)

            self.disable_ap_mode()
            print(f"[{time.time()}] WiFi interfaces initialized")
        except ImportError:
            print(f"[{time.time()}] Warning: network module not available (not running on ESP8266)")
            self.sta_if = None
            self.ap_if = None

    def disable_ap_mode(self):
        """Disable the Wi-Fi Access Point interface to save power"""
        self.ap_if.active(False)

    def connect(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network with timeout and retry logic"""
        if not self.sta_if:
            print(f"[{time.time()}] Error: WiFi interface not available")
            return False

        print(f"[{time.time()}] Connecting to WiFi SSID: {ssid}")

        try:
            self.sta_if.active(True)

            if self.sta_if.isconnected():
                print(f"[{time.time()}] Disconnecting from current network...")
                self.sta_if.disconnect()
                sleep(1)

            self.sta_if.connect(ssid, password)

            timeout = 15
            while not self.sta_if.isconnected() and timeout > 0:
                print(".", end="")
                sleep(1)
                timeout -= 1

            print() 

            if self.sta_if.isconnected():
                config = self.sta_if.ifconfig()
                print(f"[{time.time()}] ✓ Connected successfully!")
                print(f"[{time.time()}]   IP: {config[0]}")
                print(f"[{time.time()}]   Subnet: {config[1]}")
                print(f"[{time.time()}]   Gateway: {config[2]}")
                print(f"[{time.time()}]   DNS: {config[3]}")
                return True
            else:
                print(f"[{time.time()}] ✗ Connection timeout - failed to connect")
                return False

        except Exception as e:
            print(f"[{time.time()}] ✗ Connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from WiFi network"""
        if not self.sta_if:
            print(f"[{time.time()}] Error: WiFi interface not available")
            return False

        try:
            if self.sta_if.isconnected():
                print(f"[{time.time()}] Disconnecting from WiFi...")
                self.sta_if.disconnect()

                timeout = 5
                while self.sta_if.isconnected() and timeout > 0:
                    sleep(0.5)
                    timeout -= 0.5

                if not self.sta_if.isconnected():
                    print(f"[{time.time()}] ✓ Disconnected successfully")
                    return True
                else:
                    print(f"[{time.time()}] ⚠️  Disconnection timeout")
                    return False
            else:
                print(f"[{time.time()}] Already disconnected")
                return True

        except Exception as e:
            print(f"[{time.time()}] ✗ Disconnection error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to WiFi"""
        if not self.sta_if:
            return False
        return self.sta_if.isconnected()
