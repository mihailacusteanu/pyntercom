from src.driver.driver_manager import DriverManager
import src.config as config
from src.helper import sleep
import time

class Intercom:
    def __init__(self):
        self.driver_manager = DriverManager()
        self._load_drivers()
        self._initialize_state()
        
    def _initialize_state(self):
        self.is_connected_to_wifi = False
        self.is_connected_to_mqtt = False
        self._last_call_detected_time = 0
        
    def _load_drivers(self):
        """Load all drivers needed for the intercom system."""
        self.wifi_driver = self.driver_manager.load_wifi_driver()
        self.mqtt_driver = self.driver_manager.load_mqtt_driver()
        self.gpio_driver = self.driver_manager.load_gpio_driver()
        print("Intercom: Drivers loaded successfully")
        
    def run(self, test_mode: bool = False, max_iterations: int = 3):
        print("🚪 Intercom system starting...")
        self._setup_mqtt_callbacks()
        print("📡 Starting main intercom loop...")
        
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
                        print(f"🧪 Test mode: completed {iteration_count} iterations")
                        break
                        
            except Exception as e:
                print(f"🚨 Error: {e}")
                self._reset_connections()
                if self._should_stop_test(test_mode, iteration_count, max_iterations):
                    break
                iteration_count += 1
    
    def _ensure_wifi_connected(self):
        if self.is_connected_to_wifi:
            return True
            
        print("📶 WiFi not connected, attempting to connect...")
        if self.connect_to_wifi():
            return True
            
        print("❌ WiFi connection failed, retrying...")
        return False
    
    def _ensure_mqtt_connected(self):
        if self.is_connected_to_mqtt:
            return True
            
        print("🔗 MQTT not connected, attempting to connect...")
        if self.connect_to_mqtt():
            self._subscribe_to_topics()
            return True
            
        print("❌ MQTT connection failed, retrying...")
        return False
    
    def _process_call_detection(self):
        if not self.detect_call():
            return
            
        current_time = time.time()
        if current_time - self._last_call_detected_time >= 5:
            print("📞 Call detected! Publishing to MQTT...")
            self.mqtt_driver.publish(config.CALL_DETECTED_TOPIC, "call_detected")
            self._last_call_detected_time = current_time
    
    def _process_mqtt_messages(self):
        if hasattr(self.mqtt_driver, 'check_messages'):
            if not self.mqtt_driver.check_messages():
                print("🔌 MQTT connection lost, reconnecting...")
                self.is_connected_to_mqtt = False
                return False
        return True
    
    def _should_stop_test(self, test_mode, iteration_count, max_iterations):
        return test_mode and iteration_count >= max_iterations
    
    def _reset_connections(self):
        self.is_connected_to_wifi = False
        self.is_connected_to_mqtt = False
    
    def _setup_mqtt_callbacks(self):
        self.subscribe_to_mqtt_topic_for_openning_door()
    
    def _subscribe_to_topics(self):
        self.subscribe_to_mqtt_topic_for_openning_door()
    
    def connect_to_wifi(self):
        if self.wifi_driver.connect(config.WIFI_SSID, config.WIFI_PASSWORD):
            self.is_connected_to_wifi = True
            return True
        return False
    
    def connect_to_mqtt(self):
        if self.mqtt_driver.connect():
            self.is_connected_to_mqtt = True
            return True
        return False
    
    def detect_call(self):
        return self.gpio_driver.detect_call()
    
    def detect_call_and_send_message(self):
        if self.gpio_driver.detect_call():
            self.mqtt_driver.publish(config.CALL_DETECTED_TOPIC, "call_detected")
            
    def subscribe_to_mqtt_topic_for_openning_door(self):
        self.mqtt_driver.subscribe(config.UNLOCK_TOPIC, self._handle_open_door_message)

    def _handle_open_door_message(self, topic, message):
        if message == config.DOOR_UNLOCKED_MESSAGE:
            self.gpio_driver.open_conversation()
            sleep(1)  
            self.gpio_driver.unlock()
            sleep(5)
            self.gpio_driver.close_conversation()
            self.gpio_driver.lock()
            print("Intercom: Door unlocked")
        else:
            print("Intercom: Invalid message for unlocking door")