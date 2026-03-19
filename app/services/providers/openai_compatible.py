from __future__ import annotations
from pathlib import Path
import base64, requests
from app.services.providers.base import BaseProvider
from app.services.providers.exceptions import ProviderAuthError, ProviderModelError, ProviderError

class OpenAICompatibleProvider(BaseProvider):
    def __init__(self, api_key: str, model: str, profile_text: str, prompt: str, base_url: str):
        super().__init__(api_key, model, profile_text, prompt, base_url)

    def _post(self, payload: dict):
        url = self.base_url.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        if r.status_code in (401, 403):
            raise ProviderAuthError("API key provider tidak valid atau tidak punya akses.")
        if r.status_code == 404:
            raise ProviderModelError(f"Model '{self.model}' tidak tersedia pada provider ini.")
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise ProviderError(msg)
        data = r.json()
        return data["choices"][0]["message"]["content"], data

    def vision_json(self, image_path: str | Path):
        p = Path(image_path)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        data_uri = f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode('utf-8')}"
        payload = {"model": self.model, "messages": [{"role": "user", "content": [{"type": "text", "text": self.render_prompt()}, {"type": "image_url", "image_url": {"url": data_uri}}]}], "temperature": 0.2}
        return self._post(payload)

    def text_json(self, prompt: str):
        payload = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.2}
        return self._post(payload)
