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
BOOTSTRAP_ARGS = (
    "--workspace",
    "C:/work/canon",
    "--state-dir",
    "C:/work/canon/.canon",
    "--target",
    "chatgpt-app",
    "--tier",
    "guided",
    "--profile",
    "handoff",
    "--offline",
    "--run-id",
    "run-cli",
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


def test_placeholder_commands_emit_accessible_result_to_injected_stdout() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    active = {"bootstrap", "compile", "preview"}
    for command in tuple(command for command in COMMANDS if command not in active):
        stdout = io.StringIO()
        stderr = io.StringIO()
        assert run_cli([command], stdout=stdout, stderr=stderr, environ={}) == EX_OK
        message = "preview ready" if command == "init" else "ready"
        assert stdout.getvalue() == f"PASS {command}: {message}\n"
        assert stderr.getvalue() == ""


def test_bootstrap_command_emits_accessible_result_to_injected_stdout() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["bootstrap", *BOOTSTRAP_ARGS], stdout=stdout, stderr=stderr, environ={}) == EX_OK

    assert stdout.getvalue() == "PASS bootstrap: release to work\n"
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


def test_python_module_json_stdout_is_utf8_bytes_with_lf_only() -> None:
    env = dict(os.environ)
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src_path

    result = subprocess.run(
        [sys.executable, "-m", "canon", "--json", "doctor"],
        cwd=Path.cwd(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == (
        b'{"command":"doctor","data":null,"exit_code":0,'
        b'"failure_code":"ok","message":"ready","ok":true}\n'
    )
    assert b"\r" not in result.stdout
    assert result.stderr == b""


def test_bootstrap_json_output_is_canonical_and_contains_state_report() -> None:
    import json

    from canon.canonical_json import canonical_json_text
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(["--json", "bootstrap", *BOOTSTRAP_ARGS], stdout=stdout, stderr=stderr, environ={})

    assert exit_code == EX_OK
    assert stderr.getvalue() == ""
    assert stdout.getvalue().endswith("\n")
    assert "\r" not in stdout.getvalue()
    payload = json.loads(stdout.getvalue())
    assert stdout.getvalue() == canonical_json_text(payload)
    assert payload["command"] == "bootstrap"
    assert payload["message"] == "release to work"
    assert payload["data"]["adapter_id"] == "chatgpt-app"
    assert payload["data"]["authoritative_tier"] == "guided"
    assert payload["data"]["requested_tier"] == "guided"
    assert [event["state"] for event in payload["data"]["events"]][-1] == "release_to_work"


def test_python_module_json_parse_error_suppresses_parser_stderr() -> None:
    env = dict(os.environ)
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src_path

    result = subprocess.run(
        [sys.executable, "-m", "canon", "--json", "not-a-command"],
        cwd=Path.cwd(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == (
        b'{"command":"canon","data":null,"exit_code":2,'
        b'"failure_code":"invalid_args","message":"invalid arguments","ok":false}\n'
    )
    assert b"not-a-command" not in result.stdout
    assert result.stderr == b""
