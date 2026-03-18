from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

class BaseAIProvider(ABC):
    def __init__(self, api_key: str, model: str, prompt_template: str, profile_text: str):
        self.api_key = api_key
        self.model = model
        self.prompt_template = prompt_template
        self.profile_text = profile_text

    def build_prompt(self) -> str:
        return self.prompt_template.replace("{{PROFILE_TEXT}}", self.profile_text)

    @abstractmethod
    def analyze_job_image(self, image_path: str | Path) -> tuple[str, dict]:
        raise NotImplementedError
