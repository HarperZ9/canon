"""Shared context operations over Canon's existing audited SQLite record store."""
from __future__ import annotations

import hashlib
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


class ContextStore:
    def __init__(self, path):
        path = Path(path)
        if not path.is_absolute():
            raise ValueError("context database path must be absolute")
        self._backend = SqliteBackend(path)

    def ingest(self, payload):
        records = make_records(payload)
        with self._backend._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
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
                return self._ingest_result(records, "already_present", 0)
            for record in records:
                envelope = record.to_json()
                digest = hashlib.sha256(envelope.encode()).hexdigest()
                key = record_key(record)
                conn.execute("INSERT INTO records(key,scope,id,kind,envelope,sha256) VALUES(?,?,?,?,?,?)",
                             (key, record.scope, record.id, record.kind, envelope, digest))
                self._backend._append_audit(conn, key, digest)
        return self._ingest_result(records, "stored", len(records))

    @staticmethod
    def _ingest_result(records, status, count):
        return {"schema": "canon.context-ingest/v1", "status": status,
                "event_record_id": records[0].id, "records_stored": count,
                "source_hash": records[0].provenance.source_hash,
                "does_not_prove": list(LIMITS)}

    @staticmethod
    def _verify_row(conn, key, envelope, digest):
        expected = hashlib.sha256(envelope.encode()).hexdigest()
        row = conn.execute("SELECT sha256 FROM audit WHERE key=? ORDER BY seq DESC LIMIT 1",
                           (key,)).fetchone()
        if expected != digest or not row or row[0] != digest:
            raise ContextIntegrityError("stored context payload integrity failed")

    def _records(self, workspace, project):
        result = []
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            rows = self._verified_rows(conn)
            for key, envelope, digest in rows:
                rec = Record.from_json(envelope)
                if (rec.data.get("workspace_id"), rec.data.get("project_id")) != (workspace, project):
                    continue
                if not rec.data.get("event_record_id"):
                    continue
                result.append(rec)
        return result

    def query(self, workspace_id, project_id, query, top_k=5, include_pending=True):
        workspace, project = scope(workspace_id, project_id)
        return search(self._records(workspace, project), workspace, project, query, top_k, include_pending)

    def get(self, workspace_id, project_id, record_id):
        workspace, project = scope(workspace_id, project_id)
        for rec in self._records(workspace, project):
            if rec.id == record_id:
                return {"status": "found_in_searched_sources", "record_key": record_key(rec), "record": rec.to_dict(),
                        "does_not_prove": list(LIMITS)}
        return {"status": "not_found_in_searched_sources", "does_not_prove": list(LIMITS)}

    def verify_chain(self):
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            length = conn.execute("SELECT COUNT(*) FROM audit").fetchone()[0]
            try:
                self._verified_rows(conn)
            except ContextIntegrityError:
                return {"ok": False, "length": length}
            return {"ok": True, "length": length}

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
        return rows
