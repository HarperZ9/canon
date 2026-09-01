from __future__ import annotations

import io
import re

import pytest

from canon.exit_codes import EX_OK

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


class TtyStringIO(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_human_result_has_visible_pass_and_fail_labels_without_color() -> None:
    from canon.cli_format import make_result, write_result

    pass_out = io.StringIO()
    pass_err = io.StringIO()
    fail_out = io.StringIO()
    fail_err = io.StringIO()

    write_result(
        make_result(ok=True, command="doctor", failure_code="ok", message="ready"),
        stdout=pass_out,
        stderr=pass_err,
        json_output=False,
        color=False,
    )
    write_result(
        make_result(ok=False, command="doctor", failure_code="conflict", message="blocked"),
        stdout=fail_out,
        stderr=fail_err,
        json_output=False,
        color=False,
    )

    assert pass_out.getvalue() == "PASS doctor: ready\n"
    assert pass_err.getvalue() == ""
    assert fail_out.getvalue() == ""
    assert fail_err.getvalue() == "FAIL doctor: blocked\n"
    assert ANSI_RE.search(pass_out.getvalue()) is None
    assert ANSI_RE.search(fail_err.getvalue()) is None


def test_human_color_supplements_visible_label_and_resets_cleanly() -> None:
    from canon.cli_format import make_result, write_result

    stdout = io.StringIO()

    write_result(
        make_result(ok=True, command="doctor", failure_code="ok", message="ready"),
        stdout=stdout,
        stderr=io.StringIO(),
        json_output=False,
        color=True,
    )

    text = stdout.getvalue()
    assert "PASS" in text
    assert "doctor" in text
    assert "ready" in text
    assert "\x1b[32mPASS\x1b[0m" in text
    assert text.count("\x1b[0m") == 1
    assert text.endswith("\n")


@pytest.mark.parametrize(
    ("environ", "no_color", "is_tty", "expected"),
    (
        ({}, False, True, True),
        ({"NO_COLOR": ""}, False, True, False),
        ({"NO_COLOR": "1"}, False, True, False),
        ({}, True, True, False),
        ({}, False, False, False),
    ),
)
def test_color_enabled_uses_tty_flag_no_color_option_and_no_color_presence(
    environ: dict[str, str],
    no_color: bool,
    is_tty: bool,
    expected: bool,
) -> None:
    from canon.cli_format import color_enabled

    assert color_enabled(environ=environ, no_color=no_color, is_tty=is_tty) is expected


def test_cli_json_routes_placeholder_to_canonical_envelope() -> None:
    from canon.cli import run_cli

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(["--json", "doctor"], stdout=stdout, stderr=stderr, environ={})

    assert exit_code == EX_OK
    assert stdout.getvalue() == (
        '{"command":"doctor","data":null,"exit_code":0,'
        '"failure_code":"ok","message":"ready","ok":true}\n'
    )
    assert stderr.getvalue() == ""


def test_cli_json_parse_error_suppresses_human_error_and_uses_generic_invalid_args() -> None:
    from canon.cli import run_cli
    from canon.exit_codes import EX_USAGE

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(["--json", "not-a-command"], stdout=stdout, stderr=stderr, environ={})

    assert exit_code == EX_USAGE
    assert stdout.getvalue() == (
        '{"command":"canon","data":null,"exit_code":2,'
        '"failure_code":"invalid_args","message":"invalid arguments","ok":false}\n'
    )
    assert stderr.getvalue() == ""
    assert "not-a-command" not in stdout.getvalue()


def test_cli_json_help_still_returns_useful_help_text() -> None:
    from canon.cli import run_cli

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_cli(["--json", "--help"], stdout=stdout, stderr=stderr, environ={})

    assert exit_code == EX_OK
    assert "usage: canon" in stdout.getvalue()
    assert "--json" in stdout.getvalue()
    assert stderr.getvalue() == ""


def test_cli_no_color_no_color_env_and_non_tty_output_keep_visible_labels_only() -> None:
    from canon.cli import run_cli

    no_color_stdout = TtyStringIO()
    no_color_env_stdout = TtyStringIO()
    non_tty_stdout = io.StringIO()

    assert run_cli(["--no-color", "doctor"], stdout=no_color_stdout, stderr=io.StringIO(), environ={}) == EX_OK
    assert run_cli(["doctor"], stdout=no_color_env_stdout, stderr=io.StringIO(), environ={"NO_COLOR": ""}) == EX_OK
    assert run_cli(["doctor"], stdout=non_tty_stdout, stderr=io.StringIO(), environ={}) == EX_OK

    assert no_color_stdout.getvalue() == "PASS doctor: ready\n"
    assert no_color_env_stdout.getvalue() == "PASS doctor: ready\n"
    assert non_tty_stdout.getvalue() == "PASS doctor: ready\n"
    assert ANSI_RE.search(no_color_stdout.getvalue()) is None
    assert ANSI_RE.search(no_color_env_stdout.getvalue()) is None
    assert ANSI_RE.search(non_tty_stdout.getvalue()) is None
