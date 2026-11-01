
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self):
        self.APP_ENV = os.getenv(
            "APP_ENV", "development"
        )

        self.FRONTEND_URL = os.getenv(
            "FRONTEND_URL", "http://localhost:5173"
        )

        self.DATABASE_URL = os.getenv("DATABASE_URL")

        if not self.DATABASE_URL:
            raise RuntimeError(
                "DATABASE_URL is not configured"
            )

        if self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )


settings = Settings()

# Preserve compatibility with existing imports
DATABASE_URL = settings.DATABASE_URL
