from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .adapter import assert_requested_tier_allowed, descriptor_for
from .bootstrap_validation import (
    BootstrapConfigError,
    require_bool,
    safe_text,
    snapshot_config_values,
    snapshot_data,
    thaw_mapping_or_none,
)
from .exit_codes import exit_code_for

BOOTSTRAP_STATES = (
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

@dataclass(frozen=True, slots=True)
class BootstrapConfig:
    workspace: str
    state_dir: str
    target: str
    tier: str
    profile: str
    offline: bool
    run_id: str
    readiness_response: Mapping[str, object] | None = None

    def __post_init__(self) -> None:
        for name, value in _snapshot_config(self).items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class BootstrapEvent:
    state: str
    ok: bool
    failure_code: str
    message: str
    data: Mapping[str, object] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _require_state(self.state)
        require_bool(self.ok, "event ok")
        safe_text(self.failure_code, "event failure_code")
        safe_text(self.message, "event message")
        _require_event_invariant(self)
        object.__setattr__(self, "data", snapshot_data(self.data))

    def to_dict(self) -> dict[str, object]:
        _require_event_serializable(self)
        return {
            "data": thaw_mapping_or_none(self.data),
            "failure_code": self.failure_code,
            "message": self.message,
            "ok": self.ok,
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class BootstrapReport:
    ok: bool
    failure_code: str
    message: str
    events: tuple[BootstrapEvent, ...]
    data: Mapping[str, object] | None = field(default=None, repr=False)
    exit_code: int = field(init=False)

    def __post_init__(self) -> None:
        require_bool(self.ok, "report ok")
        safe_text(self.failure_code, "report failure_code")
        safe_text(self.message, "report message")
        _require_events(self.events)
        _require_report_invariant(self)
        object.__setattr__(self, "data", snapshot_data(self.data))
        object.__setattr__(self, "exit_code", exit_code_for(self.failure_code))

    def to_dict(self) -> dict[str, object]:
        _require_report_serializable(self)
        return {
            "data": thaw_mapping_or_none(self.data),
            "events": [event.to_dict() for event in self.events],
            "exit_code": self.exit_code,
            "failure_code": self.failure_code,
            "message": self.message,
            "ok": self.ok,
        }

    def to_result_data(self) -> dict[str, object]:
        _require_report_serializable(self)
        data = thaw_mapping_or_none(self.data) or {}
        data["events"] = [event.to_dict() for event in self.events]
        return data


def run_bootstrap(config: BootstrapConfig) -> BootstrapReport:
    try:
        snapshot = _snapshot_config(config)
    except BootstrapConfigError:
        return _report(False, "invalid_args", "invalid bootstrap config", (), None)

    events: list[BootstrapEvent] = []
    try:
        descriptor = descriptor_for(snapshot["target"])
    except KeyError:
        return _terminal(events, "detect_entry", "invalid_args", "unsupported bootstrap target", {"reason": "unsupported_target"})

    base = _adapter_data(descriptor.adapter_id, descriptor.integration_tier, snapshot)
    if descriptor.integration_tier == "unsupported":
        return _terminal(events, "detect_entry", "unsupported_lifecycle", "unsupported bootstrap lifecycle", base)
    try:
        assert_requested_tier_allowed(descriptor, snapshot["tier"])
    except ValueError:
        return _terminal(events, "detect_entry", "tier_mislabeled", "requested tier exceeds adapter descriptor", base)

    events.append(_event("detect_entry", "detected entry", base))
    for state in BOOTSTRAP_STATES[1:]:
        if state == "readiness_probe" and snapshot["tier"] == "enforced":
            return _terminal(events, state, "readiness_failed", "readiness probe failed", base)
        events.append(_event(state, _state_message(state), _state_data(state, snapshot)))
    return _report(True, "ok", "release to work", tuple(events), base)


def _snapshot_config(config: BootstrapConfig) -> dict[str, object]:
    if type(config) is not BootstrapConfig:
        raise BootstrapConfigError("invalid bootstrap config")
    return snapshot_config_values(
        workspace=config.workspace,
        state_dir=config.state_dir,
        target=config.target,
        tier=config.tier,
        profile=config.profile,
        offline=config.offline,
        run_id=config.run_id,
        readiness_response=config.readiness_response,
    )


def _terminal(
    events: list[BootstrapEvent],
    state: str,
    failure_code: str,
    message: str,
    data: dict[str, object] | None,
) -> BootstrapReport:
    event_data = {"state": state}
    if data is not None:
        event_data.update(data)
    events.append(BootstrapEvent(state, False, failure_code, message, event_data))
    return _report(False, failure_code, message, tuple(events), data)


def _event(state: str, message: str, data: dict[str, object] | None = None) -> BootstrapEvent:
    event_data = {"state": state}
    if data is not None:
        event_data.update(data)
    return BootstrapEvent(state, True, "ok", message, event_data)


def _report(
    ok: bool,
    failure_code: str,
    message: str,
    events: tuple[BootstrapEvent, ...],
    data: dict[str, object] | None,
) -> BootstrapReport:
    return BootstrapReport(ok, failure_code, message, events, data)


def _adapter_data(adapter_id: str, authoritative_tier: str, config: dict[str, object]) -> dict[str, object]:
    return {
        "adapter_id": adapter_id,
        "authoritative_tier": authoritative_tier,
        "offline": config["offline"],
        "profile": config["profile"],
        "requested_tier": config["tier"],
        "run_id": config["run_id"],
    }


def _state_data(state: str, config: dict[str, object]) -> dict[str, object]:
    if state == "readiness_probe":
        response = "provided" if config["readiness_response"] is not None else "absent"
        return {"readiness_response": response}
    return {"deferred": True}


def _state_message(state: str) -> str:
    return state.replace("_", " ")


def _require_events(events: object) -> None:
    if type(events) is not tuple:
        raise TypeError("invalid bootstrap events")
    states = tuple(event.state for event in events if type(event) is BootstrapEvent)
    if len(states) != len(events) or states != BOOTSTRAP_STATES[: len(states)]:
        raise TypeError("invalid bootstrap events")
    for event in events:
        try:
            _require_event_invariant(event)
        except TypeError:
            raise TypeError("invalid bootstrap events") from None
    failures = [event for event in events if not event.ok]
    if len(failures) > 1 or (failures and events[-1] is not failures[0]):
        raise TypeError("invalid bootstrap events")


def _require_state(state: object) -> None:
    if type(state) is not str or state not in BOOTSTRAP_STATES:
        raise TypeError("invalid bootstrap state")


def _require_event_serializable(event: BootstrapEvent) -> None:
    try:
        _require_state(event.state)
        require_bool(event.ok, "event ok")
        safe_text(event.failure_code, "event failure_code")
        safe_text(event.message, "event message")
        _require_event_invariant(event)
        _require_serializable_data(event.data, "invalid bootstrap event")
    except TypeError:
        raise TypeError("invalid bootstrap event") from None


def _require_report_serializable(report: BootstrapReport) -> None:
    try:
        require_bool(report.ok, "report ok")
        safe_text(report.failure_code, "report failure_code")
        safe_text(report.message, "report message")
    except TypeError:
        raise TypeError("invalid bootstrap report") from None
    try:
        _require_events(report.events)
        for event in report.events:
            _require_event_serializable(event)
    except TypeError:
        raise TypeError("invalid bootstrap events") from None
    try:
        _require_report_invariant(report)
        _require_report_exit_code(report)
        _require_serializable_data(report.data, "invalid bootstrap report")
    except TypeError:
        raise TypeError("invalid bootstrap report") from None


def _require_event_invariant(event: BootstrapEvent) -> None:
    if event.ok != (event.failure_code == "ok"):
        raise TypeError("invalid bootstrap event")


def _require_report_invariant(report: BootstrapReport) -> None:
    exit_code = exit_code_for(report.failure_code)
    if report.ok:
        if report.failure_code != "ok" or exit_code != 0:
            raise TypeError("invalid bootstrap report")
        if _event_states(report.events) != BOOTSTRAP_STATES or any(not event.ok for event in report.events):
            raise TypeError("invalid bootstrap report")
        return
    if report.failure_code == "ok" or exit_code == 0:
        raise TypeError("invalid bootstrap report")
    if not report.events:
        if report.failure_code != "invalid_args" or report.message != "invalid bootstrap config":
            raise TypeError("invalid bootstrap report")
        return
    terminal = report.events[-1]
    if terminal.ok or terminal.failure_code != report.failure_code:
        raise TypeError("invalid bootstrap report")


def _require_report_exit_code(report: BootstrapReport) -> None:
    expected = exit_code_for(report.failure_code)
    if type(report.exit_code) is not int or isinstance(report.exit_code, bool) or report.exit_code != expected:
        raise TypeError("invalid bootstrap report")


def _require_serializable_data(data: Mapping[str, object] | None, message: str) -> None:
    try:
        snapshot_data(thaw_mapping_or_none(data))
    except TypeError:
        raise TypeError(message) from None


def _event_states(events: tuple[BootstrapEvent, ...]) -> tuple[str, ...]:
    return tuple(event.state for event in events)


__all__ = ["BOOTSTRAP_STATES", "BootstrapConfig", "BootstrapConfigError", "BootstrapEvent", "BootstrapReport", "run_bootstrap"]
