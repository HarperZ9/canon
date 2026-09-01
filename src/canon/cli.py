"""Internal canon command-line entrypoint."""
from __future__ import annotations

import argparse
import io
import os
import sys
from collections.abc import Mapping
from typing import TextIO

from .bootstrap import BootstrapConfig, run_bootstrap
from .cli_format import color_enabled, make_result, write_result
from .cli_init import run_init
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
    tokens = _argv_copy(argv, stderr)
    if tokens is None:
        return EX_USAGE
    tokens = _normalize_global_options(tokens)

    json_requested = _json_requested(tokens)
    parse_color = color_enabled(environ=environ, no_color="--no-color" in tokens, is_tty=_is_tty(stdout))
    parser_stderr = io.StringIO()
    parser = _build_parser(stdout=stdout, stderr=parser_stderr)
    try:
        parsed = parser.parse_args(tokens)
    except _ParserExit as error:
        if error.status == EX_OK:
            return error.status
        return _parse_error(stdout, stderr, json_requested=json_requested, color=parse_color)

    return _run_parsed(parsed, stdin=stdin, stdout=stdout, stderr=stderr, environ=environ)


def main(argv: list[str] | None = None) -> int:
    """Run canon from process-global streams."""
    tokens = list(sys.argv[1:] if argv is None else argv)
    return run_cli(tokens, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, environ=os.environ)


def _run_parsed(
    parsed: argparse.Namespace,
    *,
    stdin: TextIO | None,
    stdout: TextIO,
    stderr: TextIO,
    environ: Mapping[str, str],
) -> int:
    color = color_enabled(environ=environ, no_color=parsed.no_color, is_tty=_is_tty(stdout))
    if parsed.command in ("compile", "preview"):
        from .cli_compile import run_compile_command

        return run_compile_command(parsed, stdin=stdin, stdout=stdout, stderr=stderr, color=color)
    if parsed.command == "doctor":
        from .doctor import run_doctor_command

        return run_doctor_command(parsed, stdin=stdin, stdout=stdout, stderr=stderr, color=color)
    return write_result(
        _command_result(parsed),
        stdout=stdout,
        stderr=stderr,
        json_output=parsed.json_output,
        color=color,
    )


def _command_result(parsed: argparse.Namespace):
    if parsed.command == "init":
        return _init_result(parsed)
    if parsed.command == "bootstrap":
        return _bootstrap_result(parsed)
    return make_result(ok=True, command=parsed.command, failure_code="ok", message="ready")


def _init_result(parsed: argparse.Namespace):
    report = run_init(workspace=parsed.workspace, state_dir=parsed.state_dir, apply=parsed.apply)
    return make_result(
        ok=report.ok,
        command="init",
        failure_code=report.failure_code,
        message=report.message,
        data=report.data,
    )


def _bootstrap_result(parsed: argparse.Namespace):
    report = run_bootstrap(
        BootstrapConfig(
            workspace=parsed.workspace,
            state_dir=parsed.state_dir,
            target=parsed.target,
            tier=parsed.tier,
            profile=parsed.profile,
            offline=parsed.offline,
            run_id=parsed.run_id,
        )
    )
    return make_result(
        ok=report.ok,
        command="bootstrap",
        failure_code=report.failure_code,
        message=report.message,
        data=report.to_result_data(),
    )


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
        if command == "init":
            _add_init_args(subparser)
        elif command == "bootstrap":
            _add_bootstrap_args(subparser)
        elif command in ("compile", "preview"):
            _add_compile_args(subparser, include_out=command == "compile")
        elif command == "doctor":
            _add_doctor_args(subparser)
    return parser


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


def _argv_copy(argv: list[str], stderr: TextIO) -> list[str] | None:
    if type(argv) is not list:
        stderr.write("canon: argv must be list[str]\n")
        return None
    if any(type(item) is not str for item in argv):
        stderr.write("canon: argv entries must be str\n")
        return None
    return list(argv)


def _normalize_global_options(tokens: list[str]) -> list[str]:
    global_options = [item for item in tokens if item in ("--json", "--no-color")]
    rest = [item for item in tokens if item not in ("--json", "--no-color")]
    return global_options + rest


def _is_tty(stream: TextIO) -> bool:
    isatty = getattr(stream, "isatty", None)
    if not callable(isatty):
        return False
    try:
        return bool(isatty())
    except OSError:
        return False


def _json_requested(tokens: list[str]) -> bool:
    return "--json" in tokens


def _parse_error(stdout: TextIO, stderr: TextIO, *, json_requested: bool, color: bool) -> int:
    result = make_result(ok=False, command="canon", failure_code="invalid_args", message="invalid arguments")
    return write_result(result, stdout=stdout, stderr=stderr, json_output=json_requested, color=color)


__all__ = ["COMMANDS", "build_parser", "run_cli", "main"]
