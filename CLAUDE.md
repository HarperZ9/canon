# CLAUDE.md — canon

> Model-facing, self-contained. This repo is cloned and operated on its own; it
> does not inherit the `c:\dev` workspace canon. Anything from the workspace or
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
F0 (this slice) ships the record of record and nothing that writes a file:
- `src/canon/schema.py` — the canonical envelope, five kinds, provenance,
  temporal block, `to_dict`/`from_dict` (field-identical round-trip).
- `src/canon/validator.py` — `validate_record(rec) -> list[str]`, semantic rules.
- `src/canon/layering.py` — `resolve_blocks(pool, scope)`, per-scope override.
- `project-docs/` — the F0 specs: schema, layering, section-ownership,
  declared-drops (cited to real code), decisions.

Later phases (storage backends, renderer, verifier, migration legs) aim at this
envelope. They are planned in the workspace assessment, not built here yet.

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
