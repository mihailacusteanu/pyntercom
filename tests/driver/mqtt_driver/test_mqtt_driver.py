import pytest
from unittest.mock import Mock, patch, MagicMock
import sys


def test_esp8266_mqtt_driver_initialization():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com",
        port=1883
    )
    
    assert mqtt_driver is not None
    assert mqtt_driver.client_id == "test_client"
    assert mqtt_driver.server == "test.broker.com"
    assert mqtt_driver.port == 1883
    assert mqtt_driver.connected is False
    assert mqtt_driver.client is None
    assert mqtt_driver.subscriptions == {}


def test_esp8266_mqtt_driver_connect():
    mock_mqtt_client = Mock()
    mock_umqtt = MagicMock()
    mock_umqtt.simple.MQTTClient.return_value = mock_mqtt_client
    
    with patch.dict(sys.modules, {'umqtt.simple': mock_umqtt.simple, 'umqtt': mock_umqtt}):
        if 'src.driver.mqtt_driver.esp8266_mqtt_driver' in sys.modules:
            del sys.modules['src.driver.mqtt_driver.esp8266_mqtt_driver']
        
        from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
        
        mqtt_driver = Esp8266MQTTDriver(
            client_id="test_client",
            server="test.broker.com",
            mqtt_username="user",
            mqtt_password="pass"
        )
        
        result = mqtt_driver.connect()
        
        assert result is True
        assert mqtt_driver.connected is True
        assert mqtt_driver.client == mock_mqtt_client
        
        mock_umqtt.simple.MQTTClient.assert_called_once_with(
            client_id="test_client",
            server="test.broker.com",
            port=1883,
            user="user",
            password="pass",
            keepalive=60,
            ssl=False,
            ssl_params={}
        )
        mock_mqtt_client.set_callback.assert_called_once()
        mock_mqtt_client.connect.assert_called_once()


def test_esp8266_mqtt_driver_connect_failure():
    mock_umqtt = MagicMock()
    mock_umqtt.simple.MQTTClient.side_effect = Exception("Connection failed")
    
    with patch.dict(sys.modules, {'umqtt.simple': mock_umqtt.simple, 'umqtt': mock_umqtt}):
        if 'src.driver.mqtt_driver.esp8266_mqtt_driver' in sys.modules:
            del sys.modules['src.driver.mqtt_driver.esp8266_mqtt_driver']
        
        from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
        
        mqtt_driver = Esp8266MQTTDriver(
            client_id="test_client",
            server="test.broker.com"
        )
        
        result = mqtt_driver.connect()
        
        assert result is False
        assert mqtt_driver.connected is False
        assert mqtt_driver.client is None


def test_esp8266_mqtt_driver_connect_with_existing_subscriptions():
    mock_mqtt_client = Mock()
    mock_umqtt = MagicMock()
    mock_umqtt.simple.MQTTClient.return_value = mock_mqtt_client
    
    with patch.dict(sys.modules, {'umqtt.simple': mock_umqtt.simple, 'umqtt': mock_umqtt}):
        if 'src.driver.mqtt_driver.esp8266_mqtt_driver' in sys.modules:
            del sys.modules['src.driver.mqtt_driver.esp8266_mqtt_driver']
        
        from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
        
        mqtt_driver = Esp8266MQTTDriver(
            client_id="test_client",
            server="test.broker.com"
        )
        
        mqtt_driver.subscriptions = {"topic1": None, "topic2": None}
        
        result = mqtt_driver.connect()
        
        assert result is True
        assert mock_mqtt_client.subscribe.call_count == 2
        mock_mqtt_client.subscribe.assert_any_call("topic1")
        mock_mqtt_client.subscribe.assert_any_call("topic2")


def test_esp8266_mqtt_driver_disconnect():
    mock_mqtt_client = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    mqtt_driver.disconnect()
    
    assert mqtt_driver.connected is False
    assert mqtt_driver.client is None
    mock_mqtt_client.disconnect.assert_called_once()


def test_esp8266_mqtt_driver_disconnect_with_error():
    mock_mqtt_client = Mock()
    mock_mqtt_client.disconnect.side_effect = Exception("Disconnect failed")
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    mqtt_driver.disconnect()
    
    assert mqtt_driver.connected is False
    assert mqtt_driver.client is None


def test_esp8266_mqtt_driver_publish():
    mock_mqtt_client = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.publish("test/topic", "test message", retain=True)
    
    assert result is True
    mock_mqtt_client.publish.assert_called_once_with("test/topic", "test message", retain=True)


def test_esp8266_mqtt_driver_publish_not_connected():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    with pytest.raises(Exception, match="Not connected to MQTT broker"):
        mqtt_driver.publish("test/topic", "test message")


def test_esp8266_mqtt_driver_publish_failure():
    mock_mqtt_client = Mock()
    mock_mqtt_client.publish.side_effect = Exception("Publish failed")
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    with pytest.raises(Exception, match="Publish failed"):
        mqtt_driver.publish("test/topic", "test message")


