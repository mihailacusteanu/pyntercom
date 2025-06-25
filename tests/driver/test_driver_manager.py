import sys
import types
from src.driver.driver_manager import DriverManager
from src.driver.wifi_driver.mock_wifi_driver import MockWifiManager
from src.driver.wifi_driver.esp8266_wifi_driver import Esp8266WifiDriver
from src.driver.mqtt_driver.mock_mqtt_driver import MockMqttDriver
from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
from src.driver.gpio_driver.mock_gpio_driver import MockGpioDriver
from tests.mock.fake_pin import FakePin 
from src.driver.gpio_driver.esp8266_gpio_driver import ESP8266GPIODriver

def test_can_instantiate_driver_manager():
    driver_manager = DriverManager()
    assert driver_manager is not None
    
def test_driver_manager_can_load_the_wifi_driver():
    driver_manager = DriverManager()
    wifi_driver = driver_manager.load_wifi_driver()
    assert wifi_driver is not None
    assert hasattr(wifi_driver, 'connect')
    assert hasattr(wifi_driver, 'disconnect')
    assert hasattr(wifi_driver, 'is_connected')
    
def test_on_darwin_platform_it_loads_the_mock_wifi_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    driver_manager = DriverManager()
    wifi_driver = driver_manager.load_wifi_driver()
    assert isinstance(wifi_driver, MockWifiManager)
    monkeypatch.undo()

def test_on_esp8266_platform_it_loads_the_esp8266_wifi_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "esp8266")
    driver_manager = DriverManager()
    wifi_driver = driver_manager.load_wifi_driver()
    assert isinstance(wifi_driver, Esp8266WifiDriver) 
    monkeypatch.undo()
    
def test_on_darwin_platform_it_loads_the_mock_mqtt_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    driver_manager = DriverManager()
    mqtt_driver = driver_manager.load_mqtt_driver()
    assert isinstance(mqtt_driver, MockMqttDriver)
    monkeypatch.undo()
    
def test_on_esp8266_platform_it_loads_the_esp8266_mqtt_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "esp8266")
    driver_manager = DriverManager()
    mqtt_driver = driver_manager.load_mqtt_driver()
    assert isinstance(mqtt_driver, Esp8266MQTTDriver)
    monkeypatch.undo()
    
def test_on_darwin_platform_it_loads_the_mock_gpio_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "darwin")
    driver_manager = DriverManager()
    gpio_driver = driver_manager.load_gpio_driver()
    assert isinstance(gpio_driver, MockGpioDriver)
    monkeypatch.undo()
    
def test_on_esp8266_platform_it_loads_the_esp8266_gpio_driver(monkeypatch):
    monkeypatch.setattr(sys, "platform", "esp8266")

    fake_machine = types.ModuleType("machine")

    fake_machine.Pin = FakePin
    sys.modules["machine"] = fake_machine
      
    driver_manager = DriverManager()
    gpio_driver = driver_manager.load_gpio_driver()

    assert isinstance(gpio_driver, ESP8266GPIODriver)
