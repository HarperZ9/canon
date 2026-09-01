from __future__ import annotations

import io
import json
import os
import stat
from pathlib import Path
from typing import Any

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


def _force_posix(monkeypatch: pytest.MonkeyPatch, cli_init: Any) -> None:
    monkeypatch.setattr(cli_init.os, "name", "posix")
    monkeypatch.setattr(cli_init.os, "O_NOFOLLOW", 0x200, raising=False)
    monkeypatch.setattr(cli_init.os, "O_NONBLOCK", 0x800, raising=False)


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


@pytest.mark.parametrize(
    ("state_dir", "category"),
    [
        ("State/../AgEnTs.Md", "instruction"),
        ("claude.md/state", "instruction"),
        ("SOUL.md", "instruction"),
        ("gemini.MD", "instruction"),
        ("Codex.md", "instruction"),
        (".ChatGPT/state", "app"),
        (".CLAUDE", "app"),
        (".CoDeX/state", "app"),
        (".OpenCode", "app"),
        (".VsCode/state", "ide"),
        (".idea", "ide"),
        (".Cursor/state", "ide"),
        (".WindSurf", "ide"),
        (".GitHub/state", "vcs"),
        (".GIT", "vcs"),
    ],
)
def test_reserved_host_surface_state_components_are_rejected_before_mutation(
    tmp_path: Path,
    state_dir: str,
    category: str,
) -> None:
    del category
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--state-dir", state_dir, "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "unsafe_path"
    assert _rel_tree(workspace) == []


