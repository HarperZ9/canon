from __future__ import annotations

import gc
import json
import socket
import subprocess
import tempfile
import weakref
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

import pytest

FIXTURES = Path(__file__).parent / "fixtures" / "bootstrap"


def _config(**overrides: object):
    from canon.bootstrap import BootstrapConfig

    workspace = Path(tempfile.mkdtemp(prefix="canon-bootstrap-test-"))
    values = {
        "workspace": str(workspace),
        "state_dir": ".canon",
        "target": "codex-cli",
        "tier": "native-advisory",
        "profile": "handoff",
        "offline": False,
        "run_id": "run-1",
    }
    values.update(overrides)
    return BootstrapConfig(**values)


def _event_states(report: object) -> tuple[str, ...]:
    return tuple(event.state for event in report.events)  # type: ignore[attr-defined]


def _success_report():
    from canon.bootstrap import run_bootstrap

    return run_bootstrap(_config(target="chatgpt-app", tier="guided"))


def _copy_inputs(workspace: Path) -> None:
    (workspace / "records.jsonl").write_bytes((FIXTURES / "records.jsonl").read_bytes())
    (workspace / "atoms.jsonl").write_bytes((FIXTURES / "atoms.jsonl").read_bytes())
    (workspace / "readiness_pass.json").write_bytes((FIXTURES / "readiness_pass.json").read_bytes())
    (workspace / "readiness_fail_missing_goal.json").write_bytes(
        (FIXTURES / "readiness_fail_missing_goal.json").read_bytes(),
    )


def _source_config(workspace: Path, **overrides: object):
    values = {
        "workspace": str(workspace),
        "state_dir": ".canon",
        "target": "codex-cli",
        "tier": "native-advisory",
        "profile": "handoff",
        "offline": False,
        "run_id": "run:task9.v1",
        "records_path": "records.jsonl",
        "atoms_path": "atoms.jsonl",
        "readiness_response_path": "readiness_pass.json",
    }
    values.update(overrides)
    return _config(**values)


def _run_source_bootstrap(workspace: Path, **overrides: object):
    from canon.bootstrap import run_bootstrap

    return run_bootstrap(_source_config(workspace, **overrides))


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _state_event(report: object, state: str):
    for event in report.events:  # type: ignore[attr-defined]
        if event.state == state:
            return event
    raise AssertionError(f"missing state {state}")


def _witness_path(report: object, workspace: Path) -> Path:
    value = report.to_result_data()["witness_path"]  # type: ignore[index]
    assert type(value) is str
    assert "\\" not in value
    return workspace / value


def _cache_entry(report: object, workspace: Path) -> dict[str, object]:
    key = report.to_result_data()["cache_key"]  # type: ignore[index]
    assert type(key) is str
    return _read_json(workspace / ".canon" / "cache" / "bundles" / f"{key.removeprefix('sha256:')}.json")


def _assert_no_raw_material(rendered: str, workspace: Path) -> None:
    assert "Feature-first. Words with weight." not in rendered
    assert "# CANON" not in rendered
    assert str(workspace) not in rendered
    assert _Canary.token not in rendered


def _report_serializers(report: object):
    return (report.to_dict, report.to_result_data)  # type: ignore[attr-defined]


class _Canary:
    token = "leaked-secret-token"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def fail(self, name: str) -> object:
        self.calls.append(name)
        raise RuntimeError(self.token)

    def repr_text(self, name: str) -> str:
        self.calls.append(name)
        return self.token


class _HostileMapping(Mapping[str, object]):
    def __init__(self, canary: _Canary) -> None:
        self._canary = canary

    def __getitem__(self, key: str) -> object:
        return self._canary.fail("__getitem__")

    def __iter__(self):
        return self._canary.fail("__iter__")

    def __len__(self) -> int:
        self._canary.fail("__len__")
        return 0

    def items(self):
        return self._canary.fail("items")

    def __repr__(self) -> str:
        return self._canary.repr_text("__repr__")


class _HostileList(list):
    def __init__(self, canary: _Canary) -> None:
        super().__init__(["bad"])
        self._canary = canary

    def __getitem__(self, index: int) -> object:
        return self._canary.fail("__getitem__")

    def __iter__(self):
        return self._canary.fail("__iter__")

    def __len__(self) -> int:
        self._canary.fail("__len__")
        return 1

    def __repr__(self) -> str:
        return self._canary.repr_text("__repr__")


def _assert_sanitized_type_error(callable_object: object, canary: _Canary, text: str) -> None:
    with pytest.raises(TypeError) as excinfo:
        callable_object()  # type: ignore[operator]
    message = str(excinfo.value)
    assert text in message
    assert _Canary.token not in message
    assert canary.calls == []


def _assert_sanitized_error(callable_object: object, error_type: type[Exception], text: str, canary: _Canary | None) -> None:
    with pytest.raises(error_type) as excinfo:
        callable_object()  # type: ignore[operator]
    message = str(excinfo.value)
    assert text in message
    assert _Canary.token not in message
    assert excinfo.value.__cause__ is None
    if canary is not None:
        assert canary.calls == []


