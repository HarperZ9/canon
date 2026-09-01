from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest


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


def test_run_cli_help_uses_injected_stdout_and_lists_parser_surface(capsys: pytest.CaptureFixture[str]) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["--help"], stdout=stdout, stderr=stderr, environ={}) == EX_OK

    help_text = stdout.getvalue()
    assert "--json" in help_text
    assert "--no-color" in help_text
    for command in COMMANDS:
        assert command in help_text
    assert stderr.getvalue() == ""
    assert capsys.readouterr() == ("", "")


def test_unknown_command_returns_usage_without_raising_or_using_global_streams(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["not-a-command"], stdout=stdout, stderr=stderr, environ={}) == EX_USAGE

    assert stdout.getvalue() == ""
    diagnostic = stderr.getvalue()
    assert "usage:" in diagnostic
    assert "invalid choice: 'not-a-command'" in diagnostic
    assert capsys.readouterr() == ("", "")


def test_subcommand_help_uses_injected_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["doctor", "--help"], stdout=stdout, stderr=stderr, environ={}) == EX_OK

    assert "usage: canon doctor" in stdout.getvalue()
    assert stderr.getvalue() == ""
    assert capsys.readouterr() == ("", "")


def test_subcommand_parse_errors_use_injected_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["doctor", "--bad"], stdout=stdout, stderr=stderr, environ={}) == EX_USAGE

    assert stdout.getvalue() == ""
    assert "unrecognized arguments: --bad" in stderr.getvalue()
    assert capsys.readouterr() == ("", "")


def test_placeholder_commands_echo_the_command_name_to_injected_stdout() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    for command in COMMANDS:
        stdout = io.StringIO()
        stderr = io.StringIO()
        assert run_cli([command], stdout=stdout, stderr=stderr, environ={}) == EX_OK
        assert stdout.getvalue() == command + "\n"
        assert stderr.getvalue() == ""


def test_run_cli_does_not_mutate_caller_argv() -> None:
    from canon.cli import run_cli

    argv = ["--json", "--no-color", "doctor"]
    before = list(argv)

    run_cli(argv, stdout=io.StringIO(), stderr=io.StringIO(), environ={})

    assert argv == before


def test_build_parser_returns_argparse_parser_with_placeholder_commands() -> None:
    import argparse

    from canon.cli import build_parser

    parser = build_parser()

    assert isinstance(parser, argparse.ArgumentParser)
    help_text = parser.format_help()
    for command in COMMANDS:
        assert command in help_text


def test_python_module_help_exits_zero_and_lists_commands() -> None:
    env = dict(os.environ)
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src_path

    result = subprocess.run(
        [sys.executable, "-m", "canon", "--help"],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "--json" in result.stdout
    assert "--no-color" in result.stdout
    for command in COMMANDS:
        assert command in result.stdout
    assert result.stderr == ""
