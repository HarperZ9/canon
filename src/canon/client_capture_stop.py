"""Stop deliveries: the client's last assistant message as a paired answer event.

Response capture is off unless the hook runs with `--capture prompts+responses`
(or `CANON_CONTEXT_CAPTURE`). Then a Stop delivery stores the client's
`last_assistant_message` as an assistant event. It is linked to the prompt
event captured for the same `prompt_id` (Claude Code) or `turn_id` (Codex) by a
`canon_event_ref` source and by `responds_to`, which is what a purge follows
when it removes a prompt together with its answer.

The answer's event id is `<native_id>-response-<segment>`. Reusing the prompt's
native id would give the answer the prompt's identity with different content,
which the store refuses as a collision. A redelivered Stop with the same text
is idempotent at its segment; a different answer for the same prompt, as when a
Stop hook asks the client to continue, takes the next segment.

The event records that tool calls and reasoning were not captured, and whether
the prompt it answers was found in the store. A Stop the hook does not store
always returns a message saying why, so a hook mounted on Stop never fails
silently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .client_capture_payload import (
    CaptureInputError, native_prompt_id, safe_event_id, source_app_for, sources_for,
    string_field,
)
from .context_records import sha

CAPTURE_PROMPTS = "prompts"
CAPTURE_RESPONSES = "prompts+responses"
CAPTURE_MODES = (CAPTURE_PROMPTS, CAPTURE_RESPONSES)
MAX_SEGMENTS = 16
OFF_MESSAGE = "Canon: response capture is off; this Stop event was not stored"
NO_MESSAGE = "Canon: this Stop event carried no last assistant message and was not stored"
NO_PROMPT_ID = ("Canon: this Stop event has no prompt id to pair the answer with, "
                "so it was not stored")


def capture_stop(hook: dict[str, Any], args, open_service: Callable[[], Any]) -> dict:
    """Store the answer a Stop delivery carries, or say why it was not stored."""
    if args.capture != CAPTURE_RESPONSES:
        return {"systemMessage": OFF_MESSAGE}
    message = hook.get("last_assistant_message")
    if not isinstance(message, str) or not message.strip():
        return {"systemMessage": NO_MESSAGE}
    source_app = source_app_for(args.client, hook)
    native_id, identified = native_prompt_id(source_app, hook)
    if not identified:
        return {"systemMessage": NO_PROMPT_ID}
    session_id = string_field(hook, "session_id")
    prompt_ref = prompt_record_id(args.workspace_id, args.project_id, source_app,
                                  session_id, native_id)
    service = open_service()
    found = service.get(args.workspace_id, args.project_id, prompt_ref)["status"]
    pairing = ("prompt_event_found" if found == "found_in_searched_sources"
               else "prompt_event_not_found")
    answer = _Answer(source_app, native_id, session_id, message, prompt_ref, pairing)
    _ingest_first_free_segment(service, hook, args, answer)
    return {}


def prompt_record_id(workspace_id: str, project_id: str, source_app: str,
                     session_id: str, native_id: str) -> str:
    """The record id the store gives the prompt event for this native id,
    computed the way context_records.make_records computes it."""
    identity = [workspace_id, project_id, source_app, session_id, safe_event_id(native_id)]
    return "context-event-" + sha(identity)


@dataclass(frozen=True)
class _Answer:
    source_app: str
    native_id: str
    session_id: str
    message: str
    prompt_ref: str
    pairing: str


def _ingest_first_free_segment(service, hook, args, answer: _Answer) -> None:
    from .context_store import ContextCollision

    for segment in range(1, MAX_SEGMENTS + 1):
        payload = {"workspace_id": args.workspace_id, "project_id": args.project_id,
                   "event": _answer_event(hook, args, answer, segment)}
        try:
            service.ingest(payload)
            return
        except ContextCollision:
            continue
    raise CaptureInputError(f"this prompt already has {MAX_SEGMENTS} different stored "
                            "answers; the answer was not stored")


def _answer_event(hook, args, answer: _Answer, segment: int) -> dict[str, Any]:
    ref = {"source_id": "prompt_event", "source_kind": "canon_event_ref",
           "ref": answer.prompt_ref, "extraction_status": "completed"}
    transcript = hook.get("transcript_path") if args.transcript_locator == "path" else None
    locators = [source for source in sources_for(answer.source_app, answer.native_id,
                                                 transcript if isinstance(transcript, str)
                                                 else None)
                if source["source_kind"] == "transcript_locator"]
    return {
        "event_id": f"{safe_event_id(answer.native_id)}-response-{segment}",
        "source_app": answer.source_app,
        "native_id": answer.native_id,
        "session_id": answer.session_id,
        "message_text": answer.message,
        "message_role": "assistant",
        "responds_to": answer.prompt_ref,
        "container_id": args.container_id,
        "coverage": {
            "response": "captured",
            "tool_calls": "not_captured",
            "reasoning": "not_captured",
            "transcript": "locator_only_not_read" if locators else "locator_not_recorded",
            "pairing": answer.pairing,
        },
        "sources": [ref] + locators,
    }
