from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .bootstrap_runtime_inputs import source_item_dict
from .canonical_json import is_sha256_ref, sha256_text
from .capsule import Capsule, CapsuleBundle, validate_capsule
from .readiness import ReadinessProbe, validate_readiness_probe
from .source_state_cache import SourceStateCache, SourceStateCacheError

BOOTSTRAP_CACHE_SCHEMA = "canon.bootstrap-cache-entry/v1"


@dataclass(frozen=True, slots=True)
class BootstrapCacheResult:
    cache_status: str
    cache_key: str
    capsule: Capsule
    readiness_probe: ReadinessProbe
    manifest_sha256: str
    canon_md_sha256: str
    does_not_prove: tuple[str, ...]


def select_cache(context: object, make_entry: Callable[[object], dict[str, object]]) -> BootstrapCacheResult:
    cache = SourceStateCache(context.state_dir / "cache")  # type: ignore[attr-defined]
    current = cache.current()
    if current is not None and current.get("cache_key") == context.cache_key:  # type: ignore[attr-defined]
        return _cache_result(_validate_entry(current, context), "hit")
    existing = cache.get(context.cache_key)  # type: ignore[attr-defined]
    if existing is not None:
        return _cache_result(_validate_entry(existing, context), "hit")
    entry = make_entry(context)
    cache.put(context.cache_key, entry)  # type: ignore[attr-defined]
    return _cache_result(_validate_entry(entry, context), "miss")


def cache_entry_from_bundle(context: object, bundle: CapsuleBundle) -> dict[str, object]:
    entry = {
        "budget_key": context.budget_key, "cache_key": context.cache_key,  # type: ignore[attr-defined]
        "canon_md_sha256": sha256_text(bundle.canon_md), "capsule": bundle.capsule.to_dict(),
        "compiler_key": context.compiler_key, "does_not_prove": list(bundle.capsule.does_not_prove),  # type: ignore[attr-defined]
        "manifest_sha256": bundle.capsule.integrity.manifest_sha256,
        "readiness_probe": bundle.readiness_probe.to_dict(), "schema": BOOTSTRAP_CACHE_SCHEMA,
        "source_inputs": [source_item_dict(item) for item in context.source_items],  # type: ignore[attr-defined]
        "source_state": context.source_state.to_dict(), "target": context.target.to_dict(),  # type: ignore[attr-defined]
    }
    return _validate_entry(entry, context)


def cache_failure(exc: SourceStateCacheError) -> str:
    return "conflict" if exc.code == "semantic-cache-mismatch" else "io_error"


def _validate_entry(entry: dict[str, object], context: object) -> dict[str, object]:
    try:
        _validate_entry_fields(entry, context)
        capsule = Capsule.from_dict(entry["capsule"])  # type: ignore[arg-type]
        probe = ReadinessProbe.from_dict(entry["readiness_probe"])  # type: ignore[arg-type]
    except (KeyError, TypeError, ValueError) as exc:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt") from exc
    if validate_capsule(capsule) or validate_readiness_probe(probe):
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    if capsule.capsule_id != entry["manifest_sha256"] or probe.capsule_id != capsule.capsule_id:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    if capsule.source_state.to_dict() != context.source_state.to_dict():  # type: ignore[attr-defined]
        raise SourceStateCacheError("semantic-cache-mismatch", "cache entry does not match request")
    if capsule.target.to_dict() != context.target.to_dict():  # type: ignore[attr-defined]
        raise SourceStateCacheError("semantic-cache-mismatch", "cache entry does not match request")
    return entry


def _validate_entry_fields(entry: dict[str, object], context: object) -> None:
    expected = {"schema", "cache_key", "compiler_key", "budget_key", "source_state",
                "source_inputs", "target", "capsule", "canon_md_sha256",
                "manifest_sha256", "readiness_probe", "does_not_prove"}
    if set(entry) != expected or entry["schema"] != BOOTSTRAP_CACHE_SCHEMA:
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")
    if entry["cache_key"] != context.cache_key or entry["compiler_key"] != context.compiler_key:  # type: ignore[attr-defined]
        raise SourceStateCacheError("semantic-cache-mismatch", "cache entry does not match request")
    if entry["budget_key"] != context.budget_key or entry["source_state"] != context.source_state.to_dict():  # type: ignore[attr-defined]
        raise SourceStateCacheError("semantic-cache-mismatch", "cache entry does not match request")
    expected_inputs = [source_item_dict(item) for item in context.source_items]  # type: ignore[attr-defined]
    if entry["source_inputs"] != expected_inputs or entry["target"] != context.target.to_dict():  # type: ignore[attr-defined]
        raise SourceStateCacheError("semantic-cache-mismatch", "cache entry does not match request")
    if not is_sha256_ref(entry["canon_md_sha256"]) or not is_sha256_ref(entry["manifest_sha256"]):
        raise SourceStateCacheError("corrupt-cache-entry", "cache entry is corrupt")


def _cache_result(entry: dict[str, object], status: str) -> BootstrapCacheResult:
    return BootstrapCacheResult(
        status, entry["cache_key"], Capsule.from_dict(entry["capsule"]),
        ReadinessProbe.from_dict(entry["readiness_probe"]), entry["manifest_sha256"],
        entry["canon_md_sha256"], tuple(entry["does_not_prove"]),  # type: ignore[arg-type]
    )


__all__ = ["BOOTSTRAP_CACHE_SCHEMA", "BootstrapCacheResult", "cache_entry_from_bundle", "cache_failure", "select_cache"]
