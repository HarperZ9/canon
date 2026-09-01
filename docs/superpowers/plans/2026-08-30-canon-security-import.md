# Canon Security Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add fail-closed security and import-boundary primitives for Canon before any external capsule, archive, or imported continuity data can write records or become active.

**Architecture:** Keep the existing `canon.record/v1` storage/render spine intact and add small stdlib-only policy modules around it. The first task fixes the verified `FilesBackend` invalid-scope path blocker; downstream tasks add read-only or plan-only security primitives that consume the foundation `CanonAtom`, `Omission`, and `TransformReceipt` modules instead of defining duplicate continuity types.

**Tech Stack:** Python 3.11+, standard library only, pytest, dataclasses, pathlib/os/stat/hashlib/json/zipfile.

**Spec:** `project-docs/SPEC-CANON-PILLAR-20260830.md`; supporting design and audit inputs are `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md`, `project-docs/audits/2026-08-30/SECURITY-PRIVACY-THREAT-MODEL.md`, and `project-docs/audits/2026-08-30/CORE-SCHEMA-I0-AUDIT.md`.

## Global Constraints

- Python 3.11+.
- Standard library only; `pyproject.toml` currently has `dependencies = []` and must stay that way.
- TDD. Every source change in this plan starts with a failing pytest test.
- Quality gates from `CLAUDE.md`: no source file over 300 lines, no function over 50 lines.
- No CLI, no extraction, no product-surface edits, no network calls, no cryptographic-signature implementation, and no external service integration.
- `canon.record/v1` scopes remain exactly `global` and `workspace`; richer personal/team/org/session/repo semantics stay in the foundation atom layer or a future versioned migration.
- Import content remains inactive until schema, trust, freshness, conflict, source-reachability, secret/PII, disclosure, budget, replay, and source-state checks pass.
- `.canonpack` support in this plan is manifest and zip central-directory preflight only; it must never call `ZipFile.extract`, write archive entries, or auto-promote content into startup instructions.
- Security/import modules must import foundation continuity types and must not define duplicate classes named `CanonAtom`, `Omission`, or `TransformReceipt`.
- Foundation dependency contract: this plan consumes `from canon.atom import CanonAtom`, `from canon.omission import Omission`, and `from canon.transform import TransformReceipt`. Those foundation modules own `from_dict(d: dict)`, `to_dict() -> dict`, validation for their schemas, and schema constants for `canon.atom/v1`, `canon.omission/v1`, and `canon.transform-receipt/v1`.

---

## Verified Current Baseline

- `src/canon/backends/files.py:42-50` derives a filesystem path from `record.scope` before full semantic validation; only `id` is URL-quoted.
- `src/canon/backends/base.py:78-89` uses raw `scope/id` in `record_key` and `split_key`.
- `src/canon/backends/base.py:115-127` `guard_put` checks supported kind and declared drops, but not `validate_record(record)`.
- `src/canon/validator.py:84-116` already rejects unknown scopes, so the bug is enforcement at backend entry, not missing semantic knowledge.
- `src/canon/schema.py:62-67` fixes `canon.record/v1` scopes to `global` and `workspace`.
- `src/canon/registry.py:58-84` has a lexical allow-list for managed instruction surfaces.
- `src/canon/vault_mirror.py:77-107` has a lexical/commonpath vault target guard.
- `project-docs/CANON-CONTINUITY-CAPSULE-DESIGN.md:529-533` makes the `FilesBackend` validation bug a release blocker before import writes.
- `project-docs/audits/2026-08-30/SECURITY-PRIVACY-THREAT-MODEL.md:517-546` defines SEC-001 through SEC-016 and the measurable release gates this plan covers in security/import scope.
- Local verification before this plan: `python -m pytest -p no:cacheprovider` reported `407 passed`.

## File Structure

- Modify `src/canon/backends/base.py`: add backend validation exceptions and make backend key helpers fail closed before path derivation.
- Modify `src/canon/backends/files.py`: keep files layout unchanged, but reject invalid keys/scopes before any filesystem path is computed and restrict enumeration to known scope directories.
- Modify `src/canon/backends/__init__.py` and `src/canon/__init__.py`: export new backend exceptions/helpers.
- Create `src/canon/path_policy.py`: root containment, protected-path, symlink, junction, reparse-point, and Windows ADS guards.
- Create `src/canon/import_policy.py`: trust and disclosure decision helpers over foundation `CanonAtom`, `Omission`, and `TransformReceipt`.
- Create `src/canon/secret_quarantine.py`: deterministic local secret/PII scanner and quarantine receipt interface.
- Create `src/canon/canonpack.py`: `.canonpack` manifest and zip preflight without extraction.
- Create `src/canon/source_state.py`: canonical source-state serialization and compare-and-swap checks.
- Create `src/canon/replay.py`: replay key and in-memory replay claim primitives for tests and future stores.
- Create `src/canon/concurrency.py`: local lock-file primitive and guarded commit wrapper.
- Create `src/canon/retention.py`: retention/tombstone planning interfaces that do not delete files.
- Create `src/canon/import_review.py`: read-only composition layer that folds trust, disclosure, secret, source-state, and replay findings without writing to a backend.
- Test files: `tests/test_backend_base.py`, `tests/test_files_backend.py`, `tests/test_path_policy.py`, `tests/test_import_policy.py`, `tests/test_secret_quarantine.py`, `tests/test_canonpack.py`, `tests/test_source_state.py`, `tests/test_replay.py`, `tests/test_concurrency.py`, `tests/test_retention.py`, and `tests/test_import_review.py`.

---

### Task 1: FilesBackend Semantic Validation Before Path Derivation

**Files:**
- Modify: `src/canon/backends/base.py:53-127`
- Modify: `src/canon/backends/files.py:16-67`
- Modify: `src/canon/backends/__init__.py:19-67`
- Modify: `src/canon/__init__.py:13-94`
- Test: `tests/test_backend_base.py`
- Test: `tests/test_files_backend.py`

**Interfaces:**
- Consumes: `canon.validator.validate_record(record: Record) -> list[str]`, `canon.schema.SCOPES`, and existing `MemoryBackend`.
- Produces:
  - `class InvalidRecord(BackendError):`
  - `class InvalidKey(BackendError):`
  - `def validate_put_record(backend: MemoryBackend, record: Record) -> None`
  - `def record_key(record: Record) -> str`
  - `def split_key(key: str) -> tuple[str, str]`

- [ ] **Step 1: Add failing backend-base tests for invalid records and keys**

Add these tests to `tests/test_backend_base.py`:

```python
from dataclasses import replace

import pytest

from canon.backends import InvalidKey, InvalidRecord, guard_put, record_key, split_key

from ._helpers import RECORD_FILES, load_record


class _AllKindsBackend:
    name = "all-kinds-test"

    def supported_kinds(self) -> frozenset[str]:
        return frozenset({
            "personality-block",
            "episodic-memory",
            "synthesized-persona-l3",
            "adr-decision",
            "research-artifact-ref",
        })

    def declared_drops(self) -> frozenset[str]:
        return frozenset()


def test_guard_put_rejects_semantically_invalid_record() -> None:
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope="..")
    with pytest.raises(InvalidRecord, match="unknown scope"):
        guard_put(_AllKindsBackend(), rec)


@pytest.mark.parametrize("scope", ["", ".", "..", "repo", "../x", "global/../../x", "C:/tmp", "C:\\tmp"])
def test_record_key_rejects_invalid_scope_values(scope: str) -> None:
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope=scope)
    with pytest.raises(InvalidRecord):
        record_key(rec)


@pytest.mark.parametrize("key", ["", "global", "/id", "../x", "repo/x", "C:/tmp/x", "C:\\tmp\\x"])
def test_split_key_rejects_invalid_backend_keys(key: str) -> None:
    with pytest.raises(InvalidKey):
        split_key(key)
```

