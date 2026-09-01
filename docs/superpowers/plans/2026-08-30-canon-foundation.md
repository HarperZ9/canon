# Canon Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the deterministic local Canon foundation: `canon.atom/v1`, `canon.capsule/v1`, descriptor schemas, validators, fixtures, generated `CANON.md`, and public exports.

**Architecture:** Add a stdlib-only schema layer above existing `canon.record/v1`. Keep existing record scopes unchanged; richer session/project/team/org semantics live in atoms and capsule metadata. Build everything with small frozen dataclasses, `to_dict`/`from_dict`, validator functions returning `list[str]`, deterministic canonical JSON, and pytest fixtures.

**Tech Stack:** Python 3.11+, standard library only, pytest for tests, existing `canon.record/v1` dataclasses and validators as inputs.

**Spec:** `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`

## Global Constraints

- Python `>=3.11`.
- Standard library only; no runtime dependencies.
- Do not edit audit reports, the pillar spec, release metadata, protected I0 artifacts, product code outside the task file list, or other plans.
- `canon.record/v1` remains stable with scopes `global` and `workspace`.
- Keep the canonical module name `canonical_json.py`.
- Keep the generated Markdown module name `canonmd.py`; do not rename it to `canon_md.py` or `markdown.py`.
- Keep the `CanonAtom` interfaces in this plan as the authoritative foundation contract.
- No CLI, MCP, `.canonpack`, import-write, undo, public release, package rename, or provider enforcement claim in this tranche.
- All schema fixtures land before green implementation.
- Deterministic bytes use `json-sorted-compact-lf`.
- Witnesses may include event time; deterministic capsule manifests must not depend on wall-clock time.
- A capsule cannot literally hash final bytes that contain their own hash. Compute identity from a canonical identity payload with `capsule_id` and `integrity.manifest_sha256` blanked, then write that digest into the final manifest.

---

## Verified Basis

