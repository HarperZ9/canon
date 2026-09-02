from __future__ import annotations

import os
from pathlib import Path
import stat

from .canonical_json import sha256_bytes
from .cli_artifacts import WorkspaceRoot
from .path_policy import PathPolicyError, assert_operational_surface_path, is_reparse_point, resolve_under_root
from .undo_receipts import UndoError, UndoReceipt, valid_receipt_id

_TEMP_ATTEMPTS = 8


def undo_root_path(root: Path) -> Path:
    try:
        return resolve_under_root(".canon/undo", root=root)
    except PathPolicyError as exc:
        raise UndoError("unsafe_path") from exc


def ensure_undo_root(root: Path) -> Path:
    undo_root = undo_root_path(root)
    try:
        undo_root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise UndoError("io_error") from exc
    if is_reparse_point(undo_root) or not stat.S_ISDIR(undo_root.lstat().st_mode):
        raise UndoError("unsafe_path")
    return undo_root


def receipt_path(root: Path, receipt_id: str) -> Path:
    if not valid_receipt_id(receipt_id):
        raise UndoError("invalid_args")
    return root / f"{receipt_id}.json"


def checked_receipt_target(receipt: UndoReceipt, *, workspace: WorkspaceRoot) -> Path:
    _assert_workspace_stable(workspace)
    try:
        target = assert_operational_surface_path(receipt.target_path, root=workspace.path)
    except PathPolicyError as exc:
        raise UndoError("unsafe_path") from exc
    _reject_reserved_target(target, workspace.path)
    if (receipt.target_adapter, receipt.target_surface, receipt.target_path) not in {
        ("codex-cli", "AGENTS.md", "AGENTS.md"),
        ("claude-code", "CLAUDE.md", "CLAUDE.md"),
    }:
        raise UndoError("conflict")
    _assert_workspace_stable(workspace)
    return target


def read_regular_file(path: Path) -> bytes:
    try:
        before = path.lstat()
    except FileNotFoundError as exc:
        raise UndoError("conflict") from exc
    except OSError as exc:
        raise UndoError("io_error") from exc
    if not stat.S_ISREG(before.st_mode) or is_reparse_point(path):
        raise UndoError("unsafe_path")
    fd = _open_regular_for_read(path)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or _stat_key(info) != _stat_key(before):
            raise UndoError("unsafe_path")
        return _read_fd(fd, info.st_size)
    finally:
        os.close(fd)


def replace_file_guarded(path: Path, expected_hash: str, replacement: bytes) -> None:
    if sha256_bytes(read_regular_file(path)) != expected_hash:
        raise UndoError("conflict")
    _atomic_replace(path, expected_hash, replacement)
    if sha256_bytes(read_regular_file(path)) != sha256_bytes(replacement):
        raise UndoError("io_error")


def write_new_or_same(path: Path, data: bytes) -> str:
    if _exists_or_link(path):
        if read_regular_file(path) == data:
            return "idempotent"
        raise UndoError("conflict")
    fd: int | None = None
    try:
        fd = os.open(path, _write_flags(), 0o600)
        _write_all(fd, data)
        os.fsync(fd)
    except FileExistsError:
        return write_new_or_same(path, data)
    except OSError as exc:
        raise UndoError("io_error") from exc
    finally:
        if fd is not None:
            os.close(fd)
    if read_regular_file(path) != data:
        raise UndoError("io_error")
    return "created"


def _atomic_replace(path: Path, expected_hash: str, replacement: bytes) -> None:
    mode = stat.S_IMODE(path.lstat().st_mode)
    for _attempt in range(_TEMP_ATTEMPTS):
        temp = path.parent / f".{path.name}.{os.urandom(8).hex()}.tmp"
        fd: int | None = None
        try:
            fd = os.open(temp, _write_flags(), 0o600)
            _write_all(fd, replacement)
            os.fsync(fd)
        except FileExistsError:
            continue
        except Exception:
            _close_fd(fd)
            _cleanup_temp(temp)
            raise
        _close_fd(fd)
        try:
            os.chmod(temp, mode)
            if sha256_bytes(read_regular_file(path)) != expected_hash:
                raise UndoError("conflict")
            os.replace(temp, path)
            return
        except Exception:
            _cleanup_temp(temp)
            raise
    raise UndoError("io_error")


def _open_regular_for_read(path: Path) -> int:
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        return os.open(path, flags)
    except OSError as exc:
        raise UndoError("unsafe_path") from exc


def _write_flags() -> int:
    return os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)


def _read_fd(fd: int, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = os.read(fd, min(remaining, 65536))
        if not chunk:
            raise UndoError("io_error")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _reject_reserved_target(path: Path, root: Path) -> None:
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    parts = tuple(part.casefold() for part in rel.split("/"))
    if parts[0] == ".git" or parts[:2] == (".canon", "undo") or parts[:2] == ("tests", "fixtures"):
        raise UndoError("unsafe_path")


def _assert_workspace_stable(workspace: WorkspaceRoot) -> None:
    try:
        info = workspace.path.lstat()
    except OSError as exc:
        raise UndoError("unsafe_path") from exc
    if _stat_key(info) != workspace.stat_key or not stat.S_ISDIR(info.st_mode) or is_reparse_point(workspace.path):
        raise UndoError("unsafe_path")


def _close_fd(fd: int | None) -> None:
    if fd is None:
        return
    try:
        os.close(fd)
    except OSError:
        pass


def _cleanup_temp(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _exists_or_link(path: Path) -> bool:
    try:
        return path.exists() or path.is_symlink()
    except OSError:
        return True


def _stat_key(info: os.stat_result) -> tuple[int, int]:
    if os.name == "nt":
        return (info.st_dev & 0xFFFFFFFF, info.st_ino)
    return (info.st_dev, info.st_ino)


__all__ = [
    "checked_receipt_target",
    "ensure_undo_root",
    "read_regular_file",
    "receipt_path",
    "replace_file_guarded",
    "undo_root_path",
    "write_new_or_same",
]
