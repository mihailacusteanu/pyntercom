from src.driver.driver_manager import DriverManager
import src.config as config
from src.helper.sleep import sleep
import time

class Intercom:
    """Main controller class for the smart intercom system.
    
    This class handles the core functionality of the intercom system including
    WiFi and MQTT connections, call detection, door unlocking, and the main control loop.
    It integrates with hardware drivers through the DriverManager and communicates
    with home automation systems via MQTT.
    """
    def __init__(self):
        """Initialize the intercom system.
        
        Sets up the driver manager, loads hardware drivers, and initializes
        system state variables.
        """
        self.driver_manager = DriverManager()
        self._load_drivers()
        self._initialize_state()
        
    def _initialize_state(self):
        """Initialize internal state variables.
        
        Sets connection status flags to False and resets the call detection timestamp.
        """
        self.is_connected_to_wifi = False
        self.is_connected_to_mqtt = False
        self._last_call_detected_time = 0
        self._previous_call_state = False  # Track previous call detection state
        
    def _load_drivers(self):
        """Load all drivers needed for the intercom system."""
        self.wifi_driver = self.driver_manager.load_wifi_driver()
        self.mqtt_driver = self.driver_manager.load_mqtt_driver()
        self.gpio_driver = self.driver_manager.load_gpio_driver()
        print(f"[{time.time()}] Intercom: Drivers loaded successfully")
        
    def run(self, test_mode: bool = False, max_iterations: int = 3):
        """Start the main intercom control loop.
        
        This is the primary entry point for running the intercom system.
        It handles WiFi/MQTT connections, call detection, and message processing
        in an infinite loop (unless in test mode).
        
        Args:
            test_mode (bool): If True, run in test mode for a limited number of iterations
            max_iterations (int): Maximum number of iterations to run in test mode
        """
        print(f"[{time.time()}] 🚪 Intercom system starting...")
        print(f"[{time.time()}] 📡 Starting main intercom loop...")
        
        iteration_count = 0
        
        while True:
            try:
                if not self._ensure_wifi_connected():
                    if self._should_stop_test(test_mode, iteration_count, max_iterations):
                        break
                    iteration_count += 1
                    continue
                
                if not self._ensure_mqtt_connected():
                    if self._should_stop_test(test_mode, iteration_count, max_iterations):
                        break
                    iteration_count += 1
                    continue
                
                self._process_call_detection()
                
                if not self._process_mqtt_messages():
                    continue
                
                sleep(0.1)
                
                if test_mode:
                    iteration_count += 1
                    if iteration_count >= max_iterations:
                        print(f"[{time.time()}] 🧪 Test mode: completed {iteration_count} iterations")
                        break
                        
            except Exception as e:
                print(f"[{time.time()}] 🚨 Error: {e}")
                self._reset_connections()
                if self._should_stop_test(test_mode, iteration_count, max_iterations):
                    break
                iteration_count += 1
    
    def _ensure_wifi_connected(self):
        """Ensure WiFi connection is established.
        
        Checks current WiFi connection status and attempts to reconnect if disconnected.
        
        Returns:
            bool: True if connected (or connection successful), False otherwise
        """
        if self.is_connected_to_wifi:
            return True
            
        print(f"[{time.time()}] 📶 WiFi not connected, attempting to connect...")
        if self.connect_to_wifi():
            return True
            
        print(f"[{time.time()}] ❌ WiFi connection failed, retrying...")
        return False
    
    def _ensure_mqtt_connected(self):
        """Ensure MQTT connection is established.
        
        Checks current MQTT connection status and attempts to reconnect if disconnected.
        If reconnection is successful, re-subscribes to required topics.
        
        Returns:
            bool: True if connected (or connection successful), False otherwise
        """
        if self.is_connected_to_mqtt:
            return True
            
        print(f"[{time.time()}] 🔗 MQTT not connected, attempting to connect...")
        if self.connect_to_mqtt():
            self._subscribe_to_topics()
            return True
            
        print(f"[{time.time()}] ❌ MQTT connection failed, retrying...")
        return False
    
    def _process_call_detection(self):
        """Process intercom call detection with edge detection.
        
        Only triggers on the transition from 'no call' to 'call detected' to prevent
        continuous triggering during a single call event.
        Includes debouncing logic to prevent multiple messages for the same call.
        """
        current_call_detected = self.detect_call()
        
        # Only process if this is a NEW call detection (edge detection)
        if not current_call_detected or current_call_detected == self._previous_call_state:
            self._previous_call_state = current_call_detected
            return
        
        # This is a rising edge: False -> True
        self._previous_call_state = current_call_detected
        
        current_time = time.time()
        time_since_last_call = current_time - self._last_call_detected_time
        
        print(f"[{time.time()}] 🔍 Debug: NEW call detected! Current time: {current_time}, Last call: {self._last_call_detected_time}, Diff: {time_since_last_call}")
        print(f"[{time.time()}] 🚀 DEBUG: Using edge detection + 5s debounce (v4.2)")
        print(f"[{time.time()}] 🔍 Debug condition check: {time_since_last_call} > 5 = {time_since_last_call > 5}")
        
        # Use 5 second debounce to prevent spam
        if time_since_last_call > 5:
            print(f"[{time.time()}] 📞 Call detected! Publishing to MQTT...")
            # Ensure MQTT is still connected before publishing
            if self.is_connected_to_mqtt:
                self.mqtt_driver.publish(config.CALL_DETECTED_TOPIC, config.CALL_DETECTED_MESSAGE)
                self._last_call_detected_time = current_time
                print(f"[{time.time()}] ✅ Call published, next call allowed after: {current_time + 5}")
            else:
                print(f"[{time.time()}] ⚠️ MQTT not connected, cannot publish call detection")
        else:
            print(f"[{time.time()}] ⏰ Call ignored (debounce): {(5 - time_since_last_call):.1f}s remaining")
    
    def _process_mqtt_messages(self):
        """Process pending MQTT messages.
        
        Checks for pending MQTT messages and handles reconnection if connection is lost.
        
        Returns:
            bool: True if connection is OK, False if reconnection is needed
        """
        if hasattr(self.mqtt_driver, 'check_messages'):
            if not self.mqtt_driver.check_messages():
                print(f"[{time.time()}] 🔌 MQTT connection lost, reconnecting...")
                self.is_connected_to_mqtt = False
                return False
        return True
    
    def _should_stop_test(self, test_mode, iteration_count, max_iterations):
        return test_mode and iteration_count >= max_iterations
    
    def _reset_connections(self):
        self.is_connected_to_wifi = False
        self.is_connected_to_mqtt = False
    
    def _subscribe_to_topics(self):
        self.subscribe_to_mqtt_topic_for_opening_door()
    
    def connect_to_wifi(self):
        """Connect to WiFi network using configured credentials.
        
        Attempts to connect to the WiFi network using SSID and password from config.
        Updates connection status on success.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.wifi_driver.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
            self.is_connected_to_wifi = True
            return True
        return False
    
    def connect_to_mqtt(self):
        """Connect to MQTT broker.
        
        Attempts to connect to the MQTT broker using configuration from config.
        Updates connection status on success.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if self.mqtt_driver.connect():
            self.is_connected_to_mqtt = True
            return True
        return False
    
    def detect_call(self):
        """Detect if an intercom call is occurring.
        
        Reads the call detection pin via the GPIO driver to determine if a call
        is currently being received.
        
        Returns:
            bool: True if call detected, False otherwise
        """
        return self.gpio_driver.detect_call()
    
    def detect_call_and_send_message(self):
        """Detect call and send MQTT notification.
        
        Checks for call detection and immediately publishes an MQTT message
        if a call is detected. Unlike _process_call_detection, this doesn't
        implement debouncing logic.
        """
        if self.gpio_driver.detect_call():
            self.mqtt_driver.publish(config.CALL_DETECTED_TOPIC, config.CALL_DETECTED_MESSAGE)
            
    def subscribe_to_mqtt_topic_for_opening_door(self):
        """Subscribe to the door unlock MQTT topic.
        
        Sets up subscription to the door unlock topic and configures the
        message handler for processing unlock commands.
        """
        self.mqtt_driver.subscribe(config.UNLOCK_TOPIC, self._handle_open_door_message)

    def _handle_open_door_message(self, topic, message):
        """Handle door unlock messages from MQTT.
        
        Processes incoming MQTT messages for door unlocking. When a valid unlock
        message is received, executes the door unlock sequence with error handling:
        1. Open intercom conversation
        2. Brief pause
        3. Unlock door
        4. Wait for entry (5 seconds)
        5. Close conversation and relock
        
        Args:
            topic (str): The MQTT topic the message was received on
            message (str): The message payload
        """
        print(f"🔍 Debug: Received MQTT message on '{topic}': '{message}' (expected: '{config.DOOR_UNLOCKED_MESSAGE}')")
        print(f"📊 Debug: Message received at time: {time.time()}")
        
        if message == config.DOOR_UNLOCKED_MESSAGE:
            try:
                print(f"[{time.time()}] 🔓 Starting door unlock sequence...")
                self.gpio_driver.open_conversation()
                sleep(1)  
                self.gpio_driver.unlock()
                sleep(5)
                self.gpio_driver.close_conversation()
                self.gpio_driver.lock()
                print(f"[{time.time()}] ✅ Intercom: Door unlock sequence completed successfully")
            except Exception as e:
                print(f"[{time.time()}] 🚨 Error during door unlock sequence: {e}")
                # Attempt to ensure door is locked and conversation closed on error
                # Try each operation independently for maximum safety
                try:
                    self.gpio_driver.close_conversation()
                    print(f"[{time.time()}] 🔒 Emergency: Conversation closed after error")
                except Exception as close_error:
                    print(f"[{time.time()}] 🚨 Critical: Failed to close conversation after error: {close_error}")
                
                try:
                    self.gpio_driver.lock()
                    print(f"[{time.time()}] 🔒 Emergency: Door locked after error")
                except Exception as lock_error:
                    print(f"[{time.time()}] 🚨 Critical: Failed to lock door after error: {lock_error}")
        else:
            print(f"[{time.time()}] Intercom: Invalid message for unlocking door")