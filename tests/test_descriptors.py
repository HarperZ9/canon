from __future__ import annotations

import json
from pathlib import Path

import pytest

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


@pytest.mark.parametrize("field", ("affected_ids", "affected_source_refs", "does_not_prove"))
def test_omission_rejects_scalar_sequence_fields_from_dict(field: str):
    d = load_fixture("omission_budget_noncritical.json")
    d[field] = "not-a-list"
    omission = Omission.from_dict(d)
    assert getattr(omission, field) == "not-a-list"
    assert omission.to_dict()[field] == "not-a-list"
    assert any(field in p for p in validate_omission(omission))


def test_omission_rejects_scalar_sequence_fields_from_direct_construction():
    omission = Omission(
        "budget",
        1,
        "fact-1",
        "record:workspace/fact-1",
        False,
        "omitted",
        "not-proof-text",
    )
    assert omission.to_dict()["affected_ids"] == "fact-1"
    problems = validate_omission(omission)
    assert any("affected_ids" in p for p in problems)
    assert any("affected_source_refs" in p for p in problems)
    assert any("does_not_prove" in p for p in problems)


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


@pytest.mark.parametrize("field", ("input_refs", "retained_critical_atom_ids", "does_not_prove"))
def test_transform_receipt_rejects_scalar_sequence_fields_from_dict(field: str):
    d = load_fixture("transform_summary.json")
    d[field] = "not-a-list"
    receipt = TransformReceipt.from_dict(d)
    assert getattr(receipt, field) == "not-a-list"
    assert receipt.to_dict()[field] == "not-a-list"
    assert any(field in p for p in validate_transform_receipt(receipt))


def test_transform_receipt_rejects_scalar_sequence_fields_from_direct_construction():
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs="record:workspace/goal-1",
        input_span_hash="sha256:" + "a" * 64,
        output_ref="atom:goal-1",
        output_hash="sha256:" + "b" * 64,
        lossy=True,
        retained_critical_atom_ids="goal-1",
        does_not_prove="not-proof-text",
    )
    assert receipt.to_dict()["input_refs"] == "record:workspace/goal-1"
    problems = validate_transform_receipt(receipt)
    assert any("input_refs" in p for p in problems)
    assert any("retained_critical_atom_ids" in p for p in problems)
    assert any("does_not_prove" in p for p in problems)


def test_transform_receipt_rejects_dict_omissions_from_dict():
    d = load_fixture("transform_summary.json")
    d["omissions"] = load_fixture("omission_budget_noncritical.json")
    receipt = TransformReceipt.from_dict(d)
    assert receipt.omissions == d["omissions"]
    assert receipt.to_dict()["omissions"] == d["omissions"]
    assert any("omissions" in p for p in validate_transform_receipt(receipt))


@pytest.mark.parametrize("value", ("not-a-list", {"schema": "canon.omission/v1"}))
def test_transform_receipt_rejects_malformed_omissions_from_direct_construction(value):
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs=("record:workspace/goal-1",),
        input_span_hash="sha256:" + "a" * 64,
        output_ref="atom:goal-1",
        output_hash="sha256:" + "b" * 64,
        lossy=True,
        retained_critical_atom_ids=("goal-1",),
        omissions=value,
    )
    assert receipt.to_dict()["omissions"] == value
    assert any("omissions" in p for p in validate_transform_receipt(receipt))


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


from canon.adapter import (
    AdapterDescriptor,
    assert_requested_tier_allowed,
    builtin_descriptors,
    descriptor_for,
    validate_adapter_descriptor,
)


@pytest.mark.parametrize(
    ("fixture_name", "adapter_id", "integration_tier"),
    (
        ("adapter_codex_cli_native_advisory.json", "codex-cli", "native-advisory"),
        ("adapter_mcp_readonly_guided.json", "mcp-readonly", "guided"),
        ("adapter_a2a_artifact_guided.json", "a2a-artifact", "guided"),
    ),
)
def test_builtin_adapter_descriptor_fixtures_roundtrip(fixture_name, adapter_id, integration_tier):
    d = load_fixture(fixture_name)
    adapter = AdapterDescriptor.from_dict(d)
    assert adapter.adapter_id == adapter_id
    assert adapter.integration_tier == integration_tier
    assert adapter.to_dict() == d
    assert adapter.to_json().endswith("\n")
    assert validate_adapter_descriptor(adapter) == []


def test_builtin_descriptors_are_conservative_lowercase_and_valid():
    descriptors = builtin_descriptors()
    by_id = {d.adapter_id: d for d in descriptors}

    assert tuple(by_id) == (
        "codex-cli",
        "claude-code",
        "chatgpt-app",
        "claude-app",
        "api-runner",
        "local-runner",
        "mcp-readonly",
        "a2a-artifact",
    )
    assert all(d.adapter_id == d.adapter_id.lower() for d in descriptors)
    assert by_id["codex-cli"].integration_tier == "native-advisory"
    assert by_id["claude-code"].integration_tier == "native-advisory"
    assert by_id["chatgpt-app"].integration_tier == "guided"
    assert by_id["claude-app"].integration_tier == "guided"
    assert by_id["api-runner"].integration_tier == "guided"
    assert by_id["local-runner"].integration_tier == "guided"
    assert by_id["mcp-readonly"].integration_tier == "guided"
    assert by_id["a2a-artifact"].integration_tier == "guided"
    assert all(d.integration_tier != "enforced" for d in descriptors)
    assert all(d.bootstrap.get("can_block_before_work") is False for d in descriptors)
    assert all(validate_adapter_descriptor(d) == [] for d in descriptors)


def test_descriptor_for_uses_exact_lowercase_builtin_ids():
    assert descriptor_for("codex-cli").display_name == "Codex CLI"
    assert descriptor_for("claude-code").integration_tier == "native-advisory"
    assert descriptor_for("mcp-readonly").integration_tier == "guided"
    assert descriptor_for("a2a-artifact").display_name == "A2A Artifact"

    with pytest.raises(KeyError):
        descriptor_for("Codex-CLI")

    with pytest.raises(KeyError):
        descriptor_for("unknown-adapter")


def test_requested_tier_guard_rejects_unproved_promotion():
    guided = descriptor_for("chatgpt-app")
    native = descriptor_for("codex-cli")

    assert_requested_tier_allowed(guided, "guided")
    assert_requested_tier_allowed(guided, "unsupported")
    assert_requested_tier_allowed(native, "native-advisory")
    assert_requested_tier_allowed(native, "guided")

    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(guided, "native-advisory")

    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(native, "enforced")

    with pytest.raises(ValueError, match="unknown tier"):
        assert_requested_tier_allowed(native, "blocking")


def test_enforced_adapter_requires_blocking_evidence():
    adapter = AdapterDescriptor(
        adapter_id="closed-app",
        display_name="Closed App",
        version="0",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("paste",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": False},
        evidence_refs=(),
    )
    assert any("enforced" in p for p in validate_adapter_descriptor(adapter))


def test_enforced_adapter_with_blocking_evidence_validates():
    adapter = AdapterDescriptor(
        adapter_id="owned-wrapper",
        display_name="Owned Wrapper",
        version="1",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": True},
        evidence_refs=("fixture:owned-wrapper-blocking-start",),
    )
    assert validate_adapter_descriptor(adapter) == []
