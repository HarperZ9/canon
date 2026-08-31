from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.atom import (
    ATOM_SCHEMA,
    CanonAtom,
    atom_key,
    atoms_from_records,
    is_valid_atom,
    load_atoms_jsonl,
    validate_atom,
)

from ._helpers import RECORD_FILES, load_record

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"
ATOM_FIXTURES = (
    "atom_active_goal.json",
    "atom_permission.json",
    "atom_prohibition.json",
    "atom_constraint.json",
    "atom_frontier_state.json",
    "atom_conflict.json",
    "atom_unknown.json",
)


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ATOM_FIXTURES)
def test_atom_fixture_roundtrips_field_identical(name: str):
    original = load_fixture(name)
    atom = CanonAtom.from_dict(original)
    assert atom.to_dict() == original
    assert atom.to_json().endswith("\n")
    assert validate_atom(atom) == []
    assert is_valid_atom(atom)


def test_atom_schema_field_is_written():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    assert atom.to_dict()["atom_schema"] == ATOM_SCHEMA


def test_critical_normative_goal_requires_active_or_blocked_status():
    atom = CanonAtom(
        type="active-goal",
        id="goal-1",
        layer="session",
        scope_key="workspace",
        precedence_rank=0,
        status="retired",
        classification="normative",
        critical=True,
        value={"summary": "finish foundation plan"},
    )
    assert any("critical" in p and "status" in p for p in validate_atom(atom))


def test_atom_validator_reports_multiple_envelope_problems():
    atom = CanonAtom(
        type="bogus",
        id="",
        layer="bad",
        scope_key="",
        precedence_rank=-1,
        status="missing",
        classification="wrong",
        critical=True,
        value=[],
    )
    problems = validate_atom(atom)
    assert any("type" in p for p in problems)
    assert any("id" in p for p in problems)
    assert any("layer" in p for p in problems)
    assert any("value" in p for p in problems)


def test_atom_to_dict_deep_copies_nested_values():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    got = atom.to_dict()
    got["value"]["summary"] = "mutated"
    got["source_refs"].append({"ref": "changed"})
    assert atom.value["summary"] == "Implement the Canon foundation schema spine."
    assert len(atom.source_refs) == 1


def test_atom_key_names_scope_type_and_id():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    assert atom_key(atom) == ("workspace:canon", "active-goal", "goal-foundation")


def test_load_atoms_jsonl_ignores_blank_lines_and_validates():
    a = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    b = CanonAtom.from_dict(load_fixture("atom_permission.json"))
    text = "\n" + a.to_json() + "\n" + b.to_json() + "\n"
    assert [atom.id for atom in load_atoms_jsonl(text)] == ["goal-foundation", "perm-plan-only"]


def test_load_atoms_jsonl_reports_invalid_line_number():
    bad = '{"atom_schema":"canon.atom/v1","type":"bad","id":"","layer":"bad","scope_key":"","precedence_rank":0,"status":"active","classification":"normative","critical":true,"value":{},"source_refs":[],"source_span_refs":[],"freshness":{},"trust":{},"disclosure":{},"hashes":{}}\n'
    try:
        load_atoms_jsonl(bad)
    except ValueError as exc:
        assert "line 1:" in str(exc)
    else:
        raise AssertionError("invalid JSONL atom should raise ValueError")


def test_load_atoms_jsonl_wraps_non_object_atoms_with_line_number():
    try:
        load_atoms_jsonl("[]\n")
    except ValueError as exc:
        assert "line 1:" in str(exc)
    else:
        raise AssertionError("non-object JSONL atom should raise ValueError")


def test_atoms_from_records_maps_existing_records_deterministically():
    records = [
        load_record(RECORD_FILES["adr-decision"]),
        load_record(RECORD_FILES["personality-block"]),
        load_record(RECORD_FILES["research-artifact-ref"]),
    ]
    atoms = atoms_from_records(reversed(records))
    assert [atom.type for atom in atoms] == ["decision", "evidence-ref", "instruction"]
    assert [atom_key(atom) for atom in atoms] == [
        ("record-scope:workspace", "decision", "adr-0001-container-name"),
        ("record-scope:workspace", "evidence-ref", "artref-0007"),
        ("record-scope:workspace", "instruction", "voice-canon"),
    ]
    instruction = [atom for atom in atoms if atom.type == "instruction"][0]
    assert instruction.classification == "normative"
    assert instruction.critical is False
    assert instruction.hashes["record_sha256"].startswith("sha256:")
