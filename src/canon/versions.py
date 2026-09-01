"""versions.py -- the version-pin registry for every seam canon owns.

Every band lands a version-tagged wire: F0 stamps `canon.record/v1` into every
serialized record, R0 fixes the region markers, R2 fixes the frontmatter and
one-note codec, V2 fixes the drift-verdict shape, V4 fixes the run-witness
kind, and M4.1/M4.2 add the transport seam and the vault frontend. Each of
those wires needs a stable handle a caller (or a downstream tool) can look up,
compare, and refuse loud on drift. This module holds every such handle in one
`PIN_REGISTRY`, with a closed short-name vocabulary (`SEAM_PINS`) that Wave 1
kinds are explicitly excluded from (they belong to their own future bands).

The registry is a read-only `MappingProxyType` view over a module-level dict
populated once at import. `pin_registry_scope()` is the only write path outside
module init; it uses `contextvars.ContextVar` for per-context override (a test
that installs a fake pin does not affect a concurrent test in another context).
Canon carries no `threading.Lock`; the registry offers per-context isolation,
not concurrent-mutation safety (D-96).

The refusal hierarchy is two roots: `VersionError` for runtime lookup and
compat questions, `MigrationError` for the migration seam that ships in
`versions_migrate.py`. `SchemaPin.__post_init__` raises `ValueError` on bad
fields (a wiring fault, not a runtime version error).

Backwards-compat rule (D-94): the literal `"canon.record/v1"` lives here in
`PIN_RECORD.kind_tag`; `canon.schema.SCHEMA` aliases it via a bottom-of-module
import (landed in commit 8 of the M4 stack). Every module that reads `SCHEMA`
reads the same byte-identical string; no fixture is rewritten.
"""
from __future__ import annotations

import contextvars
import json
import re
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterator


class VersionError(Exception):
    """Runtime pin-lookup or compat error. Never leaked from a bad
    constructor (that is `ValueError`)."""


class UnknownPin(VersionError):
    """`pin_for` on a short-name not in `SEAM_PINS`, or
    `pin_from_schema_field` on a kind_tag no registered pin matches."""


class IncompatiblePin(VersionError):
    """`is_compatible` returned False when the caller required equality, or
    `migrate` on a (from, to) pair with no registered migrator."""


class MalformedPin(VersionError):
    """`is_compatible` called on a non-SchemaPin, or `pin_from_schema_field`
    called on a string that fails the kind_tag grammar."""


SEAM_PINS: frozenset[str] = frozenset({
    "record",
    "backend-seam",
    "textblock-grammar",
    "region-marker",
    "frontmatter",
    "vault-note",
    "vault-identity-digest",
    "vault-hub-marker",
    "drift-verdict",
    "writing-gate-register",
    "persona-thesis-payload",
    "reconcile-gate-policy",
    "run-witness",
    "transport-seam",
    "vault-frontend",
    "textutil",
})

_WAVE_ONE_NAMES: frozenset[str] = frozenset({
    "atom", "capsule", "omission", "transform-receipt",
    "readiness-probe", "bootstrap-witness", "adapter",
})
assert SEAM_PINS.isdisjoint(_WAVE_ONE_NAMES), \
    "Wave 1 short-names leaked into SEAM_PINS"

_VERSION_RE = re.compile(r"^v(0|[1-9]\d*)(\.(0|[1-9]\d*))?$")
_KIND_TAG_RE = re.compile(r"^canon\.[a-z0-9-]+/v(0|[1-9]\d*)(\.(0|[1-9]\d*))?$")


@dataclass(frozen=True, slots=True)
class SchemaPin:
    """One version-tagged seam. `name` is a short-name inside `SEAM_PINS`;
    `version` matches `_VERSION_RE` and refuses `v0.0`; `kind_tag` has the
    shape `canon.<slug>/v<n>` and its version suffix has to equal `version`;
    `adr_ref` names the decision that fixed this pin."""

    name: str
    version: str
    kind_tag: str
    adr_ref: str

    def __post_init__(self) -> None:
        self._validate_name()
        self._validate_version()
        self._validate_kind_tag()
        self._validate_adr_ref()

    def _validate_name(self) -> None:
        if not isinstance(self.name, str):
            raise ValueError(f"SchemaPin.name must be str, got {type(self.name)!r}")
        if self.name not in SEAM_PINS:
            raise ValueError(
                f"SchemaPin.name {self.name!r} is not in SEAM_PINS; add it "
                f"there first (closed vocabulary, D-92)")

    def _validate_version(self) -> None:
        if not isinstance(self.version, str):
            raise ValueError(
                f"SchemaPin.version must be str, got {type(self.version)!r}")
        if not _VERSION_RE.match(self.version):
            raise ValueError(
                f"SchemaPin.version {self.version!r} fails semver-lite "
                f"regex {_VERSION_RE.pattern!r}")
        if self.version == "v0.0":
            raise ValueError(
                "SchemaPin.version 'v0.0' is refused; use 'v0' as the "
                "canonical zero (D-91)")

    def _validate_kind_tag(self) -> None:
        if not isinstance(self.kind_tag, str):
            raise ValueError(
                f"SchemaPin.kind_tag must be str, got {type(self.kind_tag)!r}")
        if not _KIND_TAG_RE.match(self.kind_tag):
            raise ValueError(
                f"SchemaPin.kind_tag {self.kind_tag!r} fails the "
                f"canon.<slug>/v<n> grammar")
        suffix = self.kind_tag.rsplit("/", 1)[1]
        if suffix != self.version:
            raise ValueError(
                f"SchemaPin.kind_tag version suffix {suffix!r} does not "
                f"equal SchemaPin.version {self.version!r}")

    def _validate_adr_ref(self) -> None:
        if not isinstance(self.adr_ref, str):
            raise ValueError(
                f"SchemaPin.adr_ref must be str, got {type(self.adr_ref)!r}")
        if not self.adr_ref:
            raise ValueError("SchemaPin.adr_ref must be non-empty")


