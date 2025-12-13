from src.interfaces.mqtt_driver import MqttDriverInterface

class MockMqttDriver(MqttDriverInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._connected = False

    def connect(self):
        """Simulate connecting to the MQTT broker."""
        print(f"Mock connecting to MQTT broker at {self.server}:{self.port} with client ID {self.client_id}")
        self._connected = True
        return True

    def disconnect(self):
        """Simulate disconnecting from the MQTT broker."""
        print("Mock disconnected from MQTT broker")
        self._connected = False

    def publish(self, topic: str, payload: str):
        """Simulate publishing a message to a specific topic."""
        print(f"Mock publishing to topic '{topic}': {payload}")

    def subscribe(self, topic: str, callback=None):
        """Simulate subscribing to a specific topic."""
        print(f"Mock subscribed to topic '{topic}'")

    def is_connected(self) -> bool:
        """Check if currently connected to the MQTT broker."""
        return self._connected