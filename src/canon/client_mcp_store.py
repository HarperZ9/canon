"""Existing ContextStore query semantics with a non-initializing read connection.

Reads deserialize a bounded stable file snapshot into memory, never open the
live SQLite path, and never mint identity or migrate schema. WAL databases and
active journal sidecars are refused. Checkpoint and return to DELETE journal
mode outside this entrypoint. Python's SQLite must provide deserialize().
"""
from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3

from .context_audit import verified_state
from .context_migrate import compare_store_id, store_identity
from .context_store import ContextStore
from .path_policy import is_reparse_point, is_windows_ads_path

MAX_SNAPSHOT_BYTES = 256 * 1024 * 1024


def checked_path(path):
    """Reject linked components before resolve and again before each connection.

    These checks do not eliminate concurrent filesystem replacement races and
    are not an OS sandbox against another process running as the same account.
    """
    path = Path(path)
    if not path.is_absolute() or is_windows_ads_path(path):
        raise ValueError("context database requires an absolute ordinary file path")
    if any(is_reparse_point(part) for part in (path, *path.parents)):
        raise ValueError("context database path contains a linked component")
    return path


def _stat_key(info):
    # Windows 3.12 fstat and stat can disagree on ctime (creation/change time).
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _no_sidecars(path):
    if any(Path(str(path) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("client requires an idle DELETE-journal database")


def _snapshot(path):
    _no_sidecars(path)
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not 0 < before.st_size <= MAX_SNAPSHOT_BYTES:
            raise ValueError("client snapshot must be nonempty and at most 256 MiB")
        data = stream.read(MAX_SNAPSHOT_BYTES + 1)
        after = os.fstat(stream.fileno())
    checked_path(path)
    _no_sidecars(path)
    if _stat_key(before) != _stat_key(after) or _stat_key(after) != _stat_key(path.stat()):
        raise ValueError("context database changed during snapshot")
    if len(data) != before.st_size or data[18:20] != b"\x01\x01":
        raise ValueError("client requires a checkpointed DELETE-journal database")
    return data


def _read_connection(path):
    data = _snapshot(path)
    conn = sqlite3.connect(":memory:")
    try:
        conn.deserialize(data)
        conn.execute("PRAGMA query_only=ON")
        return conn
    except Exception:
        conn.close()
        raise


class ClientBackend:
    def __init__(self, path, writable=False):
        self._path = str(path)
        self.writable = writable

    @contextmanager
    def _conn(self):
        path = checked_path(self._path)
        if self.writable:
            conn = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=10)
        else:
            conn = _read_connection(path)
        try:
            yield conn
            if self.writable:
                conn.commit()
        finally:
            conn.close()


class ClientStore(ContextStore):
    """Reuse Canon's audited ingest/query/get without its initializing constructor."""

    def __init__(self, path, writable=False):
        self._backend = ClientBackend(path, writable)

    def identity(self):
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            return store_identity(conn, create=False)[0]

    def _records(self, workspace, project, expected_store_id=None):
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            store_id, version = store_identity(conn, create=False)
            compare_store_id(store_id, expected_store_id)
            state = verified_state(conn, version)
        records = [row.record for key, row in sorted(state.live.items())
                   if (row.record.data.get("workspace_id"), row.record.data.get("project_id"))
                   == (workspace, project) and row.record.data.get("event_record_id")]
        return records, store_id, state.purged_ids()

    def get(self, *args, **kwargs):
        result = super().get(*args, **kwargs)
        if "record" not in result:
            # Tombstones contain no scope; do not reveal a foreign purged id.
            result.pop("purged", None)
        return result

    def health(self, expected):
        with self._backend._conn() as conn:
            conn.execute("BEGIN")
            store_id, version = store_identity(conn, create=False)
            compare_store_id(store_id, expected)
            verified_state(conn, version)
        return {"ok": True, "store_id": store_id, "server": "canon-client",
                "does_not_prove": ["audit integrity does not establish source truth",
                                   "this launch grants access, not caller authentication"]}
