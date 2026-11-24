#!/usr/bin/env python3
"""WebCop scaffold: buat folder proyek baru (analisis + kerangka situs) dari hasil analyze.py."""
import argparse
import json
import os
import re
import shutil
from urllib.parse import urlparse


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "situs"


def main() -> None:
    ap = argparse.ArgumentParser(description="WebCop scaffold")
    ap.add_argument("report_data")
    ap.add_argument("--url", default="")
    ap.add_argument("--root", default="webcop-output")
    ap.add_argument("--template", choices=("plain", "tailwind", "bootstrap"), default="plain")
    a = ap.parse_args()

    name = slug(urlparse(a.url).netloc) if a.url else "situs"
    base = os.path.join(a.root, name)
    n = 2
    while os.path.exists(base):
        base = os.path.join(a.root, f"{name}-{n}")
        n += 1
    for d in ("analysis", "site/css", "site/js", "site/img"):
        os.makedirs(os.path.join(base, d))

    for f in ("analysis.json", "tokens.json", "structure.txt"):
        shutil.copy(os.path.join(a.report_data, f), os.path.join(base, "analysis", f))
    with open(os.path.join(a.report_data, "analysis.json"), encoding="utf-8") as f:
        an = json.load(f)
    with open(os.path.join(a.report_data, "tokens.json"), encoding="utf-8") as f:
        tk = json.load(f)

    cols = tk.get("colors", [])
    fonts = tk.get("fonts", []) or ["system-ui"]
    generic_fonts = {"system-ui", "sans-serif", "serif", "monospace", "cursive", "fantasy", "ui-sans-serif", "ui-serif", "ui-monospace"}
    primary_font = fonts[0] if fonts[0].lower() in generic_fonts else f"'{fonts[0]}'"
    var = "\n".join(f"  --color-{i+1}: {c};" for i, c in enumerate(cols))
    radius = (tk.get("border_radius") or ["8px"])[0]
    spacing = (tk.get("spacing") or ["1rem"])[0]
    shadow = (tk.get("box_shadow") or ["none"])[0]

    with open(os.path.join(base, "site/css/base.css"), "w", encoding="utf-8") as f:
        f.write(
            f":root {{\n{var}\n  --font-main: {primary_font}, system-ui, sans-serif;\n"
            f"  --radius: {radius};\n  --spacing: {spacing};\n  --shadow: {shadow};\n}}\n"
            "* { box-sizing: border-box; margin: 0; }\n"
            "body { font-family: var(--font-main); line-height: 1.5; }\n"
        )
    with open(os.path.join(base, "site/css/layout.css"), "w", encoding="utf-8") as f:
        f.write("/* TODO: grid/flex & breakpoint sesuai analysis.json */\n")
    with open(os.path.join(base, "site/css/components.css"), "w", encoding="utf-8") as f:
        f.write("/* TODO: navbar, hero, card, footer */\n")
    with open(os.path.join(base, "site/js/main.js"), "w", encoding="utf-8") as f:
        f.write("// TODO: interaksi (menu mobile, dll)\n")

    extra_head = ""
    if a.template == "tailwind":
        extra_head = '  <script src="https://cdn.tailwindcss.com"></script>\n'
    elif a.template == "bootstrap":
        extra_head = '  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">\n'

    body = []
    for line in an.get("semantic_outline", []):
        m = re.match(r"\s*([a-z]+)", line)
        if not m:
            continue
        tag = m.group(1)
        if tag in ("header", "nav", "main", "section", "article", "aside", "footer"):
            body.append(f"  <{tag}>\n    <!-- TODO: isi placeholder -->\n  </{tag}>")
    body_html = "\n".join(body) or "  <main><!-- TODO --></main>"
    with open(os.path.join(base, "site/index.html"), "w", encoding="utf-8") as f:
        f.write(
            '<!DOCTYPE html>\n<html lang="id">\n<head>\n  <meta charset="utf-8">\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '  <title>Judul Placeholder</title>\n'
            f'{extra_head}'
            '  <link rel="stylesheet" href="css/base.css">\n  <link rel="stylesheet" href="css/layout.css">\n'
            '  <link rel="stylesheet" href="css/components.css">\n</head>\n<body>\n'
            f'{body_html}\n  <script src="js/main.js"></script>\n</body>\n</html>\n'
        )
    with open(os.path.join(base, "README.md"), "w", encoding="utf-8") as f:
        f.write(
            f"# Referensi: {a.url}\n\nDibuat WebCop untuk belajar/referensi. Semua teks, gambar, dan brand adalah placeholder.\n"
            "- `analysis/` hasil analisis\n- `site/` kerangka proyek orisinal\n\nPeriksa lisensi/ketentuan situs sumber.\n"
        )
    print(base)


if __name__ == "__main__":
    main()
