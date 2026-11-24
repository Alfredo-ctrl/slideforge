"""Build a small sample deck. Run from the project root: python examples/build_example.py"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from slideforge import build_deck  # noqa: E402

out = os.path.join(os.path.dirname(__file__), "sample.pptx")
info = build_deck({
    "title": "Weekly report",
    "author": "Alfredo Ramos",
    "slides": [
        {"type": "title", "title": "Weekly report", "subtitle": "Week 47"},
        {"type": "bullets", "title": "What shipped", "items": ["pdfforge", "slideforge", "qrforge"]},
        {"type": "table", "title": "Numbers", "headers": ["Tool", "Tests"], "rows": [["pdfforge", 24], ["slideforge", 22]]},
        {"type": "text", "title": "Next", "paragraphs": ["chartforge is next in the queue."]},
    ],
}, out, theme="dark")
print(info)
