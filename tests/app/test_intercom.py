import pytest
from unittest.mock import Mock, patch
from src.app.intercom import Intercom

import threading
import time
import sys


# Test 1: Basic loop execution with stop
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


# Test 2: Loop calls _process_cycle each iteration
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


# Test 3: Loop runs continuously in thread
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


# Test 4: Track start time when run begins
def test_run_tracks_start_time():
    intercom = Intercom()

    # Make _process_cycle stop immediately
    def mock_cycle():
        intercom.stop()

    intercom._process_cycle = mock_cycle

    with patch('time.time', return_value=1000.0):
        intercom.run()

    assert intercom.start_time == 1000.0


# Test 5: should_restart returns False when start_time is None
def test_should_restart_returns_false_when_not_started():
    intercom = Intercom(restart_after_seconds=10)

    assert intercom._should_restart() == False


# Test 6: should_restart returns True when uptime exceeds threshold
def test_should_restart_returns_true_when_uptime_exceeds_threshold():
    intercom = Intercom(restart_after_seconds=10)

    with patch('time.time', return_value=1000.0):
        intercom.start_time = 1000.0

    # 15 seconds later - should restart
    with patch('time.time', return_value=1015.0):
        assert intercom._should_restart() == True


# Test 7: should_restart returns False when uptime below threshold
def test_should_restart_returns_false_when_uptime_below_threshold():
    intercom = Intercom(restart_after_seconds=10)

    with patch('time.time', return_value=1000.0):
        intercom.start_time = 1000.0

    # 5 seconds later - should NOT restart
    with patch('time.time', return_value=1005.0):
        assert intercom._should_restart() == False


# Test 8: Loop stops when restart threshold is reached
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


# Test 9: Calls machine.reset() when threshold reached
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


# Test 10: Restart immediately when restart_after_seconds is 0
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


# Test 11: Handles ImportError when machine module not available
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


# Test 12: Default restart_after_seconds is 2 days
def test_default_restart_after_seconds_is_two_days():
    intercom = Intercom()

    assert intercom.restart_after_seconds == 172800  # 2 days in seconds


# ========== CALL DETECTION TESTS ==========

# Test 13: Call detection ignores when no call detected
def test_process_call_detection_ignores_no_call():
    intercom = Intercom()
    intercom.gpio_driver.detect_call = Mock(return_value=False)
    intercom.mqtt_driver.is_connected = Mock(return_value=True)
    intercom.mqtt_driver.publish = Mock()

    with patch('time.time', return_value=1000.0):
        intercom._process_call_detection()

    # Should not publish anything
    intercom.mqtt_driver.publish.assert_not_called()


# Test 14: Call detection only triggers on rising edge (False -> True)
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


# Test 15: Call detection debouncing prevents rapid calls
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


# Test 16: Call detection publishes after debounce period expires
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

# Test 17: Auto-unlock executes when enabled and call detected
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


# Test 18: Auto-unlock does not execute when disabled
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


# Test 19: Unlock sequence executes correct GPIO operations
def test_unlock_sequence_executes_gpio_operations():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock()
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.helper.sleep.sleep'):  # Mock sleep to speed up test
        intercom._execute_unlock_sequence()

    # Verify sequence
    intercom.gpio_driver.open_conversation.assert_called_once()
    intercom.gpio_driver.unlock.assert_called_once()
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


# Test 20: Unlock sequence handles exceptions and locks door
def test_unlock_sequence_handles_exception_and_locks_door():
    intercom = Intercom()
    intercom.gpio_driver.open_conversation = Mock()
    intercom.gpio_driver.unlock = Mock(side_effect=Exception("GPIO error"))
    intercom.gpio_driver.close_conversation = Mock()
    intercom.gpio_driver.lock = Mock()

    with patch('src.helper.sleep.sleep'):
        intercom._execute_unlock_sequence()

    # Should attempt to lock even after error
    intercom.gpio_driver.close_conversation.assert_called_once()
    intercom.gpio_driver.lock.assert_called_once()


# ========== MANUAL UNLOCK TESTS ==========

# Test 21: Manual unlock message triggers unlock sequence
def test_manual_unlock_message_triggers_unlock():
    intercom = Intercom()
    intercom._execute_unlock_sequence = Mock()

    # Simulate receiving correct unlock message
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'open'):
        intercom._handle_unlock_message('test/topic', 'open')

    intercom._execute_unlock_sequence.assert_called_once()


# Test 22: Invalid unlock message does not trigger unlock
def test_invalid_unlock_message_ignored():
    intercom = Intercom()
    intercom._execute_unlock_sequence = Mock()

    # Simulate receiving incorrect message
    with patch('src.config.DOOR_UNLOCKED_MESSAGE', 'open'):
        intercom._handle_unlock_message('test/topic', 'wrong_message')

    intercom._execute_unlock_sequence.assert_not_called()


# ========== MQTT CONFIG TESTS ==========

# Test 23: Config message updates auto_unlock setting
def test_config_message_updates_auto_unlock():
    intercom = Intercom()

    config_json = '{"auto_unlock": true}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.auto_unlock == True


# Test 24: Config message updates restart_after_seconds
def test_config_message_updates_restart_after_seconds():
    intercom = Intercom()

    config_json = '{"restart_after_seconds": 86400}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.restart_after_seconds == 86400


# Test 25: Config message handles both settings
def test_config_message_updates_both_settings():
    intercom = Intercom()

    config_json = '{"auto_unlock": true, "restart_after_seconds": 3600}'
    intercom._handle_config_message('config/topic', config_json)

    assert intercom.auto_unlock == True
    assert intercom.restart_after_seconds == 3600


# Test 26: Config message handles invalid JSON gracefully
def test_config_message_handles_invalid_json():
    intercom = Intercom()
    original_auto_unlock = intercom.auto_unlock

    # Send invalid JSON
    intercom._handle_config_message('config/topic', 'not valid json {')

    # Should not crash, settings should remain unchanged
    assert intercom.auto_unlock == original_auto_unlock


# ========== EXCEPTION HANDLING TESTS ==========

# Test 27: Exception in main loop is caught and loop continues
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
    intercom.run()

    assert exception_raised == True
    assert call_count == 2  # Ran twice despite exception


# Test 28: Multiple exceptions don't prevent operation
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

    with patch('src.helper.sleep.sleep'):  # Speed up test
        intercom.run()

    # Should have handled 2 exceptions and continued to 3rd call
    assert call_count == 3

