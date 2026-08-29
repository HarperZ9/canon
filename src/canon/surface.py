"""surface.py -- R1: render the canonical pool into a managed host file.

apply_surface is the composition R1 adds on top of the R0 legs: it resolves the
pool to the effective block set for a target scope (F0 layering), projects that
mixed-origin set onto the target scope, renders it into a region interior (R0
textblock), and splices it into the host file (R0 region) with every byte
outside the markers preserved.

The projection is the point of "layering at render time": a global block that
survives into the workspace surface is emitted as a workspace-region block, so
the effective set is scope-homogeneous by the time render_region sees it and the
region a harness reads is the resolved view, not the raw per-scope pool.
"""
from __future__ import annotations

from dataclasses import replace

from canon.layering import resolve_blocks
from canon.region import extract_region, splice_region
from canon.schema import Record
from canon.textblock import render_region


class SurfaceError(Exception):
    """The host file cannot receive this render: it carries no canon region
    (off-limits) or its region's declared scope does not match the target
    scope. Refused loudly so a mis-scoped write never reaches the file."""


def render_surface(pool: list[Record], scope: str) -> str:
    """Resolve `pool` for `scope`, project the effective set onto `scope`, and
    render the region interior. The inverse of ingest_region for the resolved
    view."""
    effective = resolve_blocks(pool, scope)
    projected = [replace(rec, scope=scope) for rec in effective]
    return render_region(projected, scope)


def apply_surface(host_text: str, pool: list[Record], scope: str) -> str:
    """Return `host_text` with its canon region rewritten to the resolved view of
    `pool` at `scope`. Every byte outside the markers is preserved.

    Refuses with SurfaceError before writing if the host has no canon region or
    its region's declared scope is not `scope`: a workspace render must never be
    spliced into a region marked global (the blocks would ingest back mis-scoped).
    """
    s = extract_region(host_text)
    if not s.present:
        raise SurfaceError("host file has no canon region (off-limits)")
    if s.scope != scope:
        raise SurfaceError(
            f"region scope {s.scope!r} does not match target scope {scope!r}")
    interior = render_surface(pool, scope)
    return splice_region(host_text, interior)
