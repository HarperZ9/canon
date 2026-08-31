from __future__ import annotations


_EXISTING_EXPORTS = (
    "SCHEMA",
    "KINDS",
    "KIND_PERSONALITY_BLOCK",
    "KIND_EPISODIC_MEMORY",
    "KIND_SYNTHESIZED_PERSONA_L3",
    "KIND_ADR_DECISION",
    "KIND_RESEARCH_ARTIFACT_REF",
    "TEMPORAL_KINDS",
    "SCOPES",
    "SCOPE_GLOBAL",
    "SCOPE_WORKSPACE",
    "EPISODIC_LAYERS",
    "PERSONA_LAYER",
    "ADR_STATUSES",
    "Record",
    "Provenance",
    "Temporal",
    "is_sha256",
    "validate_record",
    "is_valid",
    "resolve_blocks",
    "is_current",
    "LayeringError",
    "MemoryBackend",
    "BackendError",
    "InvalidRecord",
    "InvalidKey",
    "UnsupportedKind",
    "DropError",
    "FilesBackend",
    "SqliteBackend",
    "MnemeBackend",
    "FlywheelBackend",
    "CAP_TEMPORAL",
    "CAP_AUDIT_CHAIN",
    "CAP_RELATIONS",
    "CAP_ARBITRARY_KIND",
    "CAP_FOREIGN_PROVENANCE",
    "record_key",
    "capabilities_required",
    "guard_put",
    "validate_put_record",
)

_FOUNDATION_EXPORTS = (
    "canonical_json_text",
    "canonical_json_bytes",
    "sha256_bytes",
    "sha256_text",
    "canonical_sha256",
    "is_sha256_ref",
    "CanonicalJSONError",
    "ATOM_SCHEMA",
    "CanonAtom",
    "atom_key",
    "atoms_from_records",
    "load_atoms_jsonl",
    "validate_atom",
    "is_valid_atom",
    "OMISSION_SCHEMA",
    "Omission",
    "validate_omission",
    "TRANSFORM_SCHEMA",
    "TransformReceipt",
    "validate_transform_receipt",
    "ADAPTER_SCHEMA",
    "AdapterDescriptor",
    "builtin_descriptors",
    "descriptor_for",
    "assert_requested_tier_allowed",
    "validate_adapter_descriptor",
    "READINESS_PROBE_SCHEMA",
    "READINESS_RESULT_SCHEMA",
    "ReadinessProbe",
    "ReadinessResult",
    "evaluate_readiness_response",
    "validate_readiness_probe",
    "validate_readiness_result",
    "BOOTSTRAP_WITNESS_SCHEMA",
    "BootstrapCheck",
    "BootstrapWitness",
    "validate_bootstrap_witness",
    "CAPSULE_SCHEMA",
    "Capsule",
    "CapsuleTarget",
    "SourceState",
    "Compatibility",
    "Budget",
    "Integrity",
    "CapsuleCompileRequest",
    "CapsuleBundle",
    "build_capsule",
    "compile_capsule",
    "capsule_bytes",
    "capsule_digest",
    "validate_capsule",
    "CANON_MD_SECTIONS",
    "render_canon_md",
    "parse_canon_md_carrier",
    "verify_canon_md",
)

_EXPECTED_EXPORTS = _EXISTING_EXPORTS + _FOUNDATION_EXPORTS

_EXPECTED_SCHEMAS = {
    "ATOM_SCHEMA": "canon.atom/v1",
    "CAPSULE_SCHEMA": "canon.capsule/v1",
    "OMISSION_SCHEMA": "canon.omission/v1",
    "TRANSFORM_SCHEMA": "canon.transform-receipt/v1",
    "READINESS_PROBE_SCHEMA": "canon.readiness-probe/v1",
    "READINESS_RESULT_SCHEMA": "canon.readiness-result/v1",
    "BOOTSTRAP_WITNESS_SCHEMA": "canon.bootstrap-witness/v1",
    "ADAPTER_SCHEMA": "canon.adapter/v1",
}

