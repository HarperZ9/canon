from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text
from canon.exit_codes import EX_CONFLICT, EX_IO, EX_OK, EX_SECURITY


CONFIG = {
    "canon_schema": "canon.init-state/v1",
    "workspace": {"relative_from_state_dir": ".."},
}


def _run(argv: list[str]) -> tuple[int, str, str]:
    from canon.cli import run_cli

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_cli(argv, stdout=stdout, stderr=stderr, environ={})
    return code, stdout.getvalue(), stderr.getvalue()


def _payload(stdout: str) -> dict[str, object]:
    data = json.loads(stdout)
    assert stdout == canonical_json_text(data)
    assert "\r" not in stdout
    return data


def _rel_tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _swap_dir_to_symlink(directory: Path, outside: Path, displaced: Path) -> bool:
    try:
        directory.rename(displaced)
        try:
            directory.symlink_to(outside, target_is_directory=True)
        except OSError:
            displaced.rename(directory)
            pytest.skip("current platform or privileges do not allow directory symlinks")
        return True
    except OSError:
        return False


def test_preview_reports_default_state_plan_without_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_bytes(b"host instructions\r\n")
    (workspace / "CLAUDE.md").write_bytes(b"claude instructions\n")

    code, stdout, stderr = _run(["--json", "--no-color", "init", "--workspace", str(workspace)])

    assert code == EX_OK
    assert stderr == ""
    payload = _payload(stdout)
    assert payload["message"] == "preview ready"
    assert payload["data"] == {
        "mode": "preview",
        "state_dir": ".canon",
        "would_create": [".canon/cache", ".canon/witnesses", ".canon/undo", ".canon/config.json"],
    }
    assert not (workspace / ".canon").exists()
    assert (workspace / "AGENTS.md").read_bytes() == b"host instructions\r\n"
    assert (workspace / "CLAUDE.md").read_bytes() == b"claude instructions\n"


def test_apply_creates_only_canon_state_tree_and_config(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / "AGENTS.md").write_text("host\n", encoding="utf-8")

    code, stdout, stderr = _run(["init", "--workspace", str(workspace), "--apply"])

    assert code == EX_OK
    assert stdout == "PASS init: initialized canon state\n"
    assert stderr == ""
    assert _rel_tree(workspace) == [
        ".canon",
        ".canon/cache",
        ".canon/config.json",
        ".canon/undo",
        ".canon/witnesses",
        "AGENTS.md",
    ]
    assert (workspace / ".canon" / "config.json").read_bytes() == canonical_json_text(CONFIG).encode("utf-8")
    assert not (workspace / "CLAUDE.md").exists()
    assert not (workspace / ".chatgpt").exists()
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "host\n"


def test_custom_state_dir_is_workspace_relative_and_confined(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / "state").mkdir()

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--state-dir", "state/canon"])

    assert code == EX_OK
    assert stderr == ""
    assert _payload(stdout)["data"] == {
        "mode": "preview",
        "state_dir": "state/canon",
        "would_create": [
            "state/canon/cache",
            "state/canon/witnesses",
            "state/canon/undo",
            "state/canon/config.json",
        ],
    }
    code, _stdout, stderr = _run(["init", "--workspace", str(workspace), "--state-dir", "state/canon", "--apply"])
    assert code == EX_OK
    assert stderr == ""
    assert (workspace / "state" / "canon" / "config.json").read_bytes() == canonical_json_text(
        {"canon_schema": "canon.init-state/v1", "workspace": {"relative_from_state_dir": "../.."}},
    ).encode("utf-8")


@pytest.mark.parametrize(
    "state_dir",
    ["..", "../outside/leaked-secret-token", ".ssh/canon", "state:ads", "."],
)
def test_unsafe_state_paths_return_sanitized_security_code_before_mutation(
    tmp_path: Path,
    state_dir: str,
) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--state-dir", state_dir, "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    payload = _payload(stdout)
    assert payload["failure_code"] == "unsafe_path"
    assert payload["message"] == "unsafe init path"
    assert "leaked-secret-token" not in stdout
    assert not (workspace / ".canon").exists()


def test_reparse_workspace_or_state_dir_is_rejected_before_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    state_link = workspace / ".canon"
    try:
        state_link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "unsafe_path"
    assert list(outside.iterdir()) == []


def test_conflicting_config_is_not_overwritten_or_advanced(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    config = workspace / ".canon" / "config.json"
    config.parent.mkdir(parents=True)
    config.write_bytes(b'{"owner":"user"}\n')

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert code == EX_CONFLICT
    assert stderr == ""
    payload = _payload(stdout)
    assert payload["failure_code"] == "conflict"
    assert payload["message"] == "canon state conflict"
    assert config.read_bytes() == b'{"owner":"user"}\n'
    assert _rel_tree(workspace) == [".canon", ".canon/config.json"]


def test_identical_config_and_repeated_apply_are_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    first = _run(["--json", "init", "--workspace", str(workspace), "--apply"])
    second = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert first[0] == second[0] == EX_OK
    assert _payload(first[1]) == _payload(second[1])
    assert first[2] == second[2] == ""
    assert (workspace / ".canon" / "config.json").read_bytes() == canonical_json_text(CONFIG).encode("utf-8")
    assert _rel_tree(workspace) == [".canon", ".canon/cache", ".canon/config.json", ".canon/undo", ".canon/witnesses"]


def test_preexisting_child_must_be_real_directory(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    cache = workspace / ".canon" / "cache"
    cache.parent.mkdir(parents=True)
    cache.write_text("not a directory", encoding="utf-8")

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "unsafe_path"
    assert not (workspace / ".canon" / "config.json").exists()


def test_workspace_swap_before_pinning_fails_without_outside_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    anchor = tmp_path / "anchor"
    workspace = anchor / "work"
    outside_anchor = tmp_path / "outside-anchor"
    outside_workspace = outside_anchor / "work"
    displaced = tmp_path / "displaced-anchor"
    workspace.mkdir(parents=True)
    outside_workspace.mkdir(parents=True)
    path_type = type(workspace)
    real_lstat = path_type.lstat
    attempted = False

    def swap_after_snapshot(path: Path) -> object:
        nonlocal attempted
        info = real_lstat(path)
        if os.path.normcase(os.fspath(path)) == os.path.normcase(os.fspath(workspace)) and not attempted:
            attempted = True
            if not _swap_dir_to_symlink(anchor, outside_anchor, displaced):
                pytest.skip("current platform blocks directory swap race setup")
        return info

    monkeypatch.setattr(path_type, "lstat", swap_after_snapshot)
    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "unsafe_path"
    assert attempted
    assert not (outside_workspace / ".canon").exists()


def test_io_failure_reports_sanitized_io_error_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_init as cli_init

    workspace = tmp_path / "work"
    workspace.mkdir()

    if os.name == "nt":
        real_rename = cli_init.os.rename

        def fail_publish(src: object, dst: object) -> None:
            if Path(dst).name == "config.json":
                raise OSError("leaked-secret-token")
            real_rename(src, dst)

        monkeypatch.setattr(cli_init.os, "rename", fail_publish)
    else:
        real_link = cli_init.os.link

        def fail_publish(src: object, dst: object, **kwargs: object) -> None:
            if dst == "config.json":
                raise OSError("leaked-secret-token")
            real_link(src, dst, **kwargs)

        monkeypatch.setattr(cli_init.os, "link", fail_publish)
    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--apply"])

    assert code == EX_IO
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "io_error"
    assert "leaked-secret-token" not in stdout
    assert list((workspace / ".canon").glob("*.tmp")) == []
