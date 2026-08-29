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


# The confirmed instruction surfaces. GEMINI.md and SOUL.md at both scopes are
# further confirmed surfaces whose global-path conventions are not yet pinned;
# they extend this catalog once those conventions are settled.
SURFACE_CATALOG: tuple[Surface, ...] = (
    Surface("claude-code", "global", ROOT_HOME, ".claude/CLAUDE.md"),
    Surface("claude-code", "workspace", ROOT_WORKSPACE, "CLAUDE.md"),
    Surface("codex", "workspace", ROOT_WORKSPACE, "AGENTS.md"),
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


def write_surface(surface: Surface, pool: list[Record], *, home: str,
                  workspace: str, read_text, write_text) -> str:
    """Render `pool` at `surface.scope` into `surface`'s file and write it back,
    only through an allow-listed surface and only when the region changes.

    Guards fail closed before any IO: a surface outside the catalog, or one that
    resolves outside the allow-listed paths, is refused. IO is injected so the
    guard is provable without touching the filesystem.
    """
    if surface not in SURFACE_CATALOG:
        raise SurfaceError(
            f"surface is not in the write allow-list: {surface!r}")
    path = resolve_surface_path(surface, home=home, workspace=workspace)
    assert_writable(path, home=home, workspace=workspace)
    host = read_text(path)
    new = apply_surface(host, pool, surface.scope)
    if new != host:
        write_text(path, new)
    return new
