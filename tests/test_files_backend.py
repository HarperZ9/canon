"""FilesBackend: one JSON file per record, field-identical, temporal kept.

A files store loses no record field -- every kind round-trips byte-for-byte
through the on-disk envelope, including live temporal history. Its single
declared drop, audit-chain, is structural: it is documented, but because no lone
record can exercise it, a put never raises for it.
"""
from __future__ import annotations

from dataclasses import replace
from urllib.parse import quote

import pytest

from canon.backends import CAP_AUDIT_CHAIN, FilesBackend, InvalidKey, InvalidRecord, record_key
from canon.schema import KINDS

from ._helpers import RECORD_FILES, load_dict, load_record


@pytest.mark.parametrize("kind", list(RECORD_FILES))
def test_roundtrip_is_field_identical(tmp_path, kind: str) -> None:
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES[kind])
    be.put(rec)
    got = be.get(record_key(rec))
    assert got is not None
    assert got.to_dict() == load_dict(RECORD_FILES[kind])


def test_declared_drops_is_audit_chain_only(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    assert be.declared_drops() == frozenset({CAP_AUDIT_CHAIN})


def test_supports_every_kind(tmp_path) -> None:
    assert FilesBackend(tmp_path).supported_kinds() == frozenset(KINDS)


def test_temporal_history_survives(tmp_path) -> None:
    # files does not drop temporal, so a superseding record keeps its pointer.
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES["synthesized-persona-l3"])
    be.put(rec)
    got = be.get(record_key(rec))
    assert got.temporal is not None
    assert got.temporal.supersedes == "persona-operator-0003"


def test_get_missing_returns_none(tmp_path) -> None:
    assert FilesBackend(tmp_path).get("global/nope") is None


def test_structural_drop_never_blocks_put(tmp_path) -> None:
    # audit-chain is dropped but not record-enforceable: put must not raise.
    be = FilesBackend(tmp_path)
    be.put(load_record(RECORD_FILES["adr-decision"]))  # no DropError


def test_records_enumerates_all_scopes(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    for kind in RECORD_FILES:
        be.put(load_record(RECORD_FILES[kind]))
    got = be.records()
    assert len(got) == len(RECORD_FILES)
    assert {r.kind for r in got} == set(RECORD_FILES)


def test_scope_lands_in_its_own_subdirectory(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    be.put(load_record(RECORD_FILES["episodic-memory"]))     # scope=global
    be.put(load_record(RECORD_FILES["personality-block"]))   # scope=workspace
    assert (tmp_path / "global").is_dir()
    assert (tmp_path / "workspace").is_dir()


def test_reload_from_disk_is_independent(tmp_path) -> None:
    # A fresh backend over the same root reads what the first one wrote.
    FilesBackend(tmp_path).put(load_record(RECORD_FILES["adr-decision"]))
    rec = load_record(RECORD_FILES["adr-decision"])
    got = FilesBackend(tmp_path).get(record_key(rec))
    assert got is not None and got.to_dict() == load_dict(RECORD_FILES["adr-decision"])


def test_put_invalid_scope_refuses_before_creating_outside_file(tmp_path) -> None:
    be = FilesBackend(tmp_path / "store")
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope="..", id="escape")

    with pytest.raises(InvalidRecord, match="unknown scope"):
        be.put(rec)

    assert not (tmp_path / "escape.json").exists()
    assert not (tmp_path / "store").exists()


@pytest.mark.parametrize("scope", ["../x", "global/../../x", "C:/tmp", "C:\\tmp", "repo"])
def test_put_rejects_path_shaped_scopes_without_writing(tmp_path, scope: str) -> None:
    be = FilesBackend(tmp_path / "store")
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope=scope, id="safe-id")

    with pytest.raises(InvalidRecord):
        be.put(rec)

    assert not (tmp_path / "store").exists()


@pytest.mark.parametrize("key", ["../escape", "repo/x", "C:/tmp/x", "C:\\tmp\\x"])
def test_get_invalid_key_refuses_before_path_lookup(tmp_path, key: str) -> None:
    with pytest.raises(InvalidKey):
        FilesBackend(tmp_path).get(key)


def test_records_ignores_unknown_scope_directories(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES["episodic-memory"])
    rogue = tmp_path / "repo"
    rogue.mkdir()
    (rogue / (quote(rec.id, safe="") + ".json")).write_text(rec.to_json(), encoding="utf-8")

    assert be.records() == []


def test_records_rejects_path_scope_mismatch(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES["episodic-memory"])
    scope_dir = tmp_path / "workspace"
    scope_dir.mkdir()
    (scope_dir / (quote(rec.id, safe="") + ".json")).write_text(rec.to_json(), encoding="utf-8")

    with pytest.raises(InvalidRecord, match="path scope"):
        be.records()
