from __future__ import annotations

import io
import json
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
    "--state-dir",
    ".canon",
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
SECRET_FIXTURE = Path(__file__).parent / "fixtures" / "bootstrap" / "secret_atoms.jsonl"
BOOTSTRAP_FIXTURES = Path(__file__).parent / "fixtures" / "bootstrap"


class _TtyStringIO(io.StringIO):
    def isatty(self) -> bool:
        return True


def _canary() -> str:
    return json.loads(SECRET_FIXTURE.read_text(encoding="utf-8"))["value"]["summary"]


def _copy_bootstrap_inputs(workspace: Path) -> None:
    (workspace / "records.jsonl").write_bytes((BOOTSTRAP_FIXTURES / "records.jsonl").read_bytes())
    (workspace / "atoms.jsonl").write_bytes((BOOTSTRAP_FIXTURES / "atoms.jsonl").read_bytes())
    (workspace / "readiness_pass.json").write_bytes((BOOTSTRAP_FIXTURES / "readiness_pass.json").read_bytes())


def _bootstrap_args(workspace: Path, *extra: str) -> list[str]:
    return ["--workspace", str(workspace), *BOOTSTRAP_ARGS, *extra]


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
    assert diagnostic == "FAIL canon: invalid arguments\n"
    assert "not-a-command" not in diagnostic
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

    assert run_cli(["doctor", "--target", "codex-cli", "--bad"], stdout=stdout, stderr=stderr, environ={}) == EX_USAGE

    assert stdout.getvalue() == ""
    assert stderr.getvalue() == "FAIL canon: invalid arguments\n"
    assert "--bad" not in stderr.getvalue()
    assert capsys.readouterr() == ("", "")


def test_human_parse_errors_suppress_secret_tokens_for_top_level_subcommand_and_color() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    canary = _canary()
    cases = (
        ([canary], io.StringIO(), "FAIL canon: invalid arguments\n"),
        (["doctor", "--target", "codex-cli", f"--{canary}"], io.StringIO(), "FAIL canon: invalid arguments\n"),
        (["doctor", "--target", "codex-cli", f"--{canary}"], _TtyStringIO(), "\x1b[31mFAIL\x1b[0m canon: invalid arguments\n"),
    )

    for argv, stdout, expected_stderr in cases:
        stderr = io.StringIO()
        assert run_cli(argv, stdout=stdout, stderr=stderr, environ={}) == EX_USAGE
        assert stdout.getvalue() == ""
        assert stderr.getvalue() == expected_stderr
        assert canary not in stdout.getvalue() + stderr.getvalue()


def test_json_requested_after_subcommand_keeps_canonical_sanitized_parse_error() -> None:
    from canon.canonical_json import canonical_json_text
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    canary = _canary()
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(
        ["doctor", "--target", "codex-cli", f"--{canary}", "--json"],
        stdout=stdout,
        stderr=stderr,
        environ={},
    )

    payload = json.loads(stdout.getvalue())
    assert exit_code == EX_USAGE
    assert stdout.getvalue() == canonical_json_text(payload)
    assert payload == {"command": "canon", "data": None, "exit_code": 2,
                       "failure_code": "invalid_args", "message": "invalid arguments", "ok": False}
    assert stderr.getvalue() == ""
    assert canary not in stdout.getvalue() + stderr.getvalue()


def test_placeholder_commands_emit_accessible_result_to_injected_stdout() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    active = {"bootstrap", "compile", "preview", "doctor"}
    for command in tuple(command for command in COMMANDS if command not in active):
        stdout = io.StringIO()
        stderr = io.StringIO()
        assert run_cli([command], stdout=stdout, stderr=stderr, environ={}) == EX_OK
        message = "preview ready" if command == "init" else "ready"
        assert stdout.getvalue() == f"PASS {command}: {message}\n"
        assert stderr.getvalue() == ""


def test_bootstrap_command_emits_accessible_result_to_injected_stdout(tmp_path: Path) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    workspace = tmp_path / "work"
    workspace.mkdir()
    stdout = io.StringIO()
    stderr = io.StringIO()

    assert run_cli(["bootstrap", *_bootstrap_args(workspace)], stdout=stdout, stderr=stderr, environ={}) == EX_OK

    assert stdout.getvalue() == "PASS bootstrap: release to work\n"
    assert stderr.getvalue() == ""