_CALLABLE_EXPORTS = (
    "canonical_json_text",
    "canonical_json_bytes",
    "sha256_bytes",
    "sha256_text",
    "canonical_sha256",
    "is_sha256_ref",
    "atom_key",
    "atoms_from_records",
    "load_atoms_jsonl",
    "validate_atom",
    "is_valid_atom",
    "validate_omission",
    "validate_transform_receipt",
    "builtin_descriptors",
    "descriptor_for",
    "assert_requested_tier_allowed",
    "validate_adapter_descriptor",
    "evaluate_readiness_response",
    "validate_readiness_probe",
    "validate_readiness_result",
    "validate_bootstrap_witness",
    "build_capsule",
    "compile_capsule",
    "capsule_bytes",
    "capsule_digest",
    "validate_capsule",
    "render_canon_md",
    "parse_canon_md_carrier",
    "verify_canon_md",
)

_EXPECTED_DESCRIPTOR_TIERS = (
    ("codex-cli", "native-advisory"),
    ("claude-code", "native-advisory"),
    ("chatgpt-app", "guided"),
    ("claude-app", "guided"),
    ("api-runner", "guided"),
    ("local-runner", "guided"),
    ("mcp-readonly", "guided"),
    ("a2a-artifact", "guided"),
)


def _import_from_canon(names: tuple[str, ...]) -> dict[str, object]:
    namespace: dict[str, object] = {}
    exec("from canon import " + ", ".join(names), namespace)
    return {name: namespace[name] for name in names}


def test_existing_public_exports_remain_importable() -> None:
    exported = _import_from_canon(_EXISTING_EXPORTS)
    assert tuple(exported) == _EXISTING_EXPORTS


def test_foundation_public_exports_import() -> None:
    exported = _import_from_canon(_FOUNDATION_EXPORTS)
    for name, expected in _EXPECTED_SCHEMAS.items():
        assert exported[name] == expected
    for name in _CALLABLE_EXPORTS:
        assert callable(exported[name])


def test_package_all_is_the_stable_public_surface() -> None:
    import canon

    assert tuple(canon.__all__) == _EXPECTED_EXPORTS
    assert all(not name.startswith("_") for name in canon.__all__)


def test_builtin_descriptor_exports_keep_order_and_tiers() -> None:
    import pytest
    from canon import assert_requested_tier_allowed, builtin_descriptors, descriptor_for

    descriptors = builtin_descriptors()
    assert tuple((d.adapter_id, d.integration_tier) for d in descriptors) == _EXPECTED_DESCRIPTOR_TIERS
    assert all(d.bootstrap.get("can_block_before_work") is False for d in descriptors)
    assert descriptor_for("mcp-readonly").integration_tier == "guided"
    assert descriptor_for("a2a-artifact").integration_tier == "guided"
    assert_requested_tier_allowed(descriptor_for("codex-cli"), "guided")
    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(descriptor_for("mcp-readonly"), "native-advisory")


def test_compile_and_render_exports_work_together() -> None:
    from canon import (
        Budget,
        CanonAtom,
        CapsuleBundle,
        CapsuleCompileRequest,
        CapsuleTarget,
        SourceState,
        compile_capsule,
        parse_canon_md_carrier,
        render_canon_md,
        validate_capsule,
        verify_canon_md,
    )

    atom = CanonAtom(
        "active-goal", "goal-1", "session", "record-scope:workspace",
        0, "active", "normative", True, {"summary": "ship public exports"},
    )
    request = CapsuleCompileRequest(
        profile="handoff",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest="sha256:" + "a" * 64),
        budget=Budget("handoff", 4096, 128, "unknown"),
        atoms=(atom,),
        required_atom_ids=("goal-1",),
        readiness_probe_id="probe-public-exports",
    )
    bundle = compile_capsule(request)
    assert isinstance(bundle, CapsuleBundle)
    assert bundle.canon_md == render_canon_md(bundle.capsule)
    assert parse_canon_md_carrier(bundle.canon_md) == bundle.capsule.to_dict()
    assert validate_capsule(bundle.capsule) == []
    assert verify_canon_md(bundle.canon_md, bundle.capsule) == []
