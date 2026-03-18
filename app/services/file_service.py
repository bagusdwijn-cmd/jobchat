from __future__ import annotations

from pathlib import Path

class FileService:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)

    def user_dir(self, chat_id: int) -> Path:
        p = self.base_dir / f"user_{chat_id}"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def cv_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "cv"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def attachment_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "attachments"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def job_dir(self, chat_id: int) -> Path:
        p = self.user_dir(chat_id) / "jobs"
        p.mkdir(parents=True, exist_ok=True)
        return p
