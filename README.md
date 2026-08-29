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
per-scope layering. F1 adds the storage seam: a `MemoryBackend` protocol with
capability tokens and four adapters, among them a zero-drop SQLite reference and
injected-handle adapters for a memory fact-engine and an authored-block store.
R0 adds the block round-trip gate: a byte-exact region boundary inside a managed
file, a record-to-text renderer and its inverse, and a go/no-go verdict that
proves a block set round-trips to its canonical form with every dropped field
declared.

canon does not yet reach into your real instruction files and rewrite them. That
renderer is the next phase. Everything shipped is proven by a full test suite and
aims at the one envelope.

## Run it

```bash
python -m pytest
```

No runtime dependencies. Python 3.11 or newer.

## Layout

```
src/canon/
  schema.py, validator.py, layering.py   the record, its rules, per-scope resolve
  backends/                              the storage seam and four adapters
  region.py, textblock.py, fidelity.py   the byte boundary, the text codec, the gate
tests/                                   round-trip, validator, layering, backend,
                                         and fidelity proofs, with fixtures
project-docs/                            the F0, F1, and R0 specs and decisions
```

See `project-docs/` for the schema reference, the layering derivation, the
section-ownership contract, the declared drops each storage backend must
announce, and the R0 decisions behind the round-trip gate.

## License

FSL-1.1-MIT. Functional Source License, source-available now for any purpose
other than a competing product, and it converts to the MIT license two years
after each version is released. See `LICENSE`.
