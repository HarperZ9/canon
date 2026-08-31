from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import ClassVar, Mapping

from .canonical_json import CanonicalJSONError, canonical_sha256, is_sha256_ref

READINESS_PROBE_SCHEMA = "canon.readiness-probe/v1"
READINESS_RESULT_SCHEMA = "canon.readiness-result/v1"
READINESS_VERDICTS = ("pass", "fail", "blocked", "unknown")
CRITICAL_SET_KEYS = ("active_goal_ids", "permission_ids", "prohibition_ids", "constraint_ids", "frontier_state_ids", "unresolved_conflict_ids", "unknown_ids")


@dataclass(frozen=True, slots=True)
class ReadinessProbe:
    probe_id: str
    capsule_id: str
    target: dict
    critical_sets: dict
    challenge: dict
    checker: dict

    schema: ClassVar[str] = READINESS_PROBE_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", copy.deepcopy(self.target))
        object.__setattr__(self, "critical_sets", _critical_sets_value(self.critical_sets))
        object.__setattr__(self, "challenge", copy.deepcopy(self.challenge))
        object.__setattr__(self, "checker", copy.deepcopy(self.checker))

    def to_dict(self) -> dict:
        return {
            "schema": READINESS_PROBE_SCHEMA,
            "probe_id": self.probe_id,
            "capsule_id": self.capsule_id,
            "target": copy.deepcopy(self.target),
            "critical_sets": _critical_sets_to_json(self.critical_sets),
            "challenge": copy.deepcopy(self.challenge),
            "checker": copy.deepcopy(self.checker),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReadinessProbe":
        if not isinstance(d, dict):
            raise TypeError(f"readiness probe JSON must be an object, got {type(d).__name__}")
        got = d.get("schema")
        if got != READINESS_PROBE_SCHEMA:
            raise ValueError(f"expected schema {READINESS_PROBE_SCHEMA!r}, got {got!r}")
        return cls(
            probe_id=d["probe_id"],
            capsule_id=d["capsule_id"],
            target=d["target"],
            critical_sets=d["critical_sets"],
            challenge=d["challenge"],
            checker=d["checker"],
        )


@dataclass(frozen=True, slots=True)
class ReadinessResult:
    probe_id: str
    capsule_id: str
    verdict: str
    reported: dict
    missing_ids: tuple[str, ...]
    mismatched_ids: tuple[str, ...]
    response_hash: str
    does_not_prove: tuple[str, ...] = ()

    schema: ClassVar[str] = READINESS_RESULT_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "reported", copy.deepcopy(self.reported))
        object.__setattr__(self, "missing_ids", _tuple_sequence(self.missing_ids))
        object.__setattr__(self, "mismatched_ids", _tuple_sequence(self.mismatched_ids))
        object.__setattr__(self, "does_not_prove", _tuple_sequence(self.does_not_prove))

    def to_dict(self) -> dict:
        return {
            "schema": READINESS_RESULT_SCHEMA,
            "probe_id": self.probe_id,
            "capsule_id": self.capsule_id,
            "verdict": self.verdict,
            "reported": copy.deepcopy(self.reported),
            "missing_ids": _json_sequence(self.missing_ids),
            "mismatched_ids": _json_sequence(self.mismatched_ids),
            "response_hash": self.response_hash,
            "does_not_prove": _json_sequence(self.does_not_prove),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ReadinessResult":
        if not isinstance(d, dict):
            raise TypeError(f"readiness result JSON must be an object, got {type(d).__name__}")
        got = d.get("schema")
        if got != READINESS_RESULT_SCHEMA:
            raise ValueError(f"expected schema {READINESS_RESULT_SCHEMA!r}, got {got!r}")
        return cls(
            probe_id=d["probe_id"],
            capsule_id=d["capsule_id"],
            verdict=d["verdict"],
            reported=d["reported"],
            missing_ids=d["missing_ids"],
            mismatched_ids=d["mismatched_ids"],
            response_hash=d["response_hash"],
            does_not_prove=d.get("does_not_prove", ()),
        )


def validate_readiness_probe(probe: ReadinessProbe) -> list[str]:
    if not isinstance(probe, ReadinessProbe):
        return ["readiness probe must be a ReadinessProbe"]
    problems: list[str] = []
    _check_non_empty_string("probe_id", probe.probe_id, problems)
    _check_sha256("capsule_id", probe.capsule_id, problems)
    _check_dict("target", probe.target, problems)
    _check_critical_sets(probe.critical_sets, problems)
    _check_dict("challenge", probe.challenge, problems)
    _check_dict("checker", probe.checker, problems)
    return problems


def validate_readiness_result(result: ReadinessResult) -> list[str]:
    if not isinstance(result, ReadinessResult):
        return ["readiness result must be a ReadinessResult"]
    problems: list[str] = []
    _check_non_empty_string("probe_id", result.probe_id, problems)
    _check_sha256("capsule_id", result.capsule_id, problems)
    if result.verdict not in READINESS_VERDICTS:
        problems.append(f"verdict must be one of {list(READINESS_VERDICTS)}, got {result.verdict!r}")
    _check_dict("reported", result.reported, problems)
    _check_string_tuple("missing_ids", result.missing_ids, problems)
    _check_string_tuple("mismatched_ids", result.mismatched_ids, problems)
    _check_sha256("response_hash", result.response_hash, problems)
    _check_string_tuple("does_not_prove", result.does_not_prove, problems)
    if result.verdict == "pass" and (result.missing_ids or result.mismatched_ids):
        problems.append("pass verdict requires no missing_ids or mismatched_ids")
    return problems


def evaluate_readiness_response(probe: ReadinessProbe, response: Mapping[str, object]) -> ReadinessResult:
    response_hash = _response_hash(response)
    reported = _reported_copy(response)
    blockers = _evaluation_blockers(probe, response)
    if blockers:
        return ReadinessResult(
            probe.probe_id if isinstance(probe, ReadinessProbe) else "",
            probe.capsule_id if isinstance(probe, ReadinessProbe) else "",
            "blocked",
            reported,
            (),
            tuple(sorted(blockers)),
            response_hash,
        )

    missing, mismatched = _compare_critical_sets(probe.critical_sets, response)
    mismatched.update(_status_mismatches(probe.critical_sets, response))
    verdict = "pass" if not missing and not mismatched else "fail"
    return ReadinessResult(
        probe.probe_id,
        probe.capsule_id,
        verdict,
        reported,
        tuple(sorted(missing)),
        tuple(sorted(mismatched)),
        response_hash,
    )


def _critical_sets_value(value: object) -> object:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    result = {}
    for key in CRITICAL_SET_KEYS:
        if key in value:
            result[key] = _tuple_sequence(value[key])
    for key in sorted((key for key in value if key not in result), key=str):
        result[key] = _tuple_sequence(value[key])
    return result


def _critical_sets_to_json(value: object) -> object:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    return {key: _json_sequence(ids) for key, ids in value.items()}


def _tuple_sequence(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return tuple(copy.deepcopy(item) for item in value)
    return copy.deepcopy(value)


def _json_sequence(value: object) -> object:
    if isinstance(value, tuple):
        return [copy.deepcopy(item) for item in value]
    if isinstance(value, list):
        return [copy.deepcopy(item) for item in value]
    return copy.deepcopy(value)


def _check_non_empty_string(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, str) or value == "":
        problems.append(f"{name} must be a non-empty string")


def _check_sha256(name: str, value: object, problems: list[str]) -> None:
    if not is_sha256_ref(value):
        problems.append(f"{name} must be a sha256: reference")


def _check_dict(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, dict):
        problems.append(f"{name} must be a dict")


def _check_critical_sets(value: object, problems: list[str]) -> None:
    if not isinstance(value, dict):
        problems.append("critical_sets must be a dict")
        return
    for key, ids in value.items():
        if key not in CRITICAL_SET_KEYS:
            problems.append(f"critical_sets key must be one of {list(CRITICAL_SET_KEYS)}, got {key!r}")
            continue
        _check_string_tuple(f"critical_sets.{key}", ids, problems)


def _check_string_tuple(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append(f"{name} must be a tuple")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            problems.append(f"{name}[{index}] must be a string")


def _evaluation_blockers(probe: object, response: object) -> list[str]:
    blockers: list[str] = []
    if not isinstance(probe, ReadinessProbe):
        blockers.append("probe")
        return blockers
    if not isinstance(probe.critical_sets, dict):
        blockers.append("critical_sets")
    elif any(not isinstance(ids, tuple) or any(not isinstance(item, str) for item in ids) for ids in probe.critical_sets.values()):
        blockers.append("critical_sets")
    if not isinstance(response, Mapping):
        blockers.append("response")
    return blockers


def _reported_copy(response: object) -> dict:
    if isinstance(response, Mapping):
        return copy.deepcopy(dict(response))
    return {"malformed_response": copy.deepcopy(response)}


def _response_hash(response: object) -> str:
    try:
        return canonical_sha256(response)
    except (CanonicalJSONError, TypeError, ValueError):
        return canonical_sha256({"malformed_response_type": type(response).__name__})


def _probe_id(probe: object) -> str:
    return probe.probe_id if isinstance(probe, ReadinessProbe) else ""


def _capsule_id(probe: object) -> str:
    return probe.capsule_id if isinstance(probe, ReadinessProbe) else ""


def _compare_critical_sets(critical_sets: dict, response: Mapping[str, object]) -> tuple[set[str], set[str]]:
    missing: set[str] = set()
    mismatched: set[str] = set()
    for key, expected_value in critical_sets.items():
        expected = set(expected_value)
        reported = set(_reported_ids(response.get(key, ())))
        missing.update(expected - reported)
        mismatched.update(reported - expected)
    return missing, mismatched


def _reported_ids(value: object) -> tuple[str, ...]:
    return () if not isinstance(value, (list, tuple)) else tuple(item for item in value if isinstance(item, str))


def _status_mismatches(critical_sets: dict, response: Mapping[str, object]) -> set[str]:
    statuses = response.get("statuses")
    expected_statuses = response.get("expected_statuses")
    if not isinstance(statuses, Mapping) or not isinstance(expected_statuses, Mapping):
        return set()
    mismatched: set[str] = set()
    for values in critical_sets.values():
        for critical_id in values:
            if critical_id in statuses and critical_id in expected_statuses:
                if statuses[critical_id] != expected_statuses[critical_id]:
                    mismatched.add(critical_id)
    return mismatched
