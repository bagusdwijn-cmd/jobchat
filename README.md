# JobChat V2 - Telegram Job Apply Bot (Dynamic AI Provider)

Bot Telegram untuk:
- setup full via Telegram
- upload CV utama dan dokumen pendukung
- pilih AI provider secara dinamis (`gemini`, `openai`, `openrouter`)
- simpan API key terenkripsi
- analisa gambar lowongan
- jika ada banyak posisi, AI memilih posisi yang paling cocok dengan profil user
- cover letter otomatis menyesuaikan posisi terpilih
- preview ringkas sebelum kirim
- kirim email otomatis dengan lampiran aktif
- lihat daftar lamaran terkirim

## Flow setup
1. `/start`
2. upload CV utama
3. upload dokumen pendukung (opsional), lalu ketik `selesai`
4. pilih AI provider (`gemini`, `openai`, `openrouter`)
5. kirim API key provider
6. kirim model AI atau ketik `default`
7. kirim Gmail address
8. kirim Gmail App Password
9. kirim profil singkat

## Flow penggunaan
1. upload gambar lowongan
2. AI ekstrak perusahaan, email HR, posisi-posisi yang tersedia
3. AI memilih posisi paling cocok untuk user
4. AI membuat cover letter yang sesuai posisi terpilih
5. bot tampilkan preview + tombol Kirim/Edit/Batal
6. jika Kirim, email dikirim dengan lampiran aktif

## Command utama
- `/start`
- `/setup`
- `/profil`
- `/lampiran`
- `/setcv`
- `/tambahlampiran`
- `/daftar`
- `/cancel`

## Catatan
- Penyimpanan saat ini masih lokal (SQLite + file lokal Railway/VPS).
- Untuk produksi jangka panjang, idealnya pindah ke PostgreSQL + object storage.
