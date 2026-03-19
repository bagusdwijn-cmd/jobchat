from __future__ import annotations
from pathlib import Path
import base64, requests
from app.services.providers.base import BaseProvider
from app.services.providers.exceptions import ProviderAuthError, ProviderModelError, ProviderError

class AnthropicProvider(BaseProvider):
    def _post(self, content):
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        payload = {"model": self.model, "max_tokens": 4096, "temperature": 0.2, "messages": [{"role": "user", "content": content}]}
        r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=120)
        if r.status_code in (401, 403):
            raise ProviderAuthError("API key Anthropic tidak valid atau tidak punya akses.")
        if r.status_code == 404:
            raise ProviderModelError(f"Model Anthropic '{self.model}' tidak tersedia.")
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise ProviderError(msg)
        data = r.json()
        text = "".join(x.get("text", "") for x in data.get("content", []) if x.get("type") == "text")
        return text, data

    def vision_json(self, image_path: str | Path):
        p = Path(image_path)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        content = [{"type": "text", "text": self.render_prompt()}, {"type": "image", "source": {"type": "base64", "media_type": mime, "data": base64.b64encode(p.read_bytes()).decode("utf-8")}}]
        return self._post(content)

    def text_json(self, prompt: str):
        return self._post([{"type": "text", "text": prompt}])
