"""vault_mirror.py -- R2: the whole-vault mirror orchestrator.

The mirror renders one note per record plus a MEMORY.md hub. It owns
containment, ownership, and all-or-nothing planning: every legal vault target is
checked before reads and rechecked before writes; foreign files are refused; and
orphans are reported, never deleted.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from canon.backends.base import record_key
# The hub orders exactly like the surface renderer: clock-free create_ord
# ascending, id tie-break, absent ordinal last. Reusing layering's key locks the
# two orders together rather than letting them drift.
from canon.layering import _sort_key
from canon.path_policy import (
    PathPolicyError,
    assert_not_protected,
    assert_operational_vault_path,
)
from canon.schema import (
    KIND_ADR_DECISION,
    KIND_EPISODIC_MEMORY,
    KIND_PERSONALITY_BLOCK,
    KIND_RESEARCH_ARTIFACT_REF,
    KIND_SYNTHESIZED_PERSONA_L3,
    SCOPES,
    Record,
)
from canon.vault import (
    VaultError,
    _display_title,
    derive_note_name,
    ingest_note,
    render_note,
)

_HUB_RELPATH = "MEMORY.md"
_HUB_H1 = "# canon memory index"
_HUB_MARKER = "<!-- canon:vault-hub v1 -- generated; edits here are not durable -->"
# Every rendered hub opens with this two-line head, so it doubles as the
# ownership token: a MEMORY.md that starts with it is canon's own to overwrite;
# one that does not is a hand-authored file the mirror must not clobber.
_HUB_HEAD = f"{_HUB_H1}\n{_HUB_MARKER}"
_HUB_CAP = 80


@dataclass(frozen=True, slots=True)
class VaultResult:
    """The outcome for one vault path: a note or the hub written or unchanged, or
    a stale canon note reported as an orphan (never written, never deleted).
    `record_key` is the record the path carries, or None for the hub."""

    path: str
    status: str
    record_key: str | None
    content: str | None


def is_vault_write_allowed(path: str, *, vault: str) -> bool:
    """True only if `path` resolves to a legal vault target under `vault`.

    A legal target is `{scope}/<name>.md` for a known scope, or the top-level
    `MEMORY.md` hub, and nothing else. Containment is lexical and case-folded
    (`normcase`): refuse the root itself, require `commonpath` to be the root (so
    a traversal that escapes fails), then check the relative tail's shape. It is
    the one lexical gate for both writes and read-side note-target recognition.
    """
    root = os.path.normcase(os.path.normpath(vault))
    target = os.path.normcase(os.path.normpath(path))
    if target == root:
        return False
    try:
        if os.path.commonpath([root, target]) != root:
            return False
    except ValueError:  # different drives, or a mix of absolute and relative
        return False
    parts = os.path.relpath(target, root).split(os.sep)
    if len(parts) == 1:
        return parts[0] == os.path.normcase(_HUB_RELPATH)
    if len(parts) == 2:
        scopes = {os.path.normcase(s) for s in SCOPES}
        return parts[0] in scopes and parts[1].endswith(".md")
    return False


def assert_under_vault_root(path: str, *, vault: str) -> None:
    """Raise VaultError unless `path` is a legal vault target under `vault`."""
    if not is_vault_write_allowed(path, vault=vault):
        raise VaultError(f"path is not an allowed vault target: {path!r}")


def _checked_vault_path(path: str, *, vault: str, path_check: str = "operational") -> str:
    """Contain `path` under `vault` and return the key the IO layer reads/writes.

    'operational' (the default, a real on-disk vault) resolves the path under the
    root on disk -- symlink, reparse point, and ADS are refused -- and refuses a
    protected name. 'lexical' is for an injected non-existent root with
    dict-backed IO (the symmetric read-fidelity harness): it keeps every
    disk-free check -- lexical containment and the protected-name refusal -- and
    skips only the on-disk resolve that a synthetic root cannot satisfy. Lexical
    mode restores the write-leg contract the disk-free vault reader round-trip
    was written against.
    """
    assert_under_vault_root(path, vault=vault)
    if path_check == "lexical":
        try:
            assert_not_protected(path)
        except PathPolicyError as exc:
            raise VaultError(str(exc)) from exc
        return os.path.normpath(path)
    try:
        return str(assert_operational_vault_path(path, vault=vault))
    except PathPolicyError as exc:
        raise VaultError(str(exc)) from exc


def _checked_vault_root(vault: str, *, path_check: str = "operational") -> None:
    _checked_vault_path(_abs(vault, _HUB_RELPATH), vault=vault, path_check=path_check)


def _flatten_ws(text: str) -> str:
    return text.replace("\r", " ").replace("\n", " ")


def _truncate(text: str, cap: int) -> str:
    return text if len(text) <= cap else text[:cap] + "..."


def _escape_hub_title(title: str) -> str:
    """One hub-safe line: cap, then escape `\\`/`[`/`]`. Truncate before escaping
    (the cap counts visible chars, never leaving a dangling `\\`); escape `\\`
    first so `\\](url)` cannot fold to a live link-closing `]` (D-33, hub leg)."""
    flat = _truncate(_flatten_ws(title), _HUB_CAP)
    return flat.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def _hook(record: Record) -> str:
    """A one-line preview for the hub entry, drawn from the record's own body."""
    data = record.data if isinstance(record.data, dict) else {}
    kind = record.kind
    if kind == KIND_PERSONALITY_BLOCK:
        raw = data.get("body", "")
    elif kind == KIND_ADR_DECISION:
        raw = data.get("decision", "")
    elif kind in (KIND_EPISODIC_MEMORY, KIND_SYNTHESIZED_PERSONA_L3):
        raw = data.get("text", "")
    elif kind == KIND_RESEARCH_ARTIFACT_REF:
        raw = data.get("locator", "")
    else:  # pragma: no cover -- render refuses unknown kinds upstream
        raw = ""
    return _truncate(_flatten_ws(str(raw)), _HUB_CAP)


