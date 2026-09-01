# Canon Adapters UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Canon's adapter, interop, semantic diff, doctor integration, controlled-runner, conformance, flight-recorder, merge, and accessible UX boundary layer on top of the already-planned foundation and bootstrap spine.

**Architecture:** This plan starts after the foundation plan has shipped `canon.canonical_json`, `CanonAtom`, omission, transform, adapter descriptor, capsule, and `canon.canonmd` primitives, and after the bootstrap plan has shipped doctor reports, bootstrap reports, and the bootstrap state machine. The adapter/UX layer adds registry-backed golden descriptors, read-only protocol surfaces, wrapper-gated runners, semantic review, and local continuity receipts without widening `canon.record/v1` or claiming host enforcement Canon cannot prove.

**Tech Stack:** Python 3.11+, standard library runtime only, `pytest>=8` from the existing dev extra, dataclasses, deterministic JSON, injected IO/callable seams, static Markdown/HTML output, no product UI framework in the Now cut.

**Spec:** `project-docs/SPEC-CANON-PILLAR-20260830.md`, `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`, approval record `project-docs/APPROVAL-CANON-CONTINUITY-20260830.md`, `project-docs/audits/2026-08-30/PLATFORM-ADAPTER-MATRIX.md`, `project-docs/audits/2026-08-30/UX-ACCESSIBILITY-FEATURE-BLUEPRINT.md`, `project-docs/audits/2026-08-30/SECURITY-PRIVACY-THREAT-MODEL.md`, `project-docs/audits/2026-08-30/VALIDATION-REPORT.md`.

## Global Constraints

- Python remains `>=3.11`; runtime dependencies remain empty.
- Preserve existing `canon.record/v1` scopes: `global` and `workspace`; richer layers stay in the foundation atom/capsule layer.
- Planning authority is limited by `project-docs/APPROVAL-CANON-CONTINUITY-20260830.md`: architecture and recommended defaults are approved for detailed implementation planning; publishing, deployment, provider outreach, telemetry, paid/live model benchmarks, and release claims remain out of scope.
- Do not redefine foundation types. Import `canonical_json_bytes`, `canonical_json_text`, `sha256_bytes`, `CanonAtom`, `Omission`, `TransformReceipt`, `AdapterDescriptor`, `builtin_descriptors`, `descriptor_for`, `assert_requested_tier_allowed`, `Capsule`, `CapsuleBundle`, `CapsuleBuildError`, `SourceState`, `Budget`, and `render_canon_md` from the foundation modules once they exist.
- Do not redefine bootstrap types. Import `BootstrapConfig`, `BootstrapReport`, `BootstrapEvent`, `DoctorFinding`, `DoctorReport`, `run_bootstrap`, and `run_doctor` from the bootstrap modules once they exist.
- `AdapterDescriptor`, `builtin_descriptors()`, `descriptor_for(adapter_id)`, and `assert_requested_tier_allowed(desc, requested_tier)` are foundation-owned in `src/canon/adapter.py`; this plan must not create, redefine, subclass, or fork them.
- Support tiers in data and code are exactly lowercase: `enforced`, `native-advisory`, `guided`, and `unsupported`.
- No fixture means no `enforced` effective tier.
- No retained primary evidence or descriptor means no stronger-than-`guided` claim for contested hosts.
- Codex and Claude Code thin shims remain `native-advisory` unless a wrapper or native hook has an executable blocking proof.
- ChatGPT and Claude closed apps remain `native-advisory` at most, with `guided` import/export language.
- MCP and A2A are `guided` generically; they become `enforced` only inside a host/controller that gates before ordinary work.
- Local OpenAI-compatible endpoints are `enforced` only through a Canon-owned wrapper that refuses to send the first model request until bootstrap passes and a witness is written.
- Raw prompt, response, screen, microphone, and transcript capture is off by default; the flight recorder records metadata and content hashes unless an explicit private capture policy enables raw content.
- Generated human surfaces must be usable without color, mouse, JavaScript, network, animation, or JSON-only interpretation.
- Every lossy projection has a typed loss case, source identity, and receipt hash.
- Canonical conformance fixtures live under `tests/fixtures/continuity_gauntlet/smoke/**`; do not introduce a parallel fixture root or public script surface in this plan.
- Every command in this plan is run from `C:\dev\public\canon` unless the step says otherwise.
- After each task, run the focused test file first, then `python -m pytest -p no:cacheprovider`.

---

## Dependency Interfaces

Executors must confirm the foundation and bootstrap plans are already green before beginning Task 1:

```powershell
python -m pytest -p no:cacheprovider tests/test_canonical_json.py tests/test_atom.py tests/test_descriptors.py tests/test_readiness.py tests/test_witness.py tests/test_capsule.py tests/test_canonmd.py tests/test_public_exports.py -q
python -m pytest -p no:cacheprovider tests/test_cli_foundation_contract.py tests/test_bootstrap_state_machine.py tests/test_doctor_cli.py tests/test_compile_preview_cli.py -q
```

Expected: both commands pass.

Required foundation imports:

```python
from canon.adapter import (
    AdapterDescriptor,
    assert_requested_tier_allowed,
    builtin_descriptors,
    descriptor_for,
    validate_adapter_descriptor,
)
from canon.atom import CanonAtom
from canon.canonical_json import canonical_json_bytes, canonical_json_text, sha256_bytes
from canon.canonmd import render_canon_md
from canon.capsule import Capsule, CapsuleBundle, SourceState, build_capsule
from canon.omission import Omission
from canon.transform import TransformReceipt
```

Required bootstrap imports:

```python
from canon.bootstrap import BootstrapConfig, BootstrapReport, run_bootstrap
from canon.doctor import DoctorFinding, DoctorReport, run_doctor
from canon.readiness import ReadinessProbe, build_readiness_probe
from canon.witness import BootstrapWitness
```

If any import is unavailable, stop this plan and finish the foundation/bootstrap dependency first.

## Design-Gate Mapping and Deferral Table

The design/audit gate vocabulary maps to this implementation plan as follows:

| Design gate | Adapter/UX handling | Test or instruction | Now/local-prototype gate |
| --- | --- | --- | --- |
| `check-normative` | Map to Task 9 `fixture_check()` normative result over `tests/fixtures/continuity_gauntlet/smoke/**`. | `tests/test_conformance.py::test_fixture_check_requires_all_required_fixture_files` must fail when `normative_constraints.json` is absent, lacks `schema`, or omits active-goal/permission/prohibition/constraint coverage. | Yes, through Task 9 and Task 10 `python -m canon continuity fixture-check <task_set>`. |
| `verify-sources` | Defer to Evidence. Source-state admission and `continuity evidence-check`/source verification are owned by the Evidence plan, not Adapter/UX. | Task 10 must not register `verify-sources`; it may preserve source-state fields in conformance JSON but must not claim Evidence admission. | No. |
| `roundtrip --matrix` | Map to Task 10 `python -m canon conformance run <fixture_root> --out <out>` writing matrix-capable conformance JSON produced by Task 9. | `tests/test_continuity_conformance_cli.py::test_conformance_run_cli_writes_report_to_out` must verify the written report includes `schema`, `ok`, `fixture_ids`, and matrix rows when adapters are present. | Yes, as `conformance run`; do not add a separate `roundtrip --matrix` command. |
| `merge-check` | Defer to Task 12 session merge. | `tests/test_session_merge.py` owns merge safety; Task 10 must not register `merge-check`. | No, not a Now/local-prototype gate until Task 12 lands. |

Task 10 is the only CLI registration task in this plan. It registers internal parser routes for the mapped Now gates and intentionally does not add public scripts or deferred commands.

## File Structure

- `src/canon/adapter_registry.py`: effective tier calculation, descriptor hash, and generated adapter matrix rows over foundation-owned descriptors plus fixture results.
- `src/canon/adapter_doctor.py`: descriptor and tier findings folded into the existing `DoctorReport`.
- `src/canon/semantic_diff.py`: meaning-level comparison between two capsules by atom/record/omission/transform identity.
- `src/canon/preview_accessible.py`: accessible Markdown and static HTML preview composition over capsule, doctor, semantic diff, and adapter matrix data.
- `src/canon/adapters/codex.py`: Codex thin shim planning, using existing `AGENTS.md` surface conventions and advisory labels.
- `src/canon/adapters/claude_code.py`: Claude Code thin shim planning, using existing `CLAUDE.md` surface conventions and advisory labels.
- `src/canon/runners/api.py`: controlled OpenAI-style request gate that refuses to call the sender until bootstrap passes.
- `src/canon/runners/local_openai.py`: local OpenAI-compatible endpoint profile and admission checks.
- `src/canon/mcp_readonly.py`: dependency-free MCP resource/tool payload shapes for read-only preview and doctor use.
- `src/canon/a2a.py`: A2A artifact/message mapping for capsule, `CANON.md`, readiness probe, and witness.
- `src/canon/conformance.py`: dry conformance fixture admission, descriptor tier checks, adapter loss checks, and secret-canary scan over generated artifacts.
- `tests/fixtures/continuity_gauntlet/smoke/**`: smoke fixtures for provider migration, agent resume, repository continuity, parallel-session merge, and ambient bootstrap.
- `src/canon/cli.py`: internal parser registration for continuity fixture checks, continuity secret scans, and conformance runs backed by `canon.conformance`.
- `tests/test_continuity_conformance_cli.py`: internal CLI tests for the exact dependency commands used by evidence and CI.
- `src/canon/flight_recorder.py`: append-only local event receipts with raw content off by default.
- `src/canon/session_merge.py`: branch/session three-way capsule merge and merge witness creation.
- `src/canon/ux_boundaries.py`: desktop/browser/IDE planning boundary records and conservative user-facing copy.

## Now Cut

Tasks 1 through 10 form the Now cut. They produce descriptor-backed adapter truth, semantic review, advisory shims, controlled runners, read-only MCP/A2A surfaces, conformance dry gates, and the internal CLI commands consumed by evidence and CI gates.

### Task 1: Adapter Effective Tier Matrix

**Files:**
- Create: `src/canon/adapter_registry.py`
- Test: `tests/test_adapter_registry.py`

**Interfaces:**
- Consumes: foundation `AdapterDescriptor`, `validate_adapter_descriptor(adapter: AdapterDescriptor) -> list[str]`, `builtin_descriptors() -> tuple[AdapterDescriptor, ...]`, `descriptor_for(adapter_id: str) -> AdapterDescriptor`, `assert_requested_tier_allowed(desc: AdapterDescriptor, requested_tier: str) -> None`, `canonical_json_bytes(value: object) -> bytes`, `sha256_bytes(data: bytes) -> str`.
- Produces:

