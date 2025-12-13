"""
PyNtercom - Smart Intercom System for ESP8266

Main entry point with optional OTA (Over-The-Air) update support.

OTA can be triggered via MQTT:
  - Send "start_ota" to "pyntercom/ota" topic
  - ESP8266 enters OTA mode (intercom pauses)
  - Deploy code with: ./scripts/ota_deploy.sh
  - ESP8266 auto-restarts after deployment

To disable OTA: Set ENABLE_OTA = False in config
"""

from src.app.intercom import Intercom
import src.config as config
import time

# OTA Configuration (can be moved to config if desired)
ENABLE_OTA = True  # Set to False to disable OTA functionality
OTA_PORT = 8266
OTA_PASSWORD = "pyntercom_ota_2024"  # CHANGE THIS IN PRODUCTION!
OTA_TIMEOUT = 300  # 5 minutes


def main():
    """Run intercom with optional OTA support."""
    ota_requested = False

    # Define OTA callback if enabled
    ota_callback = None
    if ENABLE_OTA:
        def handle_ota_message(topic: str, message: str) -> None:
            """Handle OTA trigger messages."""
            nonlocal ota_requested
            print(f"[{time.time()}] Received OTA command: {message}")

            if message == "start_ota":
                print(f"[{time.time()}] 🔄 OTA update requested, stopping intercom...")
                ota_requested = True
                intercom.stop()

        ota_callback = handle_ota_message
        print(f"[{time.time()}] OTA enabled - will subscribe to pyntercom/ota topic")

    # Create intercom with optional OTA callback
    intercom = Intercom(ota_callback=ota_callback)

    # Run intercom (it will handle WiFi/MQTT connection and subscriptions)
    print(f"[{time.time()}] Starting intercom...")
    intercom.run()

    # Handle OTA if requested
    if ENABLE_OTA and ota_requested:
        print(f"[{time.time()}] Starting OTA server...")
        try:
            from src.app.ota import start_ota_mode
            start_ota_mode(
                port=OTA_PORT,
                password=OTA_PASSWORD,
                timeout=OTA_TIMEOUT
            )
        except Exception as e:
            print(f"[{time.time()}] ❌ OTA failed: {e}")
            print(f"[{time.time()}] Restarting intercom instead...")
            # Restart the intercom if OTA fails
            main()


if __name__ == "__main__":
    main()
