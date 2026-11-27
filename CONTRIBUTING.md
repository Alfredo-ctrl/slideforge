# Contributing

slideforge grows by adding slide types. A slide type is one builder in `slideforge/decks.py` plus one row in the README table: type, what it needs.

Rules:

- One slide type does one thing. Keep the builder small and reuse the helpers (`_accent_bar`, `_slide_title`).
- Never break the JSON contract: `slideforge describe` must keep working on any .pptx.
- A new feature touches code, test, README, MCP description and example in the same commit.
- Add a test in `tests/test_decks.py` for anything new.
- Run `python -m unittest discover -s tests` before opening a PR.
- One commit per change, with a message that says why, not just what.
