from __future__ import annotations

import ctypes
import errno
import os
from ctypes import wintypes
from pathlib import Path

_CREATE_NEW = 1
_DELETE = 0x00010000
_FILE_ATTRIBUTE_DIRECTORY = 0x10
_FILE_ATTRIBUTE_NORMAL = 0x80
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
_FILE_CREATE = 2
_FILE_DELETE_ON_CLOSE = 0x00001000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_NON_DIRECTORY_FILE = 0x40
_FILE_OPEN = 1
_FILE_OPEN_REPARSE_POINT = 0x00200000
_FILE_SHARE_DELETE = 4
_FILE_SHARE_READ = 1
_FILE_SHARE_WRITE = 2
_FILE_SYNCHRONOUS_IO_NONALERT = 0x20
_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_OBJ_CASE_INSENSITIVE = 0x40
_OPEN_EXISTING = 3
_STATUS_OBJECT_NAME_COLLISION = 0xC0000035
_STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
_SYNCHRONIZE = 0x00100000
_ERROR_ALREADY_EXISTS = 183
_ERROR_FILE_EXISTS = 80
_ERROR_FILE_NOT_FOUND = 2
_ERROR_PATH_NOT_FOUND = 3
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

_CloseHandle = None
_CreateFileW = None
_GetFileInformationByHandle = None
_NtCreateFile = None
_RtlNtStatusToDosError = None
_WriteFile = None


class LockWriteError(OSError):
    pass


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class _OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(_UNICODE_STRING)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


class _IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [("Status", ctypes.c_ssize_t), ("Information", ctypes.c_size_t)]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


def supported() -> bool:
    return os.name == "nt" and hasattr(ctypes, "WinDLL")


def open_directory(path: Path) -> int:
    if not supported():
        raise OSError(errno.ENOSYS, "stable Windows lock primitive unavailable")
    handle = _create_file(
        str(path),
        _GENERIC_READ,
        _FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE,
        _OPEN_EXISTING,
        _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
    )
    try:
        attrs = _handle_attributes(handle)
        if not attrs & _FILE_ATTRIBUTE_DIRECTORY or attrs & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise OSError(errno.ELOOP, "lock directory is reparse or non-directory")
        return handle
    except Exception:
        close_handle(handle)
        raise


def create_lock_file(dir_handle: int, name: str, token: str) -> None:
    handle = _nt_create_relative(
        dir_handle,
        name,
        _GENERIC_WRITE | _SYNCHRONIZE,
        _FILE_CREATE,
        _FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
    )
    try:
        _write_file(handle, token.encode("ascii"))
        close_handle(handle)
    except OSError as exc:
        close_handle(handle)
        delete_lock_file(dir_handle, name)
        raise LockWriteError(exc.errno, str(exc)) from exc


def delete_lock_file(dir_handle: int, name: str) -> None:
    try:
        handle = _nt_create_relative(
            dir_handle,
            name,
            _DELETE | _SYNCHRONIZE,
            _FILE_OPEN,
            _FILE_NON_DIRECTORY_FILE
            | _FILE_OPEN_REPARSE_POINT
            | _FILE_SYNCHRONOUS_IO_NONALERT
            | _FILE_DELETE_ON_CLOSE,
        )
    except FileNotFoundError:
        return
    close_handle(handle)


def close_handle(handle: int) -> None:
    _load_api()
    if not _CloseHandle(wintypes.HANDLE(handle)):
        raise _last_error("CloseHandle failed")


