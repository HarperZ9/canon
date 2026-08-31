from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text, canonical_sha256
from canon.readiness import (
    CRITICAL_SET_KEYS,
    READINESS_PROBE_SCHEMA,
    READINESS_RESULT_SCHEMA,
    ReadinessProbe,
    ReadinessResult,
    evaluate_readiness_response,
    validate_readiness_probe,
    validate_readiness_result,
)

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def read_fixture_text(name: str) -> str:
    return (FOUNDATION / name).read_text(encoding="utf-8")


def make_probe(critical_sets: dict, target=None, challenge=None, checker=None) -> ReadinessProbe:
    return ReadinessProbe("probe-1", HASH_A, target or {}, critical_sets, challenge or {}, checker or {})


def test_readiness_probe_roundtrips_and_validates():
    d = load_fixture("readiness_probe.json")
    probe = ReadinessProbe.from_dict(d)
    assert probe.to_dict() == d
    assert validate_readiness_probe(probe) == []


def test_readiness_probe_fixture_matches_canonical_json_bytes():
    d = load_fixture("readiness_probe.json")
    assert read_fixture_text("readiness_probe.json") == canonical_json_text(d)


def test_readiness_probe_writes_schema_and_tuple_critical_sets():
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    assert probe.to_dict()["schema"] == READINESS_PROBE_SCHEMA
    assert tuple(probe.critical_sets) == CRITICAL_SET_KEYS
    assert probe.critical_sets["active_goal_ids"] == ("goal-foundation",)


def test_readiness_response_passes_exact_critical_sets():
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    response = {k: list(v) for k, v in probe.critical_sets.items()}
    result = evaluate_readiness_response(probe, response)
    assert result.verdict == "pass"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ()
    assert validate_readiness_result(result) == []


def test_readiness_response_fails_on_missing_critical_id():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    result = evaluate_readiness_response(probe, {"active_goal_ids": []})
    assert result.verdict == "fail"
    assert result.missing_ids == ("goal-1",)


def test_readiness_response_treats_absent_key_as_empty_list():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    result = evaluate_readiness_response(probe, {})
    assert result.verdict == "fail"
    assert result.missing_ids == ("goal-1",)


def test_readiness_response_fails_on_extra_reported_critical_id():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    result = evaluate_readiness_response(probe, {"active_goal_ids": ["goal-1", "goal-extra"]})
    assert result.verdict == "fail"
    assert result.mismatched_ids == ("goal-extra",)


def test_readiness_response_sorts_missing_and_mismatched_ids_lexically():
    probe = make_probe({
        "permission_ids": ("perm-z", "perm-a"),
        "active_goal_ids": ("goal-b", "goal-a"),
    })
    result = evaluate_readiness_response(
        probe,
        {
            "active_goal_ids": ["goal-extra-z", "goal-extra-a"],
            "permission_ids": [],
        },
    )
    assert result.missing_ids == ("goal-a", "goal-b", "perm-a", "perm-z")
    assert result.mismatched_ids == ("goal-extra-a", "goal-extra-z")


def test_readiness_response_checks_status_mismatches_when_expected_statuses_present():
    probe = make_probe({
        "active_goal_ids": ("goal-1",),
        "permission_ids": ("perm-1",),
    })
    response = {
        "active_goal_ids": ["goal-1"],
        "permission_ids": ["perm-1"],
        "statuses": {"goal-1": "stale", "perm-1": "active"},
        "expected_statuses": {"goal-1": "active", "perm-1": "active"},
    }
    result = evaluate_readiness_response(probe, response)
    assert result.verdict == "fail"
    assert result.mismatched_ids == ("goal-1",)


def test_readiness_response_mismatches_status_missing_from_expected_statuses():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    response = {
        "active_goal_ids": ("goal-1",),
        "statuses": {"goal-1": "active"},
        "expected_statuses": {},
    }
    result = evaluate_readiness_response(probe, response)
    assert result.verdict == "fail"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ("goal-1",)


@pytest.mark.parametrize("field", ("statuses", "expected_statuses"))
def test_readiness_response_blocks_malformed_status_maps(field: str):
    response = {"active_goal_ids": ["goal-1"], "statuses": {}, "expected_statuses": {}}
    response[field] = []
    result = evaluate_readiness_response(make_probe({"active_goal_ids": ("goal-1",)}), response)
    assert result.verdict == "blocked"
    assert result.mismatched_ids == (field,)


def test_readiness_response_hashes_canonical_response_and_deep_copies_reported():
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    response = {k: list(v) for k, v in probe.critical_sets.items()}
    result = evaluate_readiness_response(probe, response)
    response["active_goal_ids"].append("mutated")
    assert result.response_hash == canonical_sha256({k: list(v) for k, v in probe.critical_sets.items()})
    assert result.reported["active_goal_ids"] == ["goal-foundation"]


def test_readiness_probe_uses_defensive_copies_for_nested_values():
    target = {"adapter": "codex-cli"}
    critical_sets = {"active_goal_ids": ["goal-1"]}
    challenge = {"required_fields": ["active_goal_ids"]}
    checker = {"method": "exact-id-set-and-status-match"}
    probe = make_probe(critical_sets, target, challenge, checker)
    target["adapter"] = "mutated"
    critical_sets["active_goal_ids"].append("mutated")
    challenge["required_fields"].append("mutated")
    checker["method"] = "mutated"
    as_dict = probe.to_dict()
    as_dict["target"]["adapter"] = "dict-mutation"
    as_dict["critical_sets"]["active_goal_ids"].append("dict-mutation")
    assert probe.target == {"adapter": "codex-cli"}
    assert probe.critical_sets["active_goal_ids"] == ("goal-1",)
    assert probe.challenge == {"required_fields": ["active_goal_ids"]}
    assert probe.checker == {"method": "exact-id-set-and-status-match"}


