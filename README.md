# WebCop
<br />
<div>
<a href="https://domainkamu.com"><img src="https://img.shields.io/badge/Website-domainkamu.com-ff6b6b?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=1b1526" alt="Website" /></a>
<a href="https://linkedin.com/in/usernamekamu"><img src="https://img.shields.io/badge/LinkedIn-usernamekamu-ffb347?style=for-the-badge&logo=linkedin&logoColor=white&labelColor=1b1526" alt="LinkedIn" /></a>
<a href="https://instagram.com/usernamekamu"><img src="https://img.shields.io/badge/Instagram-@usernamekamu-7ee8c7?style=for-the-badge&logo=instagram&logoColor=white&labelColor=1b1526" alt="Instagram" /></a>
<a href="mailto:emailkamu@gmail.com"><img src="https://img.shields.io/badge/Email-Hubungi%20Saya-c4a1ff?style=for-the-badge&logo=gmail&logoColor=white&labelColor=1b1526" alt="Email" /></a>
</div>

Skill AI Agent dan CLI berbasis Python (zero-dependency, hanya stdlib Python 3.8+) untuk mempelajari struktur, teknologi, sistem layout, dan *design tokens* dari halaman web publik, lalu membuat kerangka proyek baru yang orisinal dengan konten placeholder.

---

## Fitur Utama

- **Fetch Halaman Publik (`scripts/fetch_page.py`)**: Mengunduh HTML, CSS, dan JS publik sambil mematuhi `robots.txt` (salinannya disimpan ke `robots.txt` di folder kerja). Mendukung `--delay`, `--max-files`, `--config`, dan mencatat log ke `log.txt` serta daftar gambar ke `manifest.json` (gambar tidak diunduh).
- **Analisis Struktur & Design Tokens (`scripts/analyze.py`)**: Mendeteksi teknologi frontend, SSR, dan CMS (React, Next.js, Vue, Nuxt, Angular, Svelte, Tailwind CSS, Bootstrap, WordPress, Joomla, Drupal, dll.), memetakan *semantic outline* HTML, serta mengekstrak token warna (HEX 6-digit), font, `border-radius`, `spacing`, dan `box-shadow`. Mendukung output `json` maupun `markdown` (`report.md`).
- **Scaffold Proyek Baru (`scripts/scaffold.py`)**: Menghasilkan folder proyek siap kembang (`analysis/` + `site/`) dengan variabel CSS di `base.css`, kerangka HTML semantik, dan pilihan template (`plain`, `tailwind`, `bootstrap`).

---

## Persyaratan

- **Python 3.8+** (tidak membutuhkan library eksternal / `pip install` tambahan).

---

## Cara Instalasi

Salin folder `WebCop/` ke direktori skill agent yang kamu gunakan:

- **Antigravity**: taruh di folder skills workspace (mis. `.agent/skills/webcop/`).
- **Claude**: unggah paket skill atau taruh di `~/.claude/skills/webcop/`.
- **Codex**: taruh di folder skills Codex, atau salin `AGENTS.md` ke root proyek.

Semua platform membaca file `SKILL.md` yang sama sebagai panduan utama agent.

---

## Cara Penggunaan (CLI)

1. **Fetch halaman & aset publik:**
   ```bash
   python scripts/fetch_page.py "https://example.com" --out workdir
   ```
   *(Opsional: `--delay 1.5`, `--max-files 25`, `--config config.json`)*

2. **Analisis struktur & design tokens:**
   ```bash
   python scripts/analyze.py workdir --out report_data --format all
   ```

3. **Buat kerangka proyek baru:**
   ```bash
   python scripts/scaffold.py report_data --url "https://example.com" --root webcop-output --template plain
   ```
   *(Pilihan `--template`: `plain`, `tailwind`, atau `bootstrap`)*

---

## Menjalankan Unit Test

```bash
python -m unittest discover -s tests -v
```

---

## Aturan Wajib & Etika

- Selalu patuhi `robots.txt` situs target.
- Hanya gunakan pada halaman publik (jangan mengakses halaman di balik login, paywall, atau anti-bot).
- Jangan menyalin konten, gambar, logo, atau merek dagang secara langsung—gunakan hasil analisis untuk membangun karya yang orisinal dengan placeholder.
