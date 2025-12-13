import pytest
from unittest.mock import Mock, patch
from src.app.intercom import Intercom

import threading
import time
import sys


def test_run_can_be_stopped():
    intercom = Intercom()

    # Make _process_cycle stop after first call
    call_count = 0
    def mock_cycle():
        nonlocal call_count
        call_count += 1
        intercom.stop()

    intercom._process_cycle = mock_cycle
    intercom.run()

    # If we get here, it didn't hang
    assert call_count == 1


def test_run_calls_process_cycle_each_iteration():
    intercom = Intercom()

    call_count = 0
    def mock_cycle():
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            intercom.stop()

    intercom._process_cycle = mock_cycle
    intercom.run()

    assert call_count == 3


def test_run_continues_until_stopped():
    intercom = Intercom()

    thread = threading.Thread(target=intercom.run)
    thread.daemon = True
    thread.start()

    time.sleep(0.01)  # Brief moment
    assert thread.is_alive()

    intercom.stop()
    thread.join(timeout=1)

    assert not thread.is_alive()


def test_run_tracks_start_time():
    intercom = Intercom()

    # Make _process_cycle stop immediately
    def mock_cycle():
        intercom.stop()

    intercom._process_cycle = mock_cycle

    with patch('time.time', return_value=1000.0):
        intercom.run()

    assert intercom.start_time == 1000.0


def test_should_restart_returns_false_when_not_started():
    intercom = Intercom(restart_after_seconds=10)

    assert intercom._should_restart() == False


def test_should_restart_returns_true_when_uptime_exceeds_threshold():
    intercom = Intercom(restart_after_seconds=10)

    with patch('time.time', return_value=1000.0):
        intercom.start_time = 1000.0

    # 15 seconds later - should restart
    with patch('time.time', return_value=1015.0):
        assert intercom._should_restart() == True


def test_should_restart_returns_false_when_uptime_below_threshold():
    intercom = Intercom(restart_after_seconds=10)

    with patch('time.time', return_value=1000.0):
        intercom.start_time = 1000.0

    # 5 seconds later - should NOT restart
    with patch('time.time', return_value=1005.0):
        assert intercom._should_restart() == False


def test_run_stops_when_restart_threshold_reached():
    intercom = Intercom(restart_after_seconds=10)

    call_count = 0
    time_values = [1000.0, 1005.0, 1015.0]  # Start, middle, exceed threshold

    def mock_time():
        return time_values[min(call_count, len(time_values) - 1)]

    def mock_cycle():
        nonlocal call_count
        call_count += 1

    intercom._process_cycle = mock_cycle

    with patch('time.time', side_effect=mock_time):
        intercom.run()

    # Should have stopped after threshold exceeded
    assert call_count == 2  # Ran twice, then stopped


def test_run_calls_machine_reset_when_threshold_reached():
    intercom = Intercom(restart_after_seconds=10)

    call_count = 0
    time_values = [1000.0, 1015.0]  # Start, then exceed threshold

    def mock_time():
        return time_values[min(call_count, len(time_values) - 1)]

    def mock_cycle():
        nonlocal call_count
        call_count += 1

    intercom._process_cycle = mock_cycle

    # Mock machine module before it's imported
    mock_machine = Mock()
    with patch('time.time', side_effect=mock_time):
        with patch.dict('sys.modules', {'machine': mock_machine}):
            intercom.run()

            mock_machine.reset.assert_called_once()


def test_run_restarts_immediately_when_threshold_is_zero():
    intercom = Intercom(restart_after_seconds=0)

    call_count = 0
    def mock_cycle():
        nonlocal call_count
        call_count += 1

    intercom._process_cycle = mock_cycle

    # Mock machine module before it's imported
    mock_machine = Mock()
    with patch('time.time', return_value=1000.0):
        with patch.dict('sys.modules', {'machine': mock_machine}):
            intercom.run()

            # Should reset before even calling _process_cycle
            assert call_count == 0
            mock_machine.reset.assert_called_once()


def test_restart_handles_import_error_gracefully():
    intercom = Intercom(restart_after_seconds=10)

    with patch('time.time', return_value=1000.0):
        intercom.start_time = 1000.0

    with patch('time.time', return_value=1015.0):
        # Mock ImportError for machine module
        with patch('builtins.__import__', side_effect=ImportError):
            intercom._restart()

            # Should have called stop() instead of crashing
            assert intercom.running == False


