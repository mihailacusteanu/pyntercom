from src.interfaces.mqtt_driver import MqttDriverInterface

class Esp8266MQTTDriver(MqttDriverInterface):
    def __init__(
        self,
        client_id: str,
        server: str,
        port: int = 1883,
        call_detected_topic: str = None,
        allow_conversation_topic: str = None,
        unlock_topic: str = None,
        mqtt_username: str = None,
        mqtt_password: str = None,
    ):
        super().__init__(
            client_id,
            server,
            port,
            call_detected_topic,
            allow_conversation_topic,
            unlock_topic,
            mqtt_username,
            mqtt_password,
        )
        self.connected = False
        self.client = None
        self.subscriptions = {}

    def connect(self):
        """Connect to the MQTT broker."""
        print(
            f"Connecting to MQTT broker at {self.server}:{self.port} with client ID {self.client_id}"
        )

        try:
            from umqtt.simple import MQTTClient

            self.client = MQTTClient(
                client_id=self.client_id,
                server=self.server,
                port=self.port,
                user=self.mqtt_username,
                password=self.mqtt_password,
                keepalive=60,
                ssl=False,
                ssl_params={},
            )

            self.client.set_callback(self._on_message)

            self.client.connect()

            self.connected = True
            print(f"✓ Connected to MQTT broker at {self.server}:{self.port}")

            for topic in self.subscriptions.keys():
                self.client.subscribe(topic)
                print(f"  📡 Re-subscribed to: {topic}")

            return True

        except Exception as e:
            print(f"✗ MQTT connection failed: {e}")
            self.connected = False
            self.client = None
            return False

    def disconnect(self):
        """Disconnect from the MQTT broker."""
        print("Disconnecting from MQTT broker")

        if self.client and self.connected:
            try:
                self.client.disconnect()
                print("✓ Disconnected from MQTT broker")
            except Exception as e:
                print(f"Warning: Disconnect error: {e}")

        self.connected = False
        self.client = None

    def publish(self, topic: str, payload: str, retain: bool = False):
        """Publish a message to a specific topic."""
        if not self.connected or not self.client:
            raise Exception("Not connected to MQTT broker")

        try:
            print(f"📤 Publishing to '{topic}': {payload}")
            self.client.publish(topic, payload, retain=retain)
            print(f"  ✓ Message published to {topic}")
            return True
        except Exception as e:
            print(f"✗ Publish error: {e}")
            raise

    def subscribe(self, topic: str, callback=None):
        """Subscribe to a specific topic."""
        if not self.connected or not self.client:
            raise Exception("Not connected to MQTT broker")

        try:
            print(f"📡 Subscribing to topic '{topic}'")

            self.subscriptions[topic] = callback

            self.client.subscribe(topic)
            print(f"✓ Successfully subscribed to {topic}")
            return True

        except Exception as e:
            print(f"✗ Subscribe error: {e}")
            raise

    def unsubscribe(self, topic: str):
        """Unsubscribe from a topic"""
        if not self.connected or not self.client:
            raise Exception("Not connected to MQTT broker")

        try:
            self.client.unsubscribe(topic)

            if topic in self.subscriptions:
                del self.subscriptions[topic]

            print(f"✓ Unsubscribed from {topic}")
            return True

        except Exception as e:
            print(f"✗ Unsubscribe error: {e}")
            raise

    def _on_message(self, topic, msg):
        """Internal callback for received messages"""
        topic_str = topic.decode() if isinstance(topic, bytes) else topic
        msg_str = msg.decode() if isinstance(msg, bytes) else msg

        print(f"📨 Received: {topic_str} -> {msg_str}")

        if topic_str in self.subscriptions and self.subscriptions[topic_str]:
            try:
                self.subscriptions[topic_str](topic_str, msg_str)
            except Exception as e:
                print(f"Error in message callback for {topic_str}: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected to broker"""
        return self.connected and self.client is not None

    def check_messages(self):
        """Process any pending messages (blocking for a short time)"""
        if not self.connected or not self.client:
            return False

        try:
            self.client.check_msg()
            return True
        except Exception as e:
            print(f"Error checking messages: {e}")
            self.connected = False
            return False

    def wait_msg(self):
        """Wait for a single message (blocking)"""
        if not self.connected or not self.client:
            return False

        try:
            self.client.wait_msg()
            return True
        except Exception as e:
            print(f"Error waiting for message: {e}")
            self.connected = False
            return False

    def get_client_info(self) -> dict:
        """Get client connection information"""
        return {
            "client_id": self.client_id,
            "server": self.server,
            "port": str(self.port),
            "connected": str(self.connected),
            "subscriptions": list(self.subscriptions.keys())
        }
