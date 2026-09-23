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


def _focus_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--goal", required=True, help="what the project is doing now")
    parser.add_argument("--area", action="append", default=[], help="an active file or area")
    parser.add_argument("--branch", default=None, help="branch (default: read from HEAD)")
    parser.add_argument("--notes", default=None, help="anything the next tool should know")


def _task_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("title", help="the work item")
    parser.add_argument("--status", default="open", help="open, in-progress, blocked, done, dropped")
    parser.add_argument("--detail", default=None, help="more about the work item")


def _set_status_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("record_id", help="the work item id, for example task-3")
    parser.add_argument("status", help="open, in-progress, blocked, done, dropped")
    parser.add_argument("--detail", default=None, help="replace the detail text")


def _decide_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--title", required=True, help="the decision in a few words")
    parser.add_argument("--decision", required=True, help="what was decided")
    parser.add_argument("--context", required=True, help="why it came up")
    parser.add_argument("--status", default="accepted", help="proposed, accepted, superseded, rejected")
    parser.add_argument("--reject", nargs=2, action="append", default=[],
                        metavar=("OPTION", "REASON"), help="an alternative and why it was dropped")


def _constraint_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("statement", help="the constraint or quirk")
    parser.add_argument("--quirk", action="store_true", help="a quirk of the environment")
    parser.add_argument("--reason", default=None, help="why it holds")
    parser.add_argument("--applies-to", action="append", default=[], help="a path it applies to")


_SUBCOMMANDS = (
    ("id", "show this project's identity", _no_args),
    ("list", "list this project's records", _list_args),
    ("promote", "move a record to global scope (logged)", _promote_args),
    ("adopt", "copy another project's records here (logged)", _adopt_args),
    ("focus", "set what the project is doing now", _focus_args),
    ("task", "add a work item", _task_args),
    ("set-status", "change a work item's status", _set_status_args),
    ("decide", "record a decision and the alternatives dropped", _decide_args),
    ("constraint", "record a constraint or an environment quirk", _constraint_args),
)
