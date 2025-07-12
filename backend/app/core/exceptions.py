from typing import Optional

class OpenF1APIException(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class RateLimitException(Exception):
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)

class WebSocketException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)