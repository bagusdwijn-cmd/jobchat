from __future__ import annotations
import asyncio
from pathlib import Path
from app.schemas import AutoApplyPreview
from app.utils.json_tools import extract_json_object
from app.services.providers.registry import build_provider

AUTO_APPLY_PROMPT = '''
Anda adalah asisten lamaran kerja yang sangat ketat terhadap akurasi.

PROFIL KANDIDAT:
{{PROFILE_TEXT}}

TUGAS:
1. Baca gambar lowongan kerja.
2. Ekstrak HANYA informasi yang benar-benar terlihat:
   - company
   - email
   - available_positions (array)
   - instructions
   - language
3. Jika lowongan memiliki beberapa posisi, pilih SATU posisi paling cocok untuk kandidat berdasarkan profil kandidat dan isi ke selected_position.
4. Buat subject email profesional sesuai posisi terpilih.
5. Buat body email/cover letter singkat, profesional, dan menyesuaikan posisi terpilih.
6. Jika email tidak jelas, kosongkan dan set needs_review=true.
7. Output HARUS JSON valid saja.

FORMAT JSON:
{
  "company": "",
  "email": "",
  "available_positions": [],
  "selected_position": "",
  "subject": "",
  "body": "",
  "instructions": "",
  "language": "id",
  "needs_review": true,
  "confidence": {
    "company": 0.0,
    "email": 0.0,
    "positions": 0.0,
    "selected_position": 0.0
  }
}
'''.strip()

BABYAGI_PROMPT = '''
Anda adalah autonomous task planner yang memecah goal besar menjadi langkah kecil yang dapat dieksekusi.

Buat output JSON valid:
{
  "goal": "...",
  "summary": "...",
  "steps": [
    {"title": "...", "action": "SEARCH_WEB|ANALYZE|DRAFT|REPORT", "details": "..."}
  ],
  "result": "..."
}
'''.strip()

CODY_PROMPT = '''
Anda adalah context-aware coding agent. Jawab pertanyaan user berdasarkan konteks repo yang diberikan.
Gunakan potongan file yang tersedia. Jangan mengarang file yang tidak ada.
Jawaban harus singkat, teknis, dan actionable.
'''.strip()

class AIService:
    def __init__(self, provider: str, api_key: str, model: str, profile_text: str, base_url: str = ""):
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.profile_text = profile_text
        self.base_url = base_url

    def _provider(self, prompt: str):
        return build_provider(self.provider, self.api_key, self.model, self.profile_text, prompt, self.base_url)

    async def analyze_job_image(self, image_path: str | Path):
        provider = self._provider(AUTO_APPLY_PROMPT)
        raw_text, raw_json = await asyncio.to_thread(provider.vision_json, image_path)
        data = extract_json_object(raw_text)
        preview = AutoApplyPreview(
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
        return preview, raw_json

    async def plan_tasks(self, goal: str, tool_context: str):
        provider = self._provider(BABYAGI_PROMPT)
        prompt = BABYAGI_PROMPT + "\n\nGOAL:\n" + goal + "\n\nKONTEKS ALAT:\n" + tool_context
        raw_text, raw_json = await asyncio.to_thread(provider.text_json, prompt)
        return extract_json_object(raw_text), raw_json

    async def answer_with_repo(self, question: str, repo_context: str):
        provider = self._provider(CODY_PROMPT)
        prompt = CODY_PROMPT + "\n\nPERTANYAAN USER:\n" + question + "\n\nKONTEKS REPO:\n" + repo_context
        return await asyncio.to_thread(provider.text_json, prompt)
