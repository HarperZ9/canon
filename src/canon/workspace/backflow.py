"""backflow.py -- edits made inside a canon region come back as proposals.

When a person or another tool edits the region canon wrote into an instruction
file, overwriting it on the next switch would lose that work. `find_edits`
compares the region on disk with canon's last render of it (from the render
ledger). A block that changed, appeared or disappeared becomes a proposed
personality block (a disappearance proposes retiring it), and an edited brief
is read back line by line (backflow_brief). A region whose grammar the edit
broke cannot be read block by block; its changed lines become one proposed
memory record so the text is kept.

With no ledger entry (canon never wrote this file for this project), the
region is compared with what canon would write now, and only additions and
changes count: an absent block says nothing when canon never put it there.

Proposals go through the same path as imports: scrubbed, validated, written as
proposed rows with an origin naming the surface, the file digest, the line and
the rule, and skipped when the same content was already accepted or rejected.
`switch` refuses to overwrite a region while any of its edits is undecided.
"""
from __future__ import annotations

import difflib
import hashlib
from dataclasses import dataclass, replace

from canon.layering import is_current
from canon.region import RegionError, extract_region
from canon.schema import KIND_EPISODIC_MEMORY, KIND_PERSONALITY_BLOCK, Record, Temporal
from canon.textblock import IngestRefused, ingest_region
from canon.workspace import authoring
from canon.workspace.backflow_brief import Edit, brief_edits
from canon.workspace.import_write import seen_before
from canon.workspace.rows import STATE_PROPOSED
from canon.workspace.scrub import scrub_value
from canon.workspace.store import ProjectStore, record_digest

BRIEF_BLOCK_ID = "canon-workspace-brief"
HARNESS = "canon-drift"
_PREFIX = {"work-item": "task", "environment-constraint": "constraint",
           "episodic-memory": "note", "personality-block": "block"}


@dataclass(frozen=True, slots=True)
class RegionEdits:
    edits: tuple[Edit, ...]
    parse_error: str | None


def _wrap(interior: str) -> str:
    return f"<!-- canon:begin scope=workspace -->\n{interior}<!-- canon:end -->\n"


def _sentinel_lines(host: str) -> dict[str, int]:
    """Block id to the file line number of its sentinel."""
    found = {}
    for number, line in enumerate(host.replace("\r\n", "\n").split("\n"), start=1):
        if line.startswith('<!-- canon:block id="'):
            found[line.split('"', 2)[1]] = number
    return found


def _block_edits(actual: list[Record], base: list[Record], lines: dict[str, int],
                 has_base: bool) -> list[Edit]:
    was = {b.id: b for b in base if b.id != BRIEF_BLOCK_ID}
    now = {b.id: b for b in actual if b.id != BRIEF_BLOCK_ID}
    edits = []
    for rid, block in now.items():
        if rid not in was or block.data != was[rid].data:
            rule = "new-block" if rid not in was else "edited-block"
            edits.append(Edit(rule, KIND_PERSONALITY_BLOCK, rid, dict(block.data), lines.get(rid, 0)))
    if has_base:
        for rid, block in was.items():
            if rid not in now:
                edits.append(Edit("removed-block", KIND_PERSONALITY_BLOCK, rid,
                                  dict(block.data), 0, retire=True))
    return edits


def _unparseable(actual: str, base: str, offset: int) -> Edit:
    changed = [line[1:] for line in difflib.ndiff(base.split("\n"), actual.split("\n"))
               if line.startswith("+ ") and line[2:].strip()]
    return Edit("unparseable-region", KIND_EPISODIC_MEMORY, None,
                {"layer": "L0", "text": "\n".join(c.strip() for c in changed) or actual,
                 "source_ids": []}, offset)


