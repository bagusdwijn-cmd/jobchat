from __future__ import annotations
import asyncio, json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings, BASE_DIR
from app.utils.logger import setup_logger
from app.utils.security import SecretBox
from app.utils.validators import is_valid_email, looks_like_apply_form, redact_secrets
from app.services.storage import Storage
from app.services.file_service import FileService
from app.services.user_profile_service import UserProfileService
from app.services.ai_service import AIService
from app.services.mail_service import MailService
from app.services.babyagi_service import BabyAGIService
from app.services.cody_service import CodyStyleService
from app.services.providers.exceptions import ProviderAuthError, ProviderModelError, ProviderError
from app.bot.telegram_bot import build_bot

settings = get_settings()
setup_logger(settings.log_level)
storage = Storage(settings.db_path)
file_service = FileService(BASE_DIR / "storage")
secret_box = SecretBox(settings.master_encryption_key)
profile_service = UserProfileService(storage, secret_box)
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

bot = None
dp = None
bot_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, bot_task
    await storage.init()
    if settings.app_bot_token:
        bot, dp = build_bot(settings.app_bot_token, storage, file_service, profile_service)
        bot_task = asyncio.create_task(dp.start_polling(bot))
    yield
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except BaseException:
            pass

app = FastAPI(title="JobChat V4 Final", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")

def build_profile_text(user: dict) -> str:
    return (
        f"Nama: {user.get('full_name', '')}\n"
        f"Title: {user.get('target_title', '')}\n"
        f"Skills: {user.get('skills', '')}\n"
        f"Portfolio: {user.get('portfolio', '')}\n"
        f"LinkedIn: {user.get('linkedin', '')}\n"
        f"Catatan tambahan: {user.get('extra_notes', '')}"
    )

def validate_preview(preview):
    warnings = []
    preview.email = preview.email.strip().lower()
    if not is_valid_email(preview.email):
        warnings.append("Email HR tidak valid atau tidak jelas.")
        preview.needs_review = True
    if not preview.selected_position.strip():
        warnings.append("Posisi terpilih belum jelas.")
        preview.needs_review = True
    if len((preview.body or "").strip()) < 80:
        warnings.append("Cover letter terlalu pendek.")
        preview.needs_review = True
    if looks_like_apply_form(" ".join([preview.instructions, preview.body, preview.subject, preview.company])):
        warnings.append("Lowongan terindikasi apply via form/link, bukan email.")
        preview.needs_review = True
    preview.warnings = warnings
    return preview

async def get_user_context(chat_id: int):
    user = await storage.get_user(chat_id)
    if not user or not user.get("setup_completed"):
        raise ValueError("User Telegram belum setup lengkap.")
    secrets = await profile_service.secrets(chat_id)
    if not secrets.get("api_key"):
        raise ValueError("API key provider belum tersedia. Jalankan /setup di Telegram.")
    return user, secrets

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "users": await storage.list_users()})

@app.get("/auto-apply", response_class=HTMLResponse)
async def auto_apply_page(request: Request):
    return templates.TemplateResponse("auto_apply.html", {"request": request, "users": await storage.list_users()})

@app.post("/auto-apply/analyze", response_class=HTMLResponse)
async def auto_apply_analyze(request: Request, chat_id: int = Form(...), job_image: UploadFile = File(...)):
    users = await storage.list_users()
    try:
        user, secrets = await get_user_context(chat_id)
        image_path = file_service.jobs_dir(chat_id) / job_image.filename
        image_path.write_bytes(await job_image.read())
        ai = AIService(secrets["provider"], secrets["api_key"], secrets["model"], build_profile_text(user), secrets.get("base_url", ""))
        preview, raw = await ai.analyze_job_image(image_path)
        preview = validate_preview(preview)
        attachments = [{"id": f["id"], "file_name": f["file_name"], "file_path": f["file_path"]} for f in await storage.list_user_files(chat_id) if f.get("is_active_attachment")]
        app_id = await storage.create_application({
            "chat_id": chat_id,
            "company": preview.company,
            "hr_email": preview.email,
            "available_positions": preview.available_positions,
            "selected_position": preview.selected_position,
            "subject": preview.subject,
            "body": preview.body,
            "instructions": preview.instructions,
            "language": preview.language,
            "needs_review": preview.needs_review,
            "confidence": preview.confidence.model_dump(),
            "attachments": attachments,
            "raw_ai_json": raw,
            "status": "draft",
        })
        return templates.TemplateResponse("auto_apply.html", {"request": request, "users": users, "preview": preview, "application_id": app_id, "attachments": [a["file_name"] for a in attachments]})
    except (ProviderAuthError, ProviderModelError, ProviderError, ValueError) as e:
        return templates.TemplateResponse("auto_apply.html", {"request": request, "users": users, "error": redact_secrets(str(e))})
    except Exception as e:
        return templates.TemplateResponse("auto_apply.html", {"request": request, "users": users, "error": redact_secrets(str(e))})

