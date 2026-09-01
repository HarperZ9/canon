from __future__ import annotations

import builtins
import socket
from pathlib import Path

import pytest


def _config(**overrides: object):
    from canon.bootstrap import BootstrapConfig

    values = {
        "workspace": "C:/work/canon",
        "state_dir": "C:/work/canon/.canon",
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


def _report_serializers(report: object):
    return (report.to_dict, report.to_result_data)  # type: ignore[attr-defined]


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


def test_task5_placeholder_performs_no_io_cache_witness_or_model_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    from canon.bootstrap import run_bootstrap
    from canon.source_state_cache import SourceStateCache

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("Task 5 bootstrap must not perform external work")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    monkeypatch.setattr(Path, "write_text", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(SourceStateCache, "get", forbidden)
    monkeypatch.setattr(SourceStateCache, "put", forbidden)
    monkeypatch.setattr(SourceStateCache, "current", forbidden)

    report = run_bootstrap(_config(target="chatgpt-app", tier="guided"))

    assert report.ok is True
    assert _event_states(report)[-1] == "release_to_work"
