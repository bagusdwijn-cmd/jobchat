from __future__ import annotations

import re
from email_validator import validate_email, EmailNotValidError
from app.models.schemas import DraftPreview

def normalize_email(value: str) -> str:
    return (value or "").strip().replace(" ", "").replace("\n", "").lower()

def is_valid_email(value: str) -> bool:
    if not value:
        return False
    try:
        validate_email(value, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False

def looks_like_form(text: str) -> bool:
    return bool(re.search(r"(apply via form|google form|jobstreet|linkedin|glints|bit\.ly|tinyurl)", text, re.I))

def validate_preview(draft: DraftPreview) -> DraftPreview:
    draft.email = normalize_email(draft.email)
    warnings = []

    if not is_valid_email(draft.email):
        warnings.append("Email HR tidak valid atau tidak jelas.")
        draft.needs_review = True

    if len((draft.body or "").strip()) < 60:
        warnings.append("Pesan terlalu pendek.")
        draft.needs_review = True

    joined = " ".join([draft.instructions, draft.body, draft.subject, draft.company, draft.position])
    if looks_like_form(joined):
        warnings.append("Terindikasi apply via form/link, bukan email.")
        draft.needs_review = True

    if draft.confidence.email < 0.80:
        warnings.append("Confidence email rendah.")
        draft.needs_review = True

    draft.warnings = warnings
    return draft