```python
def effective_tier(desc: AdapterDescriptor, fixture_results: Mapping[str, bool]) -> str:
    """Return integration_tier after fixture-backed demotion rules."""

def descriptor_sha256(desc: AdapterDescriptor) -> str:
    """Return a sha256 ref over canonical descriptor JSON bytes."""

def adapter_matrix(fixture_results: Mapping[str, bool]) -> tuple[dict, ...]:
    """Return compact UI/report rows derived from built-in descriptors."""
```

- [ ] **Step 1: Write registry round-trip tests**

Create `tests/test_adapter_registry.py`:

```python
from canon.adapter import descriptor_for, validate_adapter_descriptor
from canon.adapter_registry import descriptor_sha256, effective_tier

def test_registry_descriptor_uses_foundation_schema_fields():
    desc = descriptor_for("codex-cli")
    assert desc.adapter_id == "codex-cli"
    assert desc.integration_tier == "native-advisory"
    assert "AGENTS.md" in desc.target_surfaces
    assert validate_adapter_descriptor(desc) == []
    assert effective_tier(desc, {"codex-cli": True}) == "native-advisory"
    assert descriptor_sha256(desc).startswith("sha256:")
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_adapter_registry.py::test_registry_descriptor_uses_foundation_schema_fields -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.adapter_registry'`.

- [ ] **Step 3: Implement `src/canon/adapter_registry.py`**

Use only the foundation `AdapterDescriptor` class, foundation descriptor source, and foundation tier guard. Do not create a second descriptor dataclass, alternate descriptor loader, or public script. Implement these exact tier rules:

```python
from canon.adapter import (
    AdapterDescriptor,
    assert_requested_tier_allowed,
    builtin_descriptors,
    descriptor_for,
    validate_adapter_descriptor,
)
from canon.canonical_json import canonical_json_bytes, sha256_bytes

def effective_tier(desc: AdapterDescriptor, fixture_results: Mapping[str, bool]) -> str:
    if desc.integration_tier != "enforced":
        return desc.integration_tier
    if desc.bootstrap.get("can_block_before_work") is True and fixture_results.get(desc.adapter_id) is True:
        return "enforced"
    return "native-advisory"
```

`descriptor_sha256(desc)` must call `sha256_bytes(canonical_json_bytes(desc.to_dict()))`. `adapter_matrix(fixture_results)` must iterate foundation `builtin_descriptors()`, call `assert_requested_tier_allowed(desc, desc.integration_tier)` before writing each row, and include `adapter_id`, `display_name`, `advertised_tier`, `effective_tier`, `target_surfaces`, `import_modes`, `export_modes`, `loss_count`, `evidence_refs`, and `known_unknowns`. Use foundation `descriptor_for(adapter_id)` in tests and downstream callers; do not re-export or wrap it from `canon.adapter_registry`.

- [ ] **Step 4: Add conservative tier tests**

Append to `tests/test_adapter_registry.py`:

```python
def test_enforced_without_fixture_result_downgrades_to_native_advisory():
    desc = AdapterDescriptor.from_dict({
        "schema": "canon.adapter/v1",
        "adapter_id": "api-runner",
        "display_name": "OpenAI-compatible controlled runner",
        "version": "2026-08-30",
        "integration_tier": "enforced",
        "target_surfaces": ["chat.completions", "responses"],
        "import_modes": ["api-request"],
        "export_modes": ["api-response"],
        "bootstrap": {"can_block_before_work": True, "entry": "controlled-wrapper"},
        "losses": [],
        "limits": {},
        "auth": {"boundary": ["caller-owned API key"]},
        "privacy": {"boundary": ["caller-owned logs"]},
        "evidence_refs": ["fixture:api-runner-blocking"],
        "known_unknowns": [],
        "last_verified": "2026-08-30",
        "owner": "canon",
        "retirement_trigger": None
    })
    assert validate_adapter_descriptor(desc) == []
    assert effective_tier(desc, {}) == "native-advisory"
    assert effective_tier(desc, {"api-runner": False}) == "native-advisory"
    assert effective_tier(desc, {"api-runner": True}) == "enforced"
```

- [ ] **Step 5: Add foundation built-in descriptor tests**

Append to `tests/test_adapter_registry.py`:

```python
from canon.adapter import builtin_descriptors, descriptor_for
from canon.adapter_registry import adapter_matrix

def test_builtins_preserve_conservative_tiers():
    tiers = {desc.adapter_id: desc.integration_tier for desc in builtin_descriptors()}
    assert tiers["codex-cli"] == "native-advisory"
    assert tiers["claude-code"] == "native-advisory"
    assert tiers["mcp-readonly"] == "guided"
    assert tiers["a2a-artifact"] == "guided"
    assert tiers["api-runner"] == "guided"
    assert tiers["local-runner"] == "guided"

def test_effective_matrix_preserves_conservative_builtin_tiers():
    rows = {row["adapter_id"]: row for row in adapter_matrix({})}
    assert rows["api-runner"]["advertised_tier"] == "guided"
    assert rows["api-runner"]["effective_tier"] == "guided"
    assert rows["codex-cli"]["effective_tier"] == "native-advisory"
    assert rows["mcp-readonly"]["effective_tier"] == "guided"

def test_fixture_result_does_not_promote_guided_builtin():
    rows = {row["adapter_id"]: row for row in adapter_matrix({"api-runner": True})}
    assert rows["api-runner"]["effective_tier"] == "guided"

def test_descriptor_for_rejects_unknown_adapter_id():
    try:
        descriptor_for("cursor")
    except KeyError as error:
        assert "cursor" in str(error)
    else:
        raise AssertionError("unknown descriptors must be explicit, not guessed")
```

- [ ] **Step 6: Assert no duplicate descriptor ownership**

Run: `rg -n "def builtin_descriptors|def descriptor_for|def assert_requested_tier_allowed|class AdapterDescriptor" src/canon/adapter_registry.py`

Expected: no matches. Those interfaces are foundation-owned in `src/canon/adapter.py`.

- [ ] **Step 7: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_adapter_registry.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/canon/adapter_registry.py tests/test_adapter_registry.py
git commit -m "feat: add canon adapter registry"
```

### Task 2: Adapter Doctor Integration

**Files:**
- Create: `src/canon/adapter_doctor.py`
- Test: `tests/test_adapter_doctor.py`

**Interfaces:**
- Consumes: `AdapterDescriptor`, `effective_tier(desc: AdapterDescriptor, fixture_results: Mapping[str, bool]) -> str`, bootstrap-owned `DoctorFinding`, bootstrap-owned `DoctorReport`.
- Produces:

```python
def adapter_doctor_findings(
    descriptors: tuple[AdapterDescriptor, ...],
    *,
    fixture_results: Mapping[str, bool],
) -> tuple[DoctorFinding, ...]:
    """Return adapter tier, fixture, and boundary findings."""

def extend_doctor_with_adapters(
    report: DoctorReport,
    descriptors: tuple[AdapterDescriptor, ...],
    *,
    fixture_results: Mapping[str, bool],
) -> DoctorReport:
    """Return a DoctorReport with adapter findings appended deterministically."""
```

- [ ] **Step 1: Write failing tests for tier and fixture findings**

Add to `tests/test_adapter_doctor.py`:

```python
from dataclasses import replace

from canon.adapter import descriptor_for
from canon.adapter_doctor import adapter_doctor_findings

def test_adapter_doctor_flags_enforced_without_blocking_fixture():
    desc = replace(
        descriptor_for("api-runner"),
        integration_tier="enforced",
        bootstrap={"can_block_before_work": True, "entry": "controlled-wrapper"},
    )
    findings = adapter_doctor_findings((desc,), fixture_results={})
    assert [(item.code, item.severity) for item in findings] == [
        ("tier_mislabeled", "blocker")
    ]
    assert "No fixture means no enforced effective tier" in findings[0].message
    assert findings[0].evidence["adapter_id"] == "api-runner"
    assert findings[0].evidence["advertised_tier"] == "enforced"
    assert findings[0].evidence["effective_tier"] == "native-advisory"

def test_adapter_doctor_keeps_guided_api_runner_clean():
    desc = descriptor_for("api-runner")
    findings = adapter_doctor_findings((desc,), fixture_results={})
    assert findings == ()

def test_adapter_doctor_keeps_codex_advisory_clean():
    desc = descriptor_for("codex-cli")
    findings = adapter_doctor_findings((desc,), fixture_results={})
    assert findings == ()
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_adapter_doctor.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.adapter_doctor'`.

- [ ] **Step 3: Implement findings without redefining doctor types**

Build `DoctorFinding` instances imported from `canon.doctor`. Use code `tier_mislabeled` when `desc.integration_tier != effective_tier(desc, fixture_results)`. Use code `adapter_fixture_missing` when `desc.integration_tier == "enforced"` and `fixture_results.get(desc.adapter_id)` is not `True`. Put `adapter_id`, `advertised_tier`, `effective_tier`, and `can_block_before_work` in `finding.evidence`. Do not create a new report class.

- [ ] **Step 4: Add report extension test**

Add:

```python
from canon.doctor import DoctorReport
from canon.adapter_doctor import extend_doctor_with_adapters

def test_extend_doctor_appends_adapter_findings_preserving_existing_findings():
    base = DoctorReport(ok=True, failure_code="ok", exit_code=0, findings=())
    desc = replace(
        descriptor_for("api-runner"),
        integration_tier="enforced",
        bootstrap={"can_block_before_work": True, "entry": "controlled-wrapper"},
    )
    report = extend_doctor_with_adapters(base, (desc,), fixture_results={})
    assert report.ok is False
    assert report.failure_code == "tier_mislabeled"
    assert [finding.code for finding in report.findings] == ["tier_mislabeled"]
```

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_adapter_doctor.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/adapter_doctor.py tests/test_adapter_doctor.py
git commit -m "feat: add adapter doctor checks"
```

### Task 3: Semantic Continuity Diff

**Files:**
- Create: `src/canon/semantic_diff.py`
- Create: `tests/fixtures/capsules/diff_before.json`
- Create: `tests/fixtures/capsules/diff_after.json`
- Test: `tests/test_semantic_diff.py`

**Interfaces:**
- Consumes: `Capsule`, `CanonAtom`, `canonical_json_bytes(value: object) -> bytes`, `sha256_bytes(data: bytes) -> str`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class SemanticChange:
    category: str
    key: str
    change: str
    before_sha256: str | None
    after_sha256: str | None
    severity: str

@dataclass(frozen=True, slots=True)
class SemanticDiff:
    ok: bool
    changes: tuple[SemanticChange, ...]

def semantic_atom_key(atom: CanonAtom) -> tuple[str, str, str]:
    """Return the stable semantic key `(type, scope_key, id)` for one atom."""

def diff_capsules(before: Capsule, after: Capsule) -> SemanticDiff:
    """Return atom-level semantic changes between two capsules."""

def render_diff_markdown(diff: SemanticDiff) -> str:
    """Return accessible Markdown for a SemanticDiff."""
```

