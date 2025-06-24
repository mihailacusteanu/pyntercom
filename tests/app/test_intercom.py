from src.app.intercom import Intercom


def test_can_instantiate_intercom():
    intercom = Intercom()
    assert intercom is not None
    
def test_when_creating_an_instance_it_also_instantiates_the_driver_manager():
    intercom = Intercom()
    assert intercom.driver_manager is not None