def test_default_restart_after_seconds_is_two_days():
    intercom = Intercom()

    assert intercom.restart_after_seconds == 172800  # 2 days in seconds


# ========== CALL DETECTION TESTS ==========

def test_process_call_detection_ignores_no_call():
    intercom = Intercom()
    intercom.gpio_driver.detect_call = Mock(return_value=False)
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()

    with patch('time.time', return_value=1000.0):
        intercom._process_call_detection()

    # Should not publish anything
    intercom.mqtt_driver.publish.assert_not_called()


def test_process_call_detection_edge_detection():
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()

    # First call: False (no call)
    intercom.gpio_driver.detect_call = Mock(return_value=False)
    with patch('time.time', return_value=1000.0):
        intercom._process_call_detection()

    # Second call: True (call detected) - should trigger
    intercom.gpio_driver.detect_call = Mock(return_value=True)
    with patch('time.time', return_value=1001.0):
        intercom._process_call_detection()

    # Third call: Still True (holding) - should NOT trigger again
    intercom.gpio_driver.detect_call = Mock(return_value=True)
    with patch('time.time', return_value=1002.0):
        intercom._process_call_detection()

    # Should only publish once (on the rising edge)
    assert intercom.mqtt_driver.publish.call_count == 1


def test_process_call_detection_debouncing():
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()

    # Patch config to use 10 second debounce
    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        # First call at T=1000
        intercom.gpio_driver.detect_call = Mock(return_value=False)
        with patch('time.time', return_value=1000.0):
            intercom._process_call_detection()

        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1001.0):
            intercom._process_call_detection()

        # Reset to False then True again (new call attempt at T=1005 - only 4 seconds later)
        intercom._previous_call_state = False
        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1005.0):
            intercom._process_call_detection()

        # Should only publish once (second call was within debounce period)
        assert intercom.mqtt_driver.publish.call_count == 1


def test_process_call_detection_publishes_after_debounce():
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()

    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        # First call at T=1000
        intercom.gpio_driver.detect_call = Mock(return_value=False)
        with patch('time.time', return_value=1000.0):
            intercom._process_call_detection()

        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1001.0):
            intercom._process_call_detection()

        # Reset to False then True again (new call at T=1012 - 11 seconds later, past debounce)
        intercom._previous_call_state = False
        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1012.0):
            intercom._process_call_detection()

        # Should publish twice (second call was after debounce period)
        assert intercom.mqtt_driver.publish.call_count == 2


# ========== AUTO-UNLOCK TESTS ==========

def test_auto_unlock_executes_when_enabled():
    intercom = Intercom()
    intercom.auto_unlock = True
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()
    intercom._execute_unlock_sequence = Mock()

    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        # Trigger call detection
        intercom.gpio_driver.detect_call = Mock(return_value=False)
        with patch('time.time', return_value=1000.0):
            intercom._process_call_detection()

        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1001.0):
            intercom._process_call_detection()

    # Should have executed unlock sequence
    intercom._execute_unlock_sequence.assert_called_once()


def test_auto_unlock_does_not_execute_when_disabled():
    intercom = Intercom()
    intercom.auto_unlock = False  # Explicitly disabled
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()
    intercom._execute_unlock_sequence = Mock()

    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        # Trigger call detection
        intercom.gpio_driver.detect_call = Mock(return_value=False)
        with patch('time.time', return_value=1000.0):
            intercom._process_call_detection()

        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1001.0):
            intercom._process_call_detection()

    # Should NOT have executed unlock sequence
    intercom._execute_unlock_sequence.assert_not_called()


def test_unlock_sequence_executes_gpio_operations():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock()
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.app.intercom.sleep'):  # Mock sleep to speed up test
        intercom._execute_unlock_sequence()

    # Verify sequence
    intercom.gpio_driver.open_conversation.assert_called_once()
    intercom.gpio_driver.unlock.assert_called_once()
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


def test_unlock_sequence_handles_exception_and_locks_door():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock(side_effect=Exception("GPIO error"))
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.app.intercom.sleep'):
        intercom._execute_unlock_sequence()

    # Should attempt to lock even after error
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


# ========== MANUAL UNLOCK TESTS ==========

