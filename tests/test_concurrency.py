from __future__ import annotations

from collections.abc import Iterator
import errno
import hashlib
import os
import socket
from pathlib import Path

import pytest

import canon.concurrency_lock as concurrency_lock
import canon.concurrency_windows as concurrency_windows
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


def _swap_lock_dir_to_symlink(lock_dir: Path, displaced: Path, outside: Path) -> None:
    try:
        lock_dir.rename(displaced)
        lock_dir.symlink_to(outside, target_is_directory=True)
    except OSError:
        _restore_displaced_lock_dir(lock_dir, displaced)
        pytest.skip("current platform or privileges do not allow directory symlinks")


def _restore_displaced_lock_dir(lock_dir: Path, displaced: Path) -> None:
    if lock_dir.is_symlink():
        lock_dir.unlink()
    if displaced.exists():
        displaced.rename(lock_dir)


class _HostileSourceStateItem(SourceStateItem):
    _malicious = {
        "path": "../escape.md",
        "sha256": "sha256:" + "B" * 64,
        "size": True,
    }

    def __getattribute__(self, name: str) -> object:
        if name in ("path", "sha256", "size") and _hostile_armed(self):
            reads = object.__getattribute__(self, "_reads")
            reads[name] = reads.get(name, 0) + 1
            threshold = {"path": 2, "sha256": 1, "size": 1}[name]
            if reads[name] > threshold:
                return self._malicious[name]
        return super().__getattribute__(name)


def _hostile_armed(item: object) -> bool:
    try:
        return object.__getattribute__(item, "_armed")
    except AttributeError:
        return False


def _hostile_source_item() -> SourceStateItem:
    item = _HostileSourceStateItem(path="a.md", sha256=_sha("a"), size=1)
    object.__setattr__(item, "_reads", {})
    object.__setattr__(item, "_armed", True)
    return item


class _HostileSourceStateTuple(tuple):
    def __new__(cls) -> "_HostileSourceStateTuple":
        return super().__new__(cls, ())

    def __init__(self) -> None:
        self._reads = 0
        self._valid = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)
        self._malicious = SourceStateItem(path="b.md", sha256=_sha("b"), size=2)
        object.__setattr__(self._malicious, "path", "../escape.md")
        object.__setattr__(self._malicious, "sha256", "sha256:" + "B" * 64)
        object.__setattr__(self._malicious, "size", True)

    def __iter__(self) -> Iterator[SourceStateItem]:
        self._reads += 1
        if self._reads == 1:
            return iter((self._valid,))
        return iter((self._malicious,))


def _hostile_source_tuple() -> tuple[SourceStateItem, ...]:
    return _HostileSourceStateTuple()


