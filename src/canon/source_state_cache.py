from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
import os
from pathlib import Path
import stat
import tempfile

from .canonical_json import CanonicalJSONError, canonical_json_text, sha256_text
from .path_policy import PathPolicyError, resolve_under_root
from .source_state import (
    SourceStateError,
    SourceStateItem,
    assert_source_state,
    source_state_sha256,
)

_CACHE_PREFIX = "sha256:"
_HEX = frozenset("0123456789abcdef")
_BUNDLES = "bundles"
_CURRENT = "current.json"


class SourceStateCacheError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class SourceStateCache:
    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)

    @staticmethod
    def key_for(
        source_items: Sequence[SourceStateItem],
        *,
        adapter_id: str,
        profile: str,
        budget: str,
        compiler_version: str,
        offline: bool,
    ) -> str:
        payload = {
            "adapter_id": _exact_text("adapter_id", adapter_id),
            "budget": _exact_text("budget", budget),
            "compiler_version": _exact_text("compiler_version", compiler_version),
            "offline": _exact_bool("offline", offline),
            "profile": _exact_text("profile", profile),
            "source_state_sha256": source_state_sha256(_snapshot_items(source_items)),
        }
        return sha256_text(canonical_json_text(payload))

    @staticmethod
    def assert_current(
        expected_sha256: str,
        current_items: Sequence[SourceStateItem],
    ) -> None:
        assert_source_state(expected_sha256, _snapshot_items(current_items))

    def get(self, cache_key: str) -> dict[str, object] | None:
        digest = _cache_digest(cache_key)
        if self._root_missing():
            return None
        path = self._entry_path(digest)
        if not _directory_or_missing(path.parent, role="cache-directory"):
            return None
        exists = _regular_file_or_missing(path, role="cache-entry")
        if not exists:
            return None
        return _read_canonical_object(path)

    def put(self, cache_key: str, bundle: object) -> Path:
        digest = _cache_digest(cache_key)
        data = _snapshot_bundle(bundle)
        text = _canonical_text(data, code="invalid-cache-bundle")
        pointer = _canonical_text({"cache_key": cache_key}, code="invalid-cache-bundle")

        self._ensure_root()
        bundle_dir = self._ensure_bundle_dir()
        path = self._entry_path(digest)
        if path.parent != bundle_dir:
            raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe")
        _write_atomic(path, text, code="write-cache-entry")
        _write_atomic(self._current_path(), pointer, code="write-current-pointer")
        return path

    def current(self) -> dict[str, object] | None:
        if self._root_missing():
            return None
        path = self._current_path()
        exists = _regular_file_or_missing(path, role="current-pointer")
        if not exists:
            return None
        pointer = _read_canonical_object(path)
        key = _current_key(pointer)
        current = self.get(key)
        if current is None:
            raise SourceStateCacheError("missing-current-entry", "current entry is missing")
        return current

    def _entry_path(self, digest: str) -> Path:
        return self._safe_path(Path(_BUNDLES) / f"{digest}.json")

    def _current_path(self) -> Path:
        return self._safe_path(_CURRENT)

    def _ensure_root(self) -> None:
        try:
            self._root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SourceStateCacheError("invalid-cache-root", "cache root is invalid") from exc
        self._safe_path(_CURRENT)

    def _ensure_bundle_dir(self) -> Path:
        path = self._safe_path(_BUNDLES)
        try:
            path.mkdir(exist_ok=True)
        except OSError as exc:
            raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe") from exc
        path = self._safe_path(_BUNDLES)
        if not path.is_dir():
            raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe")
        return path

    def _safe_path(self, relative: str | Path) -> Path:
        try:
            return resolve_under_root(relative, root=self._root)
        except PathPolicyError as exc:
            raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe") from exc

    def _root_missing(self) -> bool:
        try:
            return not self._root.exists() and not self._root.is_symlink()
        except OSError:
            return False


def _snapshot_items(items: object) -> tuple[SourceStateItem, ...]:
    try:
        return tuple(items)  # type: ignore[arg-type]
    except Exception as exc:
        raise SourceStateError("invalid-source-state", "items must be a sequence") from exc


def _exact_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise SourceStateCacheError("invalid-cache-dimension", f"{name} has invalid type")
    return value


def _exact_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise SourceStateCacheError("invalid-cache-dimension", f"{name} has invalid type")
    return value


def _cache_digest(cache_key: object) -> str:
    if type(cache_key) is not str:
        _invalid_cache_key()
    if not cache_key.startswith(_CACHE_PREFIX) or len(cache_key) != 71:
        _invalid_cache_key()
    digest = cache_key[len(_CACHE_PREFIX):]
    if any(ch not in _HEX for ch in digest):
        _invalid_cache_key()
    return digest


def _invalid_cache_key() -> None:
    raise SourceStateCacheError(
        "invalid-cache-key",
        "cache key must be sha256:<64 lowercase hex>",
    )


def _snapshot_bundle(bundle: object) -> dict[str, object]:
    try:
        value = _snapshot_json(bundle)
    except SourceStateCacheError:
        raise
    except Exception as exc:
        raise SourceStateCacheError("invalid-cache-bundle", "bundle is invalid") from exc
    if type(value) is not dict:
        raise SourceStateCacheError("invalid-cache-bundle", "bundle must be a JSON object")
    return value


def _snapshot_json(value: object) -> object:
    if isinstance(value, Mapping):
        out: dict[str, object] = {}
        for key, item in tuple(value.items()):
            if type(key) is not str or key in out:
                raise SourceStateCacheError("invalid-cache-bundle", "bundle is invalid")
            out[key] = _snapshot_json(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_snapshot_json(item) for item in tuple(value)]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise SourceStateCacheError("invalid-cache-bundle", "bundle is invalid")


def _canonical_text(value: dict[str, object], *, code: str) -> str:
    try:
        return canonical_json_text(value)
    except CanonicalJSONError as exc:
        raise SourceStateCacheError(code, "bundle is invalid") from exc


def _regular_file_or_missing(path: Path, *, role: str) -> bool:
    try:
        st = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe") from exc
    if not stat.S_ISREG(st.st_mode):
        raise SourceStateCacheError(f"nonregular-{role}", "cache path is not a regular file")
    return True


def _directory_or_missing(path: Path, *, role: str) -> bool:
    try:
        st = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise SourceStateCacheError("unsafe-cache-path", "cache path is unsafe") from exc
    if not stat.S_ISDIR(st.st_mode):
        raise SourceStateCacheError(f"nonregular-{role}", "cache path is not a directory")
    return True


def _read_canonical_object(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt") from exc
    if type(value) is not dict:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    if text != _canonical_text(value, code="corrupt-cache-entry"):
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    return value


def _current_key(pointer: dict[str, object]) -> str:
    if set(pointer) != {"cache_key"}:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    try:
        _cache_digest(pointer["cache_key"])
    except SourceStateCacheError as exc:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt") from exc
    return pointer["cache_key"]  # type: ignore[return-value]


def _write_atomic(target: Path, text: str, *, code: str) -> None:
    _regular_file_or_missing(target, role="cache-entry")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except OSError as exc:
        _cleanup_temp(temp_path)
        raise SourceStateCacheError(code, "cache write failed") from exc


def _cleanup_temp(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
