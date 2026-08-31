# Task 7 report: Canon continuity capsule

## Scope

- Base verified before edits: `3284cf0dd50545c95817c4ed0902554af6907b4e`.
- Worktree branch: `codex/canon-continuity-foundation`.
- Owned source/test files changed:
  - `src/canon/capsule.py`
  - `tests/test_capsule.py`
  - `tests/fixtures/foundation/capsule_minimal_needle.json`
  - `tests/fixtures/foundation/capsule_handoff_full.json`
  - `.superpowers/sdd/2026-08-30-canon-foundation/task-7-report.md`
- No controller, plan, ledger, export, docs/metadata, README, or pyproject edits were made.
- No index/forum connector calls were used.

## Specification sources read

- Full `.superpowers/sdd/2026-08-30-canon-foundation/task-7-brief.md`.
- Relevant Foundation plan sections in `docs/superpowers/plans/2026-08-30-canon-foundation.md`: global constraints, schema rules, fixture content, and Task 7 requirements.
- Relevant continuity design sections in `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`.
- Local dependency modules and tests for atoms, records, omissions, transforms, readiness probes, validators, witnesses, canonical JSON, and descriptors.

## TDD record

Behavioral tests were written before implementation, then a minimal importable scaffold was added only after the first real red.

Recorded failures:

1. `python -m pytest -p no:cacheprovider tests/test_capsule.py -q`
   - Result: collection error, `ModuleNotFoundError: No module named 'canon.capsule'`.
2. Same focused command after minimal scaffold:
   - Result: 13 behavioral failures and 1 pass, primarily `NotImplementedError` from unimplemented behavior.
3. Fixture-lock tests added only after behavioral green:
   - Result: 3 failures from missing `capsule_minimal_needle.json` and `capsule_handoff_full.json`.
4. Manual-ordering validator test:
   - Result: failure because manual unsorted omissions and receipts were not yet rejected.
5. Malformed value-object preservation test:
   - Result: failure because `Compatibility.from_dict` silently defaulted missing fields instead of preserving malformed input for total validation.

Final focused capsule result:

- `python -m pytest -p no:cacheprovider tests/test_capsule.py -q`
- Result: 19 passed.

## Implementation summary

- Added `canon.capsule` with immutable value objects for capsule target, source state, compatibility, budget, integrity, capsule, compile request, and bundle.
- Implemented `build_capsule` for deterministic capsule construction from explicit atoms and record-derived atoms.
- Implemented stable canonical bytes and digest identity rules:
  - canonicalization: `json-sorted-compact-lf`
  - digest input blanks `capsule_id`
  - digest input blanks `integrity.manifest_sha256`
  - `capsule_id` and `integrity.manifest_sha256` bind to the same digest
- Implemented copy-safe tuple/deep-copy behavior for nested mutable values.
- Implemented total validation that reports multiple malformed fields and preserves malformed nested values through `from_dict`.
- Implemented deterministic ordering for atoms, records, omissions, lossy transforms, and opaque receipts.
- Preserved critical atom requirements and rejected critical omission marked as omitted.
- Preserved compatibility, budget, source-state, freshness, conflict, unknown, and does-not-prove semantics from the brief.
- Did not implement Task 8 render/compile convenience APIs.

## Fixture outputs

- `capsule_minimal_needle.json`
  - byte-identical regeneration verified
  - digest: `sha256:6320b9e64430c5054b4a452fa5e7c241182a3d77e3c373f0670e7deb4524e5ac`
- `capsule_handoff_full.json`
  - byte-identical regeneration verified
  - digest: `sha256:ff070de3eb5db0366cf84e4dbff94ec75cd5778dbe918fd2866e5a86b8abe712`

## Verification

- Baseline before edits: `python -m pytest -p no:cacheprovider` -> 552 passed.
- Focused capsule: `python -m pytest -p no:cacheprovider tests/test_capsule.py -q` -> 19 passed.
- Relevant slice: `python -m pytest -p no:cacheprovider tests/test_canonical_json.py tests/test_atom.py tests/test_descriptors.py tests/test_readiness.py tests/test_witness.py tests/test_capsule.py -q` -> passed.
- Full suite: `python -m pytest -p no:cacheprovider` -> 571 passed in 1.42s.
- No-write syntax compile: passed.
- Fixture byte/digest regeneration: passed for both fixtures.
- Size gate:
  - `src/canon/capsule.py`: 489 lines, no function over 50 lines.
  - `tests/test_capsule.py`: 373 lines, no function over 50 lines.
- External dependency scan: no matches.
- Task 8 leakage scan: no `compile_capsule`, `render_canon_md`, or `canonmd` matches.
- Secret/local-path scan over owned source/test/fixtures: no matches.
- Index/forum call/import scan over owned source/test/fixtures: no matches.
- Protected-scope diff check for README, pyproject, project docs, plan docs, exports, and ledger: no output.

## Blockers and concerns

- Blockers: none.
- Concern: `src/canon/capsule.py` is close to the 500-line ceiling at 489 lines. Future capsule work should split helper logic or move Task 8 behavior into its own module instead of extending this file.
