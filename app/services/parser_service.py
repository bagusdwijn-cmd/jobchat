from __future__ import annotations

import json
import re

def extract_json_object(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not match:
        raise ValueError("JSON tidak ditemukan pada respons AI.")
    return json.loads(match.group(0))
