# Canon Core, Schema, and I0 Audit

Date: 2026-08-30

Lane: core/schema/I0

Output: `C:\dev\public\canon\project-docs\audits\2026-08-30\CORE-SCHEMA-I0-AUDIT.md`

Scope: audit only. No product code, test, package, or parallel worktree edits.

## Claim-state legend

- `C: verified` means directly observed in source, tests, docs, command output, or tool output.
- `C: inferred` means derived from multiple verified observations but not directly implemented or declared.
- `C: unknown` means not established by this audit.
- `C: blocked` means evidence was requested but unavailable or impractical within the audit boundary.

## Evidence ledger

### Local instructions and audit contract

- `P: C:\dev\AGENTS.md`
  - `O: workspace method`
  - `C: verified`
  - Requires use of Index before architectural assumptions, evidence over assertion, secrets hygiene, no public leakage of credential material, and explicit labeling of verified facts versus assumptions.
- `P: C:\dev\public\canon\CLAUDE.md`
  - `O: Canon project guidance`
  - `C: verified`
  - Describes Canon as a provider-neutral memory-bank/personality container with one envelope across harnesses and stores, currently built through F0/F1/R0/R1/R2/V2/V3/V4 surfaces and gates.
- `P: C:\dev\public\canon\project-docs\SPEC-CANON-PILLAR-20260830.md`
  - `O: Pillar objective, architecture, bootstrap lifecycle, integration tiers, initial gates`
  - `C: verified`
  - Defines the requested Canon pillar: `CANON.md`, deterministic `canon.capsule/v1`, optional `.canonpack`, profiles, omission and lossy-transform receipts, ambient bootstrap witness, and retention gates.
- `P: C:\dev\public\canon\project-docs\audits\2026-08-30\README.md`
  - `O: audit lane rules`
  - `C: verified`
  - Requires planning evidence only, no product code/publication/deployment/package registration, no edits to the parallel I0 worktree, evidence citations, gates, explicit unknowns, and Now/Next/Later.

### Workspace/context tools

- `P: index MCP`
  - `O: mcp__index.index_map(root=C:/dev)`
  - `C: verified`
  - Returned a workspace map generated on 2026-08-30 with `repo_count: 503` and `dirty_count: 29456`.
- `P: index MCP`
  - `O: mcp__index.index_context_envelope(...)`
  - `C: verified`
  - A broad request returned a typed `index.focus-rejection/v1` because focus was unresolved across many candidates. Narrow requests for Canon/Mneme/Relay/Index timed out at 300 seconds. This audit therefore uses direct source reads for those interfaces and records the MCP timeout as a tool limitation.
- `P: forum MCP`
  - `O: mcp__forum.route(...)`
  - `C: verified`
  - Routed this investigation to `project-telos`, confidence `0.5`, with no escalation; communication contract emphasized separating observations, inferences, and unknowns.

### Commands

