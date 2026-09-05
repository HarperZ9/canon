"""cli.py -- the `canon` command.

Two verbs, both read-only. `canon mcp` runs the stdio MCP server, which is how a
harness reaches this repository. `canon check` runs the aggregate check over the
authored block set and exits non-zero when a wired leg fails, which is how a
build keys on it.

Nothing here writes a surface or a vault. Reconcile raises human gates and
rewrites instruction files, so it stays a library call a caller wires
deliberately rather than a verb a script can reach by accident.
"""
from __future__ import annotations

import argparse
import json
import sys


def _cmd_mcp(_args) -> int:
    from canon.local_mcp import serve
    return serve()


def _cmd_check(args) -> int:
    """Print the aggregate check as JSON and return its exit code.

    The MCP tool and this verb call the same `_check`, so a build gate and a
    harness question cannot disagree about what canon believes.
    """
    from canon.local_mcp import _check
    report = _check()
    json.dump(report, sys.stdout, indent=2)
    print()
    return 0 if report["ok"] else 1


def _cmd_blocks(_args) -> int:
    from canon.local_mcp import _blocks
    json.dump(_blocks({}), sys.stdout, indent=2)
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="canon", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("mcp", help="run the stdio MCP server").set_defaults(fn=_cmd_mcp)
    sub.add_parser("check", help="aggregate check over the authored blocks"
                   ).set_defaults(fn=_cmd_check)
    sub.add_parser("blocks", help="list the authored block set").set_defaults(fn=_cmd_blocks)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