def _hostile_source_digest() -> str:
    raw = (
        b'[{"path":"../escape.md","sha256":"sha256:'
        + b"B" * 64
        + b'","size":true}]\n'
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


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


def test_acquire_rejects_lock_directory_swap_after_prepare(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    real_prepare = concurrency_lock.prepare_lock_dir

    def prepare_then_swap(resolved_root: Path) -> Path:
        lock_dir = real_prepare(resolved_root)
        try:
            lock_dir.rmdir()
            lock_dir.symlink_to(outside, target_is_directory=True)
        except OSError:
            pytest.skip("current platform or privileges do not allow directory symlinks")
        return lock_dir

    monkeypatch.setattr(concurrency_lock, "prepare_lock_dir", prepare_then_swap)

    with pytest.raises(LockError, match="lock-reparse"):
        acquire_run_lock(root, "workspace")

    assert not (outside / "workspace.lock").exists()


def test_acquire_rejects_swap_back_without_outside_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    displaced = tmp_path / "displaced-locks"
    root.mkdir()
    outside.mkdir()
    real_snapshot = concurrency_lock._lock_dir_snapshot
    real_open = os.open
    swapped = False

    def snapshot_then_swap(lock_dir: Path) -> tuple[Path, int, int]:
        nonlocal swapped
        snapshot = real_snapshot(lock_dir)
        if not swapped:
            swapped = True
            _swap_lock_dir_to_symlink(lock_dir, displaced, outside)
        return snapshot

    def open_with_swap(
        path: object,
        flags: int,
        mode: int = 0o777,
        *args: object,
        **kwargs: object,
    ) -> int:
        try:
            return real_open(path, flags, mode, *args, **kwargs)
        finally:
            lock_dir = root / ".canon-locks"
            _restore_displaced_lock_dir(lock_dir, displaced)

    monkeypatch.setattr(concurrency_lock, "_lock_dir_snapshot", snapshot_then_swap)
    monkeypatch.setattr(os, "open", open_with_swap)

    try:
        with pytest.raises(LockError, match="lock-open|lock-reparse"):
            acquire_run_lock(root, "workspace")
        assert not (outside / "workspace.lock").exists()
    finally:
        (outside / "workspace.lock").unlink(missing_ok=True)
        _restore_displaced_lock_dir(root / ".canon-locks", displaced)

    assert not (root / ".canon-locks" / "workspace.lock").exists()


def test_acquire_refuses_when_stable_parent_primitive_unavailable_before_create(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    called = False

    def fail_open(*args: object, **kwargs: object) -> int:
        nonlocal called
        called = True
        raise AssertionError("full-path os.open fallback must not be used")

    monkeypatch.setattr(concurrency_lock, "_can_use_dir_fd_lock", lambda: False)
    monkeypatch.setattr(concurrency_lock, "_can_use_windows_lock", lambda: False, raising=False)
    monkeypatch.setattr(os, "open", fail_open)

    with pytest.raises(LockError, match="lock-unsupported"):
        acquire_run_lock(tmp_path, "workspace")

    assert not called
    assert not (tmp_path / ".canon-locks" / "workspace.lock").exists()


def test_windows_conflict_uses_stable_parent_handle_not_full_path_open(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if os.name != "nt":
        pytest.skip("Windows stable-parent primitive regression")
    first = acquire_run_lock(tmp_path, "workspace")

    def fail_open(*args: object, **kwargs: object) -> int:
        raise AssertionError("full-path os.open fallback must not be used")

    monkeypatch.setattr(os, "open", fail_open)
    try:
        with pytest.raises(LockError, match="lock-held"):
            acquire_run_lock(tmp_path, "workspace")
        assert first.path.read_text(encoding="utf-8") == first.token
    finally:
        release_run_lock(first)


def test_acquire_handle_cleanup_survives_lock_directory_swap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    displaced = tmp_path / "displaced-locks"
    root.mkdir()
    outside.mkdir()

    def swap_then_fail(
        lock_dir: Path,
        snapshot: tuple[Path, int, int],
        lock_path: Path,
        token: str,
    ) -> None:
        _swap_lock_dir_to_symlink(lock_dir, displaced, outside)
        raise LockError("lock-reparse", str(lock_path))

    monkeypatch.setattr(concurrency_lock, "_verify_created_lock", swap_then_fail)

    try:
        with pytest.raises(LockError, match="lock-reparse"):
            acquire_run_lock(root, "workspace")
    finally:
        _restore_displaced_lock_dir(root / ".canon-locks", displaced)

    assert not (root / ".canon-locks" / "workspace.lock").exists()
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
    calls = 0

    def partial_then_fail(fd: int, data: bytes) -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return max(1, len(data) // 2)
        raise OSError(errno.ENOSPC, "no space left")

    def fail_windows_write(handle: int, data: bytes) -> None:
        raise OSError(errno.ENOSPC, "no space left")

    if os.name == "nt":
        monkeypatch.setattr(concurrency_windows, "_write_file", fail_windows_write)
    else:
        monkeypatch.setattr(os, "write", partial_then_fail)

    with pytest.raises(LockError, match="lock-write") as caught:
        acquire_run_lock(tmp_path, "workspace")

    assert isinstance(caught.value.__cause__, OSError)
    assert not (tmp_path / ".canon-locks" / "workspace.lock").exists()


def test_acquire_maps_raw_stable_open_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def deny_open(*args: object, **kwargs: object) -> int:
        raise PermissionError(errno.EACCES, "denied")

    def deny_windows_open(path: Path) -> int:
        raise PermissionError(errno.EACCES, "denied")

    if os.name == "nt":
        monkeypatch.setattr(concurrency_windows, "open_directory", deny_windows_open)
    else:
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


def test_guarded_commit_rejects_hostile_item_subclass_without_calling_commit() -> None:
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError, match="invalid-source-state"):
        guarded_commit(_hostile_source_digest(), (_hostile_source_item(),), commit)

    assert not called


def test_guarded_commit_rejects_hostile_tuple_subclass_without_calling_commit() -> None:
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError, match="invalid-source-state"):
        guarded_commit(_hostile_source_digest(), _hostile_source_tuple(), commit)

    assert not called


def test_guarded_commit_requires_callable_after_state_validation() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    with pytest.raises(LockError, match="invalid-commit"):
        guarded_commit(source_state_sha256((item,)), (item,), object())
