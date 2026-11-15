from __future__ import annotations

from dataclasses import fields
from inspect import Parameter, signature
from typing import get_type_hints

import pytest


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_F = "sha256:" + "f" * 64


def test_foundation_cli_contract_imports() -> None:
    from canon.adapter import AdapterDescriptor, assert_requested_tier_allowed, descriptor_for
    from canon.atom import CanonAtom, atoms_from_records, load_atoms_jsonl, validate_atom
    from canon.canonical_json import canonical_json_bytes, canonical_json_text, sha256_bytes, sha256_text
    from canon.canonmd import render_canon_md
    from canon.capsule import (
        Budget,
        Capsule,
        CapsuleBundle,
        CapsuleCompileRequest,
        CapsuleTarget,
        SourceState,
        compile_capsule,
        validate_capsule,
    )
    from canon.import_review import ImportItem, review_import_items
    from canon.path_policy import (
        PathPolicyError,
        PathPolicyViolation,
        assert_not_protected,
        assert_operational_surface_path,
        assert_operational_vault_path,
        resolve_under_root,
    )
    from canon.readiness import ReadinessProbe, ReadinessResult, evaluate_readiness_response
    from canon.source_state import SourceStateItem, assert_source_state, source_state_sha256
    from canon.witness import BootstrapCheck, BootstrapWitness, validate_bootstrap_witness

    assert AdapterDescriptor.__name__ == "AdapterDescriptor"
    assert CanonAtom.__name__ == "CanonAtom"
    assert callable(assert_requested_tier_allowed)
    assert callable(descriptor_for)
    assert callable(atoms_from_records)
    assert callable(load_atoms_jsonl)
    assert callable(validate_atom)
    assert callable(canonical_json_bytes)
    assert callable(canonical_json_text)
    assert callable(sha256_bytes)
    assert callable(sha256_text)
    assert callable(render_canon_md)
    assert callable(compile_capsule)
    assert callable(validate_capsule)
    assert callable(evaluate_readiness_response)
    assert callable(validate_bootstrap_witness)
    assert callable(review_import_items)
    assert callable(resolve_under_root)
    assert callable(assert_not_protected)
    assert callable(assert_operational_surface_path)
    assert callable(assert_operational_vault_path)
    assert callable(assert_source_state)
    assert callable(source_state_sha256)
    assert ImportItem.__name__ == "ImportItem"
    assert PathPolicyError.__name__ == "PathPolicyError"
    assert PathPolicyViolation.__name__ == "PathPolicyViolation"
    assert SourceStateItem.__name__ == "SourceStateItem"
    assert ReadinessProbe.__name__ == "ReadinessProbe"
    assert ReadinessResult.__name__ == "ReadinessResult"
    assert BootstrapCheck.__name__ == "BootstrapCheck"
    assert BootstrapWitness.__name__ == "BootstrapWitness"
    assert Budget.__name__ == "Budget"
    assert Capsule.__name__ == "Capsule"
    assert CapsuleTarget.__name__ == "CapsuleTarget"
    assert SourceState.__name__ == "SourceState"
    assert CapsuleBundle.__name__ == "CapsuleBundle"
    assert CapsuleCompileRequest.__name__ == "CapsuleCompileRequest"