def _malformed_frozen_mapping_cases():
    from canon.bootstrap import BootstrapEvent
    from canon.bootstrap_validation import _FrozenBootstrapMapping

    uninitialized = _FrozenBootstrapMapping.__new__(_FrozenBootstrapMapping)

    deleted = BootstrapEvent("detect_entry", True, "ok", "detected", {"safe": True}).data
    object.__delattr__(deleted, "_items")  # type: ignore[arg-type]

    canary = _Canary()
    injected = _FrozenBootstrapMapping.__new__(_FrozenBootstrapMapping)
    object.__setattr__(injected, "_items", canary)

    return (("uninitialized", uninitialized, None), ("deleted", deleted, None), ("injected", injected, canary))


def test_bootstrap_states_are_exact_and_ordered() -> None:
    from canon.bootstrap import BOOTSTRAP_STATES

    assert BOOTSTRAP_STATES == (
        "detect_entry",
        "resolve_layers",
        "collect_source_state",
        "preflight",
        "compile_or_reuse_capsule",
        "present_context",
        "readiness_probe",
        "emit_witness",
        "release_to_work",
    )


def test_non_enforced_placeholder_reaches_full_prefix_with_adapter_tiers() -> None:
    from canon.bootstrap import BOOTSTRAP_STATES, run_bootstrap
    from canon.exit_codes import EX_OK

    report = run_bootstrap(_config(target="chatgpt-app", tier="guided"))

    assert report.ok is True
    assert report.failure_code == "ok"
    assert report.exit_code == EX_OK
    assert _event_states(report) == BOOTSTRAP_STATES
    assert all(event.ok for event in report.events)
    assert report.data["adapter_id"] == "chatgpt-app"  # type: ignore[index]
    assert report.data["authoritative_tier"] == "guided"  # type: ignore[index]
    assert report.data["requested_tier"] == "guided"  # type: ignore[index]


def test_bootstrap_sources_readiness_cache_witness_and_release(tmp_path: Path) -> None:
    from canon.bootstrap import BOOTSTRAP_STATES
    from canon.witness import BootstrapWitness, validate_bootstrap_witness

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    report = _run_source_bootstrap(workspace, started_at="2026-08-30T00:00:00Z")
    data = report.to_result_data()
    witness_path = _witness_path(report, workspace)
    witness = BootstrapWitness.from_dict(_read_json(witness_path))
    entry = _cache_entry(report, workspace)

    assert report.ok is True
    assert _event_states(report) == BOOTSTRAP_STATES
    assert data["cache_status"] == "miss"
    assert data["readiness_verdict"] == "pass"
    assert data["host_enforcement_observed"] is False
    assert witness.started_at == "2026-08-30T00:00:00Z"
    assert validate_bootstrap_witness(witness) == []
    assert entry["schema"] == "canon.bootstrap-cache-entry/v1"
    assert entry["cache_key"] == data["cache_key"]
    assert entry["source_state"] == data["source_state"]
    assert (workspace / ".canon" / "cache" / "current.json").exists()
    _assert_no_raw_material(json.dumps(report.to_result_data()), workspace)
    _assert_no_raw_material(witness_path.read_text(encoding="utf-8"), workspace)


