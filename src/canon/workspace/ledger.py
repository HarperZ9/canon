"""ledger.py -- what canon last wrote into each instruction region.

A region on disk can differ from what canon would render now for two reasons:
the records changed since the last render (canon's own file is stale), or a
person or another tool edited the region in place. Only the first is safe to
overwrite. Telling them apart needs the last render, so `switch` records the
interior it wrote for each surface, per project:

    projects/<project_id>/renders.json
    {"schema": "canon.render-ledger/v1",
     "surfaces": {"CLAUDE.md": {"target": "claude-code", "sha256": "...",
                                "interior": "..."}}}

Keys are the surface's path relative to its root, so the file names no local
path. The interior is canon's own render of records that already passed the
secret checks.
"""
from __future__ import annotations

import hashlib
import json

from canon.versions import PIN_RENDER_LEDGER
from canon.workspace.store import ProjectStore, StoreError, write_atomic

LEDGER_SCHEMA = PIN_RENDER_LEDGER.kind_tag
LEDGER_FILE = "renders.json"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load(store: ProjectStore) -> dict:
    path = store.project_dir() / LEDGER_FILE
    if not path.is_file():
        return {"schema": LEDGER_SCHEMA, "surfaces": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != LEDGER_SCHEMA or not isinstance(data.get("surfaces"), dict):
        raise StoreError(f"{LEDGER_FILE} is not a {LEDGER_SCHEMA} ledger")
    return data


def last_render(store: ProjectStore, relative_path: str) -> str | None:
    """The interior canon last wrote to this surface, or None if it never did.
    A ledger entry whose digest does not match its text is refused."""
    entry = _load(store)["surfaces"].get(relative_path)
    if entry is None:
        return None
    if _sha(entry["interior"]) != entry["sha256"]:
        raise StoreError(f"{LEDGER_FILE} entry for {relative_path} fails its digest")
    return entry["interior"]


def record_render(store: ProjectStore, relative_path: str, target: str,
                  interior: str) -> None:
    with store.locked():
        data = _load(store)
        data["surfaces"][relative_path] = {"target": target, "sha256": _sha(interior),
                                           "interior": interior}
        write_atomic(store.project_dir() / LEDGER_FILE,
                     json.dumps(data, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
