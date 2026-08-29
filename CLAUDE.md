# CLAUDE.md — canon

> Model-facing, self-contained. This repo is cloned and operated on its own; it
> does not inherit a workspace-level canon. Anything from the workspace or
> global standards this repo needs is copied here in this repo's own register.

## What canon is
A provider-neutral memory-bank and personality container. One canonical record
envelope that every harness (Claude Code, Claude CLI, ChatGPT, Codex, web
surfaces) and every store draws from and writes to. It unifies the scattered
instruction+personality files (CLAUDE.md / AGENTS.md / SOUL.md / GEMINI.md) and
session memories under a single typed record, then renders each surface's file
from that record deterministically.

canon is an assembly over existing engines, not a rewrite: mneme is the memory
fact-engine of record, flywheel's store holds authored blocks, relay is the
cross-provider transport. canon adds the one envelope they aim at, the per-scope
layering that resolves the block set, and the deterministic renderer.

## Build state
F0 ships the record of record and nothing that writes a file:
- `src/canon/schema.py` — the canonical envelope, five kinds, provenance,
  temporal block, `to_dict`/`from_dict` (field-identical round-trip).
- `src/canon/validator.py` — `validate_record(rec) -> list[str]`, semantic rules.
- `src/canon/layering.py` — `resolve_blocks(pool, scope)`, per-scope override.
- `project-docs/` — the F0 specs: schema, layering, section-ownership,
  declared-drops (cited to real code), decisions.

F1 adds the storage seam and nothing that renders a file:
- `src/canon/backends/base.py` — the `MemoryBackend` Protocol, the five
  capability tokens, `record_key`/`split_key`, and `guard_put` (refuse on kind
  mismatch or a record-enforceable dropped capability).
- `src/canon/backends/{files,sqlite,mneme,flywheel}.py` — the four adapters.
  sqlite is the zero-drop reference with a re-verifiable audit chain; mneme and
  flywheel map onto an injected, duck-typed store handle and import no engine.
