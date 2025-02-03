import time

class RateLimiter:
    """
    A simple rate limiter to control the frequency of actions based on a timeout.
    """

    def __init__(self, timeout: int = 60):
        """
        Initialize the rate limiter with a specified timeout.

        :param timeout: The timeout duration in seconds.
        """
        self.history = {}
        self.timeout = timeout

    def can_proceed(self, plate: str) -> bool:
        """
        Check if the action associated with the given plate can proceed.

        :param plate: The identifier for the action.
        :return: True if the action can proceed, False otherwise.
        """
        current_time = time.time()

        if plate not in self.history:
            self.history[plate] = current_time + self.timeout
            return True

        elif current_time >= self.history[plate]:
            self.history[plate] = current_time + self.timeout
            return True
        else:
            return False