- [ ] **Step 2: Add failing FilesBackend tests for SEC-001 and SEC-002**

Add these tests to `tests/test_files_backend.py`:

```python
from dataclasses import replace
from urllib.parse import quote

import pytest

from canon.backends import InvalidKey, InvalidRecord


def test_put_invalid_scope_refuses_before_creating_outside_file(tmp_path) -> None:
    be = FilesBackend(tmp_path / "store")
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope="..", id="escape")

    with pytest.raises(InvalidRecord, match="unknown scope"):
        be.put(rec)

    assert not (tmp_path / "escape.json").exists()
    assert not (tmp_path / "store").exists()


@pytest.mark.parametrize("scope", ["../x", "global/../../x", "C:/tmp", "C:\\tmp", "repo"])
def test_put_rejects_path_shaped_scopes_without_writing(tmp_path, scope: str) -> None:
    be = FilesBackend(tmp_path / "store")
    rec = replace(load_record(RECORD_FILES["episodic-memory"]), scope=scope, id="safe-id")

    with pytest.raises(InvalidRecord):
        be.put(rec)

    assert not (tmp_path / "store").exists()


@pytest.mark.parametrize("key", ["../escape", "repo/x", "C:/tmp/x", "C:\\tmp\\x"])
def test_get_invalid_key_refuses_before_path_lookup(tmp_path, key: str) -> None:
    with pytest.raises(InvalidKey):
        FilesBackend(tmp_path).get(key)


def test_records_ignores_unknown_scope_directories(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES["episodic-memory"])
    rogue = tmp_path / "repo"
    rogue.mkdir()
    (rogue / (quote(rec.id, safe="") + ".json")).write_text(rec.to_json(), encoding="utf-8")

    assert be.records() == []


def test_records_rejects_path_scope_mismatch(tmp_path) -> None:
    be = FilesBackend(tmp_path)
    rec = load_record(RECORD_FILES["episodic-memory"])
    scope_dir = tmp_path / "workspace"
    scope_dir.mkdir()
    (scope_dir / (quote(rec.id, safe="") + ".json")).write_text(rec.to_json(), encoding="utf-8")

    with pytest.raises(InvalidRecord, match="path scope"):
        be.records()
```

- [ ] **Step 3: Run the new failing slice**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_backend_base.py tests/test_files_backend.py -q
```

Expected: the new tests fail because `InvalidRecord` and `InvalidKey` are not exported, `guard_put` does not call `validate_record`, and `FilesBackend.get()` currently accepts invalid key strings.

- [ ] **Step 4: Implement validation in the backend seam**

Update `src/canon/backends/base.py` with this minimal shape:

```python
from canon.schema import SCOPES, Record
from canon.validator import validate_record


class InvalidRecord(BackendError):
    """The record is semantically invalid and cannot enter a backend."""


class InvalidKey(BackendError):
    """The backend key is malformed or names an unsupported scope."""


def _validate_key_parts(scope: object, rid: object, *, record: bool) -> tuple[str, str]:
    if not isinstance(scope, str) or scope not in SCOPES:
        if record:
            raise InvalidRecord(f"unknown scope {scope!r}; expected one of {list(SCOPES)}")
        raise InvalidKey(f"unknown scope {scope!r}; expected one of {list(SCOPES)}")
    if not isinstance(rid, str) or rid == "":
        if record:
            raise InvalidRecord("id must be a non-empty string")
        raise InvalidKey("id must be a non-empty string")
    return scope, rid


def record_key(record: Record) -> str:
    scope, rid = _validate_key_parts(record.scope, record.id, record=True)
    return f"{scope}/{rid}"


def split_key(key: str) -> tuple[str, str]:
    if not isinstance(key, str):
        raise InvalidKey(f"key must be str, got {type(key).__name__}")
    scope, sep, rid = key.partition("/")
    if sep == "":
        raise InvalidKey("key must be '<scope>/<id>'")
    return _validate_key_parts(scope, rid, record=False)


def validate_put_record(backend: "MemoryBackend", record: Record) -> None:
    problems = validate_record(record)
    if problems:
        raise InvalidRecord("; ".join(problems))
    if record.kind not in backend.supported_kinds():
        raise UnsupportedKind(
            f"{backend.name} does not hold kind {record.kind!r}; "
            f"supported: {sorted(backend.supported_kinds())}")
    blocked = capabilities_required(record) & backend.declared_drops()
    if blocked:
        raise DropError(
            f"{backend.name} dropped {sorted(blocked)}; record {record.id!r} "
            f"exercises it -- flatten() to store current-only.")


def guard_put(backend: "MemoryBackend", record: Record) -> None:
    validate_put_record(backend, record)
```

Export `InvalidRecord`, `InvalidKey`, and `validate_put_record` from `src/canon/backends/__init__.py` and `src/canon/__init__.py`.

- [ ] **Step 5: Harden FilesBackend enumeration without changing its on-disk layout**

Update `src/canon/backends/files.py` so `_path()` only receives validated keys and `records()` only enumerates `SCOPES`:

```python
from canon.schema import KINDS, SCOPES, Record

from .base import InvalidRecord


def records(self) -> list[Record]:
    out: list[Record] = []
    if not self._root.is_dir():
        return out
    for scope in SCOPES:
        scope_dir = self._root / scope
        if not scope_dir.is_dir():
            continue
        for f in sorted(scope_dir.glob("*.json")):
            rec = Record.from_json(f.read_text(encoding="utf-8"))
            guard_put(self, rec)
            if rec.scope != scope:
                raise InvalidRecord(
                    f"path scope {scope!r} does not match record scope {rec.scope!r}")
            out.append(rec)
    return out
```

- [ ] **Step 6: Run the fixed backend slice**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_backend_base.py tests/test_files_backend.py -q
```

Expected: PASS.

- [ ] **Step 7: Review gate for Task 1**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_sqlite_backend.py tests/test_mneme_backend.py tests/test_flywheel_backend.py tests/test_backend_base.py tests/test_files_backend.py -q
```

Expected: PASS, proving the stricter shared `guard_put()` does not break existing valid backend fixtures.

---

### Task 2: Root, Protected-Path, Symlink, Junction, Reparse, and ADS Guards

**Files:**
- Create: `src/canon/path_policy.py`
- Test: `tests/test_path_policy.py`

**Interfaces:**
- Consumes: only stdlib modules `os`, `stat`, `pathlib`, and `dataclasses`.
- Produces:
  - `@dataclass(frozen=True, slots=True) class PathPolicyViolation`
  - `class PathPolicyError(ValueError)`
  - `def is_windows_ads_path(path: str | Path) -> bool`
  - `def is_reparse_point(path: str | Path) -> bool`
  - `def classify_protected_path(path: str | Path) -> tuple[PathPolicyViolation, ...]`
  - `def resolve_under_root(path: str | Path, *, root: str | Path, must_exist: bool = False, reject_reparse: bool = True) -> Path`
  - `def assert_not_protected(path: str | Path) -> None`
  - `def assert_operational_surface_path(path: str | Path, *, root: str | Path) -> Path`
  - `def assert_operational_vault_path(path: str | Path, *, vault: str | Path) -> Path`

- [ ] **Step 1: Write failing path-policy tests**

Create `tests/test_path_policy.py`:

```python
from __future__ import annotations

