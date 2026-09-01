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


def test_malformed_config_fails_before_events_without_hostile_repr() -> None:
    from canon.bootstrap import BootstrapConfig, run_bootstrap
    from canon.exit_codes import EX_USAGE

    hostile = run_bootstrap(
        BootstrapConfig(
            workspace="C:/work/canon",
            state_dir="C:/work/canon/.canon",
            target="codex-cli",
            tier="native-advisory",
            profile="handoff",
            offline=False,
            run_id=_HostileStr("run-1"),
        )
    )
    nested = run_bootstrap(_config(readiness_response={"ids": [object()]}))

    for report in (hostile, nested):
        assert report.ok is False
        assert report.failure_code == "invalid_args"
        assert report.exit_code == EX_USAGE
        assert report.events == ()
        assert "leaked-secret-token" not in report.message


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