- `project-docs/F1-BACKENDS.md`, `F1-DECISIONS.md` (D-7 encryption-at-rest null,
  D-8 refuse-not-flatten, D-9 injected handle, D-10 mneme's temporal boundary as a
  loud put-time refusal, D-11 the fake mirrors mneme's INSERT OR REPLACE); Drop 4
  and the Status note in `F0-DECLARED-DROPS.md`.

R0 is the block round-trip go/no-go gate, the first band that turns a record into
bytes and reads it back:
- `src/canon/region.py` — the byte boundary. `extract_region`/`splice_region`
  partition a managed file into `prefix + inner + suffix` with a byte-exact
  identity; only `inner` is canon's to rewrite, and a file with no marker is
  off-limits, not an error.
- `src/canon/textblock.py` — the record-to-text layer. `render_region` projects a
  scope-homogeneous block set into the region interior and refuses any record it
  cannot represent; `ingest_region` reads records back and speaks the same
  grammar. render's refusal set is a strict superset of ingest's constraints.
- `src/canon/fidelity.py` — `roundtrip_report`, the go/no-go verdict: round-trip
  to canonical form, render idempotence, outside-byte preservation across the
  host encoding matrix, and a structural drop ledger that fails closed on any
  undeclared loss. The gate returns a verdict for any constructible record and
  never propagates an exception.
- `project-docs/R0-DECISIONS.md` — D-12 one-LF line model, D-13 render-superset
  invariant, D-14 total gate, D-15 diff-against-raw ledger, D-16 the audit-driven
  refusal of constructible-but-malformed records, and the recorded audit (six
  findings checked, five confirmed and folded in TDD-style, one refuted).

R1 is the surface renderer, the first band that reaches a live host file and
rewrites it:
- `src/canon/surface.py` — the render composition. `render_surface` resolves the
  pool for a scope, projects the effective (mixed-origin) set onto that scope,
  and renders the region interior; `apply_surface` splices it into a host file
  and refuses before writing if the host has no canon region (off-limits) or its
  region's declared scope does not match the target scope.
- `src/canon/registry.py` — the write-surface allow-list and the orchestrator. A
  fixed, path-clean catalog binds each `(harness, scope)` to a root-kind and a
  relative path, with the absolute roots injected at call time. `write_surface`
  renders one surface through injected IO and writes only a changed region;
  `write_surfaces` renders a harness's whole set by the authored-split rule and
  fails closed on a non-catalog surface or a disallowed path before any write.
- `project-docs/R1-DECISIONS.md` — D-17 project-before-render, D-18 the
  off-limits and mis-scope refusals, D-19 the path-clean injected-root catalog,
  D-20 the lexical allow-list guard, D-21 the authored-split rule for a two-file
  harness (operator ruling), D-22 off-limits as a reported skip with a
  fail-closed batch.

R2 is the vault band. R1 splices a scope's blocks into a shared instruction file;
R2 mirrors the whole pool into an Obsidian vault of one note per record, plus a
MEMORY.md index, and adds the SOUL.md instruction surface:
- `src/canon/frontmatter.py` — a constrained frontmatter codec. It emits a fixed
  set of single-quoted scalars and one authoritative `canon:` key carrying
  `record.to_json()` verbatim, and it reads only that key back. No YAML loader
  runs on ingest, so the `!!python/object` trap is inert.
- `src/canon/vault.py` — the one-record note codec. `render_note` projects a
  record to a whole markdown file (frontmatter carrier, heading, per-kind body,
  `## canon links` trailer) and refuses any record it cannot faithfully project;
  `ingest_note` reconstructs the record from the carrier JSON alone, so a
  hand-edited body never changes the record. Identity, not content, names the
  file: the path digests the `(scope, id)` key, so a hostile id cannot forge one.
- `src/canon/vault_mirror.py` — the whole-vault orchestrator. `plan_vault`
  renders the pool into contained note paths plus the hub, plans the whole set
  against what is on disk, and commits only once nothing refuses. A file that is
  not a canon note is off-limits and never clobbered; a stale note is reported as
  an orphan and never deleted.
- `src/canon/vault_fidelity.py` — the vault round-trip verdict. The note carrier
  is lossless, so its declared-drop ledger is empty and any field difference is
  an undeclared loss that fails the verdict closed.
- `src/canon/registry.py` — extended with the SOUL.md surface (a fourth catalog
  row, harness `hermes`), a lone workspace surface that renders the merged set
  through the R1 authored-split renderer unchanged, with no banner.
- `project-docs/R2-DECISIONS.md` — D-23 the constrained codec (no YAML loader),
  D-24 the whole-file note carried by one JSON line, D-25 links from relations not
  body prose, D-26 the hub reuses the surface sort key, D-27 the authoritative
  carrier and one-way body, D-28 the fixed frontmatter key order, D-29
  identity-not-content names the file, D-30 the off-limits and spoof refusals,
  D-31 the lexical vault containment, D-32 orphan reported never deleted, D-33 the
  render-superset invariant carried to the vault leg, D-34 the non-durable hub
  marker, D-35 the vault is not a registry root-kind, D-36 SOUL reuses the R0
  grammar with no banner.

V2 is the first verify band over the render legs. It writes nothing; it ships two
read-only gates a build keys on:
- `src/canon/drift.py` — the rendered-surface drift check. `surface_drift`
  re-derives a managed surface from the pool (R1's clock-free render composition,
  so byte-stable) and compares the derived region interior to what is on disk, a
  sha256-keyed verdict per surface (match, drift, off-limits, refused, missing).
  It scores canon-owned bytes (the interior between the markers), so an edit to
  the host's own prose outside the markers is never drift, and it mirrors the
  batch writer `write_surfaces` through `pool_for`, so a merged workspace file is
  flagged. `drift_report` maps the catalog and `drift_exit_code` gates a build.
- `src/canon/writing_gate.py` — the injected STE seam. canon is stdlib-only and
  the linter (`check_writing.py`) lives outside this repo, so the caller wires
  the checker; canon owns the `WritingChecker` shape, the per-surface profile
  register, and the `gate_text` pipeline. A file passes iff the checker reports
  an empty `hard` list, the exact signal `check_writing --gate` keys on. The
  register binds each surface to a profile (instruction files `readme`, SOUL.md
  `chat`); the strict `procedure` profile is unused here (an honest null).
- `project-docs/V2-DECISIONS.md` — D-37 the profile-per-surface register, D-38
  the injected gate seam, D-39 the empty-hard-list pass signal, D-40 drift scores
  the interior and mirrors the batch writer (and why `pool_for` went public),
  D-41 the sha256-keyed verdict with the catalog as manifest, D-42 both gates
  total and read-only.

V3 is the second verify band. It writes nothing; it ships one read-only adapter
that hands a persona's basis to the external crucible engine for a witnessed
drift verdict:
- `src/canon/persona_thesis.py` — the persona-as-crucible-thesis drift adapter. A
  `synthesized-persona-l3` record is a synthesis claim (this text faithfully
  summarizes these source memories), and canon has no model to re-run that
  synthesis, so it measures drift structurally from the pool on two clock-free
  axes: basis-present (every source id still resolves to a record) and
  basis-current (no source id is superseded by a newer record). `persona_thesis`
  frames the two axes as falsifiable claims carrying model-free measurements,
  `thesis_payload` serializes the thesis for the injected assessor, and
  `assess_persona` runs the assessor and folds crucible's counts into a headline
  `DriftVerdict` (any drift reads DRIFT, else any unverifiable reads UNVERIFIABLE,
  else MATCH), read by direct index so a malformed assessment is a wiring fault,
  not a silent MATCH. The assessor is an injected seam, so canon imports no
  engine; the basis is a set, so a repeated source id is one source.
- `project-docs/V3-DECISIONS.md` — D-43 persona drift measured from the basis
  model-free (never re-synthesized), D-44 the injected crucible-assessor seam,
  D-45 the strict basis tolerance encodes integer-zero as 0.5, D-46 a proven
  drift outranks an honest null (counts read fail-closed), D-47 an empty basis is
  UNVERIFIABLE not MATCH, D-48 the surface-drift-as-thesis bridge scoped out
  (honest null), D-49 the basis is a set (duplicate source ids deduped), D-50 the
  documented caller-wiring corrected and verified out-of-suite, plus the recorded
  audit.

Later phases (verifier, migration legs, region installation, the global SOUL.md
and GEMINI.md surfaces) aim at this same envelope. Each lands on its own branch.

## Working rules
- Python 3.11+. Standard library only in F0; no runtime dependencies.
- TDD. Every change lands with a test that asserts something meaningful.
- Quality gates: no source file over 300 lines, no function over 50 lines.
- Run the slice with `python -m pytest`. The full F0 suite runs in well under a
  second; run it on every change.
- Never commit `.env`. Secrets go in `.env`, template in `.env.example`.
- Branch before committing. Do not push, open a PR, or deploy without an
  explicit go.

## The one envelope (F0 contract)
A record is `{canon_schema, kind, id, scope, data, provenance, temporal}`.
- `kind` is one of: personality-block, episodic-memory, synthesized-persona-l3,
  adr-decision, research-artifact-ref.
- `scope` is `global` or `workspace`. There is no `repo` scope: the ~90 per-repo
  instruction files stay hand-authored (the self-contained-repo invariant).
- `provenance` carries `harness` + `source_hash` (both required) and a clock-free
  `create_ord` used for deterministic ordering; wall-clock `create_time` is
  nullable and never authoritative.
- `temporal` (supersede / valid_until) is present only on the four temporal
  kinds; a research-artifact-ref must not carry one.