def _hub_line(record: Record) -> str:
    title = _escape_hub_title(_display_title(record))
    return f"- [{title}]({derive_note_name(record)}) -- {_hook(record)}"


def render_hub(records: list[Record]) -> str:
    """Render the MEMORY.md hub: an H1, the generated-marker, then one H2 per
    non-empty scope (global before workspace) with one entry per note in the
    surface renderer's order. An empty pool is the head alone; an empty scope
    omits its H2."""
    sections: list[str] = []
    for scope in SCOPES:
        recs = sorted((r for r in records if r.scope == scope), key=_sort_key)
        if not recs:
            continue
        sections.append("\n".join([f"## {scope}"] + [_hub_line(r) for r in recs]))
    if not sections:
        return _HUB_HEAD + "\n"
    return _HUB_HEAD + "\n\n" + "\n\n".join(sections) + "\n"


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _abs(vault: str, relpath: str) -> str:
    return os.path.normpath(os.path.join(vault, relpath))


def _render_targets(records: list[Record]) -> dict[str, tuple[Record, str]]:
    """Map each record to its note relpath, refusing a duplicate record_key and a
    filename collision, and rendering each note (which refuses a bad record). All
    three refusals happen here, before any path resolves or any byte is read."""
    targets: dict[str, tuple[Record, str]] = {}
    seen: set[str] = set()
    for record in records:
        key = record_key(record)
        if key in seen:
            raise VaultError(f"duplicate record_key in pool: {key!r}")
        seen.add(key)
        relpath = derive_note_name(record)
        if relpath in targets:
            raise VaultError(f"note filename collision: {relpath!r}")
        targets[relpath] = (record, render_note(record))
    return targets


def _require_canon_at(text: str, relpath: str) -> Record:
    """The existing file at `relpath` must be a canon note whose name re-derives
    from its own content, or the plan fails closed."""
    try:
        record = ingest_note(_normalize(text))
    except VaultError as exc:
        raise VaultError(
            f"existing file at vault target is not a canon note: {relpath!r}"
        ) from exc
    if derive_note_name(record) != relpath:
        raise VaultError(f"vault note name does not match its content: {relpath!r}")
    return record


def _discover_orphans(targets, *, vault, read_text, list_dir, path_check="operational"):
    """Canon notes on disk under the mirror whose record_key is absent from the
    pool. A stray non-canon file that is not a target is left alone; a canon note
    whose name does not re-derive from its content is a spoof and is refused.
    Comparisons fold case (`normcase`), and containment reuses the write
    allow-list, so a case-only variant of a target is not misread as a spoof and
    an entry that is not a legal note target is skipped before it is read."""
    orphans: list[tuple[str, Record]] = []
    hub_nc = os.path.normcase(_HUB_RELPATH)
    target_ncs = {os.path.normcase(k) for k in targets}
    for relpath in list_dir(vault):
        norm = relpath.replace("\\", "/")
        norm_nc = os.path.normcase(norm)
        if norm_nc == hub_nc or norm_nc in target_ncs:
            continue
        abs_path = _abs(vault, norm)
        if not is_vault_write_allowed(abs_path, vault=vault):
            continue
        abs_path = _checked_vault_path(abs_path, vault=vault, path_check=path_check)
        content = read_text(abs_path)
        if content is None:
            continue
        try:
            record = ingest_note(_normalize(content))
        except VaultError:
            continue
        if os.path.normcase(derive_note_name(record)) != norm_nc:
            raise VaultError(f"vault note name does not match its content: {norm!r}")
        orphans.append((norm, record))
    return orphans


