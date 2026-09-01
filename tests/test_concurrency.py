from __future__ import annotations

import errno
import os
import socket
from pathlib import Path

import pytest

from canon.concurrency import (
    LockError,
    RunLock,
    acquire_run_lock,
    guarded_commit,
    release_run_lock,
)
from canon.source_state import SourceStateError, SourceStateItem, source_state_sha256


def _sha(hex_char: str) -> str:
    return "sha256:" + hex_char * 64


def test_run_lock_conflicts_until_released(tmp_path: Path) -> None:
    first = acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    try:
        with pytest.raises(LockError, match="lock-held"):
            acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    finally:
        release_run_lock(first)

    second = acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    release_run_lock(second)


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../x",
        "a/b",
        "a\\b",
        "a:b",
        "a\nb",
        "CON",
        "a.",
        "caf\u00e9",
        "cafe\u0301",
        123,
    ],
)
def test_bad_lock_names_are_rejected(tmp_path: Path, name: object) -> None:
    with pytest.raises(LockError, match="invalid-lock-name"):
        acquire_run_lock(tmp_path, name)  # type: ignore[arg-type]


def test_lock_root_must_be_existing_directory(tmp_path: Path) -> None:
    file_root = tmp_path / "file-root"
    file_root.write_text("not a directory", encoding="utf-8")

    with pytest.raises(LockError, match="invalid-lock-root"):
        acquire_run_lock(file_root, "workspace")
    with pytest.raises(LockError, match="invalid-lock-root"):
        acquire_run_lock(tmp_path / "missing", "workspace")


def test_lock_root_symlink_is_rejected_before_writing_outside(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root-link"
    try:
        root.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(LockError, match="lock-reparse"):
        acquire_run_lock(root, "workspace")
    assert not (outside / ".canon-locks" / "workspace.lock").exists()


def test_lock_directory_symlink_is_rejected_before_writing_outside(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    try:
        (root / ".canon-locks").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(LockError, match="lock-reparse"):
        acquire_run_lock(root, "workspace")
    assert not (outside / "workspace.lock").exists()


def test_release_refuses_lock_path_outside_lock_root(tmp_path: Path) -> None:
    outside = tmp_path / "outside.lock"
    outside.write_text("token", encoding="utf-8")
    lock = RunLock(root=tmp_path, name="workspace", token="token", path=outside)

    with pytest.raises(LockError, match="lock-escape"):
        release_run_lock(lock)
    assert outside.exists()


def test_release_checks_token_ownership_and_is_idempotent(tmp_path: Path) -> None:
    lock = acquire_run_lock(tmp_path, "workspace")
    lock.path.write_text("other-token", encoding="utf-8")

    with pytest.raises(LockError, match="lock-token-mismatch"):
        release_run_lock(lock)
    assert lock.path.exists()

    lock.path.write_text(lock.token, encoding="utf-8")
    release_run_lock(lock)
    release_run_lock(lock)
    assert not lock.path.exists()


def test_release_rejects_reparse_lock_file(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    lock_dir = root / ".canon-locks"
    lock_dir.mkdir()
    target = tmp_path / "outside.lock"
    target.write_text("token", encoding="utf-8")
    link = lock_dir / "workspace.lock"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")
    lock = RunLock(root=root, name="workspace", token="token", path=link)

    with pytest.raises(LockError, match="lock-reparse"):
        release_run_lock(lock)
    assert link.exists() or link.is_symlink()
    assert target.exists()


def test_release_rejects_directory_lock_path_before_reading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    lock_dir = root / ".canon-locks"
    lock_path = lock_dir / "workspace.lock"
    lock_path.mkdir(parents=True)
    lock = RunLock(root=root, name="workspace", token="token", path=lock_path)

    def fail_read_text(self: Path, *args: object, **kwargs: object) -> str:
        raise AssertionError("non-regular lock path must be rejected before read")

    monkeypatch.setattr(Path, "read_text", fail_read_text)

    with pytest.raises(LockError, match="lock-nonregular"):
        release_run_lock(lock)

    assert lock_path.is_dir()


def test_release_rejects_special_lock_path_before_reading(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if not hasattr(socket, "AF_UNIX"):
        pytest.skip("platform has no safe non-blocking socket path support")
    root = tmp_path / "root"
    lock_dir = root / ".canon-locks"
    lock_dir.mkdir(parents=True)
    lock_path = lock_dir / "workspace.lock"
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        try:
            server.bind(str(lock_path))
        except OSError:
            pytest.skip("platform cannot create a safe socket lock path")
        lock = RunLock(root=root, name="workspace", token="token", path=lock_path)

        def fail_read_text(self: Path, *args: object, **kwargs: object) -> str:
            raise AssertionError("non-regular lock path must be rejected before read")

        monkeypatch.setattr(Path, "read_text", fail_read_text)

        with pytest.raises(LockError, match="lock-nonregular"):
            release_run_lock(lock)
    finally:
        server.close()


def test_acquire_cleans_up_partial_lock_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    real_write = os.write
    calls = 0

    def partial_then_fail(fd: int, data: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return max(1, len(data) // 2)
        raise OSError(errno.ENOSPC, "no space left")

    monkeypatch.setattr(os, "write", partial_then_fail)

    with pytest.raises(LockError, match="lock-write") as caught:
        acquire_run_lock(tmp_path, "workspace")

    assert isinstance(caught.value.__cause__, OSError)
    assert not (tmp_path / ".canon-locks" / "workspace.lock").exists()
    monkeypatch.setattr(os, "write", real_write)


def test_acquire_maps_raw_os_open_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def deny_open(*args: object, **kwargs: object) -> int:
        raise PermissionError(errno.EACCES, "denied")

    monkeypatch.setattr(os, "open", deny_open)

    with pytest.raises(LockError, match="lock-open") as caught:
        acquire_run_lock(tmp_path, "workspace")

    assert isinstance(caught.value.__cause__, PermissionError)


def test_guarded_commit_aborts_without_calling_commit_on_source_change() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError):
        guarded_commit(_sha("f"), (item,), commit)

    assert not called
    assert guarded_commit(source_state_sha256((item,)), (item,), commit) == "written"


def test_guarded_commit_aborts_without_calling_commit_on_invalid_state() -> None:
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError, match="invalid-source-state"):
        guarded_commit("not-a-digest", (), commit)

    assert not called


def test_guarded_commit_aborts_without_calling_commit_on_mutated_source_item() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)
    expected = source_state_sha256((item,))
    object.__setattr__(item, "size", True)
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError, match="invalid-source-state-item"):
        guarded_commit(expected, (item,), commit)

    assert not called


def test_guarded_commit_requires_callable_after_state_validation() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    with pytest.raises(LockError, match="invalid-commit"):
        guarded_commit(source_state_sha256((item,)), (item,), object())
