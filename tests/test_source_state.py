from __future__ import annotations

import hashlib

import pytest

from canon.source_state import (
    SourceStateError,
    SourceStateItem,
    assert_source_state,
    canonical_source_state,
    source_state_sha256,
)


def _sha(hex_char: str) -> str:
    return "sha256:" + hex_char * 64


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


def _hostile_source_digest() -> str:
    raw = (
        b'[{"path":"../escape.md","sha256":"sha256:'
        + b"B" * 64
        + b'","size":true}]\n'
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def test_source_state_digest_is_order_independent() -> None:
    a = SourceStateItem(path="b.md", sha256=_sha("b"), size=2)
    b = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    assert source_state_sha256((a, b)) == source_state_sha256((b, a))


def test_canonical_source_state_uses_deterministic_compact_bytes() -> None:
    a = SourceStateItem(path="b.md", sha256=_sha("b"), size=2)
    b = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    assert canonical_source_state((a, b)) == (
        b'[{"path":"a.md","sha256":"sha256:'
        + b"a" * 64
        + b'","size":1},{"path":"b.md","sha256":"sha256:'
        + b"b" * 64
        + b'","size":2}]\n'
    )


def test_source_state_mismatch_raises_source_changed() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    try:
        assert_source_state(_sha("f"), (item,))
    except SourceStateError as exc:
        assert exc.code == "source_changed"
    else:
        raise AssertionError("expected SourceStateError")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", ""),
        ("path", 123),
        ("path", "a\0b.md"),
        ("path", "a\nb.md"),
        ("path", "../a.md"),
        ("path", "a\\b.md"),
        ("path", "C:/a.md"),
        ("path", "a.md:stream"),
        ("path", "cafe\u0301.md"),
        ("sha256", "sha256:" + "A" * 64),
        ("sha256", "sha256:deadbeef"),
        ("sha256", 123),
        ("size", -1),
        ("size", True),
        ("size", "1"),
    ],
)
def test_source_state_item_rejects_invalid_field_shapes(
    field: str,
    value: object,
) -> None:
    data: dict[str, object] = {"path": "a.md", "sha256": _sha("a"), "size": 1}
    data[field] = value

    with pytest.raises(SourceStateError, match="invalid-source-state-item"):
        SourceStateItem(**data)  # type: ignore[arg-type]


def test_canonical_source_state_rejects_duplicate_normalized_paths() -> None:
    items = (
        SourceStateItem(path="Source.md", sha256=_sha("a"), size=1),
        SourceStateItem(path="source.md", sha256=_sha("b"), size=2),
    )

    with pytest.raises(SourceStateError, match="duplicate-source-path"):
        canonical_source_state(items)


def test_source_state_functions_reject_invalid_argument_shapes() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)

    with pytest.raises(SourceStateError, match="invalid-source-state"):
        canonical_source_state([item])  # type: ignore[arg-type]
    with pytest.raises(SourceStateError, match="invalid-source-state"):
        source_state_sha256((object(),))  # type: ignore[arg-type]
    with pytest.raises(SourceStateError, match="invalid-source-state"):
        assert_source_state(123, (item,))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("path", "../escape.md"),
        ("path", "cafe\u0301.md"),
        ("sha256", "sha256:" + "A" * 64),
        ("sha256", 123),
        ("size", True),
        ("size", -1),
    ],
)
def test_canonical_source_state_revalidates_mutated_items(
    field: str,
    value: object,
) -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)
    object.__setattr__(item, field, value)

    with pytest.raises(SourceStateError, match="invalid-source-state-item"):
        canonical_source_state((item,))


def test_source_state_digest_revalidates_before_serializing_mutated_item() -> None:
    item = SourceStateItem(path="a.md", sha256=_sha("a"), size=1)
    object.__setattr__(item, "sha256", "sha256:deadbeef")

    with pytest.raises(SourceStateError, match="invalid-source-state-item"):
        source_state_sha256((item,))


def test_source_state_rejects_hostile_item_subclass_before_live_reread() -> None:
    with pytest.raises(SourceStateError, match="invalid-source-state"):
        canonical_source_state((_hostile_source_item(),))


def test_assert_source_state_rejects_hostile_item_subclass_matching_digest() -> None:
    with pytest.raises(SourceStateError, match="invalid-source-state"):
        assert_source_state(_hostile_source_digest(), (_hostile_source_item(),))