def _plan_notes(targets, *, vault, read_text, path_check="operational"):
    """Resolve, contain, and byte-compare every target note. A changed or new
    note is planned for write; a byte-identical one (after CRLF normalization) is
    reported unchanged and never rewritten."""
    planned: list[tuple[str, str]] = []
    results: list[VaultResult] = []
    for relpath in sorted(targets):
        record, note = targets[relpath]
        abs_path = _checked_vault_path(_abs(vault, relpath), vault=vault, path_check=path_check)
        existing = read_text(abs_path)
        key = record_key(record)
        if existing is not None:
            _require_canon_at(existing, relpath)
            if _normalize(existing) == note:
                results.append(VaultResult(abs_path, "unchanged", key, note))
                continue
        planned.append((abs_path, note))
        results.append(VaultResult(abs_path, "written", key, note))
    return planned, results


def _plan_hub(records, *, vault, read_text, path_check="operational"):
    """Plan the hub write, refusing to clobber a foreign MEMORY.md.

    An existing MEMORY.md that does not open with the generated head is a
    hand-authored file, not canon's own; the plan fails closed rather than
    overwrite it (the note targets' ownership rule, extended to the hub). A
    canon-owned hub is overwritten when it differs and skipped when it matches.
    """
    hub = render_hub(records)
    abs_path = _checked_vault_path(_abs(vault, _HUB_RELPATH), vault=vault, path_check=path_check)
    existing = read_text(abs_path)
    if existing is not None:
        if not _normalize(existing).startswith(_HUB_HEAD):
            raise VaultError(
                f"existing MEMORY.md is not a canon hub; refusing to clobber it: {abs_path!r}")
        if _normalize(existing) == hub:
            return None, VaultResult(abs_path, "unchanged", None, hub)
    return (abs_path, hub), VaultResult(abs_path, "written", None, hub)


def plan_vault(records, *, vault, read_text, write_text, list_dir,
               path_check="operational"):
    """Mirror the whole pool into the vault under `vault`, plan-then-commit.

    Every note and the hub are rendered, keyed, contained, and classified against
    what is on disk before the first write. Any refusal -- a duplicate key, a
    collision, a render refusal, an off-limits or spoofed existing file, a
    containment violation -- aborts with zero writes. Orphans are reported, never
    deleted. IO is injected: `read_text` returns None for an absent file,
    `list_dir` yields the POSIX relpaths present under the mirror.

    `path_check` selects how each vault target is contained: 'operational' (the
    default) resolves it under the root on disk; 'lexical' keeps the disk-free
    containment and protected-name checks but skips the on-disk resolve, for a
    caller that injects a synthetic non-existent root and dict-backed IO. An
    unknown value is a wiring fault (D-87 house rule).
    """
    if path_check not in ("operational", "lexical"):
        raise ValueError(
            f"unknown path_check {path_check!r}; expected 'operational' or 'lexical'")
    _checked_vault_root(vault, path_check=path_check)
    targets = _render_targets(records)
    orphans = _discover_orphans(
        targets, vault=vault, read_text=read_text, list_dir=list_dir,
        path_check=path_check)
    planned, results = _plan_notes(
        targets, vault=vault, read_text=read_text, path_check=path_check)
    hub_write, hub_result = _plan_hub(
        records, vault=vault, read_text=read_text, path_check=path_check)
    results.append(hub_result)
    if hub_write is not None:
        planned.append(hub_write)
    for relpath, record in orphans:
        results.append(VaultResult(_abs(vault, relpath), "orphan", record_key(record), None))
    _checked_vault_root(vault, path_check=path_check)
    for abs_path, content in planned:
        _checked_vault_path(abs_path, vault=vault, path_check=path_check)
    for abs_path, content in planned:
        write_text(_checked_vault_path(abs_path, vault=vault, path_check=path_check), content)
    return results