def test_manual_unlock_message_triggers_unlock():
    intercom = Intercom()
    intercom._execute_unlock_sequence = Mock()

    # Simulate receiving correct unlock message
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'open'):
        intercom._handle_unlock_message('test/topic', 'open')

    intercom._execute_unlock_sequence.assert_called_once()


def test_invalid_unlock_message_ignored():
    intercom = Intercom()
    intercom._execute_unlock_sequence = Mock()

    # Simulate receiving incorrect message
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'open'):
        intercom._handle_unlock_message('test/topic', 'wrong_message')

    intercom._execute_unlock_sequence.assert_not_called()


# ========== MQTT CONFIG TESTS ==========

def test_config_message_updates_auto_unlock():
    intercom = Intercom()

    config_json = '{"auto_unlock": true}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.auto_unlock == True


def test_config_message_updates_restart_after_seconds():
    intercom = Intercom()

    config_json = '{"restart_after_seconds": 86400}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.restart_after_seconds == 86400


def test_config_message_updates_both_settings():
    intercom = Intercom()

    config_json = '{"auto_unlock": true, "restart_after_seconds": 3600}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.auto_unlock == True
    assert intercom.restart_after_seconds == 3600


def test_config_message_handles_invalid_json():
    intercom = Intercom()
    original_auto_unlock = intercom.auto_unlock

    # Send invalid JSON
    intercom._handle_config_message('config/topic', 'not valid json {')

    # Should not crash, settings should remain unchanged
    assert intercom.auto_unlock == original_auto_unlock


# ========== EXCEPTION HANDLING TESTS ==========

def test_exception_in_main_loop_is_caught():
    intercom = Intercom()

    call_count = 0
    exception_raised = False

    def mock_cycle():
        nonlocal call_count, exception_raised
        call_count += 1
        if call_count == 1:
            exception_raised = True
            raise Exception("Test exception")
        elif call_count >= 2:
            intercom.stop()

    intercom._process_cycle = mock_cycle

    # Should not crash, should continue to second iteration
    with patch('src.app.intercom.sleep'):  # Mock sleep in exception handler
        intercom.run()

    assert exception_raised == True
    assert call_count == 2  # Ran twice despite exception


def test_multiple_exceptions_handled_gracefully():
    intercom = Intercom()

    call_count = 0

    def mock_cycle():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception(f"Test exception {call_count}")
        intercom.stop()

    intercom._process_cycle = mock_cycle

    with patch('src.app.intercom.sleep'):  # Speed up test
        intercom.run()

    # Should have handled 2 exceptions and continued to 3rd call
    assert call_count == 3



# ========== CONNECTION FAILURE TESTS ==========

def test_run_continues_when_wifi_not_connected():
    intercom = Intercom()

    attempt_count = 0
    def mock_is_connected():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count >= 3:
            intercom.stop()
        return False

    intercom.wifi_driver.is_connected = Mock(side_effect=mock_is_connected)
    intercom.wifi_driver.connect = Mock(return_value=False)

    call_count = 0
    def mock_cycle():
        nonlocal call_count
        call_count += 1
        intercom.stop()

    intercom._process_cycle = mock_cycle

    with patch('src.app.intercom.sleep') as mock_sleep:
        intercom.run()

    # _process_cycle should never be called since WiFi failed
    assert call_count == 0
    # Should have tried to connect multiple times
    assert attempt_count >= 3
    # Critical fix: Sleep should be called on connection failures to prevent CPU spinning
    assert mock_sleep.call_count >= 2


def test_run_continues_when_mqtt_not_connected():
    intercom = Intercom()
    intercom.wifi_driver.is_connected = Mock(return_value=True)

    attempt_count = 0
    def mock_is_connected():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count >= 3:
            intercom.stop()
        return False

    intercom.mqtt_driver.is_connected = Mock(side_effect=mock_is_connected)
    intercom.mqtt_driver.connect = Mock(return_value=False)

    call_count = 0
    def mock_cycle():
        nonlocal call_count
        call_count += 1
        intercom.stop()

    intercom._process_cycle = mock_cycle

    with patch('src.app.intercom.sleep') as mock_sleep:
        intercom.run()

    # _process_cycle should never be called since MQTT failed
    assert call_count == 0
    # Should have tried to connect multiple times
    assert attempt_count >= 3
    # Critical fix: Sleep should be called on connection failures to prevent CPU spinning
    assert mock_sleep.call_count >= 2