def test_foundation_schema_constants_and_layouts_are_authoritative() -> None:
    from canon.adapter import ADAPTER_SCHEMA, INTEGRATION_TIERS, AdapterDescriptor
    from canon.atom import (
        ATOM_CLASSIFICATIONS,
        ATOM_LAYERS,
        ATOM_SCHEMA,
        ATOM_STATUSES,
        ATOM_TYPES,
        CanonAtom,
    )
    from canon.capsule import (
        CANONICALIZATION,
        CAPSULE_PROFILES,
        CAPSULE_SCHEMA,
        SOURCE_STATE_DIGEST_KEYS,
        Budget,
        Capsule,
        CapsuleBundle,
        CapsuleCompileRequest,
        CapsuleTarget,
        SourceState,
    )
    from canon.readiness import (
        CRITICAL_SET_KEYS,
        READINESS_PROBE_SCHEMA,
        READINESS_RESULT_SCHEMA,
        READINESS_VERDICTS,
        ReadinessProbe,
        ReadinessResult,
    )
    from canon.witness import (
        BOOTSTRAP_CHECK_NAMES,
        BOOTSTRAP_CHECK_VERDICTS,
        BOOTSTRAP_WITNESS_SCHEMA,
        BootstrapCheck,
        BootstrapWitness,
    )

    assert ADAPTER_SCHEMA == "canon.adapter/v1"
    assert INTEGRATION_TIERS == ("enforced", "native-advisory", "guided", "unsupported")
    assert ATOM_SCHEMA == "canon.atom/v1"
    assert ATOM_TYPES == (
        "instruction",
        "active-goal",
        "permission",
        "prohibition",
        "constraint",
        "decision",
        "frontier-state",
        "evidence-ref",
        "episodic-fact",
        "synthesized-persona",
        "conflict",
        "unknown",
        "omission",
        "lossy-transform",
        "bootstrap-probe",
        "bootstrap-witness",
        "adapter-capability",
    )
    assert ATOM_LAYERS == (
        "session",
        "task",
        "project",
        "repo",
        "workspace",
        "personal",
        "team",
        "organization",
        "imported-history",
    )
    assert ATOM_STATUSES == (
        "active",
        "retired",
        "superseded",
        "stale",
        "contradictory",
        "untrusted",
        "unknown",
        "blocked",
    )
    assert ATOM_CLASSIFICATIONS == ("normative", "descriptive", "derived", "receipt")
    assert CAPSULE_SCHEMA == "canon.capsule/v1"
    assert CAPSULE_PROFILES == ("needle", "handoff", "archive", "custom")
    assert CANONICALIZATION == "json-sorted-compact-lf"
    assert SOURCE_STATE_DIGEST_KEYS == (
        "records_digest",
        "inventory_digest",
        "context_envelope_digest",
        "mneme_snapshot_digest",
        "relay_checkpoint",
        "worktree_digest",
    )
    assert READINESS_PROBE_SCHEMA == "canon.readiness-probe/v1"
    assert READINESS_RESULT_SCHEMA == "canon.readiness-result/v1"
    assert READINESS_VERDICTS == ("pass", "fail", "blocked", "unknown")
    assert CRITICAL_SET_KEYS == (
        "active_goal_ids",
        "permission_ids",
        "prohibition_ids",
        "constraint_ids",
        "frontier_state_ids",
        "unresolved_conflict_ids",
        "unknown_ids",
    )
    assert BOOTSTRAP_WITNESS_SCHEMA == "canon.bootstrap-witness/v1"
    assert BOOTSTRAP_CHECK_NAMES == (
        "freshness",
        "conflicts",
        "secrets",
        "budget",
        "reachability",
        "readiness",
    )
    assert BOOTSTRAP_CHECK_VERDICTS == ("pass", "fail", "warn", "blocked", "unknown")
    assert _field_names(AdapterDescriptor) == (
        "adapter_id",
        "display_name",
        "version",
        "integration_tier",
        "target_surfaces",
        "import_modes",
        "export_modes",
        "bootstrap",
        "losses",
        "limits",
        "auth",
        "privacy",
        "evidence_refs",
        "known_unknowns",
        "last_verified",
        "owner",
        "retirement_trigger",
    )
    assert _field_names(CanonAtom) == (
        "type",
        "id",
        "layer",
        "scope_key",
        "precedence_rank",
        "status",
        "classification",
        "critical",
        "value",
        "source_refs",
        "source_span_refs",
        "freshness",
        "trust",
        "disclosure",
        "hashes",
    )
    assert _field_names(CapsuleTarget) == (
        "adapter",
        "surface",
        "integration_tier",
        "host_enforcement_observed",
    )
    assert _field_names(SourceState) == (
        "records_digest",
        "inventory_digest",
        "context_envelope_digest",
        "mneme_snapshot_digest",
        "relay_checkpoint",
        "worktree_digest",
    )
    assert _field_names(Budget) == (
        "profile",
        "max_tokens",
        "estimated_tokens",
        "estimator",
        "policy",
    )
    assert _field_names(Capsule) == (
        "capsule_id",
        "profile",
        "target",
        "source_state",
        "compatibility",
        "budget",
        "layers",
        "atoms",
        "records",
        "conflicts",
        "unknowns",
        "omissions",
        "lossy_transforms",
        "freshness",
        "integrity",
        "receipts",
        "does_not_prove",
    )
    assert _field_names(CapsuleCompileRequest) == (
        "profile",
        "target",
        "source_state",
        "budget",
        "atoms",
        "records",
        "omissions",
        "lossy_transforms",
        "receipts",
        "does_not_prove",
        "required_atom_ids",
        "readiness_probe_id",
        "readiness_target",
    )
    assert _field_names(CapsuleBundle) == ("capsule", "manifest_bytes", "canon_md", "readiness_probe")
    assert _field_names(ReadinessProbe) == (
        "probe_id",
        "capsule_id",
        "target",
        "critical_sets",
        "challenge",
        "checker",
    )
    assert _field_names(ReadinessResult) == (
        "probe_id",
        "capsule_id",
        "verdict",
        "reported",
        "missing_ids",
        "mismatched_ids",
        "response_hash",
        "does_not_prove",
    )
    assert _field_names(BootstrapCheck) == ("name", "verdict", "evidence_refs", "details")
    assert _field_names(BootstrapWitness) == (
        "run_id",
        "capsule_id",
        "capsule_manifest_sha256",
        "source_state",
        "target",
        "integration_tier_claimed",
        "host_enforcement_observed",
        "started_at",
        "checks",
        "omissions",
        "lossy_transforms",
        "readiness_result",
        "does_not_prove",
    )


