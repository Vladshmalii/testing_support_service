from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL")
    mongodb_url: str = os.getenv("MONGODB_URL")
    mongodb_database: str = os.getenv("MONGODB_DATABASE")
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"

    initial_admin_email: str = os.getenv("INITIAL_ADMIN_EMAIL")
    initial_admin_password: str = os.getenv("INITIAL_ADMIN_PASSWORD")
    initial_staff_email: str = os.getenv("INITIAL_STAFF_EMAIL")
    initial_staff_password: str = os.getenv("INITIAL_STAFF_PASSWORD")
    initial_user_email: str = os.getenv("INITIAL_USER_EMAIL")
    initial_user_password: str = os.getenv("INITIAL_USER_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

tortoise_config = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": ["src.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "timezone": "UTC",
}