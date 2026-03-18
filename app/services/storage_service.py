from __future__ import annotations

import json
from pathlib import Path
import aiosqlite

class StorageService:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    async def init(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(
                '''
                CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    full_name TEXT DEFAULT '',
                    target_title TEXT DEFAULT '',
                    skills TEXT DEFAULT '',
                    portfolio TEXT DEFAULT '',
                    linkedin TEXT DEFAULT '',
                    extra_notes TEXT DEFAULT '',
                    gmail_address TEXT DEFAULT '',
                    gmail_app_password_encrypted TEXT DEFAULT '',
                    gemini_api_key_encrypted TEXT DEFAULT '',
                    setup_completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    telegram_file_id TEXT DEFAULT '',
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    mime_type TEXT DEFAULT '',
                    is_primary_cv INTEGER DEFAULT 0,
                    is_active_attachment INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    company TEXT DEFAULT '',
                    position TEXT DEFAULT '',
                    hr_email TEXT DEFAULT '',
                    subject TEXT DEFAULT '',
                    body TEXT DEFAULT '',
                    instructions TEXT DEFAULT '',
                    language TEXT DEFAULT 'id',
                    needs_review INTEGER DEFAULT 1,
                    confidence_json TEXT DEFAULT '{}',
                    attachments_json TEXT DEFAULT '[]',
                    raw_ai_json TEXT DEFAULT '{}',
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP
                );
                '''
            )
            await db.commit()

    async def ensure_user(self, chat_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (chat_id) VALUES (?)",
                (chat_id,),
            )
            await db.commit()

    async def update_user_field(self, chat_id: int, field_name: str, value: str | int) -> None:
        allowed = {
            "full_name", "target_title", "skills", "portfolio", "linkedin",
            "extra_notes", "gmail_address", "gmail_app_password_encrypted",
            "gemini_api_key_encrypted", "setup_completed"
        }
        if field_name not in allowed:
            raise ValueError("Field user tidak diizinkan")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE users SET {field_name} = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                (value, chat_id),
            )
            await db.commit()

    async def get_user(self, chat_id: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def add_user_file(
        self,
        chat_id: int,
        telegram_file_id: str,
        file_name: str,
        file_path: str,
        mime_type: str,
        is_primary_cv: bool = False,
        is_active_attachment: bool = True,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            if is_primary_cv:
                await db.execute(
                    "UPDATE user_files SET is_primary_cv = 0 WHERE chat_id = ?",
                    (chat_id,),
                )
            cur = await db.execute(
                '''
                INSERT INTO user_files (
                    chat_id, telegram_file_id, file_name, file_path, mime_type,
                    is_primary_cv, is_active_attachment
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    chat_id, telegram_file_id, file_name, file_path, mime_type,
                    1 if is_primary_cv else 0,
                    1 if is_active_attachment else 0,
                ),
            )
            await db.commit()
            return cur.lastrowid

    async def list_user_files(self, chat_id: int) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM user_files WHERE chat_id = ? ORDER BY is_primary_cv DESC, id ASC",
                (chat_id,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def create_application(self, payload: dict) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                '''
                INSERT INTO applications (
                    chat_id, company, position, hr_email, subject, body, instructions,
                    language, needs_review, confidence_json, attachments_json, raw_ai_json, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    payload["chat_id"],
                    payload.get("company", ""),
                    payload.get("position", ""),
                    payload.get("hr_email", ""),
                    payload.get("subject", ""),
                    payload.get("body", ""),
                    payload.get("instructions", ""),
                    payload.get("language", "id"),
                    1 if payload.get("needs_review", True) else 0,
                    json.dumps(payload.get("confidence", {}), ensure_ascii=False),
                    json.dumps(payload.get("attachments", []), ensure_ascii=False),
                    json.dumps(payload.get("raw_ai_json", {}), ensure_ascii=False),
                    payload.get("status", "draft"),
                ),
            )
            await db.commit()
            return cur.lastrowid

    async def get_application(self, app_id: int) -> dict | None:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_applications(self, chat_id: int, only_sent: bool = False) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if only_sent:
                cur = await db.execute(
                    "SELECT * FROM applications WHERE chat_id = ? AND status = 'sent' ORDER BY id DESC LIMIT 20",
                    (chat_id,),
                )
            else:
                cur = await db.execute(
                    "SELECT * FROM applications WHERE chat_id = ? ORDER BY id DESC LIMIT 20",
                    (chat_id,),
                )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_application_field(self, app_id: int, field_name: str, value: str) -> None:
        allowed = {"hr_email", "subject", "body", "status", "sent_at"}
        if field_name not in allowed:
            raise ValueError("Field application tidak diizinkan")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE applications SET {field_name} = ? WHERE id = ?",
                (value, app_id),
            )
            await db.commit()

    async def mark_application_sent(self, app_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE applications SET status = 'sent', sent_at = CURRENT_TIMESTAMP WHERE id = ?",
                (app_id,),
            )
            await db.commit()