def test_foundation_behavior_contracts_are_not_only_importable() -> None:
    from canon.adapter import assert_requested_tier_allowed, descriptor_for, validate_adapter_descriptor
    from canon.atom import CanonAtom, validate_atom
    from canon.canonmd import CANON_MD_SECTIONS, parse_canon_md_carrier, render_canon_md, verify_canon_md
    from canon.capsule import Budget, CapsuleCompileRequest, CapsuleTarget, SourceState, compile_capsule, validate_capsule
    from canon.readiness import ReadinessProbe, ReadinessResult, evaluate_readiness_response, validate_readiness_probe
    from canon.witness import BootstrapCheck, BootstrapWitness, validate_bootstrap_witness

    descriptor = descriptor_for("codex-cli")
    assert descriptor.integration_tier == "native-advisory"
    assert descriptor.target_surfaces == ("CANON.md", "AGENTS.md")
    assert descriptor.bootstrap == {"can_block_before_work": False, "mode": "native-context-file"}
    assert validate_adapter_descriptor(descriptor) == []
    assert_requested_tier_allowed(descriptor, "native-advisory")
    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(descriptor, "enforced")

    atom = CanonAtom(
        "active-goal",
        "goal-contract",
        "session",
        "workspace:canon",
        0,
        "active",
        "normative",
        True,
        {"summary": "guard CLI prerequisites"},
    )
    assert validate_atom(atom) == []
    assert validate_atom(object()) == ["atom must be a CanonAtom, got object"]

    request = CapsuleCompileRequest(
        profile="handoff",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest=HASH_A),
        budget=Budget("handoff", 4096, 128, "unknown"),
        atoms=(atom,),
        required_atom_ids=("goal-contract",),
        readiness_probe_id="probe-contract",
    )
    bundle = compile_capsule(request)
    assert validate_capsule(bundle.capsule) == []
    assert validate_capsule(object()) == ["capsule must be a Capsule"]
    assert CANON_MD_SECTIONS == (
        "Capsule identity",
        "Target and integration tier",
        "Freshness, trust, and unknowns",
        "Active goals",
        "Authority, permissions, prohibitions, and constraints",
        "Current frontier and working state",
        "Decisions and rationale",
        "Conflicts requiring resolution",
        "Canonical instructions",
        "Evidence references",
        "Omissions",
        "Lossy transforms",
        "Bootstrap readiness probe",
        "Does-not-prove",
    )
    rendered = render_canon_md(bundle.capsule)
    assert rendered.splitlines()[0] == "# CANON"
    assert rendered.splitlines()[1].startswith("<!-- canon:capsule/v1 digest=sha256:")
    assert parse_canon_md_carrier(rendered) == bundle.capsule.to_dict()
    assert verify_canon_md(rendered, bundle.capsule) == []
    assert any("body drift" in problem for problem in verify_canon_md(rendered.replace("## Active goals", "## Active goals\n\nTampered", 1)))

    probe = ReadinessProbe("probe-contract", bundle.capsule.capsule_id, {}, {"active_goal_ids": ("goal-contract",)}, {}, {})
    readiness = evaluate_readiness_response(probe, {"active_goal_ids": []})
    assert readiness.verdict == "fail"
    assert readiness.missing_ids == ("goal-contract",)
    assert validate_readiness_probe(object()) == ["readiness probe must be a ReadinessProbe"]

    witness = BootstrapWitness(
        "run-contract",
        bundle.capsule.capsule_id,
        bundle.capsule.capsule_id,
        {"records_digest": HASH_A},
        {"adapter": "codex-cli", "surface": "CANON.md"},
        "native-advisory",
        False,
        "2026-08-30T00:00:00Z",
        (BootstrapCheck("readiness", "pass", ("capsule:" + bundle.capsule.capsule_id,), {}),),
        (),
        (),
        ReadinessResult("probe-contract", bundle.capsule.capsule_id, "pass", {}, (), (), HASH_B),
    )
    assert validate_bootstrap_witness(witness) == []
    bad = BootstrapWitness(
        "",
        "bad",
        "bad",
        [],
        [],
        "blocking",
        "yes",
        "",
        ({"name": "readiness"},),
        (),
        (),
        object(),
    )
    problems = validate_bootstrap_witness(bad)
    assert any("run_id" in problem for problem in problems)
    assert any("target" in problem for problem in problems)


def test_security_source_state_contracts_are_authoritative() -> None:
    from canon.source_state import (
        SourceStateError,
        SourceStateItem,
        assert_source_state,
        canonical_source_state,
        source_state_sha256,
    )

    assert _field_names(SourceStateItem) == ("path", "sha256", "size")
    a = SourceStateItem(path="b.md", sha256=HASH_B, size=2)
    b = SourceStateItem(path="a.md", sha256=HASH_A, size=1)
    canonical = canonical_source_state((a, b))
    assert canonical == (
        b'[{"path":"a.md","sha256":"sha256:'
        + b"a" * 64
        + b'","size":1},{"path":"b.md","sha256":"sha256:'
        + b"b" * 64
        + b'","size":2}]\n'
    )
    assert source_state_sha256((a, b)) == "sha256:5f133a4d9a5a2344a980695f27aff749e2ec776a7d300a13736919ea96cac753"
    with pytest.raises(SourceStateError) as mismatch:
        assert_source_state(HASH_F, (b,))
    assert mismatch.value.code == "source_changed"
    assert str(mismatch.value).startswith("source_changed: expected sha256:")
    with pytest.raises(SourceStateError) as invalid:
        canonical_source_state([b])  # type: ignore[arg-type]
    assert invalid.value.code == "invalid-source-state"


