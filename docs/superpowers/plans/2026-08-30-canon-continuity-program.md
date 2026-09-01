# Canon Continuity Program Orchestration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Orchestrate delivery of the operator-approved Canon Continuity Capsule architecture through independently testable foundation, security, bootstrap, adapter/UX, evidence, and release subplans without disturbing the parallel I0 worktree or making unsupported provider and release claims.

**Architecture:** This file is the orchestration index; task-level Files, Interfaces, code, and red-green steps live in the five linked implementation subplans. Keep `canon.record/v1` stable and add continuity semantics above it through `canon.atom/v1`, `canon.capsule/v1`, generated `CANON.md`, typed receipts, and descriptor-backed adapters. Execute the subplans in dependency order, with the verified FilesBackend path blocker first, a deterministic stdlib-only local spine next, and integrations, evidence, and public maturity gates only after the core contracts are green.

**Tech Stack:** Python `>=3.11`, standard library runtime only, `pytest>=8`, deterministic JSON/Markdown, injected IO seams, Git worktree isolation at execution time, Windows/macOS/Linux CI in the release tranche.

**Spec:** Approved design `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`; authority receipt `project-docs/APPROVAL-CANON-CONTINUITY-20260830.md`; governing audit contract `project-docs/SPEC-CANON-PILLAR-20260830.md`; validated audit set `project-docs/audits/2026-08-30/`.

## Global Constraints

- Read `C:\dev\public\canon\CLAUDE.md` and this plan before every execution tranche.
- Use `superpowers:using-git-worktrees` before product-code work. Create the worktree from the current `feat/v4-reconcile-loop` HEAD, not from `main`, because V4 is part of the verified baseline.
- Treat `C:\dev\worktrees\canon-full-history-memory-bank-20260830` as read-only user-owned work. Do not edit, stage, move, reformat, merge, or delete its untracked I0 files.
- The untracked planning artifacts in `C:\dev\public\canon\project-docs` and `docs/superpowers/plans` remain the source specification. Do not delete, overwrite, or auto-copy them into a product worktree.
- Keep `canon.record/v1`, its five kinds, and its `global` / `workspace` scopes backward compatible.
- Keep runtime dependencies empty unless the operator approves a separate dependency decision.
- Foundation owns adapter descriptors, built-in conservative lookup, and requested-tier guards. Adapter/UX owns fixture-backed effective-tier reports and matrix generation.
- Security owns `path_policy.py`, `import_review.py`, and canonical source-state digest/check primitives. Bootstrap consumes them and owns only cache and CLI orchestration.
- `tests/fixtures/continuity_gauntlet/smoke/` is the canonical continuity fixture root. Runtime evidence belongs under `artifacts/continuity-benchmark/`.
- Adapter/UX owns internal `continuity fixture-check`, `continuity secret-scan`, and `conformance run` parser registration. Evidence/Release owns only `continuity evidence-check`, `continuity conformance-report`, and `release readiness` additions.
- Use `python -m canon` as the internal CLI. Do not add `[project.scripts]`, a public `canon` executable, renamed package metadata, package reservation, publishing, tags, deployment, or compatibility marks until the naming and license gates pass.
- Do not label an adapter `enforced` without an executable blocking fixture. Closed ChatGPT and Claude application paths remain `native-advisory` at most or `guided`.
- Do not copy raw transcripts, protected I0 content, `.env` values, credentials, browser profiles, private databases, or absolute workstation paths into fixtures, capsules, witnesses, examples, logs, or public artifacts.
- Critical active goals, permissions, prohibitions, constraints, conflicts, frontier state, and explicit unknowns are retained or compilation fails.
- Every omission is typed and visible. Every lossy transform is source-bound and receipt-backed.
- Preserve unknown, blocked, stale, contradictory, untrusted, and unsupported as distinct states.
- Keep 14B/32B quality and release claims blocked until exact endpoint gates exist and release ownership reconciles the evidence conflict.
- No live model benchmark, public release, package upload, provider outreach, or deployment occurs without separate explicit approval.

