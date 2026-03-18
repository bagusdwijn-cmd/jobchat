from __future__ import annotations

import logging
from pathlib import Path

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext

from app.handlers.states import SetupStates, UploadModeStates

logger = logging.getLogger(__name__)

def get_router(storage, file_service, profile_service) -> Router:
    router = Router()

    async def _safe_delete_user_message(message: Message) -> None:
        try:
            await message.delete()
        except Exception:
            pass

    @router.message(Command("start"))
    async def start_command(message: Message, state: FSMContext) -> None:
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer(
            "Halo, kita setup dulu ya.\n\n"
            "Langkah 1/6:\n"
            "Silakan upload CV utama Anda (PDF/DOC/DOCX)."
        )

    @router.message(Command("setup"))
    async def setup_command(message: Message, state: FSMContext) -> None:
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer("Setup diulang. Silakan upload CV utama Anda.")

    @router.message(Command("setcv"))
    async def setcv_command(message: Message, state: FSMContext) -> None:
        await state.set_state(UploadModeStates.waiting_new_cv)
        await message.answer("Silakan upload CV utama baru Anda (PDF/DOC/DOCX).")

    @router.message(Command("tambahlampiran"))
    async def add_attachment_command(message: Message, state: FSMContext) -> None:
        await state.set_state(UploadModeStates.waiting_new_attachment)
        await message.answer("Silakan upload dokumen pendukung baru.")

    @router.message(SetupStates.waiting_cv, F.document)
    async def handle_setup_cv(message: Message, state: FSMContext) -> None:
        doc: Document = message.document
        target_dir = file_service.cv_dir(message.chat.id)
        path = target_dir / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(
            chat_id=message.chat.id,
            telegram_file_id=doc.file_id,
            file_name=doc.file_name,
            file_path=str(path),
            mime_type=doc.mime_type or "",
            is_primary_cv=True,
            is_active_attachment=True,
        )
        await state.set_state(SetupStates.waiting_attachment)
        await message.answer(
            "CV utama tersimpan.\n\n"
            "Langkah 2/6:\n"
            "Upload dokumen pendukung satu per satu.\n"
            "Kalau sudah selesai, ketik: selesai"
        )

    @router.message(UploadModeStates.waiting_new_cv, F.document)
    async def handle_replace_cv(message: Message, state: FSMContext) -> None:
        doc: Document = message.document
        target_dir = file_service.cv_dir(message.chat.id)
        path = target_dir / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(
            chat_id=message.chat.id,
            telegram_file_id=doc.file_id,
            file_name=doc.file_name,
            file_path=str(path),
            mime_type=doc.mime_type or "",
            is_primary_cv=True,
            is_active_attachment=True,
        )
        await state.clear()
        await message.answer(f"✅ CV utama diganti menjadi: {doc.file_name}")

    @router.message(UploadModeStates.waiting_new_attachment, F.document)
    async def handle_new_attachment(message: Message, state: FSMContext) -> None:
        doc: Document = message.document
        target_dir = file_service.attachment_dir(message.chat.id)
        path = target_dir / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(
            chat_id=message.chat.id,
            telegram_file_id=doc.file_id,
            file_name=doc.file_name,
            file_path=str(path),
            mime_type=doc.mime_type or "",
            is_primary_cv=False,
            is_active_attachment=True,
        )
        await state.clear()
        await message.answer(f"✅ Lampiran ditambahkan: {doc.file_name}")

    @router.message(SetupStates.waiting_attachment, F.document)
    async def handle_setup_attachment(message: Message) -> None:
        doc: Document = message.document
        target_dir = file_service.attachment_dir(message.chat.id)
        path = target_dir / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(
            chat_id=message.chat.id,
            telegram_file_id=doc.file_id,
            file_name=doc.file_name,
            file_path=str(path),
            mime_type=doc.mime_type or "",
            is_primary_cv=False,
            is_active_attachment=True,
        )
        await message.answer(f"Dokumen tersimpan: {doc.file_name}\nUpload lagi atau ketik 'selesai'.")

    @router.message(SetupStates.waiting_attachment, F.text)
    async def finish_attachment_step(message: Message, state: FSMContext) -> None:
        if message.text.strip().lower() != "selesai":
            await message.answer("Upload dokumen lagi atau ketik 'selesai'.")
            return
        await state.set_state(SetupStates.waiting_gemini_key)
        await message.answer("Langkah 3/6:\nKirim Gemini API Key Anda.")

    @router.message(SetupStates.waiting_gemini_key, F.text)
    async def handle_gemini_key(message: Message, state: FSMContext) -> None:
        await profile_service.save_gemini_key(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer("API Key diterima dan disimpan aman.\n\nLangkah 4/6:\nKirim alamat Gmail Anda.")

    @router.message(SetupStates.waiting_gmail, F.text)
    async def handle_gmail(message: Message, state: FSMContext) -> None:
        await profile_service.save_gmail_address(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        await state.set_state(SetupStates.waiting_app_password)
        await message.answer("Alamat Gmail diterima.\n\nLangkah 5/6:\nKirim App Password Gmail Anda.")

    @router.message(SetupStates.waiting_app_password, F.text)
    async def handle_app_password(message: Message, state: FSMContext) -> None:
        await profile_service.save_gmail_app_password(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        await state.set_state(SetupStates.waiting_profile)
        await message.answer(
            "App Password diterima.\n\n"
            "Langkah 6/6:\n"
            "Kirim profil singkat Anda. Contoh:\n"
            "Nama: Bagus Dwi\n"
            "Title: Senior Fullstack Engineer\n"
            "Skills: React, Node.js, Tailwind\n"
            "Portfolio: ...\n"
            "LinkedIn: ..."
        )

    @router.message(SetupStates.waiting_profile, F.text)
    async def handle_profile(message: Message, state: FSMContext) -> None:
        text = message.text.strip()
        await storage.update_user_field(message.chat.id, "extra_notes", text)
        full_name = ""
        target_title = ""
        skills = ""
        portfolio = ""
        linkedin = ""
        for line in text.splitlines():
            low = line.lower()
            if low.startswith("nama:"):
                full_name = line.split(":", 1)[1].strip()
            elif low.startswith("title:"):
                target_title = line.split(":", 1)[1].strip()
            elif low.startswith("skills:"):
                skills = line.split(":", 1)[1].strip()
            elif low.startswith("portfolio:"):
                portfolio = line.split(":", 1)[1].strip()
            elif low.startswith("linkedin:"):
                linkedin = line.split(":", 1)[1].strip()

        if full_name:
            await storage.update_user_field(message.chat.id, "full_name", full_name)
        if target_title:
            await storage.update_user_field(message.chat.id, "target_title", target_title)
        if skills:
            await storage.update_user_field(message.chat.id, "skills", skills)
        if portfolio:
            await storage.update_user_field(message.chat.id, "portfolio", portfolio)
        if linkedin:
            await storage.update_user_field(message.chat.id, "linkedin", linkedin)

        await storage.update_user_field(message.chat.id, "setup_completed", 1)
        await state.clear()
        await message.answer("✅ Setup selesai. Sekarang Anda bisa langsung kirim gambar lowongan kapan saja.")

    return router
