"""Markdown to deck structure.

Conventions, kept small on purpose:
- `# Title` at the top: deck title, next paragraph is the subtitle.
- `## Slide title`: starts a slide.
- `- item`: bullets. Plain lines: paragraphs.
- `![caption](path)`: image slide (caption = alt text).
- `| a | b |` rows with a `|---|---|` line: table slide.
"""

import re

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _is_table_sep(line):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    return bool(cells) and all(set(c) <= set("-: ") and "-" in c for c in cells)


def _split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_markdown(text):
    if not isinstance(text, str) or not text.strip():
        raise ValueError("markdown needs some text, e.g. '# My talk\\n\\n## Intro\\n\\n- point one'")
    lines = text.splitlines()
    title = "Untitled deck"
    subtitle = ""
    sections = []
    current = None

    def flush():
        nonlocal current
        if current is not None:
            sections.append(current)
        current = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# ") and current is None and not sections:
            title = line[2:].strip() or title
            continue
        if line.startswith("## "):
            flush()
            current = {"title": line[3:].strip(), "bullets": [], "paragraphs": [], "image": None, "caption": "", "table": []}
            continue
        if current is None:
            # text before the first ## is the title slide subtitle
            if subtitle:
                subtitle += " " + line.strip()
            else:
                subtitle = line.strip()
            continue
        m = _IMG_RE.search(line)
        if m:
            current["image"] = m.group(2).strip()
            current["caption"] = m.group(1).strip()
            continue
        if line.strip().startswith("|"):
            if _is_table_sep(line):
                continue
            current["table"].append(_split_row(line))
            continue
        if line.lstrip().startswith(("- ", "* ")):
            current["bullets"].append(line.lstrip()[2:].strip())
            continue
        current["paragraphs"].append(line.strip())
    flush()

    slides = [{"type": "title", "title": title}]
    if subtitle:
        slides[0]["subtitle"] = subtitle
    for s in sections:
        if not s["title"]:
            raise ValueError("every '## ' heading needs a title")
        if s["table"]:
            rows = s["table"]
            slides.append({"type": "table", "title": s["title"], "headers": rows[0], "rows": rows[1:]})
        elif s["image"]:
            slide = {"type": "image", "title": s["title"], "image": s["image"]}
            if s["caption"]:
                slide["caption"] = s["caption"]
            slides.append(slide)
        elif s["bullets"]:
            slides.append({"type": "bullets", "title": s["title"], "items": s["bullets"]})
        elif s["paragraphs"]:
            slides.append({"type": "text", "title": s["title"], "paragraphs": s["paragraphs"]})
        else:
            raise ValueError(f"slide '{s['title']}' is empty: add bullets, text, an image or a table")
    return {"title": title, "slides": slides}
