from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text, sha256_text
from canon.source_state import SourceStateError, SourceStateItem, source_state_sha256
from canon.source_state_cache import SourceStateCache, SourceStateCacheError
import canon.source_state_cache as source_state_cache


def _sha(hex_char: str) -> str:
    return "sha256:" + hex_char * 64


def _cache_key(hex_char: str) -> str:
    return "sha256:" + hex_char * 64


def _digest(cache_key: str) -> str:
    return cache_key.removeprefix("sha256:")


def _item(path: str, hex_char: str, size: int) -> SourceStateItem:
    return SourceStateItem(path=path, sha256=_sha(hex_char), size=size)


def _entry_path(root: Path, key: str) -> Path:
    return root / "bundles" / f"{_digest(key)}.json"


def _write_entry(root: Path, key: str, body: dict[str, object]) -> Path:
    path = _entry_path(root, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json_text(body), encoding="utf-8")
    return path


def _key_kwargs(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "adapter_id": "codex-cli",
        "profile": "bootstrap",
        "budget": "standard",
        "compiler_version": "canon-0",
        "offline": False,
    }
    data.update(overrides)
    return data


def _key_for(
    items: object,
    **overrides: object,
) -> str:
    return SourceStateCache.key_for(  # type: ignore[arg-type]
        items,
        **_key_kwargs(**overrides),  # type: ignore[arg-type]
    )


class _HostileStr(str):
    pass


class _OnePassItems:
    def __init__(self, item: SourceStateItem) -> None:
        self._item = item
        self.reads = 0

    def __iter__(self) -> Iterator[SourceStateItem]:
        self.reads += 1
        if self.reads == 1:
            return iter((self._item,))
        return iter((object(),))  # type: ignore[arg-type]


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


def test_key_for_is_portable_deterministic_and_uses_security_digest(
    tmp_path: Path,
) -> None:
    first = (_item("b.md", "b", 2), _item("a.md", "a", 1))
    second = (_item("a.md", "a", 1), _item("b.md", "b", 2))
    expected_payload = {
        "adapter_id": "codex-cli",
        "budget": "standard",
        "compiler_version": "canon-0",
        "offline": False,
        "profile": "bootstrap",
        "source_state_sha256": source_state_sha256(first),
    }
    expected = sha256_text(canonical_json_text(expected_payload))

    assert _key_for(list(first)) == expected
    assert _key_for(second) == expected
    assert SourceStateCache(tmp_path / "one").key_for(first, **_key_kwargs()) == expected
    assert SourceStateCache(tmp_path / "two").key_for(first, **_key_kwargs()) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("adapter_id", "relay"),
        ("profile", "release"),
        ("budget", "tiny"),
        ("compiler_version", "canon-1"),
        ("offline", True),
    ],
)
def test_key_for_is_sensitive_to_compilation_dimensions(
    field: str,
    value: object,
) -> None:
    items = (_item("a.md", "a", 1),)

    assert _key_for(items, **{field: value}) != _key_for(items)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("adapter_id", _HostileStr("codex-cli")),
        ("profile", _HostileStr("bootstrap")),
        ("budget", _HostileStr("standard")),
        ("compiler_version", _HostileStr("canon-0")),
        ("offline", 0),
        ("offline", _HostileStr("false")),
    ],
)
def test_key_for_rejects_non_exact_dimension_types(
    field: str,
    value: object,
) -> None:
    with pytest.raises(SourceStateCacheError, match="invalid-cache-dimension"):
        _key_for((_item("a.md", "a", 1),), **{field: value})


def test_key_for_snapshots_source_sequence_before_security_digest() -> None:
    source_items = _OnePassItems(_item("a.md", "a", 1))
    expected = _key_for((_item("a.md", "a", 1),))

    assert _key_for(source_items) == expected
    assert source_items.reads == 1


def test_assert_current_preserves_source_state_error_code() -> None:
    current = [_item("a.md", "a", 1)]

    SourceStateCache.assert_current(source_state_sha256(tuple(current)), current)
    with pytest.raises(SourceStateError) as raised:
        SourceStateCache.assert_current(_sha("f"), current)
    assert raised.value.code == "source_changed"


def test_put_get_and_current_use_canonical_json_and_snapshot_bundle(
    tmp_path: Path,
) -> None:
    cache = SourceStateCache(tmp_path / "cache")
    key = _cache_key("a")
    bundle = {"z": [{"n": 1}], "a": "first"}

    path = cache.put(key, bundle)
    bundle["z"][0]["n"] = 99  # type: ignore[index]
    expected = {"a": "first", "z": [{"n": 1}]}

    assert path == (tmp_path / "cache" / "bundles" / f"{_digest(key)}.json").resolve()
    assert path.read_text(encoding="utf-8") == canonical_json_text(expected)
    assert (tmp_path / "cache" / "current.json").read_text(
        encoding="utf-8",
    ) == canonical_json_text({"cache_key": key})
    assert cache.get(key) == expected
    assert cache.current() == expected


