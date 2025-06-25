from src.interfaces.gpio_driver import GPIODriverInterface


class MockGpioDriver(GPIODriverInterface):
    """Mock GPIO driver implementation for testing"""

    def detect_call(self) -> bool:
        print("MockGpioDriver: Simulated call detection (always returns True)")
        return True

    def open_conversation(self) -> None:
        print("MockGpioDriver: Opened conversation (simulated GPIO ON)")

    def close_conversation(self) -> None:
        print("MockGpioDriver: Closed conversation (simulated GPIO OFF)")

    def unlock(self) -> None:
        print("MockGpioDriver: Device unlocked (simulated GPIO ON)")

    def lock(self) -> None:
        print("MockGpioDriver: Device locked (simulated GPIO OFF)")
