"""Build .pptx decks from a structure dict. 16:9, blank layout, drawn shapes.

A deck is a dict: title, author, theme, slides. Each slide has a "type":
title, bullets, text, image or table. No templates, no GUI, just python-pptx.
"""

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from .markdown import parse_markdown

THEMES = {
    "light": {"bg": "FFFFFF", "title": "1A1A2E", "body": "333333", "accent": "2563EB", "muted": "6B7280"},
    "dark": {"bg": "111827", "title": "F9FAFB", "body": "D1D5DB", "accent": "60A5FA", "muted": "9CA3AF"},
    "blue": {"bg": "EFF6FF", "title": "1E3A5F", "body": "334155", "accent": "0E7490", "muted": "64748B"},
}

_SLIDE_W = Inches(13.333)
_SLIDE_H = Inches(7.5)
_MARGIN = Inches(0.7)

_TYPES = ("title", "bullets", "text", "image", "table")


def _rgb(hexcolor):
    return RGBColor.from_string(hexcolor)


def list_themes():
    return {name: dict(spec) for name, spec in THEMES.items()}


def _theme(name):
    if name is None:
        name = "light"
    if name not in THEMES:
        raise ValueError(f"unknown theme '{name}'. Run 'slideforge themes' to see them all.")
    return THEMES[name]


def _bg(slide, color):
    shape = slide.shapes.add_shape(1, 0, 0, _SLIDE_W, _SLIDE_H)  # plain rectangle
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(color)
    shape.line.fill.background()
    return shape


def _textbox(slide, left, top, width, height):
    box = slide.shapes.add_textbox(left, top, width, height)
    frame = box.text_frame
    frame.word_wrap = True
    return frame


def _para(frame, text, size, color, bold=False, first=False, align=PP_ALIGN.LEFT, space_after=6):
    para = frame.paragraphs[0] if first else frame.add_paragraph()
    para.text = ""
    para.alignment = align
    para.space_after = Pt(space_after)
    run = para.add_run()
    run.text = str(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    return para


def _accent_bar(slide, theme):
    bar = slide.shapes.add_shape(1, _MARGIN, Inches(1.15), Inches(0.9), Pt(4))
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme["accent"])
    bar.line.fill.background()


def _slide_title(slide, title, theme):
    _accent_bar(slide, theme)
    frame = _textbox(slide, _MARGIN, Inches(0.35), _SLIDE_W - 2 * _MARGIN, Inches(0.7))
    _para(frame, title, 32, theme["title"], bold=True, first=True, space_after=0)


def _new_slide(prs, theme):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _bg(slide, theme["bg"])
    return slide