def test_missing_entry_and_current_pointer_return_none(tmp_path: Path) -> None:
    cache = SourceStateCache(tmp_path / "cache")

    assert cache.get(_cache_key("0")) is None
    assert cache.current() is None


def test_broken_symlink_cache_root_is_not_treated_as_a_miss(tmp_path: Path) -> None:
    root = tmp_path / "cache-link"
    try:
        root.symlink_to(tmp_path / "missing-target", target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).get(_cache_key("0"))
    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).current()


def test_get_rejects_non_directory_bundle_parent_as_corruption(tmp_path: Path) -> None:
    root = tmp_path / "cache"
    root.mkdir()
    (root / "bundles").write_text("not a directory", encoding="utf-8")

    with pytest.raises(SourceStateCacheError, match="nonregular-cache-directory"):
        SourceStateCache(root).get(_cache_key("0"))


@pytest.mark.parametrize(
    "bad_key",
    [
        "",
        "sha256:" + "A" * 64,
        "sha256:" + "a" * 63,
        "sha256:" + "a" * 64 + "/escape",
        "sha256:" + "a" * 64 + ":stream",
        "../sha256:" + "a" * 64,
        "sha256:%2e%2e",
        _HostileStr("sha256:" + "a" * 64),
    ],
)
def test_invalid_cache_keys_are_rejected_before_io(
    tmp_path: Path,
    bad_key: str,
) -> None:
    root = tmp_path / "missing-cache"
    cache = SourceStateCache(root)

    with pytest.raises(SourceStateCacheError, match="invalid-cache-key"):
        cache.get(bad_key)
    with pytest.raises(SourceStateCacheError, match="invalid-cache-key"):
        cache.put(bad_key, {"ok": True})
    assert not root.exists()


@pytest.mark.parametrize(
    "text",
    [
        "{bad-json\n",
        "[]\n",
        '{"b":2,"a":1}\n',
    ],
)
def test_get_rejects_corrupt_non_object_and_noncanonical_entries(
    tmp_path: Path,
    text: str,
) -> None:
    key = _cache_key("b")
    path = tmp_path / "cache" / "bundles" / f"{_digest(key)}.json"
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")

    with pytest.raises(SourceStateCacheError, match="corrupt-cache-entry"):
        SourceStateCache(tmp_path / "cache").get(key)


@pytest.mark.parametrize(
    "text",
    [
        "[]\n",
        canonical_json_text({"cache_key": _cache_key("C")}),
    ],
)
def test_current_rejects_malformed_current_pointer(tmp_path: Path, text: str) -> None:
    root = tmp_path / "cache"
    root.mkdir()
    (root / "current.json").write_text(text, encoding="utf-8")

    with pytest.raises(SourceStateCacheError, match="corrupt-cache-entry"):
        SourceStateCache(root).current()


def test_get_rejects_symlink_cache_entry_before_read(tmp_path: Path) -> None:
    key = _cache_key("c")
    root = tmp_path / "cache"
    target = root / "bundles" / f"{_digest(key)}.json"
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text(canonical_json_text({"outside": True}), encoding="utf-8")
    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")

    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).get(key)


def test_get_rejects_entry_swapped_to_symlink_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "cache"
    key = _cache_key("6")
    target = _write_entry(root, key, {"inside": True})
    outside = tmp_path / "outside-entry.json"
    outside.write_text(canonical_json_text({"outside": True}), encoding="utf-8")
    real_regular = source_state_cache._regular_file_or_missing
    swapped = False

    def swap_after_lstat(path: Path, *, role: str) -> bool:
        nonlocal swapped
        exists = real_regular(path, role=role)
        if path == target.resolve() and role == "cache-entry" and not swapped:
            swapped = True
            path.unlink()
            path.symlink_to(outside)
        return exists

    monkeypatch.setattr(
        source_state_cache,
        "_regular_file_or_missing",
        swap_after_lstat,
    )

    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).get(key)
    assert swapped


def test_current_rejects_pointer_swapped_to_symlink_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "cache"
    first = _cache_key("7")
    second = _cache_key("8")
    _write_entry(root, first, {"version": 1})
    _write_entry(root, second, {"version": 2})
    current = root / "current.json"
    current.write_text(canonical_json_text({"cache_key": first}), encoding="utf-8")
    outside = tmp_path / "outside-current.json"
    outside.write_text(canonical_json_text({"cache_key": second}), encoding="utf-8")
    real_regular = source_state_cache._regular_file_or_missing
    swapped = False

    def swap_after_lstat(path: Path, *, role: str) -> bool:
        nonlocal swapped
        exists = real_regular(path, role=role)
        if path == current.resolve() and role == "current-pointer" and not swapped:
            swapped = True
            path.unlink()
            path.symlink_to(outside)
        return exists

    monkeypatch.setattr(
        source_state_cache,
        "_regular_file_or_missing",
        swap_after_lstat,
    )

    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).current()
    assert swapped


