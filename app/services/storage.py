from __future__ import annotations
import json
from pathlib import Path
import aiosqlite

class Storage:
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
                    ai_provider TEXT DEFAULT '',
                    ai_model TEXT DEFAULT '',
                    ai_base_url TEXT DEFAULT '',
                    ai_api_key_encrypted TEXT DEFAULT '',
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
                    hr_email TEXT DEFAULT '',
                    available_positions_json TEXT DEFAULT '[]',
                    selected_position TEXT DEFAULT '',
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
                CREATE TABLE IF NOT EXISTS agent_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    agent_type TEXT NOT NULL,
                    input_text TEXT DEFAULT '',
                    result_json TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS repo_indexes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    repo_name TEXT DEFAULT '',
                    repo_path TEXT DEFAULT '',
                    index_json TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                '''
            )
            await db.commit()

    async def ensure_user(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
            await db.commit()

    async def update_user_field(self, chat_id: int, field: str, value):
        allowed = {
            "full_name", "target_title", "skills", "portfolio", "linkedin", "extra_notes",
            "gmail_address", "gmail_app_password_encrypted", "ai_provider", "ai_model",
            "ai_base_url", "ai_api_key_encrypted", "setup_completed"
        }
        if field not in allowed:
            raise ValueError("Field user tidak diizinkan")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?", (value, chat_id))
            await db.commit()

    async def get_user(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users WHERE chat_id = ?", (chat_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM users ORDER BY updated_at DESC")
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def add_user_file(self, **payload):
        async with aiosqlite.connect(self.db_path) as db:
            if payload.get("is_primary_cv"):
                await db.execute("UPDATE user_files SET is_primary_cv = 0 WHERE chat_id = ?", (payload["chat_id"],))
            cur = await db.execute(
                "INSERT INTO user_files (chat_id, telegram_file_id, file_name, file_path, mime_type, is_primary_cv, is_active_attachment) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (payload["chat_id"], payload.get("telegram_file_id", ""), payload["file_name"], payload["file_path"], payload.get("mime_type", ""), 1 if payload.get("is_primary_cv") else 0, 1 if payload.get("is_active_attachment", True) else 0)
            )
            await db.commit()
            return cur.lastrowid

    async def list_user_files(self, chat_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM user_files WHERE chat_id = ? ORDER BY is_primary_cv DESC, id ASC", (chat_id,))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def create_application(self, payload: dict):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "INSERT INTO applications (chat_id, company, hr_email, available_positions_json, selected_position, subject, body, instructions, language, needs_review, confidence_json, attachments_json, raw_ai_json, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    payload["chat_id"], payload.get("company", ""), payload.get("hr_email", ""), json.dumps(payload.get("available_positions", []), ensure_ascii=False), payload.get("selected_position", ""), payload.get("subject", ""), payload.get("body", ""), payload.get("instructions", ""), payload.get("language", "id"), 1 if payload.get("needs_review", True) else 0, json.dumps(payload.get("confidence", {}), ensure_ascii=False), json.dumps(payload.get("attachments", []), ensure_ascii=False), json.dumps(payload.get("raw_ai_json", {}), ensure_ascii=False), payload.get("status", "draft")
                )
            )
            await db.commit()
            return cur.lastrowid

    async def get_application(self, app_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def mark_application_sent(self, app_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE applications SET status='sent', sent_at=CURRENT_TIMESTAMP WHERE id = ?", (app_id,))
            await db.commit()

    async def list_applications(self, chat_id: int, only_sent: bool = False):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            q = "SELECT * FROM applications WHERE chat_id = ?"
            if only_sent:
                q += " AND status='sent'"
            q += " ORDER BY id DESC LIMIT 50"
            cur = await db.execute(q, (chat_id,))
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def create_agent_run(self, chat_id: int, agent_type: str, input_text: str, result_json: dict):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("INSERT INTO agent_runs (chat_id, agent_type, input_text, result_json) VALUES (?, ?, ?, ?)", (chat_id, agent_type, input_text, json.dumps(result_json, ensure_ascii=False)))
            await db.commit()
            return cur.lastrowid

    async def create_repo_index(self, chat_id: int, repo_name: str, repo_path: str, index_json: dict):
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("INSERT INTO repo_indexes (chat_id, repo_name, repo_path, index_json) VALUES (?, ?, ?, ?)", (chat_id, repo_name, repo_path, json.dumps(index_json, ensure_ascii=False)))
            await db.commit()
            return cur.lastrowid
