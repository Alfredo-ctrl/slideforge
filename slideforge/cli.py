"""slideforge command line. JSON in, JSON out."""

import argparse
import json
import sys

from . import __version__, build_deck, describe, from_markdown, list_themes


def _exit_error(msg):
    print(json.dumps({"error": msg}), file=sys.stderr)
    raise SystemExit(1)


def _print_result(payload):
    print(json.dumps(payload))


def cmd_create(args):
    try:
        if args.markdown:
            with open(args.markdown, encoding="utf-8") as f:
                result = from_markdown(f.read(), args.output, args.theme)
        else:
            result = build_deck(json.loads(args.structure), args.output, args.theme)
    except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as e:
        _exit_error(str(e))
    _print_result(result)


def cmd_describe(args):
    try:
        result = describe(args.input)
    except (ValueError, OSError) as e:
        _exit_error(str(e))
    _print_result(result)


def cmd_themes(args):
    _print_result(list_themes())


def cmd_mcp(args):
    from .mcp_server import run

    run()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="slideforge", description="Build .pptx decks from JSON or Markdown.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="Build a .pptx deck from JSON structure or a Markdown file.")
    p_create.add_argument("-o", "--output", required=True, help="Output .pptx path")
    p_create.add_argument("--structure", help='JSON structure, e.g. \'{"title": "Talk", "slides": [{"type": "title", "title": "Hi"}]}\'')
    p_create.add_argument("--markdown", help="Markdown file to build the deck from")
    p_create.add_argument("--theme", default="light", help="Theme: light, dark or blue (default light)")
    p_create.set_defaults(func=cmd_create)

    p_desc = sub.add_parser("describe", help="Print deck info as JSON.")
    p_desc.add_argument("-i", "--input", required=True, help="Input .pptx path")
    p_desc.set_defaults(func=cmd_describe)

    p_themes = sub.add_parser("themes", help="List the built-in themes.")
    p_themes.set_defaults(func=cmd_themes)

    p_mcp = sub.add_parser("mcp", help="Start the MCP server on stdio.")
    p_mcp.set_defaults(func=cmd_mcp)

    args = parser.parse_args(argv)
    if args.command == "create" and not args.structure and not args.markdown:
        parser.error("create needs --structure or --markdown")
    args.func(args)


if __name__ == "__main__":
    main()
