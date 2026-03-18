from __future__ import annotations

from pydantic import BaseModel, Field

class ConfidenceScore(BaseModel):
    company: float = 0.0
    email: float = 0.0
    positions: float = 0.0
    selected_position: float = 0.0

class DraftPreview(BaseModel):
    company: str = ""
    email: str = ""
    available_positions: list[str] = Field(default_factory=list)
    selected_position: str = ""
    subject: str = ""
    body: str = ""
    instructions: str = ""
    language: str = "id"
    needs_review: bool = True
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    warnings: list[str] = Field(default_factory=list)

class ProviderChoice(BaseModel):
    provider: str = "gemini"
    model: str = ""
