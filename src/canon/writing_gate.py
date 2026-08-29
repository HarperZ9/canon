"""writing_gate.py -- V2: the injected STE writing gate.

canon is self-contained and stdlib-only, and the STE linter (check_writing.py)
and its profiles live outside this repo. So the gate is an injected seam. canon
owns three things: the checker callable's shape, the per-surface profile
register, and the gate pipeline. The caller wires the real checker, keeping
profile loading on its own side:

    from local_model.scripts import check_writing, writing_profiles
    checker = lambda text, name: check_writing.check_text(
        text, writing_profiles.load(name))

A file passes iff the checker reports an empty `hard` list. That is the exact
signal check_writing --gate keys on (`return 1 if (args.gate and any_hard) else
0`), so the gate here and the linter's own CLI agree on the verdict.

The register binds each surface's rendered prose to an STE profile. The
instruction files (CLAUDE.md, AGENTS.md) are documentation register (readme);
SOUL.md is the voice surface (chat). The strict procedure profile governs error
messages and commits, no rendered surface, so it is unused here (D-37 null).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Callable, Optional

from canon.registry import Surface

# (text, profile_name) -> a score mapping whose `hard` key lists the
# hard-violation categories. The caller loads the profile, so canon never
# imports writing_profiles.
WritingChecker = Callable[[str, str], Mapping]

# A cheap pre-clean applied before the check (forum_prose_humanize is the wired
# instance). Optional: the gate is the same with or without it.
PreCleaner = Callable[[str], str]

HARD_KEY = "hard"

STE_PROFILE_BY_HARNESS_SCOPE: dict[tuple[str, str], str] = {
    ("claude-code", "global"): "readme",
    ("claude-code", "workspace"): "readme",
    ("codex", "workspace"): "readme",
    ("hermes", "workspace"): "chat",
}

DEFAULT_STE_PROFILE = "readme"


def ste_profile_for(surface: Surface) -> str:
    """The STE profile name that governs `surface`'s rendered prose, falling
    back to DEFAULT_STE_PROFILE for a surface not yet in the register."""
    return STE_PROFILE_BY_HARNESS_SCOPE.get(
        (surface.harness, surface.scope), DEFAULT_STE_PROFILE)


@dataclass(frozen=True, slots=True)
class GateResult:
    """One writing-gate pass. ok is true iff the checker reported no hard
    violations; hard lists the categories it did report; cleaned is the text
    actually scored (post pre-clean, if any); label names the source."""

    ok: bool
    profile: str
    hard: tuple[str, ...]
    cleaned: str
    label: str


def gate_text(text: str, profile: str, *, checker: WritingChecker,
              pre_clean: Optional[PreCleaner] = None,
              label: str = "") -> GateResult:
    """Score `text` against `profile` through the injected checker, pre-cleaning
    first when a pre_clean is given. Passes iff the checker reports an empty
    hard list.

    The gate trusts the checker's contract: it reads the `hard` key and does not
    catch a checker that raises, since a raising checker is a wiring fault for
    the caller to see, not a canon refusal to absorb.
    """
    cleaned = pre_clean(text) if pre_clean is not None else text
    score = checker(cleaned, profile)
    hard = tuple(score.get(HARD_KEY, ()))
    return GateResult(ok=not hard, profile=profile, hard=hard,
                      cleaned=cleaned, label=label)


def gate_surface(surface: Surface, text: str, *, checker: WritingChecker,
                 pre_clean: Optional[PreCleaner] = None) -> GateResult:
    """gate_text with the surface's registered profile and its path as label."""
    return gate_text(text, ste_profile_for(surface), checker=checker,
                     pre_clean=pre_clean, label=surface.relative_path)