- [ ] **Step 1: Write failing semantic grouping tests**

Add:

```python
from canon.semantic_diff import diff_capsules, render_diff_markdown

def test_diff_groups_added_removed_changed_by_atom_type(capsule_factory, atom_factory):
    before = capsule_factory(atoms=[
        atom_factory("active-goal", "goal-a", value={"text": "ship adapter registry"}),
        atom_factory("unknown", "unk-a", value={"text": "host hook proof missing"}),
    ])
    after = capsule_factory(atoms=[
        atom_factory("active-goal", "goal-a", value={"text": "ship adapter registry and matrix"}),
        atom_factory("permission", "perm-a", value={"text": "write generated CANON.md"}),
    ])
    diff = diff_capsules(before, after)
    rows = [(item.category, item.change, item.severity) for item in diff.changes]
    assert rows == [
        ("active-goal", "Changed", "high"),
        ("permission", "Added", "high"),
        ("unknown", "Removed", "high"),
    ]
```

If no shared `capsule_factory` or `atom_factory` exists from the foundation plan, add local helper functions inside `tests/test_semantic_diff.py` that construct foundation `CanonAtom` and `Capsule` objects. Do not create alternate production dataclasses.

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_semantic_diff.py::test_diff_groups_added_removed_changed_by_atom_type -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.semantic_diff'`.

- [ ] **Step 3: Implement deterministic comparison**

Compare atoms by `semantic_atom_key(atom)`. Serialize each atom with `sha256_bytes(canonical_json_bytes(atom.to_dict()))`. Severity is `high` for `active-goal`, `permission`, `prohibition`, `constraint`, `conflict`, `unknown`, and `frontier-state`; otherwise `medium`. Sort rows by `(category, key, change)`.

- [ ] **Step 4: Add state-distinction and non-color tests**

Add:

```python
def test_diff_keeps_stale_contradictory_unknown_untrusted_distinct(capsule_factory, atom_factory):
    before = capsule_factory(atoms=[
        atom_factory("episodic-fact", "fact-a", status="stale", value={"text": "old"}),
    ])
    after = capsule_factory(atoms=[
        atom_factory("episodic-fact", "fact-a", status="contradictory", value={"text": "old"}),
        atom_factory("episodic-fact", "fact-b", status="untrusted", value={"text": "imported"}),
        atom_factory("unknown", "unk-b", status="unknown", value={"text": "missing source"}),
    ])
    md = render_diff_markdown(diff_capsules(before, after))
    assert "Changed" in md
    assert "contradictory" in md
    assert "untrusted" in md
    assert "unknown" in md
    assert "+ " not in md and "- " not in md
```

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_semantic_diff.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/semantic_diff.py tests/test_semantic_diff.py tests/fixtures/capsules/diff_before.json tests/fixtures/capsules/diff_after.json
git commit -m "feat: add semantic capsule diff"
```

### Task 4: Accessible Preview Composition

**Files:**
- Create: `src/canon/preview_accessible.py`
- Create: `tests/fixtures/accessibility/expected_preview.md`
- Create: `tests/fixtures/accessibility/expected_preview.html`
- Create: `tests/fixtures/accessibility/expected_preview_rtl.html`
- Test: `tests/test_preview_accessible.py`
- Test: `tests/test_accessibility_static.py`

**Interfaces:**
- Consumes: foundation `CapsuleBundle`, bootstrap-owned `DoctorReport`, `SemanticDiff`, `adapter_matrix(fixture_results: Mapping[str, bool]) -> tuple[dict, ...]`.
- Produces:

```python
STATUS_LABELS = {
    "ready": "Ready",
    "advisory": "Advisory",
    "blocked": "Blocked",
    "stale": "Stale",
    "conflict": "Conflict",
    "unknown": "Unknown",
    "secret_quarantined": "Secret quarantined",
}

def status_label(code: str) -> str:
    """Return a non-color-only user-facing label for one status code."""

def render_accessible_preview_markdown(
    bundle: CapsuleBundle,
    *,
    doctor_report: DoctorReport | None = None,
    diff: SemanticDiff | None = None,
    adapter_rows: tuple[dict, ...] = (),
) -> str:
    """Return screen-reader-friendly Markdown preview content."""

def render_accessible_preview_html(
    bundle: CapsuleBundle,
    *,
    doctor_report: DoctorReport | None = None,
    diff: SemanticDiff | None = None,
    adapter_rows: tuple[dict, ...] = (),
    lang: str = "en",
    direction: str = "ltr",
) -> str:
    """Return static HTML preview content with accessible landmarks and labels."""
```

- [ ] **Step 1: Write failing Markdown preview tests**

Add:

```python
from canon.preview_accessible import render_accessible_preview_markdown

def test_preview_markdown_contains_next_model_context_and_omission_counts(bundle_factory, doctor_report_factory):
    bundle = bundle_factory()
    report = doctor_report_factory(codes=["tier_mislabeled"])
    text = render_accessible_preview_markdown(bundle, doctor_report=report)
    assert "# Canon Preview" in text
    assert "What the next model will know" in text
    assert bundle.capsule.capsule_id in text
    assert "Omissions" in text
    assert "tier_mislabeled" in text
    assert "\x1b[" not in text
```

- [ ] **Step 2: Run focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_preview_accessible.py::test_preview_markdown_contains_next_model_context_and_omission_counts -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.preview_accessible'`.

- [ ] **Step 3: Implement Markdown preview**

Use deterministic section order:

1. `# Canon Preview`
2. `## Status`
3. `## What the next model will know`
4. `## Adapter tier`
5. `## Doctor findings`
6. `## Semantic changes`
7. `## Omissions`
8. `## Does-not-prove`
9. `## Exact CANON.md`

Render status as words, never color-only symbols.

- [ ] **Step 4: Write failing static HTML accessibility tests**

Add:

```python
from html.parser import HTMLParser
from canon.preview_accessible import render_accessible_preview_html

class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

def test_preview_html_has_landmarks_language_direction_and_captions(bundle_factory):
    html = render_accessible_preview_html(bundle_factory(), lang="en", direction="ltr")
    parser = TagCollector()
    parser.feed(html)
    attrs = {tag: data for tag, data in parser.tags if tag in {"html", "main"}}
    assert attrs["html"]["lang"] == "en"
    assert attrs["html"]["dir"] == "ltr"
    assert "main" in [tag for tag, _ in parser.tags]
    assert "<caption>Adapter tiers</caption>" in html
    assert "aria-live=\"polite\"" in html

def test_preview_html_rtl_smoke_sets_dir_rtl(bundle_factory):
    html = render_accessible_preview_html(bundle_factory(), lang="ar", direction="rtl")
    assert "<html lang=\"ar\" dir=\"rtl\">" in html
```

- [ ] **Step 5: Implement static HTML with no remote assets**

Escape text with `html.escape`. Include skip link, `<main>`, `<section aria-labelledby>`, table captions, visible text labels, and CSS inside one `<style>` tag. Do not include JavaScript or external CSS.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_preview_accessible.py tests/test_accessibility_static.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/canon/preview_accessible.py tests/test_preview_accessible.py tests/test_accessibility_static.py tests/fixtures/accessibility
git commit -m "feat: add accessible capsule preview"
```

### Task 5: Codex and Claude Code Thin Shims

**Files:**
- Create: `src/canon/adapters/__init__.py`
- Create: `src/canon/adapters/codex.py`
- Create: `src/canon/adapters/claude_code.py`
- Test: `tests/test_codex_adapter.py`
- Test: `tests/test_claude_code_adapter.py`

**Interfaces:**
- Consumes: foundation `CapsuleBundle`, `descriptor_for(adapter_id: str) -> AdapterDescriptor`.
- Produces:

```python
CODEX_NATIVE_ADVISORY_NOTE = "Codex AGENTS.md loading is native-advisory and not a technical enforcement gate until a wrapper or native hook proves a blocking pre-first-work gate."

@dataclass(frozen=True, slots=True)
class ShimPlan:
    adapter_id: str
    integration_tier: str
    target_files: tuple[str, ...]
    launch_command: tuple[str, ...]
    canon_md: str
    witness_required: bool
    enforcement_note: str

def codex_shim_plan(bundle: CapsuleBundle, *, workspace: str) -> ShimPlan:
    """Return advisory AGENTS.md write targets for a Codex workspace."""

def claude_code_shim_plan(bundle: CapsuleBundle, *, workspace: str, home: str) -> ShimPlan:
    """Return advisory CLAUDE.md write targets for workspace and optional global surfaces."""
```

- [ ] **Step 1: Write failing Codex shim tests**

Add:

```python
from canon.adapters.codex import CODEX_NATIVE_ADVISORY_NOTE, codex_shim_plan

def test_codex_shim_targets_workspace_agents_md_and_labels_native_advisory(bundle_factory):
    plan = codex_shim_plan(bundle_factory(), workspace="C:/repo")
    assert plan.adapter_id == "codex-cli"
    assert plan.integration_tier == "native-advisory"
    assert plan.target_files == ("C:/repo/AGENTS.md",)
    assert plan.enforcement_note == CODEX_NATIVE_ADVISORY_NOTE
    assert "not a technical enforcement gate" in CODEX_NATIVE_ADVISORY_NOTE
    assert "enforced" not in plan.enforcement_note
```

- [ ] **Step 2: Run focused Codex test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_codex_adapter.py::test_codex_shim_targets_workspace_agents_md_and_labels_native_advisory -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.adapters'`.

- [ ] **Step 3: Implement Codex shim**

Return target file `os.path.normpath(os.path.join(workspace, "AGENTS.md"))`. Return `launch_command=("codex",)` only as a display plan; do not call Codex. Set `witness_required=True` and `enforcement_note=CODEX_NATIVE_ADVISORY_NOTE`.

- [ ] **Step 4: Write failing Claude Code shim tests**

