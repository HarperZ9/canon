"""import_claude.py -- propose records from a Claude Code session transcript.

Claude Code writes one JSON object per line to a session file. Anthropic's
documentation says the entry format is internal and changes between versions,
so this importer reads only the fields public parsers agree on, names what it
drops, and refuses an entry type it has not seen rather than guess.

Read (field names confirmed against public parsers, 2026-09-23):

  type: user | assistant      message.role, message.content (string or blocks)
  content blocks              text, tool_use {name, input}, tool_result,
                              thinking, redacted_thinking, image
  type: summary               summary (the session's own title for itself)
  sessionId, cwd, gitBranch   session id, the project check, the focus branch
  TodoWrite tool_use          input.todos[] {content, status}: the plan
  Edit/Write/MultiEdit        input.file_path: the areas being worked on

Every other entry type Claude Code is known to write is a declared drop. The
format is not a stable interface; a new Claude Code release can add an entry
type, and this importer then refuses until the drop is declared.
"""
from __future__ import annotations

from canon.workspace.import_common import (
    COMMON_DROPS,
    Collector,
    Extraction,
    Ledger,
    Source,
)
from canon.workspace.identity import ProjectIdentity

IMPORTER = "claude-code"
META_TYPES = frozenset({
    "system", "file-history-snapshot", "queue-operation", "attachment", "progress",
    "ai-title", "last-prompt", "permission-mode", "custom-title", "agent-name",
    "agent-color", "frame-link",
})
EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
              "NotebookEdit": "notebook_path"}
DECLARED_DROPS = {
    **COMMON_DROPS,
    "meta-entry": "an entry that carries no conversation: " + ", ".join(sorted(META_TYPES)),
    "sidechain": "a sidechain (subagent) entry",
    "meta-message": "a message Claude Code marked isMeta (injected, not typed)",
    "thinking": "an assistant thinking block",
    "message-metadata": "an assistant entry's model, request id and token usage",
}


def _content_blocks(content: object, line: int, ledger: Ledger) -> list[dict]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if not isinstance(content, list):
        ledger.unknown("message content shape", line)
        return []
    return [block if isinstance(block, dict) else {"type": None} for block in content]


def _tool_use(block: dict, line: int, col: Collector) -> None:
    name, payload = block.get("name"), block.get("input")
    payload = payload if isinstance(payload, dict) else {}
    if name == "TodoWrite":
        todos = payload.get("todos")
        if not isinstance(todos, list):
            col.ledger.unknown("TodoWrite input shape", line)
            return
        col.add_plan(line, [(t.get("content", ""), t.get("status"))
                            for t in todos if isinstance(t, dict)])
    elif name in EDIT_TOOLS and isinstance(payload.get(EDIT_TOOLS[name]), str):
        col.add_edit(payload[EDIT_TOOLS[name]])
    else:
        col.ledger.drop("tool-call")


def _block(block: dict, line: int, role: str, col: Collector) -> None:
    kind = block.get("type")
    if kind == "text" and isinstance(block.get("text"), str):
        col.add_text(block["text"], line, role=role)
    elif kind in ("thinking", "redacted_thinking"):
        col.ledger.drop("thinking")
    elif kind == "image":
        col.ledger.drop("image")
    elif kind == "tool_use":
        _tool_use(block, line, col)
    elif kind == "tool_result":
        col.ledger.drop("tool-output")
    else:
        col.ledger.unknown(f"content block {kind!r}", line)


def _entry(obj: dict, line: int, col: Collector, ex: Extraction) -> None:
    kind = obj.get("type")
    if kind in META_TYPES:
        col.ledger.drop("meta-entry")
        return
    if kind == "summary":
        if isinstance(obj.get("summary"), str) and obj["summary"].strip():
            col.set_summary(line, obj["summary"])
        return
    if kind not in ("user", "assistant"):
        col.ledger.unknown(f"entry type {kind!r}", line)
        return
    if obj.get("isSidechain") is True:
        col.ledger.drop("sidechain")
        return
    if obj.get("isMeta") is True:
        col.ledger.drop("meta-message")
        return
    _session_fields(obj, col, ex)
    if kind == "assistant":
        col.ledger.drop("message-metadata")
    message = obj.get("message") if isinstance(obj.get("message"), dict) else {}
    for block in _content_blocks(message.get("content"), line, col.ledger):
        _block(block, line, kind, col)


def _session_fields(obj: dict, col: Collector, ex: Extraction) -> None:
    if ex.session_id is None and isinstance(obj.get("sessionId"), str):
        ex.session_id = obj["sessionId"]
    if isinstance(obj.get("cwd"), str) and obj["cwd"] not in ex.cwds:
        ex.cwds.append(obj["cwd"])
    if isinstance(obj.get("gitBranch"), str) and obj["gitBranch"]:
        col.branch = obj["gitBranch"]


def extract(source: Source, identity: ProjectIdentity, *,
            user_drops: frozenset[str] = frozenset()) -> Extraction:
    """Walk a Claude Code session and collect candidates and the loss ledger."""
    ledger = Ledger(DECLARED_DROPS, user_drops)
    if source.truncated_tail:
        ledger.drop("truncated-tail")
    ex = Extraction([], ledger)
    col = Collector(identity, ledger, hits=ex.hits)
    for line, obj, _raw in source.lines:
        _entry(obj, line, col, ex)
    ex.candidates = col.finish()
    return ex
