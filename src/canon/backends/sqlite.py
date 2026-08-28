"""backends/sqlite.py -- SqliteBackend: the faithful, audited reference store.

A single SQLite file holds every record verbatim (its canonical to_dict() as
JSON) keyed by (scope, id), and every write is appended to a hash-chained audit
ledger the owner can re-verify -- the same chain discipline flywheel's store
keeps, ported to canon's own table. It holds every kind, loses no field, and
carries the audit chain a FilesBackend drops, so its declared_drops() is empty.
This is the zero-drop backend the round-trip proof (R0) measures the others
against.
"""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from canon.schema import KINDS, Record

from .base import flatten_for_drops, guard_put, record_key

_GENESIS = "0" * 64


class SqliteBackend:
    name = "sqlite"

    def __init__(self, path: "str | Path") -> None:
        self._path = str(path)
        self._init()

    def supported_kinds(self) -> frozenset[str]:
        return frozenset(KINDS)

    def declared_drops(self) -> frozenset[str]:
        return frozenset()

    def flatten(self, record: Record) -> Record:
        return flatten_for_drops(record, self.declared_drops())

    @contextmanager
    def _conn(self) -> Iterator[sqlite3.Connection]:
        c = sqlite3.connect(self._path, timeout=10)
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def _init(self) -> None:
        with self._conn() as c:
            c.executescript(
                "CREATE TABLE IF NOT EXISTS records("
                " key TEXT PRIMARY KEY, scope TEXT, id TEXT, kind TEXT,"
                " envelope TEXT, sha256 TEXT);"
                "CREATE TABLE IF NOT EXISTS audit("
                " seq INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT,"
                " sha256 TEXT, prev_hash TEXT, chain_hash TEXT);")

    def put(self, record: Record) -> None:
        guard_put(self, record)
        key = record_key(record)
        envelope = record.to_json()
        sha = hashlib.sha256(envelope.encode()).hexdigest()
        with self._conn() as c:
            c.execute(
                "INSERT OR REPLACE INTO records"
                "(key, scope, id, kind, envelope, sha256) VALUES(?,?,?,?,?,?)",
                (key, record.scope, record.id, record.kind, envelope, sha))
            self._append_audit(c, key, sha)

    def _append_audit(self, c: sqlite3.Connection, key: str, sha: str) -> None:
        row = c.execute(
            "SELECT chain_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        prev = row[0] if row else _GENESIS
        chain = hashlib.sha256((prev + key + sha).encode()).hexdigest()
        c.execute(
            "INSERT INTO audit(key, sha256, prev_hash, chain_hash)"
            " VALUES(?,?,?,?)", (key, sha, prev, chain))

    def get(self, key: str) -> Record | None:
        with self._conn() as c:
            row = c.execute(
                "SELECT envelope FROM records WHERE key=?", (key,)).fetchone()
        return Record.from_json(row[0]) if row else None

    def records(self) -> list[Record]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT envelope FROM records ORDER BY key").fetchall()
        return [Record.from_json(r[0]) for r in rows]

    def verify_chain(self) -> dict:
        """Walk the audit ledger, recomputing each row's chain hash from the
        prior. Returns {ok, length}; ok is False at the first mismatch."""
        with self._conn() as c:
            rows = c.execute(
                "SELECT key, sha256, prev_hash, chain_hash FROM audit"
                " ORDER BY seq").fetchall()
        prev = _GENESIS
        for key, sha, prev_hash, chain in rows:
            expect = hashlib.sha256((prev + key + sha).encode()).hexdigest()
            if prev_hash != prev or chain != expect:
                return {"ok": False, "length": len(rows)}
            prev = chain
        return {"ok": True, "length": len(rows)}