Add:

```python
from canon.adapters.claude_code import claude_code_shim_plan

def test_claude_code_shim_targets_claude_files_and_labels_native_advisory(bundle_factory):
    plan = claude_code_shim_plan(bundle_factory(), workspace="C:/repo", home="C:/home")
    assert plan.adapter_id == "claude-code"
    assert plan.integration_tier == "native-advisory"
    assert plan.target_files == (
        "C:/home/.claude/CLAUDE.md",
        "C:/repo/CLAUDE.md",
    )
    assert "startup context is advisory" in plan.enforcement_note
```

- [ ] **Step 5: Implement Claude Code shim**

Return normalized target files in global then workspace order. Return `launch_command=("claude",)` only as a display plan. Do not install hooks, settings, or marker regions in this task.

- [ ] **Step 6: Add no-overclaim tests**

Add:

```python
def test_thin_shims_do_not_claim_enforced_without_wrapper_or_hook_fixture(bundle_factory):
    codex = codex_shim_plan(bundle_factory(), workspace="C:/repo")
    claude = claude_code_shim_plan(bundle_factory(), workspace="C:/repo", home="C:/home")
    assert codex.integration_tier == "native-advisory"
    assert claude.integration_tier == "native-advisory"
    assert "enforced" not in codex.enforcement_note
    assert "enforced" not in claude.enforcement_note
```

- [ ] **Step 7: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_codex_adapter.py tests/test_claude_code_adapter.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/canon/adapters tests/test_codex_adapter.py tests/test_claude_code_adapter.py
git commit -m "feat: add codex and claude code shims"
```

### Task 6: Controlled API and Local OpenAI-Compatible Runners

**Files:**
- Create: `src/canon/runners/__init__.py`
- Create: `src/canon/runners/api.py`
- Create: `src/canon/runners/local_openai.py`
- Test: `tests/test_api_runner.py`
- Test: `tests/test_local_openai_runner.py`

**Interfaces:**
- Consumes: foundation `CapsuleBundle`, bootstrap-owned `BootstrapReport`, foundation `BootstrapWitness`, foundation `AdapterDescriptor`.
- Produces:

```python
Sender = Callable[[Mapping[str, object]], Mapping[str, object]]

@dataclass(frozen=True, slots=True)
class RunnerResult:
    ok: bool
    request_sent: bool
    response: Mapping[str, object] | None
    witness: BootstrapWitness | None
    failure_code: str | None

def build_openai_request(
    request: Mapping[str, object],
    *,
    bundle: CapsuleBundle,
) -> dict:
    """Return an OpenAI-compatible request with Canon instructions injected."""

def run_enforced_request(
    request: Mapping[str, object],
    *,
    bundle: CapsuleBundle,
    adapter: AdapterDescriptor,
    bootstrap_report: BootstrapReport,
    send: Sender,
) -> RunnerResult:
    """Gate one model request behind bootstrap success and witness availability."""

def local_endpoint_profile(
    *,
    base_url: str,
    model: str,
    observed_model: str | None,
    unsupported_fields: tuple[str, ...],
    context_window: int | None,
    tool_calling: str,
) -> dict:
    """Return normalized local endpoint capability data for admission checks."""

def admit_local_quality_run(profile: Mapping[str, object], *, model_family: str) -> tuple[bool, str | None]:
    """Return whether a local profile may run quality-critical Canon tasks."""
```

- [ ] **Step 1: Write failing API enforcement tests**

Add:

```python
from canon.runners.api import build_openai_request, run_enforced_request

def test_enforced_runner_does_not_call_sender_when_bootstrap_failed(bundle_factory, bootstrap_report_factory, descriptor_factory):
    calls = []
    def sender(payload):
        calls.append(payload)
        return {"id": "resp-1"}
    result = run_enforced_request(
        {"model": "gpt-test", "input": "continue"},
        bundle=bundle_factory(),
        adapter=descriptor_factory("api-runner"),
        bootstrap_report=bootstrap_report_factory(ok=False, failure_code="readiness_failed"),
        send=sender,
    )
    assert result.ok is False
    assert result.request_sent is False
    assert result.failure_code == "readiness_failed"
    assert calls == []

def test_runner_request_includes_canon_md_and_manifest_hash(bundle_factory):
    bundle = bundle_factory()
    request = build_openai_request({"model": "gpt-test", "input": "continue"}, bundle=bundle)
    assert request["model"] == "gpt-test"
    assert request["metadata"]["canon_capsule_id"] == bundle.capsule.capsule_id
    assert bundle.canon_md in request["input"][0]["content"][0]["text"]
```

- [ ] **Step 2: Run focused API tests and verify they fail**

Run: `python -m pytest -p no:cacheprovider tests/test_api_runner.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.runners'`.

- [ ] **Step 3: Implement the controlled sender gate**

`run_enforced_request()` must inspect `bootstrap_report.ok`, `bootstrap_report.failure_code`, `adapter.integration_tier`, and `adapter.bootstrap["can_block_before_work"]`. If the report is not ok, the failure code is not `ok`, the adapter is not `enforced`, or the adapter cannot block before work, return without calling `send`. If all gates pass, call `send()` exactly once with `build_openai_request(...)`.

- [ ] **Step 4: Write local endpoint admission tests**

Add:

```python
from canon.runners.local_openai import admit_local_quality_run, local_endpoint_profile

def test_local_endpoint_profile_declares_openai_compatible_subset_losses():
    profile = local_endpoint_profile(
        base_url="http://127.0.0.1:8000/v1",
        model="local-14b",
        observed_model="local-14b",
        unsupported_fields=("parallel_tool_calls", "user"),
        context_window=32768,
        tool_calling="unknown",
    )
    assert profile["schema"] == "canon.local-endpoint-profile/v1"
    assert profile["unsupported_fields"] == ["parallel_tool_calls", "user"]
    assert profile["tool_calling"] == "unknown"

def test_local_14b_32b_quality_runs_block_without_endpoint_profile_and_gate():
    ok, reason = admit_local_quality_run({}, model_family="14B")
    assert ok is False
    assert reason == "endpoint_profile_missing"
    profile = local_endpoint_profile(
        base_url="http://127.0.0.1:8000/v1",
        model="local-32b",
        observed_model=None,
        unsupported_fields=(),
        context_window=None,
        tool_calling="unknown",
    )
    ok, reason = admit_local_quality_run(profile, model_family="32B")
    assert ok is False
    assert reason == "endpoint_gate_missing"
```

- [ ] **Step 5: Implement local endpoint profile and admission**

Admission requires schema `canon.local-endpoint-profile/v1`, non-empty `observed_model`, positive integer `context_window`, and `endpoint_generation_gate_sha256` present. Missing profile returns `endpoint_profile_missing`; missing gate returns `endpoint_gate_missing`; otherwise return `(True, None)`.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_api_runner.py tests/test_local_openai_runner.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/canon/runners tests/test_api_runner.py tests/test_local_openai_runner.py
git commit -m "feat: add controlled api runners"
```

### Task 7: MCP Read-Only Preview and Doctor

**Files:**
- Create: `src/canon/mcp_readonly.py`
- Test: `tests/test_mcp_readonly.py`

**Interfaces:**
- Consumes: `CapsuleBundle`, `DoctorReport`, `render_accessible_preview_markdown`.
- Produces:

```python
MCP_RESOURCES = (
    "canon://capsule/current",
    "canon://capsule/current/manifest",
    "canon://capsule/current/canon-md",
    "canon://capsule/current/omissions",
    "canon://capsule/current/doctor",
    "canon://capsule/current/receipts",
)

READ_ONLY_TOOLS = ("canon.preview", "canon.doctor", "canon.compile.check")

def list_mcp_resources() -> tuple[dict, ...]:
    """Return read-only Canon MCP resource descriptors."""

def read_mcp_resource(uri: str, *, bundle: CapsuleBundle, doctor_report: DoctorReport) -> dict:
    """Return one read-only Canon MCP resource payload."""

def list_mcp_tools() -> tuple[dict, ...]:
    """Return read-only Canon MCP tool descriptors."""

def call_mcp_tool(
    name: str,
    arguments: Mapping[str, object],
    *,
    bundle: CapsuleBundle,
    doctor_report: DoctorReport,
) -> dict:
    """Execute one allowed read-only MCP tool and reject all mutating names."""
```

- [ ] **Step 1: Write failing resource tests**

Add:

```python
from canon.mcp_readonly import MCP_RESOURCES, list_mcp_resources, read_mcp_resource

def test_mcp_resources_expose_manifest_canon_md_omissions_doctor_receipts(bundle_factory, doctor_report_factory):
    uris = [row["uri"] for row in list_mcp_resources()]
    assert tuple(uris) == MCP_RESOURCES
    bundle = bundle_factory()
    report = doctor_report_factory(codes=[])
    canon_md = read_mcp_resource("canon://capsule/current/canon-md", bundle=bundle, doctor_report=report)
    assert canon_md["mimeType"] == "text/markdown"
    assert bundle.capsule.capsule_id in canon_md["text"]
```

- [ ] **Step 2: Run focused MCP tests and verify they fail**

Run: `python -m pytest -p no:cacheprovider tests/test_mcp_readonly.py::test_mcp_resources_expose_manifest_canon_md_omissions_doctor_receipts -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.mcp_readonly'`.

- [ ] **Step 3: Implement dependency-free MCP payload functions**

Do not add an MCP runtime dependency. Return plain dictionaries shaped for an MCP server wrapper to expose later. Unknown URI returns:

```python
{"isError": True, "code": "unknown_resource", "message": "Unknown Canon MCP resource: <uri>"}
```

- [ ] **Step 4: Write read-only and secret tests**

Add:

```python
from canon.mcp_readonly import call_mcp_tool, list_mcp_tools

def test_mcp_tools_are_read_only_in_now_cut():
    names = [row["name"] for row in list_mcp_tools()]
    assert names == ["canon.preview", "canon.doctor", "canon.compile.check"]
    assert all(row["readOnlyHint"] is True for row in list_mcp_tools())

def test_mcp_tool_results_include_typed_errors_and_no_secret_values(bundle_factory, doctor_report_factory):
    result = call_mcp_tool(
        "canon.import",
        {},
        bundle=bundle_factory(secret_canary="CANARY_API_KEY_DO_NOT_EXPORT_fixture"),
        doctor_report=doctor_report_factory(codes=[]),
    )
    assert result["isError"] is True
    assert result["code"] == "unknown_tool"
    assert "CANARY_API_KEY_DO_NOT_EXPORT" not in str(result)
```

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_mcp_readonly.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/mcp_readonly.py tests/test_mcp_readonly.py
git commit -m "feat: add read-only mcp preview"
```

### Task 8: A2A Artifact Mapping

**Files:**
- Create: `src/canon/a2a.py`
- Test: `tests/test_a2a.py`

**Interfaces:**
- Consumes: `CapsuleBundle`, `ReadinessProbe`, `BootstrapWitness`.
- Produces:

```python
def capsule_to_a2a_artifacts(bundle: CapsuleBundle) -> tuple[dict, ...]:
    """Return A2A artifacts for capsule manifest, CANON.md, and receipts."""