- `P: C:\dev\public\canon`
  - `O: git -C C:\dev\public\canon status --short`
  - `C: verified`
  - Before report creation the only visible untracked audit inputs were `project-docs/SPEC-CANON-PILLAR-20260830.md` and `project-docs/audits/`.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830`
  - `O: git -C C:\dev\worktrees\canon-full-history-memory-bank-20260830 status --short`
  - `C: verified`
  - The I0 worktree had untracked I0 files under `project-docs/`, `src/canon/history_*`, and `tests/test_history_inventory.py`. It was inspected read-only.
- `P: C:\dev\public\canon`
  - `O: rg --files C:\dev\public\canon`
  - `C: verified`
  - Main Canon contains source modules for record schema, validators, layering, backends, surfaces, vault mirror, drift, persona thesis, and reconcile gates; it did not contain this audit report before creation.
- `P: C:\dev\public\canon`
  - `O: $env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -p no:cacheprovider`
  - `C: verified`
  - Main Canon test suite result: `407 passed in 1.36s`.
- `P: C:\dev\public\canon`
  - `O: rg --files ... -g '__pycache__/**' -g '.pytest_cache/**'`
  - `C: verified`
  - No bytecode or pytest cache artifacts were observed after the test command.

### Canon main repo files

- `P: C:\dev\public\canon\pyproject.toml`
  - `O: project metadata`
  - `C: verified`
  - Package name `canon`, version `0.0.0`, Python `>=3.11`, license `FSL-1.1-MIT`, empty runtime dependency list, optional dev dependency on pytest.
- `P: C:\dev\public\canon\README.md`
  - `O: status and quickstart`
  - `C: verified`
  - Documents no runtime dependencies and current F0/F1/R0/R1/R2 status. Future work includes verifier, region installation, and global `SOUL.md`/`GEMINI.md`.
- `P: C:\dev\public\canon\src\canon\schema.py`
  - `O: Record, Provenance, Temporal, constants`
  - `C: verified`
  - Defines `canon.record/v1`, five record kinds, two scopes, sorted JSON serialization, provenance fields, and optional temporal metadata.
- `P: C:\dev\public\canon\src\canon\validator.py`
  - `O: validate_record`
  - `C: verified`
  - Enforces required data fields and kind/scope/temporal/provenance shape. It rejects temporal metadata for `research-artifact-ref`.
- `P: C:\dev\public\canon\src\canon\layering.py`
  - `O: render_layers`
  - `C: verified`
  - Accepts only `personality-block` records. Global rendering excludes workspace-only records. Workspace rendering overlays workspace blocks over global blocks by ID. Current-state filtering excludes records with `valid_until`.
- `P: C:\dev\public\canon\src\canon\backends\base.py`
  - `O: MemoryBackend, guard_put`
  - `C: verified`
  - Defines backend capability tokens and declared drops. Only record-level temporal drops are enforceable by the base guard; structural drop declarations are ledger facts.
- `P: C:\dev\public\canon\src\canon\backends\sqlite.py`
  - `O: SQLiteBackend`
  - `C: verified`
  - Stores full envelopes with hash-chain audit rows and `verify_chain`.
- `P: C:\dev\public\canon\src\canon\backends\files.py`
  - `O: file backend`
  - `C: verified`
  - File backend is part of the F1 surface set and is tested as a per-record JSON backend with audit-chain drop declaration.
- `P: C:\dev\public\canon\src\canon\backends\mneme.py`
  - `O: MnemeBackend`
  - `C: verified`
  - Supports memory record kinds, maps Canon scope to Mneme user/session, drops arbitrary kinds, relations, and foreign provenance, and refuses temporal/supersession cases Mneme cannot represent safely.
- `P: C:\dev\public\canon\src\canon\backends\flywheel.py`
  - `O: FlywheelBackend`
  - `C: verified`
  - Stores full envelopes in injected Flywheel data blobs keyed by Canon record key and refuses live temporal data unless flattened.
- `P: C:\dev\public\canon\src\canon\region.py`
  - `O: marker extraction/splice`
  - `C: verified`
  - Implements Canon marker extraction and replacement for global/workspace regions and fails closed on malformed markers or off-limits files.
- `P: C:\dev\public\canon\src\canon\textblock.py`
  - `O: render_textblock_region, ingest_textblock_region`
  - `C: verified`
  - Implements deterministic textblock rendering/ingestion for personality blocks only and reconstructs `canon-text` provenance on ingest.
- `P: C:\dev\public\canon\src\canon\fidelity.py`
  - `O: roundtrip_report`
  - `C: verified`
  - Produces declared drop ledgers and field diffs for textblock round trips.
- `P: C:\dev\public\canon\src\canon\surface.py`
  - `O: apply_surface`
  - `C: verified`
  - Applies layered personality blocks to a target surface while preserving bytes outside markers.
- `P: C:\dev\public\canon\src\canon\registry.py`
  - `O: SURFACE_CATALOG, write_surfaces`
  - `C: verified`
  - Catalogs four surfaces: Claude Code global, Claude Code workspace, Codex workspace, and Hermes workspace. It guards allowed paths and plans all writes before commit.
- `P: C:\dev\public\canon\src\canon\frontmatter.py`
  - `O: render_frontmatter_note, ingest_frontmatter_note`
  - `C: verified`
  - Uses constrained frontmatter without a YAML loader and treats `canon:` JSON as the authoritative carrier.
- `P: C:\dev\public\canon\src\canon\vault.py`
  - `O: render_note, ingest_note`
  - `C: verified`
  - Renders all five record kinds to vault notes and reconstructs records from frontmatter, not body text.
- `P: C:\dev\public\canon\src\canon\vault_mirror.py`
  - `O: plan_mirror, write_mirror`
  - `C: verified`
  - Mirrors records into a vault path with path containment, ownership checks, and orphan reporting without deletion.
- `P: C:\dev\public\canon\src\canon\vault_fidelity.py`
  - `O: vault_roundtrip_report`
  - `C: verified`
  - Reports vault round-trip fidelity against raw records with an empty declared drop ledger for supported records.
- `P: C:\dev\public\canon\src\canon\drift.py`
  - `O: surface drift verifier`
  - `C: verified`
  - Re-derives expected surface regions and returns match/drift/off-limits/refused/missing verdicts without writing.
- `P: C:\dev\public\canon\src\canon\persona_thesis.py`
  - `O: evaluate_persona_thesis`
  - `C: verified`
  - Implements model-free claims for synthesized persona basis presence/currentness with injected assessment.
- `P: C:\dev\public\canon\src\canon\reconcile_gate.py`
  - `O: GateRecord, decide_gate`
  - `C: verified`
  - Implements approved/edited/rejected/pending conflict gate semantics with frozen deadlines and fail-closed expiry handling.
- `P: C:\dev\public\canon\src\canon\reconcile.py`
  - `O: classify_surface`
  - `C: verified`
  - Classifies byte/persona drift into in-sync, fast-forward, held, conflict, skip, or failed states.
- `P: C:\dev\public\canon\src\canon\reconcile_run.py`
  - `O: run_reconcile, run_witness_payload`
  - `C: verified`
  - Performs two-phase classification/write handling and emits path-clean pool-bound witnesses.

### Canon main tests and fixtures

- `P: C:\dev\public\canon\tests\fixtures\records\*.json`
  - `O: record fixtures`
  - `C: verified`
  - Provide fixtures for the five current record kinds.
- `P: C:\dev\public\canon\tests\test_schema_roundtrip.py`
  - `O: schema round-trip tests`
  - `C: verified`
  - Covers field-identical from/to dict, stable JSON round trip, schema rejection, provenance/temporal handling, and deep-copy behavior.
- `P: C:\dev\public\canon\tests\test_validator.py`
  - `O: validator tests`
  - `C: verified`
  - Covers valid fixtures and negative cases for kinds, scopes, hashes, temporal/provenance types, and research-ref temporal rejection.
- `P: C:\dev\public\canon\tests\test_layering.py`
  - `O: layering tests`
  - `C: verified`
  - Covers override semantics, global/workspace separation, supersession/current filtering, deterministic ordering, and invalid input rejection.
- `P: C:\dev\public\canon\tests\test_reconcile.py`
  - `O: reconcile classifier tests`
  - `C: verified`
  - Covers persona fold, drift lattice, held/conflict outcomes, fail-closed behavior, and gate creation constraints.
- `P: C:\dev\public\canon\tests\test_reconcile_run.py`
  - `O: reconcile runner tests`
  - `C: verified`
  - Covers classify-before-write, fast-forward, conflicts, approved overrides, deadline freeze, witness payload shape, and exit behavior.

### Parallel I0 worktree, read-only

- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\project-docs\I0-HISTORY-INGESTION-DESIGN.md`
  - `O: design`
  - `C: verified`
  - Defines a protected inventory-first history ingestion design. It separates inventory from promotion, forbids output under the public repo, refuses symlink/junction traversal, excludes credential paths, quarantines secret signals, and emits public-clean references rather than raw private transcript content.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\project-docs\I0-HISTORY-INGESTION-PLAN.md`
  - `O: plan`
  - `C: verified`
  - Defines implementation steps from tests through discovery, parsers, quarantine, projection, CLI/protected run, and final validation.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\src\canon\history_inventory.py`
  - `O: SourcePlan, InventoryPlan, ArtifactRow, inventory_sources, validate_plan`
  - `C: verified`
  - Implements plan validation, path-safe discovery, credential path exclusion, binary/oversize references, secret quarantine, parser disposition, and deterministic source/locator sorting.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\src\canon\history_manifest.py`
  - `O: canonical_manifest_bytes, project_records, build_receipt`
  - `C: verified`
  - Implements `canon.history-manifest/v1`, `canon.history-receipt/v1`, deterministic manifest bytes, `research-artifact-ref` projection for hashed rows, and aggregate receipt counts.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\src\canon\history_parsers.py`
  - `O: parse_content`
  - `C: verified`
  - Detects common secret patterns and extracts structural metadata from JSONL, JSON, and text without copying document bodies.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\src\canon\history_cli.py`
  - `O: CLI main`
  - `C: verified`
  - Provides a private-plan CLI that refuses unsafe output locations and plan digest mismatches, writes manifest/records/receipt atomically, and prints only aggregate non-secret metadata.
- `P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\tests\test_history_inventory.py`
  - `O: I0 tests`
  - `C: verified`
  - Covers invalid plans, sorting, credential exclusion, binary/oversize references, unreadable rows, parser failures, no markdown body copy, secret quarantine, stable projected records, receipt aggregation, CLI writes, output-under-repo refusal, and plan mismatch refusal.

### Adjacent Index, Relay, and Mneme interfaces

- `P: C:\dev\public\index\src\index_graph\context\envelope.py`
  - `O: build_context_envelope`
  - `C: verified`
  - Defines `project-telos.context-envelope/v1`, source references, freshness receipts, explicit budget omission/failure codes, lossless-by-reference policy, and `raw_source_included: false`.
- `P: C:\dev\public\index\tests\test_context_envelope.py`
  - `O: context envelope tests`
  - `C: verified`
  - Covers receipt-backed envelopes, source refs as verifiable handles, lossless reference policy, budget omissions, selection/freshness receipts, and CLI JSON behavior.
- `P: C:\dev\public\index\src\index_graph\mcp.py`
  - `O: MCP tool surface`
  - `C: verified`
  - Exposes Index MCP tools, typed tool errors, and cache keys that include workspace signature and tool version.
- `P: C:\dev\public\relay\src\relay\compaction.py`
  - `O: compact_messages, verify_compaction`
  - `C: verified`
  - Defines `relay.compaction/v1`, deterministic middle compaction, head/tail/pinned preservation, span and summary hashes, and drift verification.
- `P: C:\dev\public\relay\tests\test_compaction.py`
  - `O: compaction tests`
  - `C: verified`
  - Covers no-op compaction, over-budget folding, pinned message preservation, honest/tampered verification, deterministic summary, and ledger witness behavior.
- `P: C:\dev\public\relay\src\relay\local_session.py`
  - `O: SessionLedger`
  - `C: verified`
  - Implements hash-chained local session entries and checkpoint verification. Its transcript API can expose raw conversation bodies; this audit cites the interface and does not copy private bodies.
- `P: C:\dev\public\relay\src\relay\session_store.py`
  - `O: list_saved_sessions, get_saved_session`
  - `C: verified`
  - Lists and reads saved ledger sessions and marks tampered sessions unverified.
- `P: C:\dev\public\relay\src\relay\contract.py`
  - `O: evaluate_contract`
  - `C: verified`
  - Evaluates witnessed runs for chain integrity, non-gamed checks, no claimed history, no edit, tests pass, reviewability, claim grounding, and approved steps.
- `P: C:\dev\public\relay\src\relay\intent_audit.py`
  - `O: audit_ledger`
  - `C: verified`
  - Audits witnessed ledger entries for claimed history and optional intent/scope drift.
- `P: C:\dev\public\relay\src\relay\claim_grounding.py`
  - `O: ground_final_answer`
  - `C: verified`
  - Grounds final-answer claims against ledger evidence and fails closed for unclassified claims.
- `P: C:\dev\public\mneme\src\mneme\schema.py`
  - `O: SQLite schema v4`
  - `C: verified`
  - Defines turns, memories, source hashes, temporal fields, user/session scope, and schema migrations through version 4.
- `P: C:\dev\public\mneme\src\mneme\store.py`
  - `O: MemoryStore`
  - `C: verified`
  - Implements L0-L3 memory layers, persisted ordinals, source content hashes, supersession, current/as-of recall, cross-user collision refusal, and hash-chained audit.
- `P: C:\dev\public\mneme\src\mneme\receipt.py`
  - `O: ProvenanceReceipt, RecallReceipt`
  - `C: verified`
  - Defines content/memory hashes, provenance receipt validation, hit binding, recall receipts, and recheck command metadata.
- `P: C:\dev\public\mneme\tests\test_recall_receipt.py`
  - `O: recall receipt tests`
  - `C: verified`
  - Covers vector recall with no fake cosine fallback, receipt scope/recheck metadata, hit content-hash binding, and scorer definition hash.
- `P: C:\dev\public\mneme\tests\test_provenance_grounding.py`
  - `O: provenance grounding tests`
  - `C: verified`
  - Covers sourceless memories, forged hash rejection, and well-formed grounded origin receipts.
- `P: C:\dev\public\mneme\tests\test_scope_isolation.py`
  - `O: tenant/scope tests`
  - `C: verified`
  - Covers user-scoped MCP recall, unknown argument rejection, user-scoped persona/scenario consolidation, and cross-tenant collision refusal.

## Executive finding

Current Canon has a solid, tested `canon.record/v1` core and deterministic surfaces for a narrow instruction/personality memory-bank use case. It does not yet implement the Canon Pillar I0 target as specified: no `canon.capsule/v1` compiler, no generated `CANON.md` surface, no `.canonpack`, no ambient bootstrap witness, no readiness probe schema, no adapter-tier verification matrix, and no capsule migration framework were observed in the main Canon repo. `C: verified`

The parallel I0 worktree provides a strong inventory-first boundary for full-history ingestion. It should be integrated as a protected evidence/reference pipeline, not as a direct raw-transcript memory importer. Promotion from inventory references into durable continuity atoms must be a separate reviewed stage with source spans, transform receipts, and secret gates. `C: inferred`

Ambient startup can be called "enforced" only where a host adapter can actually block or fail work before ordinary task execution. For advisory or guided environments, Canon must record the lower tier explicitly and must not claim enforcement. `C: verified` from the pillar spec and `C: inferred` for the required implementation consequence.

## Verified current state

### Record schema

Main Canon currently defines one canonical envelope, `canon.record/v1`. `C: verified`

Current record shape:

```text
Record:
  canon_schema
  kind
  id
  scope
  data
  provenance
  temporal?

