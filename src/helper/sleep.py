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

    from src.config import MOCK_SLEEP

    if force_real or not MOCK_SLEEP:
        time.sleep(seconds)
    else:
        print(f"Mock sleep for {seconds} seconds")