import os
from pathlib import Path

import pytest

from canon.path_policy import (
    PathPolicyError,
    assert_not_protected,
    assert_operational_surface_path,
    assert_operational_vault_path,
    is_windows_ads_path,
    resolve_under_root,
)


def test_resolve_under_root_rejects_root_itself(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="root-target"):
        resolve_under_root(tmp_path, root=tmp_path)


def test_resolve_under_root_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="outside-root"):
        resolve_under_root(tmp_path / ".." / "escape.md", root=tmp_path)


@pytest.mark.parametrize("name", [".env", ".env.local", "id_rsa", "id_ed25519", "cookies.sqlite", "Login Data"])
def test_assert_not_protected_rejects_sensitive_file_names(tmp_path: Path, name: str) -> None:
    with pytest.raises(PathPolicyError, match="protected-path"):
        assert_not_protected(tmp_path / name)


@pytest.mark.parametrize("relative", [".ssh/id_rsa", ".aws/credentials", ".config/gcloud/application_default_credentials.json"])
def test_assert_not_protected_rejects_sensitive_directories(tmp_path: Path, relative: str) -> None:
    with pytest.raises(PathPolicyError, match="protected-path"):
        assert_not_protected(tmp_path / Path(relative))


def test_ads_detection_rejects_named_stream() -> None:
    assert is_windows_ads_path("AGENTS.md:secret")
    with pytest.raises(PathPolicyError, match="ads"):
        resolve_under_root("AGENTS.md:secret", root=".")


