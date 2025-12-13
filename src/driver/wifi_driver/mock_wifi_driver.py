from src.interfaces.wifi_driver import WifiDriverInterface

class MockWifiDriver(WifiDriverInterface):
    def __init__(self):
        self._connected = False

    def connect(self, ssid: str, password: str) -> bool:
        """Simulate connecting to a WiFi network."""
        print(f"MockWifiDriver: Connecting to SSID: {ssid}")
        print(f"MockWifiDriver: Connected successfully!")
        self._connected = True
        return True

    def disconnect(self) -> bool:
        """Simulate disconnecting from a WiFi network."""
        print("MockWifiDriver: Disconnected from WiFi")
        self._connected = False
        return True

    def is_connected(self) -> bool:
        """Simulate checking if connected to a WiFi network."""
        return self._connected