def test_run_cli_does_not_mutate_caller_argv() -> None:
    from canon.cli import run_cli

    argv = ["--json", "--no-color", "doctor", "--target", "codex-cli"]
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
        [sys.executable, "-m", "canon", "--json", "doctor", "--target", "codex-cli"],
        cwd=Path.cwd(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == (
        b'{"command":"doctor","data":{"findings":[{"code":"adapter_descriptor_valid",'
        b'"evidence":{"adapter_id":"codex-cli","integration_tier":"native-advisory"},'
        b'"failure_code":"ok","message":"adapter descriptor valid","severity":"info"},'
        b'{"code":"source_state_bound","evidence":{"source_count":0},'
        b'"failure_code":"ok","message":"source state bound","severity":"info"}],'
        b'"offline":false,"source_inputs":[],"source_state_sha256":"sha256:37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",'
        b'"target":{"adapter_id":"codex-cli","bootstrap":{"can_block_before_work":false,'
        b'"mode":"native-context-file"},"display_name":"Codex CLI",'
        b'"integration_tier":"native-advisory","known_unknowns":["Native context can advise the run; '
        b'this foundation descriptor does not assert a universal hard block before work."],'
        b'"target_surfaces":["CANON.md","AGENTS.md"]}},"exit_code":0,'
        b'"failure_code":"ok","message":"doctor diagnostics complete","ok":true}\n'
    )
    assert b"\r" not in result.stdout
    assert result.stderr == b""


def test_bootstrap_json_output_is_canonical_and_contains_state_report(tmp_path: Path) -> None:
    import json

    from canon.canonical_json import canonical_json_text
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    workspace = tmp_path / "work"
    workspace.mkdir()
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(["--json", "bootstrap", *_bootstrap_args(workspace)], stdout=stdout, stderr=stderr, environ={})

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
    assert payload["data"]["readiness_verdict"] == "unknown"
    assert not Path(payload["data"]["witness_path"]).is_absolute()
    assert [event["state"] for event in payload["data"]["events"]][-1] == "release_to_work"


def test_bootstrap_cli_sources_readiness_and_option_order_are_canonical(tmp_path: Path) -> None:
    from canon.canonical_json import canonical_json_text
    from canon.cli import run_cli
    from canon.exit_codes import EX_OK

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_bootstrap_inputs(workspace)
    args = _bootstrap_args(
        workspace,
        "--records",
        "records.jsonl",
        "--atoms",
        "atoms.jsonl",
        "--readiness-response",
        "readiness_pass.json",
        "--started-at",
        "2026-08-30T00:00:00Z",
    )
    first_out, first_err = io.StringIO(), io.StringIO()
    second_out, second_err = io.StringIO(), io.StringIO()

    first = run_cli(["--json", "bootstrap", *args], stdout=first_out, stderr=first_err, environ={})
    second = run_cli(["bootstrap", *args, "--json"], stdout=second_out, stderr=second_err, environ={})
    first_payload = json.loads(first_out.getvalue())
    second_payload = json.loads(second_out.getvalue())

    assert first == second == EX_OK
    assert first_err.getvalue() == second_err.getvalue() == ""
    assert first_out.getvalue() == canonical_json_text(first_payload)
    assert second_out.getvalue() == canonical_json_text(second_payload)
    assert first_payload["data"]["readiness_verdict"] == "pass"
    assert second_payload["data"]["cache_status"] == "hit"
    assert first_payload["data"]["witness_path"] == second_payload["data"]["witness_path"]
    assert "Feature-first. Words with weight." not in first_out.getvalue() + second_out.getvalue()


@pytest.mark.parametrize(
    "extra",
    (
        ("--records", "records.jsonl"),
        ("--atoms", "atoms.jsonl"),
        ("--records", "-", "--atoms", "atoms.jsonl"),
    ),
)
def test_bootstrap_cli_rejects_source_pair_errors_and_stdin(tmp_path: Path, extra: tuple[str, ...]) -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_bootstrap_inputs(workspace)
    stdout = io.StringIO()
    stderr = io.StringIO()

    code = run_cli(["--json", "bootstrap", *_bootstrap_args(workspace, *extra)], stdout=stdout, stderr=stderr, environ={})

    assert code == EX_USAGE
    assert stderr.getvalue() == ""
    payload = json.loads(stdout.getvalue())
    assert payload["failure_code"] == "invalid_args"
    assert "records.jsonl" not in stdout.getvalue()


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


def test_python_module_human_parse_error_suppresses_secret_parser_stderr() -> None:
    env = dict(os.environ)
    src_path = str(Path.cwd() / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else src_path
    canary = _canary()

    result = subprocess.run(
        [sys.executable, "-m", "canon", "doctor", "--target", "codex-cli", f"--{canary}"],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "FAIL canon: invalid arguments\n"
    assert canary not in result.stdout + result.stderr
