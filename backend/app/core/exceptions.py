class NotFoundError(Exception):
    def __init__(self, message: str = "record not found"):
        super().__init__(message)
        self.message = message


class ConflictError(Exception):
    def __init__(self, message: str = "conflict"):
        super().__init__(message)
        self.message = message


class UnauthorizedError(Exception):
    def __init__(self, message: str = "authentication required"):
        super().__init__(message)
        self.message = message
