
"""Application settings, loaded once from environment / .env file.

Other modules import the singleton:
    from config import settings
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Application configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
        self.gemini_model: str = os.getenv(
            "GEMINI_MODEL", "gemini-3.8-flash"
        )
        self.frontend_origin: str = os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:5173"
        )
        self.max_upload_mb: int = int(
            os.getenv("MAX_UPLOAD_MB", "10")
        )
        self.upload_dir: str = os.getenv(
            "UPLOAD_DIR", "data/uploads"
        )

        # Uppercase aliases for compatibility with existing code
        self.GOOGLE_API_KEY = self.google_api_key
        self.GEMINI_MODEL = self.gemini_model
        self.FRONTEND_ORIGIN = self.frontend_origin
        self.MAX_UPLOAD_MB = self.max_upload_mb
        self.UPLOAD_DIR = self.upload_dir


settings = Settings()
