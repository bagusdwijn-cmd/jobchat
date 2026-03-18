from __future__ import annotations

import json
import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message

from app.models.schemas import DraftPreview
from app.services.ai_service import AIService
from app.services.telegram_ui import preview_keyboard
from app.utils.validators import validate_preview

logger = logging.getLogger(__name__)

def build_profile_text(user: dict) -> str:
    return (
        f"Nama: {user.get('full_name', '')}\n"
        f"Title: {user.get('target_title', '')}\n"
        f"Skills: {user.get('skills', '')}\n"
        f"Portfolio: {user.get('portfolio', '')}\n"
        f"LinkedIn: {user.get('linkedin', '')}\n"
        f"Catatan tambahan: {user.get('extra_notes', '')}"
    )

def compact_preview_text(preview: DraftPreview, attachments: list[dict]) -> str:
    attachment_names = [a.get("file_name", "-") for a in attachments]
    text = (
        f"Perusahaan: {preview.company or '-'}\n"
        f"Email HR: {preview.email or '-'}\n\n"
        f"Pesan Gmail:\n{preview.body or '-'}\n\n"
        f"Lampiran:\n- " + "\n- ".join(attachment_names if attachment_names else ["Tidak ada"])
    )
    if preview.warnings:
        text += "\n\n⚠️ Warning:\n- " + "\n- ".join(preview.warnings)
    return text

def get_router(storage, profile_service, file_service, prompt_template: str) -> Router:
    router = Router()

    @router.message(F.photo)
    async def handle_job_image(message: Message) -> None:
        user = await storage.get_user(message.chat.id)
        if not user or not user.get("setup_completed"):
            await message.answer("Setup belum selesai. Ketik /start dulu ya.")
            return

        secrets = await profile_service.read_secrets(message.chat.id)
        if not secrets["gemini_api_key"] or not secrets["gmail_address"] or not secrets["gmail_app_password"]:
            await message.answer("Kredensial belum lengkap. Jalankan /setup.")
            return

        processing = await message.answer("⏳ Sedang membaca lowongan...")

        photo = message.photo[-1]
        job_dir = file_service.job_dir(message.chat.id)
        image_path = job_dir / f"{photo.file_id}.jpg"
        file = await message.bot.get_file(photo.file_id)
        await message.bot.download(file, destination=image_path)

        try:
            ai_service = AIService(
                api_key=secrets["gemini_api_key"],
                profile_text=build_profile_text(user),
                prompt_template=prompt_template,
            )
            preview, raw_json = await ai_service.analyze_job_image(image_path)
            preview = validate_preview(preview)

            attachments = [
                {
                    "id": f["id"],
                    "file_name": f["file_name"],
                    "file_path": f["file_path"],
                }
                for f in await storage.list_user_files(message.chat.id)
                if f.get("is_active_attachment")
            ]

            app_id = await storage.create_application(
                {
                    "chat_id": message.chat.id,
                    "company": preview.company,
                    "position": preview.position,
                    "hr_email": preview.email,
                    "subject": preview.subject,
                    "body": preview.body,
                    "instructions": preview.instructions,
                    "language": preview.language,
                    "needs_review": preview.needs_review,
                    "confidence": preview.confidence.model_dump(),
                    "attachments": attachments,
                    "raw_ai_json": raw_json,
                    "status": "draft",
                }
            )

            await processing.edit_text(
                compact_preview_text(preview, attachments),
                reply_markup=preview_keyboard(app_id),
            )
        except Exception as exc:
            logger.exception("Failed to analyze image")
            await processing.edit_text(f"❌ Gagal memproses lowongan: {exc}")

    return router
