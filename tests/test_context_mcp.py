from __future__ import annotations

import io
import json
import sqlite3
from pathlib import Path

from canon import context_mcp
from canon.context_mcp import ENV_CONTEXT_DB, handle, serve


def _payload(result: dict) -> dict:
    return json.loads(result["content"][0]["text"])


def _call(name: str, arguments: dict | None = None) -> dict:
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": name, "arguments": arguments or {}}}
    return handle(req)["result"]


def _tool(name: str, arguments: dict | None = None) -> dict:
    return _payload(_call(name, arguments))


def _ingest_args() -> dict:
    return {
        "workspace_id": "cdev",
        "project_id": "canon",
        "event": {
            "event_id": "turn-1",
            "source_app": "codex",
            "message_text": "Remember the shared-context MCP facade.",
            "attachments": [{"ref": "C:/private/image.png", "caption": "diagram"}],
            "extractions": [{
                "source_id": "message",
                "text": "Remember the shared-context MCP facade.",
                "claim_state": "reported_by_source",
            }],
        },
    }


def test_context_mcp_lists_only_the_context_tools() -> None:
    listed = handle({"id": 1, "method": "tools/list"})["result"]["tools"]
    assert [tool["name"] for tool in listed] == [
        "canon.context.health",
        "canon.context.ingest",
        "canon.context.query",
        "canon.context.get",
    ]


def test_health_reports_missing_explicit_database_without_creating_cwd_file(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(ENV_CONTEXT_DB, raising=False)

    health = _tool("canon.context.health")
    assert health["ok"] is False
    assert health["configured"] is False
    assert not (tmp_path / "canon-context.sqlite").exists()


def test_ingest_query_and_get_use_the_configured_database(monkeypatch, tmp_path) -> None:
    db = tmp_path / "context.sqlite"
    monkeypatch.setenv(ENV_CONTEXT_DB, str(db))

    ingest = _tool("canon.context.ingest", _ingest_args())
    assert ingest["status"] == "stored"
    query = _tool("canon.context.query", {
        "workspace_id": "cdev",
        "project_id": "canon",
        "query": "MCP facade",
    })
    assert query["status"] == "found_in_searched_sources"
    got = _tool("canon.context.get", {
        "workspace_id": "cdev",
        "project_id": "canon",
        "record_id": ingest["event_record_id"],
    })
    assert got["status"] == "found_in_searched_sources"
    assert got["record"]["data"]["attachments"][0]["ref"] == "C:/private/image.png"


def test_mcp_does_not_read_attachment_paths(monkeypatch, tmp_path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("do-not-read-this", encoding="utf-8")
    db = tmp_path / "context.sqlite"
    monkeypatch.setenv(ENV_CONTEXT_DB, str(db))
    args = _ingest_args()
    args["event"]["attachments"][0]["ref"] = str(secret)

    ingest = _tool("canon.context.ingest", args)
    got = _tool("canon.context.get", {
        "workspace_id": "cdev",
        "project_id": "canon",
        "record_id": ingest["event_record_id"],
    })
    assert "do-not-read-this" not in json.dumps(got)
    assert got["record"]["data"]["attachments"][0]["ref"] == str(secret)


def test_malformed_context_args_return_tool_errors(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(ENV_CONTEXT_DB, str(tmp_path / "context.sqlite"))

    result = _call("canon.context.query", {"workspace_id": "cdev", "query": "x"})
    assert result["isError"] is True
    assert "project_id" in result["content"][0]["text"]


def test_health_reports_configured_database_with_failed_integrity(monkeypatch, tmp_path) -> None:
    db = tmp_path / "context.sqlite"
    monkeypatch.setenv(ENV_CONTEXT_DB, str(db))
    ingest = _tool("canon.context.ingest", _ingest_args())
    con = sqlite3.connect(str(db))
    con.execute("DELETE FROM records WHERE id=?", (ingest["event_record_id"],))
    con.commit()
    con.close()

    health = _tool("canon.context.health")

    assert health["configured"] is True
    assert health["ok"] is False


def test_serve_round_trips_context_stdio(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv(ENV_CONTEXT_DB, str(tmp_path / "context.sqlite"))
    lines = [
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"}),
        json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "canon.context.ingest", "arguments": _ingest_args()}}),
    ]
    out = io.StringIO()

    assert serve(io.StringIO("\n".join(lines) + "\n"), out) == 0
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert replies[0]["result"]["serverInfo"]["name"] == "canon-context"
    assert _payload(replies[1]["result"])["status"] == "stored"


def test_module_version_matches_packaged_version() -> None:
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml"
                 ).read_text(encoding="utf-8")
    declared = next(line.split("=", 1)[1].strip().strip('"')
                    for line in pyproject.splitlines()
                    if line.startswith("version"))
    assert context_mcp.__version__ == declared
