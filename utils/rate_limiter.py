import time

class RateLimiter:
    def __init__(self, timeout=60):
        self.history = {}
        self.timeout = timeout

    def can_proceed(self, plate: str) -> bool:
        current_time = time.time()

        if plate not in self.history:
            self.history[plate] = current_time + self.timeout
            return True

        elif current_time >= self.history[plate]:
            self.history[plate] = current_time + self.timeout
            return True
        else:
            return False