## Detailed Subplans

| Order | Plan | Responsibility | Entry gate | Exit gate |
|---:|---|---|---|---|
| 1 | `docs/superpowers/plans/2026-08-30-canon-security-import.md` | FilesBackend blocker first; after Foundation, path policy, trust/disclosure, secret quarantine, `.canonpack` preflight, replay/concurrency, retention, import review | Current 407-test baseline | Security Task 1 is green before any external import/write work; remaining security tasks consume foundation types |
| 2 | `docs/superpowers/plans/2026-08-30-canon-foundation.md` | Canonical JSON, atoms, omissions, transforms, adapters, readiness/witness schemas, capsule compiler, `CANON.md`, public Python exports | FilesBackend Task 1 may run first or canonical JSON Task 1 may run in parallel on disjoint files | Foundation focused tests and full suite pass; deterministic fixtures rederive |
| 3 | `docs/superpowers/plans/2026-08-30-canon-bootstrap-cli.md` | Internal `python -m canon`, source-state cache, state machine, preview/doctor/export/rescue/import-review/undo | Foundation complete; Security Tasks 1-8 complete because Bootstrap consumes path-policy, source-state, and import-review APIs | S0-S8 bootstrap and all CLI gates pass without public CLI metadata |
| 4 | `docs/superpowers/plans/2026-08-30-canon-adapters-ux.md` | Adapter registry, semantic diff, accessible preview, thin shims, controlled runners, MCP/A2A, conformance, flight recorder, merge | Foundation and bootstrap complete; relevant security primitives green | Now-cut adapter/UX fixtures pass; Next-cut work remains separately reviewable |
| 5 | `docs/superpowers/plans/2026-08-30-canon-evidence-release.md` | Evidence admission, continuity reports, internal evidence CLI, CI, docs/community, package dry run, supply-chain and release gates | Prior conformance/report contracts stable | Local-prototype readiness passes; public-alpha remains blocked until operator decisions and fresh receipts exist |

## Execution DAG

```text
Security Task 1: FilesBackend fail-closed validation
        |
        |
Foundation canonical JSON and schemas
        |
Foundation atoms, receipts, descriptors, readiness
        |
Foundation capsule + CANON.md + public Python exports
        |
Security path policy, import review, source state, and remaining security tasks
        |
Bootstrap source state + doctor + state machine + internal CLI
        |
Adapter registry + diff + accessible preview + shims/runners/MCP/A2A
        |
Conformance dry gates + flight recorder + session merge
        |
Evidence admission + CI + docs/community + release-readiness gates
```

## Worktree and Branch Preparation

- [ ] **Step 1: Read the isolation skill**

Read `superpowers:using-git-worktrees` completely before filesystem or branch operations.

- [ ] **Step 2: Verify both current worktrees**

Run:

```powershell
git -C C:\dev\public\canon status --short --branch
git -C C:\dev\worktrees\canon-full-history-memory-bank-20260830 status --short --branch
```

Expected: Canon is on `feat/v4-reconcile-loop` with only approved untracked planning artifacts; the I0 worktree retains its previously observed untracked I0 files.

- [ ] **Step 3: Create an isolated implementation worktree**

Use the isolation skill to create branch `codex/canon-continuity-foundation` from the exact current `feat/v4-reconcile-loop` commit. The target directory must be outside `C:\dev\public\canon` and must not reuse the I0 worktree.

Expected: the new worktree is clean and resolves to the same starting commit as `feat/v4-reconcile-loop`.

- [ ] **Step 4: Establish the baseline**

