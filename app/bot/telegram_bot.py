from __future__ import annotations

import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, Document, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.states import SetupStates, UploadStates
from app.services.ai_service import AIService
from app.services.babyagi_service import BabyAGIService
from app.services.cody_service import CodyStyleService
from app.services.mail_service import MailService
from app.services.providers.exceptions import ProviderAuthError, ProviderModelError, ProviderError
from app.services.providers.registry import SUPPORTED_PROVIDERS
from app.utils.validators import redact_secrets


def preview_keyboard(app_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text='✅ Kirim', callback_data=f'send:{app_id}'),
            InlineKeyboardButton(text='❌ Batal', callback_data=f'cancel:{app_id}')
        ]]
    )


def build_bot(token, storage, file_service, profile_service):
    bot = Bot(token=token)
    dp = Dispatcher(storage=MemoryStorage())
    router = Router()

    async def _safe_delete(message: Message):
        try:
            await message.delete()
        except Exception:
            pass

    async def _safe_answer(message: Message, text: str, **kwargs):
        try:
            await message.answer(text, **kwargs)
        except Exception:
            pass

    def _compact_preview(draft: dict) -> str:
        positions = draft.get('available_positions', []) or []
        attachments = draft.get('attachments', []) or []
        attach_names = [x.get('file_name', '-') for x in attachments]
        return (
            f"Perusahaan: {draft.get('company','-')}\n"
            f"Email HR: {draft.get('hr_email','-')}\n"
            f"Posisi tersedia: {', '.join(positions) if positions else '-'}\n"
            f"Posisi dipilih AI: {draft.get('selected_position','-')}\n\n"
            f"Pesan Gmail:\n{draft.get('body','-')}\n\n"
            f"Lampiran:\n- " + "\n- ".join(attach_names if attach_names else ['Tidak ada'])
        )

    async def _build_ai(chat_id: int):
        user = await storage.get_user(chat_id)
        if not user or not user.get('setup_completed'):
            raise ValueError('Setup belum selesai. Jalankan /start atau /setup.')
        secrets = await profile_service.secrets(chat_id)
        if not secrets.get('api_key'):
            raise ValueError('API key provider belum tersedia. Jalankan /setup.')
        profile = (
            f"Nama: {user.get('full_name','')}\n"
            f"Title: {user.get('target_title','')}\n"
            f"Skills: {user.get('skills','')}\n"
            f"Portfolio: {user.get('portfolio','')}\n"
            f"LinkedIn: {user.get('linkedin','')}\n"
            f"Catatan tambahan: {user.get('extra_notes','')}"
        )
        ai = AIService(secrets['provider'], secrets['api_key'], secrets['model'], profile, secrets.get('base_url', ''))
        return user, secrets, ai

    @router.message(Command('help'))
    async def help_cmd(message: Message):
        await _safe_answer(
            message,
            '/start\n'
            '/setup\n'
            '/profil\n'
            '/lampiran\n'
            '/setcv\n'
            '/tambahlampiran\n'
            '/daftar\n'
            '/babyagi <goal>\n'
            '/cody_upload\n'
            '/cody_ask <instruksi>\n'
            'Kirim foto lowongan untuk auto apply'
        )

    @router.message(Command('start'))
    async def start(message: Message, state):
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer('Halo, kita setup dulu ya.\n\nLangkah 1/9:\nSilakan upload CV utama Anda (PDF/DOC/DOCX).')

    @router.message(Command('setup'))
    async def setup(message: Message, state):
        await storage.ensure_user(message.chat.id)
        await state.clear()
        await state.set_state(SetupStates.waiting_cv)
        await message.answer('Setup diulang. Upload CV utama Anda.')

    @router.message(Command('setcv'))
    async def setcv(message: Message, state):
        await state.set_state(UploadStates.waiting_new_cv)
        await message.answer('Silakan upload CV utama baru.')

    @router.message(Command('tambahlampiran'))
    async def tambah(message: Message, state):
        await state.set_state(UploadStates.waiting_new_attachment)
        await message.answer('Silakan upload dokumen tambahan baru.')

    @router.message(Command('cody_upload'))
    async def cody_upload(message: Message, state):
        await state.set_state(UploadStates.waiting_cody_zip)
        await message.answer('Silakan upload file ZIP repo/source Anda.')

    @router.message(Command('profil'))
    async def profil(message: Message):
        user = await storage.get_user(message.chat.id)
        if not user:
            await message.answer('Belum ada profil.')
            return
        await message.answer(
            'Profil:\n'
            f"Nama: {user.get('full_name') or '-'}\n"
            f"Title: {user.get('target_title') or '-'}\n"
            f"Skills: {user.get('skills') or '-'}\n"
            f"Provider: {user.get('ai_provider') or '-'}\n"
            f"Model: {user.get('ai_model') or '-'}\n"
            f"Base URL: {user.get('ai_base_url') or '-'}\n"
            f"Gmail: {user.get('gmail_address') or '-'}"
        )

    @router.message(Command('lampiran'))
    async def lampiran(message: Message):
        files = await storage.list_user_files(message.chat.id)
        if not files:
            await message.answer('Belum ada file tersimpan.')
            return
        lines = ['Lampiran aktif:']
        for i, f in enumerate(files, start=1):
            kind = 'CV Utama' if f.get('is_primary_cv') else 'Dokumen'
            status = 'aktif' if f.get('is_active_attachment') else 'nonaktif'
            lines.append(f"{i}. {f['file_name']} — {kind} — {status}")
        await message.answer('\n'.join(lines))

    @router.message(Command('daftar'))
    async def daftar(message: Message):
        apps = await storage.list_applications(message.chat.id)
        runs = await storage.list_agent_runs(message.chat.id)
        lines = []
        if apps:
            lines.append('Daftar lamaran:')
            for i, app in enumerate(apps[:10], start=1):
                lines.append(f"{i}. {app.get('company') or '-'} — {app.get('selected_position') or '-'} — {app.get('status') or '-'}")
        if runs:
            if lines:
                lines.append('')
            lines.append('Riwayat agent:')
            for i, run in enumerate(runs[:10], start=1):
                lines.append(f"{i}. {run.get('agent_type')} — {(run.get('input_text') or '')[:80]}")
        await message.answer('\n'.join(lines) if lines else 'Belum ada riwayat.')

    @router.message(Command('babyagi'))
    async def babyagi(message: Message):
        goal = message.text.removeprefix('/babyagi').strip()
        if not goal:
            await message.answer('Contoh: /babyagi Cari kerja manufaktur Indonesia dan susun next actions')
            return
        wait = await message.answer('⏳ Menjalankan BabyAGI planner...')
        try:
            _, _, ai = await _build_ai(message.chat.id)
            result = await BabyAGIService(ai).run(goal)
            await storage.create_agent_run(message.chat.id, 'babyagi', goal, result)
            parts = []
            if result.get('summary'):
                parts.append(f"Summary:\n{result['summary']}")
            for i, step in enumerate(result.get('executions', [])[:5], start=1):
                output = step.get('output')
                if not isinstance(output, str):
                    output = json.dumps(output, ensure_ascii=False)
                parts.append(f"{i}. {step.get('step') or '-'}\nTool: {step.get('action') or '-'}\n{output[:800]}")
            await wait.edit_text('✅ BabyAGI selesai\n\n' + '\n\n'.join(parts[:6]))
        except Exception as e:
            await wait.edit_text(f"❌ BabyAGI gagal\n\nDetail: {redact_secrets(str(e))}")

    @router.message(Command('cody_ask'))
    async def cody_ask(message: Message):
        question = message.text.removeprefix('/cody_ask').strip()
        if not question:
            await message.answer('Contoh: /cody_ask Jelaskan struktur repo ini dan file mana yang relevan untuk cover letter automation')
            return
        wait = await message.answer('⏳ Menjalankan Cody-style agent...')
        try:
            user, _, ai = await _build_ai(message.chat.id)
            repo_id = user.get('last_repo_index_id')
            if not repo_id:
                await wait.edit_text('❌ Belum ada repo context. Jalankan /cody_upload dulu.')
                return
            repo = await storage.get_repo_index(int(repo_id))
            if not repo:
                await wait.edit_text('❌ Repo context tidak ditemukan. Upload ulang dengan /cody_upload.')
                return
            index = json.loads(repo.get('index_json') or '{}')
            answer = await CodyStyleService(ai, file_service).answer(index, question)
            await storage.create_agent_run(message.chat.id, 'cody', question, answer)
            await wait.edit_text('✅ Cody-style agent selesai\n\n' + answer.get('answer', '')[:3900])
        except Exception as e:
            await wait.edit_text(f"❌ Cody-style agent gagal\n\nDetail: {redact_secrets(str(e))}")

    @router.message(SetupStates.waiting_cv, F.document)
    async def setup_cv(message: Message, state):
        doc: Document = message.document
        path = file_service.cv_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or '', is_primary_cv=True, is_active_attachment=True)
        await state.set_state(SetupStates.waiting_attachment)
        await message.answer('CV utama tersimpan.\n\nLangkah 2/9:\nUpload dokumen tambahan satu per satu. Kalau selesai, ketik: selesai')

    @router.message(UploadStates.waiting_new_cv, F.document)
    async def replace_cv(message: Message, state):
        doc = message.document
        path = file_service.cv_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or '', is_primary_cv=True, is_active_attachment=True)
        await state.clear()
        await message.answer('CV utama berhasil diganti.')

    @router.message(UploadStates.waiting_new_attachment, F.document)
    async def new_attach(message: Message, state):
        doc = message.document
        path = file_service.attachment_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or '', is_primary_cv=False, is_active_attachment=True)
        await state.clear()
        await message.answer('Lampiran baru ditambahkan.')

    @router.message(UploadStates.waiting_cody_zip, F.document)
    async def upload_repo_zip(message: Message, state):
        doc = message.document
        if not doc.file_name.lower().endswith('.zip'):
            await message.answer('File harus ZIP.')
            return
        wait = await message.answer('⏳ Sedang membuat repo context...')
        try:
            path = file_service.repo_dir(message.chat.id) / doc.file_name
            await message.bot.download(doc, destination=path)
            extracted = file_service.extract_repo_zip(message.chat.id, doc.file_name.replace('.zip', ''), path)
            _, _, ai = await _build_ai(message.chat.id)
            cody = CodyStyleService(ai, file_service)
            index = cody.build_index(extracted)
            repo_id = await storage.create_repo_index(message.chat.id, doc.file_name, str(extracted), index)
            await storage.update_user_field(message.chat.id, 'last_repo_index_id', repo_id)
            await state.clear()
            await wait.edit_text(f'✅ Repo context tersimpan. Repo ID: {repo_id}\nSekarang jalankan /cody_ask <instruksi>')
        except Exception as e:
            await wait.edit_text(f"❌ Gagal memproses ZIP\n\nDetail: {redact_secrets(str(e))}")

    @router.message(SetupStates.waiting_attachment, F.document)
    async def setup_attachment(message: Message):
        doc = message.document
        path = file_service.attachment_dir(message.chat.id) / doc.file_name
        await message.bot.download(doc, destination=path)
        await storage.add_user_file(chat_id=message.chat.id, telegram_file_id=doc.file_id, file_name=doc.file_name, file_path=str(path), mime_type=doc.mime_type or '', is_primary_cv=False, is_active_attachment=True)
        await message.answer(f"Dokumen tersimpan: {doc.file_name}. Upload lagi atau ketik 'selesai'.")

    @router.message(SetupStates.waiting_attachment, F.text)
    async def finish_attachment(message: Message, state):
        if message.text.strip().lower() != 'selesai':
            await message.answer("Upload lagi atau ketik 'selesai'.")
            return
        await state.set_state(SetupStates.waiting_provider)
        await message.answer('Langkah 3/9:\nPilih provider AI: ' + ' / '.join(SUPPORTED_PROVIDERS))

    @router.message(SetupStates.waiting_provider, F.text)
    async def provider(message: Message, state):
        provider = message.text.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            await message.answer('Provider tidak valid.')
            return
        await profile_service.save_provider(message.chat.id, provider)
        await state.update_data(provider=provider)
        await state.set_state(SetupStates.waiting_api_key)
        await message.answer('Langkah 4/9:\nKirim API key provider Anda.')

    @router.message(SetupStates.waiting_api_key, F.text)
    async def api_key(message: Message, state):
        await profile_service.save_api_key(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_model)
        await message.answer('Langkah 5/9:\nKirim model AI, atau ketik `default`.')

    @router.message(SetupStates.waiting_model, F.text)
    async def model(message: Message, state):
        data = await state.get_data()
        provider = data.get('provider', 'gemini')
        await profile_service.save_model(message.chat.id, provider, message.text.strip())
        if provider == 'custom_compatible':
            await state.set_state(SetupStates.waiting_base_url)
            await message.answer('Langkah 6/9:\nKirim base URL provider OpenAI-compatible Anda. Contoh: https://api.example.com/v1')
            return
        await profile_service.save_base_url(message.chat.id, '')
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer('Langkah 6/9:\nKirim alamat Gmail Anda.')

    @router.message(SetupStates.waiting_base_url, F.text)
    async def base_url(message: Message, state):
        await profile_service.save_base_url(message.chat.id, message.text.strip())
        await state.set_state(SetupStates.waiting_gmail)
        await message.answer('Langkah 7/9:\nKirim alamat Gmail Anda.')

    @router.message(SetupStates.waiting_gmail, F.text)
    async def gmail(message: Message, state):
        await profile_service.save_gmail(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_gmail_pwd)
        await message.answer('Langkah 8/9:\nKirim App Password Gmail Anda.')

    @router.message(SetupStates.waiting_gmail_pwd, F.text)
    async def gmail_pwd(message: Message, state):
        await profile_service.save_gmail_app_password(message.chat.id, message.text.strip())
        await _safe_delete(message)
        await state.set_state(SetupStates.waiting_profile)
        await message.answer('Langkah 9/9:\nKirim profil singkat Anda. Contoh:\nNama: ...\nTitle: ...\nSkills: ...\nPortfolio: ...\nLinkedIn: ...')

    @router.message(SetupStates.waiting_profile, F.text)
    async def profile(message: Message, state):
        text = message.text.strip()
        await storage.update_user_field(message.chat.id, 'extra_notes', text)
        mapping = {'nama:': 'full_name', 'title:': 'target_title', 'skills:': 'skills', 'portfolio:': 'portfolio', 'linkedin:': 'linkedin'}
        for line in text.splitlines():
            low = line.lower().strip()
            for prefix, field_name in mapping.items():
                if low.startswith(prefix):
                    value = line.split(':', 1)[1].strip()
                    if value:
                        await storage.update_user_field(message.chat.id, field_name, value)
        await storage.update_user_field(message.chat.id, 'setup_completed', 1)
        await state.clear()
        await message.answer('✅ Setup selesai. Sekarang Anda bisa pakai web dan Telegram.')

    @router.message(F.photo)
    async def handle_photo(message: Message):
        wait = await message.answer('⏳ Sedang membaca lowongan...')
        try:
            photo = message.photo[-1]
            path = file_service.jobs_dir(message.chat.id) / f'{photo.file_id}.jpg'
            file = await message.bot.get_file(photo.file_id)
            await message.bot.download(file, destination=path)
            user, secrets, ai = await _build_ai(message.chat.id)
            preview, raw = await ai.analyze_job_image(path)
            attachments = [
                {'id': f['id'], 'file_name': f['file_name'], 'file_path': f['file_path']}
                for f in await storage.list_user_files(message.chat.id) if f.get('is_active_attachment')
            ]
            app_id = await storage.create_application({
                'chat_id': message.chat.id,
                'company': preview.company,
                'hr_email': preview.email,
                'available_positions': preview.available_positions,
                'selected_position': preview.selected_position,
                'subject': preview.subject,
                'body': preview.body,
                'instructions': preview.instructions,
                'language': preview.language,
                'needs_review': preview.needs_review,
                'confidence': preview.confidence.model_dump(),
                'attachments': attachments,
                'raw_ai_json': raw,
                'status': 'draft',
            })
            draft = {
                'company': preview.company,
                'hr_email': preview.email,
                'available_positions': preview.available_positions,
                'selected_position': preview.selected_position,
                'body': preview.body,
                'attachments': attachments,
                'app_id': app_id,
            }
            await wait.edit_text(_compact_preview(draft), reply_markup=preview_keyboard(app_id))
        except (ProviderAuthError, ProviderModelError, ProviderError, Exception) as e:
            await wait.edit_text(f"❌ Gagal memproses lowongan\n\nDetail: {redact_secrets(str(e))}")

    @router.callback_query(F.data.startswith('send:'))
    async def send_draft(callback: CallbackQuery):
        app_id = int(callback.data.split(':')[1])
        try:
            app = await storage.get_application(app_id)
            if not app:
                await callback.message.answer('Application tidak ditemukan.')
                await callback.answer()
                return
            secrets = await profile_service.secrets(callback.message.chat.id)
            attachments = json.loads(app.get('attachments_json') or '[]')
            MailService(secrets['gmail'], secrets['gmail_app_password']).send(app['hr_email'], app['subject'], app['body'], attachments)
            await storage.mark_application_sent(app_id)
            await callback.message.answer('✅ Email berhasil dikirim.')
        except Exception as e:
            await callback.message.answer(f"❌ Gagal kirim email\n\nDetail: {redact_secrets(str(e))}")
        await callback.answer()

    @router.callback_query(F.data.startswith('cancel:'))
    async def cancel_draft(callback: CallbackQuery):
        app_id = int(callback.data.split(':')[1])
        await storage.update_application_field(app_id, 'status', 'cancelled')
        await callback.message.answer('Dibatalkan.')
        await callback.answer()

    dp.include_router(router)
    return bot, dp
