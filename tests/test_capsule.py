from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.atom import CanonAtom
from canon.canonical_json import canonical_json_text
from canon.capsule import (
    Budget,
    Capsule,
    CapsuleBundle,
    CapsuleBuildError,
    CapsuleCompileRequest,
    CapsuleTarget,
    SourceState,
    build_capsule,
    capsule_bytes,
    capsule_digest,
    validate_capsule,
)
from canon.omission import Omission
from canon.readiness import ReadinessProbe
from canon.transform import TransformReceipt

from ._helpers import RECORD_FILES, load_record

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def read_fixture_text(name: str) -> str:
    return (FOUNDATION / name).read_text(encoding="utf-8")


def _atom(name: str) -> CanonAtom:
    return CanonAtom.from_dict(load_fixture(name))


def _target() -> CapsuleTarget:
    return CapsuleTarget("codex-cli", "CANON.md", "native-advisory")


def _source_state() -> SourceState:
    return SourceState(records_digest=HASH_A)


def _budget(profile: str = "handoff") -> Budget:
    return Budget(profile, 4096, 512, "unknown")


def _capsule_fixture() -> Capsule:
    atoms = (
        _atom("atom_permission.json"),
        _atom("atom_active_goal.json"),
        _atom("atom_prohibition.json"),
        _atom("atom_constraint.json"),
        _atom("atom_frontier_state.json"),
        _atom("atom_conflict.json"),
        _atom("atom_unknown.json"),
    )
    return build_capsule(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=atoms,
        omissions=(Omission.from_dict(load_fixture("omission_budget_noncritical.json")),),
        lossy_transforms=(TransformReceipt.from_dict(load_fixture("transform_summary.json")),),
        does_not_prove=("This capsule does not prove host-level enforcement.",),
        required_atom_ids=("goal-foundation", "perm-plan-only", "prohibit-product-code"),
    )


def test_build_capsule_is_stable_for_shuffled_inputs():
    atoms = [
        CanonAtom(
            "permission", "perm-1", "session", "ws", 1, "active",
            "normative", True, {"allowed": ["edit src/canon"]},
        ),
        CanonAtom(
            "active-goal", "goal-1", "session", "ws", 0, "active",
            "normative", True, {"summary": "build foundation"},
        ),
    ]
    kwargs = dict(
        profile="handoff",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest=HASH_A),
        budget=Budget("handoff", 4096, 512, "unknown"),
        required_atom_ids=("goal-1", "perm-1"),
    )
    a = build_capsule(atoms=atoms, **kwargs)
    b = build_capsule(atoms=list(reversed(atoms)), **kwargs)
    assert capsule_bytes(a) == capsule_bytes(b)
    assert a.capsule_id == b.capsule_id


def test_build_capsule_sorts_omissions_transforms_and_receipts():
    receipt_z = {"kind": "witness", "id": "z", "refs": ["b"]}
    receipt_a = {"kind": "witness", "id": "a", "refs": ["a"]}
    capsule = build_capsule(
        profile="archive",
        target=_target(),
        source_state=_source_state(),
        budget=Budget("archive", 8192, 2048, "unknown"),
        atoms=(),
        omissions=(
            Omission("policy", 0, (), (), False, "reference-only"),
            Omission("budget", 0, (), (), False, "omitted"),
        ),
        lossy_transforms=(
            TransformReceipt(
                "summary", "z-method", (), HASH_B, "atom:z", HASH_C, False, (),
            ),
            TransformReceipt(
                "migration", "a-method", (), HASH_B, "atom:a", HASH_C, False, (),
            ),
        ),
        receipts=(receipt_z, receipt_a),
    )
    assert [omission.reason for omission in capsule.omissions] == ["budget", "policy"]
    assert [receipt.transform for receipt in capsule.lossy_transforms] == ["migration", "summary"]
    assert [receipt["id"] for receipt in capsule.receipts] == ["a", "z"]


def test_build_capsule_fails_when_required_critical_atom_is_missing():
    with pytest.raises(CapsuleBuildError):
        build_capsule(
            profile="needle",
            target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
            source_state=SourceState(records_digest=HASH_A),
            budget=Budget("needle", 1024, 0, "unknown"),
            atoms=(),
            required_atom_ids=("goal-1",),
        )