def _load_api() -> None:
    global _CloseHandle, _CreateFileW, _GetFileInformationByHandle
    global _NtCreateFile, _RtlNtStatusToDosError, _WriteFile
    if _CreateFileW is not None:
        return
    if not supported():
        raise OSError(errno.ENOSYS, "stable Windows lock primitive unavailable")
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    _CloseHandle = kernel32.CloseHandle
    _CloseHandle.argtypes = [wintypes.HANDLE]
    _CloseHandle.restype = wintypes.BOOL
    _CreateFileW = kernel32.CreateFileW
    _CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _CreateFileW.restype = wintypes.HANDLE
    _GetFileInformationByHandle = kernel32.GetFileInformationByHandle
    _GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)]
    _GetFileInformationByHandle.restype = wintypes.BOOL
    _WriteFile = kernel32.WriteFile
    _WriteFile.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
    _WriteFile.restype = wintypes.BOOL
    _NtCreateFile = ntdll.NtCreateFile
    _NtCreateFile.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_OBJECT_ATTRIBUTES),
        ctypes.POINTER(_IO_STATUS_BLOCK),
        wintypes.LPVOID,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.ULONG,
    ]
    _NtCreateFile.restype = wintypes.LONG
    _RtlNtStatusToDosError = ntdll.RtlNtStatusToDosError
    _RtlNtStatusToDosError.argtypes = [wintypes.LONG]
    _RtlNtStatusToDosError.restype = wintypes.ULONG


def _create_file(path: str, access: int, share: int, disposition: int, flags: int) -> int:
    _load_api()
    handle = _CreateFileW(path, access, share, None, disposition, flags, None)
    if handle == _INVALID_HANDLE_VALUE:
        raise _last_error("CreateFileW failed")
    return int(handle)


def _nt_create_relative(dir_handle: int, name: str, access: int, disposition: int, options: int) -> int:
    _load_api()
    name_obj, name_buffer = _object_name(name)
    attrs = _OBJECT_ATTRIBUTES(
        ctypes.sizeof(_OBJECT_ATTRIBUTES),
        wintypes.HANDLE(dir_handle),
        ctypes.pointer(name_obj),
        _OBJ_CASE_INSENSITIVE,
        None,
        None,
    )
    ios = _IO_STATUS_BLOCK()
    handle = wintypes.HANDLE()
    status = _NtCreateFile(
        ctypes.byref(handle),
        access,
        ctypes.byref(attrs),
        ctypes.byref(ios),
        None,
        _FILE_ATTRIBUTE_NORMAL,
        0,
        disposition,
        options,
        None,
        0,
    )
    _keep_alive(name_buffer)
    if status < 0:
        _raise_nt(status, name)
    return int(handle.value)


def _object_name(name: str) -> tuple[_UNICODE_STRING, ctypes.Array[ctypes.c_wchar]]:
    buffer = ctypes.create_unicode_buffer(name)
    return (
        _UNICODE_STRING(len(name) * 2, ctypes.sizeof(buffer), ctypes.cast(buffer, wintypes.LPWSTR)),
        buffer,
    )


def _raise_nt(status: int, name: str) -> None:
    unsigned = status & 0xFFFFFFFF
    dos = int(_RtlNtStatusToDosError(status))
    if unsigned == _STATUS_OBJECT_NAME_COLLISION or dos in (_ERROR_ALREADY_EXISTS, _ERROR_FILE_EXISTS):
        raise FileExistsError(dos, "lock exists", name)
    if unsigned == _STATUS_OBJECT_NAME_NOT_FOUND or dos in (_ERROR_FILE_NOT_FOUND, _ERROR_PATH_NOT_FOUND):
        raise FileNotFoundError(dos, "lock missing", name)
    raise OSError(dos, f"NtCreateFile failed: 0x{unsigned:08x}", name)


def _write_file(handle: int, data: bytes) -> None:
    _load_api()
    written = wintypes.DWORD()
    buffer = ctypes.create_string_buffer(data)
    ok = _WriteFile(wintypes.HANDLE(handle), buffer, len(data), ctypes.byref(written), None)
    if not ok:
        raise _last_error("WriteFile failed")
    if written.value != len(data):
        raise OSError(errno.EIO, "short lock write")


def _handle_attributes(handle: int) -> int:
    _load_api()
    info = _BY_HANDLE_FILE_INFORMATION()
    ok = _GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(info))
    if not ok:
        raise _last_error("GetFileInformationByHandle failed")
    return int(info.dwFileAttributes)


def _last_error(message: str) -> OSError:
    error = ctypes.get_last_error()
    return OSError(error, message)


def _keep_alive(value: object) -> None:
    if value is None:
        raise AssertionError("unreachable")