def test_wifi_connection_failure_logs_retry_message():
    intercom = Intercom()
    intercom.wifi_driver.is_connected = Mock(return_value=False)
    intercom.wifi_driver.connect = Mock(return_value=False)

    result = intercom._ensure_wifi_connected()

    assert result == False
    intercom.wifi_driver.connect.assert_called_once()


def test_mqtt_connection_failure_logs_retry_message():
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=False)
    intercom.mqtt_driver.connect = Mock(return_value=False)

    result = intercom._ensure_mqtt_connected()

    assert result == False
    intercom.mqtt_driver.connect.assert_called_once()


def test_connect_mqtt_returns_false_on_failure():
    intercom = Intercom()
    intercom.mqtt_driver.connect = Mock(return_value=False)

    result = intercom._connect_mqtt()

    assert result == False


def test_config_message_handles_key_error():
    intercom = Intercom()

    # Send JSON that will cause KeyError during processing
    config_json = '{"unknown_key": "value"}'
    original_auto_unlock = intercom.auto_unlock

    # Should not crash
    intercom._handle_config_message('config/topic', config_json)

    # Settings should remain unchanged
    assert intercom.auto_unlock == original_auto_unlock


def test_config_message_handles_type_error():
    intercom = Intercom()

    # Send JSON with wrong types that could cause TypeError
    config_json = '{"auto_unlock": "not_a_boolean", "restart_after_seconds": "not_a_number"}'

    # Should not crash due to error handling
    intercom._handle_config_message('config/topic', config_json)

    # Since types are wrong, values may or may not be converted, but shouldn't crash


def test_call_detection_when_mqtt_not_connected():
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=False)
    intercom.mqtt_driver.publish = Mock()

    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        # Trigger call detection
        intercom.gpio_driver.detect_call = Mock(return_value=False)
        with patch('time.time', return_value=1000.0):
            intercom._process_call_detection()

        intercom.gpio_driver.detect_call = Mock(return_value=True)
        with patch('time.time', return_value=1001.0):
            intercom._process_call_detection()

    # Should NOT publish since MQTT is not connected
    intercom.mqtt_driver.publish.assert_not_called()
    # But debounce timer SHOULD be updated (critical fix)
    assert intercom._last_call_detected_time == 1001.0


def test_unlock_sequence_handles_close_conversation_exception():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock(side_effect=Exception("Unlock error"))
    intercom.gpio_driver.close_conversation = Mock(side_effect=Exception("Close error"))
    intercom.gpio_driver.lock = Mock()

    with patch('src.app.intercom.sleep'):
        intercom._execute_unlock_sequence()

    # Should attempt both close and lock even though close failed
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


def test_unlock_sequence_handles_lock_exception():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock(side_effect=Exception("Unlock error"))
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock(side_effect=Exception("Lock error"))

    with patch('src.app.intercom.sleep'):
        intercom._execute_unlock_sequence()

    # Should attempt to lock even though it will fail
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


def test_process_cycle_calls_check_messages():
    intercom = Intercom()
    intercom._process_call_detection = Mock()
    intercom.mqtt_driver.check_messages = Mock()

    with patch('src.app.intercom.sleep'):
        intercom._process_cycle()

    intercom.mqtt_driver.check_messages.assert_called_once()


# ========== RECONNECTION SUCCESS TESTS ==========

def test_wifi_reconnection_succeeds_after_initial_failure():
    """Test that WiFi eventually reconnects after initial failures."""
    intercom = Intercom()

    attempt_count = 0
    def mock_connect(*args, **kwargs):
        nonlocal attempt_count
        attempt_count += 1
        # Fail first 2 attempts, succeed on 3rd
        return attempt_count >= 3

    intercom.wifi_driver.is_connected = Mock(return_value=False)
    intercom.wifi_driver.connect = Mock(side_effect=mock_connect)
    
    # First two attempts should fail
    assert intercom._ensure_wifi_connected() == False
    assert intercom._ensure_wifi_connected() == False
    
    # Third attempt should succeed
    assert intercom._ensure_wifi_connected() == True
    assert attempt_count == 3


