"""test_writing_gate.py -- V2: the injected STE writing gate.

canon is self-contained and stdlib-only, and the STE linter (check_writing.py)
and its profiles live outside this repo. So the gate is an injected seam: canon
defines the checker callable, the per-surface profile register, and the gate
pipeline; the caller wires the real checker as
`lambda text, name: check_writing.check_text(text, writing_profiles.load(name))`.

A file passes iff the checker reports an empty `hard` list -- the exact signal
check_writing --gate keys on. These tests inject a fake checker mirroring that
contract, so no external linter is imported.
"""
from __future__ import annotations

from canon.registry import (
    ROOT_HOME,
    ROOT_WORKSPACE,
    Surface,
    pool_for,
)
from canon.schema import KIND_PERSONALITY_BLOCK, Provenance, Record
from canon.surface import render_surface
from canon.writing_gate import (
    DEFAULT_STE_PROFILE,
    GateResult,
    STE_PROFILE_BY_HARNESS_SCOPE,
    gate_surface,
    gate_text,
    ste_profile_for,
)

CLAUDE_GLOBAL = Surface("claude-code", "global", ROOT_HOME, ".claude/CLAUDE.md")
CLAUDE_WS = Surface("claude-code", "workspace", ROOT_WORKSPACE, "CLAUDE.md")
CODEX_WS = Surface("codex", "workspace", ROOT_WORKSPACE, "AGENTS.md")
SOUL_WS = Surface("hermes", "workspace", ROOT_WORKSPACE, "SOUL.md")


def _block(id: str, scope: str, body: str, create_ord: int) -> Record:
    prov = Provenance(harness="claude-code", source_hash="a" * 64,
                      create_ord=create_ord)
    return Record(kind=KIND_PERSONALITY_BLOCK, id=id, scope=scope,
                  data={"title": id.title(), "body": body}, provenance=prov)


def _checker(hard_categories):
    """A fake WritingChecker mirroring check_writing.check_text: returns a score
    mapping whose `hard` key lists hard-violation categories. It also echoes the
    text and profile it saw, so a test can assert what it was called with."""
    calls: list[tuple[str, str]] = []

    def check(text: str, profile: str):
        calls.append((text, profile))
        return {"hard": list(hard_categories), "profile": profile}

    check.calls = calls  # type: ignore[attr-defined]
    return check


def test_gate_passes_when_no_hard_violations():
    result = gate_text("clean prose", "readme", checker=_checker([]))
    assert isinstance(result, GateResult)
    assert result.ok
    assert result.hard == ()


def test_gate_fails_on_a_hard_violation():
    result = gate_text("prose -- with an em dash", "readme",
                       checker=_checker(["em_dash"]))
    assert not result.ok
    assert result.hard == ("em_dash",)


def test_gate_calls_the_checker_with_the_named_profile():
    checker = _checker([])
    gate_text("some text", "chat", checker=checker)
    assert checker.calls == [("some text", "chat")]


def test_pre_clean_runs_before_the_check():
    checker = _checker([])
    result = gate_text("dirty", "readme", checker=checker,
                       pre_clean=str.upper)
    assert result.cleaned == "DIRTY"
    assert checker.calls == [("DIRTY", "readme")]  # checker saw cleaned text


def test_ste_profile_register_maps_each_surface():
    assert ste_profile_for(CLAUDE_GLOBAL) == "readme"
    assert ste_profile_for(CLAUDE_WS) == "readme"
    assert ste_profile_for(CODEX_WS) == "readme"
    assert ste_profile_for(SOUL_WS) == "chat"


def test_ste_profile_defaults_for_an_unregistered_surface():
    unknown = Surface("gemini", "workspace", ROOT_WORKSPACE, "GEMINI.md")
    assert ste_profile_for(unknown) == DEFAULT_STE_PROFILE
    assert ("gemini", "workspace") not in STE_PROFILE_BY_HARNESS_SCOPE


def test_gate_surface_uses_the_registered_profile_and_path_label():
    checker = _checker([])
    result = gate_surface(SOUL_WS, "voice prose", checker=checker)
    assert result.profile == "chat"
    assert result.label == "SOUL.md"
    assert checker.calls == [("voice prose", "chat")]


def test_gate_surfaces_a_malformed_score_missing_hard():
    # The gate reads the checker's pass/fail signal, the `hard` list. A checker
    # that returns a score without it is broken, and the gate must surface that
    # wiring fault (D-39), not silently green-light. Fail closed, not open.
    def broken(text: str, profile: str):
        return {"em_dash": 0}  # no `hard` key

    try:
        gate_text("text", "readme", checker=broken)
    except KeyError:
        return
    raise AssertionError("gate must raise on a score with no hard key")


def test_rendered_surface_fails_then_passes():
    # The exit criterion: the gate runs on the actual rendered file. Render a
    # surface interior, gate it with a checker that flags a hard violation
    # (fail), then with a clean checker (pass).
    pool = [_block("tone", "workspace", "W tone", 20)]
    rendered = render_surface(pool_for(CLAUDE_WS, pool), CLAUDE_WS.scope)

    failing = gate_surface(CLAUDE_WS, rendered, checker=_checker(["parataxis"]))
    assert not failing.ok
    assert failing.cleaned == rendered

    passing = gate_surface(CLAUDE_WS, rendered, checker=_checker([]))
    assert passing.ok
