"""Tests run against decks built on the fly, no fixtures needed."""

import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slideforge import build_deck, describe, from_markdown, list_themes, parse_markdown  # noqa: E402


def _make_image(path, size=(800, 600)):
    from PIL import Image

    Image.new("RGB", size, color=(37, 99, 235)).save(path)


STRUCTURE = {
    "title": "Weekly report",
    "author": "Alfredo Ramos",
    "slides": [
        {"type": "title", "title": "Weekly report", "subtitle": "Week 47"},
        {"type": "bullets", "title": "What shipped", "items": ["pdfforge", "slideforge", "qrforge"]},
        {"type": "text", "title": "Notes", "paragraphs": ["First note.", "Second note."]},
        {"type": "table", "title": "Numbers", "headers": ["Tool", "Tests"], "rows": [["pdfforge", 24], ["slideforge", 22]]},
    ],
}

MD = """# Weekly report
Week 47

## What shipped
- pdfforge
- slideforge

## Numbers
| Tool | Tests |
| ---- | ----- |
| pdfforge | 24 |

## Screenshot
![The new deck](shot.png)
"""


class TestSlideforge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.img = os.path.join(cls.tmp, "shot.png")
        _make_image(cls.img)

    def out(self, name):
        return os.path.join(self.tmp, name)

    def test_themes(self):
        themes = list_themes()
        self.assertEqual(set(themes), {"light", "dark", "blue"})
        for spec in themes.values():
            for key in ("bg", "title", "body", "accent", "muted"):
                self.assertIn(key, spec)

    def test_build_structure(self):
        out = build_deck(STRUCTURE, self.out("talk.pptx"))
        self.assertEqual(out["slides"], 4)
        self.assertEqual(out["title"], "Weekly report")
        self.assertEqual(out["author"], "Alfredo Ramos")
        self.assertEqual(out["width_in"], 13.333)
        self.assertEqual(out["height_in"], 7.5)
        self.assertGreater(out["size_bytes"], 10000)

    def test_build_dark_theme(self):
        out = build_deck(STRUCTURE, self.out("dark.pptx"), theme="dark")
        self.assertEqual(out["slides"], 4)
        self.assertEqual(out["theme"], "dark")

    def test_build_image_slide(self):
        structure = {"title": "Pics", "slides": [
            {"type": "title", "title": "Pics"},
            {"type": "image", "title": "Screenshot", "image": self.img, "caption": "The new deck"},
        ]}
        out = build_deck(structure, self.out("pics.pptx"))
        self.assertEqual(out["slides"], 2)

    def test_build_image_wide(self):
        wide = os.path.join(self.tmp, "wide.png")
        _make_image(wide, size=(2000, 300))
        structure = {"title": "Pics", "slides": [
            {"type": "image", "title": "Wide", "image": wide},
        ]}
        out = build_deck(structure, self.out("wide.pptx"))
        self.assertEqual(out["slides"], 1)

    def test_unknown_theme_fails(self):
        with self.assertRaises(ValueError):
            build_deck(STRUCTURE, self.out("bad.pptx"), theme="neon")

    def test_empty_slides_fails(self):
        with self.assertRaises(ValueError):
            build_deck({"title": "Empty", "slides": []}, self.out("empty.pptx"))

    def test_unknown_type_fails(self):
        with self.assertRaises(ValueError):
            build_deck({"title": "Bad", "slides": [{"type": "video", "title": "Nope"}]}, self.out("bad.pptx"))

    def test_bullets_need_items(self):
        with self.assertRaises(ValueError):
            build_deck({"title": "Bad", "slides": [{"type": "bullets", "title": "Empty", "items": []}]},
                       self.out("bad.pptx"))

    def test_table_ragged_rows_fails(self):
        with self.assertRaises(ValueError):
            build_deck({"title": "Bad", "slides": [
                {"type": "table", "title": "T", "headers": ["A", "B"], "rows": [["only one"]]}]},
                self.out("bad.pptx"))

    def test_missing_image_fails(self):
        with self.assertRaises(ValueError):
            build_deck({"title": "Bad", "slides": [
                {"type": "image", "title": "Gone", "image": os.path.join(self.tmp, "nope.png")}]},
                self.out("bad.pptx"))

    def test_describe(self):
        path = self.out("desc.pptx")
        build_deck(STRUCTURE, path)
        info = describe(path)
        self.assertEqual(info["slides"], 4)
        self.assertEqual(info["title"], "Weekly report")

    def test_describe_missing(self):
        with self.assertRaises(ValueError):
            describe(os.path.join(self.tmp, "nope.pptx"))

    def test_parse_markdown(self):
        structure = parse_markdown(MD.replace("shot.png", self.img))
        self.assertEqual(structure["title"], "Weekly report")
        types = [s["type"] for s in structure["slides"]]
        self.assertEqual(types, ["title", "bullets", "table", "image"])
        self.assertEqual(structure["slides"][0]["subtitle"], "Week 47")
        self.assertEqual(structure["slides"][1]["items"], ["pdfforge", "slideforge"])
        self.assertEqual(structure["slides"][2]["headers"], ["Tool", "Tests"])
        self.assertEqual(structure["slides"][2]["rows"], [["pdfforge", "24"]])
        self.assertEqual(structure["slides"][3]["image"], self.img)

    def test_parse_markdown_text_slide(self):
        structure = parse_markdown("# Talk\n\n## Intro\nSome words here.\nMore words.")
        self.assertEqual(structure["slides"][1]["type"], "text")
        self.assertEqual(structure["slides"][1]["paragraphs"], ["Some words here.", "More words."])

    def test_parse_markdown_empty_fails(self):
        with self.assertRaises(ValueError):
            parse_markdown("   \n")

    def test_parse_markdown_empty_slide_fails(self):
        with self.assertRaises(ValueError):
            parse_markdown("# Talk\n\n## Nothing here\n\n## Next\n- one")

    def test_from_markdown(self):
        out = from_markdown(MD.replace("shot.png", self.img), self.out("md.pptx"), theme="blue")
        self.assertEqual(out["slides"], 4)
        self.assertEqual(out["theme"], "blue")

    def test_cli_create_structure(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        r = subprocess.run(
            [sys.executable, "-m", "slideforge.cli", "create", "-o", self.out("cli.pptx"),
             "--structure", json.dumps(STRUCTURE)],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["slides"], 4)

    def test_cli_create_markdown(self):
        md_path = os.path.join(self.tmp, "talk.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(MD.replace("shot.png", self.img))
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        r = subprocess.run(
            [sys.executable, "-m", "slideforge.cli", "create", "-o", self.out("cli-md.pptx"),
             "--markdown", md_path],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["slides"], 4)

    def test_cli_themes(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        r = subprocess.run([sys.executable, "-m", "slideforge.cli", "themes"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("dark", json.loads(r.stdout))

    def test_cli_describe(self):
        path = self.out("cli-desc.pptx")
        build_deck(STRUCTURE, path)
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        r = subprocess.run([sys.executable, "-m", "slideforge.cli", "describe", "-i", path],
                           capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)["slides"], 4)

    def test_mcp_smoke(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__), ".."))
        proc = subprocess.Popen(
            [sys.executable, "-m", "slideforge.cli", "mcp"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
        )
        try:
            reqs = [
                {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
                {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": "list_themes", "arguments": {}}},
            ]
            for req in reqs:
                proc.stdin.write(json.dumps(req) + "\n")
            proc.stdin.flush()
            lines = [proc.stdout.readline() for _ in range(3)]
            init = json.loads(lines[0])
            self.assertEqual(init["result"]["serverInfo"]["name"], "slideforge")
            tools = json.loads(lines[1])["result"]["tools"]
            self.assertIn("create_deck", [t["name"] for t in tools])
            payload = json.loads(json.loads(lines[2])["result"]["content"][0]["text"])
            self.assertIn("dark", payload)
        finally:
            proc.stdin.close()
            proc.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
