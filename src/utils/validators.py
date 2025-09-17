import re
from typing import List, Tuple
from pydantic import validator


class ValidationUtils:

    @staticmethod
    def validate_email_format(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone_format(phone: str) -> bool:
        pattern = r'^\+?[1-9]\d{1,14}$'
        return re.match(pattern, phone) is not None

    @staticmethod
    def validate_inn_format(inn: str) -> bool:
        if not inn.isdigit():
            return False
        return len(inn) in [10, 12]

    @staticmethod
    def sanitize_input(text: str) -> str:
        if not text:
            return text

        text = re.sub(r'<[^>]*>', '', text)
        text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE)

        return text.strip()


def password_strength_validator(password: str) -> Tuple[bool, List[str]]:
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors