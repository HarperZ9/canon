from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LockCapability:
    root: Path
    name: str
    lock_name: str
    token: str
    path: Path
    backend: str
    dir_ref: int
    file_ref: int
    file_id: tuple[int, ...]
    owner: object | None = None
    released: bool = False


_REGISTRY: dict[int, LockCapability] = {}


def register(owner: object, capability: LockCapability) -> None:
    capability.owner = owner
    _REGISTRY[id(owner)] = capability


def lookup(owner: object) -> LockCapability | None:
    capability = _REGISTRY.get(id(owner))
    if capability is None or capability.owner is not owner:
        return None
    return capability


def unregister(owner: object) -> None:
    _REGISTRY.pop(id(owner), None)


def metadata_matches(
    capability: LockCapability,
    *,
    root: Path,
    name: str,
    token: str,
    path: Path,
) -> bool:
    return (
        capability.root == root
        and capability.name == name
        and capability.token == token
        and capability.path == path
    )
