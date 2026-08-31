from __future__ import annotations

import json
from pathlib import Path
from typing import get_type_hints

import pytest

from canon.canonical_json import canonical_json_text
from canon.omission import Omission
from canon.readiness import ReadinessResult
from canon.transform import TransformReceipt
from canon.witness import BootstrapCheck, BootstrapWitness, validate_bootstrap_witness

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def read_fixture_text(name: str) -> str:
    return (FOUNDATION / name).read_text(encoding="utf-8")


def fixture_witness(**overrides) -> BootstrapWitness:
    d = load_fixture("bootstrap_witness_pass.json")
    d.update(overrides)
    return BootstrapWitness.from_dict(d)


def check_dict(name: str = "readiness", verdict: str = "pass", evidence: bool = True) -> dict:
    refs = ["capsule:" + HASH_A] if evidence else []
    return {"details": {}, "evidence_refs": refs, "name": name, "verdict": verdict}


def test_bootstrap_witness_roundtrips_and_validates():
    d = load_fixture("bootstrap_witness_pass.json")
    witness = BootstrapWitness.from_dict(d)
    assert witness.to_dict() == d
    assert witness.to_json().endswith("\n")
    assert validate_bootstrap_witness(witness) == []


def test_bootstrap_witness_fixture_matches_canonical_json_bytes():
    d = load_fixture("bootstrap_witness_pass.json")
    assert read_fixture_text("bootstrap_witness_pass.json") == canonical_json_text(d)
    assert BootstrapWitness.from_dict(d).to_json() == canonical_json_text(d)


def test_enforced_witness_cannot_claim_observed_without_pass_readiness():
    result = ReadinessResult(
        "probe-1",
        HASH_A,
        "fail",
        {},
        ("goal-1",),
        (),
        HASH_B,
    )
    witness = BootstrapWitness(
        run_id="run-1",
        capsule_id=HASH_A,
        capsule_manifest_sha256=HASH_A,
        source_state={"records_digest": HASH_C},
        target={"adapter": "codex-cli", "surface": "CANON.md"},
        integration_tier_claimed="enforced",
        host_enforcement_observed=True,
        started_at="2026-08-30T00:00:00Z",
        checks=(BootstrapCheck("readiness", "fail"),),
        omissions=(),
        lossy_transforms=(),
        readiness_result=result,
    )
    assert any("readiness" in p for p in validate_bootstrap_witness(witness))


def test_enforced_observed_witness_requires_all_checks_passed():
    witness = BootstrapWitness.from_dict(load_fixture("bootstrap_witness_pass.json"))
    enforced = BootstrapWitness(
        run_id=witness.run_id,
        capsule_id=witness.capsule_id,
        capsule_manifest_sha256=witness.capsule_manifest_sha256,
        source_state=witness.source_state,
        target=witness.target,
        integration_tier_claimed="enforced",
        host_enforcement_observed=True,
        started_at=witness.started_at,
        checks=(BootstrapCheck("readiness", "pass", ("capsule:" + HASH_A,), {}), BootstrapCheck("secrets", "unknown")),
        omissions=witness.omissions,
        lossy_transforms=witness.lossy_transforms,
        readiness_result=witness.readiness_result,
        does_not_prove=witness.does_not_prove,
    )
    assert any("checks" in p and "pass" in p for p in validate_bootstrap_witness(enforced))


def test_enforced_observed_witness_requires_check_evidence():
    witness = BootstrapWitness.from_dict(load_fixture("bootstrap_witness_pass.json"))
    enforced = BootstrapWitness(
        run_id=witness.run_id,
        capsule_id=witness.capsule_id,
        capsule_manifest_sha256=witness.capsule_manifest_sha256,
        source_state=witness.source_state,
        target=witness.target,
        integration_tier_claimed="enforced",
        host_enforcement_observed=True,
        started_at=witness.started_at,
        checks=(BootstrapCheck("readiness", "pass"),),
        omissions=witness.omissions,
        lossy_transforms=witness.lossy_transforms,
        readiness_result=witness.readiness_result,
        does_not_prove=witness.does_not_prove,
    )
    assert any("evidence_refs" in p for p in validate_bootstrap_witness(enforced))