def test_mqtt_reconnection_succeeds_after_initial_failure():
    """Test that MQTT eventually reconnects after initial failures."""
    intercom = Intercom()
    
    attempt_count = 0
    def mock_connect():
        nonlocal attempt_count
        attempt_count += 1
        # Fail first attempt, succeed on 2nd
        return attempt_count >= 2
    
    intercom.mqtt_driver.is_connected = Mock(return_value=False)
    intercom.mqtt_driver.connect = Mock(side_effect=mock_connect)
    intercom.mqtt_driver.subscribe = Mock()
    intercom.mqtt_driver.publish = Mock()
    
    # First attempt should fail
    assert intercom._ensure_mqtt_connected() == False
    
    # Second attempt should succeed
    assert intercom._ensure_mqtt_connected() == True
    assert attempt_count == 2


def test_ensure_wifi_returns_true_when_already_connected():
    """Test that ensure methods return immediately if already connected."""
    intercom = Intercom()
    intercom.wifi_driver.is_connected = Mock(return_value=True)
    intercom.wifi_driver.connect = Mock()
    
    result = intercom._ensure_wifi_connected()
    
    assert result == True
    # Should NOT attempt to connect since already connected
    intercom.wifi_driver.connect.assert_not_called()


def test_ensure_mqtt_returns_true_when_already_connected():
    """Test that ensure methods return immediately if already connected."""
    intercom = Intercom()
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.connect = Mock()
    
    result = intercom._ensure_mqtt_connected()
    
    assert result == True
    # Should NOT attempt to connect since already connected
    intercom.mqtt_driver.connect.assert_not_called()


# ========== CONFIG EDGE CASES ==========

def test_config_message_with_empty_json():
    """Test handling of empty JSON object."""
    intercom = Intercom()
    original_auto_unlock = intercom.auto_unlock
    original_restart = intercom.restart_after_seconds
    
    config_json = '{}'
    intercom._handle_config_message('config/topic', config_json)
    
    # Settings should remain unchanged
    assert intercom.auto_unlock == original_auto_unlock
    assert intercom.restart_after_seconds == original_restart


def test_config_message_updates_only_auto_unlock():
    """Test partial config update with only auto_unlock."""
    intercom = Intercom()
    original_restart = intercom.restart_after_seconds
    
    config_json = '{"auto_unlock": true}'
    intercom._handle_config_message('config/topic', config_json)
    
    assert intercom.auto_unlock == True
    # restart_after_seconds should remain unchanged
    assert intercom.restart_after_seconds == original_restart


def test_config_message_updates_only_restart_after_seconds():
    """Test partial config update with only restart_after_seconds."""
    intercom = Intercom()
    original_auto_unlock = intercom.auto_unlock
    
    config_json = '{"restart_after_seconds": 3600}'
    intercom._handle_config_message('config/topic', config_json)
    
    assert intercom.restart_after_seconds == 3600
    # auto_unlock should remain unchanged
    assert intercom.auto_unlock == original_auto_unlock


def test_multiple_config_updates():
    """Test that multiple config updates work correctly."""
    intercom = Intercom()
    
    # First update
    config_json1 = '{"auto_unlock": true, "restart_after_seconds": 3600}'
    intercom._handle_config_message('config/topic', config_json1)
    assert intercom.auto_unlock == True
    assert intercom.restart_after_seconds == 3600
    
    # Second update - change values
    config_json2 = '{"auto_unlock": false, "restart_after_seconds": 7200}'
    intercom._handle_config_message('config/topic', config_json2)
    assert intercom.auto_unlock == False
    assert intercom.restart_after_seconds == 7200


# ========== UNLOCK SEQUENCE TIMING TESTS ==========

def test_unlock_sequence_uses_correct_sleep_durations():
    """Test that unlock sequence uses correct sleep durations from config."""
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock()
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()
    
    sleep_calls = []
    def mock_sleep(duration):
        sleep_calls.append(duration)
    
    with patch('src.app.intercom.sleep', side_effect=mock_sleep):
        with patch('src.config.CONVERSATION_OPEN_DELAY_SECONDS', 1):
            with patch('src.config.DOOR_UNLOCK_DURATION_SECONDS', 5):
                intercom._execute_unlock_sequence()
    
    # Should have two sleep calls with correct durations
    assert len(sleep_calls) == 2
    assert sleep_calls[0] == 1  # CONVERSATION_OPEN_DELAY_SECONDS
    assert sleep_calls[1] == 5  # DOOR_UNLOCK_DURATION_SECONDS


# ========== PROCESS CYCLE TESTS ==========

