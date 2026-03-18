from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, Document
from aiogram.fsm.context import FSMContext

from app.handlers.states import SetupStates, UploadModeStates

SUPPORTED_PROVIDERS = {"gemini", "openai", "openrouter"}

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
        await message.answer("Halo, kita setup dulu ya.\n\nLangkah 1/8:\nSilakan upload CV utama Anda (PDF/DOC/DOCX).")

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
        await message.answer("CV utama tersimpan.\n\nLangkah 2/8:\nUpload dokumen pendukung satu per satu.\nKalau sudah selesai, ketik: selesai")

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
        await state.set_state(SetupStates.waiting_provider)
        await message.answer("Langkah 3/8:\nPilih AI provider: gemini / openai / openrouter")

    @router.message(SetupStates.waiting_provider, F.text)
    async def handle_provider(message: Message, state: FSMContext) -> None:
        provider = message.text.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            await message.answer("Provider tidak valid. Pilih: gemini / openai / openrouter")
            return
        await profile_service.save_ai_provider(message.chat.id, provider)
        await state.update_data(ai_provider=provider)
        await state.set_state(SetupStates.waiting_ai_key)
        await message.answer("Langkah 4/8:\nKirim API key AI provider Anda.")

    @router.message(SetupStates.waiting_ai_key, F.text)
    async def handle_ai_key(message: Message, state: FSMContext) -> None:
        await profile_service.save_ai_key(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        data = await state.get_data()
        provider = data.get("ai_provider", "gemini")
        await state.set_state(SetupStates.waiting_ai_model)
        await message.answer(f"API key {provider} diterima dan disimpan aman.\n\nLangkah 5/8:\nKirim model AI Anda, atau ketik `default`.")

    @router.message(SetupStates.waiting_ai_model, F.text)
    async def handle_ai_model(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        provider = data.get("ai_provider", "gemini")
        await profile_service.save_ai_model(message.chat.id, message.text.strip(), provider)
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer("Langkah 6/8:\nKirim alamat Gmail Anda.")

    @router.message(SetupStates.waiting_gmail, F.text)
    async def handle_gmail(message: Message, state: FSMContext) -> None:
        await profile_service.save_gmail_address(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        await state.set_state(SetupStates.waiting_app_password)
        await message.answer("Langkah 7/8:\nKirim App Password Gmail Anda.")

    @router.message(SetupStates.waiting_app_password, F.text)
    async def handle_app_password(message: Message, state: FSMContext) -> None:
        await profile_service.save_gmail_app_password(message.chat.id, message.text.strip())
        await _safe_delete_user_message(message)
        await state.set_state(SetupStates.waiting_profile)
        await message.answer(
            "Langkah 8/8:\n"
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
        mapping = {"nama:": "full_name", "title:": "target_title", "skills:": "skills", "portfolio:": "portfolio", "linkedin:": "linkedin"}
        for line in text.splitlines():
            low = line.lower().strip()
            for prefix, field_name in mapping.items():
                if low.startswith(prefix):
                    value = line.split(":", 1)[1].strip()
                    if value:
                        await storage.update_user_field(message.chat.id, field_name, value)

        await storage.update_user_field(message.chat.id, "setup_completed", 1)
        await state.clear()
        await message.answer("✅ Setup selesai. Sekarang Anda bisa langsung kirim gambar lowongan kapan saja.")

    return router