def test_symlink_parent_refused_before_operational_write(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "root" / "link"
    link.parent.mkdir()
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(PathPolicyError, match="reparse"):
        assert_operational_surface_path(link / "AGENTS.md", root=tmp_path / "root")


def test_operational_vault_allows_regular_scope_note(tmp_path: Path) -> None:
    target = tmp_path / "vault" / "workspace" / "note.md"
    target.parent.mkdir(parents=True)
    target.write_text("body", encoding="utf-8")

    assert assert_operational_vault_path(target, vault=tmp_path / "vault") == target.resolve()


def test_operational_vault_rejects_hub_root_directory(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    with pytest.raises(PathPolicyError, match="root-target"):
        assert_operational_vault_path(vault, vault=vault)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_path_policy.py -q
```

Expected: FAIL because `canon.path_policy` does not exist.

- [ ] **Step 3: Implement the focused path policy module**

Create `src/canon/path_policy.py` with these exact public names and codes:

```python
from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

_PROTECTED_NAMES = frozenset({
    ".env",
    ".env.local",
    ".env.production",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "known_hosts",
    "cookies.sqlite",
    "login data",
})

_PROTECTED_PARTS = (
    (".ssh",),
    (".gnupg",),
    (".aws",),
    (".azure",),
    (".config", "gcloud"),
    ("appdata", "local", "google", "chrome", "user data"),
    ("appdata", "roaming", "mozilla", "firefox", "profiles"),
    ("library", "application support", "google", "chrome"),
)


@dataclass(frozen=True, slots=True)
class PathPolicyViolation:
    code: str
    path: str
    reason: str


class PathPolicyError(ValueError):
    def __init__(self, violations: tuple[PathPolicyViolation, ...]) -> None:
        self.violations = violations
        joined = "; ".join(f"{v.code}: {v.path} ({v.reason})" for v in violations)
        super().__init__(joined)
```

Implement:

- `is_windows_ads_path()` returns true when any path part except a drive designator contains `:`.
- `is_reparse_point()` returns true for `Path.is_symlink()` or, when available, `lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT`.
- `classify_protected_path()` lower-cases path parts and emits `PathPolicyViolation("protected-path", ...)` for protected basenames or protected part sequences.
- `resolve_under_root()` resolves `root`, refuses root itself as `root-target`, refuses ADS, refuses paths outside root using `os.path.commonpath`, refuses non-existing targets when `must_exist=True`, and checks every existing parent plus the target for `reparse` when `reject_reparse=True`.
- `assert_not_protected()` raises `PathPolicyError` when `classify_protected_path()` returns any violation.
- `assert_operational_surface_path()` and `assert_operational_vault_path()` call `resolve_under_root()` and `assert_not_protected()` and return the resolved `Path`.

- [ ] **Step 4: Run path-policy tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_path_policy.py -q
```

Expected: PASS.

- [ ] **Step 5: Review gate for Task 2**

Run:

```bash
python -m compileall -q src/canon/path_policy.py tests/test_path_policy.py
python -m pytest -p no:cacheprovider tests/test_path_policy.py -q
```

Expected: both commands pass and `src/canon/path_policy.py` remains under 300 lines.

---

### Task 3: Trust and Disclosure Labels for Inactive Imports

**Files:**
- Create: `src/canon/import_policy.py`
- Test: `tests/test_import_policy.py`

**Interfaces:**
- Consumes:
  - `from canon.atom import CanonAtom`
  - `from canon.omission import Omission`
  - `from canon.transform import TransformReceipt`
- Produces:
  - `TRUST_LABELS: tuple[str, ...]`
  - `DISCLOSURE_PROFILES: tuple[str, ...]`
  - `@dataclass(frozen=True, slots=True) class ImportSubject`
  - `@dataclass(frozen=True, slots=True) class ImportDecision`
  - `def classify_trust(*, signature_status: str, key_id: str | None, pinned_key_ids: frozenset[str], local: bool, model_synthesized: bool = False) -> str`
  - `def validate_atom_activation(atom: CanonAtom, *, trust_label: str) -> tuple[str, ...]`
  - `def disclosure_omissions(atoms: tuple[CanonAtom, ...], *, profile: str) -> tuple[Omission, ...]`
  - `def review_import_subject(subject: ImportSubject, *, profile: str, pinned_key_ids: frozenset[str]) -> ImportDecision`

- [ ] **Step 1: Write failing import-policy tests with foundation atom imports**

Create `tests/test_import_policy.py`:

```python
from __future__ import annotations

from canon.atom import CanonAtom
from canon.import_policy import (
    classify_trust,
    disclosure_omissions,
    review_import_subject,
    validate_atom_activation,
    ImportSubject,
)


def _atom(atom_id: str, *, atom_type: str, critical: bool, classification: str,
          trust_label: str = "trusted-local", disclosure_label: str = "project-only") -> CanonAtom:
    return CanonAtom.from_dict({
        "atom_schema": "canon.atom/v1",
        "type": atom_type,
        "id": atom_id,
        "layer": "workspace",
        "scope_key": "public/canon",
        "precedence_rank": 50,
        "status": "active",
        "classification": classification,
        "critical": critical,
        "value": {"text": f"value for {atom_id}"},
        "source_refs": ["source:1"],
        "source_span_refs": [],
        "freshness": {"state": "current"},
        "trust": {"label": trust_label},
        "disclosure": {"label": disclosure_label},
        "hashes": {"content_sha256": "sha256:" + "1" * 64},
    })


def test_signed_unknown_key_is_integrity_only_and_inactive() -> None:
    atom = _atom("permission-1", atom_type="permission", critical=True, classification="normative")
    subject = ImportSubject(
        source_id="capsule-a",
        atoms=(atom,),
        signature_status="valid",
        key_id="unknown-key",
        local=False,
        source_state_sha256="sha256:" + "2" * 64,
    )

    decision = review_import_subject(subject, profile="project-only", pinned_key_ids=frozenset({"pinned-key"}))

    assert not decision.ok
    assert decision.trust_label == "signed-unknown-key"
    assert "untrusted-import" in decision.reason_codes
    assert decision.accepted_atom_ids == ()


def test_model_synthesized_unreviewed_normative_atom_cannot_activate() -> None:
    atom = _atom("prohibition-1", atom_type="prohibition", critical=True, classification="normative")

    reasons = validate_atom_activation(atom, trust_label="model-synthesized-unreviewed")

    assert "unreviewed-model-normative" in reasons


def test_private_local_only_is_omitted_from_cloud_profiles() -> None:
    atom = _atom(
        "fact-1",
        atom_type="episodic-fact",
        critical=False,
        classification="descriptive",
        disclosure_label="private-local-only",
    )

    omissions = disclosure_omissions((atom,), profile="team-safe")

    assert len(omissions) == 1
    assert omissions[0].to_dict()["subject_id"] == "fact-1"
    assert omissions[0].to_dict()["reason_code"] == "private-local-only"


def test_critical_private_local_only_blocks_cloud_profile() -> None:
    atom = _atom(
        "goal-1",
        atom_type="active-goal",
        critical=True,
        classification="normative",
        disclosure_label="private-local-only",
    )
    subject = ImportSubject(
        source_id="capsule-b",
        atoms=(atom,),
        signature_status="none",
        key_id=None,
        local=True,
        source_state_sha256="sha256:" + "3" * 64,
    )

    decision = review_import_subject(subject, profile="team-safe", pinned_key_ids=frozenset())

    assert not decision.ok
    assert "critical-disclosure-omission" in decision.reason_codes
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_import_policy.py -q
```

Expected: FAIL because `canon.import_policy` does not exist. If the failure is `ModuleNotFoundError: canon.atom`, stop this plan and finish the foundation plan first; do not create temporary `CanonAtom` replacements in this plan.

- [ ] **Step 3: Implement import-policy dataclasses and label constants**

Create `src/canon/import_policy.py` with these constants:

```python
TRUST_LABELS = (
    "trusted-local",
    "signed-pinned",
    "signed-unknown-key",
    "unsigned-local",
    "imported-untrusted",
    "model-synthesized-unreviewed",
    "secret-quarantined",
    "stale",
    "public-exportable",
    "private-local-only",
)

DISCLOSURE_PROFILES = (
    "full-local",
    "project-only",
    "no-secrets",
    "team-safe",
    "public-safe",
    "need-to-know",
)
```

Use these dataclass shapes:

```python
@dataclass(frozen=True, slots=True)
class ImportSubject:
    source_id: str
    atoms: tuple[CanonAtom, ...]
    signature_status: str
    key_id: str | None
    local: bool
    source_state_sha256: str
    model_synthesized: bool = False


@dataclass(frozen=True, slots=True)
class ImportDecision:
    ok: bool
    trust_label: str
    profile: str
    accepted_atom_ids: tuple[str, ...]
    omissions: tuple[Omission, ...]
    receipts: tuple[TransformReceipt, ...]
    reason_codes: tuple[str, ...]
```

- [ ] **Step 4: Implement minimal fail-closed trust/disclosure functions**

Implementation rules:

- `classify_trust(signature_status="valid", key_id in pinned_key_ids)` returns `signed-pinned`.
- `classify_trust(signature_status="valid", key_id not in pinned_key_ids)` returns `signed-unknown-key`.
- `classify_trust(local=True, signature_status!="valid")` returns `unsigned-local`.
- `classify_trust(local=False, signature_status!="valid")` returns `imported-untrusted`.
- `model_synthesized=True` overrides to `model-synthesized-unreviewed`.
- `validate_atom_activation()` reads `atom.to_dict()`, blocks `signed-unknown-key`, `imported-untrusted`, `secret-quarantined`, and `stale`, and blocks `model-synthesized-unreviewed` when `classification == "normative"` or `type` is one of `active-goal`, `permission`, `prohibition`, `constraint`, `conflict`, or `unknown`.
- `disclosure_omissions()` emits foundation `Omission.from_dict(...)` records for atoms with `disclosure.label == "private-local-only"` when `profile` is `team-safe`, `public-safe`, `no-secrets`, or `need-to-know`.
- `review_import_subject()` returns `ok=False` when any reason code is present, when any critical atom is omitted by disclosure, or when trust is not `trusted-local`, `signed-pinned`, or `unsigned-local`.

Use this omission constructor shape so omission receipts are compatible with the foundation plan:

```python
Omission.from_dict({
    "omission_schema": "canon.omission/v1",
    "id": f"omission:{atom_dict['id']}:private-local-only",
    "subject_id": atom_dict["id"],
    "reason_code": "private-local-only",
    "critical": bool(atom_dict.get("critical")),
    "source_ids": tuple(atom_dict.get("source_refs", ())),
    "visible": True,
    "redacted_hash": atom_dict.get("hashes", {}).get("content_sha256"),
})
```

- [ ] **Step 5: Run import-policy tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_import_policy.py -q
```

Expected: PASS.

---

### Task 4: Secret Quarantine Interface

**Files:**
- Create: `src/canon/secret_quarantine.py`
- Test: `tests/test_secret_quarantine.py`

**Interfaces:**
- Consumes:
  - `from canon.omission import Omission`
  - `from canon.transform import TransformReceipt`
- Produces:
  - `@dataclass(frozen=True, slots=True) class SecretFinding`
  - `@dataclass(frozen=True, slots=True) class SecretQuarantine`
  - `class SecretQuarantineError(ValueError)`
  - `def scan_text(text: str, *, source_id: str) -> tuple[SecretFinding, ...]`
  - `def quarantine_text(text: str, *, source_id: str, critical: bool = False) -> SecretQuarantine`
  - `def quarantine_path(path: str | Path, *, source_id: str, critical: bool = False) -> SecretQuarantine`

- [ ] **Step 1: Write failing secret-quarantine tests**

Create `tests/test_secret_quarantine.py`:

```python
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from canon.secret_quarantine import SecretQuarantineError, quarantine_path, quarantine_text, scan_text


def test_secret_canary_is_not_serialized_in_quarantine_result() -> None:
    canary = "sk-live-abcdefghijklmnopqrstuvwxyz012345"
    result = quarantine_text(f"token={canary}", source_id="fixture-secret", critical=False)

    assert result.safe_text is None
    assert result.findings[0].code == "openai-api-key"
    assert canary not in repr(result)
    assert canary not in str(asdict(result))
    assert result.omissions[0].to_dict()["reason_code"] == "secret-quarantined"


def test_email_and_ssn_are_quarantined_as_pii() -> None:
    findings = scan_text("owner jane@example.com ssn 123-45-6789", source_id="fixture-pii")

    assert {f.code for f in findings} == {"email", "ssn"}


def test_critical_secret_raises_before_returning_safe_text() -> None:
    with pytest.raises(SecretQuarantineError, match="critical-secret"):
        quarantine_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----", source_id="fixture-key", critical=True)


def test_quarantine_path_refuses_protected_path_without_reading(tmp_path: Path) -> None:
    protected = tmp_path / ".env"
    protected.write_text("TOKEN=sk-live-abcdefghijklmnopqrstuvwxyz012345", encoding="utf-8")

    result = quarantine_path(protected, source_id="env-file", critical=False)

    assert result.safe_text is None
    assert result.findings[0].code == "protected-path"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_secret_quarantine.py -q
```

Expected: FAIL because `canon.secret_quarantine` does not exist.

- [ ] **Step 3: Implement scanner and quarantine result without raw snippets**

Create `src/canon/secret_quarantine.py` using only deterministic regexes and SHA-256 digests:

```python
_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("openai-api-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
)


@dataclass(frozen=True, slots=True)
class SecretFinding:
    code: str
    source_id: str
    start: int
    end: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SecretQuarantine:
    safe_text: str | None
    findings: tuple[SecretFinding, ...]
    omissions: tuple[Omission, ...]
    receipts: tuple[TransformReceipt, ...]
    reason_codes: tuple[str, ...]
```

Implementation rules:

- Store only `sha256:<digest>` of matched text in `SecretFinding.sha256`; never store the raw matched value.
- `quarantine_text()` returns `safe_text=text` only when there are no findings.
- If findings exist and `critical=False`, return `safe_text=None`, one visible foundation `Omission` per source, and one foundation `TransformReceipt` with transform kind `redaction`.
- If findings exist and `critical=True`, raise `SecretQuarantineError("critical-secret: <source_id>")`.
- `quarantine_path()` must call `path_policy.classify_protected_path()` before `Path.read_text()`. For protected paths it returns a protected-path finding without reading the file.

- [ ] **Step 4: Run secret-quarantine tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_secret_quarantine.py -q
```

Expected: PASS.

---

### Task 5: Safe `.canonpack` Manifest and Zip Preflight Without Extraction

**Files:**
- Create: `src/canon/canonpack.py`
- Test: `tests/test_canonpack.py`

**Interfaces:**
- Consumes: `canon.path_policy.is_windows_ads_path`.
- Produces:
  - `class CanonpackError(ValueError)`
  - `@dataclass(frozen=True, slots=True) class CanonpackLimits`
  - `@dataclass(frozen=True, slots=True) class CanonpackEntry`
  - `@dataclass(frozen=True, slots=True) class CanonpackPreflight`
  - `def normalize_manifest_path(name: str) -> str`
  - `def preflight_manifest(manifest: dict, *, limits: CanonpackLimits = CanonpackLimits()) -> CanonpackPreflight`
  - `def preflight_zip(path: str | Path, *, limits: CanonpackLimits = CanonpackLimits()) -> CanonpackPreflight`

- [ ] **Step 1: Write failing canonpack preflight tests**

Create `tests/test_canonpack.py`:

```python
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from canon.canonpack import CanonpackError, CanonpackLimits, preflight_manifest, preflight_zip


def _manifest_entry(path: str, *, body: bytes = b"{}") -> dict:
    return {
        "path": path,
        "sha256": "sha256:" + hashlib.sha256(body).hexdigest(),
        "size": len(body),
        "compressed_size": len(body),
        "compression": "stored",
        "kind": "record",
    }


@pytest.mark.parametrize("name", ["", "../records/a.json", "/abs/a.json", "C:/tmp/a.json", "records\\a.json", "records/a.json:ads", "records/./a.json"])
def test_manifest_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(CanonpackError):
        preflight_manifest({"schema": "canonpack.manifest/v1", "entries": [_manifest_entry(name)]})


def test_manifest_rejects_duplicate_case_fold_names() -> None:
    manifest = {
        "schema": "canonpack.manifest/v1",
        "entries": [_manifest_entry("records/A.json"), _manifest_entry("records/a.json")],
    }

    with pytest.raises(CanonpackError, match="duplicate-path"):
        preflight_manifest(manifest)


def test_manifest_rejects_decompression_ratio() -> None:
    entry = _manifest_entry("records/a.json")
    entry["size"] = 10_000
    entry["compressed_size"] = 1

    with pytest.raises(CanonpackError, match="compression-ratio"):
        preflight_manifest({"schema": "canonpack.manifest/v1", "entries": [entry]}, limits=CanonpackLimits(max_compression_ratio=10))


def test_zip_preflight_rejects_symlink_entry(tmp_path: Path) -> None:
    pack = tmp_path / "bad.canonpack"
    with zipfile.ZipFile(pack, "w") as zf:
        info = zipfile.ZipInfo("records/link")
        info.external_attr = 0o120777 << 16
        zf.writestr(info, "target")

    with pytest.raises(CanonpackError, match="symlink-entry"):
        preflight_zip(pack)


def test_zip_preflight_checks_digest_without_extracting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = tmp_path / "ok.canonpack"
    body = b'{"canon_schema":"canon.record/v1"}'
    manifest = {
        "schema": "canonpack.manifest/v1",
        "entries": [_manifest_entry("records/a.json", body=body)],
    }
    with zipfile.ZipFile(pack, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("manifest.json", __import__("json").dumps(manifest, sort_keys=True))
        zf.writestr("records/a.json", body)

    def fail_extract(*args, **kwargs):
        raise AssertionError("preflight_zip must not extract archive members")

    monkeypatch.setattr(zipfile.ZipFile, "extract", fail_extract)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", fail_extract)

    result = preflight_zip(pack)

    assert result.ok
    assert result.entries[0].path == "records/a.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_canonpack.py -q
```

Expected: FAIL because `canon.canonpack` does not exist.

- [ ] **Step 3: Implement manifest-only and central-directory preflight**

Create `src/canon/canonpack.py`:

```python
@dataclass(frozen=True, slots=True)
class CanonpackLimits:
    max_entries: int = 2000
    max_total_uncompressed: int = 50_000_000
    max_entry_uncompressed: int = 10_000_000
    max_compression_ratio: int = 100


@dataclass(frozen=True, slots=True)
class CanonpackEntry:
    path: str
    sha256: str
    size: int
    compressed_size: int
    compression: str
    kind: str


@dataclass(frozen=True, slots=True)
class CanonpackPreflight:
    ok: bool
    entries: tuple[CanonpackEntry, ...]
    manifest_sha256: str
    reason_codes: tuple[str, ...]
```

Implementation rules:

- `normalize_manifest_path()` rejects empty names, absolute names, drive-qualified names, backslashes, `.` segments, `..` segments, ADS names, and names that normalize differently after POSIX cleanup.
- Duplicate detection uses `name.casefold()` on normalized names.
- `preflight_manifest()` validates `schema == "canonpack.manifest/v1"`, entry count, per-entry size, total uncompressed size, compression in `stored` or `deflated`, ratio, path safety, and `sha256:<64 lowercase hex>`.
- `preflight_zip()` opens with `zipfile.ZipFile`, rejects entries whose Unix mode is a symlink (`0o120000`), rejects unsupported `compress_type`, rejects unsafe central-directory names before reading member bytes, reads `manifest.json`, calls `preflight_manifest()`, verifies each manifest entry exists once in the archive, and verifies each entry digest by reading bytes with `ZipFile.open()`.
- `preflight_zip()` must not call `extract()` or `extractall()`.

- [ ] **Step 4: Run canonpack tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_canonpack.py -q
```

Expected: PASS.

---

### Task 6: Replay, Source-State, and Concurrency Primitives

**Files:**
- Create: `src/canon/source_state.py`
- Create: `src/canon/replay.py`
- Create: `src/canon/concurrency.py`
- Test: `tests/test_source_state.py`
- Test: `tests/test_replay.py`
- Test: `tests/test_concurrency.py`

**Interfaces:**
- Consumes: stdlib `hashlib`, `json`, `os`, `time`, `dataclasses`, `pathlib`, and callable injection for commits.
- Produces:
  - `@dataclass(frozen=True, slots=True) class SourceStateItem`
  - `class SourceStateError(ValueError)`
  - `def canonical_source_state(items: tuple[SourceStateItem, ...]) -> bytes`
  - `def source_state_sha256(items: tuple[SourceStateItem, ...]) -> str`
  - `def assert_source_state(expected_sha256: str, current: tuple[SourceStateItem, ...]) -> None`
  - `@dataclass(frozen=True, slots=True) class ReplayClaim`
  - `class ReplayError(ValueError)`
  - `def replay_key(claim: ReplayClaim) -> str`
  - `def check_replay_claim(claim: ReplayClaim, *, seen: set[str], current_ord: int) -> str`
  - `@dataclass(frozen=True, slots=True) class RunLock`
  - `class LockError(ValueError)`
  - `def acquire_run_lock(root: str | Path, name: str) -> RunLock`
  - `def release_run_lock(lock: RunLock) -> None`
  - `def guarded_commit(expected_source_state: str, current_items: tuple[SourceStateItem, ...], commit) -> object`

- [ ] **Step 1: Write failing source-state tests**

Create `tests/test_source_state.py`:

```python
from canon.source_state import SourceStateError, SourceStateItem, assert_source_state, source_state_sha256


def test_source_state_digest_is_order_independent() -> None:
    a = SourceStateItem(path="b.md", sha256="sha256:" + "b" * 64, size=2)
    b = SourceStateItem(path="a.md", sha256="sha256:" + "a" * 64, size=1)

    assert source_state_sha256((a, b)) == source_state_sha256((b, a))


def test_source_state_mismatch_raises_source_changed() -> None:
    item = SourceStateItem(path="a.md", sha256="sha256:" + "a" * 64, size=1)

    try:
        assert_source_state("sha256:" + "f" * 64, (item,))
    except SourceStateError as exc:
        assert exc.code == "source_changed"
    else:
        raise AssertionError("expected SourceStateError")
```

- [ ] **Step 2: Write failing replay tests**

Create `tests/test_replay.py`:

```python
from canon.replay import ReplayClaim, ReplayError, check_replay_claim


def _claim(nonce: str = "n1", expires_ord: int = 10) -> ReplayClaim:
    return ReplayClaim(
        principal="operator",
        source_state_sha256="sha256:" + "1" * 64,
        capsule_sha256="sha256:" + "2" * 64,
        nonce=nonce,
        expires_ord=expires_ord,
    )


def test_duplicate_replay_claim_is_rejected() -> None:
    seen: set[str] = set()
    key = check_replay_claim(_claim(), seen=seen, current_ord=1)
    assert key in seen

    try:
        check_replay_claim(_claim(), seen=seen, current_ord=2)
    except ReplayError as exc:
        assert exc.code == "replay"
    else:
        raise AssertionError("expected ReplayError")


def test_expired_replay_claim_is_rejected() -> None:
    try:
        check_replay_claim(_claim(expires_ord=3), seen=set(), current_ord=3)
    except ReplayError as exc:
        assert exc.code == "stale"
    else:
        raise AssertionError("expected ReplayError")
```

- [ ] **Step 3: Write failing concurrency tests**

Create `tests/test_concurrency.py`:

```python
from pathlib import Path

import pytest

from canon.concurrency import LockError, acquire_run_lock, guarded_commit, release_run_lock
from canon.source_state import SourceStateError, SourceStateItem, source_state_sha256


def test_run_lock_conflicts_until_released(tmp_path: Path) -> None:
    first = acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    try:
        with pytest.raises(LockError, match="lock-held"):
            acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    finally:
        release_run_lock(first)

    second = acquire_run_lock(tmp_path, "workspace-AGENTS.md")
    release_run_lock(second)


@pytest.mark.parametrize("name", ["", ".", "..", "../x", "a/b", "a\\b", "a:b"])
def test_bad_lock_names_are_rejected(tmp_path: Path, name: str) -> None:
    with pytest.raises(LockError, match="invalid-lock-name"):
        acquire_run_lock(tmp_path, name)


def test_guarded_commit_aborts_without_calling_commit_on_source_change() -> None:
    item = SourceStateItem(path="a.md", sha256="sha256:" + "a" * 64, size=1)
    called = False

    def commit() -> str:
        nonlocal called
        called = True
        return "written"

    with pytest.raises(SourceStateError):
        guarded_commit("sha256:" + "f" * 64, (item,), commit)

    assert not called
    assert guarded_commit(source_state_sha256((item,)), (item,), commit) == "written"
```

- [ ] **Step 4: Run tests to verify they fail**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_source_state.py tests/test_replay.py tests/test_concurrency.py -q
```

Expected: FAIL because the modules do not exist.

- [ ] **Step 5: Implement source-state canonicalization**

Create `src/canon/source_state.py`:

```python
@dataclass(frozen=True, slots=True)
class SourceStateItem:
    path: str
    sha256: str
    size: int


class SourceStateError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
```

Implementation rules:

- `canonical_source_state()` sorts by `path`, serializes dictionaries with keys `path`, `sha256`, and `size` using `json.dumps(..., sort_keys=True, separators=(",", ":"))`, and appends one `\n`.
- `source_state_sha256()` returns `sha256:<digest>`.
- `assert_source_state()` compares the expected digest to the digest of current items and raises `SourceStateError("source_changed", ...)` on mismatch.

- [ ] **Step 6: Implement replay primitives**

Create `src/canon/replay.py`:

```python
@dataclass(frozen=True, slots=True)
class ReplayClaim:
    principal: str
    source_state_sha256: str
    capsule_sha256: str
    nonce: str
    expires_ord: int


class ReplayError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
```

Implementation rules:

- `replay_key()` hashes a sorted compact JSON object containing all claim fields.
- `check_replay_claim()` rejects `current_ord >= claim.expires_ord` as `ReplayError("stale", ...)`, rejects existing keys as `ReplayError("replay", ...)`, adds accepted keys to `seen`, and returns the key.

- [ ] **Step 7: Implement local lock and guarded commit**

Create `src/canon/concurrency.py`:

```python
@dataclass(frozen=True, slots=True)
class RunLock:
    root: Path
    name: str
    token: str
    path: Path


class LockError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
```

Implementation rules:

- Valid lock names contain only letters, digits, `.`, `_`, and `-`; they cannot be empty, `.`, or `..`.
- `acquire_run_lock()` creates `root / ".canon-locks" / f"{name}.lock"` with `os.O_CREAT | os.O_EXCL | os.O_WRONLY`, writes a token generated from process id and `time.monotonic_ns()`, and raises `LockError("lock-held", ...)` if the file exists.
- `release_run_lock()` unlinks only the exact `RunLock.path` after verifying it is under `root / ".canon-locks"`.
- `guarded_commit()` calls `assert_source_state()` before invoking `commit`.

- [ ] **Step 8: Run primitive tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_source_state.py tests/test_replay.py tests/test_concurrency.py -q
```

Expected: PASS.

---

### Task 7: Retention and Tombstone Policy Interfaces

**Files:**
- Create: `src/canon/retention.py`
- Test: `tests/test_retention.py`

**Interfaces:**
- Consumes:
  - `from canon.atom import CanonAtom`
  - `from canon.omission import Omission`
  - `from canon.transform import TransformReceipt`
- Produces:
  - `RETENTION_ACTIONS: tuple[str, ...]`
  - `DERIVED_STORES: tuple[str, ...]`
  - `@dataclass(frozen=True, slots=True) class DerivedArtifactRef`
  - `@dataclass(frozen=True, slots=True) class RetentionPolicy`
  - `@dataclass(frozen=True, slots=True) class Tombstone`
  - `@dataclass(frozen=True, slots=True) class RetentionPlan`
  - `def validate_retention_policy(policy: RetentionPolicy) -> tuple[str, ...]`
  - `def make_tombstone(subject_id: str, *, reason_code: str, purged_at_ord: int, retain_content_hash: bool, content_sha256: str | None) -> Tombstone`
  - `def plan_retention(subject_id: str, *, policy: RetentionPolicy, derived_refs: tuple[DerivedArtifactRef, ...], content_sha256: str | None) -> RetentionPlan`

- [ ] **Step 1: Write failing retention tests**

Create `tests/test_retention.py`:

```python
from canon.retention import (
    DerivedArtifactRef,
    RetentionPolicy,
    make_tombstone,
    plan_retention,
    validate_retention_policy,
)


def test_invalid_action_is_reported() -> None:
    policy = RetentionPolicy(subject_id="atom-1", action="erase", retain_content_hash=False, derived_stores=("files",))

    assert validate_retention_policy(policy) == ("invalid-action",)


def test_unknown_derived_store_is_reported() -> None:
    policy = RetentionPolicy(subject_id="atom-1", action="tombstone", retain_content_hash=False, derived_stores=("unknown-store",))

    assert validate_retention_policy(policy) == ("unknown-derived-store:unknown-store",)


def test_purge_tombstone_does_not_retain_hash_when_policy_disallows_it() -> None:
    tombstone = make_tombstone(
        "atom-1",
        reason_code="operator-request",
        purged_at_ord=44,
        retain_content_hash=False,
        content_sha256="sha256:" + "a" * 64,
    )

    assert tombstone.content_sha256 is None
    assert "raw" not in repr(tombstone).casefold()


def test_plan_retention_covers_all_refs_but_does_not_delete() -> None:
    refs = (
        DerivedArtifactRef(store="files", locator="global/a.json", content_sha256="sha256:" + "1" * 64, contains_raw=True),
        DerivedArtifactRef(store="vault", locator="workspace/a.md", content_sha256="sha256:" + "2" * 64, contains_raw=True),
    )
    policy = RetentionPolicy(subject_id="atom-1", action="purge-derived", retain_content_hash=False, derived_stores=("files", "vault"))

    plan = plan_retention("atom-1", policy=policy, derived_refs=refs, content_sha256="sha256:" + "a" * 64)

    assert plan.ok
    assert plan.refs_to_purge == refs
    assert plan.deleted_paths == ()
    assert plan.tombstone is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_retention.py -q
```

Expected: FAIL because `canon.retention` does not exist.

- [ ] **Step 3: Implement plan-only retention types**

Create `src/canon/retention.py`:

```python
RETENTION_ACTIONS = ("retain", "tombstone", "purge-derived", "purge-all")
DERIVED_STORES = (
    "sqlite",
    "files",
    "vault",
    "managed-surface",
    "capsule",
    "canonpack",
    "witness",
    "backup",
    "exported-artifact",
)


@dataclass(frozen=True, slots=True)
class DerivedArtifactRef:
    store: str
    locator: str
    content_sha256: str | None
    contains_raw: bool


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    subject_id: str
    action: str
    retain_content_hash: bool
    derived_stores: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Tombstone:
    subject_id: str
    reason_code: str
    purged_at_ord: int
    content_sha256: str | None


@dataclass(frozen=True, slots=True)
class RetentionPlan:
    ok: bool
    subject_id: str
    action: str
    refs_to_purge: tuple[DerivedArtifactRef, ...]
    tombstone: Tombstone | None
    omissions: tuple[Omission, ...]
    receipts: tuple[TransformReceipt, ...]
    violations: tuple[str, ...]
    deleted_paths: tuple[str, ...] = ()
```

Implementation rules:

- `validate_retention_policy()` returns codes, not exceptions, so import review can aggregate.
- `make_tombstone()` includes `content_sha256` only when `retain_content_hash=True`.
- `plan_retention()` never deletes files and must always return `deleted_paths=()`.
- `plan_retention()` selects refs whose `store` is in `policy.derived_stores`; for `purge-all`, all passed refs are selected.
- Use foundation `Omission` and `TransformReceipt` for receipts when action is not `retain`; do not create duplicate receipt dataclasses.

- [ ] **Step 4: Run retention tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_retention.py -q
```

Expected: PASS.

---

### Task 8: Read-Only Import Review Composition

**Files:**
- Create: `src/canon/import_review.py`
- Test: `tests/test_import_review.py`

**Interfaces:**
- Consumes:
  - `CanonAtom` from `canon.atom`
  - `Omission` from `canon.omission`
  - `TransformReceipt` from `canon.transform`
  - `ImportSubject` and `review_import_subject` from `canon.import_policy`
  - `quarantine_text` from `canon.secret_quarantine`
  - `assert_source_state` from `canon.source_state`
  - `check_replay_claim` and `ReplayClaim` from `canon.replay`
- Produces:
  - `@dataclass(frozen=True, slots=True) class ImportItem`
  - `@dataclass(frozen=True, slots=True) class ImportFinding`
  - `@dataclass(frozen=True, slots=True) class ImportReview`
  - `def review_import_items(items: tuple[ImportItem, ...], *, profile: str, pinned_key_ids: frozenset[str], expected_source_state: str, current_source_items: tuple[SourceStateItem, ...], seen_replay_keys: set[str], current_ord: int) -> ImportReview`

- [ ] **Step 1: Write failing import-review tests**

Create `tests/test_import_review.py`:

```python
from __future__ import annotations

from canon.atom import CanonAtom
from canon.import_review import ImportItem, review_import_items
from canon.source_state import SourceStateItem, source_state_sha256


def _atom(atom_id: str, *, critical: bool = False, disclosure_label: str = "project-only") -> CanonAtom:
    return CanonAtom.from_dict({
        "atom_schema": "canon.atom/v1",
        "type": "active-goal" if critical else "episodic-fact",
        "id": atom_id,
        "layer": "workspace",
        "scope_key": "public/canon",
        "precedence_rank": 50,
        "status": "active",
        "classification": "normative" if critical else "descriptive",
        "critical": critical,
        "value": {"text": "do not drop me" if critical else "ordinary fact"},
        "source_refs": ["source:1"],
        "source_span_refs": [],
        "freshness": {"state": "current"},
        "trust": {"label": "trusted-local"},
        "disclosure": {"label": disclosure_label},
        "hashes": {"content_sha256": "sha256:" + "1" * 64},
    })


def test_combined_untrusted_secret_and_source_stale_findings_are_visible() -> None:
    current = (SourceStateItem(path="source.json", sha256="sha256:" + "a" * 64, size=1),)
    item = ImportItem(
        source_id="capsule-1",
        atom=_atom("fact-1"),
        text="token sk-live-abcdefghijklmnopqrstuvwxyz012345",
        signature_status="valid",
        key_id="unknown",
        local=False,
        model_synthesized=False,
        replay_nonce="nonce-1",
        replay_expires_ord=100,
    )

    review = review_import_items(
        (item,),
        profile="project-only",
        pinned_key_ids=frozenset({"pinned"}),
        expected_source_state="sha256:" + "f" * 64,
        current_source_items=current,
        seen_replay_keys=set(),
        current_ord=1,
    )

    assert not review.ok
    assert {"untrusted-import", "secret-quarantined", "source_changed"} <= {f.code for f in review.findings}
    assert review.accepted_atoms == ()


def test_critical_disclosure_omission_blocks_import() -> None:
    current = (SourceStateItem(path="source.json", sha256="sha256:" + "a" * 64, size=1),)
    expected = source_state_sha256(current)
    item = ImportItem(
        source_id="capsule-2",
        atom=_atom("goal-1", critical=True, disclosure_label="private-local-only"),
        text="safe text",
        signature_status="none",
        key_id=None,
        local=True,
        model_synthesized=False,
        replay_nonce="nonce-2",
        replay_expires_ord=100,
    )

    review = review_import_items(
        (item,),
        profile="team-safe",
        pinned_key_ids=frozenset(),
        expected_source_state=expected,
        current_source_items=current,
        seen_replay_keys=set(),
        current_ord=1,
    )

    assert not review.ok
    assert "critical-disclosure-omission" in {f.code for f in review.findings}


def test_clean_trusted_local_review_accepts_atom_without_backend_write() -> None:
    current = (SourceStateItem(path="source.json", sha256="sha256:" + "a" * 64, size=1),)
    expected = source_state_sha256(current)
    item = ImportItem(
        source_id="capsule-3",
        atom=_atom("fact-2"),
        text="safe text",
        signature_status="none",
        key_id=None,
        local=True,
        model_synthesized=False,
        replay_nonce="nonce-3",
        replay_expires_ord=100,
    )

    review = review_import_items(
        (item,),
        profile="project-only",
        pinned_key_ids=frozenset(),
        expected_source_state=expected,
        current_source_items=current,
        seen_replay_keys=set(),
        current_ord=1,
    )

    assert review.ok
    assert tuple(a.to_dict()["id"] for a in review.accepted_atoms) == ("fact-2",)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_import_review.py -q
```

Expected: FAIL because `canon.import_review` does not exist.

- [ ] **Step 3: Implement read-only composition types**

Create `src/canon/import_review.py`:

```python
@dataclass(frozen=True, slots=True)
class ImportItem:
    source_id: str
    atom: CanonAtom
    text: str
    signature_status: str
    key_id: str | None
    local: bool
    model_synthesized: bool
    replay_nonce: str
    replay_expires_ord: int


@dataclass(frozen=True, slots=True)
class ImportFinding:
    code: str
    severity: str
    subject_id: str
    message: str


@dataclass(frozen=True, slots=True)
class ImportReview:
    ok: bool
    findings: tuple[ImportFinding, ...]
    accepted_atoms: tuple[CanonAtom, ...]
    omissions: tuple[Omission, ...]
    receipts: tuple[TransformReceipt, ...]
```

Implementation rules:

- Build one `ImportSubject` per item and call `review_import_subject()`.
- Run `quarantine_text()` on `item.text`; convert quarantine reason codes into `ImportFinding` records.
- Call `assert_source_state()` once before accepting any item. On mismatch, record `ImportFinding("source_changed", "critical", "source-state", ...)`.
- Build a `ReplayClaim` per item and call `check_replay_claim()`. Convert `ReplayError.code` into an `ImportFinding`.
- Do not accept any atom if any finding has severity `critical` or `warning`.
- Do not call any backend, renderer, writer, unzip extraction, network request, or CLI.

- [ ] **Step 4: Run import-review tests**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_import_review.py -q
```

Expected: PASS.

---

## Final Review Gates

- [ ] **Gate 1: Security/import unit slices pass**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_backend_base.py tests/test_files_backend.py tests/test_path_policy.py tests/test_import_policy.py tests/test_secret_quarantine.py tests/test_canonpack.py tests/test_source_state.py tests/test_replay.py tests/test_concurrency.py tests/test_retention.py tests/test_import_review.py -q
```

Expected: PASS.

- [ ] **Gate 2: Full Canon suite passes**

Run:

```bash
python -m pytest -p no:cacheprovider
```

Expected: PASS.

- [ ] **Gate 3: Compile all Python files**

Run:

```bash
python -m compileall -q src tests
```

Expected: exit code 0.

- [ ] **Gate 4: Dependency and integration boundary check**

Run:

```bash
git diff -- pyproject.toml
rg -n "requests|httpx|aiohttp|cryptography|yaml|boto|openai|anthropic" src/canon tests
rg -n "ZipFile\\.(extract|extractall)|extract\\(" src/canon tests
```

Expected:

- `git diff -- pyproject.toml` prints nothing.
- The dependency search has no new runtime dependency imports.
- The extraction search finds no call to `ZipFile.extract`, `ZipFile.extractall`, or archive extraction helper in `src/canon`.

- [ ] **Gate 5: FilesBackend blocker proof**

Run:

```bash
python -m pytest -p no:cacheprovider tests/test_files_backend.py::test_put_invalid_scope_refuses_before_creating_outside_file tests/test_files_backend.py::test_get_invalid_key_refuses_before_path_lookup -q
```

Expected: PASS, with no file created outside the temp backend root.

- [ ] **Gate 6: Manual diff review**

Review:

```bash
git diff -- src/canon tests
```

Expected findings:

- `FilesBackend` path derivation cannot receive an invalid record scope or malformed key.
- Path-policy code is local, deterministic, and stdlib-only.
- Trust/disclosure, quarantine, replay, source-state, retention, and import-review modules import foundation `CanonAtom`, `Omission`, and `TransformReceipt` instead of redefining them.
- `.canonpack` code performs preflight only and never extracts archive contents.
- Retention code returns plans and tombstones only; it performs no deletion.
- Import review is read-only and never calls backend `put()`, surface writers, vault writers, network clients, or subprocesses.

## Review Notes for Implementers

- Task 1 is a release blocker and must land before any task that can write imported records.
- If foundation atom/omission/receipt modules are not present, stop after Task 1 and complete the foundation plan. Do not add compatibility shims in security/import modules.
- Keep new source files small. If a file approaches 300 lines, split private helpers into a second focused module with tests in the same task.
- Use exact failure codes in tests. These codes become the stable boundary between library policy and any future CLI, MCP, app, or adapter layer.
