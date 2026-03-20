from __future__ import annotations
from pathlib import Path
import base64, requests
from app.services.providers.base import BaseProvider
from app.services.providers.exceptions import ProviderAuthError, ProviderModelError, ProviderError

FALLBACKS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]

class GeminiProvider(BaseProvider):
    def _call(self, model: str, parts: list[dict]):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json={"contents": [{"parts": parts}]}, timeout=120)
        if r.status_code in (401, 403):
            raise ProviderAuthError("API key Gemini tidak valid atau tidak punya akses.")
        if r.status_code == 404:
            raise ProviderModelError(f"Model Gemini '{model}' tidak tersedia.")
        if r.status_code >= 400:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:200])
            except Exception:
                msg = r.text[:200]
            raise ProviderError(msg)
        data = r.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, data

    def vision_json(self, image_path: str | Path):
        p = Path(image_path)
        mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        models = [self.model] if self.model else []
        for m in FALLBACKS:
            if m not in models:
                models.append(m)
        last = None
        for model in models:
            try:
                text, data = self._call(model, [{"text": self.render_prompt()}, {"inline_data": {"mime_type": mime, "data": base64.b64encode(p.read_bytes()).decode("utf-8")}}])
                data["_resolved_model"] = model
                return text, data
            except ProviderModelError as e:
                last = e
                continue
        if last:
            raise last
        raise ProviderError("Gemini gagal memproses gambar.")

    def text_json(self, prompt: str):
        models = [self.model] if self.model else []
        for m in FALLBACKS:
            if m not in models:
                models.append(m)
        last = None
        for model in models:
            try:
                text, data = self._call(model, [{"text": prompt}])
                data["_resolved_model"] = model
                return text, data
            except ProviderModelError as e:
                last = e
                continue
        if last:
            raise last
        raise ProviderError("Gemini gagal memproses teks.")
