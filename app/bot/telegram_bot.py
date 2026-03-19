from __future__ import annotations
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, Document
from aiogram.fsm.storage.memory import MemoryStorage
from app.bot.states import SetupStates, UploadStates
from app.services.providers.registry import SUPPORTED_PROVIDERS

def build_bot(token, storage, file_service, profile_service):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    router = Router()

    async def _safe_delete(message: Message):
        try:
            await message.delete()
        except Exception:
            pass

    @router.message(Command("start"))
    async def start(message: Message, state):
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer("Halo, kita setup dulu ya.\n\nLangkah 1/9:\nSilakan upload CV utama Anda (PDF/DOC/DOCX).")

    @router.message(Command("setup"))
    async def setup(message: Message, state):
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer("Setup diulang. Upload CV utama Anda.")

    @router.message(Command("setcv"))
    async def setcv(message: Message, state):
        await state.set_state(UploadStates.waiting_new_cv)
        await message.answer("Silakan upload CV utama baru.")

    @router.message(Command("tambahlampiran"))
    async def tambah(message: Message, state):
        await state.set_state(UploadStates.waiting_new_attachment)
        await message.answer("Silakan upload dokumen tambahan baru.")

    @router.message(Command("profil"))
    async def profil(message: Message):
        user = await storage.get_user(message.chat.id)
        if not user:
            await message.answer("Belum ada profil.")
            return
        await message.answer(
            "Profil:\n"
            f"Nama: {user.get('full_name') or '-'}\n"
            f"Title: {user.get('target_title') or '-'}\n"
            f"Skills: {user.get('skills') or '-'}\n"
            f"Provider: {user.get('ai_provider') or '-'}\n"
            f"Model: {user.get('ai_model') or '-'}\n"
            f"Base URL: {user.get('ai_base_url') or '-'}\n"
            f"Gmail: {user.get('gmail_address') or '-'}"
        )

    @router.message(Command("lampiran"))
    async def lampiran(message: Message):
        files = await storage.list_user_files(message.chat.id)
        if not files:
            await message.answer("Belum ada file tersimpan.")
            return
        lines = ["Lampiran aktif:"]
        for i, f in enumerate(files, start=1):
            kind = "CV Utama" if f.get("is_primary_cv") else "Dokumen"
            status = "aktif" if f.get("is_active_attachment") else "nonaktif"
            lines.append(f"{i}. {f['file_name']} — {kind} — {status}")
        await message.answer("\n".join(lines))

    @router.message(Command("daftar"))
    async def daftar(message: Message):
        apps = await storage.list_applications(message.chat.id, only_sent=True)
        if not apps:
            await message.answer("Belum ada lamaran terkirim.")
            return
        lines = ["Daftar lamaran terkirim:"]
        for i, app in enumerate(apps, start=1):
            lines.append(f"{i}. {app.get('company') or '-'} - {app.get('selected_position') or '-'}")
        await message.answer("\n".join(lines))

    @router.message(Command("help"))
    async def help_cmd(message: Message):
        await message.answer("/start\n/setup\n/profil\n/lampiran\n/setcv\n/tambahlampiran\n/daftar\n/help")

    @router.message(SetupStates.waiting_cv, F.document)
    async def setup_cv(message: Message, state):
        doc: Document = message.document
        path = file_service.cv_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or "", is_primary_cv=True, is_active_attachment=True)
        await state.set_state(SetupStates.waiting_attachment)
        await message.answer("CV utama tersimpan.\n\nLangkah 2/9:\nUpload dokumen tambahan satu per satu. Kalau selesai, ketik: selesai")

    @router.message(UploadStates.waiting_new_cv, F.document)
    async def replace_cv(message: Message, state):
        doc = message.document
        path = file_service.cv_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or "", is_primary_cv=True, is_active_attachment=True)
        await state.clear()
        await message.answer("CV utama berhasil diganti.")

    @router.message(UploadStates.waiting_new_attachment, F.document)
    async def new_attach(message: Message, state):
        doc = message.document
        path = file_service.attachment_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or "", is_primary_cv=False, is_active_attachment=True)
        await state.clear()
        await message.answer("Lampiran baru ditambahkan.")

    @router.message(SetupStates.waiting_attachment, F.document)
    async def setup_attachment(message: Message):
        doc = message.document
        path = file_service.attachment_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or "", is_primary_cv=False, is_active_attachment=True)
        await message.answer(f"Dokumen tersimpan: {doc.file_name}. Upload lagi atau ketik 'selesai'.")

    @router.message(SetupStates.waiting_attachment, F.text)
    async def finish_attachment(message: Message, state):
        if message.text.strip().lower() != "selesai":
            await message.answer("Upload lagi atau ketik 'selesai'.")
            return
        await state.set_state(SetupStates.waiting_provider)
        await message.answer("Langkah 3/9:\nPilih provider AI: " + " / ".join(SUPPORTED_PROVIDERS))

    @router.message(SetupStates.waiting_provider, F.text)
    async def provider(message: Message, state):
        provider = message.text.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            await message.answer("Provider tidak valid.")
            return
        await profile_service.save_provider(message.chat.id, provider)
        await state.update_data(provider=provider)
        await state.set_state(SetupStates.waiting_api_key)
        await message.answer("Langkah 4/9:\nKirim API key provider Anda.")

    @router.message(SetupStates.waiting_api_key, F.text)
    async def api_key(message: Message, state):
        await profile_service.save_api_key(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_model)
        await message.answer("Langkah 5/9:\nKirim model AI, atau ketik `default`.")

    @router.message(SetupStates.waiting_model, F.text)
    async def model(message: Message, state):
        data = await state.get_data()
        provider = data.get("provider", "gemini")
        await profile_service.save_model(message.chat.id, provider, message.text.strip())
        if provider == "custom_compatible":
            await state.set_state(SetupStates.waiting_base_url)
            await message.answer("Langkah 6/9:\nKirim base URL provider OpenAI-compatible Anda. Contoh: https://api.example.com/v1")
            return
        await profile_service.save_base_url(message.chat.id, "")
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer("Langkah 6/9:\nKirim alamat Gmail Anda.")

    @router.message(SetupStates.waiting_base_url, F.text)
    async def base_url(message: Message, state):
        await profile_service.save_base_url(message.chat.id, message.text.strip())
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer("Langkah 7/9:\nKirim alamat Gmail Anda.")

    @router.message(SetupStates.waiting_gmail, F.text)
    async def gmail(message: Message, state):
        await profile_service.save_gmail(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_gmail_pwd)
        await message.answer("Langkah 8/9:\nKirim App Password Gmail Anda.")

    @router.message(SetupStates.waiting_gmail_pwd, F.text)
    async def gmail_pwd(message: Message, state):
        await profile_service.save_gmail_app_password(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_profile)
        await message.answer("Langkah 9/9:\nKirim profil singkat Anda. Contoh:\nNama: ...\nTitle: ...\nSkills: ...\nPortfolio: ...\nLinkedIn: ...")

    @router.message(SetupStates.waiting_profile, F.text)
    async def profile(message: Message, state):
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
        await message.answer("✅ Setup selesai. Sekarang Anda bisa pakai web dan Telegram.")

    dp.include_router(router)
    return bot, dp
