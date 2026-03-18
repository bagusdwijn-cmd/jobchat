from __future__ import annotations

import base64
from pathlib import Path
import requests

from app.services.ai.base import BaseAIProvider

class OpenAICompatibleProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str, prompt_template: str, profile_text: str, base_url: str):
        super().__init__(api_key, model, prompt_template, profile_text)
        self.base_url = base_url.rstrip("/")

    def analyze_job_image(self, image_path: str | Path) -> tuple[str, dict]:
        image_path = Path(image_path)
        mime = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            mime = "image/png"
        data_uri = f"data:{mime};base64,{base64.b64encode(image_path.read_bytes()).decode('utf-8')}"

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.build_prompt()},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            "temperature": 0.2,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        return text, data
