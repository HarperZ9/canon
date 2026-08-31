from __future__ import annotations
import copy
import json
from dataclasses import dataclass, field, replace
from typing import Callable, ClassVar, Iterable
from .adapter import INTEGRATION_TIERS
from .atom import CanonAtom, atoms_from_records, validate_atom
from .canonical_json import (
    CANONICALIZATION as JSON_CANONICALIZATION,
    CanonicalJSONError,
    canonical_json_bytes,
    canonical_json_text,
    canonical_sha256,
    is_sha256_ref,
)
from .omission import Omission, validate_omission
from .schema import SCHEMA as RECORD_SCHEMA, Record
from .transform import TransformReceipt, validate_transform_receipt
from .readiness import ReadinessProbe
from .validator import validate_record
CAPSULE_SCHEMA = "canon.capsule/v1"
CAPSULE_PROFILES = ("needle", "handoff", "archive", "custom")
CANONICALIZATION = JSON_CANONICALIZATION
SOURCE_STATE_DIGEST_KEYS = (
    "records_digest",
    "inventory_digest",
    "context_envelope_digest",
    "mneme_snapshot_digest",
    "relay_checkpoint",
    "worktree_digest",
)
class CapsuleError(ValueError): pass
class CapsuleBuildError(CapsuleError): pass
@dataclass(frozen=True, slots=True)
class CapsuleTarget:
    adapter: str
    surface: str
    integration_tier: str
    host_enforcement_observed: bool = False
    def to_dict(self) -> dict:
        return {
            "adapter": self.adapter,
            "surface": self.surface,
            "integration_tier": self.integration_tier,
            "host_enforcement_observed": self.host_enforcement_observed,
        }
    @classmethod
    def from_dict(cls, d: dict) -> "CapsuleTarget":
        if not isinstance(d, dict):
            raise TypeError(f"capsule target JSON must be an object, got {type(d).__name__}")
        return cls(d["adapter"], d["surface"], d["integration_tier"], d.get("host_enforcement_observed", False))
@dataclass(frozen=True, slots=True)
class SourceState:
    records_digest: str
    inventory_digest: str | None = None
    context_envelope_digest: str | None = None
    mneme_snapshot_digest: str | None = None
    relay_checkpoint: str | None = None
    worktree_digest: str | None = None
    def to_dict(self) -> dict:
        return {
            "records_digest": self.records_digest,
            "inventory_digest": self.inventory_digest,
            "context_envelope_digest": self.context_envelope_digest,
            "mneme_snapshot_digest": self.mneme_snapshot_digest,
            "relay_checkpoint": self.relay_checkpoint,
            "worktree_digest": self.worktree_digest,
        }
    @classmethod
    def from_dict(cls, d: dict) -> "SourceState":
        if not isinstance(d, dict):
            raise TypeError(f"source state JSON must be an object, got {type(d).__name__}")
        return cls(
            d["records_digest"],
            d.get("inventory_digest"),
            d.get("context_envelope_digest"),
            d.get("mneme_snapshot_digest"),
            d.get("relay_checkpoint"),
            d.get("worktree_digest"),
        )
@dataclass(frozen=True, slots=True)
class Compatibility:
    record_schema_min: str = RECORD_SCHEMA
    capsule_schema: str = CAPSULE_SCHEMA
    requires_features: tuple[str, ...] = ()
    def __post_init__(self) -> None:
        object.__setattr__(self, "requires_features", _tuple_sequence(self.requires_features))
    def to_dict(self) -> dict:
        return {
            "record_schema_min": self.record_schema_min,
            "capsule_schema": self.capsule_schema,
            "requires_features": _json_sequence(self.requires_features),
        }
    @classmethod
    def from_dict(cls, d: dict) -> "Compatibility":
        if not isinstance(d, dict):
            raise TypeError(f"compatibility JSON must be an object, got {type(d).__name__}")
        return cls(d["record_schema_min"], d["capsule_schema"], d["requires_features"])
@dataclass(frozen=True, slots=True)
class Budget:
    profile: str
    max_tokens: int
    estimated_tokens: int
    estimator: str
    policy: str = "critical-atoms-lossless"
    def to_dict(self) -> dict:
        return {
            "profile": self.profile,
            "max_tokens": self.max_tokens,
            "estimated_tokens": self.estimated_tokens,
            "estimator": self.estimator,
            "policy": self.policy,
        }
    @classmethod
    def from_dict(cls, d: dict) -> "Budget":
        if not isinstance(d, dict):
            raise TypeError(f"budget JSON must be an object, got {type(d).__name__}")
        return cls(d["profile"], d["max_tokens"], d["estimated_tokens"], d["estimator"], d.get("policy", "critical-atoms-lossless"))
