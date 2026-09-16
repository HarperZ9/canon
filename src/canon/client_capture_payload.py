"""Normalize provider hook payloads into the shared context ingest shape."""
from __future__ import annotations

import re
from typing import Any
from uuid import uuid4


class CaptureInputError(ValueError):
    """The hook input cannot be safely captured as a user prompt."""


_SAFE_ID = re.compile(r"[^A-Za-z0-9_.:-]+")


def event_from_hook(
    hook: dict[str, Any],
    client: str,
    workspace_id: str,
    project_id: str,
    container_id: str,
) -> dict[str, Any]:
    """Build a ContextStore.ingest payload from a UserPromptSubmit hook."""
    _require_user_prompt(hook)
    source_app = _source_app(client, hook)
    prompt = _prompt_text(hook)
    native_id, identified = _native_prompt_id(source_app, hook)
    event = _event_data(hook, source_app, prompt, native_id, identified, container_id)
    return {"workspace_id": workspace_id, "project_id": project_id, "event": event}


def _event_data(
    hook: dict[str, Any],
    source_app: str,
    prompt: str,
    native_id: str,
    identified: bool,
    container_id: str,
) -> dict[str, Any]:
    coverage_note = (
        "Hook input captures prompt text only; transcript and attachment paths "
        "are retained as locators and are not read by this adapter."
    )
    return {
        "event_id": _safe_event_id(native_id),
        "source_app": source_app,
        "native_id": native_id,
        "session_id": _string_field(hook, "session_id"),
        "message_text": prompt,
        "container_id": container_id,
        "cwd": _optional_string(hook, "cwd"),
        "permission_mode": _optional_string(hook, "permission_mode"),
        "model": _optional_string(hook, "model"),
        "links": [],
        "attachments": [_pending_attachment()],
        "coverage": {
            "prompt": "captured",
            "attachments": "capture_coverage_unknown",
            "transcript": "locator_only_not_read",
            "deduplication": (
                "stable_native_prompt_id" if identified
                else "unsupported_without_native_prompt_id"
            ),
        },
        "sources": _sources(source_app, native_id, _optional_string(hook, "transcript_path")),
        "extractions": [{
            "source_id": "prompt",
            "text": prompt,
            "claim_state": "reported_by_source",
            "extraction_status": "completed",
        }],
        "interpretations": [{
            "text": coverage_note,
            "status": "capture_coverage_note",
            "source_ids": ["prompt", "attachment_coverage"],
        }],
    }


def _require_user_prompt(hook: dict[str, Any]) -> None:
    if hook.get("hook_event_name") != "UserPromptSubmit":
        raise CaptureInputError("expected UserPromptSubmit hook input")


def _source_app(client: str, hook: dict[str, Any]) -> str:
    if client == "auto":
        if "turn_id" in hook:
            return "codex"
        if "prompt_id" in hook:
            return "claude-code"
        raise CaptureInputError("missing stable prompt id for auto client")
    if client in {"codex", "claude-code"}:
        return client
    raise CaptureInputError(f"unsupported client {client!r}")


def _prompt_text(hook: dict[str, Any]) -> str:
    prompt = hook.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        raise CaptureInputError("missing prompt text")
    return prompt


def _native_prompt_id(source_app: str, hook: dict[str, Any]) -> tuple[str, bool]:
    field = "turn_id" if source_app == "codex" else "prompt_id"
    fallback = "prompt_id" if field == "turn_id" else "turn_id"
    value = hook.get(field) or hook.get(fallback)
    if isinstance(value, str) and value.strip():
        return value.strip(), True
    return f"unidentified-{uuid4().hex}", False


def _safe_event_id(native_id: str) -> str:
    safe = _SAFE_ID.sub("-", native_id).strip("-")
    if not safe:
        raise CaptureInputError("stable prompt id has no safe identifier characters")
    return safe[:120]


def _string_field(hook: dict[str, Any], field: str) -> str:
    value = hook.get(field)
    if not isinstance(value, str) or not value:
        raise CaptureInputError(f"missing {field}")
    return value


def _optional_string(hook: dict[str, Any], field: str) -> str | None:
    value = hook.get(field)
    return value if isinstance(value, str) and value else None


def _pending_attachment() -> dict[str, str]:
    return {
        "ref": "hook-payload:attachments",
        "media_type": "unknown",
        "caption": "Attachment capture coverage unknown for this prompt hook.",
        "extraction_status": "pending_extraction",
    }


def _sources(source_app: str, native_id: str, transcript_path: str | None) -> list[dict[str, str]]:
    sources = [{
        "source_id": "prompt",
        "source_kind": "prompt",
        "locator": f"{source_app}:{native_id}",
        "extraction_status": "completed",
    }]
    if transcript_path:
        sources.append({
            "source_id": "transcript_path",
            "source_kind": "transcript_locator",
            "locator": transcript_path,
            "extraction_status": "locator_only_not_read",
        })
    sources.append({
        "source_id": "attachment_coverage",
        "source_kind": "attachment_manifest_absent",
        "locator": "hook-payload:attachments",
        "extraction_status": "capture_coverage_unknown",
    })
    return sources
