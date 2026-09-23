"""switch.py -- put the brief where the next agent reads it on its own.

Switching to a target renders that target's workspace instruction file region:
the project's personality blocks (by the authored-split rule the rest of canon
uses) followed by one generated block holding the resume brief. The target
loads its instruction file at startup, so the brief reaches it without a paste.

The write goes through the same allow-list and region rules as every other
canon write: only a catalog surface, only between the canon markers, and only
into a file that already carries a region, or into a file that does not exist
yet when the caller asks for it to be created. A target whose host truncates
the instruction file past a fixed size is refused before writing rather than
cut. IO is injected, so planning reads and commit writes are separate steps.
"""
from __future__ import annotations

from dataclasses import dataclass

from canon.layering import LayeringError
from canon.region import RegionError, extract_region, splice_region
from canon.registry import (
    SURFACE_CATALOG,
    Surface,
    assert_writable,
    pool_for,
    resolve_surface_path,
)
from canon.schema import KIND_PERSONALITY_BLOCK, Provenance, Record
from canon.surface import SurfaceError, render_surface
from canon.textblock import RenderRefused, recompute_source_hash
from canon.workspace.brief import Brief, make_brief, refuse_secrets
from canon.workspace.hosts import new_host_text
from canon.workspace.identity import ProjectIdentity
from canon.workspace.pool import TaggedRecord, block_pool
from canon.workspace.targets import Target

BRIEF_BLOCK_ID = "canon-workspace-brief"
BRIEF_HARNESS = "canon-handoff"


class SwitchRefused(Exception):
    """The switch cannot write this target; `code` is the CLI failure code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class SwitchPlan:
    target: Target
    brief: Brief
    surface: Surface | None
    path: str | None
    status: str
    old_text: str | None
    new_text: str | None
    interior: str | None
    warnings: tuple[str, ...]


def workspace_surface(target: Target) -> Surface | None:
    for surface in SURFACE_CATALOG:
        if surface.harness == target.harness and surface.scope == "workspace":
            return surface
    return None


def brief_record(brief: Brief) -> Record:
    """The brief as a personality block: its heading becomes the block title and
    the rest its body, so the region grammar carries it unchanged."""
    lines = brief.text.rstrip("\n").split("\n")
    title = lines[0].lstrip("#").strip()
    body = "\n".join(lines[2:])
    return Record(kind=KIND_PERSONALITY_BLOCK, id=BRIEF_BLOCK_ID, scope="workspace",
                  data={"title": title, "body": body},
                  provenance=Provenance(harness=BRIEF_HARNESS,
                                        source_hash=recompute_source_hash(title, body)))


def region_interior(pool: list[TaggedRecord], surface: Surface, brief: Brief) -> str:
    blocks = pool_for(surface, block_pool(pool))
    if any(b.id == BRIEF_BLOCK_ID for b in blocks):
        raise SwitchRefused("conflict", f"a stored block already uses the reserved id {BRIEF_BLOCK_ID!r}")
    try:
        return render_surface(blocks + [brief_record(brief)], "workspace")
    except (LayeringError, RenderRefused) as exc:
        raise SwitchRefused("conflict", f"the region cannot be rendered: {exc}") from exc


def _host(path: str, target: Target, read_text, create: bool) -> tuple[str, str]:
    host = read_text(path)
    if host is not None:
        return host, "write"
    if not create:
        raise SwitchRefused("not_found", f"{path} does not exist; pass --create to "
                                         "create it with a canon region")
    return new_host_text(target.name), "create"


def _checked_region(host: str, path: str) -> None:
    try:
        region = extract_region(host)
    except RegionError as exc:
        raise SwitchRefused("conflict", f"{path}: deformed canon region: {exc}") from exc
    if not region.present:
        raise SwitchRefused("conflict", f"{path} has no canon region; add the "
                                        "canon markers to opt this file in")
    if region.scope != "workspace":
        raise SwitchRefused("conflict", f"{path}: region scope is {region.scope!r}, "
                                        "not workspace")


def _limits(target: Target, text: str) -> tuple[str, ...]:
    size = len(text.encode("utf-8"))
    if target.file_bytes_limit is not None and size > target.file_bytes_limit:
        raise SwitchRefused(
            "budget_too_small", f"the file would be {size} bytes; {target.display} "
            f"reads at most {target.file_bytes_limit} and truncates the rest")
    lines = text.count("\n")
    if target.file_lines_advice is not None and lines > target.file_lines_advice:
        return (f"the file is {lines} lines; {target.display} guidance is under "
                f"{target.file_lines_advice}",)
    return ()


def plan_switch(identity: ProjectIdentity, pool: list[TaggedRecord], target: Target, *,
                home: str, read_text, create: bool = False,
                budget_bytes: int | None = None, budget_lines: int | None = None,
                declared: tuple[str, ...] = ()) -> SwitchPlan:
    """Read the target's surface and plan the rewrite. Writes nothing."""
    brief = make_brief(identity, pool, target, budget_bytes=budget_bytes,
                       budget_lines=budget_lines, declared=declared, level=2)
    surface = workspace_surface(target)
    if surface is None:
        return SwitchPlan(target, brief, None, None, "no-surface", None, None, None, ())
    workspace = str(identity.root)
    path = resolve_surface_path(surface, home=home, workspace=workspace)
    try:
        assert_writable(path, home=home, workspace=workspace)
    except SurfaceError as exc:
        raise SwitchRefused("unsafe_path", str(exc)) from exc
    host, status = _host(path, target, read_text, create)
    _checked_region(host, path)
    interior = region_interior(pool, surface, brief)
    refuse_secrets(interior, "instruction region")
    new_text = splice_region(host, interior)
    warnings = _limits(target, new_text)
    if status == "write" and new_text == host:
        status = "unchanged"
    old = None if status == "create" else host
    return SwitchPlan(target, brief, surface, path, status, old, new_text, interior, warnings)


def commit_switch(plan: SwitchPlan, write_text) -> None:
    """Write the planned file when the plan changes it."""
    if plan.status in ("write", "create"):
        write_text(plan.path, plan.new_text)