@pytest.mark.parametrize(
    "state_dir",
    [
        "ＡＧＥＮＴＳ.ｍｄ",
        "AＧENTS.md",
        "ＣＬＡＵＤＥ．ｍｄ",
        "CＬAUDE.md",
        "SＯUL.md",
        "ＧＥＭＩＮＩ.ｍｄ",
        "GＥMINI.md",
        "ＣＯＤＥＸ.ｍｄ",
        "CＯDEX.md",
        "．chatgpt",
        ".chatｇpt",
        "．claude",
        "﹒claude",
        "․claude",
        ".clａude",
        "․codex",
        ".coｄex",
        "．vscode",
        ".vsｃode",
        "﹒idea",
        ".ideａ",
        "․cursor",
        ".cuｒsor",
        "．windsurf",
        ".windｓurf",
        "﹒opencode",
        ".openｃode",
        "․github",
        ".gitｈub",
        "．git",
        ".gｉt",
    ],
)
def test_reserved_host_surface_compatibility_aliases_are_rejected_before_mutation(
    tmp_path: Path,
    state_dir: str,
) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, stdout, stderr = _run(["--json", "init", "--workspace", str(workspace), "--state-dir", state_dir, "--apply"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _payload(stdout)["failure_code"] == "unsafe_path"
    assert _rel_tree(workspace) == []


@pytest.mark.parametrize("state_dir", ["．canon", "﹒canon", "․canon", ".ｃanon"])
def test_canon_compatibility_aliases_remain_allowed_when_path_policy_allows(
    tmp_path: Path,
    state_dir: str,
) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, _stdout, stderr = _run(["init", "--workspace", str(workspace), "--state-dir", state_dir, "--apply"])

    assert code == EX_OK
    assert stderr == ""
    assert (workspace / state_dir / "config.json").exists()


def test_default_canon_state_dir_is_not_a_reserved_host_surface(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, _stdout, stderr = _run(["init", "--workspace", str(workspace), "--apply"])

    assert code == EX_OK
    assert stderr == ""
    assert (workspace / ".canon" / "config.json").exists()


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


def test_posix_config_preflight_rejects_fifo_before_open_without_blocking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_init as cli_init

    calls: list[str] = []
    real_stat = cli_init.os.stat
    real_open = cli_init.os.open
    _force_posix(monkeypatch, cli_init)

    def fake_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
        if path == "config.json" and kwargs.get("dir_fd") == 99:
            assert kwargs.get("follow_symlinks") is False
            return os.stat_result((stat.S_IFIFO | 0o600, 0, 0, 0, 0, 0, 0, 0, 0, 0))
        return real_stat(path, *args, **kwargs)

    def forbidden_open(*args: object, **kwargs: object) -> int:
        if args and args[0] == "config.json":
            calls.append("open")
            raise AssertionError("FIFO config preflight must not open")
        return real_open(*args, **kwargs)  # type: ignore[call-overload]

    monkeypatch.setattr(cli_init.os, "stat", fake_stat)
    monkeypatch.setattr(cli_init.os, "open", forbidden_open)

    with pytest.raises(cli_init._InitFailure) as excinfo:
        cli_init._posix_read_config(99)
    assert excinfo.value.code == "conflict"
    assert calls == []


def test_posix_config_open_uses_nonblock_and_rechecks_regular_file_race(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_init as cli_init

    flags_seen: list[int] = []
    closed: list[int] = []
    real_stat = cli_init.os.stat
    real_close = cli_init.os.close
    real_fstat = cli_init.os.fstat
    _force_posix(monkeypatch, cli_init)
    regular = os.stat_result((stat.S_IFREG | 0o600, 0, 0, 0, 0, 0, 3, 0, 0, 0))
    fifo = os.stat_result((stat.S_IFIFO | 0o600, 0, 0, 0, 0, 0, 0, 0, 0, 0))

    def fake_stat(path: object, *args: object, **kwargs: object) -> os.stat_result:
        if path == "config.json" and kwargs.get("dir_fd") == 99:
            assert kwargs.get("follow_symlinks") is False
            return regular
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(cli_init.os, "stat", fake_stat)

    def fake_open(path: object, flags: int, *, dir_fd: int) -> int:
        if path == "config.json" and dir_fd == 99:
            flags_seen.append(flags)
            return 123
        raise AssertionError("unexpected open")

    monkeypatch.setattr(cli_init.os, "open", fake_open)
    monkeypatch.setattr(cli_init.os, "fstat", lambda fd: fifo if fd == 123 else real_fstat(fd))

    def fake_close(fd: int) -> None:
        if fd == 123:
            closed.append(fd)
            return
        real_close(fd)

    monkeypatch.setattr(cli_init.os, "close", fake_close)
    monkeypatch.setattr(
        cli_init.os,
        "pread",
        lambda fd, *a: (_ for _ in ()).throw(AssertionError("must not read FIFO")),
        raising=False,
    )

    with pytest.raises(cli_init._InitFailure) as excinfo:
        cli_init._posix_read_config(99)
    assert excinfo.value.code == "conflict"
    assert flags_seen and flags_seen[0] & cli_init.os.O_NONBLOCK
    assert closed == [123]


@pytest.mark.parametrize("failure", ["write", "fsync", "close"])
def test_posix_temp_create_unlinks_relative_temp_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    import canon.cli_init as cli_init

    closed: list[int] = []
    unlinked: list[tuple[str, int]] = []
    monkeypatch.setattr(cli_init.os, "urandom", lambda size: b"\x01" * size)
    _force_posix(monkeypatch, cli_init)

    def fake_open(path: object, flags: int, mode: int, *, dir_fd: int) -> int:
        assert path == ".config.json.0101010101010101.tmp"
        assert dir_fd == 99
        return 123

    monkeypatch.setattr(cli_init.os, "open", fake_open)

    def fake_write_all(fd: int, data: bytes) -> None:
        assert fd == 123
        assert data == b"body\n"
        if failure == "write":
            raise OSError("synthetic write failure")

    def fake_fsync(fd: int) -> None:
        assert fd == 123
        if failure == "fsync":
            raise OSError("synthetic fsync failure")

    def fake_close(fd: int) -> None:
        assert fd == 123
        closed.append(fd)
        if failure == "close":
            raise OSError("synthetic close failure")

    def fake_unlink(name: str, *, dir_fd: int) -> None:
        unlinked.append((name, dir_fd))

    monkeypatch.setattr(cli_init, "_write_all", fake_write_all)
    monkeypatch.setattr(cli_init.os, "fsync", fake_fsync)
    monkeypatch.setattr(cli_init.os, "close", fake_close)
    monkeypatch.setattr(cli_init.os, "unlink", fake_unlink)

    with pytest.raises(OSError):
        cli_init._create_posix_temp(99, b"body\n")

    assert closed == [123]
    assert unlinked == [(".config.json.0101010101010101.tmp", 99)]


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
