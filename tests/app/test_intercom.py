import pytest
from unittest.mock import Mock, patch
from src.app.intercom import Intercom
from src.config.core import CALL_DETECTED_TOPIC, CALL_DETECTED_MESSAGE


def test_can_instantiate_intercom():
    intercom = Intercom()
    assert intercom is not None


def test_when_creating_an_instance_it_also_instantiates_the_driver_manager():
    intercom = Intercom()
    assert intercom.driver_manager is not None


def test_intercom_can_load_drivers():
    intercom = Intercom()
    intercom._load_drivers()
    assert intercom.wifi_driver is not None
    assert intercom.mqtt_driver is not None
    assert intercom.gpio_driver is not None


def test_intercom_drivers_are_loaded_correctly():
    intercom = Intercom()
    intercom._load_drivers()
    
    assert intercom.wifi_driver.__class__.__name__ == "MockWifiDriver"
    assert intercom.mqtt_driver.__class__.__name__ == "MockMqttDriver"
    assert intercom.gpio_driver.__class__.__name__ == "MockGpioDriver"


def test_when_detecting_call_should_send_message_to_mqtt():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.detect_call.return_value = True
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    intercom.detect_call_and_send_message()
    
    mock_gpio_driver.detect_call.assert_called_once()
    mock_mqtt_driver.publish.assert_called_once_with(CALL_DETECTED_TOPIC, CALL_DETECTED_MESSAGE)


def test_when_no_call_detected_should_not_send_message_to_mqtt():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.detect_call.return_value = False
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    intercom.detect_call_and_send_message()
    
    mock_gpio_driver.detect_call.assert_called_once()
    mock_mqtt_driver.publish.assert_not_called()


@patch('src.config.CALL_DETECTED_TOPIC', 'test/call/detected')
def test_mqtt_message_uses_correct_topic_from_config():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.detect_call.return_value = True
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    intercom.detect_call_and_send_message()
    
    mock_mqtt_driver.publish.assert_called_once_with("test/call/detected", "call_detected")


def test_intercom_with_driver_manager_mocking():
    with patch('src.app.intercom.DriverManager') as mock_driver_manager_class:
        mock_wifi_driver = Mock()
        mock_mqtt_driver = Mock()
        mock_gpio_driver = Mock()
        
        mock_driver_manager = Mock()
        mock_driver_manager.load_wifi_driver.return_value = mock_wifi_driver
        mock_driver_manager.load_mqtt_driver.return_value = mock_mqtt_driver
        mock_driver_manager.load_gpio_driver.return_value = mock_gpio_driver
        
        mock_driver_manager_class.return_value = mock_driver_manager
        
        mock_gpio_driver.detect_call.return_value = True
        
        intercom = Intercom()
        
        mock_driver_manager_class.assert_called_once()
        mock_driver_manager.load_wifi_driver.assert_called_once()
        mock_driver_manager.load_mqtt_driver.assert_called_once()
        mock_driver_manager.load_gpio_driver.assert_called_once()
        
        intercom.detect_call_and_send_message()
        
        mock_gpio_driver.detect_call.assert_called_once()
        mock_mqtt_driver.publish.assert_called_once()


def test_intercom_error_handling_when_gpio_driver_fails():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.detect_call.side_effect = Exception("GPIO error")
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with pytest.raises(Exception, match="GPIO error"):
        intercom.detect_call_and_send_message()


def test_intercom_error_handling_when_mqtt_driver_fails():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.detect_call.return_value = True
    mock_mqtt_driver.publish.side_effect = Exception("MQTT error")
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with pytest.raises(Exception, match="MQTT error"):
        intercom.detect_call_and_send_message()


def test_subscribe_to_mqtt_topic_for_opening_door():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.UNLOCK_TOPIC', 'test/unlock/topic'):
        intercom.subscribe_to_mqtt_topic_for_opening_door()
        
        mock_mqtt_driver.subscribe.assert_called_once_with('test/unlock/topic', intercom._handle_open_door_message)


