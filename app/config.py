from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    bot_token: str
    master_encryption_key: str
    db_path: Path
    log_level: str = "INFO"

def get_settings() -> Settings:
    return Settings(
        bot_token=os.getenv("APP_BOT_TOKEN", ""),
        master_encryption_key=os.getenv("MASTER_ENCRYPTION_KEY", ""),
        db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "storage" / "bot.db"))),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