@dataclass(frozen=True, slots=True)
class Integrity:
    canonicalization: str
    manifest_sha256: str
    def to_dict(self) -> dict:
        return {"canonicalization": self.canonicalization, "manifest_sha256": self.manifest_sha256}
    @classmethod
    def from_dict(cls, d: dict) -> "Integrity":
        if not isinstance(d, dict):
            raise TypeError(f"integrity JSON must be an object, got {type(d).__name__}")
        return cls(d["canonicalization"], d["manifest_sha256"])
@dataclass(frozen=True, slots=True)
class Capsule:
    capsule_id: str
    profile: str
    target: CapsuleTarget
    source_state: SourceState
    compatibility: Compatibility
    budget: Budget
    layers: tuple[str, ...]
    atoms: tuple[CanonAtom, ...]
    records: tuple[Record, ...]
    conflicts: tuple[CanonAtom, ...]
    unknowns: tuple[CanonAtom, ...]
    omissions: tuple[Omission, ...]
    lossy_transforms: tuple[TransformReceipt, ...]
    freshness: tuple[dict, ...]
    integrity: Integrity
    receipts: tuple[dict, ...]
    does_not_prove: tuple[str, ...]
    schema: ClassVar[str] = CAPSULE_SCHEMA
    def __post_init__(self) -> None:
        object.__setattr__(self, "target", _value_of(self.target, CapsuleTarget.from_dict))
        object.__setattr__(self, "source_state", _value_of(self.source_state, SourceState.from_dict))
        object.__setattr__(self, "compatibility", _value_of(self.compatibility, Compatibility.from_dict))
        object.__setattr__(self, "budget", _value_of(self.budget, Budget.from_dict))
        object.__setattr__(self, "integrity", _value_of(self.integrity, Integrity.from_dict))
        object.__setattr__(self, "layers", _tuple_sequence(self.layers))
        object.__setattr__(self, "atoms", _tuple_of(self.atoms, CanonAtom.from_dict))
        object.__setattr__(self, "records", _tuple_of(self.records, Record.from_dict))
        object.__setattr__(self, "conflicts", _tuple_of(self.conflicts, CanonAtom.from_dict))
        object.__setattr__(self, "unknowns", _tuple_of(self.unknowns, CanonAtom.from_dict))
        object.__setattr__(self, "omissions", _tuple_of(self.omissions, Omission.from_dict))
        object.__setattr__(self, "lossy_transforms", _tuple_of(self.lossy_transforms, TransformReceipt.from_dict))
        object.__setattr__(self, "freshness", _tuple_sequence(self.freshness))
        object.__setattr__(self, "receipts", _tuple_sequence(self.receipts))
        object.__setattr__(self, "does_not_prove", _tuple_sequence(self.does_not_prove))
    def to_dict(self, *, identity: bool = True) -> dict:
        capsule_id = self.capsule_id if identity else ""
        result = {
            "schema": CAPSULE_SCHEMA,
            "capsule_id": capsule_id,
            "profile": self.profile,
            "target": _value_to_dict(self.target, CapsuleTarget),
            "source_state": _value_to_dict(self.source_state, SourceState),
            "compatibility": _value_to_dict(self.compatibility, Compatibility),
            "budget": _value_to_dict(self.budget, Budget),
            "layers": _json_sequence(self.layers),
            "atoms": _items_to_json(self.atoms, CanonAtom),
            "records": _items_to_json(self.records, Record),
            "conflicts": _items_to_json(self.conflicts, CanonAtom),
            "unknowns": _items_to_json(self.unknowns, CanonAtom),
            "omissions": _items_to_json(self.omissions, Omission),
            "lossy_transforms": _items_to_json(self.lossy_transforms, TransformReceipt),
            "freshness": _json_sequence(self.freshness),
            "integrity": _value_to_dict(self.integrity, Integrity),
            "receipts": _json_sequence(self.receipts),
            "does_not_prove": _json_sequence(self.does_not_prove),
        }
        if not identity:
            _blank_manifest_sha256(result)
        return result
    @classmethod
    def from_dict(cls, d: dict) -> "Capsule":
        if not isinstance(d, dict):
            raise TypeError(f"capsule JSON must be an object, got {type(d).__name__}")
        got = d.get("schema")
        if got != CAPSULE_SCHEMA:
            raise ValueError(f"expected schema {CAPSULE_SCHEMA!r}, got {got!r}")
        return cls(
            d["capsule_id"], d["profile"], d["target"], d["source_state"], d["compatibility"],
            d["budget"], d["layers"], d["atoms"], d["records"], d["conflicts"],
            d["unknowns"], d["omissions"], d["lossy_transforms"], d["freshness"],
            d["integrity"], d["receipts"], d.get("does_not_prove", ()),
        )
    def to_json(self) -> str:
        return canonical_json_text(self.to_dict())