Run in the implementation worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider
```

Expected: 407 tests pass before implementation. If the count or result differs, stop and diagnose before editing.

- [ ] **Step 5: Make the approved plans available by absolute path**

Executors read plans from `C:\dev\public\canon\docs\superpowers\plans\`. Do not copy untracked planning files into the implementation worktree as an unreviewed bulk operation.

## Tranche A: Security Blocker

- [ ] **Step 1: Execute Security Plan Task 1 tests first**

Open `2026-08-30-canon-security-import.md`, Task 1. Add the exact failing `InvalidRecord` / `InvalidKey` and outside-root tests before implementation.

- [ ] **Step 2: Prove the tests fail for the intended reason**

Run the focused backend commands from the subplan. Expected: failure because semantic/key validation is missing, not because a fixture or import path is wrong.

- [ ] **Step 3: Implement the minimal backend validation change**

Change only the exact backend/base/export files assigned by Security Task 1. Preserve current `UnsupportedKind` and declared-drop behavior while preventing invalid scope/key path derivation.

- [ ] **Step 4: Run focused and full tests**

Expected: focused backend tests and the complete suite pass; the invalid-scope fixture creates no artifact outside the backend root.

- [ ] **Step 5: Run two-stage review**

Use one spec-compliance reviewer against Security Task 1, then one code-quality reviewer. Address only verified findings and rerun focused/full tests.

- [ ] **Step 6: Commit the independently reviewable blocker**

Commit only the Security Task 1 source/tests/exports with a focused message such as `fix: validate backend keys before path derivation`.

## Tranche B: Foundation

- [ ] **Step 1: Execute foundation tasks in its declared DAG**

Use fresh workers per task. T1 precedes all schema work; T3 and T4 may run in parallel only after T1; T5 depends on T1/T2; T6 depends on receipts, adapter, and readiness; capsule and `CANON.md` follow their declared inputs; public exports run last.

- [ ] **Step 2: Preserve exact foundation interfaces**

Do not rename `canonical_json.py`, `CanonAtom`, `Omission`, `TransformReceipt`, `AdapterDescriptor`, `ReadinessProbe`, `BootstrapWitness`, `CapsuleCompileRequest`, `CapsuleBundle`, `compile_capsule`, or `canonmd.py` without updating every dependent plan and receiving review approval.

- [ ] **Step 3: Apply red-green-review-commit for every foundation task**

Each worker runs the exact failing test, implements only that task, runs focused tests, runs the full suite, receives spec and code-quality review, and commits only that task's files.

- [ ] **Step 4: Run the foundation final gates**

Run all commands in the foundation plan's Final Review Gates. Expected: deterministic fixture bytes, critical-retention failures where planted, no runtime dependency imports, no placeholders, and no project-doc/package metadata drift.

## Tranche C: Remaining Security and Bootstrap

- [ ] **Step 1: Execute Security Plan Tasks 2 through 8**

Use the now-green foundation types. `.canonpack` work is manifest preflight only; retention is plan/tombstone only; import review is read-only; secret scanning uses injected scanner seams.

- [ ] **Step 2: Execute Bootstrap Plan in dependency order**

Start with its foundation-contract check, then exit codes/formatting, source-state cache, doctor, import review, undo, rescue/export, and S0-S8 state machine as ordered in the plan.

- [ ] **Step 3: Verify bootstrap tier behavior**

Run the closed-app negative fixtures. Expected: ChatGPT and Claude app paths cannot emit an enforced witness; enforced runners fail closed on readiness or witness failure.

- [ ] **Step 4: Verify write boundaries**

Expected: default workflows write only `.canon/` state or generated artifacts; host surfaces require existing Canon-owned markers, preview, source-state compare, and undo receipt.

- [ ] **Step 5: Run tranche review and regression**

Use spec and code-quality review after each task, then run the full suite and all bootstrap subplan final commands.

## Tranche D: Adapters, UX, Flight Recorder, and Merge

- [ ] **Step 1: Execute the adapter/UX Now cut**

Build the registry and fixture-backed tier calculation, adapter doctor integration, semantic diff, accessible preview, Codex/Claude Code shims, controlled API/local runners, read-only MCP/A2A mappings, and conformance dry gates.

- [ ] **Step 2: Keep native claims conservative**

Every built-in descriptor uses lowercase machine tiers and carries evidence refs, known unknowns, losses, and privacy/auth boundaries. Fixture failure demotes the effective tier.

- [ ] **Step 3: Execute the Next cut only after Now review**

Add the metadata-only flight recorder, session three-way merge, UX boundary records, and endpoint/CI admission. Raw prompt/response/screen/microphone/transcript capture remains off by default; disabled mode writes nothing.

- [ ] **Step 4: Run accessibility and concurrency gates**

Expected: human output works without color, HTML has semantic structure and RTL smoke coverage, concurrent source changes abort or conflict visibly, and merge never chooses by wall-clock recency.

## Tranche E: Evidence and Release Maturity

- [ ] **Step 1: Execute evidence-manifest and release-readiness core tasks**

Build report admission and local-prototype gates before CI consumes them.

- [ ] **Step 2: Register internal evidence CLI commands**

Modify the existing bootstrap parser only as specified in the evidence plan. Keep `python -m canon`; add no public script or package metadata.

- [ ] **Step 3: Add CI and documentation gates**

CI runs tests and dry evidence on Windows, macOS, and Linux. Release dry run never uploads, tags, deploys, reserves, or attests as a signed public release.

- [ ] **Step 4: Preserve public-alpha blockers**

Naming/package/CLI/mark, license split, fresh registry/provider receipts, security channel, governance, accessibility, and 14B/32B evidence remain typed blockers until their approved artifacts exist.

- [ ] **Step 5: Run the evidence/release integration gate**

Expected: local-prototype readiness passes; public-alpha readiness fails with explicit blockers rather than implied readiness.

## Review and Commit Protocol

- [ ] Every implementation task begins with a failing test and records the expected failure reason.
- [ ] Every task ends with focused tests and the full Canon suite.
- [ ] Every task receives a spec-compliance review before a code-quality review.
- [ ] Reviews cite files and exact findings; workers do not accept unverified suggestions blindly.
- [ ] Each commit contains one independently reviewable task and no unrelated planning, I0, release, or workspace files.
- [ ] Before every commit, run `git status --short`, inspect staged paths, and verify no `.env`, token, credential, browser profile, private database, protected artifact, or absolute workstation path entered the diff.
- [ ] Do not commit directly to `main`. Use the `codex/` implementation branch created by the isolation step.

## Program Verification

- [ ] **Step 1: Run all tests without cache artifacts**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider
```

