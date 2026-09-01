from __future__ import annotations

from dataclasses import dataclass

from .atom import CanonAtom, validate_atom
from .canonical_json import is_sha256_ref
from .omission import Omission, validate_omission
from .transform import TransformReceipt

TRUST_LABELS = ("trusted-local", "signed-pinned", "signed-unknown-key", "unsigned-local", "imported-untrusted", "model-synthesized-unreviewed", "secret-quarantined", "stale", "public-exportable", "private-local-only")
DISCLOSURE_PROFILES = ("full-local", "project-only", "no-secrets", "team-safe", "public-safe", "need-to-know")


@dataclass(frozen=True, slots=True)
class ImportSubject:
    source_id: str
    atoms: tuple[CanonAtom, ...]
    signature_status: str
    key_id: str | None
    local: bool
    source_state_sha256: str
    model_synthesized: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "atoms", _tuple_or_original(self.atoms))


@dataclass(frozen=True, slots=True)
class ImportDecision:
    ok: bool
    trust_label: str
    profile: str
    accepted_atom_ids: tuple[str, ...]
    omissions: tuple[Omission, ...]
    receipts: tuple[TransformReceipt, ...]
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", _tuple_or_original(self.accepted_atom_ids))
        object.__setattr__(self, "omissions", _tuple_or_original(self.omissions))
        object.__setattr__(self, "receipts", _tuple_or_original(self.receipts))
        object.__setattr__(self, "reason_codes", _tuple_or_original(self.reason_codes))


def classify_trust(
    *,
    signature_status: str,
    key_id: str | None,
    pinned_key_ids: frozenset[str],
    local: bool,
    model_synthesized: bool = False,
) -> str:
    if model_synthesized is True:
        return "model-synthesized-unreviewed"
    if signature_status not in ("valid", "none"):
        return "imported-untrusted"
    if signature_status == "valid":
        if _non_empty_string(key_id) and _valid_pin_set(pinned_key_ids) and key_id in pinned_key_ids:
            return "signed-pinned"
        return "signed-unknown-key"
    if local is True:
        return "unsigned-local"
    return "imported-untrusted"


def validate_atom_activation(atom: CanonAtom, *, trust_label: str) -> tuple[str, ...]:
    reasons: list[str] = []
    if trust_label not in TRUST_LABELS:
        _add(reasons, "invalid-trust-label")
    elif trust_label in _BLOCKED_TRUST:
        _add(reasons, _BLOCKED_TRUST[trust_label])
    atom_dict = _validated_atom_dict(atom, reasons)
    if atom_dict is None:
        return tuple(reasons)
    _add_atom_policy_reasons(atom_dict, reasons)
    if trust_label == "model-synthesized-unreviewed" and _normative_like(atom_dict):
        _add(reasons, "unreviewed-model-normative")
    return tuple(reasons)


def disclosure_omissions(atoms: tuple[CanonAtom, ...], *, profile: str) -> tuple[Omission, ...]:
    if profile not in _OMITTING_PROFILES or not isinstance(atoms, (tuple, list)):
        return ()
    omissions: list[Omission] = []
    for atom in atoms:
        atom_dict = _atom_dict(atom)
        if atom_dict is None or _disclosure_profile(atom_dict) != "private-local-only":
            continue
        atom_id = atom_dict.get("id")
        if not _non_empty_string(atom_id):
            continue
        critical = atom_dict.get("critical") is True
        omissions.append(Omission(
            reason="policy",
            count=1,
            affected_ids=(atom_id,),
            affected_source_refs=_source_ref_strings(atom_dict),
            critical=critical,
            decision="fail-build" if critical else "omitted",
            does_not_prove=(_PRIVATE_LOCAL_ONLY_LIMITATION,),
        ))
    return tuple(omissions)


def review_import_subject(
    subject: ImportSubject,
    *,
    profile: str,
    pinned_key_ids: frozenset[str],
) -> ImportDecision:
    if not isinstance(subject, ImportSubject):
        return _decision(False, "imported-untrusted", profile, (), (), ("invalid-subject",))
    reasons: list[str] = []
    _validate_subject_inputs(subject, profile, pinned_key_ids, reasons)
    trust_label = classify_trust(
        signature_status=subject.signature_status,
        key_id=subject.key_id,
        pinned_key_ids=pinned_key_ids,
        local=subject.local,
        model_synthesized=subject.model_synthesized,
    )
    atoms = subject.atoms if isinstance(subject.atoms, tuple) else ()
    if not isinstance(subject.atoms, tuple):
        _add(reasons, "invalid-atoms")
    _check_duplicate_ids(atoms, reasons)
    for atom in atoms:
        for reason in validate_atom_activation(atom, trust_label=trust_label):
            _add(reasons, reason)
    omissions = disclosure_omissions(atoms, profile=profile)
    _add_omission_reasons(omissions, reasons)
    if trust_label not in _ACTIVATING_TRUST:
        _add(reasons, "untrusted-import")
    accepted = _accepted_ids(atoms) if not reasons else ()
    return _decision(not reasons, trust_label, profile, accepted, omissions, tuple(reasons))


