from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

def get_router(storage) -> Router:
    router = Router()

    @router.message(Command("daftar"))
    async def daftar_command(message: Message) -> None:
        apps = await storage.list_applications(message.chat.id, only_sent=True)
        if not apps:
            await message.answer("Belum ada lamaran yang terkirim.")
            return

        lines = ["Daftar lamaran terkirim:\n"]
        for i, app in enumerate(apps, start=1):
            lines.append(
                f"{i}. {app.get('company') or '-'} - {app.get('selected_position') or '-'}\n"
                f"   Email: {app.get('hr_email') or '-'}\n"
                f"   Status: {app.get('status') or '-'}\n"
                f"   Waktu: {app.get('sent_at') or app.get('created_at')}"
            )
        await message.answer("\n\n".join(lines))

    return router
