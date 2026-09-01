from __future__ import annotations

import math
import re
from collections.abc import Mapping
from types import MappingProxyType

from .adapter import INTEGRATION_TIERS

_ADAPTER_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SNAPSHOT_PROXIES: list[Mapping[str, object]] = []


class BootstrapConfigError(ValueError):
    pass


def snapshot_config_values(
    *,
    workspace: object,
    state_dir: object,
    target: object,
    tier: object,
    profile: object,
    offline: object,
    run_id: object,
    readiness_response: object,
) -> dict[str, object]:
    return {
        "workspace": _path_text(workspace),
        "state_dir": _path_text(state_dir),
        "target": _adapter_id(target),
        "tier": _tier(tier),
        "profile": _token(profile, "profile"),
        "offline": _exact_bool(offline),
        "run_id": _token(run_id, "run_id"),
        "readiness_response": snapshot_response(readiness_response),
    }


def snapshot_data(data: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if data is None:
        return None
    if type(data) is not dict:
        raise TypeError("invalid bootstrap data")
    return _snapshot_mapping(data, TypeError)


def snapshot_response(value: object) -> object:
    if value is None:
        return None
    if type(value) not in (dict, MappingProxyType):
        raise BootstrapConfigError("invalid bootstrap config")
    try:
        return _snapshot_mapping(value, BootstrapConfigError)
    except TypeError as exc:
        raise BootstrapConfigError("invalid bootstrap config") from exc


def thaw_mapping_or_none(data: Mapping[str, object] | None) -> dict[str, object] | None:
    require_serializable_data(data, "invalid bootstrap data")
    if data is None:
        return None
    return _thaw_mapping(data)


def require_serializable_data(data: object, message: str) -> None:
    try:
        _require_serializable_data_shape(data)
    except TypeError:
        raise TypeError(message) from None


def require_bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise TypeError(f"invalid bootstrap {name}")


def safe_text(value: object, name: str) -> str:
    if type(value) is not str or value == "" or _has_control(value):
        raise TypeError(f"invalid bootstrap {name}")
    return value


def _snapshot_mapping(data: Mapping[object, object], error: type[Exception]) -> Mapping[str, object]:
    items: dict[str, object] = {}
    for key, value in data.items():
        items[_safe_key(key, error)] = _snapshot_value(value, error)
    proxy = MappingProxyType(items)
    _SNAPSHOT_PROXIES.append(proxy)
    return proxy


def _snapshot_value(value: object, error: type[Exception]) -> object:
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) in (dict, MappingProxyType):
        return _snapshot_mapping(value, error)
    if type(value) in (list, tuple):
        return tuple(_snapshot_value(item, error) for item in tuple(value))
    raise error("invalid bootstrap config" if error is BootstrapConfigError else "invalid bootstrap data")


def _thaw_value(value: object) -> object:
    if type(value) is dict or _is_snapshot_proxy(value):
        return _thaw_mapping(value)
    if type(value) in (list, tuple):
        return [_thaw_value(item) for item in value]
    return value


def _thaw_mapping(data: object) -> dict[str, object]:
    return {key: _thaw_value(item) for key, item in data.items()}  # type: ignore[attr-defined]


def _require_serializable_data_shape(data: object) -> None:
    if data is None:
        return
    _require_serializable_mapping(data)


def _require_serializable_mapping(data: object) -> None:
    if type(data) is not dict and not _is_snapshot_proxy(data):
        raise TypeError("invalid bootstrap data")
    for key, value in data.items():  # type: ignore[attr-defined]
        _safe_key(key, TypeError)
        _require_serializable_value(value)


def _require_serializable_value(value: object) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is dict or _is_snapshot_proxy(value):
        _require_serializable_mapping(value)
        return
    if type(value) in (list, tuple):
        for item in value:
            _require_serializable_value(item)
        return
    raise TypeError("invalid bootstrap data")


def _is_snapshot_proxy(value: object) -> bool:
    return type(value) is MappingProxyType and any(value is proxy for proxy in _SNAPSHOT_PROXIES)


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


def _safe_key(value: object, error: type[Exception]) -> str:
    if type(value) is not str or value == "" or _has_control(value):
        raise error("invalid bootstrap config" if error is BootstrapConfigError else "invalid bootstrap data")
    return value


def _has_control(value: str) -> bool:
    return "\0" in value or any(ord(char) < 32 or ord(char) == 127 for char in value)
