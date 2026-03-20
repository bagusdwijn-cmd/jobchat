# JobChat V5 Telegram First

Versi ini fokus pada tiga fitur yang bisa dipakai dari **Telegram** dan **web**:

1. Auto Apply via Email
2. BabyAGI / AutoGPT style planner
3. Cody / Sourcegraph style context agent

## Telegram commands
- `/start` atau `/setup`
- `/profil`
- `/lampiran`
- `/setcv`
- `/tambahlampiran`
- `/daftar`
- `/babyagi <goal>`
- `/cody_upload`
- `/cody_ask <instruksi>`
- kirim **foto lowongan** untuk auto apply

## Jalankan lokal
```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Railway
Variables minimal:
- APP_BOT_TOKEN
- MASTER_ENCRYPTION_KEY
- DB_PATH=storage/app.db
- LOG_LEVEL=INFO
- BASE_URL=https://domain-anda.up.railway.app

Start Command:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Generate Domain target port:
```text
8000
```