def test_readiness_result_uses_defensive_copies_for_nested_values():
    reported = {"active_goal_ids": ["goal-1"]}
    result = ReadinessResult("probe-1", HASH_A, "pass", reported, ["missing-1"], ["mismatch-1"], HASH_B, ["This result does not prove host-level enforcement."])
    reported["active_goal_ids"].append("mutated")
    as_dict = result.to_dict()
    as_dict["reported"]["active_goal_ids"].append("dict-mutation")
    as_dict["missing_ids"].append("dict-mutation")
    assert result.reported == {"active_goal_ids": ["goal-1"]}
    assert result.missing_ids == ("missing-1",)
    assert result.mismatched_ids == ("mismatch-1",)
    assert result.does_not_prove == ("This result does not prove host-level enforcement.",)


def test_readiness_result_validator_rejects_bad_response_hash():
    result = ReadinessResult(
        probe_id="probe-1",
        capsule_id=HASH_A,
        verdict="pass",
        reported={},
        missing_ids=(),
        mismatched_ids=(),
        response_hash="bad",
    )
    assert any("response_hash" in p for p in validate_readiness_result(result))


def test_readiness_probe_validator_reports_multiple_shape_problems():
    probe = ReadinessProbe("", "bad", [], "not-a-dict", [], [])
    problems = validate_readiness_probe(probe)
    assert any("probe_id" in p for p in problems)
    assert any("capsule_id" in p for p in problems)
    assert any("target" in p for p in problems)
    assert any("critical_sets" in p for p in problems)


def test_readiness_probe_validator_rejects_bad_critical_set_values():
    d = load_fixture("readiness_probe.json")
    d["critical_sets"]["active_goal_ids"] = "goal-foundation"
    probe = ReadinessProbe.from_dict(d)
    assert probe.to_dict()["critical_sets"]["active_goal_ids"] == "goal-foundation"
    assert any("active_goal_ids" in p for p in validate_readiness_probe(probe))


def test_readiness_evaluator_blocks_probe_with_unknown_critical_set_key():
    probe = make_probe({"active_goal_ids": (), "foreign_ids": ()})
    result = evaluate_readiness_response(probe, {"active_goal_ids": []})
    assert result.verdict == "blocked"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ("critical_sets",)


def test_readiness_result_validator_reports_multiple_shape_problems():
    result = ReadinessResult("", "bad", "maybe", [], "goal-1", "goal-2", "bad", "not-proof-text")
    problems = validate_readiness_result(result)
    assert any("probe_id" in p for p in problems)
    assert any("capsule_id" in p for p in problems)
    assert any("verdict" in p for p in problems)
    assert any("reported" in p for p in problems)
    assert any("missing_ids" in p for p in problems)
    assert any("mismatched_ids" in p for p in problems)
    assert any("does_not_prove" in p for p in problems)


def test_readiness_evaluator_handles_malformed_response_lists_without_crashing():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    result = evaluate_readiness_response(probe, {"active_goal_ids": "goal-1"})
    assert result.verdict == "blocked"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ("active_goal_ids",)


def test_readiness_evaluator_handles_uncanonical_response_without_crashing():
    probe = make_probe({"active_goal_ids": ("goal-1",)})
    result = evaluate_readiness_response(probe, {"active_goal_ids": [object()]})
    assert result.verdict == "blocked"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ("active_goal_ids",)
    assert result.response_hash.startswith("sha256:")


@pytest.mark.parametrize("bad_value", ("goal-1", {"id": "goal-1"}, [object()], ("goal-1", object())))
def test_readiness_blocks_malformed_present_response_values_when_expected_set_empty(bad_value):
    result = evaluate_readiness_response(make_probe({"active_goal_ids": ()}), {"active_goal_ids": bad_value})
    assert result.verdict == "blocked"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ("active_goal_ids",)


def test_readiness_blocks_malformed_response_values_in_stable_key_order():
    probe = make_probe({"permission_ids": (), "active_goal_ids": ()})
    response = {"permission_ids": "perm-1", "active_goal_ids": {"id": "goal-1"}}
    result = evaluate_readiness_response(probe, response)
    assert result.verdict == "blocked"
    assert result.mismatched_ids == ("active_goal_ids", "permission_ids")


def test_readiness_evaluator_handles_malformed_probe_or_response_without_crashing():
    probe = ReadinessProbe("probe-1", HASH_A, {}, "not-a-dict", {}, {})
    result = evaluate_readiness_response(probe, [])
    assert result.verdict == "blocked"
    assert result.mismatched_ids == ("critical_sets", "response")


def test_validators_are_total_and_list_returning():
    assert isinstance(validate_readiness_probe(object()), list)
    assert isinstance(validate_readiness_result(object()), list)
    malformed_probe = ReadinessProbe("probe-1", HASH_A, {}, {"active_goal_ids": [object()]}, {}, {})
    malformed_result = ReadinessResult("probe-1", HASH_A, "pass", {}, [object()], (), "bad")
    assert isinstance(validate_readiness_probe(malformed_probe), list)
    assert isinstance(validate_readiness_result(malformed_result), list)


def test_readiness_result_writes_schema():
    result = ReadinessResult("probe-1", HASH_A, "pass", {}, (), (), HASH_B)
    assert result.to_dict()["schema"] == READINESS_RESULT_SCHEMA
