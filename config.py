import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Конфигурация базы данных"""

    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_SCHEMA = os.getenv("DB_SCHEMA", "public")

    @classmethod
    def get_database_url(cls) -> str:
        """Формирует URL для подключения к базе данных"""
        return f"postgresql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