def test_bootstrap_witness_public_annotations_match_nested_contract():
    hints = get_type_hints(BootstrapWitness)
    assert hints["checks"] == tuple[BootstrapCheck, ...]
    assert hints["omissions"] == tuple[Omission, ...]
    assert hints["lossy_transforms"] == tuple[TransformReceipt, ...]
    assert hints["readiness_result"] is ReadinessResult


@pytest.mark.parametrize("tier", ("native-advisory", "guided", "unsupported"))
def test_observed_host_enforcement_requires_enforced_tier(tier: str):
    witness = fixture_witness(
        integration_tier_claimed=tier,
        host_enforcement_observed=True,
        checks=[check_dict()],
    )
    assert any("integration_tier_claimed" in p and "enforced" in p for p in validate_bootstrap_witness(witness))


@pytest.mark.parametrize(
    ("overrides", "want"),
    (
        ({"checks": []}, "readiness check"),
        ({"readiness_result": {"schema": "canon.readiness-result/v1"}}, "readiness_result"),
        ({"checks": [check_dict(), check_dict("secrets", "warn")]}, "checks"),
        ({"checks": [check_dict(evidence=False)]}, "evidence_refs"),
    ),
)
def test_enforced_observed_claim_requires_complete_readiness_and_evidence(overrides: dict, want: str):
    witness = fixture_witness(
        integration_tier_claimed="enforced",
        host_enforcement_observed=True,
        **overrides,
    )
    assert any(want in p for p in validate_bootstrap_witness(witness))


def test_native_advisory_witness_may_record_no_host_enforcement():
    witness = BootstrapWitness.from_dict(load_fixture("bootstrap_witness_pass.json"))
    assert witness.integration_tier_claimed == "native-advisory"
    assert witness.host_enforcement_observed is False
    assert validate_bootstrap_witness(witness) == []


def test_bootstrap_witness_reconstructs_nested_receipts():
    d = load_fixture("bootstrap_witness_pass.json")
    omission = load_fixture("omission_budget_noncritical.json")
    transform = load_fixture("transform_summary.json")
    transform["omissions"] = [omission]
    d["omissions"] = [omission]
    d["lossy_transforms"] = [transform]

    witness = BootstrapWitness.from_dict(d)

    assert isinstance(witness.checks[0], BootstrapCheck)
    assert isinstance(witness.omissions[0], Omission)
    assert isinstance(witness.lossy_transforms[0], TransformReceipt)
    assert isinstance(witness.lossy_transforms[0].omissions[0], Omission)
    assert isinstance(witness.readiness_result, ReadinessResult)
    assert witness.to_dict() == d
    assert validate_bootstrap_witness(witness) == []


def test_bootstrap_witness_uses_defensive_copies_for_nested_values():
    source_state = {"records_digest": HASH_C}
    target = {"adapter": "codex-cli", "surface": "CANON.md"}
    details = {"observed": ["readiness"]}
    checks = [BootstrapCheck("readiness", "pass", ["capsule:" + HASH_A], details)]
    does_not_prove = ["This witness does not prove host-level blocking."]

    witness = BootstrapWitness(
        "run-1", HASH_A, HASH_A, source_state, target, "native-advisory", False,
        "2026-08-30T00:00:00Z", checks, [], [], ReadinessResult("probe-1", HASH_A, "pass", {}, (), (), HASH_B),
        does_not_prove,
    )
    source_state["records_digest"] = "mutated"
    target["adapter"] = "mutated"
    details["observed"].append("mutated")
    checks.append(BootstrapCheck("secrets", "pass"))
    does_not_prove.append("mutated")
    as_dict = witness.to_dict()
    as_dict["source_state"]["records_digest"] = "dict-mutation"
    as_dict["checks"][0]["details"]["observed"].append("dict-mutation")
    as_dict["does_not_prove"].append("dict-mutation")

    assert witness.source_state == {"records_digest": HASH_C}
    assert witness.target == {"adapter": "codex-cli", "surface": "CANON.md"}
    assert witness.checks[0].details == {"observed": ["readiness"]}
    assert witness.does_not_prove == ("This witness does not prove host-level blocking.",)


