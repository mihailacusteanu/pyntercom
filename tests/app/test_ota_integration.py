"""Integration tests for OTA trigger via MQTT in intercom."""

import pytest
from unittest.mock import Mock, patch
from src.app.intercom import Intercom


def test_intercom_subscribes_to_ota_when_callback_provided():
    """Test that intercom subscribes to OTA topic when callback is provided."""
    ota_callback = Mock()
    intercom = Intercom(ota_callback=ota_callback)

    # Mock MQTT driver
    intercom.mqtt_driver.connect = Mock(return_value=True)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()

    # Connect MQTT
    result = intercom._connect_mqtt()

    assert result == True
    # Should subscribe to OTA topic with the callback
    calls = [str(call) for call in intercom.mqtt_driver.subscribe.call_args_list]
    ota_subscription_found = any("pyntercom/ota" in call for call in calls)
    assert ota_subscription_found, f"OTA subscription not found in calls: {calls}"


def test_intercom_does_not_subscribe_to_ota_when_no_callback():
    """Test that intercom doesn't subscribe to OTA topic when callback is None."""
    intercom = Intercom(ota_callback=None)

    # Mock MQTT driver
    intercom.mqtt_driver.connect = Mock(return_value=True)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()

    # Connect MQTT
    result = intercom._connect_mqtt()

    assert result == True
    # Should NOT subscribe to OTA topic
    calls = [str(call) for call in intercom.mqtt_driver.subscribe.call_args_list]
    ota_subscription_found = any("pyntercom/ota" in call for call in calls)
    assert not ota_subscription_found, f"OTA subscription should not be present: {calls}"


def test_ota_callback_is_called_when_mqtt_message_received():
    """Test that OTA callback is invoked when MQTT message arrives on OTA topic."""
    ota_callback = Mock()
    intercom = Intercom(ota_callback=ota_callback)

    # Mock MQTT connection
    intercom.mqtt_driver.connect = Mock(return_value=True)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()

    # Connect and capture the callback
    intercom._connect_mqtt()

    # Get the callback that was registered for OTA topic
    ota_topic_callback = None
    for call in intercom.mqtt_driver.subscribe.call_args_list:
        args, kwargs = call
        if args[0] == "pyntercom/ota":
            ota_topic_callback = args[1]
            break

    assert ota_topic_callback is not None, "OTA callback not registered"
    assert ota_topic_callback == ota_callback, "Wrong callback registered"


def test_ota_subscription_survives_reconnection():
    """Test that OTA subscription is restored after MQTT reconnects."""
    ota_callback = Mock()
    intercom = Intercom(ota_callback=ota_callback)

    # Mock MQTT driver
    intercom.mqtt_driver.connect = Mock(return_value=True)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()

    # Connect once
    intercom._connect_mqtt()

    # Disconnect and reconnect
    intercom.mqtt_driver.subscribe.reset_mock()
    intercom._connect_mqtt()

    # Should subscribe again
    calls = [str(call) for call in intercom.mqtt_driver.subscribe.call_args_list]
    ota_subscription_found = any("pyntercom/ota" in call for call in calls)
    assert ota_subscription_found, "OTA subscription not restored after reconnect"


def test_intercom_backwards_compatible_without_ota():
    """Test that intercom works without OTA callback (backwards compatibility)."""
    # Create intercom without OTA callback (old way)
    intercom = Intercom()

    assert intercom.ota_callback is None

    # Should still connect to MQTT successfully
    intercom.mqtt_driver.connect = Mock(return_value=True)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()

    result = intercom._connect_mqtt()
    assert result == True