def test_second_identical_bootstrap_reuses_cache_without_compiling(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.bootstrap_runtime as runtime

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    first = _run_source_bootstrap(workspace)

    def forbidden_compile(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("cache hit must not compile")

    monkeypatch.setattr(runtime, "compile_capsule", forbidden_compile)
    second = _run_source_bootstrap(workspace)

    assert first.ok is True
    assert second.ok is True
    assert first.to_result_data()["cache_status"] == "miss"
    assert second.to_result_data()["cache_status"] == "hit"
    for key in ("cache_key", "capsule_id", "manifest_sha256", "canon_md_sha256"):
        assert first.to_result_data()[key] == second.to_result_data()[key]


def test_bootstrap_cache_key_changes_for_sources_profile_offline_target_and_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.bootstrap as bootstrap
    from canon.adapter import AdapterDescriptor, descriptor_for

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    base = _run_source_bootstrap(workspace, run_id="run-base").to_result_data()["cache_key"]
    changed_source = workspace / "records.jsonl"
    changed_source.write_bytes(changed_source.read_bytes() + b"\n")
    source_key = _run_source_bootstrap(workspace, run_id="run-source").to_result_data()["cache_key"]
    changed_source.write_bytes((FIXTURES / "records.jsonl").read_bytes())
    profile_key = _run_source_bootstrap(workspace, run_id="run-profile", profile="needle").to_result_data()["cache_key"]
    offline_key = _run_source_bootstrap(workspace, run_id="run-offline", offline=True).to_result_data()["cache_key"]
    target_key = _run_source_bootstrap(workspace, run_id="run-target", target="chatgpt-app", tier="guided").to_result_data()["cache_key"]
    original = descriptor_for("codex-cli")
    patched = AdapterDescriptor.from_dict({**original.to_dict(), "version": "foundation-task9"})
    monkeypatch.setattr(bootstrap, "descriptor_for", lambda target: patched)
    descriptor_key = _run_source_bootstrap(workspace, run_id="run-descriptor").to_result_data()["cache_key"]

    assert len({base, source_key, profile_key, offline_key, target_key, descriptor_key}) == 6


@pytest.mark.parametrize("corrupt_current", (True, False))
def test_corrupt_cache_state_fails_closed_without_recompile_or_witness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    corrupt_current: bool,
) -> None:
    import canon.bootstrap_runtime as runtime

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    first = _run_source_bootstrap(workspace)
    key = first.to_result_data()["cache_key"]
    witnesses_before = _tree(workspace / ".canon" / "witnesses")
    assert type(key) is str
    if corrupt_current:
        (workspace / ".canon" / "cache" / "current.json").write_text("[]\n", encoding="utf-8")
    else:
        path = workspace / ".canon" / "cache" / "bundles" / f"{key.removeprefix('sha256:')}.json"
        path.write_text("{bad-json\n", encoding="utf-8")

    def forbidden_compile(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AssertionError("corrupt cache must fail closed")

    monkeypatch.setattr(runtime, "compile_capsule", forbidden_compile)
    report = _run_source_bootstrap(workspace, run_id="run-corrupt")

    assert report.ok is False
    assert report.failure_code in ("io_error", "conflict")
    assert report.events[-1].state == "compile_or_reuse_capsule"
    assert "release_to_work" not in _event_states(report)
    assert _tree(workspace / ".canon" / "witnesses") == witnesses_before


def test_failed_readiness_is_terminal_and_reports_missing_ids(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    report = _run_source_bootstrap(workspace, readiness_response_path="readiness_fail_missing_goal.json")
    data = report.to_result_data()

    assert report.ok is False
    assert report.failure_code == "readiness_failed"
    assert report.events[-1].state == "readiness_probe"
    assert data["readiness_verdict"] == "fail"
    assert data["missing_ids"] == ["goal-foundation"]
    assert "release_to_work" not in _event_states(report)
    assert not (workspace / ".canon" / "witnesses").exists()


def test_stale_frontier_response_shape_cannot_pass_live_readiness_api(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    response = _read_json(workspace / "readiness_pass.json")
    response["frontier"] = response.pop("frontier_state_ids")
    (workspace / "readiness_stale.json").write_text(json.dumps(response, sort_keys=True) + "\n", encoding="utf-8")

    report = _run_source_bootstrap(workspace, readiness_response_path="readiness_stale.json")

    assert report.ok is False
    assert report.failure_code == "readiness_failed"
    assert report.to_result_data()["readiness_verdict"] in ("fail", "blocked")
    assert "release_to_work" not in _event_states(report)


def test_absent_readiness_response_releases_only_for_non_enforced_builtin(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    report = _run_source_bootstrap(workspace, readiness_response_path=None, target="chatgpt-app", tier="guided")
    data = report.to_result_data()
    witness = _read_json(_witness_path(report, workspace))

    assert report.ok is True
    assert data["readiness_verdict"] == "unknown"
    assert data["readiness_response_hash"] is None
    assert data["does_not_prove"]
    assert witness["readiness_result"]["verdict"] == "unknown"


def test_absent_readiness_response_fails_closed_for_enforced_descriptor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.bootstrap as bootstrap
    from canon.adapter import AdapterDescriptor

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    descriptor = AdapterDescriptor(
        adapter_id="owned-wrapper",
        display_name="Owned Wrapper",
        version="1",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": True},
        evidence_refs=("fixture:owned-wrapper-blocking-start",),
    )
    monkeypatch.setattr(bootstrap, "descriptor_for", lambda target: descriptor)

    report = _run_source_bootstrap(workspace, target="owned-wrapper", tier="enforced", readiness_response_path=None)

    assert report.ok is False
    assert report.failure_code == "readiness_failed"
    assert report.events[-1].state == "readiness_probe"
    assert not (workspace / ".canon" / "witnesses").exists()


def test_artificial_enforced_success_records_observed_host_enforcement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.bootstrap as bootstrap
    from canon.adapter import AdapterDescriptor
    from canon.witness import BootstrapWitness, validate_bootstrap_witness

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    descriptor = AdapterDescriptor(
        adapter_id="owned-wrapper",
        display_name="Owned Wrapper",
        version="1",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": True},
        evidence_refs=("fixture:owned-wrapper-blocking-start",),
    )
    monkeypatch.setattr(bootstrap, "descriptor_for", lambda target: descriptor)

    report = _run_source_bootstrap(workspace, target="owned-wrapper", tier="enforced")
    witness = _read_json(_witness_path(report, workspace))

    assert report.ok is True
    assert report.to_result_data()["host_enforcement_observed"] is True
    assert witness["host_enforcement_observed"] is True
    assert {check["verdict"] for check in witness["checks"]} == {"pass"}
    assert validate_bootstrap_witness(BootstrapWitness.from_dict(witness)) == []


def test_witness_filename_is_digest_derived_and_duplicate_runs_are_safe(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    first = _run_source_bootstrap(workspace, run_id="run:task9.v1", started_at="same")
    second = _run_source_bootstrap(workspace, run_id="run:task9.v1", started_at="same")
    conflict = _run_source_bootstrap(workspace, run_id="run:task9.v1", started_at="different")
    witness_path = _witness_path(first, workspace)

    assert first.ok is True
    assert second.ok is True
    assert conflict.failure_code == "conflict"
    assert conflict.events[-1].state == "emit_witness"
    assert "run:task9.v1" not in witness_path.name
    assert witness_path.name.startswith("run-")
    assert witness_path.name.endswith(".json")
    assert "release_to_work" not in _event_states(conflict)


def test_witness_directory_failure_is_terminal_before_release(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    witness_parent = workspace / ".canon" / "witnesses"
    witness_parent.parent.mkdir()
    witness_parent.write_text("not a directory\n", encoding="utf-8")

    report = _run_source_bootstrap(workspace)

    assert report.ok is False
    assert report.failure_code == "io_error"
    assert report.events[-1].state == "emit_witness"
    assert "release_to_work" not in _event_states(report)


@pytest.mark.parametrize(
    ("overrides", "failure"),
    (
        ({"records_path": "missing.jsonl"}, "source_unreachable"),
        ({"records_path": "../outside.jsonl"}, "unsafe_path"),
        ({"state_dir": "../outside"}, "unsafe_path"),
        ({"records_path": "-"}, "invalid_args"),
        ({"atoms_path": None}, "invalid_args"),
    ),
)
def test_path_and_source_argument_failures_prevent_state_mutation(
    tmp_path: Path,
    overrides: dict[str, object],
    failure: str,
) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    report = _run_source_bootstrap(workspace, **overrides)

    assert report.ok is False
    assert report.failure_code == failure
    assert "compile_or_reuse_capsule" not in _event_states(report)
    assert not (workspace / ".canon").exists()


@pytest.mark.parametrize("role", ("atoms", "readiness"))
def test_secret_inputs_are_quarantined_before_cache_witness_or_public_leak(tmp_path: Path, role: str) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    canary = json.loads((FIXTURES / "secret_atoms.jsonl").read_text(encoding="utf-8"))["value"]["summary"]
    if role == "atoms":
        (workspace / "atoms.jsonl").write_bytes((FIXTURES / "secret_atoms.jsonl").read_bytes())
        report = _run_source_bootstrap(workspace)
    else:
        (workspace / "readiness_secret.json").write_text(
            json.dumps({"schema": "canon.readiness-response/v1", "active_goal_ids": [canary]}) + "\n",
            encoding="utf-8",
        )
        report = _run_source_bootstrap(workspace, readiness_response_path="readiness_secret.json")

    rendered = json.dumps(report.to_dict(), sort_keys=True) + repr(report)
    assert report.failure_code == "secret_quarantine"
    assert canary not in rendered
    assert not (workspace / ".canon").exists()


def test_direct_api_rejects_mutually_exclusive_or_hostile_readiness_inputs() -> None:
    from canon.bootstrap import BootstrapConfig, BootstrapConfigError

    with pytest.raises(BootstrapConfigError):
        _config(readiness_response={}, readiness_response_path="response.json")

    canary = _Canary()
    with pytest.raises(BootstrapConfigError) as excinfo:
        BootstrapConfig(
            workspace=".",
            state_dir=".canon",
            target="codex-cli",
            tier="native-advisory",
            profile="handoff",
            offline=False,
            run_id="run-1",
            readiness_response=_HostileMapping(canary),
        )
    assert _Canary.token not in str(excinfo.value)
    assert canary.calls == []


def test_empty_source_set_uses_live_empty_source_state_and_default_started_at(tmp_path: Path) -> None:
    from canon.source_state import source_state_sha256

    workspace = tmp_path / "work"
    workspace.mkdir()

    report = _run_source_bootstrap(workspace, records_path=None, atoms_path=None, readiness_response_path=None)
    witness = _read_json(_witness_path(report, workspace))

    assert report.ok is True
    assert report.to_result_data()["source_state"]["records_digest"] == source_state_sha256(())
    assert witness["started_at"] == "not-recorded"


def test_missing_required_critical_atom_maps_to_critical_atom_loss(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.bootstrap_runtime as runtime

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    monkeypatch.setattr(runtime, "_critical_atom_ids", lambda atoms: ("missing-critical",))

    report = _run_source_bootstrap(workspace)

    assert report.failure_code == "critical_atom_loss"
    assert report.events[-1].state == "compile_or_reuse_capsule"
    assert not (workspace / ".canon" / "witnesses").exists()


def test_unsupported_descriptor_terminates_before_lifecycle_release(monkeypatch: pytest.MonkeyPatch) -> None:
    import canon.bootstrap as bootstrap
    from canon.adapter import AdapterDescriptor
    from canon.exit_codes import EX_UNSUPPORTED

    descriptor = AdapterDescriptor(
        adapter_id="retired-target",
        display_name="Retired Target",
        version="1",
        integration_tier="unsupported",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("stdout",),
        bootstrap={"can_block_before_work": False},
    )
    monkeypatch.setattr(bootstrap, "descriptor_for", lambda target: descriptor)

    report = bootstrap.run_bootstrap(_config(target="retired-target", tier="unsupported"))

    assert report.ok is False
    assert report.failure_code == "unsupported_lifecycle"
    assert report.exit_code == EX_UNSUPPORTED
    assert _event_states(report) == ("detect_entry",)
    assert report.events[0].failure_code == "unsupported_lifecycle"
    assert "release_to_work" not in _event_states(report)


@pytest.mark.parametrize("target", ("chatgpt-app", "local-runner"))
def test_guided_targets_forced_to_enforced_fail_tier_mislabeled(target: str) -> None:
    from canon.bootstrap import run_bootstrap
    from canon.exit_codes import EX_UNSUPPORTED

    report = run_bootstrap(_config(target=target, tier="enforced"))

    assert report.ok is False
    assert report.failure_code == "tier_mislabeled"
    assert report.exit_code == EX_UNSUPPORTED
    assert _event_states(report) == ("detect_entry",)
    assert report.events[0].failure_code == "tier_mislabeled"
    assert "release_to_work" not in _event_states(report)


def test_unsupported_target_fails_closed_without_lookup_exception_or_raw_target() -> None:
    from canon.bootstrap import run_bootstrap
    from canon.exit_codes import EX_USAGE

    report = run_bootstrap(_config(target="unknown-adapter", tier="guided"))

    assert report.ok is False
    assert report.failure_code == "invalid_args"
    assert report.exit_code == EX_USAGE
    assert _event_states(report) == ("detect_entry",)
    assert "unknown-adapter" not in report.message
    assert "unknown-adapter" not in report.events[0].message


class _HostileStr(str):
    def __repr__(self) -> str:
        return "leaked-secret-token"


def test_config_constructor_rejects_malformed_values_without_hostile_repr() -> None:
    from canon.bootstrap import BootstrapConfig, BootstrapConfigError

    with pytest.raises(BootstrapConfigError) as hostile:
        BootstrapConfig(
            workspace="C:/work/canon",
            state_dir="C:/work/canon/.canon",
            target="codex-cli",
            tier="native-advisory",
            profile="handoff",
            offline=False,
            run_id=_HostileStr("run-1"),
        )
    with pytest.raises(BootstrapConfigError) as nested:
        _config(readiness_response={"ids": [object()]})

    assert "leaked-secret-token" not in str(hostile.value)
    assert "object" not in str(nested.value)


def test_run_bootstrap_revalidates_tampered_config_as_empty_event_invalid_args() -> None:
    from canon.bootstrap import run_bootstrap
    from canon.exit_codes import EX_USAGE

    config = _config()
    object.__setattr__(config, "run_id", _HostileStr("run-1"))
    report = run_bootstrap(config)

    assert report.ok is False
    assert report.failure_code == "invalid_args"
    assert report.exit_code == EX_USAGE
    assert report.events == ()
    assert "leaked-secret-token" not in report.message


def test_config_snapshots_readiness_response_before_caller_mutation() -> None:
    response = {"ids": ["goal-1"], "nested": {"ok": True}}
    config = _config(readiness_response=response)

    response["ids"].append("goal-2")  # type: ignore[attr-defined]
    response["nested"]["ok"] = False  # type: ignore[index]

    assert config.readiness_response["ids"] == ("goal-1",)  # type: ignore[index]
    assert config.readiness_response["nested"]["ok"] is True  # type: ignore[index]
    with pytest.raises(TypeError):
        config.readiness_response["nested"]["ok"] = False  # type: ignore[index]


def test_config_rejects_mappingproxy_readiness_response_without_dispatch() -> None:
    from canon.bootstrap import BootstrapConfigError

    with pytest.raises(BootstrapConfigError, match="invalid bootstrap config"):
        _config(readiness_response=MappingProxyType({"ok": True}))

    canary = _Canary()
    with pytest.raises(BootstrapConfigError) as excinfo:
        _config(readiness_response=MappingProxyType(_HostileMapping(canary)))
    assert "invalid bootstrap config" in str(excinfo.value)
    assert _Canary.token not in str(excinfo.value)
    assert canary.calls == []


def test_config_internal_snapshot_can_be_revalidated_on_rerun() -> None:
    from canon.bootstrap import run_bootstrap

    config = _config(readiness_response={"ids": ["goal-1"], "nested": {"ok": True}})
    report = run_bootstrap(config)

    assert report.ok is True
    assert config.readiness_response["ids"] == ("goal-1",)  # type: ignore[index]
    assert config.readiness_response["nested"]["ok"] is True  # type: ignore[index]


def test_config_rejects_malformed_private_readiness_snapshot_without_raw_attribute_error() -> None:
    from canon.bootstrap import BootstrapConfigError, run_bootstrap
    from canon.exit_codes import EX_USAGE

    for _, malformed, canary in _malformed_frozen_mapping_cases():
        _assert_sanitized_error(lambda: _config(readiness_response=malformed), BootstrapConfigError, "invalid bootstrap config", canary)

        config = _config()
        object.__setattr__(config, "readiness_response", malformed)
        report = run_bootstrap(config)

        assert report.ok is False
        assert report.failure_code == "invalid_args"
        assert report.exit_code == EX_USAGE
        assert report.events == ()
        assert "AttributeError" not in report.message
        assert _Canary.token not in report.message
        if canary is not None:
            assert canary.calls == []


def test_enforced_placeholder_without_readiness_response_fails_gate_code(monkeypatch: pytest.MonkeyPatch) -> None:
    import canon.bootstrap as bootstrap
    from canon.adapter import AdapterDescriptor
    from canon.exit_codes import EX_GATE

    descriptor = AdapterDescriptor(
        adapter_id="owned-wrapper",
        display_name="Owned Wrapper",
        version="1",
        integration_tier="enforced",
        target_surfaces=("CANON.md",),
        import_modes=("file",),
        export_modes=("file",),
        bootstrap={"can_block_before_work": True},
        evidence_refs=("fixture:owned-wrapper-blocking-start",),
    )
    monkeypatch.setattr(bootstrap, "descriptor_for", lambda target: descriptor)

    report = bootstrap.run_bootstrap(_config(target="owned-wrapper", tier="enforced"))

    assert report.ok is False
    assert report.failure_code == "readiness_failed"
    assert report.exit_code == EX_GATE
    assert _event_states(report) == bootstrap.BOOTSTRAP_STATES[:7]
    assert report.events[-1].state == "readiness_probe"
    assert report.events[-1].failure_code == "readiness_failed"
    assert "emit_witness" not in _event_states(report)
    assert "release_to_work" not in _event_states(report)


def test_reports_and_events_are_immutable_snapshots() -> None:
    from canon.bootstrap import run_bootstrap

    report = run_bootstrap(_config(target="chatgpt-app", tier="guided"))

    with pytest.raises(TypeError):
        report.data["adapter_id"] = "mutated"  # type: ignore[index]
    with pytest.raises(TypeError):
        report.events[0].data["state"] = "mutated"  # type: ignore[index]
    with pytest.raises(AttributeError):
        report.events[0].state = "mutated"  # type: ignore[misc]

    as_dict = report.to_dict()
    as_dict["data"]["adapter_id"] = "mutated"  # type: ignore[index]
    as_dict["events"][0]["data"]["state"] = "mutated"  # type: ignore[index]

    assert report.data["adapter_id"] == "chatgpt-app"  # type: ignore[index]
    assert report.events[0].data["state"] == "detect_entry"  # type: ignore[index]


def test_event_constructor_enforces_ok_failure_code_invariant() -> None:
    from canon.bootstrap import BootstrapEvent

    with pytest.raises(TypeError, match="invalid bootstrap event"):
        BootstrapEvent("detect_entry", True, "readiness_failed", "bad")
    with pytest.raises(TypeError, match="invalid bootstrap event"):
        BootstrapEvent("detect_entry", False, "ok", "bad")


def test_report_constructor_enforces_terminal_success_and_failure_invariants() -> None:
    from canon.bootstrap import BOOTSTRAP_STATES, BootstrapEvent, BootstrapReport

    full = tuple(BootstrapEvent(state, True, "ok", state) for state in BOOTSTRAP_STATES)
    failed = (BootstrapEvent("detect_entry", False, "tier_mislabeled", "bad"),)
    mismatch = (BootstrapEvent("detect_entry", False, "tier_mislabeled", "bad"),)

    assert BootstrapReport(True, "ok", "ready", full).exit_code == 0
    assert BootstrapReport(False, "invalid_args", "invalid bootstrap config", ()).exit_code == 2
    assert BootstrapReport(False, "tier_mislabeled", "bad", failed).exit_code == 7

    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(True, "ok", "ready", full[:-1])
    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(True, "readiness_failed", "ready", full)
    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(False, "ok", "bad", failed)
    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(False, "readiness_failed", "bad", mismatch)
    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(False, "readiness_failed", "bad", ())
    with pytest.raises(TypeError, match="invalid bootstrap report"):
        BootstrapReport(False, "invalid_args", "bad", ())


def test_report_constructor_rejects_tampered_event_invariants() -> None:
    from canon.bootstrap import BootstrapEvent, BootstrapReport

    ok_event = BootstrapEvent("detect_entry", True, "ok", "detected")
    object.__setattr__(ok_event, "failure_code", "tier_mislabeled")

    failed_event = BootstrapEvent("detect_entry", False, "tier_mislabeled", "bad")
    object.__setattr__(failed_event, "ok", True)

    with pytest.raises(TypeError, match="invalid bootstrap events"):
        BootstrapReport(False, "tier_mislabeled", "bad", (ok_event,))
    with pytest.raises(TypeError, match="invalid bootstrap events"):
        BootstrapReport(False, "tier_mislabeled", "bad", (failed_event,))


def test_event_serialization_revalidates_state_code_and_data_after_tamper() -> None:
    from canon.bootstrap import BootstrapEvent

    event = BootstrapEvent("detect_entry", True, "ok", "detected", {"safe": True})
    object.__setattr__(event, "state", "not_a_state")
    with pytest.raises(TypeError, match="invalid bootstrap event"):
        event.to_dict()

    event = BootstrapEvent("detect_entry", True, "ok", "detected")
    object.__setattr__(event, "failure_code", "tier_mislabeled")
    with pytest.raises(TypeError, match="invalid bootstrap event"):
        event.to_dict()

    event = BootstrapEvent("detect_entry", True, "ok", "detected")
    object.__setattr__(event, "data", {"bad": object()})
    with pytest.raises(TypeError, match="invalid bootstrap event"):
        event.to_dict()


def test_report_serialization_revalidates_shortened_success_events() -> None:
    report = _success_report()
    object.__setattr__(report, "events", report.events[:-1])

    for serialize in _report_serializers(report):
        with pytest.raises(TypeError, match="invalid bootstrap report"):
            serialize()


def test_report_serialization_revalidates_report_code_ok_and_exit_tamper() -> None:
    for field, value in (("ok", False), ("failure_code", "tier_mislabeled"), ("exit_code", 7)):
        report = _success_report()
        object.__setattr__(report, field, value)

        for serialize in _report_serializers(report):
            with pytest.raises(TypeError, match="invalid bootstrap report"):
                serialize()


def test_report_serialization_revalidates_nested_event_tamper() -> None:
    report = _success_report()
    object.__setattr__(report.events[0], "failure_code", "tier_mislabeled")

    for serialize in _report_serializers(report):
        with pytest.raises(TypeError, match="invalid bootstrap events"):
            serialize()


def test_report_serialization_revalidates_data_tamper_without_repr_leak() -> None:
    class Hostile:
        def __repr__(self) -> str:
            return "leaked-secret-token"

    report = _success_report()
    object.__setattr__(report, "data", {"bad": Hostile()})

    for serialize in _report_serializers(report):
        with pytest.raises(TypeError) as excinfo:
            serialize()
        message = str(excinfo.value)
        assert "invalid bootstrap report" in message
        assert "leaked-secret-token" not in message


def test_event_serialization_rejects_hostile_top_mapping_without_dispatch() -> None:
    from canon.bootstrap import BootstrapEvent

    for hostile in (_HostileMapping, lambda canary: MappingProxyType(_HostileMapping(canary))):
        canary = _Canary()
        event = BootstrapEvent("detect_entry", True, "ok", "detected")
        object.__setattr__(event, "data", hostile(canary))

        _assert_sanitized_type_error(event.to_dict, canary, "invalid bootstrap event")


def test_event_serialization_rejects_hostile_nested_mapping_without_dispatch() -> None:
    from canon.bootstrap import BootstrapEvent

    for hostile in (_HostileMapping, lambda canary: MappingProxyType(_HostileMapping(canary))):
        canary = _Canary()
        event = BootstrapEvent("detect_entry", True, "ok", "detected")
        object.__setattr__(event, "data", {"bad": hostile(canary)})

        _assert_sanitized_type_error(event.to_dict, canary, "invalid bootstrap event")


def test_report_serialization_rejects_hostile_top_mapping_without_dispatch() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for hostile in (_HostileMapping, lambda canary: MappingProxyType(_HostileMapping(canary))):
            canary = _Canary()
            report = _success_report()
            object.__setattr__(report, "data", hostile(canary))

            _assert_sanitized_type_error(getattr(report, serialize_name), canary, "invalid bootstrap report")


def test_report_serialization_rejects_hostile_nested_mapping_without_dispatch() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for hostile in (_HostileMapping, lambda canary: MappingProxyType(_HostileMapping(canary))):
            canary = _Canary()
            report = _success_report()
            object.__setattr__(report, "data", {"bad": hostile(canary)})

            _assert_sanitized_type_error(getattr(report, serialize_name), canary, "invalid bootstrap report")


def test_report_serialization_rejects_hostile_nested_event_data_without_dispatch() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for hostile in (_HostileMapping, lambda canary: MappingProxyType(_HostileMapping(canary))):
            canary = _Canary()
            report = _success_report()
            object.__setattr__(report.events[0], "data", {"bad": hostile(canary)})

            _assert_sanitized_type_error(getattr(report, serialize_name), canary, "invalid bootstrap events")


def test_serialization_rejects_hostile_sequence_subclasses_without_dispatch() -> None:
    from canon.bootstrap import BootstrapEvent

    canary = _Canary()
    event = BootstrapEvent("detect_entry", True, "ok", "detected")
    object.__setattr__(event, "data", {"bad": _HostileList(canary)})
    _assert_sanitized_type_error(event.to_dict, canary, "invalid bootstrap event")

    canary = _Canary()
    report = _success_report()
    object.__setattr__(report, "data", {"bad": _HostileList(canary)})
    _assert_sanitized_type_error(report.to_dict, canary, "invalid bootstrap report")


def test_serialization_preserves_stored_frozen_mapping_and_direct_valid_shapes() -> None:
    from canon.bootstrap import BootstrapEvent

    event = BootstrapEvent("detect_entry", True, "ok", "detected", {"nested": {"ids": ["a", 1, 1.5, None, True]}})
    assert type(event.data) is not MappingProxyType
    assert event.to_dict()["data"] == {"nested": {"ids": ["a", 1, 1.5, None, True]}}

    object.__setattr__(event, "data", {"nested": ("a", {"ok": True})})
    assert event.to_dict()["data"] == {"nested": ["a", {"ok": True}]}

    report = _success_report()
    object.__setattr__(report, "data", {"nested": ("a", {"ok": True})})
    assert report.to_result_data()["nested"] == ["a", {"ok": True}]


def test_bootstrap_snapshot_mapping_is_not_globally_retained() -> None:
    from canon.bootstrap import BootstrapEvent

    event = BootstrapEvent("detect_entry", True, "ok", "detected", {"safe": True})
    snapshot = event.data
    snapshot_ref = weakref.ref(snapshot)  # type: ignore[arg-type]

    object.__setattr__(event, "data", None)
    del snapshot
    gc.collect()

    assert snapshot_ref() is None


def test_serialization_rejects_tampered_private_mapping_internals_sanitized() -> None:
    from canon.bootstrap import BootstrapEvent

    event = BootstrapEvent("detect_entry", True, "ok", "detected", {"safe": True})
    object.__setattr__(event.data, "_items", (("bad", object()),))  # type: ignore[arg-type]

    with pytest.raises(TypeError) as excinfo:
        event.to_dict()
    assert "invalid bootstrap event" in str(excinfo.value)
    assert "object" not in str(excinfo.value)


def test_event_serialization_rejects_uninitialized_or_deleted_private_mapping_sanitized() -> None:
    from canon.bootstrap import BootstrapEvent

    for _, malformed, canary in _malformed_frozen_mapping_cases():
        event = BootstrapEvent("detect_entry", True, "ok", "detected")
        object.__setattr__(event, "data", malformed)

        _assert_sanitized_error(event.to_dict, TypeError, "invalid bootstrap event", canary)


def test_report_serialization_rejects_uninitialized_or_deleted_private_mapping_sanitized() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for _, malformed, canary in _malformed_frozen_mapping_cases():
            report = _success_report()
            object.__setattr__(report, "data", malformed)

            _assert_sanitized_error(getattr(report, serialize_name), TypeError, "invalid bootstrap report", canary)


def test_report_event_serialization_rejects_malformed_nested_private_mapping_sanitized() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for _, malformed, canary in _malformed_frozen_mapping_cases():
            report = _success_report()
            object.__setattr__(report.events[0], "data", malformed)

            _assert_sanitized_error(getattr(report, serialize_name), TypeError, "invalid bootstrap events", canary)


def test_report_data_serialization_rejects_malformed_nested_private_mapping_sanitized() -> None:
    for serialize_name in ("to_dict", "to_result_data"):
        for _, malformed, canary in _malformed_frozen_mapping_cases():
            report = _success_report()
            object.__setattr__(report, "data", {"bad": malformed})

            _assert_sanitized_error(getattr(report, serialize_name), TypeError, "invalid bootstrap report", canary)


def test_event_order_is_always_terminal_prefix() -> None:
    from canon.bootstrap import BOOTSTRAP_STATES, run_bootstrap

    reports = (
        run_bootstrap(_config(target="chatgpt-app", tier="guided")),
        run_bootstrap(_config(target="chatgpt-app", tier="enforced")),
        run_bootstrap(_config(target="unknown-adapter", tier="guided")),
    )

    for report in reports:
        states = _event_states(report)
        assert states == BOOTSTRAP_STATES[: len(states)]
        assert len(states) == len(set(states))
        failures = [event for event in report.events if not event.ok]
        assert len(failures) <= 1
        if failures:
            assert report.events[-1] is failures[0]


def test_bootstrap_performs_no_network_subprocess_or_provider_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    from canon.bootstrap import run_bootstrap

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("Task 5 bootstrap must not perform external work")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)

    report = run_bootstrap(_config(target="chatgpt-app", tier="guided"))

    assert report.ok is True
    assert _event_states(report)[-1] == "release_to_work"
