"""Bounded deterministic lookup, with explicit extraction and search coverage."""
from __future__ import annotations

import re

from .context_records import LIMITS, required_text


def pending_sources(records):
    pending = []
    for rec in records:
        if rec.data.get("record_role") != "event":
            continue
        for item in rec.data.get("attachments", []) + rec.data.get("sources", []):
            status = item.get("extraction_status", "pending_extraction")
            if status not in {"completed", "extracted", "reviewed"}:
                pending.append({"event_record_id": rec.id,
                                "ref": str(item.get("ref", item.get("locator", "unknown")))[:1024],
                                "status": str(status)[:120]})
    return pending


def search(records, workspace, project, query, top_k, include_pending):
    required_text(query, "query", 200_000)
    if type(top_k) is not int or not 0 <= top_k <= 20:
        raise ValueError("top_k must be an integer between 0 and 20")
    if type(include_pending) is not bool:
        raise ValueError("include_pending must be boolean")
    tokens = set(re.findall(r"\w+", query.casefold()))
    matches = []
    for rec in records:
        body = str(rec.data["text"])
        words = set(re.findall(r"\w+", body.casefold()))
        score = len(tokens & words)
        if score:
            matches.append((score, rec, body))
    matches.sort(key=lambda row: (-row[0], row[1].id))
    hits = [hit(rec, text, score, workspace, project) for score, rec, text in matches[:top_k]]
    pending = pending_sources(records)
    status = "found_in_searched_sources" if matches else ("pending_extraction" if pending else "not_found_in_searched_sources")
    return {"schema": "canon.context-query/v1", "status": status, "hits": hits,
            "pending_extraction": pending[:20] if include_pending else [],
            "coverage": {"workspace_id": workspace, "project_id": project,
                         "records_searched": len(records), "matching_records": len(matches),
                         "hits_omitted": max(0, len(matches) - len(hits)),
                         "pending_count": len(pending), "pending_returned": min(20, len(pending)) if include_pending else 0,
                         "method": "deterministic_keyword_overlap", "historical_completeness": "unknown",
                         "source_freshness": "not_checked", "supersession_resolution": "not_implemented"},
            "does_not_prove": list(LIMITS)}


def hit(rec, text, score, workspace, project):
    return {"record_id": rec.id, "workspace_id": workspace, "project_id": project,
            "excerpt": text[:2000], "excerpt_truncated": len(text) > 2000,
            "claim_state": rec.data.get("claim_state"), "score": score,
            "citation": {"record_key": "workspace/" + rec.id,
                         "event_record_id": rec.data["event_record_id"],
                         "source_hash": rec.provenance.source_hash,
                         "source_app": rec.provenance.harness,
                         "native_id": rec.provenance.native_id,
                         "session_id": rec.provenance.session_id}}