Provenance:
  harness
  source_hash
  native_id
  session_id?
  create_ord?
  create_time?
  model_slug?

Temporal:
  valid_until?
  supersedes[]
```

Current allowed kinds:

- `personality-block`
- `episodic-memory`
- `research-artifact-ref`
- `adr-decision`
- `synthesized-persona-l3`

Current allowed scopes:

- `global`
- `workspace`

`P: C:\dev\public\canon\src\canon\schema.py`

`C: verified`

### Validation and determinism

Validation covers known kinds, scope membership, required data fields, provenance shape, hash shape, and temporal shape. Research artifact refs are rejected if temporal metadata is attached. `C: verified`

Serialization uses deterministic sorted JSON and deep-copied data. Tests cover fixture round trips, wrong schema rejection, stable JSON, provenance/temporal handling, and deep-copy safety. `C: verified`

The record core is deterministic enough to be a capsule input, but it is not by itself a capsule manifest. It lacks target surface, budget profile, omission receipt, transform receipt, adapter tier, readiness, and source-state fields. `C: inferred`

### Layering and precedence

Layering currently applies only to `personality-block` records. Global rendering includes global blocks. Workspace rendering overlays workspace blocks over global blocks by matching ID. Current-state filtering excludes expired records and falls back to global if a workspace override is retired. Deterministic order uses `create_ord`, `id`, and source hash tie-break behavior. `C: verified`

This is a narrow two-scope precedence model. It does not yet represent authority classes such as active task instructions, operator assertions, project/repo policy, personal preference, imported history, external facts, unknowns, or conflicts as first-class precedence inputs. `C: verified`

### Surface machinery

Main Canon can render and ingest personality blocks into marked text regions. It can write known surfaces through a four-entry catalog:

- Claude Code global: `.claude/CLAUDE.md`
- Claude Code workspace: `CLAUDE.md`
- Codex workspace: `AGENTS.md`
- Hermes workspace: `SOUL.md`

The registry enforces an allow-list, keeps workspace/global authored pools separate where needed, and plans writes before commit. `C: verified`

No generated `CANON.md` target surface was observed. `C: verified`

### Vault and frontmatter

The vault/frontmatter path can carry all five existing record kinds losslessly through a constrained `canon:` frontmatter JSON carrier. The visible note body is not authoritative. The mirror layer guards path containment and ownership and reports orphans without deletion. `C: verified`

This is the closest existing mechanism to a human-readable carrier with an authoritative embedded machine payload. It can inform `CANON.md`, but it does not provide the capsule sections, bootstrap witness, or adapter target semantics requested by the pillar spec. `C: inferred`

### Drift and reconcile

The drift layer re-derives expected surface content and reports match/drift/off-limits/refused/missing without writing. V3 persona-thesis checks use injected assessment. V4 reconcile classifies surface states and uses gates for conflict and held cases. The reconcile runner classifies all surfaces before writes and emits path-clean pool-bound witness payloads. `C: verified`

These components provide useful primitives for capsule conflict handling and witness design, but they are not a full bootstrap witness or readiness probe. `C: inferred`

### Backends

The SQLite backend is the strongest current reference store because it preserves full envelopes and hash-chain audit history. `C: verified`

The file backend is a simple per-record JSON backend with an audit-chain drop declaration. `C: verified`

The Mneme backend intentionally drops some semantics, including arbitrary kinds, relations, and foreign provenance. It also refuses live temporal cases it cannot safely represent. `C: verified`

The Flywheel backend stores full envelopes in injected data blobs but declares/detects temporal limitations. `C: verified`

Backend drop declarations are already a Canon pattern and should become part of capsule adapter conformance. `C: inferred`

### Packaging and CLI state

Canon is versioned as `0.0.0`, has no runtime dependencies, and uses pytest as an optional dev dependency. No console scripts or capsule CLI entrypoints were observed. `C: verified`

## I0 integration boundary

### What I0 is, based on the read-only worktree

The parallel I0 worktree implements or proposes a full-history inventory lane that:

- Reads a private source plan outside the public repo.
- Discovers declared source roots without following symlinks/junctions.
- Excludes credential-bearing path classes.
- Quarantines files with secret signals.
- Hashes binary and oversize files by reference.
- Extracts only structural metadata from JSONL, JSON, and text.
- Emits deterministic manifests and aggregate receipts.
- Projects hashed artifacts to `research-artifact-ref` records.
- Refuses output under the repository.
- Refuses plan digest mismatches rather than mutating stale output.

`P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\project-docs\I0-HISTORY-INGESTION-DESIGN.md`

`P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\src\canon\history_*.py`

`P: C:\dev\worktrees\canon-full-history-memory-bank-20260830\tests\test_history_inventory.py`

`C: verified`

### Required boundary

I0 should feed Canon as evidence inventory, not as automatic memory truth. `C: inferred`

Recommended integration boundary:

1. Protected source inventory produces:
   - `canon.history-manifest/v1`
   - `canon.history-receipt/v1`
   - zero or more `research-artifact-ref` records
2. Capsule compiler consumes only public-clean artifact refs and aggregate receipts.
3. Promotion into stronger atom types, such as `active-goal`, `decision`, `episodic-fact`, or `instruction`, requires an explicit promotion receipt with:
   - source identity
   - source span or structural locator
   - transform method
   - input hash
   - output atom hash
   - reviewer or deterministic rule identity
   - omission list
4. Raw private conversation bodies remain outside the public repo and outside default capsule payloads.

`C: inferred`

### What must not happen

- I0 must not copy raw private transcripts into public Canon files. `C: verified` from I0 design intent and `C: inferred` as acceptance requirement.
- I0 must not treat every historical statement as current authority. `C: inferred`
- I0 must not silently promote stale, superseded, contradictory, or untrusted historical content into normative instructions. `C: inferred`
- I0 must not weaken secret handling when moving from the worktree into main Canon. `C: inferred`

## `canon.capsule/v1` proposal

### Role

`canon.capsule/v1` should be a deterministic manifest that compiles continuity atoms and supporting records for a target host/surface/profile. It should not replace `canon.record/v1`; it should sit above it. `C: inferred`

The capsule should answer:

- What continuity state is being presented?
- Which source state produced it?
- Which target host/surface/profile is it for?
- What was omitted and why?
- Which transforms were lossy?
- Which conflicts or unknowns remain visible?
- Which checks passed or failed?
- What enforcement tier can the adapter honestly claim?

`C: inferred`

### Proposed top-level schema

```json
{
  "schema": "canon.capsule/v1",
  "capsule_id": "sha256:<deterministic_manifest_sha256>",
  "profile": "needle|handoff|archive|custom",
  "target": {
    "adapter": "codex|claude-code|chatgpt|opencode|api|local",
    "surface": "CANON.md|AGENTS.md|CLAUDE.md|SOUL.md|inline|sidecar",
    "integration_tier": "enforced|native-advisory|guided|unsupported",
    "host_enforcement_observed": false
  },
  "source_state": {
    "records_digest": "sha256:...",
    "inventory_digest": "sha256:...",
    "context_envelope_digest": "sha256:...",
    "mneme_snapshot_digest": "sha256:...",
    "relay_checkpoint": "sha256:..."
  },
  "compatibility": {
    "record_schema_min": "canon.record/v1",
    "capsule_schema": "canon.capsule/v1",
    "requires_features": []
  },
  "budget": {
    "max_tokens": 0,
    "estimated_tokens": 0,
    "policy": "critical-atoms-lossless"
  },
  "layers": [],
  "atoms": [],
  "records": [],
  "conflicts": [],
  "unknowns": [],
  "omissions": [],
  "lossy_transforms": [],
  "freshness": [],
  "integrity": {
    "canonicalization": "json-sorted-compact-lf",
    "manifest_sha256": "..."
  },
  "receipts": [],
  "does_not_prove": []
}
```

`C: inferred`

### Deterministic versus event fields

The deterministic capsule manifest should exclude wall-clock event fields unless they are source facts already being hashed. Bootstrap time, receiving host, probe response, and observed enforcement belong in a separate witness. `C: inferred`

I0 already follows this split: deterministic manifest bytes are separated from receipt and run context. `C: verified`

## `CANON.md` proposal

### Role

`CANON.md` should be the human-readable target surface generated from `canon.capsule/v1`. It should be reproducible from the capsule and should contain enough visible state for an operator or receiving agent to detect omissions, stale facts, conflicts, and enforcement limits. `C: inferred`

### Required sections

Recommended deterministic order:

1. Capsule identity
2. Target and integration tier
3. Freshness, trust, and unknowns
4. Active goals
5. Authority, permissions, prohibitions, and constraints
6. Current frontier and working state
7. Decisions and rationale
8. Conflicts requiring resolution
9. Canonical instructions
10. Evidence references
11. Omissions
12. Lossy transforms
13. Bootstrap readiness probe
14. Does-not-prove

`C: inferred`

### Machine binding

`CANON.md` should carry a machine-verifiable binding to the capsule. Two safe options:

- Embed only the capsule digest and path/reference to a sidecar capsule.
- Embed a constrained frontmatter or fenced JSON carrier with the full canonical capsule for small profiles.

The existing vault/frontmatter codec shows that Canon already prefers an authoritative machine carrier over free-form visible body text. `C: verified` for the existing pattern, `C: inferred` for the proposed `CANON.md` design.

## Continuity atom types

Current record kinds are not enough to represent the pillar's required continuity semantics. `C: verified`

Recommended `canon.atom/v1` taxonomy:

| Atom type | Purpose | Current Canon mapping | Claim |
| --- | --- | --- | --- |
| `instruction` | Durable operating instruction | `personality-block` partial fit | `C: inferred` |
| `active-goal` | Current task/project objective that must survive handoff | none | `C: inferred` |
| `permission` | Explicit allowed action or authority grant | none | `C: inferred` |
| `prohibition` | Explicit disallowed action or safety boundary | none | `C: inferred` |
| `constraint` | Non-permission requirement such as no edit, no deploy, no secrets | none | `C: inferred` |
| `decision` | Accepted decision/rationale | `adr-decision` partial fit | `C: inferred` |
| `frontier-state` | Current working state, next unblocked action, open threads | none | `C: inferred` |
| `evidence-ref` | Reference to source artifact without copying raw body | `research-artifact-ref` partial fit | `C: inferred` |
| `episodic-fact` | Remembered event/fact with provenance and freshness | `episodic-memory` partial fit | `C: inferred` |
| `synthesized-persona` | L3 persona synthesis | `synthesized-persona-l3` | `C: inferred` |
| `conflict` | Unresolved contradiction or incompatible directives | V4 gate concept partial fit | `C: inferred` |
| `unknown` | Explicitly retained gap | none | `C: inferred` |
| `omission` | Typed budget, policy, or safety omission | none | `C: inferred` |
| `lossy-transform` | Summary/compaction/synthesis receipt | none | `C: inferred` |
| `bootstrap-probe` | Readiness challenge/check item | none | `C: inferred` |
| `bootstrap-witness` | Event receipt for bootstrap attempt | V4 witness concept partial fit | `C: inferred` |
| `adapter-capability` | Host adapter tier and constraints | backend capability tokens partial fit | `C: inferred` |

### Proposed atom fields

```json
{
  "atom_schema": "canon.atom/v1",
  "type": "active-goal",
  "id": "stable-id",
  "layer": "session|project|workspace|personal|org|imported",
  "scope_key": "opaque-or-path-clean-key",
  "precedence_rank": 0,
  "status": "active|retired|superseded|stale|untrusted|unknown",
  "value": {},
  "source_refs": [],
  "source_span_refs": [],
  "provenance": {},
  "freshness": {},
  "classification": "normative|descriptive|derived|receipt",
  "hashes": {}
}
```

`C: inferred`

## Authority, scope, precedence, conflict, and freshness semantics

### Authority

The pillar spec requires Canon to distinguish enforced, native advisory, guided, and unsupported integration tiers. No adapter may label advisory/guided behavior as enforced. `C: verified`

Therefore the capsule and witness must record both the advertised tier and evidence for that tier. If the host contract cannot block ordinary work until bootstrap completes, the adapter must not claim enforced ambient startup. `C: inferred`

Recommended authority representation:

- Authority atoms should be explicit, source-bound, and typed as `permission`, `prohibition`, `constraint`, `instruction`, or `active-goal`.
- Each authority atom should identify its source and current status.
- The compiler should fail rather than silently drop active permissions, prohibitions, critical constraints, active goals, unresolved conflicts, or explicit unknowns.

`C: inferred`

### Scope

Current Canon scope is exactly `global` or `workspace`. `C: verified`

The pillar needs richer target and authority scopes. Recommended capsule scopes:

- `session`
- `task`
- `project`
- `workspace`
- `repo`
- `personal`
- `team`
- `organization`
- `imported-history`

`C: inferred`

Compatibility note: introducing these scopes directly into `canon.record/v1` would break current validators and fixtures. Prefer a new atom layer or a `canon.record/v2` migration plan rather than silently widening v1. `C: inferred`

### Precedence

Current implemented precedence is workspace-over-global for personality blocks only. `C: verified`

Recommended capsule precedence:

1. Active task/session instruction
2. Explicit operator/user instruction
3. Project/repository instruction
4. Workspace instruction
5. Organization/team policy
6. Personal/global preference
7. Imported historical memory
8. External or untrusted reference

This order is a proposal, not current code. `C: inferred`

### Conflict

The pillar requires unresolved conflicts to remain visible and not be summarized away. `C: verified`

Current V4 reconcile already has a useful fail-closed conflict gate model for surface drift. `C: verified`

Recommended capsule conflict semantics:

- Contrary normative atoms produce `conflict` atoms.
- Unresolved conflict atoms are critical and cannot be omitted under budget.
- Conflict resolution must be explicit: `approved`, `edited`, `rejected`, or `pending`.
- Unknown or expired resolution fails closed.

`C: inferred`

### Freshness

Current Canon has record-level temporal fields and drift verification for surfaces. Mneme has current/as-of recall, source hashes, supersession, and provenance receipts. Index has context-envelope freshness receipts. Relay has ledger checkpoints and compaction verification. `C: verified`

The capsule should distinguish:

- `current`
- `stale`
- `superseded`
- `contradictory`
- `untrusted`
- `unknown`
- `blocked`

`C: inferred`

Freshness should be based on source-state identities and recheck commands where available, not only timestamps. `C: inferred`

## Omission and lossy-transform receipts

### Existing primitives

- Canon fidelity reports declared drops and field diffs for textblock/vault paths. `C: verified`
- Index context envelopes record retained and omitted items with explicit budget failure codes and source references, while avoiding raw source inclusion. `C: verified`
- Relay compaction records folded spans, kept head/tail/pinned policies, span hashes, summary hashes, and verification results. `C: verified`
- Mneme recall receipts bind hits to content hashes and recheck metadata. `C: verified`
- I0 receipts count dispositions, bytes, hashed bytes, failures, date coverage, duplicates, manifest digest, and does-not-prove statements. `C: verified`

### Required capsule rule

Every omission must be typed, counted, visible, and bound to the budget/safety/policy decision that caused it. Critical normative atoms must not be omitted; the capsule build must fail instead. `C: inferred`

Suggested `canon.omission/v1`:

```json
{
  "schema": "canon.omission/v1",
  "reason": "budget|secret|unsupported-adapter|policy|source-unavailable|parse-failed|invalid|duplicate|stale",
  "count": 0,
  "affected_ids": [],
  "affected_source_refs": [],
  "critical": false,
  "decision": "omitted|fail-build|reference-only",
  "does_not_prove": []
}
```

`C: inferred`

Suggested `canon.transform-receipt/v1`:

```json
{
  "schema": "canon.transform-receipt/v1",
  "transform": "summary|compaction|synthesis|projection|redaction|migration",
  "method_id": "stable-method-name-or-hash",
  "input_refs": [],
  "input_span_hash": "sha256:...",
  "output_ref": "atom-or-record-id",
  "output_hash": "sha256:...",
  "lossy": true,
  "retained_critical_atom_ids": [],
  "omissions": [],
  "verifier": "deterministic|human|model-assisted",
  "does_not_prove": []
}
```

`C: inferred`

## Bootstrap protocol, witness, and readiness probe

### Protocol

The pillar spec defines this ambient bootstrap lifecycle:

1. Detect entry.
2. Resolve layers.
3. Check freshness, trust, conflicts, budget, and reachability.
4. Compile or reuse capsule.
5. Present capsule plus unknowns and omissions.
6. Run readiness probe over critical goals, permissions, prohibitions, and current frontier.
7. Emit bootstrap witness with capsule identity, source-state identity, target surface, timestamp, checks, omissions, and readiness result.
8. Begin ordinary work only after visible bootstrap result.

`C: verified`

### Host enforcement boundary

This lifecycle is enforceable only where the receiving host exposes a blocking contract. In native advisory or guided hosts, the witness can show that bootstrap was presented and probed, but it cannot honestly prove that the host would block all ordinary work. `C: inferred`

### Proposed readiness probe schema

```json
{
  "schema": "canon.readiness-probe/v1",
  "probe_id": "stable-id",
  "capsule_id": "sha256:...",
  "target": {},
  "critical_sets": {
    "active_goal_ids": [],
    "permission_ids": [],
    "prohibition_ids": [],
    "constraint_ids": [],
    "frontier_state_ids": [],
    "unresolved_conflict_ids": []
  },
  "challenge": {
    "format": "json",
    "required_fields": [
      "active_goal_ids",
      "permission_ids",
      "prohibition_ids",
      "frontier_state_ids",
      "unresolved_conflict_ids"
    ]
  },
  "checker": {
    "method": "exact-id-set-and-status-match",
    "pass_threshold": "all-critical"
  }
}
```

`C: inferred`

### Proposed bootstrap witness schema

```json
{
  "schema": "canon.bootstrap-witness/v1",
  "run_id": "uuid-or-stable-event-id",
  "capsule_id": "sha256:...",
  "capsule_manifest_sha256": "sha256:...",
  "source_state": {},
  "target": {},
  "integration_tier_claimed": "enforced|native-advisory|guided|unsupported",
  "host_enforcement_observed": false,
  "started_at": "event-time",
  "checks": [
    {
      "name": "freshness|conflicts|secrets|budget|reachability|readiness",
      "verdict": "pass|fail|warn|blocked|unknown",
      "evidence_refs": []
    }
  ],
  "omissions": [],
  "lossy_transforms": [],
  "readiness_result": {
    "verdict": "pass|fail|blocked|unknown",
    "missing_ids": [],
    "mismatched_ids": []
  },
  "does_not_prove": []
}
```

`C: inferred`

## Versioning and migrations

### Current versioned schemas observed

- `canon.record/v1` in main Canon. `C: verified`
- `canon.history-manifest/v1` in the I0 worktree. `C: verified`
- `canon.history-receipt/v1` in the I0 worktree. `C: verified`
- `project-telos.context-envelope/v1` in Index. `C: verified`
- `relay.compaction/v1` in Relay. `C: verified`
- Mneme SQLite schema version 4 with migrations. `C: verified`

### Gap

Main Canon does not yet expose a general capsule migration framework, schema registry, or conformance CLI. `C: verified`

### Recommended rules

- `canon.record/v1` remains stable for the existing five-kind record envelope.
- `canon.atom/v1` and `canon.capsule/v1` are introduced as additive higher-level schemas.
- New required top-level fields require a new major schema name, such as `canon.capsule/v2`.
- Migrations must emit `canon.transform-receipt/v1` with before/after hashes.
- Schema fixtures must include both accepted and rejected examples.
- Migration tests must prove deterministic output from identical input bytes.

`C: inferred`

## Determinism

Verified deterministic primitives:

- Canon record JSON uses sorted key serialization. `C: verified`
- Canon layering orders records deterministically. `C: verified`
- Textblock source hashes and vault note names are deterministic for their input domains. `C: verified`
- SQLite audit chains and Relay session ledgers bind sequence order with hashes. `C: verified`
- I0 manifest bytes are sorted, compact canonical JSON with final newline. `C: verified`
- Index context envelopes include source refs, budget accounting, selection, and freshness receipts. `C: verified`
- Relay compaction is deterministic and verifiable against folded spans and summary hash. `C: verified`

Capsule determinism requirement:

- Identical source bytes, source declarations, compiler version, profile, and target adapter facts must produce the same capsule manifest digest.
- Wall-clock time, receiving host observation, and probe responses belong to witness receipts, not the deterministic manifest.
- If any source is unreachable or unsafe, the compiler must emit a typed omission or fail the build according to criticality.

`C: inferred`

## Conformance fixtures

### Existing fixtures

Main Canon has fixtures and tests for the five current record kinds, schema round trips, validation, layering, surfaces, fidelity, vault, drift, persona thesis, and reconcile. The main suite passed with 407 tests. `C: verified`

### Required new fixtures

Recommended fixture set for I0/core schema:

1. Minimal capsule with one instruction atom and no omissions.
2. Full handoff capsule with goals, permissions, prohibitions, frontier state, conflict, unknown, evidence refs, and readiness probe.
3. Budget-pressure capsule where non-critical descriptive atoms are omitted with receipts.
4. Budget-pressure capsule where critical atoms would be omitted and build fails.
5. Secret-quarantine I0 inventory fixture with no secret bytes in manifest, records, capsule, or `CANON.md`.
6. Stale/superseded/contradictory/untrusted/unknown freshness fixture.
7. Cross-adapter round trip fixture for enforced, advisory, guided, and unsupported tiers.
8. Relay compaction transform fixture mapped into capsule lossy-transform receipt.
9. Index context-envelope fixture mapped into capsule source refs and omissions.
10. Mneme provenance fixture mapped into atom source hashes and freshness.
11. Bootstrap witness pass fixture.
12. Bootstrap witness fail fixture for missing goal, permission, prohibition, conflict, or frontier state.
13. Migration fixture from `canon.record/v1` records into `canon.atom/v1`/`canon.capsule/v1`.
14. Malformed capsule fixtures for unknown schema, duplicate IDs, invalid hashes, critical omission, stale source-state digest, and tier overclaim.

`C: inferred`

## Failure modes

| Failure mode | Severity | Confidence | Claim | Evidence and mitigation |
| --- | --- | --- | --- | --- |
| Raw private conversation bodies copied into public repo or capsule | Critical | High | `C: inferred` | I0 design explicitly avoids body copy and protected roots. Gate: fixture with planted secrets and transcript bodies proves zero leaked bytes. |
| Critical goals, permissions, prohibitions, or conflicts silently summarized away | Critical | High | `C: inferred` | Pillar spec forbids silent summary of normative items. Gate: planted critical atom retention or fail-build. |
| Advisory/guided host advertised as enforced ambient bootstrap | Critical | High | `C: inferred` | Pillar spec defines tiers and forbids overclaim. Gate: adapter tier proof and witness field `host_enforcement_observed`. |
| Historical stale instruction promoted as current authority | High | High | `C: inferred` | I0 inventory is source reference, not authority. Gate: promotion receipt requires status/freshness and source span. |
| Capsule manifest nondeterminism from timestamps or unordered source discovery | High | Medium | `C: inferred` | I0 and Canon already use deterministic ordering patterns. Gate: repeated identical build hash. |
| Secret detector misses unknown credential format | Critical | Medium | `C: unknown` | No detector can prove complete coverage. Gate: known-secret fixture suite and path-class exclusion; final claim must say "does not prove no secrets exist." |
| Mneme adapter drops foreign provenance or arbitrary kinds without capsule visibility | High | High | `C: verified` | Mneme backend declares these drops. Gate: adapter drops are included in capsule omission/transform receipts. |
| Flywheel temporal loss corrupts current/superseded semantics | High | High | `C: verified` | Flywheel backend declares temporal drop and refuses live temporal unless flattened. Gate: temporal fixture across adapters. |
| Reconcile write path is not transactional across all filesystem seams | Medium | Medium | `C: inferred` | Runner plans before write but filesystem commit can still fail mid-run. Gate: witness captures partial write failure and retry state. |
| Index MCP timeout blocks envelope construction in large dirty workspace | Medium | High | `C: verified` | Narrow context-envelope requests timed out in this audit. Gate: bounded source selection, cache, and timeout receipt. |
| Parallel worktrees create divergent IDs or source-state ambiguity | Medium | High | `C: inferred` | I0 is in a parallel untracked worktree and main repo is separate. Gate: source-state includes repo/worktree identity and commit/dirty digest. |
| `CANON.md` free-form body diverges from capsule carrier | Medium | Medium | `C: inferred` | Vault precedent treats frontmatter carrier as authoritative. Gate: render/ingest consistency and embedded manifest digest. |
| Raw Relay transcript APIs are used as public evidence surfaces | Critical | Medium | `C: verified` interface, `C: inferred` risk | Relay transcript can expose message bodies. Gate: capsule uses ledger checkpoints/source refs, not transcript bodies, unless explicitly authorized and redacted. |

## Dependencies and sequencing

### Internal dependencies

- I0 inventory lane must be reviewed and landed before the capsule compiler depends on history manifests. `C: inferred`
- Canon schema fixtures should be extended before implementation work on compiler/renderers. `C: inferred`
- Security/privacy audit gates must define the public-clean, secret, and private-body boundaries before I0 real runs feed capsule artifacts. `C: inferred`
- Platform adapter lane must verify host integration tiers before any claim of enforced bootstrap. `C: inferred`
- Continuity/UX lanes should align on `CANON.md` sections and readiness probe presentation. `C: inferred`

### External/interface dependencies

- Index can supply source refs, budget omissions, and freshness receipts. `C: verified`
- Relay can supply session checkpoints and lossy compaction receipts. `C: verified`
- Mneme can supply memory provenance, current/as-of state, and source-hash grounding. `C: verified`
- Existing Canon SQLite/vault/surface paths can supply deterministic storage and fidelity patterns. `C: verified`

## Acceptance gates

These gates should block I0/core-schema completion:

1. `canon.capsule/v1` JSON schema or equivalent validator exists with positive and negative fixtures. `C: inferred`
2. `canon.atom/v1` schema exists for goals, permissions, prohibitions, constraints, conflicts, unknowns, evidence refs, omissions, transform receipts, and bootstrap probes. `C: inferred`
3. Deterministic capsule build produces identical manifest hash for identical source bytes/profile/adapter facts. `C: inferred`
4. `CANON.md` render is reproducible from the capsule and contains the capsule digest. `C: inferred`
5. `CANON.md` parser or verifier detects digest/body/carrier drift. `C: inferred`
6. 100 percent of planted active goals, permissions, prohibitions, constraints, unresolved conflicts, and frontier atoms survive all supported profiles or the build fails. `C: inferred`
7. Every omission is typed, counted, visible, and source-bound where possible. `C: inferred`
8. Every lossy transform has input refs, transform method, input/output hashes, and does-not-prove text. `C: inferred`
9. I0 inventory outputs contain no raw private conversation bodies by default. `C: inferred`
10. Planted secret fixtures do not appear in manifest, records, capsule, witness, or `CANON.md`. `C: inferred`
11. Host integration tier cannot be set to `enforced` without adapter evidence that ordinary work is blocked before bootstrap success. `C: inferred`
12. Bootstrap witness records capsule identity, source-state identity, target surface, adapter tier, checks, omissions, readiness result, and does-not-prove. `C: inferred`
13. Readiness probe fails when any planted critical goal, permission, prohibition, unresolved conflict, or frontier atom is missing or misclassified. `C: inferred`
14. Capsule compiler distinguishes stale, superseded, contradictory, untrusted, unknown, and blocked facts. `C: inferred`
15. Adapter conformance tests declare and verify loss across textblock, vault, SQLite, Mneme, Flywheel, Index, and Relay paths. `C: inferred`
16. Migration receipts prove before/after hashes and deterministic conversion from prior schemas. `C: inferred`
17. I0 CLI refuses output under the repository and refuses plan digest mismatch without mutation. `C: verified` in I0 worktree tests, `C: inferred` as mainline acceptance gate.
18. Main Canon suite stays green. Current baseline: 407 tests passed. `C: verified`

## Explicit unknowns and blocked items

- Exact strongest integration tier for each host is owned by the platform adapter lane and was not verified here. `C: unknown`
- Exact host hooks that can enforce ambient startup are not established in this audit. `C: unknown`
- Private I0 source plans and protected real-run outputs were intentionally not inspected because they may contain sensitive path and history information. `C: blocked`
- Whether the untracked I0 worktree passes its own full test suite was not verified in this audit. The main Canon suite was verified. `C: unknown`
- Final atom taxonomy and precedence ladder require maintainer/operator approval before implementation. `C: unknown`
- Final `CANON.md` UX, accessibility, and copy hierarchy belong partly to UX/platform lanes. `C: unknown`
- Final public package name, release governance, and conformance mark policy belong partly to community/release lanes. `C: unknown`
- Secret detector completeness cannot be proven. Only known patterns and path classes can be tested. `C: unknown`
- Full server-side provider histories are outside local evidence unless exported or referenced by an authorized connector/source plan. `C: unknown`

## Now / Next / Later

### Now

- Land this audit artifact only. `C: verified`
- Freeze the proposed v1 schema surface for review: `canon.atom/v1`, `canon.capsule/v1`, `canon.omission/v1`, `canon.transform-receipt/v1`, `canon.readiness-probe/v1`, and `canon.bootstrap-witness/v1`. `C: inferred`
- Treat I0 as protected inventory/reference input only, not automatic memory promotion. `C: inferred`
- Write conformance fixtures before product implementation. `C: inferred`
- Define critical-atom retention gate for goals, permissions, prohibitions, constraints, unresolved conflicts, and frontier state. `C: inferred`
- Require adapter-tier evidence before any enforced bootstrap claim. `C: inferred`

### Next

- Implement deterministic capsule compiler over existing `canon.record/v1` records plus I0 artifact refs. `C: inferred`
- Implement deterministic `CANON.md` renderer/verifier with capsule digest binding. `C: inferred`
- Add capsule validator and conformance CLI. `C: inferred`
- Add migration receipts for record-to-atom and old-capsule-to-new-capsule transforms. `C: inferred`
- Integrate Index source refs/freshness receipts, Relay compaction receipts/checkpoints, and Mneme provenance/currentness receipts through adapters with declared drops. `C: inferred`
- Build host adapter tier probes and witness checks for enforced/native-advisory/guided/unsupported environments. `C: inferred`

### Later

- Publish third-party conformance fixtures and a compatibility badge only after gates pass. `C: inferred`
- Add branch-aware three-way merge and conflict resolution for divergent worktrees. `C: inferred`
- Add sealed evidence archives and selective disclosure for protected histories. `C: inferred`
- Add optional model-assisted synthesis only behind source-span and transform-receipt gates. `C: inferred`
- Add enterprise governance surfaces for ownership, retirement, retention, and audit export. `C: inferred`
- Add accessible web preview for capsule and `CANON.md` inspection after UX/platform alignment. `C: inferred`

