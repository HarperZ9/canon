"""Plan and apply a purge of captured context events.

A plan starts from a selection: one event, every event captured before an
ordinal (the audit sequence number of its put), every event in a workspace and
project, or a retention policy (context_retention.py). Its closure is each
selected event, the records derived from it at ingest, and the answer paired
with it, meaning an assistant event whose `responds_to` names it, because an
answer often restates its prompt; `keep_responses` leaves the answer. Events
that cite a purged event keep their own text, and their query results say the
cited event was purged. The plan digest binds the store, the scope, the
selection and every record the plan removes, so a confirmation applies exactly
the plan that was shown, and a plan the store has moved past is refused.

Apply works in one transaction on a connection with secure_delete on: it plans
again, compares the digest, deletes the records, appends a purge row and a
tombstone per record, marks the store scrub-pending, raises the identity
version and commits. Then it scrubs the files, clears the mark, scans them
(context_scrub.py) and reports what remains.

A selected event that an earlier purge removed is listed as already purged
rather than refused, so the owner can rerun a command that was interrupted. A
plan that removes nothing but finds the scrub mark still set finishes that
scrub when it is confirmed.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field

from .canonical_json import canonical_json_bytes
from .context_audit import StoreState, append_purge, verified_state
from .context_migrate import (
    checked_expected_store_id, compare_store_id, prepare_write, store_identity,
)
from .context_purge_report import nothing_report, plan_extras, purge_report, scrub_report
from .context_records import scope as checked_scope
from .context_scrub import (
    clear_scrub_mark, live_values, mark_scrub_pending, residual_scan, scan_values,
    scrub_complete, scrub_connection, scrub_database, scrub_pending,
)

PLAN_SCHEMA = "canon.context-purge-plan/v1"
REASON_OWNER = "owner_request"
_ROLE_RANK = {"event": 0, "response": 1, "derived": 2}
_ONE_SELECTOR = "choose exactly one of event_id, before_ord or all"
_NOT_FOUND = "event_id is not a captured event in this workspace and project"


class ContextPurgeError(ValueError):
    """A purge selection, policy or confirmation that cannot be applied."""


class ContextPurgeNotFound(ContextPurgeError):
    """The selected event is not a captured event in this workspace and project."""


class ContextPurgeStale(ContextPurgeError):
    """The confirmed plan no longer matches what the store holds."""


@dataclass(frozen=True)
class Target:
    event_id: str
    mode: str  # "event": the event and its closure; "derived": its derived records only
    reason_code: str


@dataclass(frozen=True)
class ScopeView:
    state: StoreState
    events: dict
    derived: dict
    answers: dict


@dataclass(frozen=True)
class Selection:
    description: dict
    keep_responses: bool
    resolve: Callable[[ScopeView], list[Target]] = field(compare=False, repr=False)


def select(*, event_id=None, before_ord=None, all_events=False, keep_responses=False) -> Selection:
    """Exactly one of an event record id, an ordinal cut-off, or every event."""
    if type(keep_responses) is not bool:
        raise ContextPurgeError("keep_responses must be true or false")
    if type(all_events) is not bool or [event_id is not None, before_ord is not None,
                                        all_events].count(True) != 1:
        raise ContextPurgeError(_ONE_SELECTOR)
    if event_id is not None:
        if not isinstance(event_id, str) or not event_id:
            raise ContextPurgeError(_NOT_FOUND)
        return Selection({"event_id": event_id}, keep_responses,
                         lambda view: [Target(event_id, "event", REASON_OWNER)])
    if before_ord is not None:
        if type(before_ord) is not int or before_ord < 1:
            raise ContextPurgeError("before_ord must be a whole number of 1 or more")
        return Selection({"before_ord": before_ord}, keep_responses, lambda view: [
            Target(eid, "event", REASON_OWNER) for eid, row in sorted(view.events.items())
            if row.ordinal < before_ord])
    return Selection({"all": True}, keep_responses, lambda view: [
        Target(eid, "event", REASON_OWNER) for eid in sorted(view.events)])


def plan_purge(store, workspace_id, project_id, selection, *, expected_store_id=None,
               local_detail=False) -> dict:
    workspace, project = checked_scope(workspace_id, project_id)
    expected = checked_expected_store_id(expected_store_id)
    with store._backend._conn() as conn:
        conn.execute("BEGIN IMMEDIATE")
        store_id, version = store_identity(conn, create=True)
        compare_store_id(store_id, expected)
        state = verified_state(conn, version)
        pending = scrub_pending(conn)
    return build_plan(state, store_id, workspace, project, selection,
                      scrub_is_pending=pending, local_detail=local_detail)


def apply_purge(store, workspace_id, project_id, selection, *, confirm_plan_sha256,
                expected_store_id=None, busy_retry_seconds=30.0) -> dict:
    workspace, project = checked_scope(workspace_id, project_id)
    expected = checked_expected_store_id(expected_store_id)
    conn = scrub_connection(store.path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        store_id, version = store_identity(conn, create=True)
        compare_store_id(store_id, expected)
        state = verified_state(conn, version)
        plan = build_plan(state, store_id, workspace, project, selection,
                          scrub_is_pending=scrub_pending(conn))
        if confirm_plan_sha256 != plan["plan_sha256"]:
            raise ContextPurgeStale("context purge plan is stale; ask for a new plan")
        if not plan["entries"]:
            conn.rollback()
            if not plan["scrub_pending"]:
                return nothing_report(plan)
            return scrub_report(plan, _scrub(conn, busy_retry_seconds))
        values, short = scan_values([state.live[row["key"]].record for row in plan["entries"]])
        ordinals = _delete_and_tombstone(conn, plan["entries"])
        conn.commit()
        scrub = _scrub(conn, busy_retry_seconds)
        scan = residual_scan(store.path, values, live_values(conn), short)
    finally:
        if conn.in_transaction:
            conn.rollback()
        conn.close()
    return purge_report(plan, ordinals, scrub, scan, store.verify_chain())


def build_plan(state, store_id, workspace, project, selection, *, scrub_is_pending=False,
               local_detail=False) -> dict:
    """The digest covers what the plan removes and what it found already
    purged. The scrub mark sits beside it: a scrub that finishes between plan
    and confirmation changes nothing the owner confirms."""
    view = scope_view(state, workspace, project)
    entries, already = _closure(view, selection.resolve(view), selection.keep_responses)
    roles = [row["role"] for row in entries]
    body = {"schema": PLAN_SCHEMA, "store_id": store_id, "workspace_id": workspace,
            "project_id": project, "selection": selection.description,
            "keep_responses": selection.keep_responses, "entries": entries,
            "already_purged": already,
            "counts": {"events": roles.count("event"), "responses": roles.count("response"),
                       "derived": roles.count("derived"), "records": len(entries)}}
    digest = "sha256:" + hashlib.sha256(canonical_json_bytes(body)).hexdigest()
    return {**body, "plan_sha256": digest, "scrub_pending": scrub_is_pending,
            **plan_extras(view, entries, local_detail)}


def scope_view(state: StoreState, workspace: str, project: str) -> ScopeView:
    """The events of one workspace and project, their derived records, and the
    assistant events that answer each of them."""
    events, derived, answers = {}, {}, {}
    for key, row in state.live.items():
        data = row.record.data
        parent = data.get("event_record_id")
        if (data.get("workspace_id"), data.get("project_id")) != (workspace, project) \
                or not isinstance(parent, str):
            continue
        if data.get("record_role") == "event" and parent == row.record.id:
            events[parent] = row
        else:
            derived.setdefault(parent, []).append(key)
    for event_id, row in events.items():
        data = row.record.data
        if data.get("message_role") == "assistant" and isinstance(data.get("responds_to"), str):
            answers.setdefault(data["responds_to"], []).append(event_id)
    return ScopeView(state, events, {k: sorted(v) for k, v in derived.items()},
                     {k: sorted(v) for k, v in answers.items()})


def was_purged(view: ScopeView, event_id: str) -> bool:
    """Whether the latest audit row for this event's record is a purge."""
    return "workspace/" + event_id in view.state.purged


