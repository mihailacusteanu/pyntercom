import time
import src.config as config
import sys
from typing import TYPE_CHECKING
from src.helper.sleep import sleep

if TYPE_CHECKING:
    from typing import Optional
    from src.interfaces.gpio_driver import GPIODriverInterface
    from src.interfaces.wifi_driver import WifiDriverInterface
    from src.interfaces.mqtt_driver import MqttDriverInterface

try:
    if sys.platform == "esp8266":
        from machine import WDT

        watchdog_timer = WDT(timeout=20000)
    else:
        watchdog_timer = None
except ImportError:
    print("machine library not available, you're probably not on an ESP")
    watchdog_timer = None


class Intercom:
    """Redesigned smart intercom system controller for ESP8266.

    This is a complete redesign of the intercom system with improved architecture:

    Architecture Improvements:
    - Driver-based connection state checking (eliminates stale connection flags)
    - Type hints throughout for better code quality and IDE support
    - Clean stop() mechanism for testing without test_mode parameters
    - Configurable timing values via config module
    - Better separation of concerns and testability

    Key Features:
    - Automatic restart after configurable uptime (default 2 days)
    - Watchdog timer support for ESP8266 hardware safety
    - Dynamic MQTT configuration (JSON-based auto_unlock and restart settings)
    - Call detection with edge detection and debouncing
    - Auto-unlock on call detection (configurable via MQTT)
    - Manual unlock via MQTT messages from Home Assistant
    - Comprehensive exception handling for graceful error recovery
    - CPU-efficient main loop with proper sleep intervals

    Connection Management:
    - Uses driver's is_connected() for real-time connection state (no stale flags)
    - Automatic WiFi/MQTT reconnection with retry logic
    - Graceful handling of connection drops during operation

    Configuration via MQTT:
    Accepts JSON configuration messages on CONFIGS_TOPIC:
    {
        "auto_unlock": true,           // Enable automatic door unlock on call
        "restart_after_seconds": 172800 // Uptime threshold for automatic restart
    }
    """

    def __init__(self, restart_after_seconds: int = 172800, ota_callback=None) -> None:
        self.running: bool = False
        self.start_time: Optional[float] = None
        self.restart_after_seconds: int = restart_after_seconds
        self.auto_unlock: bool = False
        self._last_call_detected_time: float = 0
        self._previous_call_state: bool = False
        self.ota_callback = ota_callback  # Optional callback for OTA trigger

        print("Loading the drivers")
        from src.driver.driver_manager import DriverManager

        driver_manager = DriverManager()

        self.gpio_driver: GPIODriverInterface = driver_manager.load_gpio_driver()
        self.wifi_driver: WifiDriverInterface = driver_manager.load_wifi_driver()
        self.mqtt_driver: MqttDriverInterface = driver_manager.load_mqtt_driver()

    def run(self) -> None:
        """Start the main intercom control loop.

        This is the primary entry point for running the intercom system.
        It handles WiFi/MQTT connections, automatic restart, call detection,
        and message processing in an infinite loop until stopped.

        Features:
        - Automatic restart after configurable uptime (default 2 days)
        - Continuous WiFi/MQTT connection monitoring with auto-reconnection
        - Call detection with edge detection and 10-second debouncing
        - Auto-unlock on call detection (if configured via MQTT)
        - Manual unlock via MQTT messages
        - Watchdog timer feeding (ESP8266 only)
        - Exception handling for graceful error recovery

        The loop can be stopped by calling stop() or by reaching the restart threshold.
        """
        self.running = True
        self.start_time = time.time()

        while self.running:
            try:
                if self._should_restart():
                    self._restart()
                    # for testing purposes
                    break

                if not self._ensure_wifi_connected():
                    sleep(1)  # Prevent CPU spinning on connection failures
                    continue

                if not self._ensure_mqtt_connected():
                    sleep(1)  # Prevent CPU spinning on connection failures
                    continue

                if watchdog_timer is not None:
                    watchdog_timer.feed()
                self._process_cycle()

            except Exception as e:
                print(f"[{time.time()}] Error in main loop: {e}")
                # Continue running - the ensure methods will handle reconnection
                sleep(1)  # Brief pause before retrying to avoid rapid error loops

    def stop(self) -> None:
        self.running = False

    def _ensure_wifi_connected(self) -> bool:
        """Ensure WiFi connection is established.

        Checks current WiFi connection status and attempts to reconnect if disconnected.

        Returns:
            bool: True if connected (or connection successful), False otherwise
        """
        if self.wifi_driver.is_connected():
            return True

        print(f"[{time.time()}] WiFi not connected, attempting to connect...")
        if self._connect_wifi():
            return True

        print(f"[{time.time()}] WiFi connection failed, retrying...")
        return False

    def _ensure_mqtt_connected(self) -> bool:
        """Ensure MQTT connection is established.

        Checks current MQTT connection status and attempts to reconnect if disconnected.
        If reconnection is successful, topics are automatically subscribed in _connect_mqtt().

        Returns:
            bool: True if connected (or connection successful), False otherwise
        """
        if self.mqtt_driver.is_connected():
            return True

        print(f"[{time.time()}] MQTT not connected, attempting to connect...")
        if self._connect_mqtt():
            return True

        print(f"[{time.time()}] MQTT connection failed, retrying...")
        return False

    def _connect_wifi(self) -> bool:
        """Connect to WiFi network.

        Returns:
            bool: True if connection successful, False otherwise
        """
        print("Trying to connect to WIFI")
        return self.wifi_driver.connect(config.WIFI_SSID, config.WIFI_PASSWORD)

    def _connect_mqtt(self) -> bool:
        """Connect to MQTT broker and request configuration.

        Returns:
            bool: True if connection successful, False otherwise
        """
        print("connect to MQTT broker")
        if self.mqtt_driver.connect():
            print("subscribing to config topic")
            self.mqtt_driver.subscribe(
                config.CONFIGS_TOPIC, self._handle_config_message
            )
            print("subscribing to unlock topic")
            self.mqtt_driver.subscribe(config.UNLOCK_TOPIC, self._handle_unlock_message)

            # Subscribe to OTA topic if callback provided
            if self.ota_callback:
                print("subscribing to OTA topic")
                self.mqtt_driver.subscribe("pyntercom/ota", self.ota_callback)

            print("asking MQTT for the configs")
            self.mqtt_driver.publish(config.LOGS_TOPIC, "give_me_the_config")
            return True
        return False

    def _handle_config_message(self, topic: str, message: str) -> None:
        """Handle configuration messages received from MQTT.

        Expected JSON format:
        {
            "auto_unlock": true,
            "restart_after_seconds": 172800
        }
        """
        print(f"Received config on '{topic}': {message}")

        try:
            import json

            config_data = json.loads(message)

            # Update auto_unlock if present
            if "auto_unlock" in config_data:
                self.auto_unlock = bool(config_data["auto_unlock"])
                print(f"Config: auto_unlock set to {self.auto_unlock}")

            # Update restart_after_seconds if present
            if "restart_after_seconds" in config_data:
                self.restart_after_seconds = int(config_data["restart_after_seconds"])
                print(
                    f"Config: restart_after_seconds set to {self.restart_after_seconds} seconds"
                )

            print(f"Configuration updated successfully")

        except ValueError as e:
            print(f"Error parsing config JSON: {e}")
        except (KeyError, TypeError) as e:
            print(f"Error processing config data: {e}")

    def _handle_unlock_message(self, topic: str, message: str) -> None:
        """Handle door unlock messages from MQTT.

        Processes incoming MQTT messages for manual door unlocking.
        When a valid unlock message is received, executes the door unlock sequence.

        Args:
            topic (str): The MQTT topic the message was received on
            message (str): The message payload
        """
        print(
            f"[{time.time()}] Debug: Received unlock message on '{topic}': '{message}'"
        )

        if message == config.DOOR_UNLOCKED_MESSAGE:
            print(f"[{time.time()}] Manual unlock requested via MQTT")
            self._execute_unlock_sequence()
        else:
            print(f"[{time.time()}] Invalid unlock message received")

    def _restart(self) -> None:
        print("Uptime threshold reached, restarting esp8266....")
        try:
            import machine

            machine.reset()
        except ImportError:
            print(
                "machine library not available, you're probably not on an ESP, stopping instead"
            )
        self.stop()

    def _should_restart(self) -> bool:
        if self.start_time is None:
            return False
        uptime: float = time.time() - self.start_time
        return uptime >= self.restart_after_seconds

    def _process_call_detection(self) -> None:
        """Process intercom call detection with edge detection.

        Only triggers on the transition from 'no call' to 'call detected' to prevent
        continuous triggering during a single call event.
        Includes debouncing logic to prevent multiple messages for the same call.
        """
        current_call_detected = self.gpio_driver.detect_call()

        # Only process if this is a NEW call detection (edge detection)
        if (
            not current_call_detected
            or current_call_detected == self._previous_call_state
        ):
            self._previous_call_state = current_call_detected
            return

        # This is a rising edge: False -> True
        self._previous_call_state = current_call_detected

        current_time = time.time()
        time_since_last_call = current_time - self._last_call_detected_time

        print(
            f"[{time.time()}] Debug: NEW call detected! Current time: {current_time}, Last call: {self._last_call_detected_time}, Diff: {time_since_last_call}"
        )
        print(
            f"[{time.time()}] DEBUG: Using edge detection + {config.CALL_DEBOUNCE_SECONDS}s debounce"
        )
        print(
            f"[{time.time()}] Debug condition check: {time_since_last_call} > {config.CALL_DEBOUNCE_SECONDS} = {time_since_last_call > config.CALL_DEBOUNCE_SECONDS}"
        )

        # Use debounce to prevent double unlocks
        if time_since_last_call > config.CALL_DEBOUNCE_SECONDS:
            # Update debounce timer immediately to prevent rapid repeated calls
            self._last_call_detected_time = current_time

            print(f"[{time.time()}] Call detected! Publishing to MQTT...")
            # Ensure MQTT is still connected before publishing
            if self.mqtt_driver.is_connected():
                self.mqtt_driver.publish(
                    config.CALL_DETECTED_TOPIC, config.CALL_DETECTED_MESSAGE
                )
                print(
                    f"[{time.time()}] Call published, next call allowed after: {current_time + config.CALL_DEBOUNCE_SECONDS}"
                )
            else:
                print(
                    f"[{time.time()}] MQTT not connected, cannot publish call detection"
                )

            # Check if auto_unlock is enabled
            if self.auto_unlock:
                print(
                    f"[{time.time()}] Auto-unlock enabled, executing unlock sequence..."
                )
                self._execute_unlock_sequence()
        else:
            print(
                f"[{time.time()}] Call ignored (debounce): {(config.CALL_DEBOUNCE_SECONDS - time_since_last_call):.1f}s remaining"
            )

    def _execute_unlock_sequence(self) -> None:
        """Execute the door unlock sequence with error handling."""
        try:
            print(f"[{time.time()}] Starting door unlock sequence...")
            self.gpio_driver.open_conversation()
            sleep(config.CONVERSATION_OPEN_DELAY_SECONDS)
            self.gpio_driver.unlock()
            sleep(config.DOOR_UNLOCK_DURATION_SECONDS)
            self.gpio_driver.close_conversation()
            self.gpio_driver.lock()
            print(f"[{time.time()}] Door unlock sequence completed successfully")
        except Exception as e:
            print(f"[{time.time()}] Error during door unlock sequence: {e}")
            # Attempt to ensure door is locked and conversation closed on error
            # Try each operation independently for maximum safety
            try:
                self.gpio_driver.close_conversation()
                print(f"[{time.time()}] Emergency: Conversation closed after error")
            except Exception as close_error:
                print(
                    f"[{time.time()}] Critical: Failed to close conversation after error: {close_error}"
                )

            try:
                self.gpio_driver.lock()
                print(f"[{time.time()}] Emergency: Door locked after error")
            except Exception as lock_error:
                print(
                    f"[{time.time()}] Critical: Failed to lock door after error: {lock_error}"
                )

    def _process_cycle(self) -> None:
        """Process one cycle of the main loop."""
        self._process_call_detection()

        # Check for pending MQTT messages
        if hasattr(self.mqtt_driver, "check_messages"):
            self.mqtt_driver.check_messages()

        # Sleep to prevent CPU spinning and allow system tasks to run
        sleep(0.1)
