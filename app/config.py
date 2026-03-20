from __future__ import annotations
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
import os

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    app_bot_token: str
    master_encryption_key: str
    db_path: Path
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

def get_settings() -> Settings:
    return Settings(
        app_bot_token=os.getenv("APP_BOT_TOKEN", ""),
        master_encryption_key=os.getenv("MASTER_ENCRYPTION_KEY", ""),
        db_path=Path(os.getenv("DB_PATH", str(BASE_DIR / "storage" / "app.db"))),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
