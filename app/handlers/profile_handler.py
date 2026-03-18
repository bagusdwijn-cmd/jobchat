from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

def get_router(storage) -> Router:
    router = Router()

    @router.message(Command("profil"))
    async def profil_command(message: Message) -> None:
        user = await storage.get_user(message.chat.id)
        if not user:
            await message.answer("Belum ada data profil. Ketik /start untuk setup.")
            return
        await message.answer(
            "📌 Profil Tersimpan\n\n"
            f"Nama: {user.get('full_name') or '-'}\n"
            f"Title: {user.get('target_title') or '-'}\n"
            f"Skills: {user.get('skills') or '-'}\n"
            f"Portfolio: {user.get('portfolio') or '-'}\n"
            f"LinkedIn: {user.get('linkedin') or '-'}\n"
            f"Setup selesai: {'Ya' if user.get('setup_completed') else 'Belum'}\n"
            f"Gmail: {user.get('gmail_address') or '-'}"
        )

    @router.message(Command("lampiran"))
    async def lampiran_command(message: Message) -> None:
        files = await storage.list_user_files(message.chat.id)
        if not files:
            await message.answer("Belum ada file tersimpan.")
            return

        lines = ["📎 Lampiran Aktif"]
        for i, f in enumerate(files, start=1):
            kind = "CV Utama" if f.get("is_primary_cv") else "Dokumen"
            status = "aktif" if f.get("is_active_attachment") else "nonaktif"
            lines.append(f"{i}. {f.get('file_name')} — {kind} — {status}")
        await message.answer("\n".join(lines))

    return router