def _closure(view: ScopeView, targets: list[Target], keep_responses: bool):
    entries: dict[str, dict] = {}
    already: set[str] = set()
    for target in sorted(targets, key=lambda item: (item.event_id, item.mode)):
        if target.event_id not in view.events:
            if not was_purged(view, target.event_id):
                raise ContextPurgeNotFound(_NOT_FOUND)
            already.add(target.event_id)
            continue
        if target.mode != "derived":
            _add(entries, view, "workspace/" + target.event_id, target.event_id, "event",
                 target.reason_code)
        _add_derived(entries, view, target.event_id, target.reason_code)
        if target.mode == "derived" or keep_responses:
            continue
        for answer in view.answers.get(target.event_id, []):
            _add(entries, view, "workspace/" + answer, answer, "response", target.reason_code)
            _add_derived(entries, view, answer, target.reason_code)
    return [entries[key] for key in sorted(entries)], sorted(already)


def _add_derived(entries, view, event_id, reason_code) -> None:
    for key in view.derived.get(event_id, []):
        _add(entries, view, key, event_id, "derived", reason_code)


def _add(entries, view, key, event_id, role, reason_code) -> None:
    current = entries.get(key)
    if current is not None and _ROLE_RANK[current["role"]] <= _ROLE_RANK[role]:
        return
    entries[key] = {"key": key, "event_record_id": event_id, "role": role,
                    "reason_code": reason_code, "ordinal": view.state.live[key].ordinal}


def _scrub(conn, busy_retry_seconds: float) -> dict:
    """VACUUM and checkpoint, then clear the scrub mark if both finished."""
    scrub = scrub_database(conn, busy_retry_seconds)
    if scrub_complete(scrub):
        clear_scrub_mark(conn)
    scrub["pending"] = not scrub_complete(scrub)
    return scrub


def _delete_and_tombstone(conn, entries) -> list[int]:
    prepare_write(conn)
    mark_scrub_pending(conn)
    ordinals = []
    for row in entries:
        conn.execute("DELETE FROM records WHERE key=?", (row["key"],))
        ordinals.append(append_purge(conn, row["key"], row["reason_code"]))
    return ordinals
