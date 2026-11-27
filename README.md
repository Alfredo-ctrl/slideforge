# slideforge

Build .pptx decks from a JSON structure or a Markdown file — from the terminal, from Python, or over MCP.

It builds .pptx decks with python-pptx. Decks are 16:9.

## Install

```sh
pip install git+https://github.com/Alfredo-ctrl/slideforge.git
```

## Use it from the terminal

```sh
# what themes exist?
slideforge themes

# describe a deck
slideforge describe -i talk.pptx

# build a deck from JSON
slideforge create -o talk.pptx --theme dark --structure '{
  "title": "Weekly report", "author": "Alfredo Ramos",
  "slides": [
    {"type": "title", "title": "Weekly report", "subtitle": "Week 47"},
    {"type": "bullets", "title": "What shipped", "items": ["pdfforge", "slideforge", "qrforge"]},
    {"type": "table", "title": "Numbers", "headers": ["Tool", "Tests"], "rows": [["pdfforge", 27], ["slideforge", 23]]}
  ]
}'

# or build it from Markdown
slideforge create -o talk.pptx --markdown talk.md
```

## Markdown format

```md
# Weekly report
Week 47

## What shipped
- pdfforge
- slideforge
- qrforge

## Numbers
| Tool | Tests |
| ---- | ----- |
| pdfforge | 27 |
| slideforge | 23 |

## Screenshot
![The new deck](shot.png)
```

`# ` is the deck title (next line is the subtitle), `## ` starts a slide, `- ` are bullets, `![alt](path)` is an image slide, `| a | b |` rows are a table slide.

## Slide types

| type | needs |
| ---- | ----- |
| `title` | `title`, optional `subtitle` |
| `bullets` | `title`, `items` (list) |
| `text` | `title`, `paragraphs` (list) |
| `image` | `title`, `image` (path), optional `caption` |
| `table` | `title`, `headers` (list), `rows` (list of lists) |

Themes: `light`, `dark`, `blue`. Decks are 16:9.

## Use it from Python

```python
from slideforge import build_deck, from_markdown, describe

build_deck({"title": "Talk", "slides": [
    {"type": "title", "title": "Talk"},
    {"type": "bullets", "title": "Points", "items": ["one", "two"]},
]}, "talk.pptx", theme="dark")

from_markdown(open("talk.md").read(), "talk.pptx")
describe("talk.pptx")  # slides, title, size, dimensions
```

## MCP server

Any MCP client can use slideforge as tools:

```sh
slideforge mcp
```

It speaks MCP over stdio and exposes `create_deck`, `create_deck_from_markdown`, `describe_deck`, `list_themes`. Example client config:

```json
{
  "mcpServers": {
    "slideforge": {"command": "slideforge", "args": ["mcp"]}
  }
}
```

## License

See [LICENSE](LICENSE).
