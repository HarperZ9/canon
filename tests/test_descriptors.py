from __future__ import annotations

import json
from pathlib import Path

from canon.canonical_json import canonical_json_text
from canon.omission import Omission, validate_omission
from canon.transform import TransformReceipt, validate_transform_receipt

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def read_fixture_text(name: str) -> str:
    return (FOUNDATION / name).read_text(encoding="utf-8")


def test_noncritical_budget_omission_roundtrips():
    d = load_fixture("omission_budget_noncritical.json")
    omission = Omission.from_dict(d)
    assert omission.to_dict() == d
    assert omission.to_json().endswith("\n")
    assert validate_omission(omission) == []


def test_omission_fixture_matches_canonical_json_bytes():
    d = load_fixture("omission_budget_noncritical.json")
    assert read_fixture_text("omission_budget_noncritical.json") == canonical_json_text(d)
    assert Omission.from_dict(d).to_json() == canonical_json_text(d)


def test_omission_uses_tuple_storage_and_defensive_lists():
    ids = ["fact-1"]
    source_refs = ["record:workspace/fact-1"]
    does_not_prove = ["This does not prove omitted facts were irrelevant."]
    omission = Omission("budget", 1, ids, source_refs, False, "omitted", does_not_prove)
    ids.append("fact-2")
    source_refs.append("record:workspace/fact-2")
    does_not_prove.append("mutated")
    as_dict = omission.to_dict()
    as_dict["affected_ids"].append("dict-mutation")
    assert omission.affected_ids == ("fact-1",)
    assert omission.affected_source_refs == ("record:workspace/fact-1",)
    assert omission.does_not_prove == ("This does not prove omitted facts were irrelevant.",)
    assert omission.to_dict()["affected_ids"] == ["fact-1"]


def test_critical_omission_cannot_be_marked_omitted():
    omission = Omission("budget", 1, ("goal-1",), (), True, "omitted")
    assert any("critical" in p and "omitted" in p for p in validate_omission(omission))


def test_omission_count_matches_affected_ids_when_ids_are_listed():
    omission = Omission("budget", 2, ("fact-1",), (), False, "omitted")
    assert any("count" in p for p in validate_omission(omission))


def test_transform_receipt_roundtrips_nested_omissions():
    d = load_fixture("transform_summary.json")
    receipt = TransformReceipt.from_dict(d)
    assert receipt.to_dict() == d
    assert receipt.to_json().endswith("\n")
    assert validate_transform_receipt(receipt) == []


def test_transform_fixture_matches_canonical_json_bytes():
    d = load_fixture("transform_summary.json")
    assert read_fixture_text("transform_summary.json") == canonical_json_text(d)
    assert TransformReceipt.from_dict(d).to_json() == canonical_json_text(d)


def test_transform_receipt_reconstructs_nested_omissions():
    d = load_fixture("transform_summary.json")
    omission = load_fixture("omission_budget_noncritical.json")
    d["omissions"] = [omission]
    receipt = TransformReceipt.from_dict(d)
    assert isinstance(receipt.omissions[0], Omission)
    assert receipt.to_dict() == d
    assert validate_transform_receipt(receipt) == []


def test_transform_receipt_uses_tuple_storage_and_defensive_lists():
    input_refs = ["record:workspace/mem-000123"]
    retained_ids = ["goal-foundation"]
    does_not_prove = ["This receipt does not prove the summary is complete."]
    omissions = [Omission("budget", 0, (), (), False, "omitted")]
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs=input_refs,
        input_span_hash="sha256:" + "2" * 64,
        output_ref="atom:episodic-fact-1",
        output_hash="sha256:" + "3" * 64,
        lossy=True,
        retained_critical_atom_ids=retained_ids,
        omissions=omissions,
        does_not_prove=does_not_prove,
    )
    input_refs.append("record:workspace/mutated")
    retained_ids.append("mutated")
    does_not_prove.append("mutated")
    omissions.append(Omission("budget", 1, ("mutated",), (), False, "omitted"))
    as_dict = receipt.to_dict()
    as_dict["input_refs"].append("dict-mutation")
    as_dict["omissions"].append({"schema": "canon.omission/v1"})
    assert receipt.input_refs == ("record:workspace/mem-000123",)
    assert receipt.retained_critical_atom_ids == ("goal-foundation",)
    assert receipt.does_not_prove == ("This receipt does not prove the summary is complete.",)
    assert len(receipt.omissions) == 1
    assert receipt.to_dict()["input_refs"] == ["record:workspace/mem-000123"]


def test_transform_receipt_requires_hash_boundaries():
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs=("record:workspace/goal-1",),
        input_span_hash="not-a-hash",
        output_ref="atom:goal-1",
        output_hash="sha256:" + "b" * 64,
        lossy=True,
        retained_critical_atom_ids=("goal-1",),
    )
    assert any("input_span_hash" in p for p in validate_transform_receipt(receipt))


def test_transform_receipt_requires_output_hash_boundary():
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs=("record:workspace/goal-1",),
        input_span_hash="sha256:" + "a" * 64,
        output_ref="atom:goal-1",
        output_hash="sha256:" + "B" * 64,
        lossy=True,
        retained_critical_atom_ids=("goal-1",),
    )
    assert any("output_hash" in p for p in validate_transform_receipt(receipt))


def test_validators_are_total_and_list_returning():
    assert isinstance(validate_omission(object()), list)
    assert isinstance(validate_transform_receipt(object()), list)
