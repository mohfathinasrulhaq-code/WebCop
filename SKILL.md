---
name: webcop
description: Analisis struktur, layout, teknologi, dan design tokens dari halaman web publik, lalu buat kerangka proyek orisinal dengan placeholder.
---

# WebCop

Skill untuk mempelajari arsitektur frontend dari sebuah URL publik dan menghasilkan kerangka proyek baru yang orisinal.

## Alur Kerja

*(Jalankan skrip dari direktori skill atau gunakan path absolut ke folder `scripts/`)*

1. **Fetch halaman & aset publik** *(untuk URL website; lewati langkah ini jika input berupa file `.svg` desain UI/UX)*
   Jalankan:
   ```bash
   python "<SKILL_DIR>/scripts/fetch_page.py" "<URL>" --out workdir
   ```
   Jika diblokir oleh `robots.txt`, **berhenti** dan minta user menyimpan halaman secara manual.

2. **Analisis struktur & design tokens**
   Jalankan:
   ```bash
   python "<SKILL_DIR>/scripts/analyze.py" workdir --out report_data
   ```

3. **Buat kerangka proyek baru (scaffold)**
   Jalankan:
   ```bash
   python "<SKILL_DIR>/scripts/scaffold.py" report_data --url "<URL>" --root webcop-output
   ```

4. **Tulis ulang kode secara orisinal**
   - Gunakan `templates/reports.md` sebagai acuan jika user meminta laporan analisis.
   - Bangun ulang HTML, CSS, dan JS di folder `site/` menggunakan **konten placeholder** (teks, gambar, dan brand milik sendiri).

## Aturan Wajib

- **Patuhi `robots.txt`**: Jangan pernah melewati atau mengabaikan blokir `robots.txt`.
- **Hanya halaman publik**: Jangan mencoba mengakses halaman di balik login, paywall, atau anti-bot/CAPTCHA.
- **Jangan menyalin konten/aset**: Gambar tidak boleh diunduh; teks, logo, dan merek dagang harus diganti dengan placeholder orisinal.
- **Orisinalitas**: Gunakan design tokens (warna, font, radius) hanya sebagai referensi/inspirasi, lalu sesuaikan agar hasil akhir orisinal.
