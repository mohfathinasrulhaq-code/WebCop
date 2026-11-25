#!/usr/bin/env python3
"""WebCop originality checker: bandingkan proyek baru dengan situs sumber (teks, kelas, palet warna)."""
import argparse
import glob
import json
import math
import os
import re
import sys
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set, Tuple


class TextAndClassExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.classes: Set[str] = set()
        self._text_parts: List[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag in ("script", "style"):
            self._skip = True
        a = dict(attrs)
        for c in (a.get("class") or "").split():
            self.classes.add(c)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            t = data.strip()
            if t:
                self._text_parts.append(t)

    @property
    def text(self) -> str:
        return " ".join(self._text_parts)


def ngrams(text: str, n: int = 3) -> Set[Tuple[str, ...]]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def jaccard(a: Set, b: Set) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def color_distance(c1: str, c2: str) -> float:
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def extract_colors(folder: str) -> Set[str]:
    colors: Set[str] = set()
    for pattern in ("*.html", "css/*.css", "*_files/*.css"):
        for path in glob.glob(os.path.join(folder, pattern)):
            with open(path, encoding="utf-8", errors="ignore") as f:
                for c in re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", f.read()):
                    c = c.lower()
                    if len(c) == 4:
                        c = "#" + "".join(ch * 2 for ch in c[1:])
                    colors.add(c)
    return colors


def check_originality(source_dir: str, target_dir: str) -> Dict[str, object]:
    src_html_path = os.path.join(source_dir, "page.html")
    tgt_html_path = os.path.join(target_dir, "index.html")
    with open(src_html_path, encoding="utf-8", errors="ignore") as f:
        src_html = f.read()
    with open(tgt_html_path, encoding="utf-8", errors="ignore") as f:
        tgt_html = f.read()

    src_ext, tgt_ext = TextAndClassExtractor(), TextAndClassExtractor()
    src_ext.feed(src_html)
    tgt_ext.feed(tgt_html)

    text_sim = round(jaccard(ngrams(src_ext.text), ngrams(tgt_ext.text)), 4)
    class_sim = round(jaccard(src_ext.classes, tgt_ext.classes), 4)

    src_colors = extract_colors(source_dir)
    tgt_colors = extract_colors(target_dir)
    close_colors: List[Dict[str, object]] = []
    for tc in sorted(tgt_colors):
        if not src_colors:
            break
        nearest = min(src_colors, key=lambda sc: color_distance(tc, sc))
        dist = round(color_distance(tc, nearest), 2)
        if dist < 25.0:
            close_colors.append({"target": tc, "source": nearest, "distance": dist})

    warnings: List[str] = []
    if text_sim > 0.25:
        warnings.append(f"Kemiripan teks terlalu tinggi ({text_sim:.0%}); ganti teks dengan placeholder orisinal.")
    if class_sim > 0.50:
        warnings.append(f"Kemiripan nama kelas CSS tinggi ({class_sim:.0%}); pertimbangkan penamaan kelas sendiri.")
    if close_colors:
        warnings.append(f"{len(close_colors)} warna terlalu mirip dengan sumber (jarak RGB < 25).")

    return {
        "passed": len(warnings) == 0,
        "text_similarity": text_sim,
        "class_similarity": class_sim,
        "close_colors": close_colors,
        "warnings": warnings,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="WebCop originality checker")
    ap.add_argument("source_dir", help="Folder workdir hasil fetch_page.py")
    ap.add_argument("target_dir", help="Folder site/ hasil scaffold.py")
    args = ap.parse_args()

    result = check_originality(args.source_dir, args.target_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["passed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
