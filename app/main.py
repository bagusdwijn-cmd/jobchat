from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings, BASE_DIR
from app.utils.logger import setup_logger
from app.utils.security import SecretBox
from app.services.storage_service import StorageService
from app.services.file_service import FileService
from app.services.user_profile_service import UserProfileService

from app.handlers.setup_handler import get_router as get_setup_router
from app.handlers.profile_handler import get_router as get_profile_router
from app.handlers.job_handler import get_router as get_job_router
from app.handlers.callback_handler import get_router as get_callback_router
from app.handlers.list_handler import get_router as get_list_router
from app.handlers.help_handler import router as help_router

async def main() -> None:
    settings = get_settings()
    if not settings.bot_token:
        raise RuntimeError("APP_BOT_TOKEN belum diisi di .env")
    if not settings.master_encryption_key:
        raise RuntimeError("MASTER_ENCRYPTION_KEY belum diisi di .env")

    setup_logger(settings.log_level)

    storage = StorageService(settings.db_path)
    await storage.init()

    secret_box = SecretBox(settings.master_encryption_key)
    file_service = FileService(BASE_DIR / "storage")
    profile_service = UserProfileService(storage, secret_box)

    prompt_template = (BASE_DIR / "app" / "templates" / "job_prompt.txt").read_text(encoding="utf-8")

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(help_router)
    dp.include_router(get_setup_router(storage, file_service, profile_service))
    dp.include_router(get_profile_router(storage))
    dp.include_router(get_list_router(storage))
    dp.include_router(get_job_router(storage, profile_service, file_service, prompt_template))
    dp.include_router(get_callback_router(storage, profile_service))

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
