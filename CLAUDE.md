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

Later phases (verifier, migration legs, region installation, GEMINI.md and
SOUL.md surfaces) aim at this same envelope. Each lands on its own branch.

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
