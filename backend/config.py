"""Application settings, loaded once from environment / .env file.

Other modules import the singleton:
    from config import settings
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the repo root (one level above backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Settings:
    """Read-only bag of configuration values.

    Every setting has a sensible default so the app starts without a .env
    file (except GOOGLE_API_KEY, which the Gemini service checks at call
    time).
    """

    def __init__(self) -> None:
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        self.frontend_origin: str = os.getenv(
            "FRONTEND_ORIGIN", "http://localhost:5173"
        )
        self.max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "10"))
        self.upload_dir: str = os.getenv("UPLOAD_DIR", "data/uploads")


settings = Settings()
