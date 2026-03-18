from __future__ import annotations

from app.utils.security import SecretBox

class UserProfileService:
    def __init__(self, storage, secret_box: SecretBox):
        self.storage = storage
        self.secret_box = secret_box

    async def save_gemini_key(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "gemini_api_key_encrypted", self.secret_box.encrypt(value))

    async def save_gmail_address(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "gmail_address", value.strip())

    async def save_gmail_app_password(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "gmail_app_password_encrypted", self.secret_box.encrypt(value.strip()))

    async def read_secrets(self, chat_id: int) -> dict[str, str]:
        user = await self.storage.get_user(chat_id)
        if not user:
            return {"gemini_api_key": "", "gmail_app_password": "", "gmail_address": ""}
        return {
            "gemini_api_key": self.secret_box.decrypt(user.get("gemini_api_key_encrypted")),
            "gmail_app_password": self.secret_box.decrypt(user.get("gmail_app_password_encrypted")),
            "gmail_address": user.get("gmail_address", ""),
        }
