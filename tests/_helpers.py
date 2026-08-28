"""Shared fixture-loading helpers for the F0 test suite."""
from __future__ import annotations

import json
from pathlib import Path

from canon.schema import Record

FIXTURES = Path(__file__).parent / "fixtures"
RECORDS = FIXTURES / "records"

# The five canonical record fixtures, one per kind. Filename stems are stable.
RECORD_FILES = {
    "personality-block": RECORDS / "personality_block.json",
    "episodic-memory": RECORDS / "episodic_memory.json",
    "synthesized-persona-l3": RECORDS / "synthesized_persona_l3.json",
    "adr-decision": RECORDS / "adr_decision.json",
    "research-artifact-ref": RECORDS / "research_artifact_ref.json",
}


def load_dict(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_record(path: Path) -> Record:
    return Record.from_dict(load_dict(path))
