from src.interfaces.wifi_driver import WifiDriverInterface
class MockWifiDriver(WifiDriverInterface):
        def set_ssid_and_password(self, ssid: str, password: str) -> None:
            """Set the SSID and password for the mock WiFi manager."""
            self.ssid = ssid
            self.password = password
            print(f"Mock SSID set to: {ssid}")
            print(f"Mock Password set to: {password}")

        def connect(self) -> bool:
            """Simulate connecting to a WiFi network."""
            if hasattr(self, 'ssid') and hasattr(self, 'password'):
                print(f"Mock connecting to SSID: {self.ssid} with Password: {self.password}")
                return True
            else:
                print("Error: SSID and Password not set")
                return False
        
        def disconnect(self) -> None:
            """Simulate disconnecting from a WiFi network."""
            print("Mock disconnected from WiFi")    
        def is_connected(self) -> bool:
            """Simulate checking if connected to a WiFi network."""
            if hasattr(self, 'ssid') and hasattr(self, 'password'):
                print(f"Mock is connected to SSID: {self.ssid}")
                return True
            else:
                print("Mock is not connected to any WiFi network")
                return False