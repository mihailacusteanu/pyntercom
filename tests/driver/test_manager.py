

from src.driver.manager import DriverManager
def test_can_instantiate_driver_manager():
    driver_manager = DriverManager()
    assert driver_manager is not None