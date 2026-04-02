# SimKuliah Bot" an

> *"Solusi yang keren berasal dari pemikiran yang malas"*

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=flat-square&logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-USK_SimKuliah-red?style=flat-square)

**Bot absensi otomatis untuk [simkuliah.usk.ac.id](https://simkuliah.usk.ac.id)**
Jalan sendiri via GitHub Actions — gratis, tanpa server, tanpa VPS.

[🇮🇩 Bahasa Indonesia](#-panduan-lengkap) · [🇬🇧 English](#-english-guide)

</div>

---

## ⚡ Cara Kerja (Singkat)

```
Jadwal kuliah tiba  →  GitHub Actions aktif  →  Bot login SimKuliah
                                                       ↓
HP kamu dapat notif  ←  ntfy.sh  ←  Absen berhasil diklik ✓
```

Bot ini melakukan 3 hal secara otomatis:

1. **Login** ke SimKuliah — termasuk memecahkan CAPTCHA
2. **Klik tombol absen** (+ tombol konfirmasi)
3. **Kirim notifikasi** ke HP kamu via ntfy

---

## 🇮🇩 Panduan Lengkap

### Prasyarat

Kamu hanya butuh:

- Akun **GitHub** (gratis) → [daftar di sini](https://github.com/signup)
- Akun **SimKuliah** USK yang aktif
- HP Android/iOS untuk notifikasi (opsional, tapi sangat dianjurkan)

---

### Langkah 1 — Fork Repositori Ini

> Fork = menyalin repo ini ke akun GitHub kamu sendiri

1. Klik tombol **Fork** di pojok kanan atas halaman ini
2. Klik **Create fork**
3. Selesai — sekarang kamu punya salinannya sendiri

---

### Langkah 2 — Isi Data Rahasia (Secrets)

Bot butuh NPM dan password kamu, tapi jangan ditulis langsung di kode. Gunakan **GitHub Secrets** agar aman.

**Cara masuk ke halaman Secrets:**

```
Repo kamu → Settings → Secrets and variables → Actions → New repository secret
```

Tambahkan **3 secret** berikut satu per satu:

| Nama Secret | Isi dengan | Contoh |
|-------------|-----------|--------|
| `NPM` | NPM kamu | `2108107010001` |
| `PASSWORD` | Password SimKuliah kamu | `passwordkamu123` |
| `NTFY_TOPIC` | Nama unik pilihanmu (bebas) | `budi-absen-usk` |

> **Catatan:** `NTFY_TOPIC` boleh dikosongkan kalau tidak mau notifikasi. Pilih nama yang unik dan susah ditebak orang lain.

---

### Langkah 3 — Setup Notifikasi di HP (Opsional tapi Dianjurkan)

Notifikasi ini gratis dan tidak butuh akun.

**a. Install app ntfy:**

- Android → [Google Play](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
- iOS → [App Store](https://apps.apple.com/app/ntfy/id1625396347)

**b. Subscribe ke 3 topik ini** (ganti `budi-absen-usk` dengan `NTFY_TOPIC` milikmu):

| Topik | Kapan dikirim |
|-------|--------------|
| `budi-absen-usk-bisa` |  Absen berhasil |
| `budi-absen-usk-info` |  Bot jalan, tidak ada tombol absen |
| `budi-absen-usk-gagal` |  Terjadi error |

Cara subscribe: buka app ntfy → ikon `+` → ketik nama topik → Subscribe.

---

### Langkah 4 — Update Jadwal Kuliah

Bot menggunakan file `jadwal_cache.json` untuk mengetahui kapan harus jalan. File ini berisi tanggal dan jam setiap pertemuan per mata kuliah.

**Ada 2 cara mengisi file ini:**

#### Cara A — Generate Otomatis (Dianjurkan)

Jalankan workflow **Refresh Jadwal Cache** dari tab Actions:

```
Tab Actions → Refresh Jadwal Cache → Run workflow → Run workflow
```

Bot akan login ke SimKuliah, scrape seluruh jadwal semester, dan menyimpannya otomatis. Ulangi ini tiap awal semester.

#### Cara B — Edit Manual

Buka `jadwal_cache.json` dan tambahkan entry sesuai format berikut:

```json
{
  "pertemuan": 1,
  "kode_mk": "STIK3034",
  "nama_mk": "PATTERN RECOGNITION AND MACHINE LEARNING",
  "dosen": "Rizka Ramadhana, M.T.",
  "tanggal_str": "12-02-2026",
  "tanggal": "2026-02-12",
  "hari": "Kamis",
  "ruang": "A25-203",
  "jam": "08.00 - 09.40"
}
```

> **Penting:** Field `"tanggal"` harus format `YYYY-MM-DD`. Field `"tanggal_str"` boleh diisi sembarang (hanya label).

---

### Langkah 5 — Sesuaikan Jadwal Cron

Edit file `.github/workflows/absen.yml`. Cron berjalan dalam waktu **UTC** — kurangi 7 jam dari WIB.

**Rumus:** `WIB - 7 jam = UTC`

| Jam WIB | Jam UTC | Cron |
|---------|---------|------|
| 08.00 | 01.00 | `0 1 * * [hari]` |
| 10.45 | 03.45 | `45 3 * * [hari]` |
| 14.00 | 07.00 | `0 7 * * [hari]` |
| 16.35 | 09.35 | `35 9 * * [hari]` |

**Kode hari:** `1` = Senin, `2` = Selasa, `3` = Rabu, `4` = Kamis, `5` = Jumat, `6` = Sabtu, `0` = Minggu

**Contoh — kuliah Kamis jam 08.00 WIB:**

```yaml
- cron: '0 1 * * 4'
```

**Contoh — kuliah Rabu jam 14.00 dan 16.35 WIB:**

```yaml
- cron: '0 7 * * 3'   # 14.00 WIB
- cron: '35 9 * * 3'  # 16.35 WIB
```

---

### Langkah 6 — Test Pertama Kali

Sebelum mengandalkan bot, pastikan semua berjalan lancar:

1. Buka tab **Actions** di repo kamu
2. Klik **Absensi Otomatis** di sidebar kiri
3. Klik tombol **Run workflow** → **Run workflow**
4. Tunggu ~1-2 menit, lalu klik run yang muncul untuk melihat log

**Interpretasi hasil:**

- 🟢 Log menampilkan `Absen berhasil` → semuanya beres
- 🟡 Log menampilkan `tidak ada tombol absen` → bot jalan, tapi memang tidak ada jadwal aktif
- 🔴 Log menampilkan `Login gagal` → cek NPM/Password di Secrets, atau CAPTCHA gagal (coba run lagi)

---

### Jadwal Kerja Bot

Bot akan aktif otomatis sesuai cron yang kamu set. Setelah aktif:

1. Bot cek `jadwal_cache.json` — apakah hari ini ada jadwal?
2. Jika ada → login SimKuliah → klik absen
3. Jika tidak ada → kirim notif info → berhenti

> Bot bisa aktif beberapa kali sehari. Tidak masalah — kalau tidak ada jadwal, bot langsung berhenti tanpa melakukan apa-apa.

---

### Refresh Jadwal Tiap Semester

Di awal semester baru, jalankan **Refresh Jadwal Cache** secara manual:

```
Tab Actions → Refresh Jadwal Cache → Run workflow
```

Atau biarkan berjalan otomatis — workflow ini sudah dijadwalkan tiap awal Februari dan Agustus.

---

### Troubleshooting

| Masalah | Kemungkinan penyebab | Solusi |
|---------|---------------------|--------|
| Login gagal terus | CAPTCHA salah terbaca | Coba run lagi 1-2x, biasanya langsung berhasil |
| Tidak ada tombol absen padahal ada jadwal | Absen belum dibuka dosen | Tunggu dosen membuka sesi absen |
| Notif tidak masuk | NTFY_TOPIC salah | Pastikan nama topik di app sama persis dengan secret |
| Bot tidak jalan sesuai jadwal | Cron salah timezone | Pastikan sudah konversi WIB ke UTC |
| `jadwal_cache.json` kosong | Belum di-refresh | Jalankan workflow Refresh Jadwal Cache |

---

### Penjelasan File

| File | Fungsi |
|------|--------|
| `absen_runner.py` | Script utama — cek jadwal, login, klik absen, kirim notif |
| `refresh_jadwal.py` | Scrape jadwal semester dari SimKuliah ke `jadwal_cache.json` |
| `jadwal_cache.json` | Database jadwal pertemuan (di-commit ke repo) |
| `.github/workflows/absen.yml` | Jadwal cron dan pipeline GitHub Actions untuk absen |
| `.github/workflows/refresh.yml` | Workflow untuk refresh jadwal tiap awal semester |

---

### Jalankan Lokal (untuk Developer)

```bash
# Clone repo
git clone https://github.com/NapoleonPro/absenv0.1.git
cd absenv0.1

# Install dependencies
pip install selenium ddddocr python-dotenv

# Buat file .env
echo "NPM=npm_kamu" > .env
echo "PASSWORD=password_kamu" >> .env
echo "NTFY_TOPIC=topic_kamu" >> .env

# Refresh jadwal
python refresh_jadwal.py

# Jalankan absen
python absen_runner.py
```

> Butuh Google Chrome terinstall di lokal.

---

### Tech Stack

| Komponen | Kegunaan |
|----------|----------|
| Python 3.12 | Runtime utama |
| Selenium | Otomatisasi browser |
| ddddocr | Solve CAPTCHA otomatis |
| Chrome headless | Browser engine tanpa tampilan |
| python-dotenv | Baca `.env` saat development lokal |
| GitHub Actions | Scheduler gratis, jalan di cloud |
| ntfy.sh | Push notification gratis ke HP |

---

### ⚠️ Disclaimer

Bot ini dibuat untuk keperluan pribadi. Developer tidak bertanggung jawab atas segala konsekuensi akademik akibat penggunaan bot ini.

- SimKuliah bisa update tampilan kapan saja — kalau bot tiba-tiba tidak jalan, cek apakah ada perubahan di web-nya
- Selalu **verifikasi manual** bahwa absensimu tercatat di SimKuliah
- CAPTCHA bisa salah baca — bot tidak 100% sempurna, pantau notifikasi secara berkala

---

## 🇬🇧 English Guide

### Prerequisites

- A free **GitHub** account → [sign up here](https://github.com/signup)
- An active **SimKuliah USK** account
- Android/iOS phone for notifications (optional but recommended)

---

### Step 1 — Fork This Repository

Click **Fork** → **Create fork**. You now have your own copy.

### Step 2 — Add GitHub Secrets

Go to: **Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | What to Put | Example |
|-------------|-------------|---------|
| `NPM` | Your student ID | `2108107010001` |
| `PASSWORD` | Your SimKuliah password | `yourpassword` |
| `NTFY_TOPIC` | A unique name you choose | `budi-absen-usk` |

### Step 3 — Set Up Push Notifications (Optional)

1. Install **ntfy** → [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) / [iOS](https://apps.apple.com/app/ntfy/id1625396347)
2. Subscribe to 3 topics (replace `budi-absen-usk` with your chosen topic):
   - `budi-absen-usk-bisa` — attendance successful
   - `budi-absen-usk-info` — bot ran, no attendance button found
   - `budi-absen-usk-gagal` — an error occurred

### Step 4 — Load Your Schedule

Run the **Refresh Jadwal Cache** workflow from the Actions tab, or manually edit `jadwal_cache.json` with your class schedule. Each entry needs a `"tanggal"` field in `YYYY-MM-DD` format.

### Step 5 — Set Your Cron Schedule

Edit `.github/workflows/absen.yml`. GitHub Actions uses **UTC** — subtract 7 hours from WIB (Western Indonesia Time).

### Step 6 — Test It

Go to **Actions → Absensi Otomatis → Run workflow**. Check the logs after ~2 minutes.

---

### How It Works

1. Bot checks `jadwal_cache.json` — is there a class today?
2. If yes → logs in to SimKuliah (solves CAPTCHA automatically) → clicks the attendance button
3. Sends a push notification to your phone with the result

---

### Disclaimer

This project is for personal use only. The developer is not responsible for any academic policy violations. Always verify your attendance was recorded on SimKuliah. CAPTCHA solving is not 100% accurate — monitor notifications periodically.

---

<div align="center">

Made with too much coffee and too little sleep by [NapoleonPro](https://github.com/NapoleonPro)

Kalau membantu, kasih ⭐ dong — gratis kok.

</div>

