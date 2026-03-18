from __future__ import annotations

import base64
from pathlib import Path
import requests

from app.services.ai.base import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def analyze_job_image(self, image_path: str | Path) -> tuple[str, dict]:
        image_path = Path(image_path)
        mime = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            mime = "image/png"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": self.build_prompt()},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": base64.b64encode(image_path.read_bytes()).decode("utf-8"),
                            }
                        },
                    ]
                }
            ]
        }
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, data