def test_build_capsule_fails_when_required_atom_is_not_critical():
    atom = CanonAtom(
        "active-goal", "goal-1", "session", "ws", 0, "active",
        "normative", False, {"summary": "build foundation"},
    )
    with pytest.raises(CapsuleBuildError):
        build_capsule(
            profile="needle",
            target=_target(),
            source_state=_source_state(),
            budget=Budget("needle", 1024, 0, "unknown"),
            atoms=(atom,),
            required_atom_ids=("goal-1",),
        )


def test_capsule_validator_rejects_critical_omission_marked_omitted():
    capsule = build_capsule(
        profile="needle",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest=HASH_A),
        budget=Budget("needle", 1024, 0, "unknown"),
        atoms=(),
        omissions=(Omission("budget", 1, ("goal-1",), (), True, "omitted"),),
    )
    assert any("critical" in p for p in validate_capsule(capsule))


def test_capsule_identity_blanks_self_hash_fields_before_digesting():
    capsule = _capsule_fixture()
    identity = capsule.to_dict(identity=False)
    assert identity["capsule_id"] == ""
    assert identity["integrity"]["manifest_sha256"] == ""
    assert capsule.capsule_id == capsule_digest(capsule)
    assert capsule.integrity.manifest_sha256 == capsule.capsule_id


def test_capsule_derives_conflicts_unknowns_layers_and_freshness():
    capsule = _capsule_fixture()
    assert [a.id for a in capsule.conflicts] == ["conflict-enforced-tier"]
    assert [a.id for a in capsule.unknowns] == ["unknown-closed-app-hooks"]
    assert "session" in capsule.layers
    assert "project" in capsule.layers
    assert any(row["id"] == "goal-foundation" for row in capsule.freshness)


def test_build_capsule_includes_records_as_record_derived_atoms():
    record = load_record(RECORD_FILES["personality-block"])
    capsule = build_capsule(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=(),
        records=(record,),
    )
    assert capsule.records == (record,)
    assert [(atom.type, atom.id, atom.layer) for atom in capsule.atoms] == [
        ("instruction", "voice-canon", "workspace")
    ]


def test_capsule_roundtrips_from_dict():
    capsule = _capsule_fixture()
    got = Capsule.from_dict(capsule.to_dict())
    assert got == capsule
    assert validate_capsule(got) == []


def test_capsule_uses_tuple_storage_and_defensive_copies():
    receipts = [{"id": "receipt-1", "refs": ["source-a"]}]
    does_not_prove = ["This capsule does not prove host-level enforcement."]
    capsule = build_capsule(
        profile="handoff",
        target=_target(),
        source_state=SourceState(records_digest=HASH_A, inventory_digest=HASH_B),
        budget=_budget(),
        atoms=(_atom("atom_active_goal.json"),),
        receipts=receipts,
        does_not_prove=does_not_prove,
    )
    receipts[0]["refs"].append("mutated")
    does_not_prove.append("mutated")
    as_dict = capsule.to_dict()
    as_dict["receipts"][0]["refs"].append("dict-mutation")
    as_dict["does_not_prove"].append("dict-mutation")
    assert capsule.receipts == ({"id": "receipt-1", "refs": ["source-a"]},)
    assert capsule.does_not_prove == ("This capsule does not prove host-level enforcement.",)


def test_capsule_from_dict_preserves_malformed_nested_values_for_total_validation():
    d = _capsule_fixture().to_dict()
    d["atoms"] = [{"atom_schema": "canon.atom/v1"}]
    d["records"] = [{"canon_schema": "canon.record/v1"}]
    d["omissions"] = [{"schema": "canon.omission/v1"}]
    d["lossy_transforms"] = [{"schema": "canon.transform-receipt/v1"}]
    capsule = Capsule.from_dict(d)
    assert capsule.to_dict()["atoms"] == [{"atom_schema": "canon.atom/v1"}]
    assert capsule.to_dict()["records"] == [{"canon_schema": "canon.record/v1"}]
    assert any("atoms" in p for p in validate_capsule(capsule))
    assert any("records" in p for p in validate_capsule(capsule))
    assert any("omissions" in p for p in validate_capsule(capsule))
    assert any("lossy_transforms" in p for p in validate_capsule(capsule))


def test_capsule_from_dict_preserves_malformed_value_objects_for_validation():
    d = _capsule_fixture().to_dict()
    d["compatibility"] = {"capsule_schema": "canon.capsule/v1"}
    d["budget"] = {"profile": "handoff", "max_tokens": 4096}
    capsule = Capsule.from_dict(d)
    assert capsule.to_dict()["compatibility"] == {"capsule_schema": "canon.capsule/v1"}
    assert capsule.to_dict()["budget"] == {"profile": "handoff", "max_tokens": 4096}
    problems = validate_capsule(capsule)
    assert any("compatibility" in p for p in problems)
    assert any("budget" in p for p in problems)


