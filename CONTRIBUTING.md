# Contributing

slideforge grows by adding slide types or themes. A slide type is one builder in `slideforge/decks.py` plus one entry in `_BUILDERS` and one check in `_check_slide`.

Rules:

- One slide type does one thing. Keep it under 20 lines if you can.
- Never break the JSON contract: `slideforge describe` must keep working, and every slide type must run on any structure.
- Add a test in `tests/test_decks.py` that builds a deck with the new type.
- Run `python -m unittest` before opening a PR.

That's it.