- `CLAUDE.md` describes the current package as a provider-neutral memory-bank and personality container with shipped F0/F1/R0/R1/R2/V2/V3/V4 bands.
- `project-docs/SPEC-CANON-PILLAR-20260830.md` requires `CANON.md`, deterministic `canon.capsule/v1`, optional `.canonpack`, profiles, omission and lossy-transform receipts, ambient bootstrap witness, and retention gates.
- `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md` recommends shipping the deterministic local spine first: `canon.atom/v1`, `canon.capsule/v1`, generated `CANON.md`, readiness probe, bootstrap witness, adapter descriptors, and conformance fixtures.
- `project-docs/APPROVAL-CANON-CONTINUITY-20260830.md` records planning approval for the Canon Continuity Capsule architecture and its recommended defaults. It authorizes detailed implementation planning; implementation execution begins only through this validated plan's execution handoff, and the record is not a cryptographic signature or public release approval.
- `project-docs/audits/2026-08-30/CORE-SCHEMA-I0-AUDIT.md` states current mainline has `canon.record/v1` but no implemented `canon.capsule/v1`, `canon.atom/v1`, generated `CANON.md`, bootstrap witness, readiness probe schema, adapter-tier matrix, or capsule migration framework.
- Baseline command passed in `C:\dev\public\canon`: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider` -> `407 passed in 2.21s`.

## File Map

Create:

- `src/canon/canonical_json.py` - strict deterministic JSON bytes plus raw bytes/text/canonical sha256 references.
- `src/canon/atom.py` - `canon.atom/v1` dataclass, constants, JSON round trip, validator.
- `src/canon/omission.py` - `canon.omission/v1` descriptor and validator.
- `src/canon/transform.py` - `canon.transform-receipt/v1` descriptor and validator.
- `src/canon/adapter.py` - `canon.adapter/v1` descriptor, conservative built-in descriptors, lookup, and truthful integration-tier validator.
- `src/canon/readiness.py` - readiness probe/result descriptors and deterministic evaluator.
- `src/canon/witness.py` - bootstrap witness descriptor and validator.
- `src/canon/capsule.py` - capsule manifest dataclasses, builder, deterministic identity, validator, compile request/bundle convenience.
- `src/canon/canonmd.py` - generated `CANON.md` renderer, carrier parser, verifier.
- `tests/test_canonical_json.py`
- `tests/test_atom.py`
- `tests/test_descriptors.py`
- `tests/test_readiness.py`
- `tests/test_witness.py`
- `tests/test_capsule.py`
- `tests/test_canonmd.py`
- `tests/test_public_exports.py`
- `tests/fixtures/foundation/atom_active_goal.json`
- `tests/fixtures/foundation/atom_permission.json`
- `tests/fixtures/foundation/atom_prohibition.json`
- `tests/fixtures/foundation/atom_constraint.json`
- `tests/fixtures/foundation/atom_frontier_state.json`
- `tests/fixtures/foundation/atom_conflict.json`
- `tests/fixtures/foundation/atom_unknown.json`
- `tests/fixtures/foundation/omission_budget_noncritical.json`
- `tests/fixtures/foundation/transform_summary.json`
- `tests/fixtures/foundation/adapter_codex_cli_native_advisory.json`
- `tests/fixtures/foundation/adapter_mcp_readonly_guided.json`
- `tests/fixtures/foundation/adapter_a2a_artifact_guided.json`
- `tests/fixtures/foundation/readiness_probe.json`
- `tests/fixtures/foundation/bootstrap_witness_pass.json`
- `tests/fixtures/foundation/capsule_minimal_needle.json`
- `tests/fixtures/foundation/capsule_handoff_full.json`
- `tests/fixtures/foundation/CANON.expected.md`

Modify:

- `src/canon/__init__.py` - public exports for the new foundation API only.

Do not modify:

- `pyproject.toml`
- `README.md`
- `project-docs/**`
- `tests/fixtures/records/**`
- Any other plan file under `docs/superpowers/plans/**`

## Interfaces

### `src/canon/canonical_json.py`

Types:

- `JSONScalar = str | int | float | bool | None`
- `JSONValue = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]`

Constants:

- `CANONICALIZATION = "json-sorted-compact-lf"`

Classes:

- `class CanonicalJSONError(ValueError)`

Functions:

- `def canonical_json_text(value: object) -> str`
- `def canonical_json_bytes(value: object) -> bytes`
- `def sha256_bytes(data: bytes) -> str`
- `def sha256_text(text: str) -> str`
- `def canonical_sha256(value: object) -> str`
- `def is_sha256_ref(value: object) -> bool`

Rules:

- Reject non-string dict keys.
- Reject NaN and Infinity in any nested value.
- Emit compact sorted JSON with separators `(",", ":")`.
- Always append one final LF.
- Encode bytes as UTF-8.
- `sha256_bytes(data)` hashes caller-supplied bytes exactly as provided and returns the prefix `sha256:` followed by 64 lowercase hexadecimal characters.
- `sha256_text(text)` hashes `text.encode("utf-8")` exactly as provided and returns the prefix `sha256:` followed by 64 lowercase hexadecimal characters.
- `canonical_sha256(value)` hashes `canonical_json_bytes(value)` and returns the prefix `sha256:` followed by 64 lowercase hexadecimal characters.

### `src/canon/atom.py`

Constants:

- `ATOM_SCHEMA = "canon.atom/v1"`
- `ATOM_TYPES = ("instruction", "active-goal", "permission", "prohibition", "constraint", "decision", "frontier-state", "evidence-ref", "episodic-fact", "synthesized-persona", "conflict", "unknown", "omission", "lossy-transform", "bootstrap-probe", "bootstrap-witness", "adapter-capability")`
- `ATOM_LAYERS = ("session", "task", "project", "repo", "workspace", "personal", "team", "organization", "imported-history")`
- `ATOM_STATUSES = ("active", "retired", "superseded", "stale", "contradictory", "untrusted", "unknown", "blocked")`
- `ATOM_CLASSIFICATIONS = ("normative", "descriptive", "derived", "receipt")`

Class:

- `@dataclass(frozen=True, slots=True)`
- `class CanonAtom`

Fields:

- `type: str`
- `id: str`
- `layer: str`
- `scope_key: str`
- `precedence_rank: int`
- `status: str`
- `classification: str`
- `critical: bool`
- `value: dict`
- `source_refs: tuple[dict, ...] = ()`
- `source_span_refs: tuple[dict, ...] = ()`
- `freshness: dict = field(default_factory=dict)`
- `trust: dict = field(default_factory=dict)`
- `disclosure: dict = field(default_factory=dict)`
- `hashes: dict = field(default_factory=dict)`

Methods and functions:

- `def CanonAtom.to_dict(self) -> dict`
- `@classmethod def CanonAtom.from_dict(cls, d: dict) -> "CanonAtom"`
- `def CanonAtom.to_json(self) -> str`
- `@classmethod def CanonAtom.from_json(cls, text: str) -> "CanonAtom"`
- `def atom_key(atom: CanonAtom) -> tuple[str, str, str]`
- `def atoms_from_records(records: Iterable[Record]) -> list[CanonAtom]`
- `def load_atoms_jsonl(text: str) -> list[CanonAtom]`
- `def validate_atom(atom: CanonAtom) -> list[str]`
- `def is_valid_atom(atom: CanonAtom) -> bool`

Required atom JSON fields:

- `atom_schema`
- `type`
- `id`
- `layer`
- `scope_key`
- `precedence_rank`
- `status`
- `classification`
- `critical`
- `value`
- `source_refs`
- `source_span_refs`
- `freshness`
- `trust`
- `disclosure`
- `hashes`

Validation rules:

- `atom_schema` must equal `canon.atom/v1`.
- `type`, `layer`, `status`, and `classification` must be members of their constants.
- `id` and `scope_key` must be non-empty strings and may not contain bare CR or LF.
- `precedence_rank` must be a non-negative integer and not a bool.
- `critical` must be bool.
- `value`, `freshness`, `trust`, `disclosure`, and `hashes` must be dicts.
- `source_refs` and `source_span_refs` must be tuples of dicts after construction.
- Critical normative atoms of types `active-goal`, `permission`, `prohibition`, `constraint`, `frontier-state`, `conflict`, and `unknown` must have status `active`, `blocked`, `unknown`, `stale`, `contradictory`, or `untrusted`, not `retired` or `superseded`.
- `atom_key(atom)` returns `(atom.scope_key, atom.type, atom.id)`.
- `load_atoms_jsonl(text)` ignores blank lines, parses one canonical atom JSON object per non-blank line, validates each atom, and raises `ValueError` with a message beginning `line ` followed by the one-based source line number and `: ` when a parsed atom is invalid.
- `atoms_from_records(records)` maps valid `canon.record/v1` records into deterministic non-critical atoms, raises `ValueError` with `validate_record` problems for invalid records, and returns atoms sorted by `(precedence_rank, layer, type, id)`.
- `atoms_from_records(records)` maps record scope `workspace` to atom layer `workspace` and record scope `global` to atom layer `personal`, with scope keys `record-scope:workspace` and `record-scope:global`.
- `atoms_from_records(records)` maps record kinds as follows: `personality-block` -> `instruction` with classification `normative`; `adr-decision` -> `decision` with classification `descriptive`; `research-artifact-ref` -> `evidence-ref` with classification `descriptive`; `episodic-memory` -> `episodic-fact` with classification `descriptive`; `synthesized-persona-l3` -> `synthesized-persona` with classification `derived`.
- `atoms_from_records(records)` sets precedence rank `4` for workspace records and `6` for global records, status `superseded` when `record.temporal.valid_until is not None`, otherwise status `active`, freshness `{"state": "superseded", "valid_until": record.temporal.valid_until}` or `{"state": "current"}`, trust `{"label": "trusted-local", "harness": record.provenance.harness}`, disclosure `{"profile": "project-only"}`, hashes `{"record_sha256": canonical_sha256(record.to_dict())}`, and source refs `[{"ref": f"record:{record.scope}/{record.id}", "kind": record.kind, "source_hash": record.provenance.source_hash}]`.

### `src/canon/omission.py`

Constants:

- `OMISSION_SCHEMA = "canon.omission/v1"`
- `OMISSION_REASONS = ("budget", "secret", "unsupported-adapter", "policy", "source-unavailable", "parse-failed", "invalid", "duplicate", "stale")`
- `OMISSION_DECISIONS = ("omitted", "fail-build", "reference-only")`

Class:

- `@dataclass(frozen=True, slots=True)`
- `class Omission`

Fields:

- `reason: str`
- `count: int`
- `affected_ids: tuple[str, ...]`
- `affected_source_refs: tuple[str, ...]`
- `critical: bool`
- `decision: str`
- `does_not_prove: tuple[str, ...] = ()`

Methods and functions:

- `def Omission.to_dict(self) -> dict`
- `@classmethod def Omission.from_dict(cls, d: dict) -> "Omission"`
- `def Omission.to_json(self) -> str`
- `def validate_omission(omission: Omission) -> list[str]`

Validation rules:

- `schema` must equal `canon.omission/v1`.
- `reason` and `decision` must be members of their constants.
- `count` must be a non-negative integer and not a bool.
- `affected_ids`, `affected_source_refs`, and `does_not_prove` must contain only strings.
- `critical=True` with `decision="omitted"` is invalid.
- If `count != len(affected_ids)` and `affected_ids` is not empty, report a count mismatch.

### `src/canon/transform.py`

Constants:

- `TRANSFORM_SCHEMA = "canon.transform-receipt/v1"`
- `TRANSFORM_KINDS = ("summary", "compaction", "synthesis", "projection", "redaction", "migration")`
- `TRANSFORM_VERIFIERS = ("deterministic", "human", "model-assisted")`

Class:

- `@dataclass(frozen=True, slots=True)`
- `class TransformReceipt`

Fields:

- `transform: str`
- `method_id: str`
- `input_refs: tuple[str, ...]`
- `input_span_hash: str`
- `output_ref: str`
- `output_hash: str`
- `lossy: bool`
- `retained_critical_atom_ids: tuple[str, ...]`
- `omissions: tuple[Omission, ...] = ()`
- `verifier: str = "deterministic"`
- `does_not_prove: tuple[str, ...] = ()`

Methods and functions:

- `def TransformReceipt.to_dict(self) -> dict`
- `@classmethod def TransformReceipt.from_dict(cls, d: dict) -> "TransformReceipt"`
- `def TransformReceipt.to_json(self) -> str`
- `def validate_transform_receipt(receipt: TransformReceipt) -> list[str]`

Validation rules:

- `schema` must equal `canon.transform-receipt/v1`.
- `transform` and `verifier` must be members of their constants.
- `method_id` and `output_ref` must be non-empty strings.
- `input_refs`, `retained_critical_atom_ids`, and `does_not_prove` must contain only strings.
- `input_span_hash` and `output_hash` must satisfy `is_sha256_ref`.
- `lossy` must be bool.
- Nested omissions must pass `validate_omission`.

### `src/canon/adapter.py`

Constants:

- `ADAPTER_SCHEMA = "canon.adapter/v1"`
- `INTEGRATION_TIERS = ("enforced", "native-advisory", "guided", "unsupported")`

Class:

- `@dataclass(frozen=True, slots=True)`
- `class AdapterDescriptor`

Fields:

- `adapter_id: str`
- `display_name: str`
- `version: str`
- `integration_tier: str`
- `target_surfaces: tuple[str, ...]`
- `import_modes: tuple[str, ...]`
- `export_modes: tuple[str, ...]`
- `bootstrap: dict`
- `losses: tuple[dict, ...] = ()`
- `limits: dict = field(default_factory=dict)`
- `auth: dict = field(default_factory=dict)`
- `privacy: dict = field(default_factory=dict)`
- `evidence_refs: tuple[str, ...] = ()`
- `known_unknowns: tuple[str, ...] = ()`
- `last_verified: str | None = None`
- `owner: str | None = None`
- `retirement_trigger: str | None = None`

Methods and functions:

- `def AdapterDescriptor.to_dict(self) -> dict`
- `@classmethod def AdapterDescriptor.from_dict(cls, d: dict) -> "AdapterDescriptor"`
- `def AdapterDescriptor.to_json(self) -> str`
- `def builtin_descriptors() -> tuple[AdapterDescriptor, ...]`
- `def descriptor_for(adapter_id: str) -> AdapterDescriptor`
- `def assert_requested_tier_allowed(desc: AdapterDescriptor, requested_tier: str) -> None`
- `def validate_adapter_descriptor(adapter: AdapterDescriptor) -> list[str]`

Built-in descriptor rules:

- `builtin_descriptors()` returns descriptors in this exact order: `codex-cli`, `claude-code`, `chatgpt-app`, `claude-app`, `api-runner`, `local-runner`, `mcp-readonly`, `a2a-artifact`.
- Every built-in `adapter_id` is lowercase ASCII with words separated by hyphens.
- Every built-in uses `version="foundation-2026-08-30"`, `losses=()`, `limits={"max_context_tokens": None}`, `auth={"requires_login": False}`, `privacy={"default_disclosure": "project-only"}`, `evidence_refs=("project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md", "project-docs/APPROVAL-CANON-CONTINUITY-20260830.md")`, `last_verified="2026-08-30"`, `owner="canon"`, and `retirement_trigger="Revise when blocking startup proof fixtures or host capability evidence change."`.
- `codex-cli` and `claude-code` start at `integration_tier="native-advisory"`.
- `chatgpt-app`, `claude-app`, `api-runner`, `local-runner`, `mcp-readonly`, and `a2a-artifact` start at `integration_tier="guided"`.
- No built-in starts at `integration_tier="enforced"` and no built-in sets `bootstrap["can_block_before_work"]` to `True`.
- Built-in-specific fields are:

| adapter_id | display_name | integration_tier | target_surfaces | import_modes | export_modes | bootstrap | known_unknowns |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `codex-cli` | `Codex CLI` | `native-advisory` | `("CANON.md", "AGENTS.md")` | `("file", "paste")` | `("file", "stdout")` | `{"can_block_before_work": False, "mode": "native-context-file"}` | `("Native context can advise the run; this foundation descriptor does not assert a universal hard block before work.",)` |
| `claude-code` | `Claude Code` | `native-advisory` | `("CANON.md", "CLAUDE.md")` | `("file", "paste")` | `("file", "stdout")` | `{"can_block_before_work": False, "mode": "native-context-file"}` | `("Native context can advise the run; this foundation descriptor does not assert a universal hard block before work.",)` |
| `chatgpt-app` | `ChatGPT App` | `guided` | `("CANON.md", "chat-message")` | `("paste", "file")` | `("chat", "file")` | `{"can_block_before_work": False, "mode": "guided-user-message"}` | `("Closed app bootstrap is guided until blocking startup fixtures prove promotion.",)` |
| `claude-app` | `Claude App` | `guided` | `("CANON.md", "chat-message")` | `("paste", "file")` | `("chat", "file")` | `{"can_block_before_work": False, "mode": "guided-user-message"}` | `("Closed app bootstrap is guided until blocking startup fixtures prove promotion.",)` |
| `api-runner` | `API Runner` | `guided` | `("CANON.md", "json")` | `("file", "json")` | `("json", "stdout")` | `{"can_block_before_work": False, "mode": "caller-managed"}` | `("API runner enforcement depends on caller wiring and remains guided until blocking fixtures prove promotion.",)` |
| `local-runner` | `Local Runner` | `guided` | `("CANON.md", "json")` | `("file", "json")` | `("json", "stdout")` | `{"can_block_before_work": False, "mode": "caller-managed"}` | `("Local runner enforcement depends on harness wiring and remains guided until blocking fixtures prove promotion.",)` |
| `mcp-readonly` | `MCP Readonly` | `guided` | `("CANON.md", "mcp-resource")` | `("file", "resource")` | `("resource", "stdout")` | `{"can_block_before_work": False, "mode": "readonly-resource-handoff"}` | `("MCP read-only resources can expose context; this foundation descriptor does not assert tool-call blocking before work.",)` |
| `a2a-artifact` | `A2A Artifact` | `guided` | `("CANON.md", "artifact")` | `("file", "artifact")` | `("artifact", "stdout")` | `{"can_block_before_work": False, "mode": "artifact-handoff"}` | `("Artifact handoff can carry context; this foundation descriptor does not assert host-level blocking before work.",)` |

- `descriptor_for(adapter_id)` returns the matching built-in descriptor for an exact lowercase id and raises `KeyError(adapter_id)` for an unknown or non-lowercase id.
- `assert_requested_tier_allowed(desc, requested_tier)` raises `ValueError` when `requested_tier` is not in `INTEGRATION_TIERS`.
- `assert_requested_tier_allowed(desc, requested_tier)` uses tier strength `unsupported=0`, `guided=1`, `native-advisory=2`, `enforced=3` and raises `ValueError` when the requested tier is stronger than `desc.integration_tier`.
- The later Adapter/UX plan may extend the descriptor set and update proof status, but promotion above these initial tiers requires blocking proof fixtures outside this foundation tranche.

Validation rules:

- `schema` must equal `canon.adapter/v1`.
- `adapter_id`, `display_name`, `version`, and `integration_tier` must be non-empty strings.
- `integration_tier` must be a member of `INTEGRATION_TIERS`.
- `target_surfaces`, `import_modes`, `export_modes`, `evidence_refs`, and `known_unknowns` must contain only strings.
- `bootstrap`, `limits`, `auth`, and `privacy` must be dicts.
- `losses` must contain only dicts.
- `last_verified`, `owner`, and `retirement_trigger` must be strings or `None`.
- `integration_tier="enforced"` requires `bootstrap["can_block_before_work"] is True` and at least one `evidence_refs` entry.

### `src/canon/readiness.py`

Constants:

- `READINESS_PROBE_SCHEMA = "canon.readiness-probe/v1"`
- `READINESS_RESULT_SCHEMA = "canon.readiness-result/v1"`
- `READINESS_VERDICTS = ("pass", "fail", "blocked", "unknown")`
- `CRITICAL_SET_KEYS = ("active_goal_ids", "permission_ids", "prohibition_ids", "constraint_ids", "frontier_state_ids", "unresolved_conflict_ids", "unknown_ids")`

Classes:

- `@dataclass(frozen=True, slots=True) class ReadinessProbe`
- `@dataclass(frozen=True, slots=True) class ReadinessResult`

`ReadinessProbe` fields:

- `probe_id: str`
- `capsule_id: str`
- `target: dict`
- `critical_sets: dict`
- `challenge: dict`
- `checker: dict`

`ReadinessResult` fields:

- `probe_id: str`
- `capsule_id: str`
- `verdict: str`
- `reported: dict`
- `missing_ids: tuple[str, ...]`
- `mismatched_ids: tuple[str, ...]`
- `response_hash: str`
- `does_not_prove: tuple[str, ...] = ()`

Methods and functions:

- `def ReadinessProbe.to_dict(self) -> dict`
- `@classmethod def ReadinessProbe.from_dict(cls, d: dict) -> "ReadinessProbe"`
- `def ReadinessResult.to_dict(self) -> dict`
- `@classmethod def ReadinessResult.from_dict(cls, d: dict) -> "ReadinessResult"`
- `def validate_readiness_probe(probe: ReadinessProbe) -> list[str]`
- `def validate_readiness_result(result: ReadinessResult) -> list[str]`
- `def evaluate_readiness_response(probe: ReadinessProbe, response: Mapping[str, object]) -> ReadinessResult`

Readiness pass rule:

- Every critical id in `probe.critical_sets` appears in the corresponding response list.
- `response` may include a `statuses` dict. If present, any status for a critical id must match the status listed in `response["expected_statuses"]` when that key is present.
- No raw secret value is inspected or required.
- Result verdict is `pass` only when `missing_ids` and `mismatched_ids` are empty.

### `src/canon/witness.py`

Constants:

- `BOOTSTRAP_WITNESS_SCHEMA = "canon.bootstrap-witness/v1"`
- `BOOTSTRAP_CHECK_NAMES = ("freshness", "conflicts", "secrets", "budget", "reachability", "readiness")`
- `BOOTSTRAP_CHECK_VERDICTS = ("pass", "fail", "warn", "blocked", "unknown")`

Classes:

- `@dataclass(frozen=True, slots=True) class BootstrapCheck`
- `@dataclass(frozen=True, slots=True) class BootstrapWitness`

`BootstrapCheck` fields:

- `name: str`
- `verdict: str`
- `evidence_refs: tuple[str, ...] = ()`
- `details: dict = field(default_factory=dict)`

`BootstrapWitness` fields:

- `run_id: str`
- `capsule_id: str`
- `capsule_manifest_sha256: str`
- `source_state: dict`
- `target: dict`
- `integration_tier_claimed: str`
- `host_enforcement_observed: bool`
- `started_at: str`
- `checks: tuple[BootstrapCheck, ...]`
- `omissions: tuple[Omission, ...]`
- `lossy_transforms: tuple[TransformReceipt, ...]`
- `readiness_result: ReadinessResult`
- `does_not_prove: tuple[str, ...] = ()`

Methods and functions:

- `def BootstrapCheck.to_dict(self) -> dict`
- `@classmethod def BootstrapCheck.from_dict(cls, d: dict) -> "BootstrapCheck"`
- `def BootstrapWitness.to_dict(self) -> dict`
- `@classmethod def BootstrapWitness.from_dict(cls, d: dict) -> "BootstrapWitness"`
- `def BootstrapWitness.to_json(self) -> str`
- `def validate_bootstrap_witness(witness: BootstrapWitness) -> list[str]`

Validation rules:

- `schema` must equal `canon.bootstrap-witness/v1`.
- `run_id`, `capsule_id`, `capsule_manifest_sha256`, and `started_at` must be non-empty strings.
- Digest fields must satisfy `is_sha256_ref`.
- `integration_tier_claimed` must be one of `INTEGRATION_TIERS`.
- `host_enforcement_observed` must be bool.
- Checks must use known names and verdicts.
- Nested omissions, transforms, and readiness result must validate.
- `integration_tier_claimed="enforced"` and `host_enforcement_observed=True` requires readiness verdict `pass` and no failed checks.

### `src/canon/capsule.py`

Constants:

- `CAPSULE_SCHEMA = "canon.capsule/v1"`
- `CAPSULE_PROFILES = ("needle", "handoff", "archive", "custom")`
- `CANONICALIZATION = "json-sorted-compact-lf"`

Classes:

- `class CapsuleError(ValueError)`
- `class CapsuleBuildError(CapsuleError)`
- `@dataclass(frozen=True, slots=True) class CapsuleTarget`
- `@dataclass(frozen=True, slots=True) class SourceState`
- `@dataclass(frozen=True, slots=True) class Compatibility`
- `@dataclass(frozen=True, slots=True) class Budget`
- `@dataclass(frozen=True, slots=True) class Integrity`
- `@dataclass(frozen=True, slots=True) class Capsule`
- `@dataclass(frozen=True, slots=True) class CapsuleCompileRequest`
- `@dataclass(frozen=True, slots=True) class CapsuleBundle`

`CapsuleTarget` fields:

- `adapter: str`
- `surface: str`
- `integration_tier: str`
- `host_enforcement_observed: bool = False`

`SourceState` fields:

- `records_digest: str`
- `inventory_digest: str | None = None`
- `context_envelope_digest: str | None = None`
- `mneme_snapshot_digest: str | None = None`
- `relay_checkpoint: str | None = None`
- `worktree_digest: str | None = None`

`Compatibility` fields:

- `record_schema_min: str = "canon.record/v1"`
- `capsule_schema: str = CAPSULE_SCHEMA`
- `requires_features: tuple[str, ...] = ()`

`Budget` fields:

- `profile: str`
- `max_tokens: int`
- `estimated_tokens: int`
- `estimator: str`
- `policy: str = "critical-atoms-lossless"`

`Integrity` fields:

- `canonicalization: str`
- `manifest_sha256: str`

`Capsule` fields:

- `capsule_id: str`
- `profile: str`
- `target: CapsuleTarget`
- `source_state: SourceState`
- `compatibility: Compatibility`
- `budget: Budget`
- `layers: tuple[str, ...]`
- `atoms: tuple[CanonAtom, ...]`
- `records: tuple[Record, ...]`
- `conflicts: tuple[CanonAtom, ...]`
- `unknowns: tuple[CanonAtom, ...]`
- `omissions: tuple[Omission, ...]`
- `lossy_transforms: tuple[TransformReceipt, ...]`
- `freshness: tuple[dict, ...]`
- `integrity: Integrity`
- `receipts: tuple[dict, ...]`
- `does_not_prove: tuple[str, ...]`

`CapsuleCompileRequest` fields:

- `profile: str`
- `target: CapsuleTarget`
- `source_state: SourceState`
- `budget: Budget`
- `atoms: tuple[CanonAtom, ...] = ()`
- `records: tuple[Record, ...] = ()`
- `omissions: tuple[Omission, ...] = ()`
- `lossy_transforms: tuple[TransformReceipt, ...] = ()`
- `receipts: tuple[dict, ...] = ()`
- `does_not_prove: tuple[str, ...] = ()`
- `required_atom_ids: tuple[str, ...] = ()`
- `readiness_probe_id: str = "readiness-default"`
- `readiness_target: dict | None = None`

`CapsuleBundle` fields:

- `capsule: Capsule`
- `manifest_bytes: bytes`
- `canon_md: str`
- `readiness_probe: ReadinessProbe`

Methods and functions:

- `def Capsule.to_dict(self, *, identity: bool = True) -> dict`
- `@classmethod def Capsule.from_dict(cls, d: dict) -> "Capsule"`
- `def Capsule.to_json(self) -> str`
- `def capsule_identity_dict(capsule: Capsule) -> dict`
- `def capsule_digest(capsule: Capsule) -> str`
- `def capsule_bytes(capsule: Capsule) -> bytes`
- `def validate_capsule(capsule: Capsule) -> list[str]`
- `def build_capsule(*, profile: str, target: CapsuleTarget, source_state: SourceState, budget: Budget, atoms: Iterable[CanonAtom], records: Iterable[Record] = (), omissions: Iterable[Omission] = (), lossy_transforms: Iterable[TransformReceipt] = (), receipts: Iterable[dict] = (), does_not_prove: Iterable[str] = (), required_atom_ids: Iterable[str] = ()) -> Capsule`
- `def compile_capsule(request: CapsuleCompileRequest) -> CapsuleBundle`

Build rules:

- Sort atoms by `(precedence_rank, layer, type, id)`.
- Sort records by `(scope, id, kind)`.
- Sort omissions by `(reason, critical, decision, affected_ids)`.
- Sort transforms by `(transform, method_id, output_ref)`.
- Derive `layers` from sorted atom layers, preserving first occurrence after sorting.
- Derive `conflicts` from atoms with type `conflict`.
- Derive `unknowns` from atoms with type `unknown`.
- Derive `freshness` from atoms whose `freshness` dict is non-empty.
- Fail with `CapsuleBuildError` when any `required_atom_ids` is missing.
- Fail with `CapsuleBuildError` when a required atom exists but is not critical.
- Compute `capsule_id` and `integrity.manifest_sha256` from `capsule_identity_dict`.
- `compile_capsule(request)` calls `build_capsule()` with the request fields, builds `manifest_bytes` with `capsule_bytes(capsule)`, builds `canon_md` with `render_canon_md(capsule)`, and builds a `ReadinessProbe` from the capsule's critical atoms.
- `compile_capsule(request)` imports `render_canon_md` inside the function to avoid a module-import cycle between `capsule.py` and `canonmd.py`.
- The generated readiness probe uses `request.readiness_probe_id`, the final `capsule.capsule_id`, `request.readiness_target or capsule.target.to_dict()`, the fixed critical-set keys from `readiness.py`, challenge `{"format": "json", "required_fields": list(CRITICAL_SET_KEYS)}`, and checker `{"method": "exact-id-set-and-status-match", "pass_threshold": "all-critical"}`.
- The generated readiness probe fills ids from critical atoms by type: `active-goal` -> `active_goal_ids`, `permission` -> `permission_ids`, `prohibition` -> `prohibition_ids`, `constraint` -> `constraint_ids`, `frontier-state` -> `frontier_state_ids`, `conflict` -> `unresolved_conflict_ids`, and `unknown` -> `unknown_ids`.

### `src/canon/canonmd.py`

Constants:

- `CANON_MD_SECTIONS = ("Capsule identity", "Target and integration tier", "Freshness, trust, and unknowns", "Active goals", "Authority, permissions, prohibitions, and constraints", "Current frontier and working state", "Decisions and rationale", "Conflicts requiring resolution", "Canonical instructions", "Evidence references", "Omissions", "Lossy transforms", "Bootstrap readiness probe", "Does-not-prove")`

Class:

- `class CanonMdError(ValueError)`

Functions:

- `def render_canon_md(capsule: Capsule, *, include_machine_carrier: bool = True) -> str`
- `def parse_canon_md_carrier(text: str) -> dict`
- `def verify_canon_md(text: str, capsule: Capsule | None = None) -> list[str]`

Carrier rule:

```text
<!-- canon:capsule/v1 digest={capsule.capsule_id} payload={base64.urlsafe_b64encode(capsule_bytes(capsule)).decode("ascii").rstrip("=")} -->
```

Rendering rules:

- The document starts with `# CANON`.
- The carrier comment appears immediately after the title when `include_machine_carrier=True`.
- Every section in `CANON_MD_SECTIONS` appears once, in order, using a Markdown level-2 heading whose text is the section string.
- Render line endings as LF and exactly one trailing LF.
- Include capsule id, target tier, unknowns, omissions, lossy transforms, readiness probe summary when present, and does-not-prove text.
- Visible prose is reviewable; the capsule carrier is authoritative.

## Foundation Fixture Content

Create every JSON fixture with sorted keys and a final LF. These fixtures are intentionally small and public-safe.

`tests/fixtures/foundation/atom_active_goal.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"normative","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"current"},"hashes":{"value_sha256":"sha256:1111111111111111111111111111111111111111111111111111111111111111"},"id":"goal-foundation","layer":"session","precedence_rank":0,"scope_key":"workspace:canon","source_refs":[{"ref":"record:workspace/adr-0001-container-name"}],"source_span_refs":[],"status":"active","trust":{"label":"trusted-local"},"type":"active-goal","value":{"summary":"Implement the Canon foundation schema spine."}}
```

`tests/fixtures/foundation/atom_permission.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"normative","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"current"},"hashes":{},"id":"perm-plan-only","layer":"session","precedence_rank":1,"scope_key":"workspace:canon","source_refs":[],"source_span_refs":[],"status":"active","trust":{"label":"trusted-local"},"type":"permission","value":{"allows":["edit requested plan file","read public Canon source"]}}
```

`tests/fixtures/foundation/atom_prohibition.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"normative","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"current"},"hashes":{},"id":"prohibit-product-code","layer":"session","precedence_rank":1,"scope_key":"workspace:canon","source_refs":[],"source_span_refs":[],"status":"active","trust":{"label":"trusted-local"},"type":"prohibition","value":{"forbids":["edit product code outside task scope","copy secrets into fixtures"]}}
```

`tests/fixtures/foundation/atom_constraint.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"normative","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"current"},"hashes":{},"id":"constraint-stdlib","layer":"project","precedence_rank":3,"scope_key":"repo:canon","source_refs":[{"ref":"CLAUDE.md"}],"source_span_refs":[],"status":"active","trust":{"label":"trusted-local"},"type":"constraint","value":{"requires":["Python 3.11+","standard library runtime only"]}}
```

`tests/fixtures/foundation/atom_frontier_state.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"descriptive","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"current"},"hashes":{},"id":"frontier-foundation-next","layer":"session","precedence_rank":0,"scope_key":"workspace:canon","source_refs":[{"ref":"project-docs/APPROVAL-CANON-CONTINUITY-20260830.md"}],"source_span_refs":[],"status":"active","trust":{"label":"trusted-local"},"type":"frontier-state","value":{"current_state":"Architecture planning approval is recorded; implementation begins only through this validated plan's execution handoff.","first_safe_action":"Write failing canonical JSON tests."}}
```

`tests/fixtures/foundation/atom_conflict.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"normative","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"contradictory"},"hashes":{},"id":"conflict-enforced-tier","layer":"project","precedence_rank":2,"scope_key":"repo:canon","source_refs":[],"source_span_refs":[],"status":"contradictory","trust":{"label":"trusted-local"},"type":"conflict","value":{"summary":"A host cannot be labeled enforced without blocking evidence.","resolution":"pending"}}
```

`tests/fixtures/foundation/atom_unknown.json`:

```json
{"atom_schema":"canon.atom/v1","classification":"descriptive","critical":true,"disclosure":{"profile":"project-only"},"freshness":{"state":"unknown"},"hashes":{},"id":"unknown-closed-app-hooks","layer":"project","precedence_rank":6,"scope_key":"repo:canon","source_refs":[],"source_span_refs":[],"status":"unknown","trust":{"label":"unsigned-local"},"type":"unknown","value":{"question":"Exact strongest integration tier for closed app hosts remains unverified."}}
```

`tests/fixtures/foundation/omission_budget_noncritical.json`:

```json
{"affected_ids":["fact-noncritical-1"],"affected_source_refs":["record:workspace/fact-noncritical-1"],"count":1,"critical":false,"decision":"omitted","does_not_prove":["This does not prove omitted facts were irrelevant."],"reason":"budget","schema":"canon.omission/v1"}
```

`tests/fixtures/foundation/transform_summary.json`:

```json
{"does_not_prove":["This receipt does not prove the summary is complete."],"input_refs":["record:workspace/mem-000123"],"input_span_hash":"sha256:2222222222222222222222222222222222222222222222222222222222222222","lossy":true,"method_id":"deterministic-summary-v1","omissions":[],"output_hash":"sha256:3333333333333333333333333333333333333333333333333333333333333333","output_ref":"atom:episodic-fact-1","retained_critical_atom_ids":["goal-foundation"],"schema":"canon.transform-receipt/v1","transform":"summary","verifier":"deterministic"}
```

`tests/fixtures/foundation/adapter_codex_cli_native_advisory.json`:

```json
{"adapter_id":"codex-cli","auth":{"requires_login":false},"bootstrap":{"can_block_before_work":false,"mode":"native-context-file"},"display_name":"Codex CLI","evidence_refs":["project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md","project-docs/APPROVAL-CANON-CONTINUITY-20260830.md"],"export_modes":["file","stdout"],"import_modes":["file","paste"],"integration_tier":"native-advisory","known_unknowns":["Native context can advise the run; this foundation descriptor does not assert a universal hard block before work."],"last_verified":"2026-08-30","limits":{"max_context_tokens":null},"losses":[],"owner":"canon","privacy":{"default_disclosure":"project-only"},"retirement_trigger":"Revise when blocking startup proof fixtures or host capability evidence change.","schema":"canon.adapter/v1","target_surfaces":["CANON.md","AGENTS.md"],"version":"foundation-2026-08-30"}
```

`tests/fixtures/foundation/adapter_mcp_readonly_guided.json`:

```json
{"adapter_id":"mcp-readonly","auth":{"requires_login":false},"bootstrap":{"can_block_before_work":false,"mode":"readonly-resource-handoff"},"display_name":"MCP Readonly","evidence_refs":["project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md","project-docs/APPROVAL-CANON-CONTINUITY-20260830.md"],"export_modes":["resource","stdout"],"import_modes":["file","resource"],"integration_tier":"guided","known_unknowns":["MCP read-only resources can expose context; this foundation descriptor does not assert tool-call blocking before work."],"last_verified":"2026-08-30","limits":{"max_context_tokens":null},"losses":[],"owner":"canon","privacy":{"default_disclosure":"project-only"},"retirement_trigger":"Revise when blocking startup proof fixtures or host capability evidence change.","schema":"canon.adapter/v1","target_surfaces":["CANON.md","mcp-resource"],"version":"foundation-2026-08-30"}
```

`tests/fixtures/foundation/adapter_a2a_artifact_guided.json`:

```json
{"adapter_id":"a2a-artifact","auth":{"requires_login":false},"bootstrap":{"can_block_before_work":false,"mode":"artifact-handoff"},"display_name":"A2A Artifact","evidence_refs":["project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md","project-docs/APPROVAL-CANON-CONTINUITY-20260830.md"],"export_modes":["artifact","stdout"],"import_modes":["file","artifact"],"integration_tier":"guided","known_unknowns":["Artifact handoff can carry context; this foundation descriptor does not assert host-level blocking before work."],"last_verified":"2026-08-30","limits":{"max_context_tokens":null},"losses":[],"owner":"canon","privacy":{"default_disclosure":"project-only"},"retirement_trigger":"Revise when blocking startup proof fixtures or host capability evidence change.","schema":"canon.adapter/v1","target_surfaces":["CANON.md","artifact"],"version":"foundation-2026-08-30"}
```

`tests/fixtures/foundation/readiness_probe.json`:

```json
{"capsule_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","challenge":{"format":"json","required_fields":["active_goal_ids","permission_ids","prohibition_ids","constraint_ids","frontier_state_ids","unresolved_conflict_ids","unknown_ids"]},"checker":{"method":"exact-id-set-and-status-match","pass_threshold":"all-critical"},"critical_sets":{"active_goal_ids":["goal-foundation"],"constraint_ids":["constraint-stdlib"],"frontier_state_ids":["frontier-foundation-next"],"permission_ids":["perm-plan-only"],"prohibition_ids":["prohibit-product-code"],"unknown_ids":["unknown-closed-app-hooks"],"unresolved_conflict_ids":["conflict-enforced-tier"]},"probe_id":"probe-foundation-1","schema":"canon.readiness-probe/v1","target":{"adapter":"codex-cli","surface":"CANON.md"}}
```

`tests/fixtures/foundation/bootstrap_witness_pass.json`:

```json
{"capsule_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","capsule_manifest_sha256":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","checks":[{"details":{},"evidence_refs":["capsule:sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],"name":"readiness","verdict":"pass"}],"does_not_prove":["This witness does not prove host-level blocking for native-advisory adapters."],"host_enforcement_observed":false,"integration_tier_claimed":"native-advisory","lossy_transforms":[],"omissions":[],"readiness_result":{"capsule_id":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","does_not_prove":[],"mismatched_ids":[],"missing_ids":[],"probe_id":"probe-foundation-1","reported":{"active_goal_ids":["goal-foundation"]},"response_hash":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","schema":"canon.readiness-result/v1","verdict":"pass"},"run_id":"run-foundation-1","schema":"canon.bootstrap-witness/v1","source_state":{"records_digest":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"},"started_at":"2026-08-30T00:00:00Z","target":{"adapter":"codex-cli","surface":"CANON.md"}}
```

Capsule fixtures should be generated from `build_capsule` after T7 goes green, then committed as stable fixture bytes. `CANON.expected.md` should be generated from `render_canon_md` after T8 goes green, reviewed once, and then used as a drift fixture. Do not hand-edit generated expected bytes after review.

## Dependency Order

| Task | Depends On | Parallel Group | Handoff |
|---|---|---:|---|
| T1 canonical JSON | none | A | `canonical_json_text`, `canonical_json_bytes`, `sha256_bytes`, `sha256_text`, `canonical_sha256`, `is_sha256_ref` |
| T2 atom schema | T1 | B | `CanonAtom`, atom constants, `atom_key`, `atoms_from_records`, `load_atoms_jsonl`, atom fixtures |
| T3 omission and transform receipts | T1, T2 | C | receipt dataclasses and validators |
| T4 adapter descriptor | T1 | C | adapter descriptor, built-in lookup, and requested-tier guard |
| T5 readiness probe/result | T1, T2 | D | readiness descriptor and evaluator |
| T6 bootstrap witness | T3, T4, T5 | E | event witness descriptor and validator |
| T7 capsule manifest/compiler | T2, T3, T4, T5 | F | `Capsule`, `build_capsule`, deterministic bytes, final compile request/bundle interfaces |
| T8 generated `CANON.md` and compile convenience | T7 | G | renderer, carrier parser, verifier, `compile_capsule` bundle |
| T9 public exports | T1-T8 | H | package public API exports |

### Task 1: Canonical JSON

**Files:**

- Create: `src/canon/canonical_json.py`
- Create: `tests/test_canonical_json.py`

**Interfaces:**

- Consumes: only Python stdlib.
- Produces: `canonical_json_text(value: object) -> str`, `canonical_json_bytes(value: object) -> bytes`, `sha256_bytes(data: bytes) -> str`, `sha256_text(text: str) -> str`, `canonical_sha256(value: object) -> str`, `is_sha256_ref(value: object) -> bool`, `CanonicalJSONError`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_canonical_json.py`:

```python
from __future__ import annotations

import hashlib

import pytest

from canon.canonical_json import (
    CANONICALIZATION,
    CanonicalJSONError,
    canonical_json_bytes,
    canonical_json_text,
    canonical_sha256,
    is_sha256_ref,
    sha256_bytes,
    sha256_text,
)


def test_canonical_json_is_compact_sorted_and_lf_terminated():
    got = canonical_json_text({"b": 2, "a": {"d": 4, "c": 3}})
    assert got == '{"a":{"c":3,"d":4},"b":2}\n'
    assert CANONICALIZATION == "json-sorted-compact-lf"


def test_canonical_json_bytes_are_utf8_text_bytes():
    got = canonical_json_bytes({"word": "canon"})
    assert got == b'{"word":"canon"}\n'


def test_canonical_sha256_uses_canonical_bytes():
    payload = {"a": 1}
    expected = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    assert canonical_sha256(payload) == "sha256:" + expected


def test_raw_sha256_helpers_hash_exact_inputs():
    assert sha256_bytes(b"canon\n") == "sha256:" + hashlib.sha256(b"canon\n").hexdigest()
    assert sha256_text("canon\n") == "sha256:" + hashlib.sha256("canon\n".encode("utf-8")).hexdigest()
    assert sha256_text("canon") != sha256_text("canon\n")


def test_sha256_ref_validator_requires_prefixed_lowercase_digest():
    assert is_sha256_ref("sha256:" + "a" * 64)
    assert not is_sha256_ref("a" * 64)
    assert not is_sha256_ref("sha256:" + "A" * 64)
    assert not is_sha256_ref("sha256:deadbeef")


def test_canonical_json_rejects_non_string_keys_and_nan():
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({1: "bad"})
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({"n": float("nan")})
    with pytest.raises(CanonicalJSONError):
        canonical_json_text({"n": float("inf")})
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_canonical_json.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.canonical_json'`.

- [ ] **Step 3: Implement the minimal module**

Create `src/canon/canonical_json.py` with:

- the constants, types, exception, and functions from the Interfaces section;
- recursive validation of dict keys and nested float values before dumping;
- `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"`;
- `sha256_bytes(data)` as the one raw byte hash primitive;
- `sha256_text(text)` as `sha256_bytes(text.encode("utf-8"))`;
- `canonical_sha256(value)` as `sha256_bytes(canonical_json_bytes(value))`.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_canonical_json.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "sha256_bytes|sha256_text|canonical_sha256" src/canon/canonical_json.py tests/test_canonical_json.py
rg -n "import (yaml|pydantic|jsonschema|requests|click|typer|rich)|from (yaml|pydantic|jsonschema|requests|click|typer|rich)" src/canon/canonical_json.py tests/test_canonical_json.py
```

Expected: first command finds the three hash helper names; second command finds no matches.

### Task 2: `canon.atom/v1` and Atom Helpers

**Files:**

- Create: `src/canon/atom.py`
- Create: `tests/test_atom.py`
- Create: `tests/fixtures/foundation/atom_active_goal.json`
- Create: `tests/fixtures/foundation/atom_permission.json`
- Create: `tests/fixtures/foundation/atom_prohibition.json`
- Create: `tests/fixtures/foundation/atom_constraint.json`
- Create: `tests/fixtures/foundation/atom_frontier_state.json`
- Create: `tests/fixtures/foundation/atom_conflict.json`
- Create: `tests/fixtures/foundation/atom_unknown.json`

**Interfaces:**

- Consumes: `canonical_json_text`.
- Produces: `CanonAtom`, atom constants, `atom_key(atom: CanonAtom) -> tuple[str, str, str]`, `atoms_from_records(records: Iterable[Record]) -> list[CanonAtom]`, `load_atoms_jsonl(text: str) -> list[CanonAtom]`, `validate_atom(atom: CanonAtom) -> list[str]`, `is_valid_atom(atom: CanonAtom) -> bool`.

- [ ] **Step 1: Write the failing tests and fixtures**

Create fixture files exactly as listed in Foundation Fixture Content.

Create `tests/test_atom.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.atom import (
    ATOM_SCHEMA,
    CanonAtom,
    atom_key,
    atoms_from_records,
    is_valid_atom,
    load_atoms_jsonl,
    validate_atom,
)

from ._helpers import RECORD_FILES, load_record

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"
ATOM_FIXTURES = (
    "atom_active_goal.json",
    "atom_permission.json",
    "atom_prohibition.json",
    "atom_constraint.json",
    "atom_frontier_state.json",
    "atom_conflict.json",
    "atom_unknown.json",
)


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ATOM_FIXTURES)
def test_atom_fixture_roundtrips_field_identical(name: str):
    original = load_fixture(name)
    atom = CanonAtom.from_dict(original)
    assert atom.to_dict() == original
    assert atom.to_json().endswith("\n")
    assert validate_atom(atom) == []
    assert is_valid_atom(atom)


def test_atom_schema_field_is_written():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    assert atom.to_dict()["atom_schema"] == ATOM_SCHEMA


def test_critical_normative_goal_requires_active_or_blocked_status():
    atom = CanonAtom(
        type="active-goal",
        id="goal-1",
        layer="session",
        scope_key="workspace",
        precedence_rank=0,
        status="retired",
        classification="normative",
        critical=True,
        value={"summary": "finish foundation plan"},
    )
    assert any("critical" in p and "status" in p for p in validate_atom(atom))


def test_atom_validator_reports_multiple_envelope_problems():
    atom = CanonAtom(
        type="bogus",
        id="",
        layer="bad",
        scope_key="",
        precedence_rank=-1,
        status="missing",
        classification="wrong",
        critical=True,
        value=[],
    )
    problems = validate_atom(atom)
    assert any("type" in p for p in problems)
    assert any("id" in p for p in problems)
    assert any("layer" in p for p in problems)
    assert any("value" in p for p in problems)


def test_atom_to_dict_deep_copies_nested_values():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    got = atom.to_dict()
    got["value"]["summary"] = "mutated"
    got["source_refs"].append({"ref": "changed"})
    assert atom.value["summary"] == "Implement the Canon foundation schema spine."
    assert len(atom.source_refs) == 1


def test_atom_key_names_scope_type_and_id():
    atom = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    assert atom_key(atom) == ("workspace:canon", "active-goal", "goal-foundation")


def test_load_atoms_jsonl_ignores_blank_lines_and_validates():
    a = CanonAtom.from_dict(load_fixture("atom_active_goal.json"))
    b = CanonAtom.from_dict(load_fixture("atom_permission.json"))
    text = "\n" + a.to_json() + "\n" + b.to_json() + "\n"
    assert [atom.id for atom in load_atoms_jsonl(text)] == ["goal-foundation", "perm-plan-only"]


def test_load_atoms_jsonl_reports_invalid_line_number():
    bad = '{"atom_schema":"canon.atom/v1","type":"bad","id":"","layer":"bad","scope_key":"","precedence_rank":0,"status":"active","classification":"normative","critical":true,"value":{},"source_refs":[],"source_span_refs":[],"freshness":{},"trust":{},"disclosure":{},"hashes":{}}\n'
    try:
        load_atoms_jsonl(bad)
    except ValueError as exc:
        assert "line 1:" in str(exc)
    else:
        raise AssertionError("invalid JSONL atom should raise ValueError")


def test_atoms_from_records_maps_existing_records_deterministically():
    records = [
        load_record(RECORD_FILES["adr-decision"]),
        load_record(RECORD_FILES["personality-block"]),
        load_record(RECORD_FILES["research-artifact-ref"]),
    ]
    atoms = atoms_from_records(reversed(records))
    assert [atom.type for atom in atoms] == ["decision", "evidence-ref", "instruction"]
    assert [atom_key(atom) for atom in atoms] == [
        ("record-scope:workspace", "decision", "adr-0001-container-name"),
        ("record-scope:workspace", "evidence-ref", "artref-0007"),
        ("record-scope:workspace", "instruction", "voice-canon"),
    ]
    instruction = [atom for atom in atoms if atom.type == "instruction"][0]
    assert instruction.classification == "normative"
    assert instruction.critical is False
    assert instruction.hashes["record_sha256"].startswith("sha256:")
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_atom.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.atom'`.

- [ ] **Step 3: Implement atom dataclass and validator**

Create `src/canon/atom.py` using the exact interfaces above.

Implementation details:

- Store tuple fields as tuples internally.
- `to_dict()` returns lists for tuple fields.
- `to_dict()` and `from_dict()` deep-copy nested dict/list values.
- `to_json()` returns `canonical_json_text(self.to_dict())`.
- `from_json()` uses `json.loads` and `from_dict`.
- `validate_atom()` accumulates all problems and does not raise.
- `atom_key()` returns `(atom.scope_key, atom.type, atom.id)`.
- `load_atoms_jsonl()` ignores blank lines, validates every parsed atom, and raises `ValueError` with the one-based line number on invalid input.
- `atoms_from_records()` calls `validate_record()` before mapping any record and returns atoms sorted by `(precedence_rank, layer, type, id)`.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_atom.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "atom_schema|CanonAtom|atom_key|atoms_from_records|load_atoms_jsonl|critical" src/canon/atom.py tests/test_atom.py
```

Expected: matches show the schema constant, dataclass, helper contracts, JSONL loader, record mapper, and critical-retention validation test.

### Task 3: Omission and Transform Receipts

**Files:**

- Create: `src/canon/omission.py`
- Create: `src/canon/transform.py`
- Create: `tests/test_descriptors.py`
- Create: `tests/fixtures/foundation/omission_budget_noncritical.json`
- Create: `tests/fixtures/foundation/transform_summary.json`

**Interfaces:**

- Consumes: `canonical_json_text`, `is_sha256_ref`, `Omission` inside `TransformReceipt`.
- Produces: `Omission`, `TransformReceipt`, `validate_omission`, `validate_transform_receipt`.

- [ ] **Step 1: Write the failing tests and fixtures**

Create fixture files exactly as listed in Foundation Fixture Content.

Create `tests/test_descriptors.py` with the omission and transform tests first:

```python
from __future__ import annotations

import json
from pathlib import Path

from canon.omission import Omission, validate_omission
from canon.transform import TransformReceipt, validate_transform_receipt

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def test_noncritical_budget_omission_roundtrips():
    d = load_fixture("omission_budget_noncritical.json")
    omission = Omission.from_dict(d)
    assert omission.to_dict() == d
    assert omission.to_json().endswith("\n")
    assert validate_omission(omission) == []


def test_critical_omission_cannot_be_marked_omitted():
    omission = Omission("budget", 1, ("goal-1",), (), True, "omitted")
    assert any("critical" in p and "omitted" in p for p in validate_omission(omission))


def test_omission_count_matches_affected_ids_when_ids_are_listed():
    omission = Omission("budget", 2, ("fact-1",), (), False, "omitted")
    assert any("count" in p for p in validate_omission(omission))


def test_transform_receipt_roundtrips_nested_omissions():
    d = load_fixture("transform_summary.json")
    receipt = TransformReceipt.from_dict(d)
    assert receipt.to_dict() == d
    assert receipt.to_json().endswith("\n")
    assert validate_transform_receipt(receipt) == []


def test_transform_receipt_requires_hash_boundaries():
    receipt = TransformReceipt(
        transform="summary",
        method_id="deterministic-summary-v1",
        input_refs=("record:workspace/goal-1",),
        input_span_hash="not-a-hash",
        output_ref="atom:goal-1",
        output_hash="sha256:" + "b" * 64,
        lossy=True,
        retained_critical_atom_ids=("goal-1",),
    )
    assert any("input_span_hash" in p for p in validate_transform_receipt(receipt))
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_descriptors.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.omission'`.

- [ ] **Step 3: Implement omission and transform modules**

Create `src/canon/omission.py` and `src/canon/transform.py` using the exact interfaces above.

Implementation details:

- Keep validators total and list-returning.
- `to_dict()` emits `schema` first by key name after JSON sorting, not insertion order.
- `TransformReceipt.from_dict()` reconstructs nested omissions with `Omission.from_dict`.
- `TransformReceipt.to_dict()` emits nested omissions with `o.to_dict()`.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_descriptors.py -q
```

Expected: PASS for the omission and transform tests.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "critical|input_span_hash|output_hash|does_not_prove" src/canon/omission.py src/canon/transform.py tests/test_descriptors.py
```

Expected: matches show critical omission refusal, transform hash validation, and does-not-prove carriage.

### Task 4: Adapter Descriptor

**Files:**

- Create: `src/canon/adapter.py`
- Modify: `tests/test_descriptors.py`
- Create: `tests/fixtures/foundation/adapter_codex_cli_native_advisory.json`
- Create: `tests/fixtures/foundation/adapter_mcp_readonly_guided.json`
- Create: `tests/fixtures/foundation/adapter_a2a_artifact_guided.json`

**Interfaces:**

- Consumes: `canonical_json_text`.
- Produces: `AdapterDescriptor`, `builtin_descriptors`, `descriptor_for`, `assert_requested_tier_allowed`, `validate_adapter_descriptor`, `ADAPTER_SCHEMA`, `INTEGRATION_TIERS`.

- [ ] **Step 1: Append failing adapter tests and fixture**

Create `tests/fixtures/foundation/adapter_codex_cli_native_advisory.json`, `tests/fixtures/foundation/adapter_mcp_readonly_guided.json`, and `tests/fixtures/foundation/adapter_a2a_artifact_guided.json` exactly as listed in Foundation Fixture Content.

Append to `tests/test_descriptors.py`:

```python
import pytest

from canon.adapter import (
    AdapterDescriptor,
    assert_requested_tier_allowed,
    builtin_descriptors,
    descriptor_for,
    validate_adapter_descriptor,
)


@pytest.mark.parametrize(
    ("fixture_name", "adapter_id", "integration_tier"),
    (
        ("adapter_codex_cli_native_advisory.json", "codex-cli", "native-advisory"),
        ("adapter_mcp_readonly_guided.json", "mcp-readonly", "guided"),
        ("adapter_a2a_artifact_guided.json", "a2a-artifact", "guided"),
    ),
)
def test_builtin_adapter_descriptor_fixtures_roundtrip(fixture_name, adapter_id, integration_tier):
    d = load_fixture(fixture_name)
    adapter = AdapterDescriptor.from_dict(d)
    assert adapter.adapter_id == adapter_id
    assert adapter.integration_tier == integration_tier
    assert adapter.to_dict() == d
    assert adapter.to_json().endswith("\n")
    assert validate_adapter_descriptor(adapter) == []


def test_builtin_descriptors_are_conservative_lowercase_and_valid():
    descriptors = builtin_descriptors()
    by_id = {d.adapter_id: d for d in descriptors}

    assert tuple(by_id) == (
        "codex-cli",
        "claude-code",
        "chatgpt-app",
        "claude-app",
        "api-runner",
        "local-runner",
        "mcp-readonly",
        "a2a-artifact",
    )
    assert all(d.adapter_id == d.adapter_id.lower() for d in descriptors)
    assert by_id["codex-cli"].integration_tier == "native-advisory"
    assert by_id["claude-code"].integration_tier == "native-advisory"
    assert by_id["chatgpt-app"].integration_tier == "guided"
    assert by_id["claude-app"].integration_tier == "guided"
    assert by_id["api-runner"].integration_tier == "guided"
    assert by_id["local-runner"].integration_tier == "guided"
    assert by_id["mcp-readonly"].integration_tier == "guided"
    assert by_id["a2a-artifact"].integration_tier == "guided"
    assert all(d.integration_tier != "enforced" for d in descriptors)
    assert all(d.bootstrap.get("can_block_before_work") is False for d in descriptors)
    assert all(validate_adapter_descriptor(d) == [] for d in descriptors)


def test_descriptor_for_uses_exact_lowercase_builtin_ids():
    assert descriptor_for("codex-cli").display_name == "Codex CLI"
    assert descriptor_for("claude-code").integration_tier == "native-advisory"
    assert descriptor_for("mcp-readonly").integration_tier == "guided"
    assert descriptor_for("a2a-artifact").display_name == "A2A Artifact"

    with pytest.raises(KeyError):
        descriptor_for("Codex-CLI")

    with pytest.raises(KeyError):
        descriptor_for("unknown-adapter")


def test_requested_tier_guard_rejects_unproved_promotion():
    guided = descriptor_for("chatgpt-app")
    native = descriptor_for("codex-cli")

    assert_requested_tier_allowed(guided, "guided")
    assert_requested_tier_allowed(guided, "unsupported")
    assert_requested_tier_allowed(native, "native-advisory")
    assert_requested_tier_allowed(native, "guided")

    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(guided, "native-advisory")

    with pytest.raises(ValueError, match="stronger"):
        assert_requested_tier_allowed(native, "enforced")

    with pytest.raises(ValueError, match="unknown tier"):
        assert_requested_tier_allowed(native, "blocking")


def test_enforced_adapter_requires_blocking_evidence():
    adapter = AdapterDescriptor(
        adapter_id="closed-app",
        display_name="Closed App",
        version="0",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("paste",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": False},
        evidence_refs=(),
    )
    assert any("enforced" in p for p in validate_adapter_descriptor(adapter))


def test_enforced_adapter_with_blocking_evidence_validates():
    adapter = AdapterDescriptor(
        adapter_id="owned-wrapper",
        display_name="Owned Wrapper",
        version="1",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": True},
        evidence_refs=("fixture:owned-wrapper-blocking-start",),
    )
    assert validate_adapter_descriptor(adapter) == []
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_descriptors.py::test_builtin_adapter_descriptor_fixtures_roundtrip tests/test_descriptors.py::test_builtin_descriptors_are_conservative_lowercase_and_valid tests/test_descriptors.py::test_descriptor_for_uses_exact_lowercase_builtin_ids tests/test_descriptors.py::test_requested_tier_guard_rejects_unproved_promotion tests/test_descriptors.py::test_enforced_adapter_requires_blocking_evidence tests/test_descriptors.py::test_enforced_adapter_with_blocking_evidence_validates -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.adapter'`.

- [ ] **Step 3: Implement adapter descriptor module**

Create `src/canon/adapter.py` using the exact interfaces above.

Implementation details:

- Reject advertised `enforced` without both blocking bootstrap evidence and at least one retained evidence ref.
- Do not infer tier strength from adapter id or display name.
- Preserve `known_unknowns`.
- Keep `builtin_descriptors()` as the foundation-owned built-in registry until the Adapter/UX plan extends or revises proof status with explicit fixtures.
- `descriptor_for()` must not import a later `adapter_registry` module.
- `assert_requested_tier_allowed()` must reject promotion requests above the descriptor's current declared tier.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_descriptors.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "builtin_descriptors|descriptor_for|assert_requested_tier_allowed|codex-cli|claude-code|chatgpt-app|claude-app|api-runner|local-runner|mcp-readonly|a2a-artifact|enforced|native-advisory|guided|unsupported|can_block_before_work" src/canon/adapter.py tests/test_descriptors.py tests/fixtures/foundation/adapter_codex_cli_native_advisory.json tests/fixtures/foundation/adapter_mcp_readonly_guided.json tests/fixtures/foundation/adapter_a2a_artifact_guided.json
```

Expected: matches show all built-in ids, tier vocabulary, exact lookup, requested-tier guard, and the enforced blocking proof gate.

### Task 5: Readiness Probe and Result

**Files:**

- Create: `src/canon/readiness.py`
- Create: `tests/test_readiness.py`
- Create: `tests/fixtures/foundation/readiness_probe.json`

**Interfaces:**

- Consumes: `canonical_sha256`, `is_sha256_ref`.
- Produces: `ReadinessProbe`, `ReadinessResult`, validators, `evaluate_readiness_response`.

- [ ] **Step 1: Write failing readiness tests and fixture**

Create `tests/fixtures/foundation/readiness_probe.json` exactly as listed in Foundation Fixture Content.

Create `tests/test_readiness.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from canon.readiness import (
    ReadinessProbe,
    ReadinessResult,
    evaluate_readiness_response,
    validate_readiness_probe,
    validate_readiness_result,
)

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def test_readiness_probe_roundtrips_and_validates():
    d = load_fixture("readiness_probe.json")
    probe = ReadinessProbe.from_dict(d)
    assert probe.to_dict() == d
    assert validate_readiness_probe(probe) == []


def test_readiness_response_passes_exact_critical_sets():
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    response = {k: list(v) for k, v in probe.critical_sets.items()}
    result = evaluate_readiness_response(probe, response)
    assert result.verdict == "pass"
    assert result.missing_ids == ()
    assert result.mismatched_ids == ()
    assert validate_readiness_result(result) == []


def test_readiness_response_fails_on_missing_critical_id():
    probe = ReadinessProbe(
        probe_id="probe-1",
        capsule_id="sha256:" + "a" * 64,
        target={},
        critical_sets={"active_goal_ids": ("goal-1",)},
        challenge={},
        checker={},
    )
    result = evaluate_readiness_response(probe, {"active_goal_ids": []})
    assert result.verdict == "fail"
    assert result.missing_ids == ("goal-1",)


def test_readiness_result_validator_rejects_bad_response_hash():
    result = ReadinessResult(
        probe_id="probe-1",
        capsule_id="sha256:" + "a" * 64,
        verdict="pass",
        reported={},
        missing_ids=(),
        mismatched_ids=(),
        response_hash="bad",
    )
    assert any("response_hash" in p for p in validate_readiness_result(result))
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_readiness.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.readiness'`.

- [ ] **Step 3: Implement readiness module**

Create `src/canon/readiness.py` using the exact interfaces above.

Implementation details:

- `evaluate_readiness_response()` computes `response_hash` with `canonical_sha256(response)`.
- Missing critical ids are sorted lexically in `missing_ids`.
- Mismatched ids are sorted lexically in `mismatched_ids`.
- `reported` stores a deep copy of the response.
- A response key absent from the response is treated as an empty list for that critical set.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_readiness.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "active_goal_ids|permission_ids|prohibition_ids|frontier_state_ids|unresolved_conflict_ids|unknown_ids|exact-id-set" src/canon/readiness.py tests/test_readiness.py
```

Expected: matches show all critical continuity categories are checked.

### Task 6: Bootstrap Witness

**Files:**

- Create: `src/canon/witness.py`
- Create: `tests/test_witness.py`
- Create: `tests/fixtures/foundation/bootstrap_witness_pass.json`

**Interfaces:**

- Consumes: `AdapterDescriptor` tier vocabulary through `INTEGRATION_TIERS`, `Omission`, `TransformReceipt`, `ReadinessResult`, `is_sha256_ref`.
- Produces: `BootstrapCheck`, `BootstrapWitness`, `validate_bootstrap_witness`.

- [ ] **Step 1: Write failing witness tests and fixture**

Create `tests/fixtures/foundation/bootstrap_witness_pass.json` exactly as listed in Foundation Fixture Content.

Create `tests/test_witness.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from canon.readiness import ReadinessResult
from canon.witness import BootstrapCheck, BootstrapWitness, validate_bootstrap_witness

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def test_bootstrap_witness_roundtrips_and_validates():
    d = load_fixture("bootstrap_witness_pass.json")
    witness = BootstrapWitness.from_dict(d)
    assert witness.to_dict() == d
    assert witness.to_json().endswith("\n")
    assert validate_bootstrap_witness(witness) == []


def test_enforced_witness_cannot_claim_observed_without_pass_readiness():
    result = ReadinessResult(
        "probe-1",
        "sha256:" + "a" * 64,
        "fail",
        {},
        ("goal-1",),
        (),
        "sha256:" + "b" * 64,
    )
    witness = BootstrapWitness(
        run_id="run-1",
        capsule_id="sha256:" + "a" * 64,
        capsule_manifest_sha256="sha256:" + "a" * 64,
        source_state={"records_digest": "sha256:" + "c" * 64},
        target={"adapter": "codex-cli", "surface": "CANON.md"},
        integration_tier_claimed="enforced",
        host_enforcement_observed=True,
        started_at="2026-08-30T00:00:00Z",
        checks=(BootstrapCheck("readiness", "fail"),),
        omissions=(),
        lossy_transforms=(),
        readiness_result=result,
    )
    assert any("readiness" in p for p in validate_bootstrap_witness(witness))


def test_native_advisory_witness_may_record_no_host_enforcement():
    witness = BootstrapWitness.from_dict(load_fixture("bootstrap_witness_pass.json"))
    assert witness.integration_tier_claimed == "native-advisory"
    assert witness.host_enforcement_observed is False
    assert validate_bootstrap_witness(witness) == []
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_witness.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.witness'`.

- [ ] **Step 3: Implement witness module**

Create `src/canon/witness.py` using the exact interfaces above.

Implementation details:

- Convert nested checks, omissions, transforms, and readiness result in `from_dict`.
- Use `to_dict()` on nested objects.
- Include validation for failed checks when `host_enforcement_observed` is true.
- Do not validate date format beyond non-empty string in this tranche.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_witness.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate**

Run:

```powershell
rg -n "host_enforcement_observed|readiness|does_not_prove|started_at|capsule_manifest_sha256" src/canon/witness.py tests/test_witness.py
```

Expected: matches show event fields remain in witness, not in capsule identity.

### Task 7: Capsule Manifest and Compiler Base

**Files:**

- Create: `src/canon/capsule.py`
- Create: `tests/test_capsule.py`
- Create: `tests/fixtures/foundation/capsule_minimal_needle.json`
- Create: `tests/fixtures/foundation/capsule_handoff_full.json`

**Interfaces:**

- Consumes: `CanonAtom`, `Omission`, `TransformReceipt`, `AdapterDescriptor` tier values, `ReadinessProbe`, `Record`, canonical JSON helpers.
- Produces: `Capsule`, `CapsuleTarget`, `SourceState`, `Compatibility`, `Budget`, `Integrity`, `CapsuleCompileRequest`, `CapsuleBundle`, `build_capsule`, `validate_capsule`, `capsule_bytes`, `capsule_digest`. `compile_capsule(request)` is implemented in Task 8 after `render_canon_md` exists.

- [ ] **Step 1: Write failing capsule tests**

Create `tests/test_capsule.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

import pytest

from canon.atom import CanonAtom
from canon.capsule import (
    Budget,
    Capsule,
    CapsuleBundle,
    CapsuleBuildError,
    CapsuleCompileRequest,
    CapsuleTarget,
    SourceState,
    build_capsule,
    capsule_bytes,
    capsule_digest,
    validate_capsule,
)
from canon.omission import Omission
from canon.readiness import ReadinessProbe
from canon.transform import TransformReceipt

FOUNDATION = Path(__file__).parent / "fixtures" / "foundation"


def load_fixture(name: str) -> dict:
    return json.loads((FOUNDATION / name).read_text(encoding="utf-8"))


def _atom(name: str) -> CanonAtom:
    return CanonAtom.from_dict(load_fixture(name))


def _target() -> CapsuleTarget:
    return CapsuleTarget("codex-cli", "CANON.md", "native-advisory")


def _source_state() -> SourceState:
    return SourceState(records_digest="sha256:" + "a" * 64)


def _budget(profile: str = "handoff") -> Budget:
    return Budget(profile, 4096, 512, "unknown")


def _capsule_fixture() -> Capsule:
    atoms = (
        _atom("atom_permission.json"),
        _atom("atom_active_goal.json"),
        _atom("atom_prohibition.json"),
        _atom("atom_constraint.json"),
        _atom("atom_frontier_state.json"),
        _atom("atom_conflict.json"),
        _atom("atom_unknown.json"),
    )
    return build_capsule(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=atoms,
        omissions=(Omission.from_dict(load_fixture("omission_budget_noncritical.json")),),
        lossy_transforms=(TransformReceipt.from_dict(load_fixture("transform_summary.json")),),
        does_not_prove=("This capsule does not prove host-level enforcement.",),
        required_atom_ids=("goal-foundation", "perm-plan-only", "prohibit-product-code"),
    )


def test_build_capsule_is_stable_for_shuffled_inputs():
    atoms = [
        CanonAtom(
            "permission", "perm-1", "session", "ws", 1, "active",
            "normative", True, {"allowed": ["edit src/canon"]},
        ),
        CanonAtom(
            "active-goal", "goal-1", "session", "ws", 0, "active",
            "normative", True, {"summary": "build foundation"},
        ),
    ]
    kwargs = dict(
        profile="handoff",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest="sha256:" + "a" * 64),
        budget=Budget("handoff", 4096, 512, "unknown"),
        required_atom_ids=("goal-1", "perm-1"),
    )
    a = build_capsule(atoms=atoms, **kwargs)
    b = build_capsule(atoms=list(reversed(atoms)), **kwargs)
    assert capsule_bytes(a) == capsule_bytes(b)
    assert a.capsule_id == b.capsule_id


def test_build_capsule_fails_when_required_critical_atom_is_missing():
    with pytest.raises(CapsuleBuildError):
        build_capsule(
            profile="needle",
            target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
            source_state=SourceState(records_digest="sha256:" + "a" * 64),
            budget=Budget("needle", 1024, 0, "unknown"),
            atoms=(),
            required_atom_ids=("goal-1",),
        )


def test_capsule_validator_rejects_critical_omission_marked_omitted():
    capsule = build_capsule(
        profile="needle",
        target=CapsuleTarget("codex-cli", "CANON.md", "native-advisory"),
        source_state=SourceState(records_digest="sha256:" + "a" * 64),
        budget=Budget("needle", 1024, 0, "unknown"),
        atoms=(),
        omissions=(Omission("budget", 1, ("goal-1",), (), True, "omitted"),),
    )
    assert any("critical" in p for p in validate_capsule(capsule))


def test_capsule_identity_blanks_self_hash_fields_before_digesting():
    capsule = _capsule_fixture()
    identity = capsule.to_dict(identity=False)
    assert identity["capsule_id"] == ""
    assert identity["integrity"]["manifest_sha256"] == ""
    assert capsule.capsule_id == capsule_digest(capsule)
    assert capsule.integrity.manifest_sha256 == capsule.capsule_id


def test_capsule_derives_conflicts_unknowns_layers_and_freshness():
    capsule = _capsule_fixture()
    assert [a.id for a in capsule.conflicts] == ["conflict-enforced-tier"]
    assert [a.id for a in capsule.unknowns] == ["unknown-closed-app-hooks"]
    assert "session" in capsule.layers
    assert "project" in capsule.layers
    assert any(row["id"] == "goal-foundation" for row in capsule.freshness)


def test_capsule_roundtrips_from_dict():
    capsule = _capsule_fixture()
    got = Capsule.from_dict(capsule.to_dict())
    assert got == capsule
    assert validate_capsule(got) == []


def test_compile_request_and_bundle_are_plain_value_objects():
    request = CapsuleCompileRequest(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=(_atom("atom_active_goal.json"),),
        required_atom_ids=("goal-foundation",),
        readiness_probe_id="probe-foundation-1",
    )
    capsule = _capsule_fixture()
    probe = ReadinessProbe.from_dict(load_fixture("readiness_probe.json"))
    bundle = CapsuleBundle(
        capsule=capsule,
        manifest_bytes=capsule_bytes(capsule),
        canon_md="# CANON\n",
        readiness_probe=probe,
    )
    assert request.readiness_probe_id == "probe-foundation-1"
    assert bundle.capsule == capsule
    assert bundle.manifest_bytes == capsule_bytes(capsule)
    assert bundle.readiness_probe.probe_id == "probe-foundation-1"
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_capsule.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.capsule'`.

- [ ] **Step 3: Implement capsule module**

Create `src/canon/capsule.py` using the exact interfaces above, except `compile_capsule(request)`, which is wired in Task 8 after `canonmd.py` exists.

Implementation details:

- `Capsule.to_dict(identity=True)` emits final manifest fields.
- `Capsule.to_dict(identity=False)` emits `capsule_id=""` and `integrity.manifest_sha256=""`.
- `capsule_identity_dict(capsule)` returns `capsule.to_dict(identity=False)`.
- `capsule_digest(capsule)` returns `canonical_sha256(capsule_identity_dict(capsule))`.
- `capsule_bytes(capsule)` returns `canonical_json_bytes(capsule.to_dict())`.
- `build_capsule()` first builds a draft with blank identity, computes digest, then returns a final capsule with both digest fields set.
- `validate_capsule()` validates nested atoms, omissions, and transforms.
- `CapsuleCompileRequest` and `CapsuleBundle` are frozen slots dataclasses in `capsule.py`; they are not implemented in `canonmd.py`.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_capsule.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate and lock capsule fixtures**

After tests pass, generate `capsule_minimal_needle.json` and `capsule_handoff_full.json` from `build_capsule()` using the fixture atoms. The minimal fixture contains one `instruction` or `active-goal` atom and no omissions. The full handoff fixture contains goal, permission, prohibition, constraint, frontier state, conflict, unknown, one omission, one transform, and does-not-prove text.

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_capsule.py -q
```

Expected: PASS after fixture generation.

- [ ] **Step 6: Review gate**

Run:

```powershell
rg -n "CapsuleCompileRequest|CapsuleBundle|capsule_id|manifest_sha256|identity=False|critical-atoms-lossless|required_atom_ids" src/canon/capsule.py tests/test_capsule.py tests/fixtures/foundation/capsule_minimal_needle.json tests/fixtures/foundation/capsule_handoff_full.json
```

Expected: matches show compile value objects, self-hash blanking, integrity binding, and critical atom retention.

### Task 8: Generated `CANON.md` and Compile Convenience

**Files:**

- Create: `src/canon/canonmd.py`
- Modify: `src/canon/capsule.py`
- Create: `tests/test_canonmd.py`
- Create: `tests/fixtures/foundation/CANON.expected.md`

**Interfaces:**

- Consumes: `Capsule`, `CapsuleCompileRequest`, `CapsuleBundle`, `ReadinessProbe`, `capsule_bytes`, `build_capsule`, `validate_capsule`.
- Produces: `render_canon_md`, `parse_canon_md_carrier`, `verify_canon_md`, `CANON_MD_SECTIONS`, and executable `compile_capsule(request: CapsuleCompileRequest) -> CapsuleBundle` in `src/canon/capsule.py`.

- [ ] **Step 1: Write failing `CANON.md` tests**

Create `tests/test_canonmd.py`:

```python
from __future__ import annotations

from canon.canonmd import (
    CANON_MD_SECTIONS,
    parse_canon_md_carrier,
    render_canon_md,
    verify_canon_md,
)
from canon.capsule import (
    CapsuleBundle,
    CapsuleCompileRequest,
    capsule_bytes,
    compile_capsule,
)
from tests.test_capsule import _atom, _budget, _capsule_fixture, _source_state, _target


def test_render_canon_md_is_deterministic_and_section_ordered():
    text1 = render_canon_md(_capsule_fixture())
    text2 = render_canon_md(_capsule_fixture())
    assert text1 == text2
    positions = [text1.index("## " + section) for section in CANON_MD_SECTIONS]
    assert positions == sorted(positions)


def test_canon_md_carrier_roundtrips_capsule_dict():
    capsule = _capsule_fixture()
    text = render_canon_md(capsule)
    assert parse_canon_md_carrier(text) == capsule.to_dict()


def test_verify_canon_md_detects_body_drift():
    text = render_canon_md(_capsule_fixture())
    tampered = text.replace("## Active goals", "## Active goals\n\nTampered line", 1)
    assert any("body drift" in p for p in verify_canon_md(tampered))


def test_verify_canon_md_detects_capsule_mismatch():
    text = render_canon_md(_capsule_fixture())
    other = _capsule_fixture()
    changed = other.to_dict()
    changed["does_not_prove"] = ["changed"]
    assert any("capsule mismatch" in p for p in verify_canon_md(text, other))


def test_render_canon_md_includes_required_visible_state():
    text = render_canon_md(_capsule_fixture())
    assert "# CANON\n" in text
    assert "sha256:" in text
    assert "native-advisory" in text
    assert "goal-foundation" in text
    assert "perm-plan-only" in text
    assert "prohibit-product-code" in text
    assert "conflict-enforced-tier" in text
    assert "unknown-closed-app-hooks" in text
    assert "This capsule does not prove host-level enforcement." in text


def test_compile_capsule_returns_bundle_with_manifest_canon_md_and_probe():
    request = CapsuleCompileRequest(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=(
            _atom("atom_active_goal.json"),
            _atom("atom_permission.json"),
            _atom("atom_prohibition.json"),
            _atom("atom_constraint.json"),
            _atom("atom_frontier_state.json"),
            _atom("atom_conflict.json"),
            _atom("atom_unknown.json"),
        ),
        required_atom_ids=("goal-foundation", "perm-plan-only", "prohibit-product-code"),
        readiness_probe_id="probe-foundation-compile",
    )
    bundle = compile_capsule(request)
    assert isinstance(bundle, CapsuleBundle)
    assert bundle.manifest_bytes == capsule_bytes(bundle.capsule)
    assert bundle.canon_md == render_canon_md(bundle.capsule)
    assert bundle.readiness_probe.probe_id == "probe-foundation-compile"
    assert bundle.readiness_probe.capsule_id == bundle.capsule.capsule_id
    assert list(bundle.readiness_probe.critical_sets["active_goal_ids"]) == ["goal-foundation"]
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_canonmd.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.canonmd'` or `ImportError` for missing `compile_capsule` if `canonmd.py` has already been started.

- [ ] **Step 3: Implement `canonmd` renderer and verifier**

Create `src/canon/canonmd.py` and modify `src/canon/capsule.py` using the exact interfaces above.

Implementation details:

- Use `base64.urlsafe_b64encode(capsule_bytes(capsule)).decode("ascii")` for carrier payload.
- The carrier line includes `digest=` followed by `capsule.capsule_id`.
- `parse_canon_md_carrier()` finds exactly one carrier comment, validates the digest in the carrier equals the decoded capsule `capsule_id`, and returns the decoded capsule dict.
- `verify_canon_md(text, capsule=None)` returns problem strings and never raises for malformed Markdown.
- If `capsule` is provided and its dict differs from the carrier dict, report `capsule mismatch`.
- Re-render from the carrier capsule and compare full text to detect `body drift`.
- Add `compile_capsule(request)` to `src/canon/capsule.py`.
- `compile_capsule(request)` calls `build_capsule()` with the request's profile, target, source state, budget, atoms, records, omissions, transforms, receipts, does-not-prove text, and required atom ids.
- `compile_capsule(request)` creates `manifest_bytes = capsule_bytes(capsule)` and `canon_md = render_canon_md(capsule)`.
- `compile_capsule(request)` creates `ReadinessProbe` from the final capsule's critical atoms using the exact critical-set mapping in the capsule interface section.
- Keep the `render_canon_md` import local inside `compile_capsule()` so importing `canon.capsule` does not import `canon.canonmd` at module import time.

- [ ] **Step 4: Run the green test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_canonmd.py -q
```

Expected: PASS.

- [ ] **Step 5: Generate and lock expected Markdown fixture**

Generate `tests/fixtures/foundation/CANON.expected.md` from `render_canon_md(_capsule_fixture())`.

Add this test after the fixture exists:

```python
from pathlib import Path


def test_render_canon_md_matches_locked_fixture():
    expected = (Path(__file__).parent / "fixtures" / "foundation" / "CANON.expected.md").read_text(encoding="utf-8")
    assert render_canon_md(_capsule_fixture()) == expected
```

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_canonmd.py -q
```

Expected: PASS.

- [ ] **Step 6: Review gate**

Run:

```powershell
rg -n "compile_capsule|CapsuleBundle|Capsule identity|Target and integration tier|Omissions|Lossy transforms|Bootstrap readiness probe|Does-not-prove|canon:capsule/v1" src/canon/capsule.py src/canon/canonmd.py tests/test_canonmd.py tests/fixtures/foundation/CANON.expected.md
```

Expected: matches show the compile convenience path, every required visible section, and the machine carrier.

### Task 9: Public Exports and Integration

**Files:**

- Modify: `src/canon/__init__.py`
- Create: `tests/test_public_exports.py`

**Interfaces:**

- Consumes: all foundation modules.
- Produces: stable package imports for the foundation contract.

- [ ] **Step 1: Write failing public export test**

Create `tests/test_public_exports.py`:

```python
from __future__ import annotations


def test_foundation_public_exports_import():
    from canon import (
        ADAPTER_SCHEMA,
        ATOM_SCHEMA,
        BOOTSTRAP_WITNESS_SCHEMA,
        CAPSULE_SCHEMA,
        OMISSION_SCHEMA,
        READINESS_PROBE_SCHEMA,
        TRANSFORM_SCHEMA,
        AdapterDescriptor,
        BootstrapWitness,
        Budget,
        CanonAtom,
        Capsule,
        CapsuleBundle,
        CapsuleCompileRequest,
        CapsuleTarget,
        Omission,
        ReadinessProbe,
        SourceState,
        TransformReceipt,
        atom_key,
        atoms_from_records,
        assert_requested_tier_allowed,
        build_capsule,
        builtin_descriptors,
        canonical_json_text,
        compile_capsule,
        descriptor_for,
        load_atoms_jsonl,
        render_canon_md,
        sha256_bytes,
        sha256_text,
        validate_atom,
        validate_capsule,
    )

    assert ATOM_SCHEMA == "canon.atom/v1"
    assert CAPSULE_SCHEMA == "canon.capsule/v1"
    assert OMISSION_SCHEMA == "canon.omission/v1"
    assert TRANSFORM_SCHEMA == "canon.transform-receipt/v1"
    assert READINESS_PROBE_SCHEMA == "canon.readiness-probe/v1"
    assert BOOTSTRAP_WITNESS_SCHEMA == "canon.bootstrap-witness/v1"
    assert ADAPTER_SCHEMA == "canon.adapter/v1"
    assert callable(canonical_json_text)
    assert callable(sha256_bytes)
    assert callable(sha256_text)
    assert callable(atom_key)
    assert callable(atoms_from_records)
    assert callable(load_atoms_jsonl)
    assert callable(builtin_descriptors)
    assert callable(descriptor_for)
    assert callable(assert_requested_tier_allowed)
    assert tuple(d.adapter_id for d in builtin_descriptors()) == (
        "codex-cli",
        "claude-code",
        "chatgpt-app",
        "claude-app",
        "api-runner",
        "local-runner",
        "mcp-readonly",
        "a2a-artifact",
    )
    assert callable(build_capsule)
    assert callable(compile_capsule)
    assert callable(render_canon_md)
    assert callable(validate_atom)
    assert callable(validate_capsule)
```

- [ ] **Step 2: Run the red test**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_public_exports.py -q
```

Expected: FAIL with import errors for names not yet exported from `canon`.

- [ ] **Step 3: Export new public names**

Modify `src/canon/__init__.py` only.

Add imports for:

- `canonical_json_text`
- `canonical_json_bytes`
- `sha256_bytes`
- `sha256_text`
- `canonical_sha256`
- `is_sha256_ref`
- `CanonicalJSONError`
- `ATOM_SCHEMA`
- `CanonAtom`
- `atom_key`
- `atoms_from_records`
- `load_atoms_jsonl`
- `validate_atom`
- `is_valid_atom`
- `OMISSION_SCHEMA`
- `Omission`
- `validate_omission`
- `TRANSFORM_SCHEMA`
- `TransformReceipt`
- `validate_transform_receipt`
- `ADAPTER_SCHEMA`
- `AdapterDescriptor`
- `builtin_descriptors`
- `descriptor_for`
- `assert_requested_tier_allowed`
- `validate_adapter_descriptor`
- `READINESS_PROBE_SCHEMA`
- `READINESS_RESULT_SCHEMA`
- `ReadinessProbe`
- `ReadinessResult`
- `evaluate_readiness_response`
- `validate_readiness_probe`
- `validate_readiness_result`
- `BOOTSTRAP_WITNESS_SCHEMA`
- `BootstrapCheck`
- `BootstrapWitness`
- `validate_bootstrap_witness`
- `CAPSULE_SCHEMA`
- `Capsule`
- `CapsuleTarget`
- `SourceState`
- `Compatibility`
- `Budget`
- `Integrity`
- `CapsuleCompileRequest`
- `CapsuleBundle`
- `build_capsule`
- `compile_capsule`
- `capsule_bytes`
- `capsule_digest`
- `validate_capsule`
- `CANON_MD_SECTIONS`
- `render_canon_md`
- `parse_canon_md_carrier`
- `verify_canon_md`

Add each name to `__all__`.

- [ ] **Step 4: Run focused green tests**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider tests/test_public_exports.py tests/test_canonical_json.py tests/test_atom.py tests/test_descriptors.py tests/test_readiness.py tests/test_witness.py tests/test_capsule.py tests/test_canonmd.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full suite**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider
```

Expected: PASS for the full suite.

- [ ] **Step 6: Review gate**

Run:

```powershell
rg -n "ATOM_SCHEMA|CAPSULE_SCHEMA|canonical_json_text|sha256_bytes|sha256_text|CanonAtom|atom_key|atoms_from_records|load_atoms_jsonl|builtin_descriptors|descriptor_for|assert_requested_tier_allowed|mcp-readonly|a2a-artifact|CapsuleCompileRequest|CapsuleBundle|compile_capsule|render_canon_md|validate_capsule" src/canon/__init__.py tests/test_public_exports.py
```

Expected: matches show each foundation public API is exported.

## Final Review Gates

Run these before claiming completion:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider
rg -n "from (yaml|pydantic|jsonschema|requests|click|typer|rich)|import (yaml|pydantic|jsonschema|requests|click|typer|rich)" src
rg -n "TODO|TBD|placeholder" src/canon tests
git diff -- pyproject.toml README.md project-docs
git diff -- docs/superpowers/plans
```

Required outcomes:

- Pytest passes.
- Runtime dependency scan returns no matches.
- Placeholder scan returns no matches.
- `git diff -- pyproject.toml README.md project-docs` is empty.
- `git diff -- docs/superpowers/plans` shows only this plan file if the implementation agent is executing from this plan branch before code work starts.
- `src/canon/__init__.py` exports every new public schema constant, dataclass, builder, renderer, and validator.
- `src/canon/__init__.py` exports `sha256_bytes`, `sha256_text`, `atom_key`, `atoms_from_records`, `load_atoms_jsonl`, `builtin_descriptors`, `descriptor_for`, `assert_requested_tier_allowed`, `CapsuleCompileRequest`, `CapsuleBundle`, and `compile_capsule`.
- New fixtures include positive and negative coverage for atoms, omissions, transforms, readiness, witness, conservative adapter built-ins including `mcp-readonly` and `a2a-artifact`, requested-tier refusal, adapter tier proof, capsule determinism, and `CANON.md` drift.
- No implementation claims enforced bootstrap for closed/advisory hosts.
- No raw protected I0 content, secrets, `.env` values, private transcript bodies, or absolute local paths are embedded in fixtures, capsule fixtures, witness fixtures, or expected `CANON.md`.

## Self-Contained Review Checklist

- [ ] Spec coverage: `canon.atom/v1`, `canon.capsule/v1`, omission receipt, transform receipt, readiness probe, bootstrap witness, adapter descriptor, conservative adapter built-ins including `mcp-readonly` and `a2a-artifact`, adapter lookup, requested-tier guard, deterministic JSON, raw bytes/text sha256 helpers, record-to-atom helpers, atom JSONL loader, compile bundle convenience, `CANON.md`, validators, fixtures, and public exports each map to a task above.
- [ ] Type consistency: all downstream task references use `CanonicalJSONError`, `sha256_bytes`, `sha256_text`, `CanonAtom`, `atom_key`, `atoms_from_records`, `load_atoms_jsonl`, `Omission`, `TransformReceipt`, `AdapterDescriptor`, `builtin_descriptors`, `descriptor_for`, `assert_requested_tier_allowed`, `ReadinessProbe`, `ReadinessResult`, `BootstrapCheck`, `BootstrapWitness`, `CapsuleTarget`, `SourceState`, `Compatibility`, `Budget`, `Integrity`, `Capsule`, `CapsuleCompileRequest`, `CapsuleBundle`, and `compile_capsule` exactly as defined in Interfaces.
- [ ] Determinism: no wall-clock field participates in capsule identity; witness event time is outside capsule manifest identity.
- [ ] Boundary: no product release, package rename, CLI/MCP surface, `.canonpack`, import write path, protected I0 ingestion, or provider enforcement claim is part of this tranche.
- [ ] Safety: implementation uses only stdlib runtime imports and public-safe test data.
