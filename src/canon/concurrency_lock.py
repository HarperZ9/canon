from __future__ import annotations

import errno
import os
import re
import stat
import time
from pathlib import Path

from . import concurrency_windows as _win

_LOCK_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_LOCK_FLAGS = os.O_CREAT | os.O_EXCL | os.O_WRONLY
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_RESERVED = frozenset(
    {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
)

class LockError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")

def validate_lock_name(name: object) -> str:
    if not isinstance(name, str) or name in ("", ".", ".."):
        raise LockError("invalid-lock-name", "name must be non-empty text")
    if "\0" in name or has_control(name) or _LOCK_NAME_RE.fullmatch(name) is None:
        raise LockError("invalid-lock-name", name)
    if name.endswith(".") or name.split(".", 1)[0].casefold() in _RESERVED:
        raise LockError("invalid-lock-name", name)
    return name

def resolve_lock_root(root: object) -> Path:
    path = coerce_path(root, role="lock-root")
    if is_reparse_point(path):
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

def prepare_lock_dir(root: Path) -> Path:
    lock_dir = root / ".canon-locks"
    if exists_or_link(lock_dir) and is_reparse_point(lock_dir):
        raise LockError("lock-reparse", str(lock_dir))
    try:
        lock_dir.mkdir(mode=0o700, exist_ok=True)
    except OSError as exc:
        raise LockError("lock-root", str(exc)) from exc
    if is_reparse_point(lock_dir) or not lock_dir.is_dir():
        raise LockError("lock-reparse", str(lock_dir))
    return lock_dir

def new_lock_token() -> str:
    return f"{os.getpid()}:{time.monotonic_ns()}"

def write_new_lock(lock_dir: Path, lock_name: str, token: str) -> Path:
    snapshot = _lock_dir_snapshot(lock_dir)
    lock_path = lock_dir / lock_name
    if _can_use_windows_lock():
        _write_new_lock_windows(lock_dir, lock_name, token, snapshot)
        return lock_path
    if _can_use_dir_fd_lock():
        _write_new_lock_dir_fd(lock_dir, lock_name, token, snapshot)
        return lock_path
    raise LockError("lock-unsupported", "stable lock primitive unavailable")

def release_lock(root: object, name: object, token: object, path: object) -> None:
    checked_name = validate_lock_name(name)
    if not isinstance(token, str) or token == "" or has_control(token):
        raise LockError("invalid-lock", "token must be non-empty text")
    root_path = resolve_lock_root(root)
    lock_path = coerce_path(path, role="lock-path")
    _assert_release_target(root_path, checked_name, lock_path)
    if not exists_or_link(lock_path):
        return
    if is_reparse_point(lock_path):
        raise LockError("lock-reparse", str(lock_path))
    _assert_regular_lock_file(lock_path)
    if _read_lock_token(lock_path) != token:
        raise LockError("lock-token-mismatch", str(lock_path))
    _unlink_lock(lock_path)

def coerce_path(value: object, *, role: str) -> Path:
    try:
        raw = os.fspath(value)
    except TypeError as exc:
        raise LockError(f"invalid-{role}", type(value).__name__) from exc
    if not isinstance(raw, str) or raw == "" or "\0" in raw:
        raise LockError(f"invalid-{role}", str(raw))
    return Path(raw)

def has_control(value: str) -> bool:
    return any(ord(ch) < 32 or ord(ch) == 127 for ch in value)

def exists_or_link(path: Path) -> bool:
    try:
        return path.exists() or path.is_symlink()
    except OSError:
        return True

def is_reparse_point(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        attrs = getattr(path.lstat(), "st_file_attributes", None)
    except FileNotFoundError:
        return False
    except OSError:
        return True
    return bool(attrs & _REPARSE_POINT) if attrs is not None else False

def _write_new_lock_windows(lock_dir: Path, lock_name: str, token: str, snapshot: tuple[Path, int, int]) -> None:
    try:
        dir_handle = _win.open_directory(lock_dir)
    except OSError as exc:
        raise LockError("lock-open", str(exc)) from exc
    wrote = False
    try:
        _verify_lock_dir(lock_dir, snapshot)
        try:
            _win.create_lock_file(dir_handle, lock_name, token)
            wrote = True
        except FileExistsError as exc:
            raise LockError("lock-held", str(lock_dir / lock_name)) from exc
        except _win.LockWriteError as exc:
            raise LockError("lock-write", str(exc)) from exc
        except OSError as exc:
            raise LockError("lock-open", str(exc)) from exc
        _verify_created_lock(lock_dir, snapshot, lock_dir / lock_name, token)
    except LockError:
        if wrote:
            _delete_windows_lock(dir_handle, lock_name)
        raise
    finally:
        _close_windows_handle(dir_handle)

def _write_new_lock_dir_fd(lock_dir: Path, lock_name: str, token: str, snapshot: tuple[Path, int, int]) -> None:
    dir_fd = _open_lock_dir_fd(lock_dir)
    wrote = False
    try:
        _verify_lock_dir(lock_dir, snapshot)
        flags = _LOCK_FLAGS | getattr(os, "O_NOFOLLOW")
        _write_token_to_new_lock(lock_name, token, flags, dir_fd=dir_fd)
        wrote = True
        _verify_created_lock(lock_dir, snapshot, lock_dir / lock_name, token)
    except LockError:
        if wrote:
            _unlink_dir_fd_lock(dir_fd, lock_name)
        raise
    finally:
        _close_fd(dir_fd)

def _write_token_to_new_lock(target: str | Path, token: str, flags: int, *, dir_fd: int | None = None) -> None:
    try:
        fd = os.open(target, flags, 0o600, dir_fd=dir_fd)
    except FileExistsError as exc:
        raise LockError("lock-held", str(target)) from exc
    except OSError as exc:
        raise LockError("lock-open", str(exc)) from exc
    try:
        _write_all(fd, token.encode("ascii"))
        os.close(fd)
    except OSError as exc:
        _close_fd(fd)
        _unlink_dir_fd_lock(dir_fd, os.fspath(target))
        raise LockError("lock-write", str(exc)) from exc

def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError(errno.EIO, "lock write made no progress")
        offset += written

def _can_use_dir_fd_lock() -> bool:
    return os.open in os.supports_dir_fd and os.unlink in os.supports_dir_fd and all(
        hasattr(os, name) for name in ("O_DIRECTORY", "O_NOFOLLOW")
    )

def _can_use_windows_lock() -> bool:
    return os.name == "nt" and _win.supported()

def _open_lock_dir_fd(lock_dir: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY") | getattr(os, "O_NOFOLLOW")
    try:
        return os.open(lock_dir, flags)
    except OSError as exc:
        code = "lock-reparse" if exc.errno in (errno.ELOOP, errno.ENOTDIR) else "lock-open"
        raise LockError(code, str(exc)) from exc

def _verify_created_lock(lock_dir: Path, snapshot: tuple[Path, int, int], lock_path: Path, token: str) -> None:
    _verify_lock_dir(lock_dir, snapshot)
    if is_reparse_point(lock_path):
        raise LockError("lock-reparse", str(lock_path))
    _assert_regular_lock_file(lock_path, missing_ok=False)
    if _read_lock_token(lock_path) != token:
        raise LockError("lock-token-mismatch", str(lock_path))

def _lock_dir_snapshot(lock_dir: Path) -> tuple[Path, int, int]:
    if is_reparse_point(lock_dir):
        raise LockError("lock-reparse", str(lock_dir))
    try:
        resolved = lock_dir.resolve(strict=True)
        info = lock_dir.lstat()
    except FileNotFoundError as exc:
        raise LockError("lock-reparse", str(lock_dir)) from exc
    except OSError as exc:
        raise LockError("lock-root", str(exc)) from exc
    if not stat.S_ISDIR(info.st_mode):
        raise LockError("lock-reparse", str(lock_dir))
    return (resolved, info.st_dev, info.st_ino)

def _verify_lock_dir(lock_dir: Path, snapshot: tuple[Path, int, int]) -> None:
    if _lock_dir_snapshot(lock_dir) != snapshot:
        raise LockError("lock-reparse", str(lock_dir))

def _assert_release_target(root: Path, name: str, lock_path: Path) -> None:
    lock_dir = root / ".canon-locks"
    expected_name = f"{name}.lock"
    if exists_or_link(lock_dir) and is_reparse_point(lock_dir):
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

def _read_lock_token(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LockError("lock-release", str(exc)) from exc

def _assert_regular_lock_file(path: Path, *, missing_ok: bool = True) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError as exc:
        if not missing_ok:
            raise LockError("lock-open", str(path)) from exc
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

def _unlink_dir_fd_lock(dir_fd: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=dir_fd)
    except OSError:
        pass

def _delete_windows_lock(dir_handle: int, name: str) -> None:
    try:
        _win.delete_lock_file(dir_handle, name)
    except OSError:
        pass

def _close_windows_handle(handle: int) -> None:
    try:
        _win.close_handle(handle)
    except OSError:
        pass

def _close_fd(fd: int) -> None:
    try:
        os.close(fd)
    except OSError:
        pass
