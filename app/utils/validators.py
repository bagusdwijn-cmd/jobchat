from __future__ import annotations
import re
from email_validator import validate_email, EmailNotValidError

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

def looks_like_apply_form(text: str) -> bool:
    return bool(re.search(r"(apply via form|google form|jobstreet|linkedin|glints|bit\.ly|tinyurl)", text, re.I))

def redact_secrets(text: str) -> str:
    text = re.sub(r"AIza[0-9A-Za-z\-_]{20,}", "[REDACTED_API_KEY]", text)
    text = re.sub(r"sk-[A-Za-z0-9\-_]+", "[REDACTED_API_KEY]", text)
    text = re.sub(r"https?://\S+", "[URL_DIHAPUS]", text)
    return text
