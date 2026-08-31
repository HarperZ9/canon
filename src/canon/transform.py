from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar

from .canonical_json import canonical_json_text, is_sha256_ref
from .omission import Omission, validate_omission

TRANSFORM_SCHEMA = "canon.transform-receipt/v1"
TRANSFORM_KINDS = ("summary", "compaction", "synthesis", "projection", "redaction", "migration")
TRANSFORM_VERIFIERS = ("deterministic", "human", "model-assisted")


@dataclass(frozen=True, slots=True)
class TransformReceipt:
    transform: str
    method_id: str
    input_refs: tuple[str, ...]
    input_span_hash: str
    output_ref: str
    output_hash: str
    lossy: bool
    retained_critical_atom_ids: tuple[str, ...]
    omissions: tuple[Omission, ...] = ()
    verifier: str = "deterministic"
    does_not_prove: tuple[str, ...] = ()

    schema: ClassVar[str] = TRANSFORM_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_refs", _tuple_from(self.input_refs))
        object.__setattr__(self, "retained_critical_atom_ids", _tuple_from(self.retained_critical_atom_ids))
        object.__setattr__(self, "omissions", _omission_tuple(self.omissions))
        object.__setattr__(self, "does_not_prove", _tuple_from(self.does_not_prove))

    def to_dict(self) -> dict:
        return {
            "schema": TRANSFORM_SCHEMA,
            "transform": self.transform,
            "method_id": self.method_id,
            "input_refs": list(self.input_refs),
            "input_span_hash": self.input_span_hash,
            "output_ref": self.output_ref,
            "output_hash": self.output_hash,
            "lossy": self.lossy,
            "retained_critical_atom_ids": list(self.retained_critical_atom_ids),
            "omissions": [omission.to_dict() for omission in self.omissions],
            "verifier": self.verifier,
            "does_not_prove": list(self.does_not_prove),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TransformReceipt":
        if not isinstance(d, dict):
            raise TypeError(f"transform receipt JSON must be an object, got {type(d).__name__}")
        got = d.get("schema")
        if got != TRANSFORM_SCHEMA:
            raise ValueError(f"expected schema {TRANSFORM_SCHEMA!r}, got {got!r}")
        return cls(
            transform=d["transform"],
            method_id=d["method_id"],
            input_refs=d["input_refs"],
            input_span_hash=d["input_span_hash"],
            output_ref=d["output_ref"],
            output_hash=d["output_hash"],
            lossy=d["lossy"],
            retained_critical_atom_ids=d["retained_critical_atom_ids"],
            omissions=_omission_tuple(d.get("omissions", ())),
            verifier=d.get("verifier", "deterministic"),
            does_not_prove=d.get("does_not_prove", ()),
        )

    def to_json(self) -> str:
        return canonical_json_text(self.to_dict())


def validate_transform_receipt(receipt: TransformReceipt) -> list[str]:
    if not isinstance(receipt, TransformReceipt):
        return ["transform receipt must be a TransformReceipt"]
    problems: list[str] = []
    _check_member("transform", receipt.transform, TRANSFORM_KINDS, problems)
    _check_member("verifier", receipt.verifier, TRANSFORM_VERIFIERS, problems)
    _check_non_empty_string("method_id", receipt.method_id, problems)
    _check_non_empty_string("output_ref", receipt.output_ref, problems)
    _check_string_tuple("input_refs", receipt.input_refs, problems)
    _check_string_tuple("retained_critical_atom_ids", receipt.retained_critical_atom_ids, problems)
    _check_string_tuple("does_not_prove", receipt.does_not_prove, problems)
    _check_sha256("input_span_hash", receipt.input_span_hash, problems)
    _check_sha256("output_hash", receipt.output_hash, problems)
    _check_lossy(receipt.lossy, problems)
    _check_omissions(receipt.omissions, problems)
    return problems


def _tuple_from(value: object) -> tuple:
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes, dict)):
        return tuple(value)
    return (value,)


def _omission_tuple(value: object) -> tuple:
    omissions = _tuple_from(value)
    return tuple(Omission.from_dict(item) if isinstance(item, dict) else item for item in omissions)


def _check_member(name: str, value: object, allowed: tuple[str, ...], problems: list[str]) -> None:
    if value not in allowed:
        problems.append(f"{name} must be one of {list(allowed)}, got {value!r}")


def _check_non_empty_string(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, str) or value == "":
        problems.append(f"{name} must be a non-empty string")


def _check_string_tuple(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append(f"{name} must be a tuple")
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            problems.append(f"{name}[{index}] must be a string")


def _check_sha256(name: str, value: object, problems: list[str]) -> None:
    if not is_sha256_ref(value):
        problems.append(f"{name} must be a sha256: reference")


def _check_lossy(value: object, problems: list[str]) -> None:
    if not isinstance(value, bool):
        problems.append("lossy must be bool")


def _check_omissions(value: object, problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append("omissions must be a tuple")
        return
    for index, omission in enumerate(value):
        for problem in validate_omission(omission):
            problems.append(f"omissions[{index}]: {problem}")
