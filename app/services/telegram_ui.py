from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def preview_keyboard(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Kirim", callback_data=f"send:{app_id}"),
                InlineKeyboardButton(text="✏️ Edit", callback_data=f"edit:{app_id}"),
                InlineKeyboardButton(text="❌ Batal", callback_data=f"cancel:{app_id}"),
            ]
        ]
    )

def edit_keyboard(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Edit Email", callback_data=f"editfield:{app_id}:hr_email"),
                InlineKeyboardButton(text="Edit Pesan", callback_data=f"editfield:{app_id}:body"),
            ],
            [
                InlineKeyboardButton(text="Edit Subject", callback_data=f"editfield:{app_id}:subject"),
                InlineKeyboardButton(text="⬅️ Kembali", callback_data=f"back:{app_id}"),
            ]
        ]
    )
