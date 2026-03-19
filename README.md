# JobChat V4 Final

Fitur:
1. Auto apply via email dari foto lowongan.
2. BabyAGI / AutoGPT style planner.
3. Cody / Sourcegraph style repo context agent.

Semua API key provider AI diinput lewat Telegram, bukan web dan bukan Railway Variables.

Railway Variables yang dibutuhkan:
- APP_BOT_TOKEN
- MASTER_ENCRYPTION_KEY
- DB_PATH
- LOG_LEVEL

Provider AI:
- gemini
- openai
- openrouter
- anthropic
- groq
- together
- custom_compatible

## Jalankan lokal
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