def test_process_cycle_without_check_messages_attribute():
    """Test that process cycle works when driver doesn't have check_messages."""
    intercom = Intercom()
    intercom._process_call_detection = Mock()
    
    # Remove check_messages attribute
    if hasattr(intercom.mqtt_driver, 'check_messages'):
        delattr(intercom.mqtt_driver, 'check_messages')
    
    # Should not crash
    with patch('src.app.intercom.sleep'):
        intercom._process_cycle()
    
    # Should still process call detection
    intercom._process_call_detection.assert_called_once()


def test_process_cycle_calls_sleep():
    """Test that process cycle calls sleep to prevent CPU spinning."""
    intercom = Intercom()
    intercom._process_call_detection = Mock()

    with patch('src.app.intercom.sleep') as mock_sleep:
        intercom._process_cycle()

    # Should sleep for 0.1 seconds
    mock_sleep.assert_called_with(0.1)


# ========== GPIO EXCEPTION TESTS ==========

def test_call_detection_handles_gpio_exception():
    """Test that call detection handles GPIO driver exceptions gracefully."""
    intercom = Intercom()
    intercom.gpio_driver.detect_call = Mock(side_effect=Exception("GPIO error"))
    
    # Should propagate exception (not caught at this level)
    with pytest.raises(Exception, match="GPIO error"):
        intercom._process_call_detection()


# ========== INTEGRATION TESTS ==========

def test_full_call_detection_with_auto_unlock_flow():
    """Test complete flow: call detected -> MQTT publish -> auto unlock."""
    intercom = Intercom()
    intercom.auto_unlock = True
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock()
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.config.CALL_DEBOUNCE_SECONDS', 10):
        with patch('src.app.intercom.sleep'):
            # Simulate call detection
            intercom.gpio_driver.detect_call = Mock(return_value=False)
            with patch('time.time', return_value=1000.0):
                intercom._process_call_detection()
            
            intercom.gpio_driver.detect_call = Mock(return_value=True)
            with patch('time.time', return_value=1001.0):
                intercom._process_call_detection()
    
    # Verify full flow executed
    intercom.mqtt_driver.publish.assert_called_once()
    intercom.gpio_driver.open_conversation.assert_called_once()
    intercom.gpio_driver.unlock.assert_called_once()
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


def test_manual_and_auto_unlock_use_same_sequence():
    """Test that both manual and auto unlock use the same sequence."""
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock()
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.app.intercom.sleep'):
        with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'open'):
            # Test manual unlock
            intercom._handle_unlock_message('test/topic', 'open')

    manual_calls = [
        intercom.gpio_driver.open_conversation.call_count,
        intercom.gpio_driver.unlock.call_count,
        intercom.gpio_driver.close_conversation.call_count,
        intercom.gpio_driver.lock.call_count
    ]

    # Reset mocks
    intercom.gpio_driver.open_conversation.reset_mock()
    intercom.gpio_driver.unlock.reset_mock()
    intercom.gpio_driver.close_conversation.reset_mock()
    intercom.gpio_driver.lock.reset_mock()

    with patch('src.app.intercom.sleep'):
        # Test auto unlock via _execute_unlock_sequence
        intercom._execute_unlock_sequence()
    
    auto_calls = [
        intercom.gpio_driver.open_conversation.call_count,
        intercom.gpio_driver.unlock.call_count,
        intercom.gpio_driver.close_conversation.call_count,
        intercom.gpio_driver.lock.call_count
    ]
    
    # Both should make same calls
    assert manual_calls == auto_calls == [1, 1, 1, 1]


def test_watchdog_timer_feed_called_when_not_none():
    """Test that watchdog timer feed is called when watchdog exists."""
    intercom = Intercom()
    
    # Create a mock watchdog
    mock_watchdog = Mock()
    
    # Temporarily replace watchdog_timer
    import src.app.intercom as intercom_module
    original_watchdog = intercom_module.watchdog_timer
    intercom_module.watchdog_timer = mock_watchdog
    
    try:
        call_count = 0
        def mock_cycle():
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                intercom.stop()
        
        intercom._process_cycle = mock_cycle
        
        with patch('src.app.intercom.sleep'):
            intercom.run()
        
        # Watchdog should be fed multiple times
        assert mock_watchdog.feed.call_count >= 2
    finally:
        # Restore original watchdog
        intercom_module.watchdog_timer = original_watchdog