def test_capsule_validator_rejects_manual_unsorted_ordering():
    d = _capsule_fixture().to_dict()
    d["atoms"] = list(reversed(d["atoms"]))
    d["omissions"] = [
        Omission("policy", 0, (), (), False, "reference-only").to_dict(),
        Omission("budget", 0, (), (), False, "omitted").to_dict(),
    ]
    d["receipts"] = [{"id": "z"}, {"id": "a"}]
    capsule = Capsule.from_dict(d)
    problems = validate_capsule(capsule)
    assert any("atoms" in p and "sorted" in p for p in problems)
    assert any("omissions" in p and "sorted" in p for p in problems)
    assert any("receipts" in p and "sorted" in p for p in problems)


def test_capsule_validator_reports_multiple_shape_problems():
    capsule = Capsule(
        capsule_id="bad",
        profile="bad",
        target=[],
        source_state=[],
        compatibility=[],
        budget=Budget("bad", -1, True, ""),
        layers="session",
        atoms=[object()],
        records=[object()],
        conflicts=[object()],
        unknowns=[object()],
        omissions=[object()],
        lossy_transforms=[object()],
        freshness="current",
        integrity=[],
        receipts="receipt",
        does_not_prove=[object()],
    )
    problems = validate_capsule(capsule)
    assert any("capsule_id" in p for p in problems)
    assert any("profile" in p for p in problems)
    assert any("target" in p for p in problems)
    assert any("source_state" in p for p in problems)
    assert any("compatibility" in p for p in problems)
    assert any("budget.max_tokens" in p for p in problems)
    assert any("layers" in p for p in problems)
    assert any("atoms" in p for p in problems)
    assert any("records" in p for p in problems)
    assert any("freshness" in p for p in problems)
    assert any("integrity" in p for p in problems)
    assert any("receipts" in p for p in problems)
    assert any("does_not_prove" in p for p in problems)


def test_compile_request_and_bundle_are_plain_value_objects():
    request = CapsuleCompileRequest(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=(_atom("atom_active_goal.json"),),
        required_atom_ids=("goal-foundation",),
        readiness_probe_id="probe-foundation-1",
    )
    capsule = _capsule_fixture()
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    bundle = CapsuleBundle(
        capsule=capsule,
        manifest_bytes=capsule_bytes(capsule),
        canon_md="# CANON\n",
        readiness_probe=probe,
    )
    assert request.readiness_probe_id == "probe-foundation-1"
    assert bundle.capsule == capsule
    assert bundle.manifest_bytes == capsule_bytes(capsule)
    assert bundle.readiness_probe.probe_id == "probe-foundation-1"


@pytest.mark.parametrize("name", ("capsule_minimal_needle.json", "capsule_handoff_full.json"))
def test_capsule_fixture_matches_canonical_json_bytes(name: str):
    d = load_fixture(name)
    capsule = Capsule.from_dict(d)
    assert read_fixture_text(name) == canonical_json_text(d)
    assert capsule.to_dict() == d
    assert capsule.capsule_id == capsule_digest(capsule)
    assert capsule.integrity.manifest_sha256 == capsule.capsule_id
    assert validate_capsule(capsule) == []


def test_locked_capsule_fixtures_capture_minimal_and_full_profiles():
    minimal = Capsule.from_dict(load_fixture("capsule_minimal_needle.json"))
    full = Capsule.from_dict(load_fixture("capsule_handoff_full.json"))
    assert minimal.profile == "needle"
    assert [atom.id for atom in minimal.atoms] == ["goal-foundation"]
    assert minimal.omissions == ()
    assert full.profile == "handoff"
    assert [atom.id for atom in full.atoms] == [
        "goal-foundation",
        "frontier-foundation-next",
        "perm-plan-only",
        "prohibit-product-code",
        "conflict-enforced-tier",
        "constraint-stdlib",
        "unknown-closed-app-hooks",
    ]
    assert [atom.id for atom in full.conflicts] == ["conflict-enforced-tier"]
    assert [atom.id for atom in full.unknowns] == ["unknown-closed-app-hooks"]
    assert len(full.omissions) == 1
    assert len(full.lossy_transforms) == 1
    assert full.does_not_prove == ("This capsule does not prove host-level enforcement.",)


def test_validators_are_total_and_list_returning():
    assert isinstance(validate_capsule(object()), list)
