"""`canon handoff` and `canon switch`: the brief for the next agent, and the
brief placed in that agent's own instruction file.

`handoff` prints the brief (or writes it to a new file) and can write the
receipt beside it. `switch` renders the target's workspace instruction region
with the brief inside, through the allow-list, and writes it unless
`--dry-run` is given. Both read only this project's pool plus any project named
with `--include-project`.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from pathlib import Path
from typing import TextIO

from .cli_workspace_common import (
    CommandFailure,
    Output,
    WorkspaceContext,
    build_context,
    emit,
    guarded,
)
from .workspace.backflow import pending_edits
from .workspace.brief import BudgetError, SecretInRender, make_brief
from .workspace.ledger import record_render
from .workspace.pool import project_pool
from .workspace.switch import SwitchRefused, commit_switch, plan_switch
from .workspace.targets import UnknownTarget, target_for


def run_handoff_command(parsed: argparse.Namespace, *, stdout: TextIO, stderr: TextIO,
                        environ: Mapping[str, str], color: bool) -> int:
    out = Output(stdout, stderr, parsed.json_output, color)
    handler = _handoff if parsed.command == "handoff" else _switch

    def action() -> int:
        try:
            ctx = build_context(parsed, environ, out)
            return handler(parsed, ctx, out, environ)
        except UnknownTarget as exc:
            raise CommandFailure("invalid_args", str(exc)) from exc
        except BudgetError as exc:
            raise CommandFailure("budget_too_small", str(exc)) from exc
        except SwitchRefused as exc:
            raise CommandFailure(exc.code, str(exc)) from exc
        except SecretInRender as exc:
            raise CommandFailure("secret_quarantine", str(exc)) from exc

    return guarded(parsed.command, out, action)


def _write_new(path: str, text: str) -> None:
    """Write a file that must not exist yet, so a brief never clobbers a file."""
    try:
        with open(path, "x", encoding="utf-8", newline="") as handle:
            handle.write(text)
    except FileExistsError as exc:
        raise CommandFailure("conflict", f"{path} already exists; not overwritten") from exc


def _pool(parsed, ctx: WorkspaceContext):
    declared = tuple(parsed.include_project)
    return project_pool(ctx.store, include_projects=declared), declared


def _handoff(parsed, ctx: WorkspaceContext, out: Output, environ) -> int:
    target = target_for(parsed.to)
    pool, declared = _pool(parsed, ctx)
    brief = make_brief(ctx.identity, pool, target, budget_bytes=parsed.budget_bytes,
                       budget_lines=parsed.budget_lines, declared=declared)
    receipt_text = json.dumps(brief.receipt, sort_keys=True, indent=2) + "\n"
    if parsed.receipt:
        _write_new(parsed.receipt, receipt_text)
    data = {"brief": brief.text, "receipt": brief.receipt}
    message = f"brief for {target.name}: {len(brief.included)} records, " \
              f"{len(brief.left_out)} left out"
    if parsed.out:
        _write_new(parsed.out, brief.text)
        return emit(out, command="handoff", message=message, data=data,
                    text=f"{message}; wrote {parsed.out}")
    return emit(out, command="handoff", message=message, data=data, text=brief.text)


def _read_text(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8", newline="") as handle:
        return handle.read()


def _write_text(path: str, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


_DONE = {"write": "wrote", "create": "created", "unchanged": "unchanged"}
_WOULD = {"write": "would write", "create": "would create", "unchanged": "unchanged"}


def _status_words(status: str, dry_run: bool, rel: str | None) -> str:
    if rel is None:
        return "no instruction file for this target; the brief follows"
    return f"{(_WOULD if dry_run else _DONE)[status]} {rel}"


def _refuse_pending_edits(ctx: WorkspaceContext, plan, dry_run: bool) -> None:
    """Edits made inside the region since canon last wrote it become proposals,
    and the switch stops until each one is accepted or rejected."""
    report = pending_edits(ctx.store, plan, dry_run=dry_run)
    if report is None or not report["proposed"]:
        return
    rel = plan.surface.relative_path
    ids = ", ".join(p["id"] for p in report["proposed"])
    verb = "would become" if dry_run else "are now"
    raise CommandFailure(
        "edits_pending", f"{len(report['proposed'])} edits made inside the canon region "
        f"of {rel} {verb} proposals ({ids}); accept or reject each with "
        "canon workspace accept|reject, then switch again")


def _switch(parsed, ctx: WorkspaceContext, out: Output, environ) -> int:
    target = target_for(parsed.to)
    pool, declared = _pool(parsed, ctx)
    home = parsed.home or str(Path.home())
    plan = plan_switch(ctx.identity, pool, target, home=home, read_text=_read_text,
                       create=parsed.create, budget_bytes=parsed.budget_bytes,
                       budget_lines=parsed.budget_lines, declared=declared)
    _refuse_pending_edits(ctx, plan, parsed.dry_run)
    if not parsed.dry_run:
        commit_switch(plan, _write_text, _read_text)
        if plan.surface is not None:
            record_render(ctx.store, plan.surface.relative_path, target.name, plan.interior)
    rel = plan.surface.relative_path if plan.surface else None
    lines = [f"{target.display}: {_status_words(plan.status, parsed.dry_run, rel)}",
             f"brief: {len(plan.brief.included)} records, "
             f"{len(plan.brief.left_out)} left out"]
    lines += [f"warning: {w}" for w in plan.warnings]
    if plan.surface is None or parsed.dry_run:
        lines += ["", plan.brief.text if plan.surface is None else plan.interior]
    data = {"target": target.name, "status": plan.status, "dry_run": parsed.dry_run,
            "surface": rel, "warnings": list(plan.warnings),
            "brief": plan.brief.text, "receipt": plan.brief.receipt}
    return emit(out, command="switch", message=lines[0], data=data, text="\n".join(lines))