PIN_RECORD = SchemaPin("record", "v1", "canon.record/v1", "F0 D-1")
PIN_BACKEND_SEAM = SchemaPin(
    "backend-seam", "v0", "canon.backend-seam/v0", "F1 D-9")
PIN_TEXTBLOCK_GRAMMAR = SchemaPin(
    "textblock-grammar", "v0", "canon.textblock/v0", "R0 D-13")
PIN_REGION_MARKER = SchemaPin(
    "region-marker", "v0", "canon.region-marker/v0", "R0 D-12")
PIN_FRONTMATTER = SchemaPin(
    "frontmatter", "v0", "canon.frontmatter/v0", "R2 D-28")
PIN_VAULT_NOTE = SchemaPin(
    "vault-note", "v0", "canon.vault-note/v0", "R2 D-24")
PIN_VAULT_IDENTITY_DIGEST = SchemaPin(
    "vault-identity-digest", "v1",
    "canon.vault-identity-digest/v1", "R2 D-29")
PIN_VAULT_HUB_MARKER = SchemaPin(
    "vault-hub-marker", "v1", "canon.vault-hub-marker/v1", "R2 D-34")
PIN_DRIFT_VERDICT = SchemaPin(
    "drift-verdict", "v0", "canon.drift-verdict/v0", "V2 D-41")
PIN_WRITING_GATE_REGISTER = SchemaPin(
    "writing-gate-register", "v0",
    "canon.writing-gate-register/v0", "V2 D-37")
PIN_PERSONA_THESIS_PAYLOAD = SchemaPin(
    "persona-thesis-payload", "v0",
    "canon.persona-thesis-payload/v0", "V3 D-44")
PIN_RECONCILE_GATE_POLICY = SchemaPin(
    "reconcile-gate-policy", "v0",
    "canon.reconcile-gate-policy/v0", "V4 D-59")
PIN_RUN_WITNESS = SchemaPin(
    "run-witness", "v0", "canon.run-witness/v0", "V4 D-64")
PIN_TRANSPORT_SEAM = SchemaPin(
    "transport-seam", "v0", "canon.transport-seam/v0", "M4.1 D-69")
PIN_VAULT_FRONTEND = SchemaPin(
    "vault-frontend", "v0", "canon.vault-frontend/v0", "M4.2 D-79")
PIN_TEXTUTIL = SchemaPin(
    "textutil", "v0", "canon.textutil/v0", "M4.1 helpers")

_DEFAULT_REGISTRY: dict[str, SchemaPin] = {
    p.name: p for p in (
        PIN_RECORD, PIN_BACKEND_SEAM, PIN_TEXTBLOCK_GRAMMAR,
        PIN_REGION_MARKER, PIN_FRONTMATTER, PIN_VAULT_NOTE,
        PIN_VAULT_IDENTITY_DIGEST, PIN_VAULT_HUB_MARKER,
        PIN_DRIFT_VERDICT, PIN_WRITING_GATE_REGISTER,
        PIN_PERSONA_THESIS_PAYLOAD, PIN_RECONCILE_GATE_POLICY,
        PIN_RUN_WITNESS, PIN_TRANSPORT_SEAM, PIN_VAULT_FRONTEND,
        PIN_TEXTUTIL,
    )
}
assert set(_DEFAULT_REGISTRY) == SEAM_PINS, \
    "SEAM_PINS and the PIN_* constants have drifted"

PIN_REGISTRY: MappingProxyType[str, SchemaPin] = MappingProxyType(
    _DEFAULT_REGISTRY)

