from __future__ import annotations

from pydantic import BaseModel, Field

class ConfidenceScore(BaseModel):
    company: float = 0.0
    position: float = 0.0
    email: float = 0.0

class DraftPreview(BaseModel):
    company: str = ""
    position: str = ""
    email: str = ""
    subject: str = ""
    body: str = ""
    instructions: str = ""
    language: str = "id"
    needs_review: bool = True
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    warnings: list[str] = Field(default_factory=list)

class SetupProfile(BaseModel):
    full_name: str = ""
    target_title: str = ""
    skills: str = ""
    portfolio: str = ""
    linkedin: str = ""
    extra_notes: str = ""
