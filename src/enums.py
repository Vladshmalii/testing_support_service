from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    STAFF = "staff"


class RequestStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"
