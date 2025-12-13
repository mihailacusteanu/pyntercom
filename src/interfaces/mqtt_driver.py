from .base import ABC, abstractmethod

class MqttDriverInterface(ABC):
    def __init__(
        self,
        client_id: str = None,
        server: str = None,
        port: int = 1883,
        call_detected_topic: str = None,
        allow_conversation_topic: str = None,
        unlock_topic: str = None,
        mqtt_username: str = None,
        mqtt_password: str = None,
    ):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.call_detected_topic = call_detected_topic
        self.allow_conversation_topic = allow_conversation_topic
        self.unlock_topic = unlock_topic
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password

    @abstractmethod
    def connect(self):
        """Connect to the MQTT broker."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        pass

    @abstractmethod
    def publish(self, topic: str, payload: str):
        """Publish a message to a specific topic."""
        pass

    @abstractmethod
    def subscribe(self, topic: str, callback=None):
        """Subscribe to a specific topic."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to the MQTT broker."""
        pass
