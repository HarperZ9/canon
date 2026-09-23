"""Argument parsing for `canon workspace ...`, `canon handoff` and `canon switch`.

Kept apart from cli_parser.py so the older command surface stays as it was.
Every workspace subcommand shares three options: the workspace directory, the
store root, and a remote override for the project identity.
"""
from __future__ import annotations

import argparse


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=".", help="a directory inside the project")
    parser.add_argument("--store", default=None,
                        help="store root (default: CANON_STORE or ~/.canon/store)")
    parser.add_argument("--remote", default=None,
                        help="use this remote URL for the project identity")


def _inherit(child: argparse.ArgumentParser, parent: argparse.ArgumentParser) -> None:
    child._canon_stdout = parent._canon_stdout  # type: ignore[attr-defined]
    child._canon_stderr = parent._canon_stderr  # type: ignore[attr-defined]


def add_workspace_args(parser: argparse.ArgumentParser) -> None:
    subs = parser.add_subparsers(dest="ws_command", metavar="workspace-command",
                                 required=True)
    for name, help_text, adder in _SUBCOMMANDS:
        child = subs.add_parser(name, help=help_text)
        _inherit(child, parser)
        add_common(child)
        adder(child)


def _no_args(parser: argparse.ArgumentParser) -> None:
    return None


def _list_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--proposed", action="store_true", help="list proposed records")
    parser.add_argument("--kind", default=None, help="only this record kind")


def _promote_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("record_id", help="the accepted record to promote")
    parser.add_argument("--reason", required=True, help="why it applies to every project")


def _adopt_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--from", dest="from_project", required=True,
                        help="the project id whose accepted records to copy here")
    parser.add_argument("--reason", required=True, help="why these records belong here")


_SUBCOMMANDS = (
    ("id", "show this project's identity", _no_args),
    ("list", "list this project's records", _list_args),
    ("promote", "move a record to global scope (logged)", _promote_args),
    ("adopt", "copy another project's records here (logged)", _adopt_args),
)
