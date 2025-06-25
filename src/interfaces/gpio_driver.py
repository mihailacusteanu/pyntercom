from .base import ABC, abstractmethod


class GPIODriverInterface(ABC):
    @abstractmethod
    def detect_call(self) -> bool:
        """Detect if a call is present"""
        pass

    @abstractmethod
    def open_conversation(self) -> None:
        """Open a conversation by setting the appropriate GPIO pin"""
        pass

    @abstractmethod
    def close_conversation(self) -> None:
        """Close the conversation by resetting the GPIO pin"""
        pass

    @abstractmethod
    def unlock(self) -> None:
        """Unlock the device by setting the appropriate GPIO pin"""
        pass

    @abstractmethod
    def lock(self) -> None:
        """Lock the device by resetting the appropriate GPIO pin"""
        pass
