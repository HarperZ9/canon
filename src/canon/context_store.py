"""Shared context operations over Canon's existing audited SQLite record store."""
from __future__ import annotations

import hashlib
import re
import secrets
from pathlib import Path

from .backends.base import record_key
from .backends.sqlite import SqliteBackend
from .context_query import search
from .context_records import LIMITS, make_records, scope
from .schema import Record


class ContextCollision(ValueError):
    """The same observed event identity was submitted with different content."""


class ContextIntegrityError(ValueError):
    """A stored record no longer matches its audit-bound payload."""


class ContextStoreIdentityError(ValueError):
    """The caller's bound store identity does not match this Canon store."""


_META_TABLE = "context_store_meta"
_VERSION_TABLE = "context_store_identity_version"
_STORE_ID_KEY = "store_id"
_VERSION_KEY = "schema_version"
_IDENTITY_VERSION = "1"
_STORE_ID = re.compile(r"ctxstore_[0-9a-f]{32}\Z")


class ContextStore:
    def __init__(self, path):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError("context database path must be absolute")
        self._backend = SqliteBackend(path)

    def identity(self):
        with self._backend._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            return self._store_id(conn, create=True)

    def ingest(self, payload, expected_store_id=None):
        expected = _expected_store_id(expected_store_id)
        records = make_records(payload)
        with self._backend._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            store_id = self._store_id(conn, create=True)
            _compare_store_id(store_id, expected)
            self._verified_rows(conn)
            existing = conn.execute("SELECT envelope, sha256 FROM records WHERE key=?",
                                    (record_key(records[0]),)).fetchone()
            if existing:
                self._verify_row(conn, record_key(records[0]), *existing)
                if existing[0] != records[0].to_json():
                    raise ContextCollision("event identity already exists with different content")
                for record in records[1:]:
                    key = record_key(record)
                    row = conn.execute("SELECT envelope,sha256 FROM records WHERE key=?", (key,)).fetchone()
                    if not row or row[0] != record.to_json():
                        raise ContextIntegrityError("captured event has missing or changed derived records")
                    self._verify_row(conn, key, *row)
                return self._ingest_result(records, "already_present", 0, store_id)
            for record in records:
                envelope = record.to_json()
                digest = hashlib.sha256(envelope.encode()).hexdigest()
                key = record_key(record)
                conn.execute("INSERT INTO records(key,scope,id,kind,envelope,sha256) VALUES(?,?,?,?,?,?)",
                             (key, record.scope, record.id, record.kind, envelope, digest))
                self._backend._append_audit(conn, key, digest)
        return self._ingest_result(records, "stored", len(records), store_id)

    @staticmethod
    def _ingest_result(records, status, count, store_id):
        return {"schema": "canon.context-ingest/v1", "status": status,
                "event_record_id": records[0].id, "records_stored": count,
                "source_hash": records[0].provenance.source_hash, "store_id": store_id,
                "does_not_prove": list(LIMITS)}

    @staticmethod
    def _verify_row(conn, key, envelope, digest):
        expected = hashlib.sha256(envelope.encode()).hexdigest()
        row = conn.execute("SELECT sha256 FROM audit WHERE key=? ORDER BY seq DESC LIMIT 1",
                           (key,)).fetchone()
        if expected != digest or not row or row[0] != digest:
            raise ContextIntegrityError("stored context payload integrity failed")

    def _records(self, workspace, project, expected_store_id=None):
        result = []
        with self._backend._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            store_id = self._store_id(conn, create=True)
            _compare_store_id(store_id, _expected_store_id(expected_store_id))
            rows = self._verified_rows(conn)
            for key, envelope, digest in rows:
                try:
                    rec = Record.from_json(envelope)
                except Exception as exc:
                    raise ContextIntegrityError("context store integrity failed") from exc
                if (rec.data.get("workspace_id"), rec.data.get("project_id")) != (workspace, project):
                    continue
                if not rec.data.get("event_record_id"):
                    continue
                result.append(rec)
        return result, store_id

    def query(self, workspace_id, project_id, query, top_k=5, include_pending=True,
              expected_store_id=None, include_related=False, related_limit=5):
        workspace, project = scope(workspace_id, project_id)
        records, store_id = self._records(workspace, project, expected_store_id)
        result = search(records, workspace, project, query, top_k, include_pending,
                        include_related=include_related, related_limit=related_limit)
        result["store_id"] = store_id
        return result

    def get(self, workspace_id, project_id, record_id, expected_store_id=None):
        workspace, project = scope(workspace_id, project_id)
        records, store_id = self._records(workspace, project, expected_store_id)
        for rec in records:
            if rec.id == record_id:
                return {"status": "found_in_searched_sources", "record_key": record_key(rec), "record": rec.to_dict(),
                        "store_id": store_id, "does_not_prove": list(LIMITS)}
        return {"status": "not_found_in_searched_sources", "store_id": store_id, "does_not_prove": list(LIMITS)}

    def verify_chain(self):
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            length = conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
            try:
                self._verified_rows(conn)
            except ContextIntegrityError:
                return {"ok": False, "length": length}
            return {"ok": True, "length": length}

    def _store_id(self, conn, *, create):
        meta_exists = _table_exists(conn, _META_TABLE)
        version_exists = _table_exists(conn, _VERSION_TABLE)
        if not meta_exists:
            if version_exists:
                raise ContextStoreIdentityError("context store identity invalid")
            if not create:
                raise ContextStoreIdentityError("context store identity missing")
            conn.execute(
                f"CREATE TABLE {_VERSION_TABLE}(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            conn.execute(
                f"INSERT INTO {_VERSION_TABLE}(key,value) VALUES(?,?)",
                (_VERSION_KEY, _IDENTITY_VERSION),
            )
            conn.execute(
                f"CREATE TABLE {_META_TABLE}(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )
            store_id = "ctxstore_" + secrets.token_hex(16)
            conn.execute(
                f"INSERT INTO {_META_TABLE}(key,value) VALUES(?,?)",
                (_STORE_ID_KEY, store_id),
            )
            return store_id
        if not version_exists:
            raise ContextStoreIdentityError("context store identity invalid")
        try:
            versions = conn.execute(
                f"SELECT value FROM {_VERSION_TABLE} WHERE key=?",
                (_VERSION_KEY,),
            ).fetchall()
        except Exception as exc:
            raise ContextStoreIdentityError("context store identity invalid") from exc
        if versions != [(_IDENTITY_VERSION,)]:
            raise ContextStoreIdentityError("context store identity invalid")
        try:
            rows = conn.execute(
                f"SELECT value FROM {_META_TABLE} WHERE key=?",
                (_STORE_ID_KEY,),
            ).fetchall()
        except Exception as exc:
            raise ContextStoreIdentityError("context store identity invalid") from exc
        if len(rows) != 1 or not _valid_store_id(rows[0][0]):
            raise ContextStoreIdentityError("context store identity invalid")
        return rows[0][0]

    @staticmethod
    def _verified_rows(conn):
        """Reconcile payloads and audit in one snapshot, including missing rows."""
        previous, latest = "0" * 64, {}
        for key, digest, prev_hash, chain in conn.execute(
                "SELECT key,sha256,prev_hash,chain_hash FROM audit ORDER BY seq"):
            if not all(isinstance(value, str) for value in (key, digest, prev_hash, chain)):
                raise ContextIntegrityError("context audit contains malformed fields")
            expected = hashlib.sha256((previous + key + digest).encode()).hexdigest()
            if previous != prev_hash or expected != chain:
                raise ContextIntegrityError("context audit chain integrity failed")
            previous, latest[key] = chain, digest
        rows = conn.execute("SELECT key,envelope,sha256 FROM records ORDER BY key").fetchall()
        if {row[0] for row in rows} != set(latest):
            raise ContextIntegrityError("context records and audit keys differ")
        for key, envelope, digest in rows:
            if not all(isinstance(value, str) for value in (key, envelope, digest)):
                raise ContextIntegrityError("context record contains malformed fields")
            if hashlib.sha256(envelope.encode()).hexdigest() != digest or latest[key] != digest:
                raise ContextIntegrityError("stored context payload integrity failed")
            try:
                Record.from_json(envelope)
            except Exception as exc:
                raise ContextIntegrityError("context store integrity failed") from exc
        return rows


def _valid_store_id(value):
    return isinstance(value, str) and _STORE_ID.fullmatch(value) is not None


def _table_exists(conn, name):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone() is not None


def _expected_store_id(value):
    if value is None:
        return None
    if not _valid_store_id(value):
        raise ContextStoreIdentityError("expected_store_id is invalid")
    return value


def _compare_store_id(actual, expected):
    if expected is not None and actual != expected:
        raise ContextStoreIdentityError("context store identity mismatch")
