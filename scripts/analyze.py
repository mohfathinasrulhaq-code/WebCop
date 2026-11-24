#!/usr/bin/env python3
"""WebCop analyzer: petakan struktur, teknologi, design tokens, dan rekonstruksi folder."""
import argparse
import collections
import glob
import json
import logging
import os
import re
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple

SEMANTIC = {"header", "nav", "main", "section", "article", "aside", "footer", "form"}

TECH: Dict[str, List[str]] = {
    "React": [r"react(\.|-dom)", r"data-reactroot", r"__NEXT_DATA__", r"_next/"],
    "Next.js": [r"_next/", r"__NEXT_DATA__"],
    "Vue": [r"vue(\.|@)", r"data-v-", r"__vue__"],
    "Nuxt": [r"_nuxt/"],
    "Angular": [r"ng-version", r"angular"],
    "Svelte": [r"svelte"],
    "SSR": [r"hydrate(?:Root)?\(", r"renderToString", r"data-reactroot", r"__NEXT_DATA__", r"__NUXT__"],
    "jQuery": [r"jquery"],
    "Bootstrap": [r"bootstrap"],
    "Tailwind CSS": [r"tailwind", r'class="[^"]*\b(?:px|py|mt|mb)-\d[^"]*"'],
    "WordPress": [r"wp-content", r"wp-includes", r'generator" content="WordPress'],
    "Joomla": [r"/media/jui/", r'generator" content="Joomla'],
    "Drupal": [r"Drupal\.settings", r"/sites/default/files/", r'generator" content="Drupal'],
    "Google Fonts": [r"fonts\.googleapis\.com"],
    "Font Awesome": [r"font-?awesome"],
    "Alpine.js": [r"x-data", r"alpine"],
}


class Walker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.depth: int = 0
        self.tags: collections.Counter = collections.Counter()
        self.outline: List[str] = []
        self.classes: collections.Counter = collections.Counter()
        self.title: str = ""
        self._in_title: bool = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        a = dict(attrs)
        self.tags[tag] += 1
        for c in (a.get("class") or "").split():
            self.classes[c] += 1
        if tag == "title":
            self._in_title = True
        if tag in SEMANTIC or (tag == "div" and a.get("id")):
            label = tag + (f"#{a['id']}" if a.get("id") else "")
            cls = (a.get("class") or "").split()[:3]
            if cls:
                label += "." + ".".join(cls)
            self.outline.append("  " * min(self.depth, 6) + label)
        if tag not in ("br", "img", "input", "meta", "link", "hr"):
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        self.depth = max(0, self.depth - 1)

    def handle_data(self, d: str) -> None:
        if self._in_title:
            self.title += d.strip()


def normalize_hex(color: str) -> str:
    c = color.lower().strip()
    if len(c) == 4 and c.startswith("#"):
        return "#" + "".join(ch * 2 for ch in c[1:])
    return c


def read_all(folder: str, pattern: str) -> str:
    out = ""
    for p in glob.glob(os.path.join(folder, pattern)):
        with open(p, encoding="utf-8", errors="ignore") as f:
            out += f.read() + "\n"
    return out


def top(counter: collections.Counter, n: int = 8) -> List[str]:
    return [k for k, _ in counter.most_common(n)]


