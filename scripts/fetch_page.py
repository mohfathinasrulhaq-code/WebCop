#!/usr/bin/env python3
"""WebCop fetcher: ambil HTML/CSS/JS PUBLIK untuk dianalisis. Hanya stdlib."""
import argparse
import json
import logging
import os
import re
import sys
import time
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

UA = "WebCop/1.0 (referensi belajar; patuh robots.txt)"
MAX_BYTES = 2_000_000


class AssetFinder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.css: List[str] = []
        self.js: List[str] = []
        self.img: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        a = dict(attrs)
        if tag == "link" and "stylesheet" in (a.get("rel") or "") and a.get("href"):
            self.css.append(a["href"])
        elif tag == "script" and a.get("src"):
            self.js.append(a["src"])
        elif tag == "img" and a.get("src"):
            self.img.append(a["src"])


def get(url: str, timeout: int = 15) -> Tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(MAX_BYTES), r.headers.get("Content-Type", "")


def safe_path(url: str, folder: str, used: Set[str]) -> str:
    p = urlparse(url)
    name = os.path.basename(p.path) or "index"
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)[:80]
    candidate = os.path.join(folder, name)
    if candidate in used:
        stem, ext = os.path.splitext(name)
        idx = 2
        while os.path.join(folder, f"{stem}_{idx}{ext}") in used:
            idx += 1
        candidate = os.path.join(folder, f"{stem}_{idx}{ext}")
    used.add(candidate)
    return candidate


def setup_logging(out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(out_dir, "log.txt"), encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(path: Optional[str]) -> Dict[str, object]:
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser(description="WebCop fetcher")
    ap.add_argument("url")
    ap.add_argument("--out", default="workdir")
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--max-files", type=int, default=25)
    ap.add_argument("--config", default=None, help="Path ke config.json")
    args = ap.parse_args()

    cfg = load_config(args.config)
    out_dir = str(cfg.get("out", args.out))
    delay = float(cfg.get("delay", args.delay))
    max_files = int(cfg.get("max_files", args.max_files))

    u = urlparse(args.url)
    if u.scheme not in ("http", "https"):
        sys.exit("URL harus diawali http:// atau https://")

    setup_logging(out_dir)
    logging.info("Memulai fetch: %s", args.url)

    robots_url = f"{u.scheme}://{u.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    robots_saved = False
    try:
        rp_data, _ = get(robots_url, timeout=10)
        robots_text = rp_data.decode("utf-8", errors="replace")
        with open(os.path.join(out_dir, "robots.txt"), "w", encoding="utf-8") as f:
            f.write(robots_text)
        rp.parse(robots_text.splitlines())
        robots_saved = True
        logging.info("robots.txt disimpan dari %s", robots_url)
    except Exception as e:
        logging.info("robots.txt tidak tersedia/tidak terbaca (%s): lanjut dengan sopan", e)

    if not rp.can_fetch(UA, args.url):
        logging.error("DIBLOKIR oleh robots.txt: %s", args.url)
        sys.exit("DIBLOKIR oleh robots.txt. WebCop berhenti. Minta user menyimpan halaman manual.")

    os.makedirs(os.path.join(out_dir, "css"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "js"), exist_ok=True)

    html, _ = get(args.url)
    text = html.decode("utf-8", errors="replace")
    with open(os.path.join(out_dir, "page.html"), "w", encoding="utf-8") as f:
        f.write(text)

    finder = AssetFinder()
    finder.feed(text)
    manifest: Dict[str, object] = {
        "url": args.url,
        "robots_txt": robots_saved,
        "css": [],
        "js": [],
        "images_listed_only": [],
    }
    count = 0
    seen_urls: Set[str] = set()
    used_paths: Set[str] = set()

    for kind, items, folder in (("css", finder.css, "css"), ("js", finder.js, "js")):
        for ref in items:
            if count >= max_files:
                break
            full = urljoin(args.url, ref)
            if full in seen_urls:
                continue
            seen_urls.add(full)
            if not rp.can_fetch(UA, full):
                logging.info("Dilewati (robots.txt): %s", full)
                continue
            time.sleep(delay)
            try:
                data, _ = get(full)
            except Exception as e:
                logging.warning("Gagal unduh %s: %s", full, e)
                manifest[kind].append({"url": full, "error": str(e)})  # type: ignore[union-attr]
                continue
            path = safe_path(full, os.path.join(out_dir, folder), used_paths)
            with open(path, "wb") as f:
                f.write(data)
            manifest[kind].append({"url": full, "saved": path, "bytes": len(data)})  # type: ignore[union-attr]
            count += 1

    manifest["images_listed_only"] = [urljoin(args.url, i) for i in finder.img]
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    logging.info("Selesai: %d file CSS/JS, %d gambar dicatat. Folder: %s", count, len(finder.img), out_dir)


if __name__ == "__main__":
    main()
