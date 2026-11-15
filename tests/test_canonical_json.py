from __future__ import annotations

import hashlib

import pytest

from canon.canonical_json import (
    CANONICALIZATION,
    CanonicalJSONError,
    canonical_json_bytes,
    canonical_json_text,
    canonical_sha256,
    is_sha256_ref,
    sha256_bytes,
    sha256_text,
)


def test_canonical_json_is_compact_sorted_and_lf_terminated():
    got = canonical_json_text({"b": 2, "a": {"d": 4, "c": 3}})
    assert got == '{"a":{"c":3,"d":4},"b":2}\n'
    assert CANONICALIZATION == "json-sorted-compact-lf"


def test_canonical_json_bytes_are_utf8_text_bytes():
    got = canonical_json_bytes({"word": "canon"})
    assert got == b'{"word":"canon"}\n'


def test_canonical_sha256_uses_canonical_bytes():
    expected = hashlib.sha256(b'{"a":1}\n').hexdigest()
    assert canonical_sha256({"a": 1}) == "sha256:" + expected


def test_raw_sha256_helpers_hash_exact_inputs():
    assert sha256_bytes(b"canon\n") == "sha256:" + hashlib.sha256(b"canon\n").hexdigest()
    assert sha256_text("canon\n") == (
        "sha256:" + hashlib.sha256("canon\n".encode("utf-8")).hexdigest()
    )
    assert sha256_text("canon") != sha256_text("canon\n")


def test_sha256_ref_validator_requires_prefixed_lowercase_digest():
    assert is_sha256_ref("sha256:" + "a" * 64)
    assert not is_sha256_ref("a" * 64)
    assert not is_sha256_ref("sha256:" + "A" * 64)
    assert not is_sha256_ref("sha256:deadbeef")


def test_canonical_json_rejects_non_string_keys_and_nan():
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({1: "bad"})
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({"n": float("nan")})
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({"n": float("inf")})
