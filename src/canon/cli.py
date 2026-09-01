"""Internal canon command-line entrypoint."""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping
from typing import TextIO

from .cli_format import color_enabled, make_result, write_result
from .exit_codes import EX_OK, EX_USAGE

COMMANDS = (
    "init",
    "compile",
    "preview",
    "doctor",
    "export",
    "rescue",
    "import-review",
    "undo",
    "bootstrap",
)


class _ParserExit(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


class _CanonArgumentParser(argparse.ArgumentParser):
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
        target = self._stream_for(file)
        target.write(message)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if message:
            self._print_message(message, sys.stderr)
        raise _ParserExit(status)

    def print_help(self, file: TextIO | None = None) -> None:
        super().print_help(file or self._canon_stdout)

    def _stream_for(self, file: TextIO | None) -> TextIO:
        if file is None or file is sys.stderr or file is sys.__stderr__:
            return self._canon_stderr
        if file is sys.stdout or file is sys.__stdout__:
            return self._canon_stdout
        return file


def build_parser() -> argparse.ArgumentParser:
    """Build the stable placeholder parser for canon commands."""
    return _build_parser()


def run_cli(
    argv: list[str],
    *,
    stdin: TextIO | None = None,
    stdout: TextIO,
    stderr: TextIO,
    environ: Mapping[str, str],
) -> int:
    """Run canon's CLI with caller-owned streams and environment."""
    del stdin
    tokens = _argv_copy(argv, stderr)
    if tokens is None:
        return EX_USAGE

    parser = _build_parser(stdout=stdout, stderr=stderr)
    try:
        parsed = parser.parse_args(tokens)
    except _ParserExit as error:
        return error.status

    result = make_result(ok=True, command=parsed.command, failure_code="ok", message="ready")
    return write_result(
        result,
        stdout=stdout,
        stderr=stderr,
        json_output=parsed.json_output,
        color=color_enabled(environ=environ, no_color=parsed.no_color, is_tty=_is_tty(stdout)),
    )


def main(argv: list[str] | None = None) -> int:
    """Run canon from process-global streams."""
    tokens = list(sys.argv[1:] if argv is None else argv)
    return run_cli(tokens, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, environ=os.environ)


def _build_parser(stdout: TextIO | None = None, stderr: TextIO | None = None) -> _CanonArgumentParser:
    parser = _CanonArgumentParser(
        prog="canon",
        description="Canon bootstrap command surface.",
        stdout=stdout,
        stderr=stderr,
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="emit machine-readable JSON")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    subparsers = parser.add_subparsers(dest="command", metavar="command", required=True, title="commands")
    for command in COMMANDS:
        subparser = subparsers.add_parser(command, help=f"{command} placeholder")
        subparser._canon_stdout = parser._canon_stdout
        subparser._canon_stderr = parser._canon_stderr
    return parser


def _argv_copy(argv: list[str], stderr: TextIO) -> list[str] | None:
    if not isinstance(argv, list):
        stderr.write("canon: argv must be list[str]\n")
        return None
    if any(not isinstance(item, str) for item in argv):
        stderr.write("canon: argv entries must be str\n")
        return None
    return list(argv)


def _is_tty(stream: TextIO) -> bool:
    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except OSError:
        return False


__all__ = ["COMMANDS", "build_parser", "run_cli", "main"]
