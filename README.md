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

R1 renders your files from the record. It resolves the block set for a file's
scope and rewrites only the region canon owns, every byte outside it preserved.
It writes only a fixed allow-list of files, and only a file you have opted in
with a canon region. Where a tool reads both a global and a workspace file, the
workspace file carries just your workspace blocks, so a shared block is never
duplicated; where a tool reads one file, that file carries the full resolved set.

R2 mirrors your whole record set into an Obsidian vault. Each record becomes one
markdown note you can read, search, and link, and a MEMORY.md index lists them
all. The full record rides inside every note, so a rebuild is exact and editing a
note's prose never rewrites the record behind it. canon writes only inside its own
vault, never touches a file it did not write, and when you drop a record it
reports the note left behind rather than deleting it. R2 also adds SOUL.md to the
rendered surfaces.

Installing a region into a fresh file, the verifier, and the global SOUL.md and
GEMINI.md surfaces are later phases. Everything shipped is proven by a full test
suite and aims at the one envelope.

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
  surface.py, registry.py                the render composition, the write allow-list
  frontmatter.py, vault.py               the note frontmatter codec, the one-record note
  vault_mirror.py, vault_fidelity.py     the whole-vault mirror and its round-trip gate
tests/                                   round-trip, validator, layering, backend,
                                         fidelity, surface, orchestration, and vault proofs
project-docs/                            the F0, F1, R0, R1, and R2 specs and decisions
```

See `project-docs/` for the schema reference, the layering derivation, the
section-ownership contract, the declared drops each storage backend must
announce, and the R0 and R2 decisions behind the round-trip and vault gates.

## License

FSL-1.1-MIT. Functional Source License, source-available now for any purpose
other than a competing product, and it converts to the MIT license two years
after each version is released. See `LICENSE`.