def bootstrap_task_message(bundle: CapsuleBundle, probe: ReadinessProbe) -> dict:
    """Return an A2A task message for Canon bootstrap preview."""

def witness_artifact(witness: BootstrapWitness) -> dict:
    """Return an A2A artifact that carries bootstrap witness metadata."""

def a2a_loss(reason: str, *, detail: str) -> dict:
    """Return one typed A2A loss record."""
```

- [ ] **Step 1: Write failing artifact mapping tests**

Add:

```python
from canon.a2a import bootstrap_task_message, capsule_to_a2a_artifacts
from canon.canonical_json import canonical_json_bytes, sha256_bytes
from canon.readiness import build_readiness_probe

def test_capsule_maps_to_markdown_and_json_artifacts_with_content_types(bundle_factory):
    bundle = bundle_factory()
    artifacts = capsule_to_a2a_artifacts(bundle)
    assert [item["name"] for item in artifacts] == ["CANON.md", "canon.capsule.json"]
    assert artifacts[0]["parts"][0]["mimeType"] == "text/markdown"
    assert artifacts[1]["parts"][0]["mimeType"] == "application/json"
    assert artifacts[0]["metadata"]["canon_capsule_id"] == bundle.capsule.capsule_id

def test_a2a_bootstrap_task_contains_probe_and_capsule_artifact_ids(bundle_factory):
    bundle = bundle_factory()
    probe = build_readiness_probe(bundle.capsule)
    message = bootstrap_task_message(bundle, probe)
    assert message["kind"] == "canon.a2a.bootstrap-task/v1"
    assert message["capsule_id"] == bundle.capsule.capsule_id
    assert message["probe_sha256"] == sha256_bytes(canonical_json_bytes(probe.to_dict()))
    assert message["integration_tier"] == "guided"
```

- [ ] **Step 2: Run focused tests and verify they fail**

Run: `python -m pytest -p no:cacheprovider tests/test_a2a.py::test_capsule_maps_to_markdown_and_json_artifacts_with_content_types -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.a2a'`.

- [ ] **Step 3: Implement A2A mapping**

Use deterministic artifact ids:

```python
artifact_id = "canon-artifact-" + sha256_bytes(content_bytes).removeprefix("sha256:")[:24]
```

Set A2A `integration_tier` to `guided` unless a controller-supplied fixture result proves a stronger effective tier in a later task. Do not put absolute local paths in artifact metadata.

- [ ] **Step 4: Write loss and witness tests**

Add:

```python
from canon.a2a import a2a_loss, witness_artifact

def test_a2a_history_truncation_or_content_type_rejection_is_typed_loss():
    loss = a2a_loss("history_truncated", detail="historyLength omitted prior capsule message")
    assert loss == {
        "schema": "canon.adapter-loss/v1",
        "surface": "a2a-artifact",
        "reason": "history_truncated",
        "detail": "historyLength omitted prior capsule message",
    }

def test_witness_artifact_has_json_content_type_and_path_clean_metadata(bootstrap_witness_factory):
    witness = bootstrap_witness_factory()
    artifact = witness_artifact(witness)
    assert artifact["name"] == "canon.bootstrap-witness.json"
    assert artifact["parts"][0]["mimeType"] == "application/json"
    assert "C:/" not in str(artifact)
```

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_a2a.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/a2a.py tests/test_a2a.py
git commit -m "feat: map capsules to a2a artifacts"
```

### Task 9: Conformance and Continuity Dry Gates

**Files:**
- Create: `src/canon/conformance.py`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/fixture.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/oracle_facts.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/normative_constraints.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/secret_canaries.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/source_state_manifest.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/adapter_expectations.json`
- Create: `tests/fixtures/continuity_gauntlet/smoke/provider_migration/negative_controls.json`
- Repeat the same seven fixture filenames under `agent_resume`, `repository_continuity`, `parallel_session_merge`, and `ambient_bootstrap`.
- Test: `tests/test_conformance.py`

**Interfaces:**
- Consumes: `AdapterDescriptor`, `CapsuleBundle`, MCP/A2A mapping functions, API/local runner profile functions.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class ConformanceReport:
    ok: bool
    adapter_id: str
    fixture_ids: tuple[str, ...]
    failures: tuple[dict, ...]
    matrix_rows: tuple[dict, ...] = ()
    normative_ok: bool = True

def fixture_check(task_set: Path) -> ConformanceReport:
    """Run one fixture task set and return deterministic conformance failures."""

def adapter_roundtrip(
    bundle: CapsuleBundle,
    *,
    adapters: tuple[AdapterDescriptor, ...],
    fixture_results: Mapping[str, bool],
) -> ConformanceReport:
    """Return import/export round-trip results for every supplied adapter."""

def scan_for_secret_canaries(root: Path, canaries: tuple[str, ...]) -> tuple[str, ...]:
    """Return paths containing forbidden synthetic secret canary strings."""

def conformance_exit_code(report: ConformanceReport) -> int:
    """Return zero only when all conformance checks pass."""

def conformance_report_to_dict(report: ConformanceReport) -> dict:
    """Return canonical JSON-safe conformance report data."""
```

- [ ] **Step 1: Write failing fixture admission tests**

Add:

```python
import json
from pathlib import Path
from canon.conformance import fixture_check, conformance_exit_code

SMOKE = Path("tests/fixtures/continuity_gauntlet/smoke")

def test_fixture_check_requires_all_required_fixture_files():
    report = fixture_check(SMOKE)
    assert report.ok is True
    assert report.normative_ok is True
    assert set(report.fixture_ids) == {
        "provider_migration",
        "agent_resume",
        "repository_continuity",
        "parallel_session_merge",
        "ambient_bootstrap",
    }
    assert conformance_exit_code(report) == 0
```

- [ ] **Step 2: Run focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_conformance.py::test_fixture_check_requires_all_required_fixture_files -q`

Expected: FAIL because fixtures and module do not exist.

- [ ] **Step 3: Add fixture files with synthetic canaries**

Every `secret_canaries.json` must contain only synthetic values such as:

```json
{
  "schema": "canon.secret-canaries/v1",
  "canaries": [
    "CANARY_API_KEY_DO_NOT_EXPORT_provider_migration",
    "BEGIN CANARY PRIVATE KEY provider_migration END CANARY PRIVATE KEY"
  ]
}
```

Every `adapter_expectations.json` must state conservative tiers for the relevant adapter. Example for `ambient_bootstrap`:

```json
{
  "schema": "canon.adapter-expectations/v1",
  "expected": [
    {"adapter_id": "codex-cli", "max_tier_without_fixture": "native-advisory"},
    {"adapter_id": "mcp-readonly", "max_tier_without_fixture": "guided"}
  ]
}
```

- [ ] **Step 4: Implement fixture admission and exit codes**

`fixture_check()` must accept either one task-set directory containing the seven required fixture files or a root directory whose children are task-set directories. It must require the seven filenames in each task-set directory, parse them as JSON, require a `schema` key in each file, and fail if a canary value appears outside its own `secret_canaries.json`. It must set `normative_ok=False` and add failure code `normative_fixture_invalid` when `normative_constraints.json` lacks active-goal, permission, prohibition, or constraint coverage. `conformance_report_to_dict(report)` must emit schema `canon.conformance-report/v1`, `ok`, `adapter_id`, `fixture_ids`, `failures`, `matrix_rows`, and `normative_ok`.

- [ ] **Step 5: Write adapter round-trip and no-overclaim tests**

Add:

```python
from dataclasses import replace

from canon.adapter import descriptor_for
from canon.conformance import adapter_roundtrip

def test_roundtrip_fails_on_undeclared_semantic_loss(bundle_factory):
    desc = descriptor_for("mcp-readonly")
    bundle = bundle_factory(with_undeclared_loss=True)
    report = adapter_roundtrip(bundle, adapters=(desc,), fixture_results={})
    assert report.ok is False
    assert report.failures[0]["code"] == "undeclared_semantic_loss"

def test_no_enforced_tier_without_blocking_fixture(bundle_factory):
    desc = replace(
        descriptor_for("api-runner"),
        integration_tier="enforced",
        bootstrap={"can_block_before_work": True, "entry": "controlled-wrapper"},
    )
    report = adapter_roundtrip(bundle_factory(), adapters=(desc,), fixture_results={})
    assert any(item["code"] == "tier_mislabeled" for item in report.failures)

def test_roundtrip_report_preserves_guided_builtin_matrix_row(bundle_factory):
    desc = descriptor_for("api-runner")
    report = adapter_roundtrip(bundle_factory(), adapters=(desc,), fixture_results={"api-runner": True})
    assert report.matrix_rows[0]["adapter_id"] == "api-runner"
    assert report.matrix_rows[0]["effective_tier"] == "guided"
```

- [ ] **Step 6: Implement round-trip checks**

Check each adapter's `losses` against capsule omissions and transforms. If an adapter cannot carry typed capsule semantics and no declared loss names that field, return failure `undeclared_semantic_loss`. If `desc.integration_tier` is `enforced` and `effective_tier(desc, fixture_results)` is not `enforced`, return `tier_mislabeled`. Populate `matrix_rows` by calling `adapter_matrix(fixture_results)` and filtering to the supplied adapter ids.

- [ ] **Step 7: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_conformance.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/canon/conformance.py tests/test_conformance.py tests/fixtures/continuity_gauntlet
git commit -m "feat: add continuity conformance dry gates"
```

### Task 10: Internal Continuity and Conformance CLI Registration

**Files:**
- Modify: `src/canon/cli.py`
- Test: `tests/test_continuity_conformance_cli.py`

**Interfaces:**
- Consumes: `fixture_check(task_set: Path) -> ConformanceReport`, `scan_for_secret_canaries(root: Path, canaries: tuple[str, ...]) -> tuple[str, ...]`, `conformance_exit_code(report: ConformanceReport) -> int`, `conformance_report_to_dict(report: ConformanceReport) -> dict`, `canonical_json_text(value: object) -> str`, and the existing bootstrap CLI `run_cli(argv, stdout, stderr, environ) -> int`.
- Produces: parser registrations for exactly `python -m canon continuity fixture-check <task_set>`, `python -m canon continuity secret-scan <run_root>`, and `python -m canon conformance run <fixture_root> --out <out>`.

- [ ] **Step 1: Write failing CLI registration tests**

Create `tests/test_continuity_conformance_cli.py`:

```python
from __future__ import annotations

