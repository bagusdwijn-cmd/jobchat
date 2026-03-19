from __future__ import annotations
from app.services.providers.gemini import GeminiProvider
from app.services.providers.openai_compatible import OpenAICompatibleProvider
from app.services.providers.anthropic import AnthropicProvider

DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "openrouter": "openai/gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "groq": "llama-3.2-90b-vision-preview",
    "together": "meta-llama/Llama-3.2-90B-Vision-Instruct-Turbo",
    "custom_compatible": "gpt-4o-mini",
}
DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
}
SUPPORTED_PROVIDERS = list(DEFAULT_MODELS.keys())

def build_provider(provider: str, api_key: str, model: str, profile_text: str, prompt: str, base_url: str = ""):
    provider = (provider or "").strip().lower()
    model = model.strip() if model else DEFAULT_MODELS.get(provider, "")
    if provider == "gemini":
        return GeminiProvider(api_key, model, profile_text, prompt)
    if provider == "anthropic":
        return AnthropicProvider(api_key, model, profile_text, prompt)
    if provider in {"openai", "openrouter", "groq", "together"}:
        return OpenAICompatibleProvider(api_key, model, profile_text, prompt, DEFAULT_BASE_URLS[provider])
    if provider == "custom_compatible":
        return OpenAICompatibleProvider(api_key, model, profile_text, prompt, base_url)
    raise ValueError(f"Provider tidak didukung: {provider}")
