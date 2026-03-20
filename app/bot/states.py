from aiogram.fsm.state import State, StatesGroup

class SetupStates(StatesGroup):
    waiting_cv = State()
    waiting_attachment = State()
    waiting_provider = State()
    waiting_api_key = State()
    waiting_model = State()
    waiting_base_url = State()
    waiting_gmail = State()
    waiting_gmail_pwd = State()
    waiting_profile = State()

class UploadStates(StatesGroup):
    waiting_new_cv = State()
    waiting_new_attachment = State()
    waiting_cody_zip = State()
