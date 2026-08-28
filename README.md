# canon

One record for your memory bank and your personality, shared across every model
and every tool.

You keep the same working relationship whether you open Claude Code, Claude CLI,
ChatGPT, Codex, or a web surface: the same authored voice, the same accumulated
memory, the same decisions. Today that lives in a dozen files with a dozen
shapes (`CLAUDE.md`, `AGENTS.md`, `SOUL.md`, `GEMINI.md`) plus per-tool memory
stores that do not talk to each other. canon gives all of them one typed record
to draw from and write back to, and renders each tool's file from that record.

## What it does

- **One envelope, five kinds.** An authored personality block, a raw or extracted
  memory, a synthesized persona, a decision record, and a reference to an
  external research artifact all share one record shape with a provenance
  receipt on every entry.
- **Two scopes that layer.** A `global` block is your default everywhere; a
  `workspace` block with the same id overrides it where that workspace applies.
  A render resolves the effective set for its target, current entries only.
- **Deterministic by construction.** Ordering uses a clock-free ordinal, so a
  rebuild from the same records is byte-identical. The wall clock is kept only
  as a non-authoritative convenience.
- **An assembly, not a rewrite.** canon aims at proven engines rather than
  replacing them: a memory fact-engine, an authored-block store, and a
  cross-provider transport. It adds the one record they share and the renderer
  that projects each surface.

## Status

F0 is the record of record: the canonical schema, its validator, and the
per-scope layering, with a full test suite. It writes no files yet — storage
backends, the renderer, the verifier, and the migration legs are the phases
that follow, each aiming at this envelope.

## Run it

```bash
python -m pytest
```

No runtime dependencies. Python 3.11 or newer.

## Layout

```
src/canon/         schema.py, validator.py, layering.py
tests/             round-trip, validator, and layering proofs + fixtures
project-docs/      the F0 specs: schema, layering, ownership, drops, decisions
```

See `project-docs/` for the schema reference, the layering derivation, the
section-ownership contract, and the declared drops each storage backend must
announce.
