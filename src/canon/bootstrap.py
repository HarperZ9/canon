from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .adapter import INTEGRATION_TIERS, assert_requested_tier_allowed, descriptor_for
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

_ADAPTER_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class BootstrapConfigError(ValueError): pass


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


@dataclass(frozen=True, slots=True)
class BootstrapEvent:
    state: str
    ok: bool
    failure_code: str
    message: str
    data: Mapping[str, object] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        _require_state(self.state)
        _require_bool(self.ok, "event ok")
        _safe_text(self.failure_code, "event failure_code")
        _safe_text(self.message, "event message")
        object.__setattr__(self, "data", _snapshot_mapping_or_none(self.data))

    def to_dict(self) -> dict[str, object]:
        return {
            "data": _thaw_mapping_or_none(self.data),
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
        _require_bool(self.ok, "report ok")
        _safe_text(self.failure_code, "report failure_code")
        _safe_text(self.message, "report message")
        _require_events(self.events)
        object.__setattr__(self, "data", _snapshot_mapping_or_none(self.data))
        object.__setattr__(self, "exit_code", exit_code_for(self.failure_code))

    def to_dict(self) -> dict[str, object]:
        return {
            "data": _thaw_mapping_or_none(self.data),
            "events": [event.to_dict() for event in self.events],
            "exit_code": self.exit_code,
            "failure_code": self.failure_code,
            "message": self.message,
            "ok": self.ok,
        }

    def to_result_data(self) -> dict[str, object]:
        data = _thaw_mapping_or_none(self.data) or {}
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
    return {
        "workspace": _path_text(config.workspace),
        "state_dir": _path_text(config.state_dir),
        "target": _adapter_id(config.target),
        "tier": _tier(config.tier),
        "profile": _token(config.profile, "profile"),
        "offline": _exact_bool(config.offline),
        "run_id": _token(config.run_id, "run_id"),
        "readiness_response": _snapshot_response(config.readiness_response),
    }


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
    failures = [event for event in events if not event.ok]
    if len(failures) > 1 or (failures and events[-1] is not failures[0]):
        raise TypeError("invalid bootstrap events")


def _require_state(state: object) -> None:
    if type(state) is not str or state not in BOOTSTRAP_STATES:
        raise TypeError("invalid bootstrap state")

def _snapshot_mapping_or_none(data: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if data is None:
        return None
    if type(data) is not dict:
        raise TypeError("invalid bootstrap data")
    return _snapshot_mapping(data)

def _snapshot_mapping(data: dict[str, object]) -> Mapping[str, object]:
    return MappingProxyType({_safe_text(key, "data key"): _snapshot_value(value) for key, value in data.items()})

def _snapshot_value(value: object) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is dict:
        return _snapshot_mapping(value)
    if type(value) in (list, tuple):
        return tuple(_snapshot_value(item) for item in value)
    raise TypeError("invalid bootstrap data")

def _thaw_mapping_or_none(data: Mapping[str, object] | None) -> dict[str, object] | None:
    if data is None:
        return None
    return {key: _thaw_value(value) for key, value in data.items()}

def _thaw_value(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_value(item) for key, item in value.items()}
    if type(value) in (list, tuple):
        return [_thaw_value(item) for item in value]
    return value

def _path_text(value: object) -> str:
    if type(value) is not str or value == "" or _has_control(value):
        raise BootstrapConfigError("invalid bootstrap config")
    return value

def _adapter_id(value: object) -> str:
    if type(value) is not str or _ADAPTER_ID_RE.fullmatch(value) is None:
        raise BootstrapConfigError("invalid bootstrap config")
    return value

def _tier(value: object) -> str:
    if type(value) is not str or value not in INTEGRATION_TIERS:
        raise BootstrapConfigError("invalid bootstrap config")
    return value

def _token(value: object, name: str) -> str:
    if type(value) is not str or _TOKEN_RE.fullmatch(value) is None:
        raise BootstrapConfigError(f"invalid bootstrap {name}")
    return value

def _exact_bool(value: object) -> bool:
    if type(value) is not bool:
        raise BootstrapConfigError("invalid bootstrap config")
    return value

def _snapshot_response(value: object) -> object:
    if value is None:
        return None
    if type(value) is not dict:
        raise BootstrapConfigError("invalid bootstrap config")
    try:
        return _snapshot_mapping(value)
    except TypeError as exc:
        raise BootstrapConfigError("invalid bootstrap config") from exc

def _require_bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"invalid bootstrap {name}")

def _safe_text(value: object, name: str) -> str:
    if type(value) is not str or value == "" or _has_control(value):
        raise TypeError(f"invalid bootstrap {name}")
    return value

def _has_control(value: str) -> bool:
    return "\0" in value or any(ord(char) < 32 or ord(char) == 127 for char in value)


__all__ = ["BOOTSTRAP_STATES", "BootstrapConfig", "BootstrapEvent", "BootstrapReport", "run_bootstrap"]