def test_put_rejects_symlink_bundle_directory_escape(tmp_path: Path) -> None:
    root = tmp_path / "cache"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "bundles").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(SourceStateCacheError, match="unsafe-cache-path"):
        SourceStateCache(root).put(_cache_key("d"), {"ok": True})
    assert list(outside.iterdir()) == []


def test_put_does_not_follow_bundle_parent_swapped_before_temp_create(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "cache"
    outside = tmp_path / "outside-bundles"
    displaced = tmp_path / "displaced-bundles"
    outside.mkdir()
    key = _cache_key("9")
    real_named_temp = source_state_cache.tempfile.NamedTemporaryFile
    attempted = False

    def swap_before_temp(*args: object, **kwargs: object) -> object:
        nonlocal attempted
        directory = Path(kwargs["dir"])  # type: ignore[index]
        if directory.name == "bundles" and not attempted:
            attempted = True
            _swap_dir_to_symlink(directory, outside, displaced)
        return real_named_temp(*args, **kwargs)

    monkeypatch.setattr(source_state_cache.tempfile, "NamedTemporaryFile", swap_before_temp)

    SourceStateCache(root).put(key, {"version": 1})
    assert attempted
    assert not (outside / f"{_digest(key)}.json").exists()
    assert SourceStateCache(root).current() == {"version": 1}


def test_put_does_not_follow_cache_root_swapped_before_current_temp_create(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "cache"
    outside = tmp_path / "outside-root"
    displaced = tmp_path / "displaced-root"
    outside.mkdir()
    key = _cache_key("a")
    real_named_temp = source_state_cache.tempfile.NamedTemporaryFile
    attempted = False

    def swap_before_current_temp(*args: object, **kwargs: object) -> object:
        nonlocal attempted
        directory = Path(kwargs["dir"])  # type: ignore[index]
        if directory == root.resolve() and not attempted:
            attempted = True
            _swap_dir_to_symlink(directory, outside, displaced)
        return real_named_temp(*args, **kwargs)

    monkeypatch.setattr(
        source_state_cache.tempfile,
        "NamedTemporaryFile",
        swap_before_current_temp,
    )

    SourceStateCache(root).put(key, {"version": 1})
    assert attempted
    assert not (outside / "current.json").exists()
    assert SourceStateCache(root).current() == {"version": 1}


def test_put_retries_temp_name_collision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if source_state_cache.os.name != "nt":
        pytest.skip("tempfile retry probe covers the Windows path backend")
    cache = SourceStateCache(tmp_path / "cache")
    real_named_temp = source_state_cache.tempfile.NamedTemporaryFile
    calls = 0

    def collide_once(*args: object, **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise FileExistsError("synthetic temp collision")
        return real_named_temp(*args, **kwargs)

    monkeypatch.setattr(source_state_cache.tempfile, "NamedTemporaryFile", collide_once)

    cache.put(_cache_key("b"), {"version": 1})
    assert calls >= 2
    assert cache.current() == {"version": 1}


def test_put_rejects_nonregular_existing_bundle_target(tmp_path: Path) -> None:
    key = _cache_key("e")
    target = tmp_path / "cache" / "bundles" / f"{_digest(key)}.json"
    target.mkdir(parents=True)

    with pytest.raises(SourceStateCacheError, match="nonregular-cache-entry"):
        SourceStateCache(tmp_path / "cache").put(key, {"ok": True})


def test_put_does_not_advance_current_when_bundle_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = SourceStateCache(tmp_path / "cache")
    first = _cache_key("1")
    second = _cache_key("2")
    cache.put(first, {"version": 1})
    second_path = (tmp_path / "cache" / "bundles" / f"{_digest(second)}.json").resolve()
    real_replace = source_state_cache.os.replace

    def fail_bundle_replace(src: object, dst: object) -> None:
        if Path(dst) == second_path:
            raise OSError("synthetic bundle failure")
        real_replace(src, dst)

    monkeypatch.setattr(source_state_cache.os, "replace", fail_bundle_replace)

    with pytest.raises(SourceStateCacheError, match="write-cache-entry"):
        cache.put(second, {"version": 2})
    assert cache.current() == {"version": 1}
    assert not second_path.exists()
    assert list((tmp_path / "cache" / "bundles").glob("*.tmp")) == []


def test_put_writes_bundle_before_current_and_preserves_old_pointer_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = SourceStateCache(tmp_path / "cache")
    first = _cache_key("3")
    second = _cache_key("4")
    cache.put(first, {"version": 1})
    current_path = (tmp_path / "cache" / "current.json").resolve()
    real_replace = source_state_cache.os.replace

    def fail_current_replace(src: object, dst: object) -> None:
        if Path(dst) == current_path:
            raise OSError("synthetic current failure")
        real_replace(src, dst)

    monkeypatch.setattr(source_state_cache.os, "replace", fail_current_replace)

    with pytest.raises(SourceStateCacheError, match="write-current-pointer"):
        cache.put(second, {"version": 2})
    assert cache.get(second) == {"version": 2}
    assert cache.current() == {"version": 1}
    assert list((tmp_path / "cache").glob("*.tmp")) == []