def render_markdown(analysis: Dict[str, object], tokens: Dict[str, object], structure: str) -> str:
    techs = ", ".join(analysis.get("technologies", [])) or "-"  # type: ignore[arg-type]
    colors = ", ".join(tokens.get("colors", [])) or "-"  # type: ignore[arg-type]
    fonts = ", ".join(tokens.get("fonts", [])) or "-"  # type: ignore[arg-type]
    radii = ", ".join(tokens.get("border_radius", [])) or "-"  # type: ignore[arg-type]
    spacing = ", ".join(tokens.get("spacing", [])) or "-"  # type: ignore[arg-type]
    shadows = ", ".join(tokens.get("box_shadow", [])) or "-"  # type: ignore[arg-type]
    return (
        f"# Laporan Analisis WebCop: {analysis.get('title') or 'Tanpa Judul'}\n\n"
        f"- **Teknologi**: {techs}\n"
        f"- **Warna**: {colors}\n"
        f"- **Font**: {fonts}\n"
        f"- **Border Radius**: {radii}\n"
        f"- **Spacing**: {spacing}\n"
        f"- **Box Shadow**: {shadows}\n\n"
        f"## Struktur Rekonstruksi\n```\n{structure}```\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="WebCop analyzer")
    ap.add_argument("workdir")
    ap.add_argument("--out", default="report_data")
    ap.add_argument("--format", choices=("json", "markdown", "all"), default="json")
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    with open(os.path.join(args.workdir, "page.html"), encoding="utf-8", errors="ignore") as f:
        html = f.read()
    css = read_all(args.workdir, "css/*") + "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
    js_names = " ".join(os.listdir(os.path.join(args.workdir, "js"))) if os.path.isdir(os.path.join(args.workdir, "js")) else ""
    blob = html + "\n" + css + "\n" + js_names

    w = Walker()
    w.feed(html)

    tech = [n for n, pats in TECH.items() if any(re.search(p, blob, re.I) for p in pats)]
    css_keywords = {"inherit", "initial", "unset", "revert", "none", "auto"}

    colors = collections.Counter(
        normalize_hex(c) for c in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", css)
    )
    fonts = collections.Counter(
        clean for m in re.findall(r"font-family\s*:\s*([^;}{]+)", css, re.I)
        for clean in [re.sub(r"\s*!important\s*$", "", m.split(",")[0], flags=re.I).strip().strip("'\"")]
        if clean and clean.lower() not in css_keywords
    )
    radii = collections.Counter(
        clean for r in re.findall(r"border-radius\s*:\s*([^;}{]+)", css, re.I)
        for clean in [re.sub(r"\s*!important\s*$", "", r, flags=re.I).strip()]
        if clean and clean.lower() not in css_keywords
    )
    spacing = collections.Counter(
        clean for s in re.findall(r"(?:margin|padding)(?:-(?:top|right|bottom|left))?\s*:\s*([^;}{]+)", css, re.I)
        for clean in [re.sub(r"\s*!important\s*$", "", s, flags=re.I).strip()]
        if clean and clean.lower() not in css_keywords and clean != "0"
    )
    shadows = collections.Counter(
        clean for sh in re.findall(r"box-shadow\s*:\s*([^;}{]+)", css, re.I)
        for clean in [re.sub(r"\s*!important\s*$", "", sh, flags=re.I).strip()]
        if clean and clean.lower() not in css_keywords
    )

    layout = {
        "flexbox": len(re.findall(r"display\s*:\s*flex", css, re.I)),
        "grid": len(re.findall(r"display\s*:\s*grid", css, re.I)),
        "media_queries": top(collections.Counter(re.findall(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+px)", css)), 6),
    }
    components = {
        "navbar": bool(w.tags.get("nav")),
        "hero": any("hero" in c or "banner" in c for c in w.classes),
        "cards": any("card" in c for c in w.classes),
        "footer": bool(w.tags.get("footer")),
        "forms": bool(w.tags.get("form")),
    }

    lines = ["proyek-baru/", "├── index.html"]
    css_n = len(glob.glob(os.path.join(args.workdir, "css/*")))
    js_n = len(glob.glob(os.path.join(args.workdir, "js/*")))
    if css_n or "<style" in html:
        lines += ["├── css/", "│   ├── base.css       # reset, variabel (tokens)", "│   ├── layout.css", "│   └── components.css"]
    if js_n or "<script" in html:
        lines += ["├── js/", "│   └── main.js"]
    lines += ["├── img/               # GANTI dengan aset milikmu", "└── README.md"]
    structure_text = "\n".join(lines) + "\n"

    os.makedirs(args.out, exist_ok=True)
    analysis = {
        "title": w.title,
        "technologies": tech,
        "semantic_outline": w.outline[:60],
        "tag_counts": dict(w.tags.most_common(12)),
        "layout": layout,
        "components": components,
    }
    tokens = {
        "colors": top(colors, 10),
        "fonts": top(fonts, 4),
        "border_radius": top(radii, 4),
        "spacing": top(spacing, 6),
        "box_shadow": top(shadows, 3),
        "note": "Gunakan sebagai inspirasi; ubah nilainya agar desain milikmu orisinal.",
    }
    for name, data in (("analysis.json", analysis), ("tokens.json", tokens)):
        with open(os.path.join(args.out, name), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    with open(os.path.join(args.out, "structure.txt"), "w", encoding="utf-8") as f:
        f.write(structure_text)
    if args.format in ("markdown", "all"):
        with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as f:
            f.write(render_markdown(analysis, tokens, structure_text))
    print(json.dumps({"analysis": analysis, "tokens": tokens}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
