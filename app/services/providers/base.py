from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path

class BaseProvider(ABC):
    def __init__(self, api_key: str, model: str, profile_text: str, prompt: str, base_url: str = ""):
        self.api_key = api_key
        self.model = model
        self.profile_text = profile_text
        self.prompt = prompt
        self.base_url = base_url

    def render_prompt(self) -> str:
        return self.prompt.replace("{{PROFILE_TEXT}}", self.profile_text)

    @abstractmethod
    def vision_json(self, image_path: str | Path) -> tuple[str, dict]:
        raise NotImplementedError

    @abstractmethod
    def text_json(self, prompt: str) -> tuple[str, dict]:
        raise NotImplementedError
