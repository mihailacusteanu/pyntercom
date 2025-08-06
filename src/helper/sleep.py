import time

def sleep(seconds: float, force_real: bool = False) -> None:
    """
    Pause execution for the specified number of seconds.

    This function provides a platform-independent way to implement delays.
    It automatically switches between real time.sleep() and a mock implementation
    based on the MOCK_SLEEP configuration setting. This allows for faster
    execution during testing while maintaining accurate timing in production.
    
    Args:
        seconds (float): Number of seconds to pause execution
        force_real (bool): If True, always use real time.sleep() even if
                          MOCK_SLEEP is enabled. Useful for critical timing
                          operations where simulation isn't appropriate.
    
    Returns:
        None
    """
    
    # Try to import MOCK_SLEEP, but fall back to real sleep if import fails
    # This handles MicroPython environments where src.config might not be available
    try:
        from src.config import MOCK_SLEEP
        use_mock = MOCK_SLEEP and not force_real
    except (ImportError, AttributeError):
        # Fall back to real sleep if config is not available (e.g., on ESP8266)
        use_mock = False
    
    if use_mock:
        print(f"Mock sleep for {seconds} seconds")
    else:
        time.sleep(seconds)
