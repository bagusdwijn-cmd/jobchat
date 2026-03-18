from __future__ import annotations

from app.utils.security import SecretBox

DEFAULT_MODELS = {
    "gemini": "gemini-1.5-flash-latest",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
}

class UserProfileService:
    def __init__(self, storage, secret_box: SecretBox):
        self.storage = storage
        self.secret_box = secret_box

    async def save_ai_provider(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "ai_provider", value.strip().lower())

    async def save_ai_key(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "ai_api_key_encrypted", self.secret_box.encrypt(value.strip()))

    async def save_ai_model(self, chat_id: int, value: str, provider: str) -> None:
        model = value.strip()
        if model.lower() == "default" or not model:
            model = DEFAULT_MODELS.get(provider, "")
        await self.storage.update_user_field(chat_id, "ai_model", model)

    async def save_gmail_address(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "gmail_address", value.strip())

    async def save_gmail_app_password(self, chat_id: int, value: str) -> None:
        await self.storage.update_user_field(chat_id, "gmail_app_password_encrypted", self.secret_box.encrypt(value.strip()))

    async def read_secrets(self, chat_id: int) -> dict[str, str]:
        user = await self.storage.get_user(chat_id)
        if not user:
            return {"ai_provider": "", "ai_model": "", "ai_api_key": "", "gmail_app_password": "", "gmail_address": ""}
        return {
            "ai_provider": user.get("ai_provider", ""),
            "ai_model": user.get("ai_model", ""),
            "ai_api_key": self.secret_box.decrypt(user.get("ai_api_key_encrypted")),
            "gmail_app_password": self.secret_box.decrypt(user.get("gmail_app_password_encrypted")),
            "gmail_address": user.get("gmail_address", ""),
        }
