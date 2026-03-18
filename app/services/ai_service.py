from __future__ import annotations

import asyncio
from pathlib import Path

from app.models.schemas import DraftPreview
from app.services.ai.factory import create_ai_provider
from app.services.parser_service import extract_json_object

class AIService:
    def __init__(self, provider: str, api_key: str, model: str, profile_text: str, prompt_template: str):
        self.provider = create_ai_provider(provider, api_key, model, prompt_template, profile_text)

    async def analyze_job_image(self, image_path: str | Path) -> tuple[DraftPreview, dict]:
        raw_text, raw_json = await asyncio.to_thread(self.provider.analyze_job_image, image_path)
        data = extract_json_object(raw_text)
        preview = DraftPreview(
            company=data.get("company", ""),
            email=data.get("email", ""),
            available_positions=data.get("available_positions", []) or [],
            selected_position=data.get("selected_position", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            instructions=data.get("instructions", ""),
            language=data.get("language", "id"),
            needs_review=data.get("needs_review", True),
            confidence=data.get("confidence", {}),
        )
        return preview, data
