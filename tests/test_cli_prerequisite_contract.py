from __future__ import annotations


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