import io
import json
from pathlib import Path

from canon.cli import run_cli


SMOKE = Path("tests/fixtures/continuity_gauntlet/smoke")
PYTHON_M_CANON = "python -m canon "


def _run(args: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_cli(args, stdout=stdout, stderr=stderr, environ={})
    return code, stdout.getvalue(), stderr.getvalue()


def _argv(command: str) -> list[str]:
    assert command.startswith(PYTHON_M_CANON)
    return command.removeprefix(PYTHON_M_CANON).split()


def test_continuity_fixture_check_cli_calls_conformance_fixture_check():
    command = f"python -m canon continuity fixture-check {SMOKE / 'provider_migration'}"
    code, stdout, stderr = _run(_argv(command))
    assert code == 0
    assert stderr == ""
    payload = json.loads(stdout)
    assert payload["schema"] == "canon.conformance-report/v1"
    assert payload["ok"] is True
    assert payload["fixture_ids"] == ["provider_migration"]


def test_continuity_secret_scan_cli_reports_no_canary_leak(tmp_path):
    run_root = tmp_path / "run"
    run_root.mkdir()
    (run_root / "secret_canaries.json").write_text(
        json.dumps({
            "schema": "canon.secret-canaries/v1",
            "canaries": ["CANARY_API_KEY_DO_NOT_EXPORT_cli"]
        }),
        encoding="utf-8",
    )
    (run_root / "generated.txt").write_text("safe generated content", encoding="utf-8")
    command = f"python -m canon continuity secret-scan {run_root}"
    code, stdout, stderr = _run(_argv(command))
    assert code == 0
    assert stderr == ""
    payload = json.loads(stdout)
    assert payload == {
        "schema": "canon.secret-scan-result/v1",
        "ok": True,
        "failure_count": 0,
        "failures": [],
    }


def test_conformance_run_cli_writes_report_to_out(tmp_path):
    out = tmp_path / "conformance-report.json"
    command = f"python -m canon conformance run {SMOKE} --out {out}"
    code, stdout, stderr = _run(_argv(command))
    assert code == 0
    assert stderr == ""
    assert json.loads(stdout) == {
        "schema": "canon.conformance-run-result/v1",
        "ok": True,
        "out": str(out),
    }
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["schema"] == "canon.conformance-report/v1"
    assert payload["ok"] is True
    assert "matrix_rows" in payload
    assert isinstance(payload["matrix_rows"], list)


def test_internal_cli_does_not_register_public_console_script():
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "[project.scripts]" not in text
    assert "continuity =" not in text
    assert "conformance =" not in text
```

- [ ] **Step 2: Run the focused CLI tests and verify they fail**

Run: `python -m pytest -p no:cacheprovider tests/test_continuity_conformance_cli.py -q`

Expected: FAIL because `src/canon/cli.py` does not register the continuity and conformance subcommands yet.

- [ ] **Step 3: Register internal commands in `src/canon/cli.py`**

Modify the existing bootstrap CLI parser only. Do not add a public script, console entry point, shell script, or standalone module. The command handlers must call the Task 9 conformance APIs:

```python
from pathlib import Path

from .canonical_json import canonical_json_text
from .conformance import (
    conformance_exit_code,
    conformance_report_to_dict,
    fixture_check,
    scan_for_secret_canaries,
)


def _load_secret_canaries(run_root: Path) -> tuple[str, ...]:
    canaries: list[str] = []
    for path in sorted(run_root.rglob("secret_canaries.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        canaries.extend(str(item) for item in data.get("canaries", ()))
    return tuple(canaries)


def _cmd_continuity_fixture_check(args, stdout, stderr) -> int:
    report = fixture_check(Path(args.task_set))
    stdout.write(canonical_json_text(conformance_report_to_dict(report)))
    return conformance_exit_code(report)


def _cmd_continuity_secret_scan(args, stdout, stderr) -> int:
    failures = scan_for_secret_canaries(Path(args.run_root), _load_secret_canaries(Path(args.run_root)))
    payload = {
        "schema": "canon.secret-scan-result/v1",
        "ok": not failures,
        "failure_count": len(failures),
        "failures": list(failures),
    }
    stdout.write(canonical_json_text(payload))
    return 0 if not failures else 4


def _cmd_conformance_run(args, stdout, stderr) -> int:
    report = fixture_check(Path(args.fixture_root))
    Path(args.out).write_text(canonical_json_text(conformance_report_to_dict(report)), encoding="utf-8")
    stdout.write(canonical_json_text({
        "schema": "canon.conformance-run-result/v1",
        "ok": report.ok,
        "out": str(Path(args.out)),
    }))
    return conformance_exit_code(report)
```

Add the parser wiring inside the existing parser construction function in `src/canon/cli.py`. If the bootstrap CLI already has `_build_parser()`, extend that function; otherwise create this exact structure and merge existing commands into the same `subparsers` object:

```python
import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m canon")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Existing bootstrap CLI command registrations stay in this function.

    continuity_parser = subparsers.add_parser("continuity")
    continuity_subparsers = continuity_parser.add_subparsers(dest="continuity_command", required=True)

    fixture_check_parser = continuity_subparsers.add_parser("fixture-check")
    fixture_check_parser.add_argument("task_set")
    fixture_check_parser.set_defaults(handler=_cmd_continuity_fixture_check)

    secret_scan_parser = continuity_subparsers.add_parser("secret-scan")
    secret_scan_parser.add_argument("run_root")
    secret_scan_parser.set_defaults(handler=_cmd_continuity_secret_scan)

    conformance_parser = subparsers.add_parser("conformance")
    conformance_subparsers = conformance_parser.add_subparsers(dest="conformance_command", required=True)

    conformance_run_parser = conformance_subparsers.add_parser("run")
    conformance_run_parser.add_argument("fixture_root")
    conformance_run_parser.add_argument("--out", required=True)
    conformance_run_parser.set_defaults(handler=_cmd_conformance_run)

    return parser
```

The wiring primitives are:

```python
continuity_parser = subparsers.add_parser("continuity")
continuity_subparsers = continuity_parser.add_subparsers(dest="continuity_command", required=True)

fixture_check_parser = continuity_subparsers.add_parser("fixture-check")
fixture_check_parser.add_argument("task_set")
fixture_check_parser.set_defaults(handler=_cmd_continuity_fixture_check)

secret_scan_parser = continuity_subparsers.add_parser("secret-scan")
secret_scan_parser.add_argument("run_root")
secret_scan_parser.set_defaults(handler=_cmd_continuity_secret_scan)

conformance_parser = subparsers.add_parser("conformance")
conformance_subparsers = conformance_parser.add_subparsers(dest="conformance_command", required=True)

conformance_run_parser = conformance_subparsers.add_parser("run")
conformance_run_parser.add_argument("fixture_root")
conformance_run_parser.add_argument("--out", required=True)
conformance_run_parser.set_defaults(handler=_cmd_conformance_run)
```

Parser shape must accept exactly these forms:

```text
python -m canon continuity fixture-check <task_set>
python -m canon continuity secret-scan <run_root>
python -m canon conformance run <fixture_root> --out <out>
```

- [ ] **Step 4: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_continuity_conformance_cli.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 5: Review gate**

Run: `rg -n "continuity|fixture-check|secret-scan|conformance|project\\.scripts|console_scripts" src/canon/cli.py pyproject.toml tests/test_continuity_conformance_cli.py`

Expected: matches show the commands registered only under `src/canon/cli.py` and tests; no public script registration appears in `pyproject.toml`.

- [ ] **Step 6: Commit**

```bash
git add src/canon/cli.py tests/test_continuity_conformance_cli.py
git commit -m "feat: add internal continuity conformance cli"
```

## Next Cut

Tasks 11 through 13 are the Next cut. They depend on the Now cut being green and add local continuity recording, branch/session merge, and conservative desktop/browser/IDE boundaries without building app extensions yet.

### Task 11: Local Continuity Flight Recorder with Raw Content Off

**Files:**
- Create: `src/canon/flight_recorder.py`
- Test: `tests/test_flight_recorder.py`

**Interfaces:**
- Consumes: `canonical_json_bytes(value: object) -> bytes`, `sha256_bytes(data: bytes) -> str`.
- Produces:

```python
FLIGHT_EVENT_SCHEMA = "canon.flight-event/v1"

@dataclass(frozen=True, slots=True)
class FlightEvent:
    run_id: str
    sequence: int
    event_type: str
    scope_key: str
    subject_id: str
    metadata: dict
    source_refs: tuple[str, ...] = ()
    raw_content_included: bool = False
    content_sha256: str | None = None
    content_bytes: int | None = None

    def to_dict(self) -> dict:
        """Return a JSON-safe event payload without raw prompt or response bytes."""

@dataclass(frozen=True, slots=True)
class FlightEventReceipt:
    event_id: str
    event_sha256: str
    path: str
    raw_content_included: bool

def event_id(event: FlightEvent) -> str:
    """Return a deterministic event id from run id and sequence."""

def build_event(
    *,
    run_id: str,
    sequence: int,
    event_type: str,
    scope_key: str,
    subject_id: str,
    metadata: Mapping[str, object],
    source_refs: tuple[str, ...] = (),
    raw_content: bytes | None = None,
    capture_policy: str = "metadata-only",
) -> FlightEvent:
    """Return a flight event that records metadata by default and never inlines raw content."""

def append_event(root: Path, event: FlightEvent) -> FlightEventReceipt:
    """Append one event and return its receipt."""

def replay_events(root: Path, *, run_id: str) -> tuple[FlightEvent, ...]:
    """Return events for one run ordered by sequence and verified by receipt hash."""
```

- [ ] **Step 1: Write failing metadata-only tests**

Add:

```python
from canon.flight_recorder import build_event

def test_metadata_only_event_hashes_raw_content_but_does_not_store_it():
    raw = b"operator correction: keep advisory tier"
    event = build_event(
        run_id="run-1",
        sequence=1,
        event_type="operator-correction",
        scope_key="workspace",
        subject_id="adapter-tier",
        metadata={"decision": "keep Codex native-advisory"},
        raw_content=raw,
    )
    assert event.raw_content_included is False
    assert event.content_sha256 is not None
    assert event.content_bytes == len(raw)
    assert raw.decode("utf-8") not in str(event.to_dict())
```

Do not store raw bytes in metadata-only mode.

- [ ] **Step 2: Run focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_flight_recorder.py::test_metadata_only_event_hashes_raw_content_but_does_not_store_it -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.flight_recorder'`.

- [ ] **Step 3: Implement event serialization and policy**

Valid `capture_policy` values are `metadata-only`, `private-raw`, and `disabled`. `metadata-only` hashes raw content and omits it. `private-raw` sets `raw_content_included=True` and stores only `raw_content_sha256`, `content_bytes`, and a private-storage locator supplied in metadata; it still does not inline raw bytes. `disabled` must not be passed to `append_event()`.

- [ ] **Step 4: Write append, replay, idempotence, and secret tests**

Add:

```python
from canon.flight_recorder import append_event, replay_events

def test_append_event_is_idempotent_for_same_event_and_refuses_changed_duplicate(tmp_path):
    event = build_event(
        run_id="run-1",
        sequence=1,
        event_type="frontier-state",
        scope_key="workspace",
        subject_id="frontier",
        metadata={"next_action": "run adapter tests"},
    )
    first = append_event(tmp_path, event)
    second = append_event(tmp_path, event)
    assert second == first
    changed = build_event(
        run_id="run-1",
        sequence=1,
        event_type="frontier-state",
        scope_key="workspace",
        subject_id="frontier",
        metadata={"next_action": "run all tests"},
    )
    try:
        append_event(tmp_path, changed)
    except ValueError as error:
        assert "changed duplicate event" in str(error)
    else:
        raise AssertionError("changed duplicate sequence must be refused")

def test_replay_orders_by_sequence_not_wall_clock(tmp_path):
    later = build_event(run_id="run-1", sequence=2, event_type="decision", scope_key="workspace", subject_id="b", metadata={})
    earlier = build_event(run_id="run-1", sequence=1, event_type="decision", scope_key="workspace", subject_id="a", metadata={})
    append_event(tmp_path, later)
    append_event(tmp_path, earlier)
    assert [event.sequence for event in replay_events(tmp_path, run_id="run-1")] == [1, 2]

def test_secret_canary_not_present_in_event_payload_or_receipt(tmp_path):
    secret = "CANARY_API_KEY_DO_NOT_EXPORT_flight"
    event = build_event(
        run_id="run-1",
        sequence=1,
        event_type="tool-outcome",
        scope_key="workspace",
        subject_id="probe",
        metadata={"redacted": True},
        raw_content=secret.encode("utf-8"),
    )
    receipt = append_event(tmp_path, event)
    assert secret not in str(event.to_dict())
    assert secret not in str(receipt)
    assert secret not in (tmp_path / receipt.path).read_text(encoding="utf-8")
```

- [ ] **Step 5: Implement append-only paths**

Write event files under `<root>/events/<run_id>/<sequence>-<event_id>.json`. Return a path relative to `root`. Reject absolute `run_id`, path separators in `run_id`, negative sequence, unknown event type, and changed duplicate sequence/event ids.

- [ ] **Step 6: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_flight_recorder.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/canon/flight_recorder.py tests/test_flight_recorder.py
git commit -m "feat: add continuity flight recorder"
```

### Task 12: Branch and Session Capsule Merge

**Files:**
- Create: `src/canon/session_merge.py`
- Test: `tests/test_session_merge.py`

**Interfaces:**
- Consumes: foundation `Capsule`, foundation `CanonAtom`, `semantic_atom_key(atom: CanonAtom) -> tuple[str, str, str]`, `SemanticDiff`, `FlightEvent`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class CapsuleHead:
    capsule_id: str
    source_state_digest: str
    branch: str | None
    session_id: str | None

@dataclass(frozen=True, slots=True)
class MergeConflict:
    key: tuple[str, str, str]
    reason: str
    left_sha256: str | None
    right_sha256: str | None
    base_sha256: str | None

@dataclass(frozen=True, slots=True)
class MergePlan:
    ok: bool
    merged_atoms: tuple[CanonAtom, ...]
    conflicts: tuple[MergeConflict, ...]
    parent_capsule_ids: tuple[str, ...]

def merge_capsules(
    *,
    base: Capsule | None,
    left: Capsule,
    right: Capsule,
    resolutions: Mapping[tuple[str, str, str], str] = {},
) -> MergePlan:
    """Return automatic merges and explicit semantic conflicts for three capsule heads."""

def merge_witness(plan: MergePlan) -> dict:
    """Return canonical merge witness data for receipts and review."""
```

- [ ] **Step 1: Write failing three-way merge tests**

Add:

```python
from canon.session_merge import merge_capsules

def test_three_way_merge_takes_left_only_and_right_only_changes(capsule_factory, atom_factory):
    base = capsule_factory(atoms=[atom_factory("decision", "shared", value={"text": "base"})])
    left = capsule_factory(atoms=[
        atom_factory("decision", "shared", value={"text": "base"}),
        atom_factory("frontier-state", "left-only", value={"next": "test adapters"}),
    ])
    right = capsule_factory(atoms=[
        atom_factory("decision", "shared", value={"text": "base"}),
        atom_factory("unknown", "right-only", value={"text": "MCP host support"}),
    ])
    plan = merge_capsules(base=base, left=left, right=right)
    assert plan.ok is True
    assert {atom.id for atom in plan.merged_atoms} == {"shared", "left-only", "right-only"}
    assert plan.conflicts == ()
```

- [ ] **Step 2: Run focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_session_merge.py::test_three_way_merge_takes_left_only_and_right_only_changes -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.session_merge'`.

- [ ] **Step 3: Implement atom merge by key and canonical hash**

Use `semantic_atom_key(atom)` and `sha256_bytes(canonical_json_bytes(atom.to_dict()))`. Three-way rules:

- If left hash equals right hash, keep one.
- If base exists and left hash equals base hash, take right.
- If base exists and right hash equals base hash, take left.
- If base is absent and only one side has the key, take that side.
- Otherwise create `MergeConflict` and omit that atom from `merged_atoms` unless `resolutions[key]` is `left` or `right`.

- [ ] **Step 4: Add conflict and no-newest tests**

Add:

```python
def test_same_atom_divergent_normative_change_conflicts(capsule_factory, atom_factory):
    base = capsule_factory(atoms=[atom_factory("prohibition", "no-deploy", value={"text": "do not deploy"})])
    left = capsule_factory(atoms=[atom_factory("prohibition", "no-deploy", value={"text": "do not deploy or publish"})])
    right = capsule_factory(atoms=[atom_factory("prohibition", "no-deploy", value={"text": "do not deploy"})])
    plan = merge_capsules(base=base, left=left, right=right)
    assert plan.ok is True
    assert plan.conflicts == ()
    assert plan.merged_atoms[0].value["text"] == "do not deploy or publish"

def test_no_base_conflicts_on_same_key_different_payload(capsule_factory, atom_factory):
    left = capsule_factory(atoms=[atom_factory("active-goal", "goal", value={"text": "A"}, create_time="2026-08-30T10:00:00Z")])
    right = capsule_factory(atoms=[atom_factory("active-goal", "goal", value={"text": "B"}, create_time="2026-08-30T11:00:00Z")])
    plan = merge_capsules(base=None, left=left, right=right)
    assert plan.ok is False
    assert plan.conflicts[0].reason == "same_key_diverged_without_base"
    assert plan.merged_atoms == ()
```

- [ ] **Step 5: Write merge witness tests**

Add:

```python
from canon.session_merge import merge_witness

def test_merge_witness_includes_parent_capsule_digests_and_resolution_decisions(capsule_factory, atom_factory):
    left = capsule_factory(capsule_id="sha256:" + "a" * 64, atoms=[atom_factory("active-goal", "goal", value={"text": "A"})])
    right = capsule_factory(capsule_id="sha256:" + "b" * 64, atoms=[atom_factory("active-goal", "goal", value={"text": "B"})])
    key = ("active-goal", "workspace", "goal")
    plan = merge_capsules(base=None, left=left, right=right, resolutions={key: "left"})
    witness = merge_witness(plan)
    assert witness["schema"] == "canon.merge-witness/v1"
    assert witness["parent_capsule_ids"] == ("sha256:" + "a" * 64, "sha256:" + "b" * 64)
    assert witness["ok"] is True
    assert "C:/" not in str(witness)
```

- [ ] **Step 6: Implement witness**

Witness fields are `schema`, `ok`, `parent_capsule_ids`, `merged_count`, `conflict_count`, `conflicts`, and `does_not_prove`. Include does-not-prove entries for semantic equivalence, complete history, and absence of private state.

- [ ] **Step 7: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_session_merge.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/canon/session_merge.py tests/test_session_merge.py
git commit -m "feat: add branch session capsule merge"
```

### Task 13: Desktop, Browser, IDE, and Boundary UX Records

**Files:**
- Create: `src/canon/ux_boundaries.py`
- Test: `tests/test_ux_boundaries.py`

**Interfaces:**
- Consumes: `descriptor_for(adapter_id: str) -> AdapterDescriptor`, `effective_tier(desc: AdapterDescriptor, fixture_results: Mapping[str, bool]) -> str`.
- Produces:

```python
@dataclass(frozen=True, slots=True)
class SurfaceBoundary:
    surface_id: str
    horizon: str
    truthful_tier: str
    allowed_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    user_copy: str

def boundary_for(surface_id: str) -> SurfaceBoundary:
    """Return one conservative UX boundary record by surface id."""

def all_boundaries() -> tuple[SurfaceBoundary, ...]:
    """Return every conservative UX boundary record sorted by surface id."""
```

- [ ] **Step 1: Write failing boundary tests**

Add:

```python
from canon.ux_boundaries import all_boundaries, boundary_for

def test_desktop_browser_ide_are_next_not_now():
    rows = {row.surface_id: row for row in all_boundaries()}
    assert rows["desktop-launcher"].horizon == "Next"
    assert rows["browser-companion"].horizon == "Next"
    assert rows["ide-extension"].horizon == "Next"

def test_browser_closed_app_copy_does_not_claim_enforced():
    row = boundary_for("browser-companion")
    assert row.truthful_tier == "guided"
    assert "does not currently expose a Canon-verified blocking startup lifecycle" in row.user_copy
    assert "enforced" not in row.user_copy
```

- [ ] **Step 2: Run focused test and verify it fails**

Run: `python -m pytest -p no:cacheprovider tests/test_ux_boundaries.py::test_desktop_browser_ide_are_next_not_now -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'canon.ux_boundaries'`.

- [ ] **Step 3: Implement boundary records**

Create records for:

- `desktop-launcher`: horizon `Next`, tier `guided`, allowed `preview`, `doctor`, `provider-switch-plan`, `undo-timeline`; blocked `claim-enforced-closed-app`, `write-external-app-state`.
- `browser-companion`: horizon `Next`, tier `guided`, allowed `copy-handoff`, `import-checklist`, `visible-capsule-status`; blocked `claim-enforced-closed-app`, `capture-raw-chat-by-default`.
- `ide-extension`: horizon `Next`, tier `guided`, allowed `branch-session-panel`, `semantic-diff`, `merge-review`, `readiness-proof`; blocked `silent-merge`, `write-source-control-without-preview`.

- [ ] **Step 4: Add accessibility boundary tests**

Add:

```python
def test_ide_boundary_requires_merge_and_diff_before_mutation():
    row = boundary_for("ide-extension")
    assert "semantic-diff" in row.allowed_actions
    assert "merge-review" in row.allowed_actions
    assert "silent-merge" in row.blocked_actions

def test_desktop_boundary_requires_keyboard_screen_reader_and_undo_gates():
    row = boundary_for("desktop-launcher")
    assert "keyboard" in row.user_copy
    assert "screen-reader" in row.user_copy
    assert "undo" in row.user_copy
```

- [ ] **Step 5: Run focused and full tests**

Run: `python -m pytest -p no:cacheprovider tests/test_ux_boundaries.py -q`

Run: `python -m pytest -p no:cacheprovider`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/canon/ux_boundaries.py tests/test_ux_boundaries.py
git commit -m "feat: add accessible ux boundaries"
```

## Execution Order

```json
{
  "workflow_id": "canon-adapters-ux",
  "tasks": [
    {
      "id": "T1",
      "agent": "backend",
      "task": "Add adapter effective-tier, descriptor hash, and matrix helpers over foundation-owned descriptors.",
      "depends_on": ["foundation-plan"],
      "parallel_group": "A",
      "handoff_output": "effective_tier results, descriptor_sha256 values, adapter_matrix rows"
    },
    {
      "id": "T2",
      "agent": "backend",
      "task": "Integrate adapter tier and fixture findings into the existing Context Doctor report type.",
      "depends_on": ["T1", "bootstrap-plan"],
      "parallel_group": "B",
      "handoff_output": "DoctorFinding tuple and DoctorReport extension function"
    },
    {
      "id": "T3",
      "agent": "backend",
      "task": "Add semantic capsule diff with non-color Markdown rendering.",
      "depends_on": ["foundation-plan"],
      "parallel_group": "B",
      "handoff_output": "SemanticDiff and SemanticChange dataclasses plus render_diff_markdown"
    },
    {
      "id": "T4",
      "agent": "frontend",
      "task": "Add accessible Markdown and static HTML preview composition over capsule, doctor, diff, and adapter rows.",
      "depends_on": ["T1", "T2", "T3"],
      "parallel_group": "C",
      "handoff_output": "render_accessible_preview_markdown/html outputs"
    },
    {
      "id": "T5",
      "agent": "sdk-platform",
      "task": "Add Codex and Claude Code thin shim plans with native-advisory labels.",
      "depends_on": ["T1", "T4", "bootstrap-plan"],
      "parallel_group": "D",
      "handoff_output": "ShimPlan for codex-cli and claude-code"
    },
    {
      "id": "T6",
      "agent": "backend",
      "task": "Add controlled API and local OpenAI-compatible runner gates.",
      "depends_on": ["T1", "bootstrap-plan"],
      "parallel_group": "D",
      "handoff_output": "RunnerResult, build_openai_request, run_enforced_request, endpoint profile/admission"
    },
    {
      "id": "T7",
      "agent": "sdk-platform",
      "task": "Add read-only MCP preview and doctor resource/tool payloads.",
      "depends_on": ["T4"],
      "parallel_group": "D",
      "handoff_output": "MCP resource and read-only tool dictionaries"
    },
    {
      "id": "T8",
      "agent": "sdk-platform",
      "task": "Add A2A capsule, readiness, and witness artifact mapping.",
      "depends_on": ["T1", "bootstrap-plan"],
      "parallel_group": "D",
      "handoff_output": "A2A artifact/message dictionaries and typed loss rows"
    },
    {
      "id": "T9",
      "agent": "quality-assurance",
      "task": "Add continuity conformance dry gates and smoke fixtures.",
      "depends_on": ["T1", "T6", "T7", "T8"],
      "parallel_group": "E",
      "handoff_output": "ConformanceReport and fixture-check/roundtrip/secret-scan gates"
    },
    {
      "id": "T10",
      "agent": "backend",
      "task": "Register internal continuity and conformance CLI commands backed by conformance APIs.",
      "depends_on": ["T9", "bootstrap-plan"],
      "parallel_group": "F",
      "handoff_output": "python -m canon continuity fixture-check, continuity secret-scan, and conformance run command handlers"
    },
    {
      "id": "T11",
      "agent": "backend",
      "task": "Add raw-content-off local continuity flight recorder.",
      "depends_on": ["T9"],
      "parallel_group": "G",
      "handoff_output": "FlightEvent, FlightEventReceipt, append/replay event ledger"
    },
    {
      "id": "T12",
      "agent": "backend",
      "task": "Add branch/session capsule merge and merge witness.",
      "depends_on": ["T3", "T11"],
      "parallel_group": "H",
      "handoff_output": "MergePlan, MergeConflict, merge_witness"
    },
    {
      "id": "T13",
      "agent": "frontend",
      "task": "Add desktop/browser/IDE planning boundary records and conservative UX copy.",
      "depends_on": ["T1", "T4", "T12"],
      "parallel_group": "I",
      "handoff_output": "SurfaceBoundary records and boundary lookup"
    }
  ],
  "execution_order": [
    ["T1", "T3"],
    ["T2"],
    ["T4"],
    ["T5", "T6", "T7", "T8"],
    ["T9"],
    ["T10"],
    ["T11"],
    ["T12"],
    ["T13"]
  ],
  "estimated_agent_count": 6
}
```

## Handoffs

- T1 to T2/T5/T6/T7/T8/T9/T13: `effective_tier`, `descriptor_sha256`, and `adapter_matrix` over foundation-owned `AdapterDescriptor` instances, format `Python functions plus JSON-serializable matrix rows`.
- T2 to T4: adapter-related `DoctorFinding` rows folded into `DoctorReport`, format `Python dataclass`.
- T3 to T4/T12: `SemanticDiff` and Markdown diff rows, format `Python dataclass plus Markdown`.
- T4 to T7/T13: accessible preview renderers and status labels, format `Markdown` and static `HTML`.
- T5 to T9: Codex/Claude shim plans proving advisory wording, format `ShimPlan`.
- T6 to T9: API/local runner proof and endpoint admission data, format `RunnerResult` and endpoint profile JSON.
- T7 to T9: MCP read-only resource/tool payloads, format `JSON-serializable dict`.
- T8 to T9: A2A artifact/message payloads and typed loss rows, format `JSON-serializable dict`.
- T9 to T10/T11/T12/T13: fixture ids, conformance failures, report serialization, and secret-scan guarantees, format `ConformanceReport` plus JSON-safe dict.
- T10 to evidence/CI gates: exact internal CLI commands, format `python -m canon ...` command surface.
- T11 to T12: ordered flight event ledger, format `FlightEvent` tuples and receipt JSON.
- T12 to T13: merge safety states and witness payloads, format `MergePlan` and JSON witness.

## Final Verification Checklist

- [ ] Run `python -m pytest -p no:cacheprovider`.
- [ ] Run `rg -n "\"enforced\"|\"native-advisory\"|\"guided\"|\"unsupported\"" src tests docs project-docs` and confirm every product-facing tier mention is lower-case and tied to descriptor data, fixture results, or conservative UX copy.
- [ ] Run `python -c "from pathlib import Path; p=Path('docs/superpowers/plans/2026-08-30-canon-adapters-ux.md'); text=p.read_text(encoding='utf-8'); assert 'openai-api' + '-runner' not in text; assert 'local-openai-compatible' + '-runner' not in text"` and confirm runner descriptors are `api-runner` and `local-runner`.
- [ ] Run `rg -n "def builtin_descriptors|def descriptor_for|def assert_requested_tier_allowed|class AdapterDescriptor" src/canon/adapter_registry.py` and confirm there are no matches because those interfaces are foundation-owned.
- [ ] Run `rg -n "continuity fixture-check|continuity secret-scan|conformance run|project\\.scripts|console_scripts" src/canon/cli.py pyproject.toml tests/test_continuity_conformance_cli.py` and confirm the new commands are internal `python -m canon` parser routes only.
- [ ] Run `rg -n "add_parser\\(\"verify-sources\"\\)|add_parser\\(\"merge-check\"\\)" src/canon/cli.py tests/test_continuity_conformance_cli.py` and confirm there are no matches because those design gates are deferred. Confirm the design `roundtrip --matrix` gate is represented by `python -m canon conformance run <fixture_root> --out <out>` instead of a separate parser command.
- [ ] Run `rg -n "CANARY_API_KEY_DO_NOT_EXPORT|BEGIN CANARY PRIVATE KEY" src docs project-docs` and confirm synthetic canary values appear only in fixture files and tests designed to assert non-leakage.
- [ ] Run `rg -n "raw_content_included.*True|private-raw|capture_policy" src tests` and confirm raw-content capture requires explicit `private-raw` policy and never inlines raw bytes.
- [ ] Run `python -m pytest -p no:cacheprovider tests/test_adapter_registry.py tests/test_adapter_doctor.py tests/test_semantic_diff.py tests/test_preview_accessible.py tests/test_accessibility_static.py tests/test_codex_adapter.py tests/test_claude_code_adapter.py tests/test_api_runner.py tests/test_local_openai_runner.py tests/test_mcp_readonly.py tests/test_a2a.py tests/test_conformance.py tests/test_continuity_conformance_cli.py tests/test_flight_recorder.py tests/test_session_merge.py tests/test_ux_boundaries.py -q`.
- [ ] Review `git diff --stat` and confirm each task changed only the files named in that task.
