# Telegram Job Bot - Setup Full Via Telegram

Bot Telegram untuk:
- setup semua data lewat Telegram
- upload CV utama dan dokumen pendukung
- simpan Gemini API key, Gmail, dan App Password secara terenkripsi
- kirim gambar lowongan
- tampilkan preview ringkas
- kirim email otomatis dengan lampiran aktif
- lihat daftar lamaran yang sudah dikirim

## Flow
### Setup
1. `/start`
2. upload CV utama
3. upload dokumen pendukung
4. kirim Gemini API key
5. kirim Gmail address
6. kirim Gmail App Password
7. kirim profil singkat
8. setup selesai

### Pemakaian
1. kirim gambar lowongan
2. bot analisa
3. bot tampilkan preview:
   - email HR
   - nama perusahaan
   - isi pesan Gmail
   - lampiran aktif
4. pilih:
   - Kirim
   - Edit
   - Batal

### Riwayat
- `/daftar` untuk daftar lamaran terkirim
- `/profil` untuk melihat status setup
- `/lampiran` untuk melihat file aktif
- `/setcv` untuk ganti CV utama
- `/tambahlampiran` untuk tambah dokumen
- `/cancel` untuk membatalkan mode aktif

## Setup lokal
1. copy `.env.example` menjadi `.env`
2. isi:
   - `APP_BOT_TOKEN`
   - `MASTER_ENCRYPTION_KEY`
3. install dependency:
   ```bash
   pip install -r requirements.txt
   ```
4. jalankan:
   ```bash
   python -m app.main
   ```

## Catatan
- Kredensial sensitif disimpan terenkripsi di database.
- Pesan sensitif dari user dihapus setelah diproses, jika bot memiliki izin.
- Bot memakai long polling agar mudah dijalankan.
