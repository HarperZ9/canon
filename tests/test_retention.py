from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from canon.canonical_json import is_sha256_ref
from canon.omission import Omission, validate_omission
from canon.retention import (
    DERIVED_STORES,
    RETENTION_ACTIONS,
    DerivedArtifactRef,
    RetentionPolicy,
    make_tombstone,
    plan_retention,
    validate_retention_policy,
)
from canon.transform import TransformReceipt, validate_transform_receipt

HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def _ref(
    store: str = "files",
    locator: str = "global/a.json",
    digest: str | None = HASH_A,
    *,
    raw: bool = True,
) -> DerivedArtifactRef:
    return DerivedArtifactRef(store=store, locator=locator, content_sha256=digest, contains_raw=raw)


def test_retention_vocabularies_are_exact_tuple_contracts() -> None:
    assert RETENTION_ACTIONS == ("retain", "tombstone", "purge-derived", "purge-all")
    assert DERIVED_STORES == (
        "sqlite",
        "files",
        "vault",
        "managed-surface",
        "capsule",
        "canonpack",
        "witness",
        "backup",
        "exported-artifact",
    )


def test_policy_snapshots_derived_stores_and_is_frozen() -> None:
    stores = ["files"]
    policy = RetentionPolicy("atom-1", "purge-derived", False, stores)
    stores.append("vault")

    assert policy.derived_stores == ("files",)
    with pytest.raises(FrozenInstanceError):
        policy.action = "retain"


def test_invalid_action_is_reported() -> None:
    policy = RetentionPolicy(subject_id="atom-1", action="erase", retain_content_hash=False, derived_stores=("files",))

    assert validate_retention_policy(policy) == ("invalid-action",)


def test_unknown_derived_store_is_reported() -> None:
    policy = RetentionPolicy(
        subject_id="atom-1",
        action="tombstone",
        retain_content_hash=False,
        derived_stores=("unknown-store",),
    )

    assert validate_retention_policy(policy) == ("unknown-derived-store:unknown-store",)


def test_invalid_policy_problems_are_aggregated_deterministically() -> None:
    policy = RetentionPolicy(
        subject_id="bad\nid",
        action="erase",
        retain_content_hash=1,
        derived_stores=("unknown-store", "files", "files"),
    )

    assert validate_retention_policy(policy) == (
        "invalid-subject-id",
        "invalid-action",
        "invalid-retain-content-hash",
        "unknown-derived-store:unknown-store",
        "duplicate-derived-store:files",
    )


@pytest.mark.parametrize(
    "subject_id",
    ["", ".", "..", "../atom", "atom/id", "atom\\id", "atom:id", "atom\nid", "atom\0id", "cafe\u0301"],
)
def test_policy_rejects_empty_control_non_nfc_and_unsafe_subject_ids(subject_id: str) -> None:
    policy = RetentionPolicy(subject_id, "retain", False, ())

    assert validate_retention_policy(policy) == ("invalid-subject-id",)


def test_purge_tombstone_does_not_retain_hash_when_policy_disallows_it() -> None:
    tombstone = make_tombstone(
        "atom-1",
        reason_code="operator-request",
        purged_at_ord=44,
        retain_content_hash=False,
        content_sha256=HASH_A,
    )

    assert tombstone.content_sha256 is None
    assert "raw" not in repr(tombstone).casefold()


def test_tombstone_retains_valid_hash_only_when_policy_allows_it() -> None:
    tombstone = make_tombstone(
        "atom-1",
        reason_code="operator-request",
        purged_at_ord=44,
        retain_content_hash=True,
        content_sha256=HASH_A,
    )

    assert tombstone.content_sha256 == HASH_A


def test_make_tombstone_rejects_invalid_inputs_without_leaking_raw_text() -> None:
    canary = "sk-live-abcdefghijklmnopqrstuvwxyz012345"

    with pytest.raises(ValueError) as excinfo:
        make_tombstone(
            "atom-1",
            reason_code=f"operator-{canary}\n",
            purged_at_ord=True,
            retain_content_hash=True,
            content_sha256="sha256:" + "A" * 64,
        )

    assert "invalid-tombstone" in str(excinfo.value)
    assert canary not in str(excinfo.value)


def test_plan_retention_covers_all_refs_but_does_not_delete() -> None:
    refs = (
        _ref("files", "global/a.json", "sha256:" + "1" * 64),
        _ref("vault", "workspace/a.md", "sha256:" + "2" * 64),
    )
    policy = RetentionPolicy(
        subject_id="atom-1",
        action="purge-derived",
        retain_content_hash=False,
        derived_stores=("files", "vault"),
    )

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256=HASH_A)

    assert plan.ok
    assert plan.refs_to_purge == refs
    assert plan.deleted_paths == ()
    assert plan.tombstone is not None
    assert isinstance(plan.omissions[0], Omission)
    assert validate_omission(plan.omissions[0]) == []
    assert isinstance(plan.receipts[0], TransformReceipt)
    assert validate_transform_receipt(plan.receipts[0]) == []


def test_retain_action_has_no_tombstone_receipt_omission_or_deletion() -> None:
    policy = RetentionPolicy("atom-1", "retain", False, ("files",))

    plan = plan_retention("atom-1", policy=policy, derived_refs=(_ref(),), content_sha256=HASH_A)

    assert plan.ok
    assert plan.refs_to_purge == ()
    assert plan.tombstone is None
    assert plan.omissions == ()
    assert plan.receipts == ()
    assert plan.deleted_paths == ()


