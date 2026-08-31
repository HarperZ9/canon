"""registry.py -- R1: the write-surface allow-list.

The renderer may rewrite ONLY the managed instruction files named in the fixed
catalog below. Each Surface names a harness, a scope, the root it lives under
(the home directory or the workspace root), and its path relative to that root.

The absolute roots are injected at call time and never stored here, so this
public catalog carries no operator path: only the generic filename conventions
(`.claude/CLAUDE.md`, `CLAUDE.md`, `AGENTS.md`) live in source. A write is
allowed only if its resolved path is exactly one of the catalog surfaces under
the injected roots; anything else -- a secret file, a traversal escape, an
ad-hoc surface -- is refused before a byte is read or written.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from canon.path_policy import PathPolicyError, assert_operational_surface_path
from canon.region import extract_region
from canon.schema import Record
from canon.surface import SurfaceError, apply_surface

ROOT_HOME = "home"
ROOT_WORKSPACE = "workspace"


@dataclass(frozen=True, slots=True)
class Surface:
    """One managed file canon is allowed to rewrite: (harness, scope) bound to a
    root-kind and a path relative to that root. Path-free of any absolute root."""

    harness: str
    scope: str
    root: str
    relative_path: str


# The confirmed instruction surfaces. SOUL.md (harness "hermes") is a lone
# workspace surface: no global sibling, so it renders the full merged set like
# AGENTS.md, and it reuses the R0 block-region grammar with no banner. GEMINI.md
# at both scopes and the GLOBAL SOUL.md are further confirmed surfaces whose
# global-path conventions are not yet pinned; they extend this catalog once those
# conventions are settled. The vault is not listed here: it is a whole-directory
# mirror with its own containment (vault_mirror.is_vault_write_allowed), not a
# single-file region-splice surface, so it is deliberately not a root-kind (D-35).
SURFACE_CATALOG: tuple[Surface, ...] = (
    Surface("claude-code", "global", ROOT_HOME, ".claude/CLAUDE.md"),
    Surface("claude-code", "workspace", ROOT_WORKSPACE, "CLAUDE.md"),
    Surface("codex", "workspace", ROOT_WORKSPACE, "AGENTS.md"),
    Surface("hermes", "workspace", ROOT_WORKSPACE, "SOUL.md"),
)


def _root_dir(surface: Surface, *, home: str, workspace: str) -> str:
    return home if surface.root == ROOT_HOME else workspace


def resolve_surface_path(surface: Surface, *, home: str, workspace: str) -> str:
    """Join `surface` onto its injected root, normalized for the platform."""
    root = _root_dir(surface, home=home, workspace=workspace)
    return os.path.normpath(os.path.join(root, surface.relative_path))


def allowed_paths(*, home: str, workspace: str) -> set[str]:
    """Every catalog surface resolved under the injected roots."""
    return {resolve_surface_path(s, home=home, workspace=workspace)
            for s in SURFACE_CATALOG}


def is_write_allowed(path: str, *, home: str, workspace: str) -> bool:
    """True only if `path` normalizes to exactly one allow-listed surface. A
    case-insensitive filesystem folds case; a traversal escape collapses under
    normpath and simply fails to match."""
    target = os.path.normcase(os.path.normpath(path))
    allowed = {os.path.normcase(p)
               for p in allowed_paths(home=home, workspace=workspace)}
    return target in allowed


def assert_writable(path: str, *, home: str, workspace: str) -> None:
    """Raise SurfaceError unless `path` is an allow-listed surface."""
    if not is_write_allowed(path, home=home, workspace=workspace):
        raise SurfaceError(
            f"path is not an allow-listed canon surface: {path!r}")


def _checked_surface_path(surface: Surface, *, home: str, workspace: str) -> str:
    if surface not in SURFACE_CATALOG:
        raise SurfaceError(
            f"surface is not in the write allow-list: {surface!r}")
    root = _root_dir(surface, home=home, workspace=workspace)
    path = resolve_surface_path(surface, home=home, workspace=workspace)
    assert_writable(path, home=home, workspace=workspace)
    if not os.path.lexists(root):
        return path
    try:
        return str(assert_operational_surface_path(path, root=root))
    except PathPolicyError as exc:
        raise SurfaceError(str(exc)) from exc


def write_surface(surface: Surface, pool: list[Record], *, home: str,
                  workspace: str, read_text, write_text) -> str:
    """Render `pool` at `surface.scope` into `surface`'s file and write it back,
    only through an allow-listed surface and only when the region changes.

    Guards fail closed before any IO: a surface outside the catalog, or one that
    resolves outside the allow-listed paths, is refused. IO is injected so the
    guard is provable without touching the filesystem.
    """
    path = _checked_surface_path(surface, home=home, workspace=workspace)
    host = read_text(path)
    new = apply_surface(host, pool, surface.scope)
    if new != host:
        path = _checked_surface_path(surface, home=home, workspace=workspace)
        write_text(path, new)
    return new


@dataclass(frozen=True, slots=True)
class SurfaceResult:
    """The outcome of rendering one surface: written, unchanged, or off-limits
    (the host had no canon region and was left untouched)."""

    surface: Surface
    path: str
    status: str
    content: str | None


def _has_global_surface(harness: str) -> bool:
    return any(s.harness == harness and s.scope == "global"
               for s in SURFACE_CATALOG)


def pool_for(surface: Surface, pool: list[Record]) -> list[Record]:
    """The block subset a surface renders under the authored-split rule.

    A global surface renders the pool (layering resolves it to the globals). A
    workspace surface renders only the workspace-authored blocks when the same
    harness also owns a global surface -- the globals live in that sibling file,
    so folding them in here would duplicate them where a harness reads both. A
    workspace surface with no global sibling renders the full merged set, so its
    lone file stays self-sufficient.

    Public so the R1 writer and the V2 verifier resolve one authored-split: the
    drift check and the writing gate render exactly what write_surfaces writes.
    """
    if surface.scope == "global":
        return pool
    if _has_global_surface(surface.harness):
        return [r for r in pool if r.scope == "workspace"]
    return pool


def write_surfaces(pool: list[Record], *, home: str, workspace: str,
                   read_text, write_text,
                   surfaces: tuple[Surface, ...] | None = None
                   ) -> list[SurfaceResult]:
    """Render every surface in `surfaces` (default: the whole catalog) from one
    pool, each by the authored-split rule. A host with no canon region is
    skipped and reported off-limits, never mutated; a surface whose region is
    present but mis-scoped fails closed through apply_surface. Only a changed
    region is written back.

    The batch is all-or-nothing. Every surface is planned first -- static guards
    (catalog membership, allow-listed path) and every per-host refusal
    (off-limits skip, mis-scope raise) resolve in this pass, before a single
    write. Only once the whole set plans clean are the changed regions committed,
    so a later surface's refusal never leaves an earlier one half-written. This
    covers canon's own refusals; a filesystem fault inside the commit pass (a
    write_text that fails after earlier files wrote) is not rolled back.
    """
    chosen = SURFACE_CATALOG if surfaces is None else surfaces
    planned: list[tuple[Surface, str]] = []
    results: list[SurfaceResult] = []
    for surface in chosen:
        path = _checked_surface_path(surface, home=home, workspace=workspace)
        host = read_text(path)
        if not extract_region(host).present:
            results.append(SurfaceResult(surface, path, "off-limits", None))
            continue
        new = apply_surface(host, pool_for(surface, pool), surface.scope)
        if new != host:
            planned.append((surface, new))
            results.append(SurfaceResult(surface, path, "written", new))
        else:
            results.append(SurfaceResult(surface, path, "unchanged", new))
    for surface, _content in planned:
        _checked_surface_path(surface, home=home, workspace=workspace)
    for surface, content in planned:
        path = _checked_surface_path(surface, home=home, workspace=workspace)
        write_text(path, content)
    return results
