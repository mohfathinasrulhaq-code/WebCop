import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import analyze  # noqa: E402
import fetch_page  # noqa: E402
import scaffold  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
