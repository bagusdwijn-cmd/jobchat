from __future__ import annotations

from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_compatible_provider import OpenAICompatibleProvider

def create_ai_provider(provider: str, api_key: str, model: str, prompt_template: str, profile_text: str):
    provider = (provider or "").strip().lower()
    if provider == "gemini":
        return GeminiProvider(api_key, model, prompt_template, profile_text)
    if provider == "openai":
        return OpenAICompatibleProvider(api_key, model, prompt_template, profile_text, "https://api.openai.com/v1")
    if provider == "openrouter":
        return OpenAICompatibleProvider(api_key, model, prompt_template, profile_text, "https://openrouter.ai/api/v1")
    raise ValueError(f"AI provider tidak didukung: {provider}")