def find_edits(host: str, base_interior: str | None, new_interior: str,
               records: list[Record]) -> RegionEdits:
    """The in-place edits in `host`'s region, read against the base."""
    region = extract_region(host)
    actual = region.inner.replace("\r\n", "\n")
    has_base = base_interior is not None
    base = base_interior if has_base else new_interior
    if actual in (base, new_interior):
        return RegionEdits((), None)
    offset = region.prefix.replace("\r\n", "\n").count("\n") + 1
    try:
        now_blocks = ingest_region(host)
        was_blocks = ingest_region(_wrap(base))
    except (IngestRefused, RegionError) as exc:
        return RegionEdits((_unparseable(actual, base, offset),), str(exc))
    lines = _sentinel_lines(host)
    edits = _block_edits(now_blocks, was_blocks, lines, has_base)
    now_brief = next((b for b in now_blocks if b.id == BRIEF_BLOCK_ID), None)
    was_brief = next((b for b in was_blocks if b.id == BRIEF_BLOCK_ID), None)
    if now_brief is not None:
        first = lines.get(BRIEF_BLOCK_ID, 0) + 2
        edits += brief_edits(now_brief.data["body"],
                             was_brief.data["body"] if was_brief else "", first, records,
                             has_base=has_base and was_brief is not None)
    return RegionEdits(tuple(edits), None)


def _edit_id(edit: Edit, surface: str) -> str:
    if edit.rid:
        return edit.rid
    digest = hashlib.sha256(f"{surface}\n{edit.rule}\n{edit.data}".encode("utf-8"))
    return f"drift-{_PREFIX[edit.kind]}-{digest.hexdigest()[:12]}"


def _record(store: ProjectStore, edit: Edit, surface: str, ordinal: int,
            hits: dict) -> Record:
    data = scrub_value(edit.data, hits)
    record = authoring.build(edit.kind, _edit_id(edit, surface), data, ordinal,
                             harness=HARNESS, native_id=f"drift:{surface}:{edit.line}")
    if edit.retire:
        record = replace(record, temporal=Temporal(valid_until=ordinal, supersedes=None))
    return record


def propose_edits(store: ProjectStore, edits: RegionEdits, *, surface: str,
                  file_sha256: str, dry_run: bool = False) -> dict:
    """Write each edit as a proposed record unless the same content was already
    accepted or rejected. Returns what was proposed and what was decided before."""
    accepted, rejected = seen_before(store)
    hits: dict[str, int] = {}
    ordinal = store.next_ord()
    proposed, decided = [], []
    for edit in edits.edits:
        kept = accepted.get(edit.rid).provenance.create_ord if edit.rid in accepted else None
        record = _record(store, edit, surface, kept or ordinal, hits)
        ordinal += 1
        content = authoring.content_hash(record.kind, record.data) + (
            ":retire" if edit.retire else "")
        entry = {"id": record.id, "kind": record.kind, "rule": edit.rule, "line": edit.line}
        prior = accepted.get(record.id)
        same = prior is not None and prior.data == record.data and \
            (not is_current(prior)) == edit.retire
        if (record.id, content) in rejected or same:
            decided.append(entry)
            continue
        if not dry_run:
            origin = {"importer": "drift", "source": surface, "source_sha256": file_sha256,
                      "line": edit.line, "rule": edit.rule, "content_sha256": content,
                      "base_record_sha256": record_digest(prior) if prior else None}
            store.put(record, state=STATE_PROPOSED, origin=origin, action="pull")
        proposed.append(entry)
    return {"surface": surface, "proposed": proposed, "already_decided": decided,
            "parse_error": edits.parse_error, "secrets_redacted": hits, "dry_run": dry_run}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def pending_edits(store: ProjectStore, plan, *, dry_run: bool) -> dict | None:
    """Read back the in-place edits in a switch plan's current file and propose
    them. None when the plan has no existing file or its region has no edits."""
    from canon.workspace.ledger import last_render
    if plan.surface is None or plan.old_text is None:
        return None
    rel = plan.surface.relative_path
    edits = find_edits(plan.old_text, last_render(store, rel), plan.interior,
                       store.records())
    if not edits.edits:
        return None
    return propose_edits(store, edits, surface=rel, file_sha256=_sha(plan.old_text),
                         dry_run=dry_run)