def test_tombstone_action_records_marker_without_selecting_derived_refs() -> None:
    policy = RetentionPolicy("atom-1", "tombstone", False, ("files",))

    plan = plan_retention("atom-1", policy=policy, derived_refs=(_ref(),), content_sha256=HASH_A)

    assert plan.ok
    assert plan.refs_to_purge == ()
    assert plan.tombstone is not None
    assert plan.omissions[0].decision == "reference-only"
    assert plan.receipts[0].transform == "redaction"


def test_purge_all_selects_all_refs_in_deterministic_order() -> None:
    refs = (
        _ref("vault", "workspace/b.md", HASH_B),
        _ref("files", "global/a.json", HASH_A),
        _ref("backup", "snapshots/c.json", HASH_C, raw=False),
    )
    policy = RetentionPolicy("atom-1", "purge-all", False, ())

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256=HASH_A)

    assert plan.ok
    assert plan.refs_to_purge == (refs[2], refs[1], refs[0])
    assert plan.deleted_paths == ()


def test_purge_derived_reports_raw_derived_store_coverage_gap() -> None:
    refs = (
        _ref("files", "global/a.json", HASH_A),
        _ref("vault", "workspace/a.md", HASH_B),
        _ref("capsule", "capsules/a.json", HASH_C, raw=False),
    )
    policy = RetentionPolicy("atom-1", "purge-derived", False, ("files",))

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256=HASH_A)

    assert not plan.ok
    assert "uncovered-derived-store:vault" in plan.violations
    assert plan.refs_to_purge == (refs[0],)
    assert plan.deleted_paths == ()


def test_subject_policy_mismatch_blocks_plan() -> None:
    policy = RetentionPolicy("atom-2", "tombstone", False, ())

    plan = plan_retention("atom-1", policy=policy, derived_refs=(), content_sha256=HASH_A)

    assert not plan.ok
    assert plan.violations == ("subject-policy-mismatch",)
    assert plan.tombstone is None


def test_retained_content_hash_policy_requires_valid_sha256() -> None:
    policy = RetentionPolicy("atom-1", "tombstone", True, ())

    missing = plan_retention("atom-1", policy=policy, derived_refs=(), content_sha256=None)
    invalid = plan_retention("atom-1", policy=policy, derived_refs=(), content_sha256="sha256:" + "A" * 64)

    assert missing.violations == ("missing-content-sha256",)
    assert invalid.violations == ("invalid-content-sha256",)
    assert missing.tombstone is None
    assert invalid.tombstone is None


def test_invalid_refs_are_aggregated_and_raw_locator_is_not_retained() -> None:
    canary = "sk-live-abcdefghijklmnopqrstuvwxyz012345"
    refs = (
        _ref("files", f"workspace/{canary}.md\n", "sha256:" + "A" * 64, raw=True),
        _ref("unknown-store", "workspace/b.md", HASH_B, raw=True),
        DerivedArtifactRef("vault", "workspace/c.md", HASH_C, contains_raw=1),
    )
    policy = RetentionPolicy("atom-1", "purge-all", False, ())

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256=HASH_A)

    assert not plan.ok
    assert set(plan.violations) == {
        "invalid-derived-locator",
        "invalid-derived-content-sha256",
        "unknown-derived-store:unknown-store",
        "invalid-derived-contains-raw",
    }
    assert plan.refs_to_purge == ()
    assert canary not in repr(plan)


def test_duplicate_normalized_stores_and_refs_are_reported() -> None:
    policy = RetentionPolicy("atom-1", "purge-all", False, ("files", "files"))
    refs = (
        _ref("files", "Global/A.json", HASH_A),
        _ref("files", "global/a.json", HASH_B),
    )

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256=HASH_A)

    assert not plan.ok
    assert plan.violations == (
        "duplicate-derived-store:files",
        "duplicate-derived-ref:files:global/a.json",
    )


def test_retention_receipts_and_omissions_are_deterministic_and_hash_bound() -> None:
    refs_a = (_ref("vault", "workspace/b.md", HASH_B), _ref("files", "global/a.json", HASH_A))
    refs_b = tuple(reversed(refs_a))
    policy = RetentionPolicy("atom-1", "purge-all", True, ())

    plan_a = plan_retention("atom-1", policy=policy, derived_refs=refs_a, content_sha256=HASH_C)
    plan_b = plan_retention("atom-1", policy=policy, derived_refs=refs_b, content_sha256=HASH_C)

    assert plan_a.omissions[0].to_dict() == plan_b.omissions[0].to_dict()
    assert plan_a.receipts[0].to_dict() == plan_b.receipts[0].to_dict()
    assert plan_a.tombstone is not None
    assert plan_a.tombstone.content_sha256 == HASH_C
    assert plan_a.receipts[0].input_span_hash == HASH_C
    assert is_sha256_ref(plan_a.receipts[0].output_hash)


def test_plan_retention_rejects_non_exact_policy_and_refs_tuple() -> None:
    class PolicySubclass(RetentionPolicy):
        pass

    class RefTuple(tuple[DerivedArtifactRef, ...]):
        pass

    policy = PolicySubclass("atom-1", "retain", False, ())

    bad_policy = plan_retention("atom-1", policy=policy, derived_refs=(), content_sha256=None)
    bad_refs = plan_retention(
        "atom-1",
        policy=RetentionPolicy("atom-1", "retain", False, ()),
        derived_refs=RefTuple((_ref(),)),
        content_sha256=None,
    )

    assert bad_policy.violations == ("invalid-policy",)
    assert bad_refs.violations == ("invalid-derived-refs",)


def test_plan_retention_is_total_for_non_policy_objects() -> None:
    plan = plan_retention("atom-1", policy=object(), derived_refs=(), content_sha256=None)  # type: ignore[arg-type]

    assert not plan.ok
    assert plan.violations == ("invalid-policy",)
    assert plan.deleted_paths == ()