def _title_slide(prs, data, theme):
    slide = _new_slide(prs, theme)
    frame = _textbox(slide, Inches(1.2), Inches(2.4), _SLIDE_W - Inches(2.4), Inches(2.6))
    _para(frame, data["title"], 44, theme["title"], bold=True, first=True, align=PP_ALIGN.CENTER, space_after=10)
    if data.get("subtitle"):
        _para(frame, data["subtitle"], 22, theme["muted"], align=PP_ALIGN.CENTER)
    bar = slide.shapes.add_shape(1, Inches(6.0), Inches(2.1), Inches(1.3), Pt(5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = _rgb(theme["accent"])
    bar.line.fill.background()


def _bullets_slide(prs, data, theme):
    slide = _new_slide(prs, theme)
    _slide_title(slide, data["title"], theme)
    frame = _textbox(slide, _MARGIN, Inches(1.6), _SLIDE_W - 2 * _MARGIN, Inches(5.3))
    for i, item in enumerate(data["items"]):
        _para(frame, f"•  {item}", 22, theme["body"], first=(i == 0), space_after=12)


def _text_slide(prs, data, theme):
    slide = _new_slide(prs, theme)
    _slide_title(slide, data["title"], theme)
    frame = _textbox(slide, _MARGIN, Inches(1.6), _SLIDE_W - 2 * _MARGIN, Inches(5.3))
    for i, text in enumerate(data["paragraphs"]):
        _para(frame, text, 20, theme["body"], first=(i == 0), space_after=14)


def _fit_box(img_w, img_h, box_w, box_h):
    # scale the picture to fit the box, keep the aspect ratio
    scale = min(box_w / img_w, box_h / img_h)
    return img_w * scale, img_h * scale


def _image_slide(prs, data, theme):
    from PIL import Image

    path = data["image"]
    if not os.path.isfile(path):
        raise ValueError(f"image slide: can't find image '{path}'")
    slide = _new_slide(prs, theme)
    _slide_title(slide, data["title"], theme)
    with Image.open(path) as img:
        w, h = _fit_box(img.width, img.height, 11.9, 4.9)
    slide.shapes.add_picture(path, Inches((13.333 - w) / 2), Inches(1.7), width=Inches(w), height=Inches(h))
    if data.get("caption"):
        frame = _textbox(slide, _MARGIN, Inches(6.7), _SLIDE_W - 2 * _MARGIN, Inches(0.5))
        _para(frame, data["caption"], 16, theme["muted"], first=True, align=PP_ALIGN.CENTER, space_after=0)


def _table_slide(prs, data, theme):
    slide = _new_slide(prs, theme)
    _slide_title(slide, data["title"], theme)
    headers = data["headers"]
    rows = data["rows"]
    shape = slide.shapes.add_table(len(rows) + 1, len(headers), _MARGIN, Inches(1.7),
                                   _SLIDE_W - 2 * _MARGIN, Inches(0.6 * (len(rows) + 1)))
    table = shape.table
    for j, header in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = str(header)
        for para in cell.text_frame.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(18)
                run.font.color.rgb = _rgb("FFFFFF")
        cell.fill.solid()
        cell.fill.fore_color.rgb = _rgb(theme["accent"])
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            cell = table.cell(i + 1, j)
            cell.text = str(value)
            for para in cell.text_frame.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(18)
                    run.font.color.rgb = _rgb(theme["body"])


def _check_slide(data, index):
    if not isinstance(data, dict):
        raise ValueError(f"slide {index + 1} has to be an object with a 'type'")
    kind = data.get("type")
    if kind not in _TYPES:
        raise ValueError(f"slide {index + 1}: unknown type '{kind}'. Types: {', '.join(_TYPES)}")
    if kind != "title" and not data.get("title"):
        raise ValueError(f"slide {index + 1}: '{kind}' slides need a 'title'")
    if kind == "title" and not data.get("title"):
        raise ValueError(f"slide {index + 1}: 'title' slides need a 'title'")
    if kind == "bullets":
        items = data.get("items")
        if not isinstance(items, list) or not items:
            raise ValueError(f"slide {index + 1}: 'bullets' slides need a non-empty 'items' list")
    if kind == "text":
        paras = data.get("paragraphs")
        if not isinstance(paras, list) or not paras:
            raise ValueError(f"slide {index + 1}: 'text' slides need a non-empty 'paragraphs' list")
    if kind == "image" and not data.get("image"):
        raise ValueError(f"slide {index + 1}: 'image' slides need an 'image' path")
    if kind == "table":
        headers = data.get("headers")
        rows = data.get("rows")
        if not isinstance(headers, list) or not headers:
            raise ValueError(f"slide {index + 1}: 'table' slides need a non-empty 'headers' list")
        if not isinstance(rows, list) or not rows:
            raise ValueError(f"slide {index + 1}: 'table' slides need a non-empty 'rows' list")
        if any(len(row) != len(headers) for row in rows):
            raise ValueError(f"slide {index + 1}: every table row needs {len(headers)} cells")


_BUILDERS = {
    "title": _title_slide,
    "bullets": _bullets_slide,
    "text": _text_slide,
    "image": _image_slide,
    "table": _table_slide,
}


def build_deck(structure, output, theme="light"):
    if not isinstance(structure, dict):
        raise ValueError("structure has to be an object, e.g. {\"title\": \"Talk\", \"slides\": [...]}")
    slides = structure.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("structure needs a non-empty 'slides' list")
    spec = _theme(theme or structure.get("theme", "light"))
    for i, data in enumerate(slides):
        _check_slide(data, i)
    prs = Presentation()
    prs.slide_width = _SLIDE_W
    prs.slide_height = _SLIDE_H
    for data in slides:
        _BUILDERS[data["type"]](prs, data, spec)
    core = prs.core_properties
    core.title = structure.get("title", "")
    core.author = structure.get("author", "")
    prs.save(output)
    info = describe(output)
    info["output"] = output
    info["theme"] = theme or structure.get("theme", "light")
    return info


def from_markdown(text, output, theme="light"):
    return build_deck(parse_markdown(text), output, theme)


def describe(path):
    if not os.path.isfile(path):
        raise ValueError(f"can't find '{path}'")
    if os.path.splitext(path)[1].lower() != ".pptx":
        raise ValueError("describe only reads .pptx files")
    prs = Presentation(path)
    title = ""
    if prs.slides:
        for shape in prs.slides[0].shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                title = shape.text_frame.text.strip().split("\n")[0]
                break
    return {
        "slides": len(prs.slides),
        "title": title,
        "author": prs.core_properties.author or "",
        "width_in": round(prs.slide_width / 914400, 3),
        "height_in": round(prs.slide_height / 914400, 3),
        "size_bytes": os.path.getsize(path),
    }
