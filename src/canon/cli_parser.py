from __future__ import annotations

import argparse
import sys
from typing import TextIO


class ParserExit(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class CanonArgumentParser(argparse.ArgumentParser):
    def __init__(
        self,
        *args: object,
        stdout: TextIO | None = None,
        stderr: TextIO | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._canon_stdout = stdout if stdout is not None else sys.stdout
        self._canon_stderr = stderr if stderr is not None else sys.stderr

    def _print_message(self, message: str, file: TextIO | None = None) -> None:
        if not message:
            return
        self._stream_for(file).write(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise ParserExit(status)

    def print_help(self, file: TextIO | None = None) -> None:
        super().print_help(file or self._canon_stdout)

    def _stream_for(self, file: TextIO | None) -> TextIO:
        if file is None or file is sys.stderr or file is sys.__stderr__:
            return self._canon_stderr
        if file is sys.stdout or file is sys.__stdout__:
            return self._canon_stdout
        return file


def build_canon_parser(
    commands: tuple[str, ...],
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> CanonArgumentParser:
    parser = CanonArgumentParser(
        prog="canon", description="Canon bootstrap command surface.",
        stdout=stdout, stderr=stderr,
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable JSON")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    subparsers = parser.add_subparsers(dest="command", metavar="command", required=True, title="commands")
    for command in commands:
        subparser = subparsers.add_parser(command, help=f"{command} placeholder")
        _inherit_streams(subparser, parser)
        _add_command_args(command, subparser)
    return parser


def _inherit_streams(subparser: argparse.ArgumentParser, parser: CanonArgumentParser) -> None:
    subparser._canon_stdout = parser._canon_stdout  # type: ignore[attr-defined]
    subparser._canon_stderr = parser._canon_stderr  # type: ignore[attr-defined]


def _add_command_args(command: str, parser: argparse.ArgumentParser) -> None:
    if command == "init":
        _add_init_args(parser)
    elif command == "bootstrap":
        _add_bootstrap_args(parser)
    elif command in ("compile", "preview"):
        _add_compile_args(parser, include_out=command == "compile")
    elif command == "doctor":
        _add_doctor_args(parser)
    elif command == "export":
        _add_export_args(parser)
    elif command == "undo":
        _add_undo_args(parser)


def _add_init_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=".", help="workspace path")
    parser.add_argument("--state-dir", default=None, help="state directory path")
    parser.add_argument("--apply", action="store_true", help="create Canon-owned local state")


def _add_bootstrap_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=".", help="workspace path")
    parser.add_argument("--state-dir", default=".canon", help="state directory path")
    parser.add_argument("--target", required=True, help="adapter target id")
    parser.add_argument("--tier", required=True, help="requested integration tier")
    parser.add_argument("--profile", default="handoff", help="capsule profile")
    parser.add_argument("--offline", action="store_true", help="avoid later online work")
    parser.add_argument("--run-id", required=True, help="bootstrap run id")
    parser.add_argument("--records", default=None, help="Record JSONL input path")
    parser.add_argument("--atoms", default=None, help="CanonAtom JSONL input path")
    parser.add_argument("--readiness-response", default=None, help="readiness response JSON path")
    parser.add_argument("--started-at", default="not-recorded", help="explicit witness start time")


def _add_compile_args(parser: argparse.ArgumentParser, *, include_out: bool) -> None:
    parser.add_argument("--workspace", default=".", help="workspace path")
    parser.add_argument("--records", required=True, help="Record JSONL input path or '-'")
    parser.add_argument("--atoms", required=True, help="CanonAtom JSONL input path or '-'")
    parser.add_argument("--target", required=True, help="adapter target id")
    parser.add_argument("--profile", default="handoff", help="capsule profile")
    parser.add_argument("--offline", action="store_true", help="avoid later online work")
    if include_out:
        parser.add_argument("--out", default=None, help="output directory below workspace")


def _add_doctor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=".", help="workspace path")
    parser.add_argument("--target", required=True, help="adapter target id")
    parser.add_argument("--records", default=None, help="Record JSONL input path or '-'")
    parser.add_argument("--atoms", default=None, help="CanonAtom JSONL input path or '-'")
    parser.add_argument("--offline", action="store_true", help="record reachability as unknown")
    parser.add_argument("--expected-source-state", default=None, help="expected source state sha256")


def _add_export_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--workspace", default=".", help="workspace path")
    parser.add_argument("--records", required=True, help="Record JSONL input path or '-'")
    parser.add_argument("--atoms", required=True, help="CanonAtom JSONL input path or '-'")
    parser.add_argument("--target", required=True, help="adapter target id")
    parser.add_argument("--profile", default="handoff", help="capsule profile")
    parser.add_argument("--offline", action="store_true", help="avoid later online work")
    parser.add_argument("--format", default=None, help="export format")
    parser.add_argument("--out", default=None, help="output path below workspace")
    parser.add_argument("--apply-region", default=None, help="existing host file region to replace")


def _add_undo_args(parser: argparse.ArgumentParser) -> None:
    undo_subparsers = parser.add_subparsers(dest="undo_command", metavar="undo-command", required=True)
    _add_undo_list_args(undo_subparsers.add_parser("list", help="list local undo receipts"), parser)
    _add_undo_apply_args(undo_subparsers.add_parser("apply", help="apply a local undo receipt"), parser)


def _add_undo_list_args(list_parser: argparse.ArgumentParser, parent: argparse.ArgumentParser) -> None:
    list_parser._canon_stdout = parent._canon_stdout  # type: ignore[attr-defined]
    list_parser._canon_stderr = parent._canon_stderr  # type: ignore[attr-defined]
    list_parser.add_argument("--workspace", default=".", help="workspace path")


def _add_undo_apply_args(apply_parser: argparse.ArgumentParser, parent: argparse.ArgumentParser) -> None:
    apply_parser._canon_stdout = parent._canon_stdout  # type: ignore[attr-defined]
    apply_parser._canon_stderr = parent._canon_stderr  # type: ignore[attr-defined]
    apply_parser.add_argument("receipt_id", help="undo receipt id")
    apply_parser.add_argument("--workspace", default=".", help="workspace path")


__all__ = ["CanonArgumentParser", "ParserExit", "build_canon_parser"]
