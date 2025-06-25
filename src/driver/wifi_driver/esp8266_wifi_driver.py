from src.interfaces.wifi_driver import WifiDriverInterface
from src.helper import sleep


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
            print("WiFi interfaces initialized")
        except ImportError:
            print("Warning: network module not available (not running on ESP8266)")
            # For testing/development on non-ESP8266 platforms
            self.sta_if = None
            self.ap_if = None

    def disable_ap_mode(self):
        """Disable the Wi-Fi Access Point interface to save power"""
        self.ap_if.active(False)

    def connect(self, ssid: str, password: str) -> bool:
        """Connect to WiFi network with timeout and retry logic"""
        if not self.sta_if:
            print("Error: WiFi interface not available")
            return False

        print(f"Connecting to WiFi SSID: {ssid}")

        try:
            # Activate station interface
            self.sta_if.active(True)

            # Disconnect if already connected to a different network
            if self.sta_if.isconnected():
                print("Disconnecting from current network...")
                self.sta_if.disconnect()
                time.sleep(1)

            # Start connection
            self.sta_if.connect(ssid, password)

            # Wait for connection with timeout
            timeout = 15  # 15 seconds timeout
            while not self.sta_if.isconnected() and timeout > 0:
                print(".", end="")
                time.sleep(1)
                timeout -= 1

            print()  # New line after dots

            if self.sta_if.isconnected():
                config = self.sta_if.ifconfig()
                print(f"✓ Connected successfully!")
                print(f"  IP: {config[0]}")
                print(f"  Subnet: {config[1]}")
                print(f"  Gateway: {config[2]}")
                print(f"  DNS: {config[3]}")
                return True
            else:
                print("✗ Connection timeout - failed to connect")
                return False

        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False

    def disconnect(self) -> bool:
        """Disconnect from WiFi network"""
        if not self.sta_if:
            print("Error: WiFi interface not available")
            return False

        try:
            if self.sta_if.isconnected():
                print("Disconnecting from WiFi...")
                self.sta_if.disconnect()

                # Wait for disconnection
                timeout = 5
                while self.sta_if.isconnected() and timeout > 0:
                    time.sleep(0.5)
                    timeout -= 0.5

                if not self.sta_if.isconnected():
                    print("✓ Disconnected successfully")
                    return True
                else:
                    print("⚠️  Disconnection timeout")
                    return False
            else:
                print("Already disconnected")
                return True

        except Exception as e:
            print(f"✗ Disconnection error: {e}")
            return False

    def is_connected(self) -> bool:
        """Check if connected to WiFi"""
        if not self.sta_if:
            return False
        return self.sta_if.isconnected()
