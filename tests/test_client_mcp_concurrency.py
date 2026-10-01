"""A read-only client against a store another process is changing.

The read path must not create a sidecar file next to the store, must not fail
while a writer holds a transaction or changes the journal mode, and must show a
long-running reader the records an authorized writer stores later.
"""
import sqlite3
import threading
import time

import pytest

from canon import client_mcp_store
from canon.client_mcp import ClientServer
from .test_client_mcp import call, config, snapshot


def numbered_event(n):
    return {"event_id": f"turn-{n}", "source_app": "synthetic-client",
            "session_id": "synthetic-session", "native_id": f"source-turn-{n}",
            "message_text": f"Persist the azure telescope decision number {n}.",
            "extractions": [{"text": "azure telescope", "source_id": "message"}]}


def held_wal_connection(db):
    """An external connection that keeps WAL frames uncheckpointed while open."""
    conn = sqlite3.connect(db, timeout=10)
    assert conn.execute("PRAGMA journal_mode=WAL").fetchone()[0] == "wal"
    conn.execute("PRAGMA wal_autocheckpoint=0")
    conn.execute("SELECT count(*) FROM sqlite_master").fetchone()  # opens the WAL index
    return conn


def test_wal_store_with_uncheckpointed_commits_reads_without_new_files(tmp_path):
    db = tmp_path / "ctx.db"
    writer = ClientServer(config(db, "--allow-context-write"))
    external = held_wal_connection(db)
    try:
        stored = call(writer, "ingest", event=numbered_event(1))[1]
        assert (tmp_path / "ctx.db-wal").stat().st_size > 0
        before = snapshot(tmp_path)
        reader = ClientServer(config(db))
        response, found = call(reader, "query", query="azure")
        assert response["isError"] is False
        assert found["hits"]
        assert call(reader, "get", record_id=stored["event_record_id"])[1]["record"]
        assert call(reader, "health")[1]["ok"] is True
        assert snapshot(tmp_path) == before
    finally:
        external.close()


def test_running_reader_sees_later_writes_across_journal_mode_changes(tmp_path):
    db = tmp_path / "ctx.db"
    writer = ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    ids = []
    for n, mode in enumerate(["wal", "delete", "wal", "delete"], start=1):
        with sqlite3.connect(db, timeout=10) as conn:
            assert conn.execute(f"PRAGMA journal_mode={mode}").fetchone()[0] == mode
        conn.close()
        ids.append(call(writer, "ingest", event=numbered_event(n))[1]["event_record_id"])
        for record_id in ids:
            response, got = call(reader, "get", record_id=record_id)
            assert response["isError"] is False, (mode, got)
            assert got["record"]["id"] == record_id
    assert set(snapshot(tmp_path)) == {"ctx.db"}


def test_concurrent_journal_mode_changes_never_fail_the_reader(tmp_path, monkeypatch):
    db = tmp_path / "ctx.db"
    writer = ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    stop, failures, stored = threading.Event(), [], []

    def churn():
        try:
            for n in range(1, 13):
                mode = "wal" if n % 2 else "delete"
                conn = sqlite3.connect(db, timeout=10)
                conn.execute(f"PRAGMA journal_mode={mode}").fetchone()
                conn.close()
                stored.append(call(writer, "ingest", event=numbered_event(n))[1])
        except Exception as exc:  # surfaced through the assertion below
            failures.append(("writer", repr(exc)))
        finally:
            stop.set()

    thread = threading.Thread(target=churn)
    thread.start()
    reads = 0
    while not stop.is_set() or reads < 5:
        response, body = call(reader, "query", query="azure")
        if response["isError"]:
            failures.append(("reader", body))
        reads += 1
    thread.join()
    assert failures == []
    assert len(stored) == 12
    for item in stored:
        response, got = call(reader, "get", record_id=item["event_record_id"])
        assert response["isError"] is False and got["record"]
    assert set(snapshot(tmp_path)) == {"ctx.db"}


def test_an_open_writer_transaction_does_not_fail_the_reader(tmp_path):
    # Before commit SQLite leaves the journal header zeroed and the database
    # file untouched, so the reader may copy the committed state at once.
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    holder = sqlite3.connect(db, timeout=10, isolation_level=None, check_same_thread=False)
    holder.execute("BEGIN IMMEDIATE")
    holder.execute("CREATE TABLE in_flight_transaction(value TEXT)")
    assert (tmp_path / "ctx.db-journal").exists()
    try:
        response, body = call(reader, "query", query="azure")
    finally:
        holder.execute("ROLLBACK")
        holder.close()
    assert response["isError"] is False, body
    assert set(snapshot(tmp_path)) == {"ctx.db"}


def test_reader_waits_out_a_committing_writer(tmp_path):
    # A journal with a live header means the database file may be half
    # written; the reader retries until the writer finishes.
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    reader = ClientServer(config(db))
    journal = tmp_path / "ctx.db-journal"
    journal.write_bytes(b"\xd9\xd5\x05\xf9 synthetic committing writer")
    timer = threading.Timer(0.3, journal.unlink)
    started = time.monotonic()
    timer.start()
    try:
        response, body = call(reader, "query", query="azure")
    finally:
        timer.join()
    assert response["isError"] is False, body
    assert time.monotonic() - started >= 0.3
    assert set(snapshot(tmp_path)) == {"ctx.db"}


def test_a_journal_that_stays_hot_is_refused_without_modification(tmp_path, monkeypatch):
    db = tmp_path / "ctx.db"
    ClientServer(config(db, "--allow-context-write"))
    (tmp_path / "ctx.db-journal").write_bytes(b"\xd9\xd5\x05\xf9 synthetic hot journal")
    before = snapshot(tmp_path)
    monkeypatch.setattr(client_mcp_store, "SNAPSHOT_RETRY_SECONDS", 0.2)
    started = time.monotonic()
    with pytest.raises(ValueError, match="busy"):
        ClientServer(config(db))
    assert time.monotonic() - started < 5
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("suffix", ["-wal", "-shm"])
def test_stray_wal_sidecars_beside_a_delete_mode_store_are_read_past(tmp_path, suffix):
    db = tmp_path / "ctx.db"
    writer = ClientServer(config(db, "--allow-context-write"))
    stored = call(writer, "ingest", event=numbered_event(1))[1]
    (tmp_path / ("ctx.db" + suffix)).write_bytes(b"synthetic external activity")
    before = snapshot(tmp_path)
    reader = ClientServer(config(db))
    assert call(reader, "get", record_id=stored["event_record_id"])[1]["record"]
    assert snapshot(tmp_path) == before
