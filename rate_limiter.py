import time

class RateLimiter:
    def __init__(self, interval_seconds):
        self.interval_seconds = interval_seconds
        self.last_request_time = 0
    
    async def acquire(self):
        now = time.time()
        if now - self.last_request_time >= self.interval_seconds:
            self.last_request_time = now
            return True
        return False
    
    def time_until_next_request(self):
        now = time.time()
        time_passed = now - self.last_request_time
        return max(0, self.interval_seconds - time_passed)
