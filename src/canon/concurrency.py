from __future__ import annotations

import errno
import os
import re
import stat
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .source_state import SourceStateItem, assert_source_state

_LOCK_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_RESERVED = frozenset({
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
})


class LockError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class RunLock:
    root: Path
    name: str
    token: str
    path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.root, Path) or not isinstance(self.path, Path):
            raise LockError("invalid-lock", "root and path must be Path")
        _validate_lock_name(self.name)
        if not isinstance(self.token, str) or self.token == "" or _has_control(self.token):
            raise LockError("invalid-lock", "token must be non-empty text")


def acquire_run_lock(root: str | Path, name: str) -> RunLock:
    checked_name = _validate_lock_name(name)
    root_path = _resolve_lock_root(root)
    lock_dir = _prepare_lock_dir(root_path)
    lock_path = lock_dir / f"{checked_name}.lock"
    token = f"{os.getpid()}:{time.monotonic_ns()}"
    _write_new_lock(lock_path, token)
    return RunLock(root=root_path, name=checked_name, token=token, path=lock_path)


def release_run_lock(lock: RunLock) -> None:
    if not isinstance(lock, RunLock):
        raise LockError("invalid-lock", "lock must be RunLock")
    _validate_lock_name(lock.name)
    root = _resolve_lock_root(lock.root)
    lock_path = _coerce_path(lock.path, role="lock-path")
    _assert_release_target(root, lock.name, lock_path)
    if not _exists_or_link(lock_path):
        return
    if _is_reparse_point(lock_path):
        raise LockError("lock-reparse", str(lock_path))
    _assert_regular_lock_file(lock_path)
    token = _read_lock_token(lock_path)
    if token != lock.token:
        raise LockError("lock-token-mismatch", str(lock_path))
    _unlink_lock(lock_path)


def guarded_commit(
    expected_source_state: str,
    current_items: tuple[SourceStateItem, ...],
    commit: Callable[[], object],
) -> object:
    assert_source_state(expected_source_state, current_items)
    if not callable(commit):
        raise LockError("invalid-commit", "commit must be callable")
    return commit()


def _validate_lock_name(name: object) -> str:
    if not isinstance(name, str) or name in ("", ".", ".."):
        raise LockError("invalid-lock-name", "name must be non-empty text")
    if "\0" in name or _has_control(name) or _LOCK_NAME_RE.fullmatch(name) is None:
        raise LockError("invalid-lock-name", name)
    if name.endswith(".") or name.split(".", 1)[0].casefold() in _RESERVED:
        raise LockError("invalid-lock-name", name)
    return name


def _resolve_lock_root(root: object) -> Path:
    path = _coerce_path(root, role="lock-root")
    if _is_reparse_point(path):
        raise LockError("lock-reparse", str(path))
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise LockError("invalid-lock-root", str(path)) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise LockError("invalid-lock-root", str(exc)) from exc
    if not resolved.is_dir():
        raise LockError("invalid-lock-root", str(resolved))
    return resolved


def _prepare_lock_dir(root: Path) -> Path:
    lock_dir = root / ".canon-locks"
    if _exists_or_link(lock_dir) and _is_reparse_point(lock_dir):
        raise LockError("lock-reparse", str(lock_dir))
    try:
        lock_dir.mkdir(mode=0o700, exist_ok=True)
    except OSError as exc:
        raise LockError("lock-root", str(exc)) from exc
    if _is_reparse_point(lock_dir) or not lock_dir.is_dir():
        raise LockError("lock-reparse", str(lock_dir))
    return lock_dir


def _write_new_lock(path: Path, token: str) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise LockError("lock-held", str(path)) from exc
    except OSError as exc:
        raise LockError("lock-open", str(exc)) from exc
    try:
        _write_all(fd, token.encode("ascii"))
        os.close(fd)
    except OSError as exc:
        _close_fd(fd)
        _cleanup_partial_lock(path)
        raise LockError("lock-write", str(exc)) from exc


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError(errno.EIO, "lock write made no progress")
        offset += written


def _assert_release_target(root: Path, name: str, lock_path: Path) -> None:
    lock_dir = root / ".canon-locks"
    expected_name = f"{name}.lock"
    if _exists_or_link(lock_dir) and _is_reparse_point(lock_dir):
        raise LockError("lock-reparse", str(lock_dir))
    if lock_path.name != expected_name or not _is_under(lock_path, lock_dir):
        raise LockError("lock-escape", str(lock_path))


def _is_under(path: Path, root: Path) -> bool:
    try:
        root_text = os.path.normcase(os.path.abspath(root))
        path_text = os.path.normcase(os.path.abspath(path))
        return os.path.commonpath((root_text, path_text)) == root_text
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _coerce_path(value: object, *, role: str) -> Path:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise LockError(f"invalid-{role}", type(value).__name__) from exc
    if not isinstance(raw, str) or raw == "" or "\0" in raw:
        raise LockError(f"invalid-{role}", str(raw))
    return Path(raw)


def _read_lock_token(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LockError("lock-release", str(exc)) from exc


def _assert_regular_lock_file(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LockError("lock-release", str(exc)) from exc
    if not stat.S_ISREG(mode):
        raise LockError("lock-nonregular", str(path))


def _unlink_lock(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LockError("lock-release", str(exc)) from exc


def _cleanup_partial_lock(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _close_fd(fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        pass


def _exists_or_link(path: Path) -> bool:
    try:
        return path.exists() or path.is_symlink()
    except OSError:
        return True


def _is_reparse_point(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attrs = getattr(path.lstat(), "st_file_attributes", None)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return bool(attrs & _REPARSE_POINT) if attrs is not None else False


def _has_control(value: str) -> bool:
    return any(ord(ch) < 32 or ord(ch) == 127 for ch in value)
