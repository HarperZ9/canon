"""Read snapshots refresh, refuse concurrent changes, and never open live SQLite."""
import sqlite3

import pytest

from canon import client_mcp_store
from canon.client_mcp import ClientServer
from .test_client_mcp import call, config, event, snapshot


def test_long_running_reader_observes_later_authorized_ingest(tmp_path):
    db = tmp_path / "ctx.db"
    writer = ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    assert call(reader, "query", query="azure")[1]["hits"] == []
    stored = call(writer, "ingest", event=event())[1]
    assert call(reader, "query", query="azure")[1]["hits"]
    assert call(reader, "get", record_id=stored["event_record_id"])[1]["record"]


def test_wal_toggle_after_snapshot_does_not_create_reader_sidecars(tmp_path, monkeypatch):
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    original = sqlite3.connect

    def toggle_before_memory_connect(path, *args, **kwargs):
        assert path == ":memory:"
        external = original(db)
        external.execute("PRAGMA journal_mode=WAL")
        external.close()
        return original(path, *args, **kwargs)

    monkeypatch.setattr(client_mcp_store.sqlite3, "connect", toggle_before_memory_connect)
    assert call(reader, "query", query="azure")[0]["isError"] is False
    assert set(snapshot(tmp_path)) == {"ctx.db"}
    assert call(reader, "health")[0]["isError"] is True


def test_snapshot_size_limit_is_a_refusal(tmp_path, monkeypatch):
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    before = snapshot(tmp_path)
    monkeypatch.setattr(client_mcp_store, "MAX_SNAPSHOT_BYTES", 1)
    with pytest.raises(ValueError, match="at most 256 MiB"):
        ClientServer(config(db))
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
def test_sidecars_refused_without_modification(tmp_path, suffix):
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    (tmp_path / ("ctx.db" + suffix)).write_bytes(b"synthetic external activity")
    before = snapshot(tmp_path)
    with pytest.raises(ValueError, match="idle DELETE-journal"):
        ClientServer(config(db))
    assert snapshot(tmp_path) == before


def test_mutation_during_snapshot_refused(tmp_path, monkeypatch):
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    original = client_mcp_store._no_sidecars
    calls = 0

    def mutate_after_read(path):
        nonlocal calls
        calls += 1
        if calls == 2:
            with path.open("ab") as stream:
                stream.write(b"external concurrent mutation")
        return original(path)

    monkeypatch.setattr(client_mcp_store, "_no_sidecars", mutate_after_read)
    with pytest.raises(ValueError, match="changed during snapshot"):
        ClientServer(config(db))


def test_invalid_snapshot_image_refused_without_modification(tmp_path):
    db = tmp_path / "invalid.db"
    db.write_bytes(b"invalid image!!!!!!!" + b"\x01\x01" + b"x" * 100)
    before = snapshot(tmp_path)
    with pytest.raises((ValueError, sqlite3.Error)):
        ClientServer(config(db))
    assert snapshot(tmp_path) == before
