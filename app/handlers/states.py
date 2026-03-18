from aiogram.fsm.state import State, StatesGroup

class SetupStates(StatesGroup):
    waiting_cv = State()
    waiting_attachment = State()
    waiting_gemini_key = State()
    waiting_gmail = State()
    waiting_app_password = State()
    waiting_profile = State()

class EditStates(StatesGroup):
    waiting_value = State()

class UploadModeStates(StatesGroup):
    waiting_new_cv = State()
    waiting_new_attachment = State()
