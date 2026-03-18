from __future__ import annotations

from pathlib import Path
from PIL import Image
import google.generativeai as genai

from app.models.schemas import DraftPreview
from app.services.parser_service import extract_json_object

class AIService:
    def __init__(self, api_key: str, profile_text: str, prompt_template: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.profile_text = profile_text
        self.prompt_template = prompt_template

    def build_prompt(self) -> str:
        return self.prompt_template.replace("{{PROFILE_TEXT}}", self.profile_text)

    async def analyze_job_image(self, image_path: str | Path) -> tuple[DraftPreview, dict]:
        image = Image.open(image_path)
        response = self.model.generate_content([self.build_prompt(), image])
        raw_text = response.text.strip()
        data = extract_json_object(raw_text)
        preview = DraftPreview(
            company=data.get("company", ""),
            position=data.get("position", ""),
            email=data.get("email", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            instructions=data.get("instructions", ""),
            language=data.get("language", "id"),
            needs_review=data.get("needs_review", True),
            confidence=data.get("confidence", {}),
        )
        return preview, data
