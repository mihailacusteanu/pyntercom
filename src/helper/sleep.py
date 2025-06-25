import time

def sleep(seconds: float, force_real: bool = False) -> None:
    """
    Sleep for the specified number of seconds.

    Args:
        seconds: Number of seconds to sleep
        force_real: If True, always use real sleep regardless of MOCK_SLEEP
    """
    from src.config import MOCK_SLEEP

    if force_real or not MOCK_SLEEP:
        time.sleep(seconds)
    else:
        print(f"Mock sleep for {seconds} seconds")
