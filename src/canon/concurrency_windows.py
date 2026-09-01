from __future__ import annotations

import errno
from pathlib import Path

from . import concurrency_windows_api as _api

_MAX_TOKEN_BYTES = 4096


class LockWriteError(OSError):
    pass


def supported() -> bool:
    return _api.supported()


def open_directory(path: Path) -> int:
    if not supported():
        raise OSError(errno.ENOSYS, "stable Windows lock primitive unavailable")
    handle = _api.create_file(
        str(path),
        _api.GENERIC_READ,
        _api.FILE_SHARE_READ | _api.FILE_SHARE_WRITE | _api.FILE_SHARE_DELETE,
        _api.OPEN_EXISTING,
        _api.FILE_FLAG_BACKUP_SEMANTICS | _api.FILE_FLAG_OPEN_REPARSE_POINT,
    )
    try:
        attrs = _api.handle_info(handle).dwFileAttributes
        if not attrs & _api.FILE_ATTRIBUTE_DIRECTORY or attrs & _api.FILE_ATTRIBUTE_REPARSE_POINT:
            raise OSError(errno.ELOOP, "lock directory is reparse or non-directory")
        return handle
    except Exception:
        close_handle(handle)
        raise


def create_lock_file(dir_handle: int, name: str, token: str) -> int:
    handle = _api.nt_create_relative(
        dir_handle,
        name,
        _api.GENERIC_READ | _api.GENERIC_WRITE | _api.SYNCHRONIZE,
        _api.FILE_SHARE_READ | _api.FILE_SHARE_WRITE | _api.FILE_SHARE_DELETE,
        _api.FILE_CREATE,
        _api.FILE_NON_DIRECTORY_FILE | _api.FILE_OPEN_REPARSE_POINT | _api.FILE_SYNCHRONOUS_IO_NONALERT,
    )
    try:
        _write_file(handle, token.encode("ascii"))
        return handle
    except OSError as exc:
        try:
            close_handle(handle)
        finally:
            delete_lock_file(dir_handle, name)
        raise LockWriteError(exc.errno, str(exc)) from exc


def file_id(handle: int) -> tuple[int, int]:
    info = _api.handle_info(handle)
    attrs = int(info.dwFileAttributes)
    if attrs & _api.FILE_ATTRIBUTE_DIRECTORY or attrs & _api.FILE_ATTRIBUTE_REPARSE_POINT:
        raise OSError(errno.EINVAL, "lock file is non-regular")
    index = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
    return (int(info.dwVolumeSerialNumber), index)


def read_token(handle: int) -> str:
    info = _api.handle_info(handle)
    size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
    if size > _MAX_TOKEN_BYTES:
        raise OSError(errno.EFBIG, "lock token too large")
    return _api.read_file(handle, size).decode("ascii")


def delete_lock_file(dir_handle: int, name: str) -> None:
    try:
        handle = _api.nt_create_relative(
            dir_handle,
            name,
            _api.DELETE | _api.SYNCHRONIZE,
            _api.FILE_SHARE_READ | _api.FILE_SHARE_WRITE | _api.FILE_SHARE_DELETE,
            _api.FILE_OPEN,
            _api.FILE_NON_DIRECTORY_FILE
            | _api.FILE_OPEN_REPARSE_POINT
            | _api.FILE_SYNCHRONOUS_IO_NONALERT
            | _api.FILE_DELETE_ON_CLOSE,
        )
    except FileNotFoundError:
        return
    close_handle(handle)


def close_handle(handle: int) -> None:
    _api.close_handle(handle)


def _write_file(handle: int, data: bytes) -> None:
    _api.write_file(handle, data)