def test_handle_open_door_message_with_valid_message():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'unlock_door'):
        with patch('src.app.intercom.sleep') as mock_sleep:
            intercom._handle_open_door_message('test/unlock', 'unlock_door')
            
            mock_gpio_driver.open_conversation.assert_called_once()
            mock_gpio_driver.unlock.assert_called_once()
            mock_gpio_driver.close_conversation.assert_called_once()
            mock_gpio_driver.lock.assert_called_once()
            
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(5)


def test_handle_open_door_message_with_invalid_message():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'unlock_door'):
        intercom._handle_open_door_message('test/unlock', 'invalid_message')
        
        mock_gpio_driver.open_conversation.assert_not_called()
        mock_gpio_driver.unlock.assert_not_called()
        mock_gpio_driver.close_conversation.assert_not_called()
        mock_gpio_driver.lock.assert_not_called()


def test_handle_open_door_message_gpio_sequence():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'unlock_door'):
        with patch('src.app.intercom.sleep'):
            intercom._handle_open_door_message('test/unlock', 'unlock_door')
            
            calls = mock_gpio_driver.method_calls
            expected_sequence = [
                ('open_conversation', (), {}),
                ('unlock', (), {}),
                ('close_conversation', (), {}),
                ('lock', (), {})
            ]
            
            assert calls == expected_sequence


def test_handle_open_door_message_error_handling():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    mock_gpio_driver.open_conversation.side_effect = Exception("GPIO error")
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'unlock_door'):
        # Should not raise exception due to error handling
        intercom._handle_open_door_message('test/unlock', 'unlock_door')
        
        # Verify that emergency cleanup was called
        mock_gpio_driver.open_conversation.assert_called_once()
        mock_gpio_driver.close_conversation.assert_called_once()
        mock_gpio_driver.lock.assert_called_once()
        
        # unlock should not have been called due to early failure
        mock_gpio_driver.unlock.assert_not_called()


def test_handle_open_door_message_error_handling_cleanup_failure():
    """Test error handling when both the main sequence and emergency cleanup fail."""
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    # Simulate failure in main sequence
    mock_gpio_driver.open_conversation.side_effect = Exception("GPIO error")
    # Simulate failure in emergency cleanup - close_conversation fails but lock succeeds
    mock_gpio_driver.close_conversation.side_effect = Exception("Cleanup error")
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'unlock_door'):
        # Should not raise exception even when cleanup fails
        intercom._handle_open_door_message('test/unlock', 'unlock_door')
        
        # Verify that emergency cleanup was attempted for both operations
        mock_gpio_driver.open_conversation.assert_called_once()
        mock_gpio_driver.close_conversation.assert_called_once()
        mock_gpio_driver.lock.assert_called_once()  # Should still be called even if close fails


@patch('src.config.UNLOCK_TOPIC', 'test/unlock')
@patch('src.config.DOOR_UNLOCKED_MESSAGE', 'test_unlock')
def test_full_door_unlock_workflow():
    intercom = Intercom()
    
    mock_wifi_driver = Mock()
    mock_mqtt_driver = Mock()
    mock_gpio_driver = Mock()
    
    intercom.wifi_driver = mock_wifi_driver
    intercom.mqtt_driver = mock_mqtt_driver
    intercom.gpio_driver = mock_gpio_driver
    
    intercom.subscribe_to_mqtt_topic_for_opening_door()
    
    mock_mqtt_driver.subscribe.assert_called_once_with('test/unlock', intercom._handle_open_door_message)
    
    with patch('src.app.intercom.sleep'):
        intercom._handle_open_door_message('test/unlock', 'test_unlock')
        
        mock_gpio_driver.open_conversation.assert_called_once()
        mock_gpio_driver.unlock.assert_called_once()
        mock_gpio_driver.close_conversation.assert_called_once()
        mock_gpio_driver.lock.assert_called_once()