@dataclass(frozen=True, slots=True)
class CapsuleCompileRequest:
    profile: str
    target: CapsuleTarget
    source_state: SourceState
    budget: Budget
    atoms: tuple[CanonAtom, ...] = ()
    records: tuple[Record, ...] = ()
    omissions: tuple[Omission, ...] = ()
    lossy_transforms: tuple[TransformReceipt, ...] = ()
    receipts: tuple[dict, ...] = ()
    does_not_prove: tuple[str, ...] = ()
    required_atom_ids: tuple[str, ...] = ()
    readiness_probe_id: str = "readiness-default"
    readiness_target: dict | None = None
    def __post_init__(self) -> None:
        object.__setattr__(self, "target", _value_of(self.target, CapsuleTarget.from_dict))
        object.__setattr__(self, "source_state", _value_of(self.source_state, SourceState.from_dict))
        object.__setattr__(self, "budget", _value_of(self.budget, Budget.from_dict))
        object.__setattr__(self, "atoms", _tuple_of(self.atoms, CanonAtom.from_dict))
        object.__setattr__(self, "records", _tuple_of(self.records, Record.from_dict))
        object.__setattr__(self, "omissions", _tuple_of(self.omissions, Omission.from_dict))
        object.__setattr__(self, "lossy_transforms", _tuple_of(self.lossy_transforms, TransformReceipt.from_dict))
        object.__setattr__(self, "receipts", _tuple_sequence(self.receipts))
        object.__setattr__(self, "does_not_prove", _tuple_sequence(self.does_not_prove))
        object.__setattr__(self, "required_atom_ids", _tuple_sequence(self.required_atom_ids))
        object.__setattr__(self, "readiness_target", copy.deepcopy(self.readiness_target))
@dataclass(frozen=True, slots=True)
class CapsuleBundle:
    capsule: Capsule
    manifest_bytes: bytes
    canon_md: str
    readiness_probe: ReadinessProbe
def capsule_identity_dict(capsule: Capsule) -> dict:
    return capsule.to_dict(identity=False)
def capsule_digest(capsule: Capsule) -> str:
    return canonical_sha256(capsule_identity_dict(capsule))
def capsule_bytes(capsule: Capsule) -> bytes:
    return canonical_json_bytes(capsule.to_dict())
def build_capsule(
    *,
    profile: str,
    target: CapsuleTarget,
    source_state: SourceState,
    budget: Budget,
    atoms: Iterable[CanonAtom],
    records: Iterable[Record] = (),
    omissions: Iterable[Omission] = (),
    lossy_transforms: Iterable[TransformReceipt] = (),
    receipts: Iterable[dict] = (),
    does_not_prove: Iterable[str] = (),
    required_atom_ids: Iterable[str] = (),
) -> Capsule:
    record_items = tuple(records)
    atom_items = tuple(atoms) + tuple(atoms_from_records(record_items))
    duplicate_identities = _duplicate_atom_identities(atom_items)
    if duplicate_identities:
        raise CapsuleBuildError(f"duplicate atom identity {duplicate_identities[0]!r}")
    sorted_atoms = tuple(sorted(atom_items, key=_atom_sort_key))
    _check_required_atoms(sorted_atoms, tuple(required_atom_ids))
    draft = Capsule(
        "", profile, target, source_state, Compatibility(), budget,
        _layers(sorted_atoms), sorted_atoms, _sorted_records(record_items),
        _atoms_of_type(sorted_atoms, "conflict"), _atoms_of_type(sorted_atoms, "unknown"),
        _sorted_omissions(tuple(omissions)), _sorted_transforms(tuple(lossy_transforms)),
        _freshness(sorted_atoms), Integrity(CANONICALIZATION, ""),
        _sorted_receipts(tuple(receipts)), tuple(does_not_prove),
    )
    digest = capsule_digest(draft)
    return replace(draft, capsule_id=digest, integrity=Integrity(CANONICALIZATION, digest))
