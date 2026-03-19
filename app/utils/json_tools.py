from __future__ import annotations
import json, re

def extract_json_object(text: str) -> dict:
    text = (text or "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError("JSON tidak ditemukan di output AI.")
    return json.loads(m.group(0))