_SIGNATURE_STATUSES = frozenset({"valid", "none"})
_ATOM_DISCLOSURE_PROFILES = frozenset(DISCLOSURE_PROFILES + ("private-local-only",))
_OMITTING_PROFILES = frozenset({"team-safe", "public-safe", "no-secrets", "need-to-know"})
_ACTIVATING_TRUST = frozenset({"trusted-local", "signed-pinned", "unsigned-local"})
_BLOCKED_TRUST = {"signed-unknown-key": "untrusted-import", "imported-untrusted": "untrusted-import", "secret-quarantined": "secret-quarantined", "stale": "stale"}
_MODEL_NORMATIVE_TYPES = frozenset({"active-goal", "permission", "prohibition", "constraint", "frontier-state", "conflict", "unknown"})
_PRIVATE_LOCAL_ONLY_LIMITATION = "This private-local-only omission does not prove the omitted content is safe to disclose elsewhere."


def _decision(
    ok: bool,
    trust_label: str,
    profile: object,
    accepted_atom_ids: tuple[str, ...],
    omissions: tuple[Omission, ...],
    reason_codes: tuple[str, ...],
) -> ImportDecision:
    return ImportDecision(ok, trust_label, profile if isinstance(profile, str) else "", accepted_atom_ids, omissions, (), reason_codes)


def _validate_subject_inputs(
    subject: ImportSubject,
    profile: object,
    pinned_key_ids: object,
    reasons: list[str],
) -> None:
    if not _non_empty_string(subject.source_id):
        _add(reasons, "invalid-source-id")
    if profile not in DISCLOSURE_PROFILES:
        _add(reasons, "invalid-profile")
    if not _valid_pin_set(pinned_key_ids):
        _add(reasons, "invalid-pinned-key-ids")
    if subject.signature_status not in _SIGNATURE_STATUSES:
        _add(reasons, "invalid-signature-status")
    if subject.signature_status == "valid" and not _non_empty_string(subject.key_id):
        _add(reasons, "invalid-key-id")
    if subject.signature_status == "none" and subject.local is False:
        _add(reasons, "unsigned-remote")
    if not isinstance(subject.local, bool):
        _add(reasons, "invalid-local-flag")
    if not isinstance(subject.model_synthesized, bool):
        _add(reasons, "invalid-model-synthesized-flag")
    if not is_sha256_ref(subject.source_state_sha256):
        _add(reasons, "invalid-source-state-sha256")


def _validated_atom_dict(atom: object, reasons: list[str]) -> dict | None:
    try:
        problems = validate_atom(atom)
    except Exception:
        _add(reasons, "invalid-atom")
        return None
    if problems:
        _add(reasons, "invalid-atom")
    return _atom_dict(atom)


def _atom_dict(atom: object) -> dict | None:
    if not isinstance(atom, CanonAtom):
        return None
    try:
        return atom.to_dict()
    except Exception:
        return None


def _add_atom_policy_reasons(atom_dict: dict, reasons: list[str]) -> None:
    if _trust_label(atom_dict) not in TRUST_LABELS:
        _add(reasons, "invalid-atom-trust-label")
    if _disclosure_profile(atom_dict) not in _ATOM_DISCLOSURE_PROFILES:
        _add(reasons, "invalid-atom-disclosure-profile")
    if _freshness_state(atom_dict) == "stale" or atom_dict.get("status") == "stale":
        _add(reasons, "stale")
    if _invalid_hashes(atom_dict):
        _add(reasons, "invalid-atom-hash")


def _add_omission_reasons(omissions: tuple[Omission, ...], reasons: list[str]) -> None:
    for omission in omissions:
        if validate_omission(omission):
            _add(reasons, "invalid-omission")
        _add(reasons, "private-local-only")
        if omission.critical:
            _add(reasons, "critical-disclosure-omission")


def _check_duplicate_ids(atoms: tuple[object, ...], reasons: list[str]) -> None:
    seen: set[str] = set()
    for atom in atoms:
        atom_id = atom.id if isinstance(atom, CanonAtom) and isinstance(atom.id, str) else None
        if atom_id is None:
            continue
        if atom_id in seen:
            _add(reasons, "duplicate-atom-id")
        seen.add(atom_id)


def _accepted_ids(atoms: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(atom.id for atom in atoms if isinstance(atom, CanonAtom) and isinstance(atom.id, str))


def _source_ref_strings(atom_dict: dict) -> tuple[str, ...]:
    refs = atom_dict.get("source_refs", ())
    if not isinstance(refs, (list, tuple)):
        return ()
    return tuple(ref["ref"] for ref in refs if isinstance(ref, dict) and isinstance(ref.get("ref"), str))


def _invalid_hashes(atom_dict: dict) -> bool:
    hashes = atom_dict.get("hashes")
    if not isinstance(hashes, dict):
        return True
    return any(name.endswith("sha256") and not is_sha256_ref(value) for name, value in hashes.items())


def _normative_like(atom_dict: dict) -> bool:
    return atom_dict.get("critical") is True or atom_dict.get("classification") == "normative" or atom_dict.get("type") in _MODEL_NORMATIVE_TYPES


def _trust_label(atom_dict: dict) -> object:
    trust = atom_dict.get("trust")
    return trust.get("label") if isinstance(trust, dict) else None


def _disclosure_profile(atom_dict: dict) -> object:
    disclosure = atom_dict.get("disclosure")
    return disclosure.get("profile") if isinstance(disclosure, dict) else None


def _freshness_state(atom_dict: dict) -> object:
    freshness = atom_dict.get("freshness")
    return freshness.get("state") if isinstance(freshness, dict) else None


def _valid_pin_set(value: object) -> bool:
    return isinstance(value, frozenset) and all(_non_empty_string(item) for item in value)


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and value != ""


def _tuple_or_original(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return value


def _add(reasons: list[str], code: str) -> None:
    if code not in reasons:
        reasons.append(code)
