# Canon feature recovery contract inventory, 2026-09-18

Repo: `C:/dev/worktrees/canon-shipping-reconciliation-20260918`
Branch: `codex/canon-shipping-reconciliation-20260918`
Base: current `origin/main` at `8c6a8228ce2117112c5dad74ddb0450ba80aa8ff`
Seed commit on this branch: `d439fff93cb2aed96b938ea03de54665b00f75f9`
Comparison branch: `C:/dev/worktrees/canon-integration`, `integration/canon-flagship` at `b9df9854b22f59994e218c36ee2e68d0929ef121`

Current main keeps the newer MCP and shared-context capture surface. The stale integration tree cannot be replayed as a whole because its final tree lacks current-main files such as `src/canon/local_mcp.py`, `src/canon/context_*.py`, `src/canon/client_capture*.py`, `docs/shared-context.md`, `docs/client-capture.md`, `examples/shared-context-hooks/*`, `MANIFEST.in`, and the current `CHANGELOG.md`. Recovery must therefore port contracts, not branch shape.

## Current-main command surface

Current main exposes `mcp`, `check`, `blocks`, `init`, `compile`, `preview`, `export`, `undo`, and `bootstrap`. The newer read-only MCP door and shared-context capture/query files are present and must stay present. Current main has no standalone `rescue` command, no CLI-backed `doctor` command beyond the read-only MCP readiness tool name, and no library modules for import review, replay, retention, or run locks.

## Contract inventory

### Source-safe source reads

Branch-only source: `src/canon/source_safe_read.py` plus the `cli_artifacts.read_source_file` call site.

Contract: after a source path passes `resolve_under_root`, the actual file bytes are read by reopening the relative path from the checked workspace identity. Symlink or reparse components, workspace root identity drift, nonregular targets, invalid relative paths, oversized files, and unsupported safe backends fail closed with existing public failure codes. This protects compile, preview, export, doctor, and rescue source ingestion from a post-validation parent swap.

Status here: ported as the first recovery chunk. The red case was a nested source directory swapped to an outside directory symlink after `resolve_under_root`; current main returned success before the port and now returns `unsafe_path`. This keeps current MCP/context files untouched.

### Doctor diagnostics

Branch-only source: `src/canon/doctor.py` plus parser and CLI wiring.

Contract: `canon doctor` validates target descriptors, workspace/source reachability, source parsing, secret quarantine, expected source-state drift, offline unknown status, and unsupported lifecycle status without mutating the workspace. It returns sanitized findings with stable severities and failure codes. Its test suite also asserts hostile repr/input handling and no raw secret/path leaks.

Current-main overlap: the MCP `canon.doctor` tool is a block-loader readiness report. That is not the same contract as the branch CLI doctor, so a port must either add a distinct CLI path or explicitly reconcile naming with the MCP tool.

### Rescue handoff artifacts

Branch-only source: `src/canon/cli_rescue.py`, `src/canon/rescue.py`, `src/canon/rescue_artifacts.py`, and `src/canon/rescue_output.py`.

Contract: `canon rescue` builds a deterministic rescue bundle from explicit local records, atoms, target, profile, transcript summary, failure code, and run metadata. It emits safe metadata, does-not-prove text, source-state evidence, and optional artifacts without raw transcript leakage. Output publication is conflict-aware and sanitized.

Current-main overlap: current `export` already has stdout, bundle, region, undo, and safe publish behavior. Rescue should reuse current compile/export helpers and the source-safe read port, not copy stale export behavior over current main.

### Import review

Branch-only source: `src/canon/import_policy.py`, `src/canon/import_review.py`, and `src/canon/import_review_safety.py`.

Contract: imported atoms are default-denied unless trust, disclosure, locality, source-state, replay, secret quarantine, and duplicate checks all pass. Accepted review mutates replay state only after the full batch preflight succeeds. Findings aggregate policy, secret, source-state, replay, and shape failures without leaking raw content.

Current-main overlap: current schema and atom validation exist, but there is no import-review policy surface. This is a library contract and should land before any import command surface.

Status here: ported as the fourth recovery chunk. The red case was the branch import policy and review suites failing collection because `canon.import_policy` and `canon.import_review` were absent; after the port they pass focused import tests. This adds no command surface and keeps import activation default-denied unless all checks pass.

### Replay

Branch-only source: `src/canon/replay.py`.

Contract: replay claims bind capsule hash, nonce, and expiration into a stable key; stale, duplicate, malformed, subclassed, or hostile seen-set inputs fail closed before mutating replay state.

Current-main overlap: no current module. This is a small dependency for import review and can be ported independently before import-review.

Status here: ported as the second recovery chunk. The red case was the branch replay test suite failing collection because `canon.replay` was absent; after the port it passes focused replay tests. This adds no command surface and does not touch MCP/context capture.

### Retention

Branch-only source: `src/canon/retention.py`, `src/canon/retention_receipts.py`, and `src/canon/retention_safety.py`.

Contract: retention planning validates policy shape and identifiers, derives tombstone and purge plans, records omissions and transform receipts, and explicitly plans derived artifacts without deleting data. It preserves deterministic ordering and avoids retaining content hashes unless policy allows them.

Current-main overlap: current omission and transform receipt modules exist, but there is no retention planner. This should land as a library contract before it is composed into import review.

Status here: ported as the third recovery chunk. The red case was the branch retention test suite failing collection because `canon.retention` was absent; after the port it passes focused retention tests. This adds no command surface and performs no deletion.

### Concurrency/run locks

Branch-only source: `src/canon/concurrency*.py` except the shared `concurrency_windows_api.py`, which already exists on current main.

Contract: acquire and release named run locks under `.canon-locks` through stable parent capabilities. The implementation rejects bad lock names, symlink or reparse lock roots, directory swaps, fake backend namespace swaps, ownership mismatches, and unsafe release paths. Failed release retains retryable custody instead of deleting an unknown lock.

Current-main overlap: current main has the low-level Windows API helper because safe publish already uses it, but no run-lock abstraction. This is the largest recovery chunk and should be ported only with its focused tests and without changing current MCP/context behavior.

## Dependency order for recovery

1. Source-safe source reads, because doctor and rescue use the same explicit source ingestion path.
2. Replay, retention, and import-review library contracts, in that order, because import review depends on replay and composes with retention evidence.
3. CLI doctor, reconciled with the current MCP `canon.doctor` name and preserving read-only MCP behavior.
4. Rescue artifacts and CLI, rebased on current compile/export helpers rather than stale branch output code.
5. Run-lock concurrency, if still needed after current write surfaces are reviewed, because it is larger and has platform-specific custody behavior.

Each chunk needs a red regression against current main, a focused passing test set, and a local review commit before merge or release. No chunk here is shipped until root review and merge.
