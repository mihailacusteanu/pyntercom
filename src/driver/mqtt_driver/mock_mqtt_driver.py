from src.interfaces.mqtt_driver import MqttDriverInterface

class MockMqttDriver(MqttDriverInterface):
    def connect(self):
        """Simulate connecting to the MQTT broker."""
        print(f"Mock connecting to MQTT broker at {self.server}:{self.port} with client ID {self.client_id}")
        return True

    def disconnect(self):
        """Simulate disconnecting from the MQTT broker."""
        print("Mock disconnected from MQTT broker")

    def publish(self, topic: str, payload: str):
        """Simulate publishing a message to a specific topic."""
        print(f"Mock publishing to topic '{topic}': {payload}")

    def subscribe(self, topic: str, callback=None):
        """Simulate subscribing to a specific topic."""
        print(f"Mock subscribed to topic '{topic}'")
        if callback:
            callback("Mock message received")