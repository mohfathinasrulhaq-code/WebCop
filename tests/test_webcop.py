import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import analyze  # type: ignore  # noqa: E402
import check_originality  # type: ignore  # noqa: E402
import fetch_page  # type: ignore  # noqa: E402
import scaffold  # type: ignore  # noqa: E402


class TestWebCop(unittest.TestCase):
    def test_safe_path_collision(self) -> None:
        used = set()
        p1 = fetch_page.safe_path("https://example.com/a/style.css", "css", used)
        p2 = fetch_page.safe_path("https://example.com/b/style.css", "css", used)
        self.assertNotEqual(p1, p2)
        self.assertTrue(p2.endswith("style_2.css"))

    def test_asset_finder(self) -> None:
        finder = fetch_page.AssetFinder()
        finder.feed('<link rel="stylesheet" href="/a.css"><script src="/b.js"></script><img src="/c.png">')
        self.assertEqual(finder.css, ["/a.css"])
        self.assertEqual(finder.js, ["/b.js"])
        self.assertEqual(finder.img, ["/c.png"])

    def test_normalize_hex(self) -> None:
        self.assertEqual(analyze.normalize_hex("#ABC"), "#aabbcc")
        self.assertEqual(analyze.normalize_hex("#123456"), "#123456")

    def test_walker_outline(self) -> None:
        w = analyze.Walker()
        w.feed("<html><head><title>Demo</title></head><body><header><nav></nav></header><main></main></body></html>")
        self.assertEqual(w.title, "Demo")
        self.assertTrue(any("header" in line for line in w.outline))
        self.assertTrue(any("main" in line for line in w.outline))

    def test_slug(self) -> None:
        self.assertEqual(scaffold.slug("Example.COM"), "example-com")
        self.assertEqual(scaffold.slug(""), "situs")

    def _run_analyze_fixture(self, fixture_name: str) -> dict:
        fixtures_dir = os.path.join(os.path.dirname(__file__), "fixtures")
        with tempfile.TemporaryDirectory() as tmp:
            workdir = os.path.join(tmp, "work")
            outdir = os.path.join(tmp, "out")
            os.makedirs(workdir)
            shutil.copy(os.path.join(fixtures_dir, fixture_name), os.path.join(workdir, "page.html"))
            script = os.path.join(os.path.dirname(__file__), "..", "scripts", "analyze.py")
            subprocess.run([sys.executable, script, workdir, "--out", outdir], check=True, stdout=subprocess.DEVNULL)
            with open(os.path.join(outdir, "analysis.json"), encoding="utf-8") as f:
                return json.load(f)

    def test_fixtures_detection(self) -> None:
        bs = self._run_analyze_fixture("bootstrap.html")
        self.assertEqual(bs["schema_version"], "1.0.0")
        self.assertIn("Bootstrap", bs["technologies"])
        self.assertTrue(any(e["temuan"] == "Bootstrap" for e in bs["technology_evidence"]))

        tw = self._run_analyze_fixture("tailwind.html")
        self.assertIn("Tailwind CSS", tw["technologies"])

        spa = self._run_analyze_fixture("spa_empty.html")
        self.assertIn("css", spa["missing"])
        self.assertTrue(any("SPA" in w for w in spa["warnings"]))

        custom = self._run_analyze_fixture("custom_css.html")
        self.assertNotIn("Tailwind CSS", custom["technologies"])

    def test_check_originality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src")
            tgt = os.path.join(tmp, "tgt")
            os.makedirs(src)
            os.makedirs(tgt)
            with open(os.path.join(src, "page.html"), "w", encoding="utf-8") as f:
                f.write('<html><body><p class="hero-box">Halo dunia ini contoh teks sumber</p></body></html>')
            with open(os.path.join(tgt, "index.html"), "w", encoding="utf-8") as f:
                f.write('<html><body><p class="my-card">Konten baru yang sepenuhnya berbeda</p></body></html>')
            res = check_originality.check_originality(src, tgt)
            self.assertTrue(res["passed"])
            self.assertEqual(res["text_similarity"], 0.0)

    def test_svg_design_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            svg_path = os.path.join(tmp, "design.svg")
            out_dir = os.path.join(tmp, "out")
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(
                    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900">'
                    '<g id="Hero"><rect width="200" height="80" rx="12" fill="#2563eb"/>'
                    '<text font-family="Plus Jakarta Sans" fill="#ffffff">Hello</text></g>'
                    "</svg>"
                )
            script = os.path.join(os.path.dirname(__file__), "..", "scripts", "analyze.py")
            subprocess.run([sys.executable, script, svg_path, "--out", out_dir], check=True, stdout=subprocess.DEVNULL)
            with open(os.path.join(out_dir, "analysis.json"), encoding="utf-8") as f:
                an = json.load(f)
            with open(os.path.join(out_dir, "tokens.json"), encoding="utf-8") as f:
                tk = json.load(f)
            self.assertIn("Hero", an["svg_layers"])
            self.assertIn("#2563eb", tk["colors"])
            self.assertIn("Plus Jakarta Sans", tk["fonts"])
            self.assertIn("12px", tk["border_radius"])


if __name__ == "__main__":
    unittest.main()
