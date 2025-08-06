from tests.mock.fake_pin import FakePin


def test_esp8266_gpio_driver_initialization(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    assert gpio_driver.detect_call_pin is not None
    assert gpio_driver.conversation_pin is not None
    assert gpio_driver.unlock_pin is not None


def test_detect_call_and_detect_a_call(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()
    _simulate_call_detected(gpio_driver)
    assert gpio_driver.detect_call() is True
    assert gpio_driver.detect_call() is True


def test_detect_call_and_dont_detect_a_call(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    _simulate_no_call_detected(gpio_driver)
    assert gpio_driver.detect_call() is False
    assert gpio_driver.detect_call() is False


def test_unlock_door(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    gpio_driver.unlock()
    assert gpio_driver.unlock_pin.value() == 1


def test_lock_door(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    gpio_driver.lock()
    assert gpio_driver.unlock_pin.value() == 0


def test_open_conversation(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    gpio_driver.open_conversation()
    assert gpio_driver.conversation_pin.value() == 1


def test_close_conversation(monkeypatch):
    _mock_machine(monkeypatch)
    
    from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver
    gpio_driver = ESP8266GPIODriver()

    gpio_driver.close_conversation()
    assert gpio_driver.conversation_pin.value() == 0


# PRIVATE FUNCTIONS
def _mock_machine(monkeypatch):
    """Monkeypatches the entire machine module with fake implementations for testing purposes."""
    import sys
    from types import ModuleType
    
    # Create a fake machine module
    fake_machine = ModuleType('machine')
    fake_machine.Pin = FakePin
    
    # Patch it into sys.modules so imports work
    monkeypatch.setitem(sys.modules, 'machine', fake_machine)


def _mock_pin(monkeypatch):
    """Monkeypatches the machine.Pin class with FakePin for testing purposes."""
    monkeypatch.setattr("machine.Pin", FakePin)


def _simulate_call_detected(gpio_driver):
    gpio_driver.detect_call_pin._val = 1  # Match current driver logic: 1 = call detected


def _simulate_no_call_detected(gpio_driver):
    gpio_driver.detect_call_pin._val = 0  # Match current driver logic: 0 = no call
