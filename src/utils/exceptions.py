from fastapi import HTTPException, status


class BaseCustomException(HTTPException):
    pass


class PermissionDeniedException(BaseCustomException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ResourceNotOwnedException(BaseCustomException):
    def __init__(self, detail: str = "Resource not owned by user"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class InvalidTokenException(BaseCustomException):
    def __init__(self, detail: str = "Invalid or expired token"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class WeakPasswordException(BaseCustomException):
    def __init__(self, detail: str = "Password does not meet security requirements"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class RateLimitExceededException(BaseCustomException):
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)