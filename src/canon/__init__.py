"""canon -- a provider-neutral memory-bank + personality container.

F0 ships the record of record: one canonical envelope (schema.py), its
semantic validator (validator.py), and the per-scope override layering that
resolves the canon block set for a render target (layering.py). Storage
backends, renderers, verifiers, and migration legs are later phases; they all
aim at the envelope this package defines.
"""
from __future__ import annotations

from .layering import LayeringError, is_current, resolve_blocks
from .schema import (
    ADR_STATUSES,
    EPISODIC_LAYERS,
    KIND_ADR_DECISION,
    KIND_EPISODIC_MEMORY,
    KIND_PERSONALITY_BLOCK,
    KIND_RESEARCH_ARTIFACT_REF,
    KIND_SYNTHESIZED_PERSONA_L3,
    KINDS,
    PERSONA_LAYER,
    SCHEMA,
    SCOPE_GLOBAL,
    SCOPE_WORKSPACE,
    SCOPES,
    TEMPORAL_KINDS,
    Provenance,
    Record,
    Temporal,
    is_sha256,
)
from .validator import is_valid, validate_record

__all__ = [
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
]