Expected: zero failures.

- [ ] **Step 2: Run internal CLI smoke**

```powershell
python -m canon --help
python -m canon continuity evidence-check artifacts\continuity-benchmark\dry-plan
python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
```

Expected: help and admitted local-prototype evidence exit zero; public-alpha is not claimed.

- [ ] **Step 3: Run security and claim scans**

Use the exact secret, dependency, placeholder, provider-tier, and public-claim scan commands from the five subplans. Expected: no planted secret, unsupported dependency, placeholder, or unsupported enforcement/public-release claim.

- [ ] **Step 4: Verify the parallel I0 worktree stayed untouched**

```powershell
git -C C:\dev\worktrees\canon-full-history-memory-bank-20260830 status --short --branch
```

Expected: the status matches the pre-execution snapshot unless its owning user task independently changed it. No file from that worktree appears in this implementation branch.

- [ ] **Step 5: Produce the experimental outcome**

Record commands, test totals, fixture denominators, artifacts, limitations, does-not-prove language, unresolved release blockers, and the next recursive loop. Do not turn dry/null evidence into a model-quality claim.

## Stop Gates Requiring New Authority

- Public name, package family, CLI binary, compatibility mark, trademark/legal action.
- Runtime/spec/docs license changes.
- New runtime dependencies.
- Reading or importing protected raw history or private I0 outputs.
- Live provider/model benchmark runs that incur cost or expose project context.
- 14B/32B release evidence promotion or publication.
- Package upload, public release, tag, deploy, provider outreach, or telemetry enablement.

Stop at the relevant gate and request operator direction rather than assuming permission.