@app.post("/auto-apply/send/{application_id}", response_class=HTMLResponse)
async def auto_apply_send(request: Request, application_id: int):
    users = await storage.list_users()
    try:
        application = await storage.get_application(application_id)
        if not application:
            raise ValueError("Application tidak ditemukan.")
        _, secrets = await get_user_context(application["chat_id"])
        mail = MailService(secrets["gmail"], secrets["gmail_app_password"])
        attachments = json.loads(application.get("attachments_json", "[]") or "[]")
        mail.send(application["hr_email"], application["subject"], application["body"], attachments)
        await storage.mark_application_sent(application_id)
        return templates.TemplateResponse("auto_apply.html", {"request": request, "users": users, "send_result": f"Email berhasil dikirim ke {application['hr_email']}"})
    except Exception as e:
        return templates.TemplateResponse("auto_apply.html", {"request": request, "users": users, "error": redact_secrets(str(e))})

@app.get("/babyagi", response_class=HTMLResponse)
async def babyagi_page(request: Request):
    return templates.TemplateResponse("babyagi.html", {"request": request, "users": await storage.list_users()})

@app.post("/babyagi/run", response_class=HTMLResponse)
async def babyagi_run(request: Request, chat_id: int = Form(...), goal: str = Form(...)):
    users = await storage.list_users()
    try:
        user, secrets = await get_user_context(chat_id)
        ai = AIService(secrets["provider"], secrets["api_key"], secrets["model"], build_profile_text(user), secrets.get("base_url", ""))
        result = await BabyAGIService(ai).run(goal)
        await storage.create_agent_run(chat_id, "babyagi", goal, result)
        pretty = {"summary": result.get("summary", ""), "steps_pretty": json.dumps(result.get("steps", []), ensure_ascii=False, indent=2), "exec_pretty": json.dumps(result.get("executions", []), ensure_ascii=False, indent=2), "result": result.get("result", "")}
        return templates.TemplateResponse("babyagi.html", {"request": request, "users": users, "result": pretty})
    except Exception as e:
        return templates.TemplateResponse("babyagi.html", {"request": request, "users": users, "error": redact_secrets(str(e))})

@app.get("/cody", response_class=HTMLResponse)
async def cody_page(request: Request):
    return templates.TemplateResponse("cody.html", {"request": request, "users": await storage.list_users()})

@app.post("/cody/run", response_class=HTMLResponse)
async def cody_run(request: Request, chat_id: int = Form(...), question: str = Form(...), repo_zip: UploadFile = File(...)):
    users = await storage.list_users()
    try:
        user, secrets = await get_user_context(chat_id)
        zip_path = file_service.repo_dir(chat_id) / repo_zip.filename
        zip_path.write_bytes(await repo_zip.read())
        extracted = file_service.extract_repo_zip(chat_id, repo_zip.filename.replace(".zip", ""), zip_path)
        ai = AIService(secrets["provider"], secrets["api_key"], secrets["model"], build_profile_text(user), secrets.get("base_url", ""))
        cody = CodyStyleService(ai, file_service)
        index = cody.build_index(extracted)
        await storage.create_repo_index(chat_id, repo_zip.filename, str(extracted), index)
        answer = await cody.answer(index, question)
        await storage.create_agent_run(chat_id, "cody", question, answer)
        return templates.TemplateResponse("cody.html", {"request": request, "users": users, "answer": answer})
    except Exception as e:
        return templates.TemplateResponse("cody.html", {"request": request, "users": users, "error": redact_secrets(str(e))})
