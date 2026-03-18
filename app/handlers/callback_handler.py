from __future__ import annotations

import json

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.handlers.states import EditStates
from app.models.schemas import DraftPreview
from app.services.telegram_ui import preview_keyboard, edit_keyboard
from app.utils.validators import validate_preview
from app.services.mail_service import MailService

def _compact_preview(app: dict) -> str:
    attachments = json.loads(app.get("attachments_json", "[]") or "[]")
    warnings = []
    confidence = json.loads(app.get("confidence_json", "{}") or "{}")
    preview = DraftPreview(
        company=app.get("company", ""),
        position=app.get("position", ""),
        email=app.get("hr_email", ""),
        subject=app.get("subject", ""),
        body=app.get("body", ""),
        instructions=app.get("instructions", ""),
        language=app.get("language", "id"),
        needs_review=bool(app.get("needs_review", 1)),
        confidence=confidence,
    )
    preview = validate_preview(preview)
    lines = [
        f"Perusahaan: {preview.company or '-'}",
        f"Email HR: {preview.email or '-'}",
        "",
        "Pesan Gmail:",
        preview.body or "-",
        "",
        "Lampiran:",
    ]
    if attachments:
        lines.extend([f"- {x.get('file_name')}" for x in attachments])
    else:
        lines.append("- Tidak ada")
    if preview.warnings:
        lines.extend(["", "⚠️ Warning:"])
        lines.extend([f"- {w}" for w in preview.warnings])
    return "\n".join(lines)

def get_router(storage, profile_service) -> Router:
    router = Router()

    @router.callback_query(F.data.startswith("send:"))
    async def send_callback(callback: CallbackQuery) -> None:
        app_id = int(callback.data.split(":")[1])
        app = await storage.get_application(app_id)
        user = await storage.get_user(callback.message.chat.id)
        if not app or not user:
            await callback.answer("Data tidak ditemukan", show_alert=True)
            return

        secrets = await profile_service.read_secrets(callback.message.chat.id)
        mail = MailService(
            gmail_address=secrets["gmail_address"],
            gmail_app_password=secrets["gmail_app_password"],
        )
        attachments = json.loads(app.get("attachments_json", "[]") or "[]")
        try:
            mail.send_email(
                to_email=app["hr_email"],
                subject=app["subject"],
                body=app["body"],
                attachments=attachments,
            )
            await storage.mark_application_sent(app_id)
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"✅ Email berhasil dikirim ke {app['hr_email']}")
        except Exception as exc:
            await storage.update_application_field(app_id, "status", "failed")
            await callback.message.answer(f"❌ Gagal mengirim email: {exc}")
        await callback.answer()

    @router.callback_query(F.data.startswith("cancel:"))
    async def cancel_callback(callback: CallbackQuery) -> None:
        app_id = int(callback.data.split(":")[1])
        await storage.update_application_field(app_id, "status", "cancelled")
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer("Dibatalkan. Email tidak dikirim.")
        await callback.answer()

    @router.callback_query(F.data.startswith("edit:"))
    async def edit_callback(callback: CallbackQuery) -> None:
        app_id = int(callback.data.split(":")[1])
        await callback.message.answer("Pilih yang ingin diubah:", reply_markup=edit_keyboard(app_id))
        await callback.answer()

    @router.callback_query(F.data.startswith("back:"))
    async def back_callback(callback: CallbackQuery) -> None:
        app_id = int(callback.data.split(":")[1])
        app = await storage.get_application(app_id)
        if not app:
            await callback.answer("Data tidak ditemukan", show_alert=True)
            return
        await callback.message.answer(_compact_preview(app), reply_markup=preview_keyboard(app_id))
        await callback.answer()

    @router.callback_query(F.data.startswith("editfield:"))
    async def edit_field_callback(callback: CallbackQuery, state: FSMContext) -> None:
        _, app_id, field_name = callback.data.split(":")
        await state.update_data(app_id=int(app_id), field_name=field_name)
        await state.set_state(EditStates.waiting_value)
        await callback.message.answer(f"Kirim nilai baru untuk: {field_name}")
        await callback.answer()

    @router.message(EditStates.waiting_value)
    async def edit_value_message(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        app_id = int(data["app_id"])
        field_name = data["field_name"]
        await storage.update_application_field(app_id, field_name, message.text.strip())
        app = await storage.get_application(app_id)
        if not app:
            await message.answer("Data tidak ditemukan.")
            await state.clear()
            return
        await message.answer("✅ Draft diperbarui.\n\n" + _compact_preview(app), reply_markup=preview_keyboard(app_id))
        await state.clear()

    return router
