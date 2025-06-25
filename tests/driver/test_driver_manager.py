import sys
from src.driver.driver_manager import DriverManager
from src.driver.wifi_driver.mock_wifi_driver import MockWifiManager
from src.driver.wifi_driver.esp8266_wifi_driver import Esp8266WifiDriver

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