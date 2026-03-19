from __future__ import annotations
from app.utils.security import SecretBox
from app.services.providers.registry import DEFAULT_MODELS

class UserProfileService:
    def __init__(self, storage, secret_box: SecretBox):
        self.storage = storage
        self.secret_box = secret_box

    async def save_provider(self, chat_id: int, provider: str):
        await self.storage.update_user_field(chat_id, "ai_provider", provider)

    async def save_api_key(self, chat_id: int, api_key: str):
        await self.storage.update_user_field(chat_id, "ai_api_key_encrypted", self.secret_box.encrypt(api_key))

    async def save_model(self, chat_id: int, provider: str, model: str):
        value = model.strip()
        if not value or value.lower() == "default":
            value = DEFAULT_MODELS.get(provider, "")
        await self.storage.update_user_field(chat_id, "ai_model", value)

    async def save_base_url(self, chat_id: int, base_url: str):
        await self.storage.update_user_field(chat_id, "ai_base_url", base_url.strip())

    async def save_gmail(self, chat_id: int, gmail: str):
        await self.storage.update_user_field(chat_id, "gmail_address", gmail.strip())

    async def save_gmail_app_password(self, chat_id: int, pwd: str):
        await self.storage.update_user_field(chat_id, "gmail_app_password_encrypted", self.secret_box.encrypt(pwd.strip()))

    async def secrets(self, chat_id: int):
        user = await self.storage.get_user(chat_id)
        if not user:
            return {}
        return {
            "provider": user.get("ai_provider", ""),
            "model": user.get("ai_model", ""),
            "base_url": user.get("ai_base_url", ""),
            "api_key": self.secret_box.decrypt(user.get("ai_api_key_encrypted")),
            "gmail": user.get("gmail_address", ""),
            "gmail_app_password": self.secret_box.decrypt(user.get("gmail_app_password_encrypted")),
        }