def validate_capsule(capsule: Capsule) -> list[str]:
    if not isinstance(capsule, Capsule):
        return ["capsule must be a Capsule"]
    problems: list[str] = []
    _check_member("profile", capsule.profile, CAPSULE_PROFILES, problems)
    _check_sha256("capsule_id", capsule.capsule_id, problems)
    _check_target(capsule.target, problems)
    _check_source_state(capsule.source_state, problems)
    _check_compatibility(capsule.compatibility, problems)
    _check_budget(capsule.profile, capsule.budget, problems)
    _check_string_tuple("layers", capsule.layers, problems)
    _check_nested("atoms", capsule.atoms, CanonAtom, validate_atom, problems)
    for key in _duplicate_atom_identities(capsule.atoms):
        problems.append(f"atoms contain duplicate atom identity {key!r}")
    _check_nested("records", capsule.records, Record, validate_record, problems)
    _check_nested("conflicts", capsule.conflicts, CanonAtom, validate_atom, problems)
    _check_nested("unknowns", capsule.unknowns, CanonAtom, validate_atom, problems)
    _check_nested("omissions", capsule.omissions, Omission, validate_omission, problems)
    _check_nested("lossy_transforms", capsule.lossy_transforms, TransformReceipt, validate_transform_receipt, problems)
    _check_dict_tuple("freshness", capsule.freshness, problems)
    _check_dict_tuple("receipts", capsule.receipts, problems)
    _check_string_tuple("does_not_prove", capsule.does_not_prove, problems)
    _check_integrity(capsule, problems)
    _check_ordering(capsule, problems)
    _check_derived_fields(capsule, problems)
    return problems
def _value_of(value: object, factory: Callable[[dict], object]) -> object:
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    try:
        return factory(value)
    except (KeyError, TypeError, ValueError):
        return copy.deepcopy(value)
def _tuple_of(value: object, factory: Callable[[dict], object]) -> object:
    if not isinstance(value, (list, tuple)):
        return copy.deepcopy(value)
    return tuple(_value_of(item, factory) for item in value)
