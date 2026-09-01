# Canon Evidence Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Canon's release-evidence layer: dry-plan benchmark admission, conformance report admission, CI checks, docs/community gates, package dry-run evidence, SBOM/signing dry-run artifacts, naming/license/provider decision gates, and staged release-readiness verdicts.

**Architecture:** This plan sits above the foundation, security, bootstrap, and adapter plans. It does not define `canon.atom/v1`, `canon.capsule/v1`, `.canonpack`, bootstrap state, adapter descriptors, or conformance execution. It consumes those dependency outputs, adds internal `python -m canon` parser registration for release-evidence commands inside the existing bootstrap-owned CLI, checks reports and artifacts, and blocks public release claims when required evidence is missing, stale, conditional, or unsafe.

**Tech Stack:** Python 3.11+, standard library runtime only, pytest for tests, GitHub Actions YAML checked by stdlib text parsing, Markdown docs, SPDX-shaped SBOM JSON for dry-run evidence, no publishing or deployment.

**Spec:** `C:\dev\public\canon\project-docs\SPEC-CANON-PILLAR-20260830.md`; design proposal `C:\dev\public\canon\project-docs\CANON-CONTINUITY-CAPSULE-DESIGN.md`; audit set `C:\dev\public\canon\project-docs\audits\2026-08-30\`.

**Approval Record:** `C:\dev\public\canon\project-docs\CANON-CONTINUITY-CAPSULE-DESIGN.md:3` records `Status: APPROVED FOR IMPLEMENTATION PLANNING`; `C:\dev\public\canon\project-docs\CANON-CONTINUITY-CAPSULE-DESIGN.md:7` records operator approval on 2026-08-30 for detailed implementation planning, with no active worktree edits, publication, deployment, package registration, provider claims, or release work authorized by that approval alone.

## Global Constraints

- `C:\dev\public\canon\CLAUDE.md` requires Python 3.11+, TDD, no source file over 300 lines, no function over 50 lines, `python -m pytest` on every change, never commit `.env`, branch before committing, and no push, PR, or deploy without explicit go.
- `C:\dev\public\canon\pyproject.toml` currently has `name = "canon"`, `version = "0.0.0"`, `requires-python = ">=3.11"`, `license = { text = "FSL-1.1-MIT" }`, and no runtime dependencies.
- Do not add a `console_scripts` entry, public CLI binary name, public package name, upload configuration, package reservation, publish job, deployment job, or public compatibility mark until the naming/license gate is approved.
- Keep registry, provider, competitor, and host-lifecycle facts conditional unless current receipts are retained with retrieval date, source URL or command, response digest, and decision impact.
- Keep 14B and 32B benchmark/release readiness blocked until endpoint profile artifacts, endpoint generation gate artifacts, and release-owner reconciliation exist for the exact artifacts tested.
- No plan task may publish, deploy, reserve a registry name, create a tag, push a branch, open a PR, or mutate external services.
- Public reports cite artifact paths and hashes. They do not copy private raw prompts, raw outputs, transcripts, credentials, `.env` values, browser profiles, private databases, or unpublished protected material.

---

## Evidence Baseline

- Current branch observed during planning: `feat/v4-reconcile-loop`.
- Current untracked planning evidence observed during planning: `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`, `project-docs/SPEC-CANON-PILLAR-20260830.md`, and `project-docs/audits/`.
- Existing suite command run during planning: `python -m pytest -p no:cacheprovider`.
- Existing suite result observed during planning: `407 passed in 1.27s`.
- Existing tracked release infrastructure: no `.github` directory, no CI workflow, no tracked release automation, no tracked console script, no SBOM, no signing or attestation artifact.
- No retained `index_map(root=C:\dev)` receipt path is cited in this plan. Workspace graph evidence is blocked until a receipt file with command, timestamp, digest, and output path is retained; `index_router(root=C:\dev)` timed out during planning, so full workspace graph claims remain blocked.

## Dependency Contracts

This plan begins only after the lower-level implementation plans provide these contracts. The release-evidence tasks validate their outputs and must not redefine them.

- Foundation dependency produces `src/canon/canonical_json.py`, `src/canon/atom.py`, `src/canon/omission.py`, `src/canon/transform.py`, `src/canon/adapter.py`, `src/canon/readiness.py`, `src/canon/witness.py`, `src/canon/capsule.py`, and `src/canon/canonmd.py`.
- Security dependency produces `src/canon/secret_quarantine.py`, `src/canon/path_policy.py`, `src/canon/import_review.py`, and `src/canon/source_state.py`.
- Bootstrap dependency produces `src/canon/bootstrap.py`, readiness probes, bootstrap witnesses, failure classifications, and the bootstrap-owned `python -m canon compile ...` command.
- Adapter dependency produces `src/canon/adapter_registry.py`, `src/canon/conformance.py`, `tests/fixtures/continuity_gauntlet/smoke/**`, and adapter-owned `python -m canon continuity fixture-check ...`, `python -m canon continuity secret-scan ...`, and `python -m canon conformance run ...` commands.
- Bootstrap CLI dependency owns `src/canon/cli.py`, `python -m canon`, and the top-level parser. This plan modifies that existing parser only to register internal `continuity evidence-check`, `continuity conformance-report`, and `release readiness` commands backed by this plan's modules; it does not add `project.scripts`, `console_scripts`, public package metadata, public CLI binary names, publish jobs, or deploy jobs.

## Design-Gate Mapping Contract

The approved design names user-facing continuity checks, but this plan must admit them through the owning implementation plans instead of registering duplicate commands.

- `check-normative` is admitted via adapter fixture-check normative result.
- `verify-sources` is admitted via evidence-check plus Security source-state admission.
- `roundtrip --matrix` is admitted via conformance run matrix output.
- `merge-check` is a Next-cut session-merge gate and remains typed/deferred until Adapter Task 12 is implemented.

| Design gate | Owning implementation | Admitted evidence in this plan | Release-stage effect |
| --- | --- | --- | --- |
| `check-normative` | Adapter `fixture_check(task_set: Path) -> ConformanceReport` and adapter-owned `python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke`. | The adapter fixture-check result must include a normative result for each smoke fixture that encodes oracle facts, normative constraints, and negative controls. Task 3 admits the resulting conformance report only when the adapter result records those normative rows as passing. | `public-alpha` may count `conformance_ok=True` only when this normative result is present and passing. |
| `verify-sources` | This plan's `python -m canon continuity evidence-check <run_root>` plus Security `source_state` admission from `src/canon/source_state.py`. | Task 2 admits artifact layout and scorecard denominators. Task 1 requires Security `source_state`, and Task 6 runs evidence-check against the bootstrap compile output. Source verification is not a provider fact and does not authorize registry/provider claims. | `local-prototype` needs only tests and internal docs. `public-alpha` may count `evidence_manifest_ok=True` only when evidence-check and source-state admission both pass. |
| `roundtrip --matrix` | Adapter `python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out <dir>` matrix output, backed by `src/canon/adapter_registry.py` and `src/canon/conformance.py`. | Task 3 admits `canon.conformance-report/v1` only when the report includes adapter matrix rows with fixture id, adapter id, claimed tier, admitted tier, and declared losses. | `public-alpha` may count `conformance_ok=True` only from this matrix output, and no adapter may claim `Enforced` without a passing blocking fixture. |
| `merge-check` | Adapter Next-cut session-merge gate in Adapter Task 12. | Typed as `merge_check_state = "deferred-next-cut"` until Adapter Task 12 exists. This plan does not register a `merge-check` command and does not synthesize session-merge evidence from the `parallel_session_merge` smoke fixture. | `local-prototype` and `public-alpha` exclude session-merge from admitted capabilities. `beta`, `stable`, and `ecosystem-standard` remain not in scope for first implementation. |

## File Structure

- Create `src/canon/release_dependencies.py`: dependency artifact checker, used before evidence and release gates.
- Create `src/canon/evidence_manifest.py`: continuity benchmark artifact-layout and scorecard admission checks.
- Create `src/canon/conformance_report.py`: conformance report shape, loss-ledger, and tier-claim admission checks.
- Modify `src/canon/cli.py`: register internal release-evidence subcommands under the existing `python -m canon` parser without changing package metadata.
- Create `src/canon/release_ci.py`: GitHub Actions workflow contract checker.
- Create `src/canon/docs_gate.py`: Markdown, community-file, accessibility, and executable-doc block gates.
- Create `src/canon/package_dry_run.py`: local sdist/wheel dry-run artifact hash and metadata report helpers.
- Create `src/canon/supply_chain.py`: SPDX-shaped SBOM and unsigned dry-run attestation helpers.
- Create `src/canon/release_decisions.py`: naming, license, registry/provider receipt, and local-model blocker checks.
- Create `src/canon/release_readiness.py`: maturity-stage verdict aggregator.
- Create tests under `tests/test_release_*.py`, `tests/test_evidence_manifest.py`, `tests/test_conformance_report.py`, `tests/test_release_cli_integration.py`, `tests/test_docs_gate.py`, and `tests/test_package_dry_run.py`.
- Create `.github/workflows/ci.yml` and `.github/workflows/release-dry-run.yml` as dry-run-only workflows.
- Create docs/community files: `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `MAINTAINERS.md`, `SUPPORT.md`, `CHANGELOG.md`, `ROADMAP.md`, `.github/PULL_REQUEST_TEMPLATE.md`, and issue templates.
- Create release docs under `project-docs/release/`: `SUPPLY-CHAIN.md`, `OPERATOR-DECISIONS.md`, `REGISTRY-PROVIDER-FACTS.md`, and `MATURITY-LADDER.md`.

## Dependency DAG

External plan outputs must exist or be reported blocked before this plan claims release readiness:

- Foundation: `canonical_json`, `atom`, `omission`, `transform`, `adapter`, `readiness`, `witness`, `capsule`, and `canonmd`.
- Security: `secret_quarantine`, `path_policy`, `import_review`, and `source_state`.
- Bootstrap: `bootstrap` and `python -m canon compile`.
- Adapter: `adapter_registry`, `conformance`, `tests/fixtures/continuity_gauntlet/smoke/**`, `python -m canon continuity fixture-check`, `python -m canon continuity secret-scan`, and `python -m canon conformance run`.

Task execution order:

| Task | Depends on | Produces for downstream tasks |
| --- | --- | --- |
| Task 1 Dependency Artifact Gate | External foundation, security, bootstrap, adapter, and CLI files may be present or missing. | `canon.release-dependencies/v1` report. |
| Task 2 Dry-Plan Benchmark Artifact Admission | Task 1 contract names and adapter smoke fixture root. | `canon.evidence-manifest-report/v1` and `check_benchmark_artifact_layout`. |
| Task 3 Conformance Report Admission | Adapter-owned `conformance run` report schema. | `conformance_report_problems` and conservative tier-claim admission. |
| Task 4 Release Stage Acceptance Aggregator | Evidence-key names from Tasks 1, 2, 3, 6, 7, 8, 9, and 10. | `release_readiness`, `release_readiness_to_dict`, and `release_exit_code`. |
| Task 5 Internal CLI Registration Integration | Tasks 2, 3, 4 and bootstrap-owned `src/canon/cli.py`. | Only `continuity evidence-check`, `continuity conformance-report`, and `release readiness` parser additions. |
| Task 6 GitHub Actions CI and Release Dry-Run Contracts | Task 5 CLI registration plus bootstrap and adapter CLI commands. | Cross-platform CI and release dry-run workflow contract report. |
| Task 7 Docs, Community, and Accessibility Gates | Task 5 command names and Task 6 workflow constraints. | Community docs, docs gate report, and executable-doc command allowlist. |
| Task 8 Package Build Dry-Run Evidence | Current `pyproject.toml` metadata and no naming approval. | Local artifact hash report and non-publishable package status. |
| Task 9 SBOM and Signing Dry-Run Design | Task 8 local artifact hashes. | SPDX-shaped SBOM and unsigned dry-run attestation design. |
| Task 10 Naming, License, Registry, Provider, and Local-Model Decision Gates | Approval record and audit set. | Decision gate report with registry/provider conditional and 14B/32B blocked states. |
| Task 11 End-to-End Release Evidence Dry Run | Tasks 1 through 10. | Local-only acceptance report; no publish, deploy, tag, package reservation, or external mutation. |

### Task 1: Dependency Artifact Gate

**Files:**
- Create: `C:\dev\public\canon\src\canon\release_dependencies.py`
- Test: `C:\dev\public\canon\tests\test_release_dependencies.py`

**Interfaces:**
- Consumes: dependency files from foundation/security/bootstrap/adapter/CLI plans.
- Produces:
  - `DependencyCheck(name: str, path: str, ok: bool, detail: str)`
  - `ReleaseDependencyReport(ok: bool, checks: tuple[DependencyCheck, ...])`
  - `check_release_dependencies(root: str | Path) -> ReleaseDependencyReport`
  - `dependency_report_to_dict(report: ReleaseDependencyReport) -> dict[str, object]`

- [ ] **Step 1: Write the failing dependency gate tests**

```python
# tests/test_release_dependencies.py
from pathlib import Path

from canon.release_dependencies import check_release_dependencies, dependency_report_to_dict


def test_dependency_gate_reports_missing_foundation_security_bootstrap_and_adapter_files(tmp_path):
    report = check_release_dependencies(tmp_path)
    assert not report.ok
    missing = {check.name for check in report.checks if not check.ok}
    assert "foundation_canonical_json" in missing
    assert "foundation_capsule" in missing
    assert "security_secret_quarantine" in missing
    assert "security_source_state" in missing
    assert "adapter_registry" in missing
    assert "bootstrap_witness" in missing
    assert "adapter_conformance" in missing
    assert "internal_cli_module" in missing


def test_dependency_gate_passes_when_expected_dependency_files_exist(tmp_path):
    for rel in (
        "src/canon/canonical_json.py",
        "src/canon/atom.py",
        "src/canon/omission.py",
        "src/canon/transform.py",
        "src/canon/adapter.py",
        "src/canon/readiness.py",
        "src/canon/witness.py",
        "src/canon/capsule.py",
        "src/canon/canonmd.py",
        "src/canon/secret_quarantine.py",
        "src/canon/path_policy.py",
        "src/canon/import_review.py",
        "src/canon/source_state.py",
        "src/canon/bootstrap.py",
        "src/canon/adapter_registry.py",
        "src/canon/conformance.py",
        "src/canon/cli.py",
        "tests/fixtures/continuity_gauntlet/smoke/provider_migration/fixture.json",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    report = check_release_dependencies(tmp_path)
    assert report.ok
    assert all(check.ok for check in report.checks)


def test_dependency_report_dict_is_json_safe(tmp_path):
    report = check_release_dependencies(tmp_path)
    payload = dependency_report_to_dict(report)
    assert payload["schema"] == "canon.release-dependencies/v1"
    assert payload["ok"] is False
    assert isinstance(payload["checks"], list)
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_release_dependencies.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.release_dependencies'`.

- [ ] **Step 3: Implement the minimal dependency checker**

```python
# src/canon/release_dependencies.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DependencyCheck:
    name: str
    path: str
    ok: bool
    detail: str


@dataclass(frozen=True, slots=True)
class ReleaseDependencyReport:
    ok: bool
    checks: tuple[DependencyCheck, ...]


_REQUIRED_FILES = (
    ("foundation_canonical_json", "src/canon/canonical_json.py"),
    ("foundation_atom", "src/canon/atom.py"),
    ("foundation_omission", "src/canon/omission.py"),
    ("foundation_transform", "src/canon/transform.py"),
    ("foundation_adapter", "src/canon/adapter.py"),
    ("foundation_readiness", "src/canon/readiness.py"),
    ("foundation_witness", "src/canon/witness.py"),
    ("foundation_capsule", "src/canon/capsule.py"),
    ("foundation_canonmd", "src/canon/canonmd.py"),
    ("security_secret_quarantine", "src/canon/secret_quarantine.py"),
    ("security_path_policy", "src/canon/path_policy.py"),
    ("security_import_review", "src/canon/import_review.py"),
    ("security_source_state", "src/canon/source_state.py"),
    ("bootstrap_witness", "src/canon/bootstrap.py"),
    ("adapter_registry", "src/canon/adapter_registry.py"),
    ("adapter_conformance", "src/canon/conformance.py"),
    ("internal_cli_module", "src/canon/cli.py"),
)

_REQUIRED_DIRS = (
    ("smoke_fixture_set", "tests/fixtures/continuity_gauntlet/smoke"),
)


def check_release_dependencies(root: str | Path) -> ReleaseDependencyReport:
    base = Path(root)
    checks = []
    for name, rel in _REQUIRED_FILES:
        path = base / rel
        ok = path.is_file()
        detail = "file present" if ok else "file missing"
        checks.append(DependencyCheck(name, rel, ok, detail))
    for name, rel in _REQUIRED_DIRS:
        path = base / rel
        ok = path.is_dir() and any(path.rglob("fixture.json"))
        detail = "fixture tree present" if ok else "fixture tree missing fixture.json"
        checks.append(DependencyCheck(name, rel, ok, detail))
    return ReleaseDependencyReport(
        ok=all(check.ok for check in checks),
        checks=tuple(checks),
    )


def dependency_report_to_dict(report: ReleaseDependencyReport) -> dict[str, object]:
    return {
        "schema": "canon.release-dependencies/v1",
        "ok": report.ok,
        "checks": [
            {
                "name": check.name,
                "path": check.path,
                "ok": check.ok,
                "detail": check.detail,
            }
            for check in report.checks
        ],
    }
```

- [ ] **Step 4: Run tests to verify green**

Run: `python -m pytest tests/test_release_dependencies.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/canon/release_dependencies.py tests/test_release_dependencies.py
git commit -m "test: add release dependency gate"
```

### Task 2: Dry-Plan Benchmark Artifact Admission

**Files:**
- Create: `C:\dev\public\canon\src\canon\evidence_manifest.py`
- Test: `C:\dev\public\canon\tests\test_evidence_manifest.py`

**Interfaces:**
- Consumes: benchmark dependency artifacts under `artifacts/continuity-benchmark/<run_id>/`.
- Produces:
  - `EvidenceProblem(code: str, path: str, detail: str)`
  - `EvidenceManifestReport(ok: bool, run_id: str, problems: tuple[EvidenceProblem, ...])`
  - `check_benchmark_artifact_layout(run_root: str | Path) -> EvidenceManifestReport`
  - `check_scorecard_denominators(scorecard: Mapping[str, object]) -> list[EvidenceProblem]`
  - `evidence_report_to_dict(report: EvidenceManifestReport) -> dict[str, object]`

- [ ] **Step 1: Write the failing artifact-layout tests**

```python
# tests/test_evidence_manifest.py
import json

from canon.evidence_manifest import (
    check_benchmark_artifact_layout,
    check_scorecard_denominators,
    evidence_report_to_dict,
)


REQUIRED_DIRS = (
    "task_set",
    "source_state",
    "capsules",
    "provider_runs",
    "roundtrips",
    "scorecards",
    "security",
    "replay",
    "logs/redacted",
)


def _write_minimal_run(root):
    (root / "manifest.json").write_text(
        json.dumps({"schema": "canon.continuity-run/v1", "run_id": "run-001"}),
        encoding="utf-8",
    )
    (root / "run_environment.json").write_text(
        json.dumps({"schema": "canon.run-environment/v1", "platform": "test"}),
        encoding="utf-8",
    )
    for rel in REQUIRED_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "scorecards" / "scorecard.json").write_text(
        json.dumps(
            {
                "schema": "canon.continuity-scorecard/v1",
                "n_tasks": 5,
                "n_replicates": 1,
                "n_attempted": 5,
                "n_valid": 5,
                "n_excluded_non_execution": 0,
                "n_endpoint_blocked": 0,
                "n_secret_scan_unverifiable": 0,
                "n_timed_out": 0,
            }
        ),
        encoding="utf-8",
    )


def test_layout_rejects_missing_scorecard(tmp_path):
    _write_minimal_run(tmp_path)
    (tmp_path / "scorecards" / "scorecard.json").unlink()
    report = check_benchmark_artifact_layout(tmp_path)
    assert not report.ok
    assert any(problem.code == "MISSING_SCORECARD" for problem in report.problems)


def test_layout_accepts_required_dry_plan_directories(tmp_path):
    _write_minimal_run(tmp_path)
    report = check_benchmark_artifact_layout(tmp_path)
    assert report.ok
    assert report.problems == ()
    assert evidence_report_to_dict(report)["schema"] == "canon.evidence-manifest-report/v1"


def test_scorecard_denominator_gate_rejects_percentage_without_denominators():
    scorecard = {"schema": "canon.continuity-scorecard/v1", "critical_retention_rate": 1.0}
    problems = check_scorecard_denominators(scorecard)
    assert [problem.code for problem in problems] == ["MISSING_DENOMINATOR"]
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_evidence_manifest.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.evidence_manifest'`.

- [ ] **Step 3: Implement layout and scorecard admission**

```python
# src/canon/evidence_manifest.py
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class EvidenceProblem:
    code: str
    path: str
    detail: str


@dataclass(frozen=True, slots=True)
class EvidenceManifestReport:
    ok: bool
    run_id: str
    problems: tuple[EvidenceProblem, ...]


_REQUIRED_DIRS = (
    "task_set",
    "source_state",
    "capsules",
    "provider_runs",
    "roundtrips",
    "scorecards",
    "security",
    "replay",
    "logs/redacted",
)

_DENOMINATORS = (
    "n_tasks",
    "n_replicates",
    "n_attempted",
    "n_valid",
    "n_excluded_non_execution",
    "n_endpoint_blocked",
    "n_secret_scan_unverifiable",
    "n_timed_out",
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_scorecard_denominators(scorecard: Mapping[str, object]) -> list[EvidenceProblem]:
    if any(key.endswith("_rate") or key.endswith("_percent") for key in scorecard):
        missing = [key for key in _DENOMINATORS if key not in scorecard]
        if missing:
            return [EvidenceProblem("MISSING_DENOMINATOR", "scorecard.json", ",".join(missing))]
    return []


def check_benchmark_artifact_layout(run_root: str | Path) -> EvidenceManifestReport:
    root = Path(run_root)
    problems: list[EvidenceProblem] = []
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        problems.append(EvidenceProblem("MISSING_MANIFEST", "manifest.json", "run manifest is required"))
        run_id = ""
    else:
        manifest = _read_json(manifest_path)
        run_id = str(manifest.get("run_id", ""))
        if manifest.get("schema") != "canon.continuity-run/v1":
            problems.append(EvidenceProblem("BAD_MANIFEST_SCHEMA", "manifest.json", "expected canon.continuity-run/v1"))
    if not (root / "run_environment.json").is_file():
        problems.append(EvidenceProblem("MISSING_RUN_ENVIRONMENT", "run_environment.json", "environment receipt is required"))
    for rel in _REQUIRED_DIRS:
        if not (root / rel).is_dir():
            problems.append(EvidenceProblem("MISSING_DIRECTORY", rel, "required artifact directory is absent"))
    scorecard_path = root / "scorecards" / "scorecard.json"
    if not scorecard_path.is_file():
        problems.append(EvidenceProblem("MISSING_SCORECARD", "scorecards/scorecard.json", "scorecard is required"))
    else:
        problems.extend(check_scorecard_denominators(_read_json(scorecard_path)))
    return EvidenceManifestReport(ok=not problems, run_id=run_id, problems=tuple(problems))


def evidence_report_to_dict(report: EvidenceManifestReport) -> dict[str, object]:
    return {
        "schema": "canon.evidence-manifest-report/v1",
        "ok": report.ok,
        "run_id": report.run_id,
        "problems": [
            {"code": problem.code, "path": problem.path, "detail": problem.detail}
            for problem in report.problems
        ],
    }
```

- [ ] **Step 4: Run tests and dependency dry-plan commands**

Run: `python -m pytest tests/test_evidence_manifest.py -q`

Expected: PASS.

Run after the foundation/bootstrap CLI dependency commands land. Task 5 wires Task 2's report function to `python -m canon continuity evidence-check`.

```powershell
python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl --atoms tests/fixtures/bootstrap/minimal_atoms.jsonl --target local-runner --profile handoff --out $env:TEMP\canon-continuity-dry-plan --json
```

Expected: both exit `0`; the first command validates the adapter-owned smoke gauntlet fixtures, and the second command creates bootstrap-owned compile artifacts under the output root for later admission checks.

- [ ] **Step 5: Commit**

```bash
git add src/canon/evidence_manifest.py tests/test_evidence_manifest.py
git commit -m "test: gate continuity benchmark evidence layout"
```

### Task 3: Conformance Report Admission

**Files:**
- Create: `C:\dev\public\canon\src\canon\conformance_report.py`
- Test: `C:\dev\public\canon\tests\test_conformance_report.py`

**Interfaces:**
- Consumes: `canon.conformance-report/v1` JSON emitted by the adapter/conformance dependency.
- Produces:
  - `conformance_report_problems(report: Mapping[str, object]) -> list[str]`
  - `conformance_report_ok(report: Mapping[str, object]) -> bool`
  - `admit_tier_claim(report: Mapping[str, object]) -> list[str]`

- [ ] **Step 1: Write the failing conformance tests**

```python
# tests/test_conformance_report.py
from canon.conformance_report import (
    admit_tier_claim,
    conformance_report_ok,
    conformance_report_problems,
)


def _report(**overrides):
    base = {
        "schema": "canon.conformance-report/v1",
        "tool_version": "0.0.0",
        "fixture_set_digest": "sha256:" + "a" * 64,
        "adapter_id": "codex-cli",
        "tier_claimed": "Native advisory",
        "tier_admitted": "Native advisory",
        "results": [{"fixture": "fixture_declared_loss", "status": "pass"}],
        "matrix": [
            {
                "fixture_id": "provider_migration",
                "adapter_id": "codex-cli",
                "tier_claimed": "Native advisory",
                "tier_admitted": "Native advisory",
                "check_normative": "pass",
                "roundtrip": "pass",
                "declared_losses": ["provenance.native_id"],
            }
        ],
        "declared_losses": [{"field": "provenance.native_id", "reason": "markdown-only"}],
        "problems": [],
    }
    base.update(overrides)
    return base


def test_conformance_report_accepts_clean_native_advisory_report():
    assert conformance_report_problems(_report()) == []
    assert conformance_report_ok(_report())


def test_conformance_report_rejects_wrong_schema():
    problems = conformance_report_problems(_report(schema="canon.compat/v1"))
    assert problems == ["BAD_SCHEMA"]


def test_enforced_claim_requires_blocking_fixture_pass():
    report = _report(tier_claimed="Enforced", tier_admitted="Enforced", results=[])
    assert admit_tier_claim(report) == ["ENFORCED_WITHOUT_BLOCKING_FIXTURE"]


def test_tier_overclaim_fails_even_if_report_has_no_problem_rows():
    report = _report(tier_claimed="Enforced", tier_admitted="Native advisory", problems=[])
    assert not conformance_report_ok(report)
    assert "TIER_OVERCLAIM" in conformance_report_problems(report)


def test_roundtrip_matrix_output_is_required_for_public_alpha_design_gate_mapping():
    problems = conformance_report_problems(_report(matrix=[]))
    assert "MISSING_ROUNDTRIP_MATRIX" in problems


def test_check_normative_requires_passing_normative_fixture_result():
    report = _report(matrix=[{"fixture_id": "provider_migration", "adapter_id": "codex-cli", "roundtrip": "pass"}])
    problems = conformance_report_problems(report)
    assert "NORMATIVE_RESULT_MISSING" in problems
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_conformance_report.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.conformance_report'`.

- [ ] **Step 3: Implement conformance report checks**

```python
# src/canon/conformance_report.py
from __future__ import annotations

from typing import Mapping


_TIER_RANK = {
    "Unsupported": 0,
    "Guided": 1,
    "Native advisory": 2,
    "Enforced": 3,
}


def _results(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    value = report.get("results", [])
    return list(value) if isinstance(value, list) else []


def _matrix_rows(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    value = report.get("matrix", [])
    return list(value) if isinstance(value, list) else []


def _matrix_problems(report: Mapping[str, object]) -> list[str]:
    rows = _matrix_rows(report)
    if not rows:
        return ["MISSING_ROUNDTRIP_MATRIX"]
    problems: list[str] = []
    for row in rows:
        for key in ("fixture_id", "adapter_id", "tier_claimed", "tier_admitted"):
            if key not in row:
                problems.append("MISSING_MATRIX_" + key.upper())
        if row.get("check_normative") != "pass":
            problems.append("NORMATIVE_RESULT_MISSING")
        if row.get("roundtrip") not in {"pass", "declared-loss"}:
            problems.append("ROUNDTRIP_MATRIX_NOT_ADMITTED")
    return problems


def admit_tier_claim(report: Mapping[str, object]) -> list[str]:
    claimed = str(report.get("tier_claimed", ""))
    admitted = str(report.get("tier_admitted", ""))
    problems: list[str] = []
    if _TIER_RANK.get(claimed, -1) > _TIER_RANK.get(admitted, -1):
        problems.append("TIER_OVERCLAIM")
    if claimed == "Enforced":
        has_blocking = any(
            row.get("fixture") == "fixture_bootstrap_blocking" and row.get("status") == "pass"
            for row in _results(report)
        )
        if not has_blocking:
            problems.append("ENFORCED_WITHOUT_BLOCKING_FIXTURE")
    return problems


def conformance_report_problems(report: Mapping[str, object]) -> list[str]:
    problems: list[str] = []
    if report.get("schema") != "canon.conformance-report/v1":
        problems.append("BAD_SCHEMA")
    for key in ("tool_version", "fixture_set_digest", "adapter_id", "tier_claimed", "tier_admitted"):
        if key not in report:
            problems.append(f"MISSING_{key.upper()}")
    problems.extend(_matrix_problems(report))
    problems.extend(admit_tier_claim(report))
    for row in report.get("problems", []):
        if isinstance(row, str):
            problems.append(row)
        elif isinstance(row, Mapping):
            problems.append(str(row.get("code", "PROBLEM")))
    return problems


def conformance_report_ok(report: Mapping[str, object]) -> bool:
    return conformance_report_problems(report) == []
```

- [ ] **Step 4: Run tests and conformance dependency command**

Run: `python -m pytest tests/test_conformance_report.py -q`

Expected: PASS.

Run after the adapter/conformance dependency lands:

```powershell
python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out $env:TEMP\canon-conformance
```

Expected: exit `0`, creates a `canon.conformance-report/v1` JSON report, and does not label any adapter `Enforced` unless `fixture_bootstrap_blocking` passed for that adapter.

- [ ] **Step 5: Commit**

```bash
git add src/canon/conformance_report.py tests/test_conformance_report.py
git commit -m "test: admit conformance reports before release claims"
```

### Task 4: Release Stage Acceptance Aggregator

**Files:**
- Create: `C:\dev\public\canon\src\canon\release_readiness.py`
- Create: `C:\dev\public\canon\project-docs\release\MATURITY-LADDER.md`
- Test: `C:\dev\public\canon\tests\test_release_readiness.py`

**Interfaces:**
- Consumes: evidence keys produced by dependency report, evidence manifest report, conformance report, docs gate report, CI workflow report, package dry-run report, supply-chain dry-run artifacts, decision gate, registry/provider fact state, and local-model state.
- Produces:
  - `ReleaseReadinessReport(stage: str, ok: bool, blockers: tuple[str, ...], conditional: tuple[str, ...])`
  - `release_readiness(root: str | Path, *, stage: str, evidence: Mapping[str, object]) -> ReleaseReadinessReport`
  - `release_readiness_to_dict(report: ReleaseReadinessReport) -> dict[str, object]`
  - `release_exit_code(report: ReleaseReadinessReport) -> int`

- [ ] **Step 1: Write failing release-readiness tests**

```python
# tests/test_release_readiness.py
from canon.release_readiness import release_exit_code, release_readiness, release_readiness_to_dict


def _evidence(**overrides):
    base = {
        "tests_passed": True,
        "internal_docs_present": True,
        "dependency_report_ok": True,
        "evidence_manifest_ok": True,
        "conformance_ok": True,
        "docs_gate_ok": True,
        "ci_workflow_ok": True,
        "package_dry_run_ok": True,
        "sbom_present": True,
        "attestation_status": "unsigned-dry-run",
        "decision_gate_ok": False,
        "registry_provider_state": "conditional",
        "local_model_14b_state": "blocked",
        "local_model_32b_state": "blocked",
        "publish_or_deploy_requested": False,
    }
    base.update(overrides)
    return base


def test_local_prototype_stage_passes_with_current_non_publishable_evidence():
    report = release_readiness(".", stage="local-prototype", evidence=_evidence())
    assert report.ok
    assert release_exit_code(report) == 0
    assert release_readiness_to_dict(report)["stage"] == "local-prototype"


def test_public_alpha_blocks_on_naming_license_and_conditional_registry_facts():
    report = release_readiness(".", stage="public-alpha", evidence=_evidence())
    assert not report.ok
    assert "DECISION_GATE_BLOCKED" in report.blockers
    assert "REGISTRY_PROVIDER_FACTS_CONDITIONAL" in report.conditional


def test_any_stage_blocks_publish_or_deploy_request():
    report = release_readiness(".", stage="local-prototype", evidence=_evidence(publish_or_deploy_requested=True))
    assert not report.ok
    assert report.blockers == ("PUBLISH_OR_DEPLOY_NOT_AUTHORIZED",)


def test_local_and_public_alpha_do_not_claim_deferred_merge_readiness():
    local = release_readiness(".", stage="local-prototype", evidence=_evidence(merge_check_state="deferred-next-cut"))
    assert local.ok
    assert all("MERGE" not in code for code in local.blockers + local.conditional)
    alpha = release_readiness(".", stage="public-alpha", evidence=_evidence(merge_check_state="deferred-next-cut"))
    assert all("MERGE" not in code for code in alpha.blockers + alpha.conditional)
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_release_readiness.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.release_readiness'`.

- [ ] **Step 3: Implement release readiness**

```python
# src/canon/release_readiness.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ReleaseReadinessReport:
    stage: str
    ok: bool
    blockers: tuple[str, ...]
    conditional: tuple[str, ...]


def _need(evidence: Mapping[str, object], key: str, code: str, blockers: list[str]) -> None:
    if not evidence.get(key):
        blockers.append(code)


def release_readiness(root: str | Path, *, stage: str, evidence: Mapping[str, object]) -> ReleaseReadinessReport:
    Path(root)
    blockers: list[str] = []
    conditional: list[str] = []
    # merge_check_state is intentionally not admitted for local-prototype or public-alpha.
    # Adapter Task 12 owns the Next-cut session-merge gate.
    if evidence.get("publish_or_deploy_requested"):
        return ReleaseReadinessReport(stage, False, ("PUBLISH_OR_DEPLOY_NOT_AUTHORIZED",), ())
    if stage == "local-prototype":
        _need(evidence, "tests_passed", "TESTS_NOT_PASSING", blockers)
        _need(evidence, "internal_docs_present", "INTERNAL_DOCS_MISSING", blockers)
    elif stage == "public-alpha":
        for key, code in (
            ("tests_passed", "TESTS_NOT_PASSING"),
            ("dependency_report_ok", "DEPENDENCIES_NOT_READY"),
            ("evidence_manifest_ok", "EVIDENCE_MANIFEST_NOT_READY"),
            ("conformance_ok", "CONFORMANCE_NOT_READY"),
            ("docs_gate_ok", "DOCS_GATE_NOT_READY"),
            ("ci_workflow_ok", "CI_WORKFLOW_NOT_READY"),
            ("package_dry_run_ok", "PACKAGE_DRY_RUN_NOT_READY"),
            ("sbom_present", "SBOM_MISSING"),
            ("decision_gate_ok", "DECISION_GATE_BLOCKED"),
        ):
            _need(evidence, key, code, blockers)
        if evidence.get("registry_provider_state") == "conditional":
            conditional.append("REGISTRY_PROVIDER_FACTS_CONDITIONAL")
        if evidence.get("local_model_14b_state") == "blocked":
            conditional.append("14B_BLOCKED")
        if evidence.get("local_model_32b_state") == "blocked":
            conditional.append("32B_BLOCKED")
    elif stage in {"beta", "stable", "ecosystem-standard"}:
        blockers.append(stage.upper().replace("-", "_") + "_NOT_IN_SCOPE_FOR_FIRST_IMPLEMENTATION")
    else:
        blockers.append("UNKNOWN_STAGE")
    return ReleaseReadinessReport(stage, not blockers, tuple(blockers), tuple(conditional))


def release_readiness_to_dict(report: ReleaseReadinessReport) -> dict[str, object]:
    return {
        "schema": "canon.release-readiness/v1",
        "stage": report.stage,
        "ok": report.ok,
        "blockers": list(report.blockers),
        "conditional": list(report.conditional),
    }


def release_exit_code(report: ReleaseReadinessReport) -> int:
    return 0 if report.ok else 1
```

- [ ] **Step 4: Create maturity ladder document**

`project-docs/release/MATURITY-LADDER.md` must define:

- `Local prototype`: tests pass, internal docs exist, no public release claims.
- `Public alpha`: non-colliding naming decision, security/community docs, internal CLI, smoke fixtures, CI dry run, package build dry run, SBOM dry-run evidence, conformance report, conservative adapter claims, and session-merge excluded from admitted capabilities.
- `Beta`: JSON Schemas, fixture zoo, conformance CLI/report, signed prerelease path, migration policy, docs site plan, adapter tier matrix, clean-room read-only reader gate.
- `Stable`: semver-stable capsule schema, CLI JSON, MCP resources, SDK API, conformance fixtures, security response, accessibility gates, reproducible artifacts, SBOM/signing/attestation.
- `Ecosystem standard`: multiple maintained implementations, public conformance reports, neutral or RFC governance, adapter registry, retirement criteria, sustained support metrics.

The document must state that only `local-prototype` can pass before naming/license approval and fresh registry/provider receipts. It must also state that `merge-check` remains typed as `deferred-next-cut` until Adapter Task 12 and is not part of `local-prototype` or `public-alpha` acceptance.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_release_readiness.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/release_readiness.py tests/test_release_readiness.py project-docs/release/MATURITY-LADDER.md
git commit -m "test: add release maturity stage gates"
```

### Task 5: Internal CLI Registration Integration

**Files:**
- Modify: `C:\dev\public\canon\src\canon\cli.py`
- Test: `C:\dev\public\canon\tests\test_release_cli_integration.py`

**Interfaces:**
- Consumes:
  - Bootstrap-owned `main(argv: Sequence[str] | None = None) -> int` from `src/canon/cli.py`.
  - Bootstrap-owned top-level `argparse._SubParsersAction` created by the existing `python -m canon` parser.
  - Task 2 `check_benchmark_artifact_layout(run_root: str | Path) -> EvidenceManifestReport`.
  - Task 2 `evidence_report_to_dict(report: EvidenceManifestReport) -> dict[str, object]`.
  - Task 3 `conformance_report_problems(report: Mapping[str, object]) -> list[str]`.
  - Task 4 `release_readiness(root: str | Path, *, stage: str, evidence: Mapping[str, object]) -> ReleaseReadinessReport`.
  - Task 4 `release_readiness_to_dict(report: ReleaseReadinessReport) -> dict[str, object]`.
  - Task 4 `release_exit_code(report: ReleaseReadinessReport) -> int`.
- Produces:
  - `register_evidence_release_commands(subparsers: argparse._SubParsersAction) -> None`
  - `cmd_continuity_evidence_check(args: argparse.Namespace) -> int`
  - `cmd_continuity_conformance_report(args: argparse.Namespace) -> int`
  - `cmd_release_readiness(args: argparse.Namespace) -> int`
- Does not produce: `check-normative`, `verify-sources`, `roundtrip --matrix`, or `merge-check` CLI commands.

- [ ] **Step 1: Write failing CLI integration tests**

```python
# tests/test_release_cli_integration.py
import json
from pathlib import Path
import tomllib

from canon.cli import main


def _write_minimal_run(root: Path) -> None:
    for rel in (
        "task_set",
        "source_state",
        "capsules",
        "provider_runs",
        "roundtrips",
        "scorecards",
        "security",
        "replay",
        "logs/redacted",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "manifest.json").write_text(
        json.dumps({"schema": "canon.continuity-run/v1", "run_id": "run-cli"}),
        encoding="utf-8",
    )
    (root / "run_environment.json").write_text(
        json.dumps({"schema": "canon.run-environment/v1"}),
        encoding="utf-8",
    )
    (root / "scorecards" / "scorecard.json").write_text(
        json.dumps(
            {
                "schema": "canon.continuity-scorecard/v1",
                "n_tasks": 1,
                "n_replicates": 1,
                "n_attempted": 1,
                "n_valid": 1,
                "n_excluded_non_execution": 0,
                "n_endpoint_blocked": 0,
                "n_secret_scan_unverifiable": 0,
                "n_timed_out": 0,
            }
        ),
        encoding="utf-8",
    )


def test_continuity_evidence_check_subcommand_emits_json_report(tmp_path, capsys):
    run_root = tmp_path / "run"
    _write_minimal_run(run_root)
    code = main(["continuity", "evidence-check", str(run_root), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "canon.evidence-manifest-report/v1"
    assert payload["ok"] is True
    assert payload["run_id"] == "run-cli"


def test_continuity_conformance_report_subcommand_blocks_overclaim(tmp_path, capsys):
    report = tmp_path / "conformance.json"
    report.write_text(
        json.dumps(
            {
                "schema": "canon.conformance-report/v1",
                "tool_version": "0.0.0",
                "fixture_set_digest": "sha256:" + "a" * 64,
                "adapter_id": "codex-cli",
                "tier_claimed": "Enforced",
                "tier_admitted": "Native advisory",
                "results": [],
                "declared_losses": [],
                "problems": [],
            }
        ),
        encoding="utf-8",
    )
    code = main(["continuity", "conformance-report", str(report), "--json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "canon.conformance-admission/v1"
    assert "TIER_OVERCLAIM" in payload["problems"]


def test_release_readiness_subcommand_uses_explicit_local_evidence(capsys):
    code = main(
        [
            "release",
            "readiness",
            "--stage",
            "local-prototype",
            "--tests-passed",
            "--internal-docs-present",
            "--json",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "canon.release-readiness/v1"
    assert payload["stage"] == "local-prototype"
    assert payload["ok"] is True


def test_release_readiness_subcommand_reads_public_alpha_evidence_file(tmp_path, capsys):
    evidence = tmp_path / "evidence.json"
    evidence.write_text(
        json.dumps(
            {
                "tests_passed": True,
                "dependency_report_ok": True,
                "evidence_manifest_ok": True,
                "conformance_ok": True,
                "docs_gate_ok": True,
                "ci_workflow_ok": True,
                "package_dry_run_ok": True,
                "sbom_present": True,
                "decision_gate_ok": False,
                "registry_provider_state": "conditional",
                "local_model_14b_state": "blocked",
                "local_model_32b_state": "blocked",
                "publish_or_deploy_requested": False,
            }
        ),
        encoding="utf-8",
    )
    code = main(["release", "readiness", "--stage", "public-alpha", "--evidence-json", str(evidence), "--json"])
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert "DECISION_GATE_BLOCKED" in payload["blockers"]
    assert "REGISTRY_PROVIDER_FACTS_CONDITIONAL" in payload["conditional"]


def test_cli_integration_does_not_add_project_script_metadata():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    assert "scripts" not in project
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_release_cli_integration.py -q`

Expected before this task: FAIL because `continuity evidence-check`, `continuity conformance-report`, or `release readiness` is not registered on the existing `python -m canon` parser. If the bootstrap dependency has not landed, FAIL with `ModuleNotFoundError: No module named 'canon.cli'`.

- [ ] **Step 3: Register release-evidence commands in the existing parser**

Add this code to `C:\dev\public\canon\src\canon\cli.py` and call `register_evidence_release_commands(subparsers)` at the point where the existing bootstrap parser has created the top-level subparser object. Do not replace dependency-owned commands such as bootstrap `compile`, adapter `continuity fixture-check`, adapter `continuity secret-scan`, or adapter `conformance run`. Do not register `check-normative`, `verify-sources`, `roundtrip --matrix`, or `merge-check`.

```python
# src/canon/cli.py
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from canon.conformance_report import conformance_report_problems
from canon.evidence_manifest import check_benchmark_artifact_layout, evidence_report_to_dict
from canon.release_readiness import release_exit_code, release_readiness, release_readiness_to_dict


def _subparsers(parser: argparse.ArgumentParser, *, dest: str) -> argparse._SubParsersAction:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return parser.add_subparsers(dest=dest, required=True)


def _load_json(path: Path) -> Mapping[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _print_payload(payload: Mapping[str, object], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


def cmd_continuity_evidence_check(args: argparse.Namespace) -> int:
    report = check_benchmark_artifact_layout(args.run_root)
    _print_payload(evidence_report_to_dict(report), json_output=args.json)
    return 0 if report.ok else 1


def cmd_continuity_conformance_report(args: argparse.Namespace) -> int:
    problems = conformance_report_problems(_load_json(args.report_json))
    payload = {
        "schema": "canon.conformance-admission/v1",
        "ok": not problems,
        "problems": problems,
    }
    _print_payload(payload, json_output=args.json)
    return 0 if not problems else 1


def _release_evidence_from_args(args: argparse.Namespace) -> dict[str, object]:
    evidence = dict(_load_json(args.evidence_json)) if args.evidence_json else {}
    if args.tests_passed:
        evidence["tests_passed"] = True
    if args.internal_docs_present:
        evidence["internal_docs_present"] = True
    evidence.setdefault("publish_or_deploy_requested", False)
    return evidence


def cmd_release_readiness(args: argparse.Namespace) -> int:
    report = release_readiness(Path.cwd(), stage=args.stage, evidence=_release_evidence_from_args(args))
    _print_payload(release_readiness_to_dict(report), json_output=args.json)
    return release_exit_code(report)


def register_evidence_release_commands(subparsers: argparse._SubParsersAction) -> None:
    continuity = subparsers.choices.get("continuity")
    if continuity is None:
        continuity = subparsers.add_parser("continuity", help="Continuity evidence utilities")
    continuity_subparsers = _subparsers(continuity, dest="continuity_command")

    evidence = continuity_subparsers.add_parser("evidence-check", help="Check a continuity dry-plan artifact layout")
    evidence.add_argument("run_root", type=Path)
    evidence.add_argument("--json", action="store_true")
    evidence.set_defaults(func=cmd_continuity_evidence_check)

    conformance = continuity_subparsers.add_parser("conformance-report", help="Admit a conformance JSON report")
    conformance.add_argument("report_json", type=Path)
    conformance.add_argument("--json", action="store_true")
    conformance.set_defaults(func=cmd_continuity_conformance_report)

    release = subparsers.choices.get("release")
    if release is None:
        release = subparsers.add_parser("release", help="Release evidence gates")
    release_subparsers = _subparsers(release, dest="release_command")

    readiness = release_subparsers.add_parser("readiness", help="Evaluate release readiness for a maturity stage")
    readiness.add_argument("--stage", required=True, choices=("local-prototype", "public-alpha", "beta", "stable", "ecosystem-standard"))
    readiness.add_argument("--evidence-json", type=Path)
    readiness.add_argument("--tests-passed", action="store_true")
    readiness.add_argument("--internal-docs-present", action="store_true")
    readiness.add_argument("--json", action="store_true")
    readiness.set_defaults(func=cmd_release_readiness)
```

- [ ] **Step 4: Run tests to verify green**

Run: `python -m pytest tests/test_release_cli_integration.py -q`

Expected: PASS.

- [ ] **Step 5: Verify the internal CLI surface directly**

Run:

```powershell
python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present --json
```

Expected: exit `0`, emits `canon.release-readiness/v1`, and does not require or create `project.scripts`, `console_scripts`, package upload configuration, registry reservation, tag creation, or deployment configuration.

- [ ] **Step 6: Commit**

```bash
git add src/canon/cli.py tests/test_release_cli_integration.py
git commit -m "test: register internal release evidence CLI commands"
```

### Task 6: GitHub Actions CI and Release Dry-Run Contracts

**Files:**
- Create: `C:\dev\public\canon\.github\workflows\ci.yml`
- Create: `C:\dev\public\canon\.github\workflows\release-dry-run.yml`
- Create: `C:\dev\public\canon\src\canon\release_ci.py`
- Test: `C:\dev\public\canon\tests\test_release_ci.py`

**Interfaces:**
- Consumes: Task 4 release-readiness functions, Task 5 internal CLI registration, dependency CLI commands, pytest suite, package build command.
- Produces:
  - `check_workflow_contract(path: str | Path, *, kind: str) -> list[str]`
  - `workflow_contract_report(root: str | Path) -> dict[str, object]`

- [ ] **Step 1: Write the failing workflow contract tests**

```python
# tests/test_release_ci.py
from canon.release_ci import check_workflow_contract


CI_YML = """
name: ci
on: [push, pull_request]
jobs:
  tests:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install -e .[dev]
      - run: python -m pytest -p no:cacheprovider
      - run: python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
      - run: python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl --atoms tests/fixtures/bootstrap/minimal_atoms.jsonl --target local-runner --profile handoff --out "$RUNNER_TEMP/canon-continuity" --json
      - run: python -m canon continuity evidence-check "$RUNNER_TEMP/canon-continuity"
      - run: python -m canon continuity secret-scan "$RUNNER_TEMP/canon-continuity"
      - run: python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out "$RUNNER_TEMP/canon-conformance"
      - run: python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
      - run: python -m build --sdist --wheel --outdir "$RUNNER_TEMP/canon-dist"
"""


RELEASE_DRY_RUN_YML = """
name: release-dry-run
on:
  workflow_dispatch:
jobs:
  dry-run:
    permissions:
      contents: read
      id-token: none
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python -m pip install -e .[dev]
      - run: python -m build --sdist --wheel --outdir "$RUNNER_TEMP/canon-dist"
      - run: python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
"""


def test_ci_contract_requires_windows_macos_linux_and_python_matrix(tmp_path):
    path = tmp_path / "ci.yml"
    path.write_text(CI_YML, encoding="utf-8")
    assert check_workflow_contract(path, kind="ci") == []


def test_ci_contract_rejects_missing_windows_runner(tmp_path):
    path = tmp_path / "ci.yml"
    path.write_text(CI_YML.replace("windows-latest", "ubuntu-22.04"), encoding="utf-8")
    assert "MISSING_WINDOWS_RUNNER" in check_workflow_contract(path, kind="ci")


def test_release_dry_run_forbids_publish_and_deploy_actions(tmp_path):
    path = tmp_path / "release-dry-run.yml"
    path.write_text(RELEASE_DRY_RUN_YML + "\n      - run: python -m twine upload dist/*\n", encoding="utf-8")
    assert "PUBLISH_OR_DEPLOY_STEP_PRESENT" in check_workflow_contract(path, kind="release-dry-run")
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_release_ci.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.release_ci'`.

- [ ] **Step 3: Implement the workflow checker**

```python
# src/canon/release_ci.py
from __future__ import annotations

from pathlib import Path


_FORBIDDEN_RELEASE_TOKENS = (
    "twine upload",
    "pypa/gh-action-pypi-publish",
    "npm publish",
    "cargo publish",
    "gh release create",
    "deploy-pages",
    "peaceiris/actions-gh-pages",
)


def check_workflow_contract(path: str | Path, *, kind: str) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    problems: list[str] = []
    if kind == "ci":
        for runner, code in (
            ("ubuntu-latest", "MISSING_LINUX_RUNNER"),
            ("macos-latest", "MISSING_MACOS_RUNNER"),
            ("windows-latest", "MISSING_WINDOWS_RUNNER"),
        ):
            if runner not in text:
                problems.append(code)
        for version in ('"3.11"', '"3.12"'):
            if version not in text:
                problems.append(f"MISSING_PYTHON_{version.strip(chr(34)).replace('.', '_')}")
        for command in (
            "python -m pytest -p no:cacheprovider",
            "python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke",
            "python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl",
            "python -m canon continuity evidence-check",
            "python -m canon continuity secret-scan",
            "python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke",
            "python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present",
            "python -m build --sdist --wheel",
        ):
            if command not in text:
                problems.append("MISSING_COMMAND:" + command)
    if kind == "release-dry-run":
        lowered = text.lower()
        if any(token in lowered for token in _FORBIDDEN_RELEASE_TOKENS):
            problems.append("PUBLISH_OR_DEPLOY_STEP_PRESENT")
        if "id-token: none" not in text:
            problems.append("ID_TOKEN_NOT_DISABLED_FOR_DRY_RUN")
    return problems


def workflow_contract_report(root: str | Path) -> dict[str, object]:
    base = Path(root)
    ci = check_workflow_contract(base / ".github/workflows/ci.yml", kind="ci")
    dry = check_workflow_contract(base / ".github/workflows/release-dry-run.yml", kind="release-dry-run")
    return {
        "schema": "canon.workflow-contract-report/v1",
        "ok": not ci and not dry,
        "ci_problems": ci,
        "release_dry_run_problems": dry,
    }
```

- [ ] **Step 4: Add the CI workflow**

```yaml
# .github/workflows/ci.yml
name: ci

on:
  push:
  pull_request:

jobs:
  tests:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.11", "3.12"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: python -m pip install --upgrade pip build
      - run: python -m pip install -e .[dev]
      - run: python -m pytest -p no:cacheprovider
      - run: python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
      - run: python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl --atoms tests/fixtures/bootstrap/minimal_atoms.jsonl --target local-runner --profile handoff --out "$RUNNER_TEMP/canon-continuity" --json
      - run: python -m canon continuity evidence-check "$RUNNER_TEMP/canon-continuity"
      - run: python -m canon continuity secret-scan "$RUNNER_TEMP/canon-continuity"
      - run: python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out "$RUNNER_TEMP/canon-conformance"
      - run: python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
      - run: python -m build --sdist --wheel --outdir "$RUNNER_TEMP/canon-dist"
```

- [ ] **Step 5: Add the release dry-run workflow**

```yaml
# .github/workflows/release-dry-run.yml
name: release-dry-run

on:
  workflow_dispatch:

jobs:
  dry-run:
    permissions:
      contents: read
      id-token: none
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip build
      - run: python -m pip install -e .[dev]
      - run: python -m pytest -p no:cacheprovider
      - run: python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
      - run: python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out "$RUNNER_TEMP/canon-conformance"
      - run: python -m build --sdist --wheel --outdir "$RUNNER_TEMP/canon-dist"
      - run: python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
```

- [ ] **Step 6: Run tests to verify green**

Run: `python -m pytest tests/test_release_ci.py -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/release-dry-run.yml src/canon/release_ci.py tests/test_release_ci.py
git commit -m "ci: add cross-platform release evidence dry run"
```

### Task 7: Docs, Community, and Accessibility Gates

**Files:**
- Create: `C:\dev\public\canon\src\canon\docs_gate.py`
- Create: `C:\dev\public\canon\SECURITY.md`
- Create: `C:\dev\public\canon\CONTRIBUTING.md`
- Create: `C:\dev\public\canon\CODE_OF_CONDUCT.md`
- Create: `C:\dev\public\canon\GOVERNANCE.md`
- Create: `C:\dev\public\canon\MAINTAINERS.md`
- Create: `C:\dev\public\canon\SUPPORT.md`
- Create: `C:\dev\public\canon\CHANGELOG.md`
- Create: `C:\dev\public\canon\ROADMAP.md`
- Create: `C:\dev\public\canon\.github\PULL_REQUEST_TEMPLATE.md`
- Create: `C:\dev\public\canon\.github\ISSUE_TEMPLATE\bug_report.yml`
- Create: `C:\dev\public\canon\.github\ISSUE_TEMPLATE\adapter_request.yml`
- Create: `C:\dev\public\canon\.github\ISSUE_TEMPLATE\conformance_failure.yml`
- Create: `C:\dev\public\canon\.github\ISSUE_TEMPLATE\security_redirect.yml`
- Create: `C:\dev\public\canon\docs\quickstart.md`
- Create: `C:\dev\public\canon\docs\capsule-format.md`
- Create: `C:\dev\public\canon\docs\conformance.md`
- Create: `C:\dev\public\canon\docs\adapter-tiers.md`
- Create: `C:\dev\public\canon\docs\privacy.md`
- Create: `C:\dev\public\canon\docs\troubleshooting.md`
- Create: `C:\dev\public\canon\docs\release-process.md`
- Create: `C:\dev\public\canon\examples\continuity-rescue\README.md`
- Test: `C:\dev\public\canon\tests\test_docs_gate.py`

**Interfaces:**
- Consumes: docs and community files.
- Produces:
  - `check_markdown_accessibility(path: str | Path) -> list[str]`
  - `check_required_community_files(root: str | Path) -> list[str]`
  - `extract_executable_blocks(path: str | Path) -> list[str]`
  - `docs_gate_report(root: str | Path) -> dict[str, object]`

- [ ] **Step 1: Write the failing docs gate tests**

```python
# tests/test_docs_gate.py
from canon.docs_gate import (
    check_markdown_accessibility,
    check_required_community_files,
    extract_executable_blocks,
)


def test_markdown_accessibility_requires_h1(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("## Starts Too Low\n\nContent.\n", encoding="utf-8")
    assert check_markdown_accessibility(path) == ["MISSING_H1"]


def test_markdown_accessibility_rejects_color_only_status(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Guide\n\nThe red item fails and the green item passes.\n", encoding="utf-8")
    assert "COLOR_ONLY_STATUS" in check_markdown_accessibility(path)


def test_executable_blocks_ignore_text_blocks(tmp_path):
    path = tmp_path / "guide.md"
    path.write_text("# Guide\n\n```text\npython -m pytest\n```\n\n```powershell\npython -m pytest\n```\n", encoding="utf-8")
    assert extract_executable_blocks(path) == ["python -m pytest"]


def test_required_community_files_include_security_warning(tmp_path):
    (tmp_path / "SECURITY.md").write_text(
        "# Security\n\nDo not paste secrets, private capsules, raw transcripts, or credentials into public issues.\n",
        encoding="utf-8",
    )
    for rel in (
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "GOVERNANCE.md",
        "MAINTAINERS.md",
        "SUPPORT.md",
        "CHANGELOG.md",
        "ROADMAP.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/adapter_request.yml",
        ".github/ISSUE_TEMPLATE/conformance_failure.yml",
        ".github/ISSUE_TEMPLATE/security_redirect.yml",
    ):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Present\n", encoding="utf-8")
    assert check_required_community_files(tmp_path) == []
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_docs_gate.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.docs_gate'`.

- [ ] **Step 3: Implement docs/community checks**

```python
# src/canon/docs_gate.py
from __future__ import annotations

import re
from pathlib import Path


_COMMUNITY_FILES = (
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "GOVERNANCE.md",
    "MAINTAINERS.md",
    "SUPPORT.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/adapter_request.yml",
    ".github/ISSUE_TEMPLATE/conformance_failure.yml",
    ".github/ISSUE_TEMPLATE/security_redirect.yml",
)


def check_markdown_accessibility(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    problems: list[str] = []
    if not text.startswith("# "):
        problems.append("MISSING_H1")
    lowered = text.lower()
    if "red item fails" in lowered and "green item passes" in lowered:
        problems.append("COLOR_ONLY_STATUS")
    if re.search(r"\]\((?:file://|https://localhost)", text):
        problems.append("NON_PORTABLE_LINK")
    return problems


def extract_executable_blocks(path: str | Path) -> list[str]:
    text = Path(path).read_text(encoding="utf-8")
    blocks: list[str] = []
    for match in re.finditer(r"```(\w+)\n(.*?)```", text, re.DOTALL):
        lang = match.group(1).lower()
        body = match.group(2).strip()
        if lang in {"bash", "sh", "shell", "powershell", "pwsh", "python"}:
            blocks.append(body)
    return blocks


def check_required_community_files(root: str | Path) -> list[str]:
    base = Path(root)
    problems: list[str] = []
    for rel in _COMMUNITY_FILES:
        if not (base / rel).is_file():
            problems.append("MISSING:" + rel)
    security = base / "SECURITY.md"
    if security.is_file():
        text = security.read_text(encoding="utf-8").lower()
        for phrase in ("do not paste secrets", "private capsules", "raw transcripts", "credentials"):
            if phrase not in text:
                problems.append("SECURITY_MISSING_WARNING:" + phrase)
    return problems


def docs_gate_report(root: str | Path) -> dict[str, object]:
    base = Path(root)
    problems = check_required_community_files(base)
    for rel in ("docs/quickstart.md", "docs/conformance.md", "docs/adapter-tiers.md", "docs/privacy.md"):
        path = base / rel
        if path.is_file():
            problems.extend(f"{rel}:{code}" for code in check_markdown_accessibility(path))
        else:
            problems.append("MISSING:" + rel)
    return {"schema": "canon.docs-gate-report/v1", "ok": not problems, "problems": problems}
```

- [ ] **Step 4: Add community files with required sections**

Required non-code content:

- `SECURITY.md`: supported versions, private vulnerability channel, no secrets in public issues, no raw transcripts, no private capsules, response expectations, and scope of security reports.
- `CONTRIBUTING.md`: Python 3.11 setup, `python -m pytest`, dependency plan order, fixture policy, docs checks, secret handling, no publish/deploy without explicit go.
- `CODE_OF_CONDUCT.md`: scope, expected behavior, unacceptable behavior, enforcement contact, maintainer action path.
- `GOVERNANCE.md`: decision authority, compatibility-impacting change process, release authority, adapter owner duties, retirement criteria.
- `MAINTAINERS.md`: maintainers, domains, review expectations, security contact owner, signing/trust-store owner.
- `SUPPORT.md`: supported versions, public support channel, private security channel, enterprise boundary, non-goals.
- `CHANGELOG.md`: unreleased section with "No public release has been published from this repository."
- `ROADMAP.md`: Now/Next/Later with no public date promises.
- Pull request template: tests, docs, compatibility, migration, security/privacy, accessibility, release notes, no secrets.
- Issue templates: bug, adapter request, conformance failure, security redirect.

- [ ] **Step 5: Add docs and example pages with executable blocks**

Every executable block must use one of these commands exactly after Task 5 registers the release-evidence CLI commands:

```powershell
python -m pytest -p no:cacheprovider
python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl --atoms tests/fixtures/bootstrap/minimal_atoms.jsonl --target local-runner --profile handoff --out $env:TEMP\canon-continuity-dry-plan --json
python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out $env:TEMP\canon-conformance
python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
```

No docs page may state that package publication, provider enforcement, local 14B/32B readiness, or a public compatibility mark exists.

- [ ] **Step 6: Run tests and review gates**

Run: `python -m pytest tests/test_docs_gate.py -q`

Expected: PASS.

Review:
- `SECURITY.md` sends vulnerability reports away from public issues.
- `docs/adapter-tiers.md` says `Enforced` requires an executable blocking fixture.
- `docs/privacy.md` says current storage is plaintext until encryption is implemented.
- `docs/release-process.md` says release dry-run creates evidence only and does not publish.

- [ ] **Step 7: Commit**

```bash
git add SECURITY.md CONTRIBUTING.md CODE_OF_CONDUCT.md GOVERNANCE.md MAINTAINERS.md SUPPORT.md CHANGELOG.md ROADMAP.md .github/PULL_REQUEST_TEMPLATE.md .github/ISSUE_TEMPLATE src/canon/docs_gate.py tests/test_docs_gate.py docs examples/continuity-rescue
git commit -m "docs: add community and accessibility release gates"
```

### Task 8: Package Build Dry-Run Evidence

**Files:**
- Create: `C:\dev\public\canon\src\canon\package_dry_run.py`
- Test: `C:\dev\public\canon\tests\test_package_dry_run.py`

**Interfaces:**
- Consumes: built artifacts in a local temp dist directory.
- Produces:
  - `artifact_hashes(dist_dir: str | Path) -> dict[str, str]`
  - `package_dry_run_report(project_root: str | Path, dist_dir: str | Path) -> dict[str, object]`
  - `package_dry_run_problems(report: Mapping[str, object]) -> list[str]`

- [ ] **Step 1: Write failing package dry-run tests**

```python
# tests/test_package_dry_run.py
from canon.package_dry_run import artifact_hashes, package_dry_run_problems, package_dry_run_report


def test_artifact_hashes_reports_sha256_for_wheel_and_sdist(tmp_path):
    (tmp_path / "canon-0.0.0-py3-none-any.whl").write_bytes(b"wheel")
    (tmp_path / "canon-0.0.0.tar.gz").write_bytes(b"sdist")
    hashes = artifact_hashes(tmp_path)
    assert sorted(hashes) == ["canon-0.0.0-py3-none-any.whl", "canon-0.0.0.tar.gz"]
    assert all(value.startswith("sha256:") and len(value) == 71 for value in hashes.values())


def test_package_report_blocks_public_alpha_when_name_is_current_internal_name(tmp_path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "canon"\nversion = "0.0.0"\nlicense = { text = "FSL-1.1-MIT" }\ndependencies = []\n',
        encoding="utf-8",
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "canon-0.0.0.tar.gz").write_bytes(b"sdist")
    report = package_dry_run_report(tmp_path, dist)
    assert "PUBLIC_NAME_NOT_APPROVED" in package_dry_run_problems(report)
    assert report["publishable"] is False
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_package_dry_run.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.package_dry_run'`.

- [ ] **Step 3: Implement package dry-run helpers**

```python
# src/canon/package_dry_run.py
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Mapping


def artifact_hashes(dist_dir: str | Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(Path(dist_dir).iterdir()):
        if path.is_file() and path.suffix in {".whl", ".gz", ".zip"}:
            out[path.name] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def _project_field(pyproject: str, name: str) -> str:
    match = re.search(rf'^{name}\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    return match.group(1) if match else ""


def package_dry_run_report(project_root: str | Path, dist_dir: str | Path) -> dict[str, object]:
    root = Path(project_root)
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    project_name = _project_field(pyproject, "name")
    version = _project_field(pyproject, "version")
    hashes = artifact_hashes(dist_dir)
    problems: list[str] = []
    if not hashes:
        problems.append("NO_DIST_ARTIFACTS")
    if project_name == "canon":
        problems.append("PUBLIC_NAME_NOT_APPROVED")
    return {
        "schema": "canon.package-dry-run-report/v1",
        "project_name": project_name,
        "version": version,
        "artifacts": hashes,
        "publishable": False,
        "problems": problems,
    }


def package_dry_run_problems(report: Mapping[str, object]) -> list[str]:
    problems = report.get("problems", [])
    return list(problems) if isinstance(problems, list) else ["BAD_PROBLEMS"]
```

- [ ] **Step 4: Run local package dry run**

Run:

```powershell
python -m pip install --upgrade build
python -m build --sdist --wheel --outdir $env:TEMP\canon-dist
python -m pytest tests/test_package_dry_run.py -q
```

Expected: build command creates local sdist/wheel under `$env:TEMP\canon-dist`; no upload step runs; tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/canon/package_dry_run.py tests/test_package_dry_run.py
git commit -m "test: record package build dry-run evidence"
```

### Task 9: SBOM and Signing Dry-Run Design

**Files:**
- Create: `C:\dev\public\canon\src\canon\supply_chain.py`
- Create: `C:\dev\public\canon\project-docs\release\SUPPLY-CHAIN.md`
- Test: `C:\dev\public\canon\tests\test_supply_chain.py`

**Interfaces:**
- Consumes: package dry-run artifact hashes and source commit identity.
- Produces:
  - `spdx_sbom(project: Mapping[str, object], artifacts: Mapping[str, str]) -> dict[str, object]`
  - `unsigned_dry_run_attestation(subjects: Mapping[str, str], source: Mapping[str, str]) -> dict[str, object]`
  - `supply_chain_problems(payload: Mapping[str, object]) -> list[str]`

- [ ] **Step 1: Write failing SBOM/signing tests**

```python
# tests/test_supply_chain.py
from canon.supply_chain import spdx_sbom, supply_chain_problems, unsigned_dry_run_attestation


def test_spdx_sbom_records_current_local_metadata_and_zero_runtime_deps():
    sbom = spdx_sbom(
        {"name": "canon", "version": "0.0.0", "license": "FSL-1.1-MIT", "runtime_dependencies": []},
        {"canon-0.0.0.tar.gz": "sha256:" + "a" * 64},
    )
    assert sbom["spdxVersion"] == "SPDX-2.3"
    assert sbom["packages"][0]["name"] == "canon"
    assert sbom["packages"][0]["versionInfo"] == "0.0.0"
    assert sbom["packages"][0]["licenseDeclared"] == "FSL-1.1-MIT"
    assert sbom["packages"][0]["externalRefs"] == []


def test_unsigned_attestation_cannot_be_mistaken_for_signed_release():
    attestation = unsigned_dry_run_attestation(
        {"canon-0.0.0.tar.gz": "sha256:" + "a" * 64},
        {"commit": "abc1234", "workflow": "release-dry-run"},
    )
    assert attestation["schema"] == "canon.release-attestation/v1"
    assert attestation["status"] == "unsigned-dry-run"
    assert "SIGNATURE_NOT_PRESENT" in supply_chain_problems(attestation)
    assert attestation["publishable"] is False
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_supply_chain.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.supply_chain'`.

- [ ] **Step 3: Implement SBOM and dry-run attestation helpers**

```python
# src/canon/supply_chain.py
from __future__ import annotations

from typing import Mapping


def spdx_sbom(project: Mapping[str, object], artifacts: Mapping[str, str]) -> dict[str, object]:
    package = {
        "SPDXID": "SPDXRef-Package-canon",
        "name": str(project["name"]),
        "versionInfo": str(project["version"]),
        "licenseDeclared": str(project["license"]),
        "filesAnalyzed": False,
        "checksums": [{"algorithm": "SHA256", "checksumValue": value.removeprefix("sha256:")} for value in artifacts.values()],
        "externalRefs": [],
    }
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "canon-dry-run-sbom",
        "documentNamespace": "https://example.invalid/canon/dry-run-sbom",
        "packages": [package],
    }


def unsigned_dry_run_attestation(subjects: Mapping[str, str], source: Mapping[str, str]) -> dict[str, object]:
    return {
        "schema": "canon.release-attestation/v1",
        "status": "unsigned-dry-run",
        "publishable": False,
        "subjects": dict(subjects),
        "source": dict(source),
        "signature": None,
        "does_not_prove": [
            "This dry run does not prove that a public artifact was signed.",
            "This dry run does not authorize package upload, deployment, or registry reservation.",
        ],
    }


def supply_chain_problems(payload: Mapping[str, object]) -> list[str]:
    problems: list[str] = []
    if payload.get("schema") == "canon.release-attestation/v1" and payload.get("signature") is None:
        problems.append("SIGNATURE_NOT_PRESENT")
    if payload.get("publishable") is not False:
        problems.append("DRY_RUN_MARKED_PUBLISHABLE")
    return problems
```

- [ ] **Step 4: Draft supply-chain design document**

`project-docs/release/SUPPLY-CHAIN.md` must contain these sections:

- `# Canon Supply Chain Dry-Run Design`
- `## Current Local Metadata`
- `## Build Dry Run`
- `## SBOM`
- `## Signing and Attestation`
- `## No Publish Boundary`
- `## Future Approval Gates`

Required statements:
- The current local distribution name is `canon`, and public publication under that name is blocked pending naming approval.
- The dry-run attestation is intentionally unsigned and not publishable.
- Public signing design prefers trusted publishing, Sigstore, PyPI attestations, or GitHub provenance over long-lived local keys.
- No release workflow uploads packages, creates tags, deploys docs, or reserves names without explicit approval.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_supply_chain.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/supply_chain.py tests/test_supply_chain.py project-docs/release/SUPPLY-CHAIN.md
git commit -m "docs: add supply-chain dry-run evidence"
```

### Task 10: Naming, License, Registry, Provider, and Local-Model Decision Gates

**Files:**
- Create: `C:\dev\public\canon\src\canon\release_decisions.py`
- Create: `C:\dev\public\canon\project-docs\release\OPERATOR-DECISIONS.md`
- Create: `C:\dev\public\canon\project-docs\release\REGISTRY-PROVIDER-FACTS.md`
- Test: `C:\dev\public\canon\tests\test_release_decisions.py`

**Interfaces:**
- Consumes: operator decision doc, registry/provider fact receipts, local-model endpoint evidence.
- Produces:
  - `decision_gate(root: str | Path) -> dict[str, object]`
  - `registry_provider_facts_state(root: str | Path) -> dict[str, object]`
  - `local_model_release_state(evidence: Mapping[str, object]) -> dict[str, object]`

- [ ] **Step 1: Write failing decision-gate tests**

```python
# tests/test_release_decisions.py
from canon.release_decisions import decision_gate, local_model_release_state, registry_provider_facts_state


def test_decision_gate_blocks_public_alpha_without_naming_and_license_approval(tmp_path):
    (tmp_path / "project-docs" / "release").mkdir(parents=True)
    (tmp_path / "project-docs" / "release" / "OPERATOR-DECISIONS.md").write_text(
        "# Operator Decisions\n\n## Naming\nStatus: blocked\n\n## License Split\nStatus: blocked\n",
        encoding="utf-8",
    )
    report = decision_gate(tmp_path)
    assert not report["ok"]
    assert "NAMING_BLOCKED" in report["blockers"]
    assert "LICENSE_SPLIT_BLOCKED" in report["blockers"]


def test_registry_provider_facts_are_conditional_without_receipts(tmp_path):
    (tmp_path / "project-docs" / "release").mkdir(parents=True)
    (tmp_path / "project-docs" / "release" / "REGISTRY-PROVIDER-FACTS.md").write_text(
        "# Registry and Provider Facts\n\nCurrent facts require fresh receipts before decision use.\n",
        encoding="utf-8",
    )
    report = registry_provider_facts_state(tmp_path)
    assert report["state"] == "conditional"
    assert "FRESH_RECEIPTS_MISSING" in report["conditions"]


def test_14b_and_32b_remain_blocked_without_endpoint_and_release_owner_evidence():
    state = local_model_release_state(
        {
            "14b_endpoint_profile": False,
            "14b_endpoint_gate": False,
            "14b_release_owner_reconciled": False,
            "32b_endpoint_profile": False,
            "32b_endpoint_gate": False,
        }
    )
    assert state["14B"] == "blocked"
    assert state["32B"] == "blocked"
```

- [ ] **Step 2: Run tests to verify red**

Run: `python -m pytest tests/test_release_decisions.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.release_decisions'`.

- [ ] **Step 3: Implement decision gates**

```python
# src/canon/release_decisions.py
from __future__ import annotations

from pathlib import Path
from typing import Mapping


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def decision_gate(root: str | Path) -> dict[str, object]:
    text = _read_optional(Path(root) / "project-docs/release/OPERATOR-DECISIONS.md").lower()
    blockers: list[str] = []
    if "naming\nstatus: approved" not in text and "naming: approved" not in text:
        blockers.append("NAMING_BLOCKED")
    if "license split\nstatus: approved" not in text and "license split: approved" not in text:
        blockers.append("LICENSE_SPLIT_BLOCKED")
    if "public package name\nstatus: approved" not in text and "public package name: approved" not in text:
        blockers.append("PUBLIC_PACKAGE_NAME_BLOCKED")
    return {"schema": "canon.decision-gate/v1", "ok": not blockers, "blockers": blockers}


def registry_provider_facts_state(root: str | Path) -> dict[str, object]:
    text = _read_optional(Path(root) / "project-docs/release/REGISTRY-PROVIDER-FACTS.md").lower()
    has_receipts = all(token in text for token in ("retrieval date:", "source:", "response digest:", "decision impact:"))
    if has_receipts:
        return {"schema": "canon.registry-provider-facts/v1", "state": "receipt-backed", "conditions": []}
    return {
        "schema": "canon.registry-provider-facts/v1",
        "state": "conditional",
        "conditions": ["FRESH_RECEIPTS_MISSING"],
    }


def local_model_release_state(evidence: Mapping[str, object]) -> dict[str, object]:
    def state(prefix: str) -> str:
        needed = (
            bool(evidence.get(prefix.lower() + "_endpoint_profile")),
            bool(evidence.get(prefix.lower() + "_endpoint_gate")),
        )
        if prefix == "14B":
            needed = needed + (bool(evidence.get("14b_release_owner_reconciled")),)
        return "ready" if all(needed) else "blocked"

    return {"schema": "canon.local-model-release-state/v1", "14B": state("14B"), "32B": state("32B")}
```

- [ ] **Step 4: Create operator decision and fact files**

`project-docs/release/OPERATOR-DECISIONS.md` must record these current blocked decisions:

- Naming: blocked until operator approves final public project/package/CLI/mark family.
- Public package name: blocked; do not publish as `canon` unless operator records intentional risk and registry path.
- License split: blocked until runtime, specs, fixtures, conformance, docs, examples, SDKs, and adapters have explicit license policy.
- Compatibility mark: blocked; do not use `Canon Compatible` publicly until governance and conformance policy are approved.
- Provider enforcement wording: blocked for closed apps and host lifecycles without executable blocking fixtures.
- 14B/32B release evidence: blocked until endpoint and release-owner gates pass.

`project-docs/release/REGISTRY-PROVIDER-FACTS.md` must state:

- Registry/provider facts from `project-docs/audits/2026-08-30/COMMUNITY-RELEASE-PILLAR-AUDIT.md` and `PLATFORM-ADAPTER-MATRIX.md` are lane-reported evidence only until fresh receipts are retained.
- Required receipt fields are `Retrieval date:`, `Source:`, `Response digest:`, and `Decision impact:`.
- No package reservation, provider claim, or compatibility claim is authorized by this file.

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/test_release_decisions.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/release_decisions.py tests/test_release_decisions.py project-docs/release/OPERATOR-DECISIONS.md project-docs/release/REGISTRY-PROVIDER-FACTS.md
git commit -m "test: gate naming license provider and local-model claims"
```

### Task 11: End-to-End Release Evidence Dry Run

**Files:**
- Test: `C:\dev\public\canon\tests\test_release_evidence_integration.py`

**Interfaces:**
- Consumes: all modules from Tasks 1 through 10 plus dependency command outputs.
- Produces: one local-only acceptance report under a temp directory during tests.

- [ ] **Step 1: Write failing integration test**

```python
# tests/test_release_evidence_integration.py
from canon.conformance_report import conformance_report_ok
from canon.evidence_manifest import check_benchmark_artifact_layout
from canon.release_readiness import release_readiness


def test_release_evidence_accepts_local_prototype_and_blocks_public_alpha(tmp_path):
    run_root = tmp_path / "run"
    for rel in (
        "task_set",
        "source_state",
        "capsules",
        "provider_runs",
        "roundtrips",
        "scorecards",
        "security",
        "replay",
        "logs/redacted",
    ):
        (run_root / rel).mkdir(parents=True, exist_ok=True)
    (run_root / "manifest.json").write_text('{"schema":"canon.continuity-run/v1","run_id":"run-001"}', encoding="utf-8")
    (run_root / "run_environment.json").write_text('{"schema":"canon.run-environment/v1"}', encoding="utf-8")
    (run_root / "scorecards" / "scorecard.json").write_text(
        '{"schema":"canon.continuity-scorecard/v1","n_tasks":5,"n_replicates":1,"n_attempted":5,"n_valid":5,"n_excluded_non_execution":0,"n_endpoint_blocked":0,"n_secret_scan_unverifiable":0,"n_timed_out":0}',
        encoding="utf-8",
    )
    evidence_report = check_benchmark_artifact_layout(run_root)
    assert evidence_report.ok

    conf = {
        "schema": "canon.conformance-report/v1",
        "tool_version": "0.0.0",
        "fixture_set_digest": "sha256:" + "a" * 64,
        "adapter_id": "codex-cli",
        "tier_claimed": "Native advisory",
        "tier_admitted": "Native advisory",
        "results": [{"fixture": "fixture_declared_loss", "status": "pass"}],
        "matrix": [
            {
                "fixture_id": "provider_migration",
                "adapter_id": "codex-cli",
                "tier_claimed": "Native advisory",
                "tier_admitted": "Native advisory",
                "check_normative": "pass",
                "roundtrip": "pass",
                "declared_losses": [],
            }
        ],
        "declared_losses": [],
        "problems": [],
    }
    assert conformance_report_ok(conf)

    local = release_readiness(".", stage="local-prototype", evidence={"tests_passed": True, "internal_docs_present": True})
    assert local.ok
    alpha = release_readiness(
        ".",
        stage="public-alpha",
        evidence={
            "tests_passed": True,
            "dependency_report_ok": True,
            "evidence_manifest_ok": True,
            "conformance_ok": True,
            "docs_gate_ok": True,
            "ci_workflow_ok": True,
            "package_dry_run_ok": True,
            "sbom_present": True,
            "decision_gate_ok": False,
            "registry_provider_state": "conditional",
            "local_model_14b_state": "blocked",
            "local_model_32b_state": "blocked",
            "publish_or_deploy_requested": False,
        },
    )
    assert not alpha.ok
    assert "DECISION_GATE_BLOCKED" in alpha.blockers
    assert "REGISTRY_PROVIDER_FACTS_CONDITIONAL" in alpha.conditional
```

- [ ] **Step 2: Run integration test to verify red or dependency-blocked**

Run: `python -m pytest tests/test_release_evidence_integration.py -q`

Expected before Tasks 1 through 10: FAIL due missing modules or missing CLI registration.  
Expected after Tasks 1 through 10: PASS.

- [ ] **Step 3: Run full local verification**

Run:

```powershell
cd C:\dev\public\canon
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider
python -m canon continuity fixture-check tests/fixtures/continuity_gauntlet/smoke
python -m canon compile --records tests/fixtures/bootstrap/minimal_records.jsonl --atoms tests/fixtures/bootstrap/minimal_atoms.jsonl --target local-runner --profile handoff --out $env:TEMP\canon-continuity-dry-plan --json
python -m canon continuity evidence-check $env:TEMP\canon-continuity-dry-plan
python -m canon continuity secret-scan $env:TEMP\canon-continuity-dry-plan
python -m canon conformance run tests/fixtures/continuity_gauntlet/smoke --out $env:TEMP\canon-conformance
python -m build --sdist --wheel --outdir $env:TEMP\canon-dist
python -m canon release readiness --stage local-prototype --tests-passed --internal-docs-present
```

Expected:
- pytest passes with the existing 407 tests plus the new release-evidence tests.
- adapter-owned continuity commands and bootstrap-owned compile command exit `0` only after their dependency plans land.
- conformance command exits `0` only after adapter/conformance dependency lands.
- package build creates local artifacts under `$env:TEMP\canon-dist`.
- release readiness for `local-prototype` exits `0`.
- no command uploads, publishes, deploys, creates a tag, reserves a name, or contacts a package registry.

- [ ] **Step 4: Run non-code review gates**

Review and record outcomes in the implementation handoff:
- `project-docs/release/OPERATOR-DECISIONS.md` keeps naming, public package name, license split, provider enforcement wording, compatibility mark, and 14B/32B release evidence blocked until approved.
- `project-docs/release/REGISTRY-PROVIDER-FACTS.md` keeps registry/provider facts conditional unless fresh receipts are attached.
- `project-docs/release/SUPPLY-CHAIN.md` states dry-run attestation is unsigned and not publishable.
- `.github/workflows/release-dry-run.yml` contains no upload, publish, deploy, release, tag, or registry-reservation step.
- `SECURITY.md` tells users not to paste secrets, private capsules, raw transcripts, or credentials into public issues.
- Public docs do not claim ecosystem-standard status, broad enforced bootstrap, provider partnership, public package availability, or local 14B/32B readiness.

- [ ] **Step 5: Commit**

```bash
git add tests/test_release_evidence_integration.py
git commit -m "test: verify local release evidence dry run"
```

## Final Acceptance

- [ ] Dependency plans have landed or this plan reports missing dependencies through `canon.release-dependencies/v1`.
- [ ] Internal `python -m canon continuity evidence-check`, `python -m canon continuity conformance-report`, and `python -m canon release readiness` commands are registered in `src/canon/cli.py` with no project script metadata.
- [ ] `python -m pytest -p no:cacheprovider` passes on Windows, macOS, and Linux in CI.
- [ ] Dry-plan continuity fixture, bootstrap compile, secret scan, conformance, package build, SBOM, and release-readiness evidence are generated locally without publishing.
- [ ] `public-alpha` remains blocked until operator decisions and fresh receipts exist.
- [ ] 14B and 32B remain blocked from Canon release claims until endpoint profile, endpoint generation gate, and release-owner reconciliation are present.
- [ ] No pyproject public console script or renamed public package metadata is added before naming approval.
- [ ] No workflow or command publishes, deploys, reserves a name, creates a tag, or mutates external services.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-30-canon-evidence-release.md`. Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration.
2. Inline Execution - execute tasks in this session using executing-plans, batch execution with checkpoints.

The first implementation action is Task 1. Do not start Task 2 against the real repository until the dependency contracts are either present or explicitly reported as blocked by Task 1.