def test_security_path_policy_contracts_are_authoritative(tmp_path) -> None:
    from canon.path_policy import (
        PathPolicyViolation,
        assert_not_protected,
        assert_operational_surface_path,
        assert_operational_vault_path,
        resolve_under_root,
    )

    assert _field_names(PathPolicyViolation) == ("code", "path", "reason")

    resolve_sig = signature(resolve_under_root)
    assert tuple(resolve_sig.parameters) == ("path", "root", "must_exist", "reject_reparse")
    assert resolve_sig.parameters["path"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert resolve_sig.parameters["root"].kind is Parameter.KEYWORD_ONLY
    assert resolve_sig.parameters["root"].default is Parameter.empty
    assert resolve_sig.parameters["must_exist"].kind is Parameter.KEYWORD_ONLY
    assert resolve_sig.parameters["must_exist"].default is False
    assert resolve_sig.parameters["reject_reparse"].kind is Parameter.KEYWORD_ONLY
    assert resolve_sig.parameters["reject_reparse"].default is True

    surface_sig = signature(assert_operational_surface_path)
    assert tuple(surface_sig.parameters) == ("path", "root")
    assert surface_sig.parameters["path"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert surface_sig.parameters["root"].kind is Parameter.KEYWORD_ONLY
    assert surface_sig.parameters["root"].default is Parameter.empty

    vault_sig = signature(assert_operational_vault_path)
    assert tuple(vault_sig.parameters) == ("path", "vault")
    assert vault_sig.parameters["path"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert vault_sig.parameters["vault"].kind is Parameter.KEYWORD_ONLY
    assert vault_sig.parameters["vault"].default is Parameter.empty

    root = tmp_path / "root"
    vault = tmp_path / "vault"
    root.mkdir()
    vault.mkdir()
    surface = root / "docs" / "AGENTS.md"
    note = vault / "workspace" / "note.md"
    assert resolve_under_root(surface, root=root) == surface.resolve()
    assert assert_operational_surface_path(surface, root=root) == surface.resolve()
    assert assert_operational_vault_path(note, vault=vault) == note.resolve()

    assert _path_policy_codes(lambda: resolve_under_root(root / ".." / "escape.md", root=root)) == (
        "outside-root",
    )
    assert _path_policy_codes(lambda: resolve_under_root(root, root=root)) == ("root-target",)
    assert _path_policy_codes(lambda: resolve_under_root("AGENTS.md:secret", root=root)) == ("ads",)
    assert _path_policy_codes(lambda: assert_not_protected(root / ".env")) == ("protected-path",)
    assert _path_policy_codes(lambda: assert_not_protected(root / ".aws" / "credentials")) == (
        "protected-path",
        "protected-path",
    )


def test_security_import_review_contracts_are_authoritative() -> None:
    from canon.atom import CanonAtom
    from canon.import_review import ImportFinding, ImportItem, ImportReview, review_import_items
    from canon.source_state import SourceStateItem, source_state_sha256

    assert _field_names(ImportItem) == (
        "source_id",
        "atom",
        "text",
        "signature_status",
        "key_id",
        "local",
        "model_synthesized",
        "replay_nonce",
        "replay_expires_ord",
    )
    assert _field_names(ImportFinding) == ("code", "severity", "subject_id", "message")
    assert _field_names(ImportReview) == ("ok", "findings", "accepted_atoms", "omissions", "receipts")

    sig = signature(review_import_items)
    assert tuple(sig.parameters) == (
        "items",
        "profile",
        "pinned_key_ids",
        "expected_source_state",
        "current_source_items",
        "seen_replay_keys",
        "current_ord",
    )
    assert sig.parameters["items"].kind is Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        sig.parameters[name].kind is Parameter.KEYWORD_ONLY
        for name in (
            "profile",
            "pinned_key_ids",
            "expected_source_state",
            "current_source_items",
            "seen_replay_keys",
            "current_ord",
        )
    )
    assert all(parameter.default is Parameter.empty for parameter in sig.parameters.values())
    hints = get_type_hints(review_import_items)
    assert hints["items"] == tuple[ImportItem, ...]
    assert hints["profile"] is str
    assert hints["pinned_key_ids"] == frozenset[str]
    assert hints["expected_source_state"] is str
    assert hints["current_source_items"] == tuple[SourceStateItem, ...]
    assert hints["seen_replay_keys"] == set[str]
    assert hints["current_ord"] is int
    assert hints["return"] is ImportReview

    atom = CanonAtom(
        "episodic-fact",
        "fact-contract",
        "workspace",
        "repo:canon",
        50,
        "active",
        "descriptive",
        False,
        {"text": "safe text"},
        freshness={"state": "current"},
        trust={"label": "trusted-local"},
        disclosure={"profile": "project-only"},
        hashes={"value_sha256": HASH_A},
    )
    current = (SourceStateItem(path="source.json", sha256=HASH_A, size=1),)
    item = ImportItem("capsule-contract", atom, "safe text", "none", None, True, False, "nonce-contract", 100)
    review = review_import_items(
        (item,),
        profile="project-only",
        pinned_key_ids=frozenset(),
        expected_source_state=source_state_sha256(current),
        current_source_items=current,
        seen_replay_keys=set(),
        current_ord=1,
    )
    assert review == ImportReview(True, (), (atom,), (), ())

    stale = review_import_items(
        (item,),
        profile="project-only",
        pinned_key_ids=frozenset(),
        expected_source_state=HASH_F,
        current_source_items=current,
        seen_replay_keys=set(),
        current_ord=1,
    )
    assert stale.ok is False
    assert stale.findings[0] == ImportFinding(
        "source_changed",
        "critical",
        "source-state",
        "source_changed blocked import review",
    )


def _field_names(cls: type) -> tuple[str, ...]:
    return tuple(field.name for field in fields(cls))


def _path_policy_codes(action) -> tuple[str, ...]:
    from canon.path_policy import PathPolicyError

    with pytest.raises(PathPolicyError) as error:
        action()
    return tuple(violation.code for violation in error.value.violations)