def _tuple_sequence(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return tuple(copy.deepcopy(item) for item in value)
    return copy.deepcopy(value)
def _json_sequence(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return [copy.deepcopy(item) for item in value]
    return copy.deepcopy(value)
def _items_to_json(value: object, item_type: type) -> object:
    if not isinstance(value, (list, tuple)):
        return copy.deepcopy(value)
    return [item.to_dict() if isinstance(item, item_type) else copy.deepcopy(item) for item in value]
def _value_to_dict(value: object, value_type: type) -> object:
    return value.to_dict() if isinstance(value, value_type) else copy.deepcopy(value)
def _blank_manifest_sha256(result: dict) -> None:
    integrity = result.get("integrity")
    if isinstance(integrity, dict):
        integrity["manifest_sha256"] = ""
def _atom_sort_key(atom: CanonAtom) -> tuple[object, ...]:
    return (atom.precedence_rank, atom.layer, atom.type, atom.id)
def _duplicate_atom_identities(atoms: object) -> tuple[tuple[object, ...], ...]:
    counts: dict[tuple[object, ...], int] = {}
    if isinstance(atoms, tuple):
        for atom in atoms:
            if isinstance(atom, CanonAtom):
                key = _atom_sort_key(atom); counts[key] = counts.get(key, 0) + 1
    return tuple(key for key, count in sorted(counts.items()) if count > 1)
def _sorted_records(records: tuple[Record, ...]) -> tuple[Record, ...]:
    return tuple(sorted(records, key=lambda r: (r.scope, r.id, r.kind)))
def _sorted_omissions(omissions: tuple[Omission, ...]) -> tuple[Omission, ...]:
    return tuple(sorted(omissions, key=lambda o: (o.reason, o.critical, o.decision, o.affected_ids)))
def _sorted_transforms(receipts: tuple[TransformReceipt, ...]) -> tuple[TransformReceipt, ...]:
    return tuple(sorted(receipts, key=lambda r: (r.transform, r.method_id, r.output_ref)))
def _sorted_receipts(receipts: tuple[dict, ...]) -> tuple[dict, ...]:
    return tuple(sorted((copy.deepcopy(r) for r in receipts), key=_receipt_sort_key))
def _receipt_sort_key(receipt: dict) -> str:
    try:
        return canonical_json_text(receipt)
    except (CanonicalJSONError, TypeError, ValueError):
        return repr(receipt)
def _layers(atoms: tuple[CanonAtom, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    layers: list[str] = []
    for atom in atoms:
        if atom.layer not in seen:
            seen.add(atom.layer)
            layers.append(atom.layer)
    return tuple(layers)
def _atoms_of_type(atoms: tuple[CanonAtom, ...], atom_type: str) -> tuple[CanonAtom, ...]:
    return tuple(atom for atom in atoms if atom.type == atom_type)
def _freshness(atoms: tuple[CanonAtom, ...]) -> tuple[dict, ...]:
    return tuple(_freshness_row(atom) for atom in atoms if atom.freshness)
def _freshness_row(atom: CanonAtom) -> dict:
    return {"id": atom.id, "type": atom.type, "status": atom.status, "freshness": copy.deepcopy(atom.freshness)}
def _check_required_atoms(atoms: tuple[CanonAtom, ...], required_ids: tuple[str, ...]) -> None:
    by_id = {atom.id: atom for atom in atoms}
    for required_id in required_ids:
        atom = by_id.get(required_id)
        if atom is None:
            raise CapsuleBuildError(f"required atom {required_id!r} is missing")
        if atom.critical is not True:
            raise CapsuleBuildError(f"required atom {required_id!r} is not critical")
def _check_member(name: str, value: object, allowed: tuple[str, ...], problems: list[str]) -> None:
    if value not in allowed:
        problems.append(f"{name} must be one of {list(allowed)}, got {value!r}")
def _check_non_empty_string(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, str) or value == "":
        problems.append(f"{name} must be a non-empty string")
def _check_sha256(name: str, value: object, problems: list[str]) -> None:
    if not is_sha256_ref(value):
        problems.append(f"{name} must be a sha256: reference")
def _check_non_negative_int(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        problems.append(f"{name} must be a non-negative int")
def _check_string_tuple(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append(f"{name} must be a tuple")
        return
    for position, item in enumerate(value):
        if not isinstance(item, str):
            problems.append(f"{name}[{position}] must be a string")
def _check_dict_tuple(name: str, value: object, problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append(f"{name} must be a tuple")
        return
    for position, item in enumerate(value):
        if not isinstance(item, dict):
            problems.append(f"{name}[{position}] must be a dict")
def _check_nested(name: str, value: object, item_type: type, validator: Callable[[object], list[str]], problems: list[str]) -> None:
    if not isinstance(value, tuple):
        problems.append(f"{name} must be a tuple")
        return
    for position, item in enumerate(value):
        if not isinstance(item, item_type):
            problems.append(f"{name}[{position}] must be a {item_type.__name__}")
            continue
        for problem in validator(item):
            problems.append(f"{name}[{position}]: {problem}")
def _check_target(target: object, problems: list[str]) -> None:
    if not isinstance(target, CapsuleTarget):
        problems.append("target must be a CapsuleTarget")
        return
    _check_non_empty_string("target.adapter", target.adapter, problems)
    _check_non_empty_string("target.surface", target.surface, problems)
    _check_member("target.integration_tier", target.integration_tier, INTEGRATION_TIERS, problems)
    if not isinstance(target.host_enforcement_observed, bool):
        problems.append("target.host_enforcement_observed must be bool")
    if target.host_enforcement_observed is True and target.integration_tier != "enforced":
        problems.append("target.host_enforcement_observed requires integration_tier 'enforced'")
def _check_source_state(source_state: object, problems: list[str]) -> None:
    if not isinstance(source_state, SourceState):
        problems.append("source_state must be a SourceState")
        return
    for key in SOURCE_STATE_DIGEST_KEYS:
        value = getattr(source_state, key)
        if key == "records_digest" or value is not None:
            _check_sha256(f"source_state.{key}", value, problems)
def _check_compatibility(compatibility: object, problems: list[str]) -> None:
    if not isinstance(compatibility, Compatibility):
        problems.append("compatibility must be a Compatibility")
        return
    if compatibility.record_schema_min != RECORD_SCHEMA:
        problems.append(f"compatibility.record_schema_min must be {RECORD_SCHEMA!r}")
    if compatibility.capsule_schema != CAPSULE_SCHEMA:
        problems.append(f"compatibility.capsule_schema must be {CAPSULE_SCHEMA!r}")
    _check_string_tuple("compatibility.requires_features", compatibility.requires_features, problems)
def _check_budget(profile: str, budget: object, problems: list[str]) -> None:
    if not isinstance(budget, Budget):
        problems.append("budget must be a Budget")
        return
    _check_member("budget.profile", budget.profile, CAPSULE_PROFILES, problems)
    if budget.profile != profile:
        problems.append("budget.profile must match profile")
    _check_non_negative_int("budget.max_tokens", budget.max_tokens, problems)
    _check_non_negative_int("budget.estimated_tokens", budget.estimated_tokens, problems)
    if isinstance(budget.estimated_tokens, int) and isinstance(budget.max_tokens, int):
        if not isinstance(budget.estimated_tokens, bool) and budget.estimated_tokens > budget.max_tokens:
            problems.append("budget.estimated_tokens must be <= budget.max_tokens")
    _check_member("budget.estimator", budget.estimator, ("known", "unknown"), problems)
    if budget.policy != "critical-atoms-lossless":
        problems.append("budget.policy must be 'critical-atoms-lossless'")
def _check_integrity(capsule: Capsule, problems: list[str]) -> None:
    integrity = capsule.integrity
    if not isinstance(integrity, Integrity):
        problems.append("integrity must be an Integrity")
        return
    if integrity.canonicalization != CANONICALIZATION:
        problems.append(f"integrity.canonicalization must be {CANONICALIZATION!r}")
    _check_sha256("integrity.manifest_sha256", integrity.manifest_sha256, problems)
    if integrity.manifest_sha256 != capsule.capsule_id:
        problems.append("integrity.manifest_sha256 must match capsule_id")
    _check_digest_binding(capsule, problems)
def _check_digest_binding(capsule: Capsule, problems: list[str]) -> None:
    try:
        expected = capsule_digest(capsule)
    except (CanonicalJSONError, TypeError, ValueError, AttributeError):
        problems.append("capsule identity payload must be canonical JSON encodable")
        return
    if is_sha256_ref(capsule.capsule_id) and capsule.capsule_id != expected:
        problems.append("capsule_id must match identity digest")
def _check_ordering(capsule: Capsule, problems: list[str]) -> None:
    if isinstance(capsule.atoms, tuple) and all(isinstance(a, CanonAtom) for a in capsule.atoms):
        if capsule.atoms != tuple(sorted(capsule.atoms, key=_atom_sort_key)):
            problems.append("atoms must be sorted by precedence_rank, layer, type, id")
    if isinstance(capsule.records, tuple) and all(isinstance(r, Record) for r in capsule.records):
        if capsule.records != _sorted_records(capsule.records):
            problems.append("records must be sorted by scope, id, kind")
    if isinstance(capsule.omissions, tuple) and all(isinstance(o, Omission) for o in capsule.omissions):
        if capsule.omissions != _sorted_omissions(capsule.omissions):
            problems.append("omissions must be sorted by reason, critical, decision, affected_ids")
    if isinstance(capsule.lossy_transforms, tuple) and all(isinstance(r, TransformReceipt) for r in capsule.lossy_transforms):
        if capsule.lossy_transforms != _sorted_transforms(capsule.lossy_transforms):
            problems.append("lossy_transforms must be sorted by transform, method_id, output_ref")
    if isinstance(capsule.receipts, tuple) and all(isinstance(r, dict) for r in capsule.receipts):
        if capsule.receipts != _sorted_receipts(capsule.receipts):
            problems.append("receipts must be sorted by canonical JSON")
def _check_derived_fields(capsule: Capsule, problems: list[str]) -> None:
    if not isinstance(capsule.atoms, tuple) or not all(isinstance(a, CanonAtom) for a in capsule.atoms):
        return
    if capsule.layers != _layers(capsule.atoms):
        problems.append("layers must be derived from sorted atoms")
    if capsule.conflicts != _atoms_of_type(capsule.atoms, "conflict"):
        problems.append("conflicts must be derived from atoms")
    if capsule.unknowns != _atoms_of_type(capsule.atoms, "unknown"):
        problems.append("unknowns must be derived from atoms")
    if capsule.freshness != _freshness(capsule.atoms):
        problems.append("freshness must be derived from atoms")
