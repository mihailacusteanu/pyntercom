from .base import ABC, abstractmethod

class WifiDriverInterface(ABC):
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