@pytest.mark.parametrize("field", ("checks", "omissions", "lossy_transforms", "does_not_prove"))
def test_bootstrap_witness_rejects_scalar_sequence_fields(field: str):
    d = load_fixture("bootstrap_witness_pass.json")
    d[field] = "not-a-list"
    witness = BootstrapWitness.from_dict(d)
    assert witness.to_dict()[field] == "not-a-list"
    assert any(field in p for p in validate_bootstrap_witness(witness))


def test_source_state_requires_records_digest():
    witness = fixture_witness(source_state={})
    assert any("source_state.records_digest" in p for p in validate_bootstrap_witness(witness))


@pytest.mark.parametrize(
    "field",
    ("records_digest", "inventory_digest", "context_envelope_digest", "mneme_snapshot_digest", "worktree_digest"),
)
def test_source_state_validates_known_digest_fields(field: str):
    state = {"records_digest": HASH_C, field: "not-a-sha256-ref"}
    witness = fixture_witness(source_state=state)
    assert any(f"source_state.{field}" in p for p in validate_bootstrap_witness(witness))


@pytest.mark.parametrize("target", ({}, {"adapter": "", "surface": "CANON.md"}, {"adapter": "codex-cli", "surface": ""}))
def test_target_requires_adapter_and_surface_strings(target: dict):
    witness = fixture_witness(target=target)
    problems = validate_bootstrap_witness(witness)
    assert any("target.adapter" in p or "target.surface" in p for p in problems)


def test_from_dict_preserves_malformed_nested_values_for_total_to_dict():
    d = load_fixture("bootstrap_witness_pass.json")
    d["checks"] = [{"name": "readiness"}]
    d["omissions"] = [{"schema": "canon.omission/v1"}]
    d["lossy_transforms"] = [{"schema": "canon.transform-receipt/v1"}]
    d["readiness_result"] = {"schema": "canon.readiness-result/v1"}
    witness = BootstrapWitness.from_dict(d)
    assert witness.to_dict()["checks"] == [{"name": "readiness"}]
    assert witness.to_dict()["omissions"] == [{"schema": "canon.omission/v1"}]
    assert witness.to_dict()["lossy_transforms"] == [{"schema": "canon.transform-receipt/v1"}]
    assert witness.to_dict()["readiness_result"] == {"schema": "canon.readiness-result/v1"}
    assert any("checks" in p for p in validate_bootstrap_witness(witness))


def test_bootstrap_witness_validator_reports_multiple_shape_problems():
    witness = BootstrapWitness(
        run_id="",
        capsule_id="bad",
        capsule_manifest_sha256="bad",
        source_state=[],
        target=[],
        integration_tier_claimed="blocking",
        host_enforcement_observed="yes",
        started_at="",
        checks=({"name": "readiness"},),
        omissions=({"schema": "canon.omission/v1"},),
        lossy_transforms=({"schema": "canon.transform-receipt/v1"},),
        readiness_result={"schema": "canon.readiness-result/v1"},
        does_not_prove=("ok", 1),
    )
    problems = validate_bootstrap_witness(witness)
    assert any("run_id" in p for p in problems)
    assert any("capsule_id" in p for p in problems)
    assert any("capsule_manifest_sha256" in p for p in problems)
    assert any("source_state" in p for p in problems)
    assert any("target" in p for p in problems)
    assert any("integration_tier_claimed" in p for p in problems)
    assert any("host_enforcement_observed" in p for p in problems)
    assert any("started_at" in p for p in problems)
    assert any("checks" in p for p in problems)
    assert any("omissions" in p for p in problems)
    assert any("lossy_transforms" in p for p in problems)
    assert any("readiness_result" in p for p in problems)
    assert any("does_not_prove" in p for p in problems)


def test_validators_are_total_and_list_returning():
    malformed = BootstrapWitness.from_dict(load_fixture("bootstrap_witness_pass.json"))
    malformed = BootstrapWitness(
        malformed.run_id, malformed.capsule_id, malformed.capsule_manifest_sha256,
        malformed.source_state, malformed.target, malformed.integration_tier_claimed,
        malformed.host_enforcement_observed, malformed.started_at, [object()],
        [object()], [object()], object(), [object()],
    )
    assert isinstance(validate_bootstrap_witness(object()), list)
    assert isinstance(validate_bootstrap_witness(malformed), list)
