from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SRC = str(Path(__file__).resolve().parents[1] / "src")
INIT = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}}


@pytest.mark.parametrize("module", ["canon", "canon.cli"])
def test_module_entry_serves_mcp_initialize(module: str) -> None:
    # Catches: canon.cli losing its __main__ guard, so "python -m canon.cli mcp" (the form MCP
    # host configs use) exits 0 without reading stdin and the host reports "Connection closed".
    env = dict(os.environ, PYTHONPATH=SRC + os.pathsep + os.environ.get("PYTHONPATH", ""))
    proc = subprocess.run([sys.executable, "-m", module, "mcp"], input=json.dumps(INIT) + "\n",
                          capture_output=True, text=True, timeout=60, env=env)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    assert lines, f"no MCP response from python -m {module} mcp; stderr: {proc.stderr[-400:]}"
    reply = json.loads(lines[0])
    assert reply["id"] == 1
    assert reply["result"]["serverInfo"]["name"] == "canon"
