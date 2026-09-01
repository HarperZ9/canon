from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .canonical_json import sha256_text
from .cli_artifacts import WorkspaceRoot
from .path_policy import is_reparse_point, resolve_under_root
from .witness import BootstrapWitness, validate_bootstrap_witness


class BootstrapWitnessStoreError(OSError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class WitnessWrite:
    relative_path: str
    status: str


def write_bootstrap_witness(
    witness: BootstrapWitness,
    *,
    workspace: WorkspaceRoot,
    state_dir: Path,
) -> WitnessWrite:
    if validate_bootstrap_witness(witness):
        raise BootstrapWitnessStoreError("io_error")
    _assert_workspace_stable(workspace)
    root = _witness_root(state_dir)
    target = _target_path(root, witness.run_id)
    data = witness.to_json().encode("utf-8")
    status = _write_once(target, data)
    _assert_workspace_stable(workspace)
    return WitnessWrite(_relative_text(target, workspace.path), status)


def _witness_root(state_dir: Path) -> Path:
    try:
        root = resolve_under_root("witnesses", root=state_dir)
    except Exception as exc:
        raise BootstrapWitnessStoreError("unsafe_path") from exc
    try:
        if root.exists() or root.is_symlink():
            if is_reparse_point(root):
                raise BootstrapWitnessStoreError("unsafe_path")
            if not stat.S_ISDIR(root.lstat().st_mode):
                raise BootstrapWitnessStoreError("io_error")
        root.mkdir(parents=True, exist_ok=True)
    except BootstrapWitnessStoreError:
        raise
    except OSError as exc:
        raise BootstrapWitnessStoreError("io_error") from exc
    return root


def _target_path(root: Path, run_id: str) -> Path:
    digest = sha256_text(run_id).removeprefix("sha256:")
    try:
        return resolve_under_root(f"run-{digest}.json", root=root)
    except Exception as exc:
        raise BootstrapWitnessStoreError("unsafe_path") from exc


def _write_once(path: Path, data: bytes) -> str:
    if path.exists() or path.is_symlink():
        return _existing_status(path, data)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        return _existing_status(path, data)
    except OSError as exc:
        raise BootstrapWitnessStoreError("io_error") from exc
    try:
        _write_all(fd, data)
        os.fsync(fd)
    except OSError as exc:
        raise BootstrapWitnessStoreError("io_error") from exc
    finally:
        os.close(fd)
    if _read_existing(path) != data:
        raise BootstrapWitnessStoreError("io_error")
    return "created"


def _existing_status(path: Path, expected: bytes) -> str:
    if is_reparse_point(path):
        raise BootstrapWitnessStoreError("unsafe_path")
    if _read_existing(path) == expected:
        return "idempotent"
    raise BootstrapWitnessStoreError("conflict")


def _read_existing(path: Path) -> bytes:
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise BootstrapWitnessStoreError("conflict")
        data = path.read_bytes()
        after = path.lstat()
    except BootstrapWitnessStoreError:
        raise
    except OSError as exc:
        raise BootstrapWitnessStoreError("io_error") from exc
    if (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size):
        raise BootstrapWitnessStoreError("unsafe_path")
    return data


def _write_all(fd: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(fd, data[offset:])
        if written <= 0:
            raise OSError("short witness write")
        offset += written


def _assert_workspace_stable(workspace: WorkspaceRoot) -> None:
    try:
        info = workspace.path.lstat()
    except OSError as exc:
        raise BootstrapWitnessStoreError("unsafe_path") from exc
    if _stat_key(info) != workspace.stat_key or not stat.S_ISDIR(info.st_mode):
        raise BootstrapWitnessStoreError("unsafe_path")
    if is_reparse_point(workspace.path):
        raise BootstrapWitnessStoreError("unsafe_path")


def _relative_text(path: Path, root: Path) -> str:
    try:
        return os.path.relpath(path, root).replace(os.sep, "/")
    except ValueError as exc:
        raise BootstrapWitnessStoreError("unsafe_path") from exc


def _stat_key(info: os.stat_result) -> tuple[int, int]:
    if os.name == "nt":
        return (info.st_dev & 0xFFFFFFFF, info.st_ino)
    return (info.st_dev, info.st_ino)


__all__ = ["BootstrapWitnessStoreError", "WitnessWrite", "write_bootstrap_witness"]
