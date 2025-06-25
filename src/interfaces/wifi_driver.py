from .base import ABC, abstractmethod

class WifiDriverInterface(ABC):
    def set_ssid_and_password(self, ssid: str, password: str) -> None:
        """Set the SSID and password for the Wi-Fi network."""
        self.ssid = ssid
        self.password = password
    
    @abstractmethod
    def connect(self, ssid: str, password: str) -> bool:
        """Connect to a Wi-Fi network with the given SSID and password."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the current Wi-Fi network."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if the device is currently connected to a Wi-Fi network."""
        pass