def test_esp8266_mqtt_driver_subscribe():
    mock_mqtt_client = Mock()
    mock_callback = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.subscribe("test/topic", mock_callback)
    
    assert result is True
    assert "test/topic" in mqtt_driver.subscriptions
    assert mqtt_driver.subscriptions["test/topic"] == mock_callback
    mock_mqtt_client.subscribe.assert_called_once_with("test/topic")


def test_esp8266_mqtt_driver_subscribe_not_connected():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    with pytest.raises(Exception, match="Not connected to MQTT broker"):
        mqtt_driver.subscribe("test/topic")


def test_esp8266_mqtt_driver_unsubscribe():
    mock_mqtt_client = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    mqtt_driver.subscriptions["test/topic"] = Mock()
    
    result = mqtt_driver.unsubscribe("test/topic")
    
    assert result is True
    assert "test/topic" not in mqtt_driver.subscriptions
    mock_mqtt_client.unsubscribe.assert_called_once_with("test/topic")


def test_esp8266_mqtt_driver_on_message():
    mock_callback = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.subscriptions["test/topic"] = mock_callback
    
    mqtt_driver._on_message(b"test/topic", b"test message")
    
    mock_callback.assert_called_once_with("test/topic", "test message")


def test_esp8266_mqtt_driver_on_message_string_input():
    mock_callback = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.subscriptions["test/topic"] = mock_callback
    
    mqtt_driver._on_message("test/topic", "test message")
    
    mock_callback.assert_called_once_with("test/topic", "test message")


def test_esp8266_mqtt_driver_on_message_no_callback():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.subscriptions["test/topic"] = None
    
    mqtt_driver._on_message("test/topic", "test message")


def test_esp8266_mqtt_driver_on_message_callback_error():
    mock_callback = Mock()
    mock_callback.side_effect = Exception("Callback error")
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.subscriptions["test/topic"] = mock_callback
    
    mqtt_driver._on_message("test/topic", "test message")


def test_esp8266_mqtt_driver_is_connected():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    assert mqtt_driver.is_connected() is False
    
    mqtt_driver.connected = True
    mqtt_driver.client = Mock()
    
    assert mqtt_driver.is_connected() is True


def test_esp8266_mqtt_driver_check_messages():
    mock_mqtt_client = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.check_messages()
    
    assert result is True
    mock_mqtt_client.check_msg.assert_called_once()


def test_esp8266_mqtt_driver_check_messages_not_connected():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    result = mqtt_driver.check_messages()
    
    assert result is False


def test_esp8266_mqtt_driver_check_messages_error():
    mock_mqtt_client = Mock()
    mock_mqtt_client.check_msg.side_effect = Exception("Check message error")
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.check_messages()
    
    assert result is False
    assert mqtt_driver.connected is False


def test_esp8266_mqtt_driver_wait_msg():
    mock_mqtt_client = Mock()
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.wait_msg()
    
    assert result is True
    mock_mqtt_client.wait_msg.assert_called_once()


def test_esp8266_mqtt_driver_wait_msg_not_connected():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    result = mqtt_driver.wait_msg()
    
    assert result is False


def test_esp8266_mqtt_driver_wait_msg_error():
    mock_mqtt_client = Mock()
    mock_mqtt_client.wait_msg.side_effect = Exception("Wait message error")
    
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    mqtt_driver.client = mock_mqtt_client
    mqtt_driver.connected = True
    
    result = mqtt_driver.wait_msg()
    
    assert result is False
    assert mqtt_driver.connected is False


def test_esp8266_mqtt_driver_get_client_info():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com",
        port=8883
    )
    
    mqtt_driver.connected = True
    mqtt_driver.subscriptions = {"topic1": None, "topic2": Mock()}
    
    info = mqtt_driver.get_client_info()
    
    expected_info = {
        "client_id": "test_client",
        "server": "test.broker.com",
        "port": "8883",
        "connected": "True",
        "subscriptions": ["topic1", "topic2"]
    }
    
    assert info == expected_info


@pytest.fixture
def mock_mqtt_success():
    mock_mqtt_client = Mock()
    mock_umqtt = MagicMock()
    mock_umqtt.simple.MQTTClient.return_value = mock_mqtt_client
    
    with patch.dict(sys.modules, {'umqtt.simple': mock_umqtt.simple, 'umqtt': mock_umqtt}):
        if 'src.driver.mqtt_driver.esp8266_mqtt_driver' in sys.modules:
            del sys.modules['src.driver.mqtt_driver.esp8266_mqtt_driver']
        
        yield {
            'mqtt_client': mock_mqtt_client,
            'umqtt': mock_umqtt
        }


def test_with_fixture(mock_mqtt_success):
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    result = mqtt_driver.connect()
    
    assert result is True
    assert mqtt_driver.connected is True
    mock_mqtt_success['mqtt_client'].connect.assert_called_once()
    
def test_esp8266_mqtt_driver_no_umqtt_module():
    from src.driver.mqtt_driver.esp8266_mqtt_driver import Esp8266MQTTDriver
    
    mqtt_driver = Esp8266MQTTDriver(
        client_id="test_client",
        server="test.broker.com"
    )
    
    result = mqtt_driver.connect()
    assert result is False
    assert mqtt_driver.connected is False
    assert mqtt_driver.client is None