_REGISTRY_OVERRIDE: contextvars.ContextVar[dict[str, SchemaPin] | None] = \
    contextvars.ContextVar("_REGISTRY_OVERRIDE", default=None)


def _active_registry() -> dict[str, SchemaPin] | MappingProxyType[str, SchemaPin]:
    override = _REGISTRY_OVERRIDE.get()
    return override if override is not None else PIN_REGISTRY


def pin_for(name: str) -> SchemaPin:
    """Look up a pin by short-name. Raises `UnknownPin` on miss."""
    reg = _active_registry()
    try:
        return reg[name]
    except KeyError:
        raise UnknownPin(
            f"pin_for({name!r}) failed: not in the active registry "
            f"(known: {sorted(reg)!r})") from None


def all_pins() -> tuple[SchemaPin, ...]:
    """Every pin in the active registry, sorted by name. Byte-stable across
    calls and independent of dict insertion order."""
    reg = _active_registry()
    return tuple(reg[name] for name in sorted(reg))


def is_compatible(theirs: SchemaPin, ours: SchemaPin) -> bool:
    """True iff two pins are byte-equal on name, version, and kind_tag.
    `adr_ref` is metadata and is not part of compatibility (a rewritten
    decision reference does not break the wire).

    Raises `MalformedPin` on a non-SchemaPin argument (a wiring fault caller
    would otherwise get `AttributeError` for)."""
    if not isinstance(theirs, SchemaPin) or not isinstance(ours, SchemaPin):
        raise MalformedPin(
            f"is_compatible requires SchemaPin arguments, got "
            f"{type(theirs)!r} and {type(ours)!r}")
    return (theirs.name == ours.name
            and theirs.version == ours.version
            and theirs.kind_tag == ours.kind_tag)


def describe(pin: SchemaPin, *, form: str = "human") -> str:
    """Human-readable or byte-stable JSON description of a pin. `form="human"`
    returns `<name> <version> (<kind_tag>) [<adr_ref>]`; `form="json"` returns
    `json.dumps(..., sort_keys=True)` over the same fields."""
    if not isinstance(pin, SchemaPin):
        raise MalformedPin(
            f"describe requires a SchemaPin, got {type(pin)!r}")
    if form == "human":
        return f"{pin.name} {pin.version} ({pin.kind_tag}) [{pin.adr_ref}]"
    if form == "json":
        return json.dumps({
            "name": pin.name, "version": pin.version,
            "kind_tag": pin.kind_tag, "adr_ref": pin.adr_ref,
        }, sort_keys=True)
    raise ValueError(f"describe(form={form!r}) is not one of 'human', 'json'")


def pin_from_schema_field(schema_str: str) -> SchemaPin:
    """Reverse lookup: find the pin whose `kind_tag` equals `schema_str`.
    Raises `MalformedPin` on a string that fails the kind_tag grammar and
    `UnknownPin` on a well-shaped kind_tag no registered pin matches."""
    if not isinstance(schema_str, str):
        raise MalformedPin(
            f"pin_from_schema_field requires str, got {type(schema_str)!r}")
    if not _KIND_TAG_RE.match(schema_str):
        raise MalformedPin(
            f"pin_from_schema_field({schema_str!r}) fails the "
            f"canon.<slug>/v<n> grammar")
    for pin in _active_registry().values():
        if pin.kind_tag == schema_str:
            return pin
    raise UnknownPin(
        f"pin_from_schema_field({schema_str!r}) found no pin with "
        f"matching kind_tag")


@contextmanager
def pin_registry_scope() -> Iterator[dict[str, SchemaPin]]:
    """Per-context registry override. Snapshots the current pin registry AND
    the migrator registry into fresh mutable dicts, yields the pin dict, and
    restores the prior context on exit (including on exception). Uses
    `contextvars.ContextVar`, so a test that installs a fake pin (or a fake
    migrator) does not affect a concurrent task in another context (D-96). Not
    thread-safe; per-context isolation only. The migrator snapshot is applied
    via a late import from `versions_migrate` to avoid a module-level cycle."""
    from canon import versions_migrate as _vm

    prior_pins = _REGISTRY_OVERRIDE.get()
    prior_migs = _vm._MIGRATORS_OVERRIDE.get()
    scratch_pins = dict(_active_registry())
    scratch_migs = dict(_vm._active_migrators())
    pin_token = _REGISTRY_OVERRIDE.set(scratch_pins)
    mig_token = _vm._MIGRATORS_OVERRIDE.set(scratch_migs)
    try:
        yield scratch_pins
    finally:
        _vm._MIGRATORS_OVERRIDE.reset(mig_token)
        _REGISTRY_OVERRIDE.reset(pin_token)
        assert _REGISTRY_OVERRIDE.get() is prior_pins
        assert _vm._MIGRATORS_OVERRIDE.get() is prior_migs
