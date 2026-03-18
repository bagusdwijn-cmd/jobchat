from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()

@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "/start - mulai setup\n"
        "/setup - ulang setup\n"
        "/profil - lihat profil\n"
        "/setcv - ganti CV utama\n"
        "/lampiran - lihat lampiran aktif\n"
        "/tambahlampiran - tambah dokumen pendukung\n"
        "/daftar - daftar lamaran terkirim\n"
        "/cancel - batalkan mode aktif\n\n"
        "Setelah setup, cukup kirim gambar lowongan."
    )

@router.message(Command("cancel"))
async def cancel_command(message: Message, state) -> None:
    await state.clear()
    await message.answer("Mode aktif dibatalkan.")
