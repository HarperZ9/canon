from __future__ import annotations

from pathlib import Path

import pytest

from canon.canonmd import (
    CANON_MD_SECTIONS,
    CanonMdError,
    parse_canon_md_carrier,
    render_canon_md,
    verify_canon_md,
)
from canon.capsule import (
    Capsule,
    CapsuleBundle,
    CapsuleCompileRequest,
    capsule_bytes,
    compile_capsule,
)
from tests.test_capsule import _atom, _budget, _capsule_fixture, _source_state, _target


def test_render_canon_md_is_deterministic_and_section_ordered():
    text1 = render_canon_md(_capsule_fixture())
    text2 = render_canon_md(_capsule_fixture())
    assert text1 == text2
    positions = [text1.index("## " + section) for section in CANON_MD_SECTIONS]
    assert positions == sorted(positions)


def test_canon_md_carrier_roundtrips_capsule_dict():
    capsule = _capsule_fixture()
    text = render_canon_md(capsule)
    assert parse_canon_md_carrier(text) == capsule.to_dict()


def test_verify_canon_md_detects_body_drift():
    text = render_canon_md(_capsule_fixture())
    tampered = text.replace("## Active goals", "## Active goals\n\nTampered line", 1)
    assert any("body drift" in p for p in verify_canon_md(tampered))


def test_verify_canon_md_detects_capsule_mismatch():
    text = render_canon_md(_capsule_fixture())
    changed = _capsule_fixture().to_dict()
    changed["does_not_prove"] = ["changed"]
    assert any("capsule mismatch" in p for p in verify_canon_md(text, Capsule.from_dict(changed)))


def test_render_canon_md_includes_required_visible_state():
    text = render_canon_md(_capsule_fixture())
    assert "# CANON\n" in text
    assert "sha256:" in text
    assert "native-advisory" in text
    assert "goal-foundation" in text
    assert "perm-plan-only" in text
    assert "prohibit-product-code" in text
    assert "conflict-enforced-tier" in text
    assert "unknown-closed-app-hooks" in text
    assert "This capsule does not prove host-level enforcement." in text


def test_compile_capsule_returns_bundle_with_manifest_canon_md_and_probe():
    request = CapsuleCompileRequest(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=(
            _atom("atom_active_goal.json"),
            _atom("atom_permission.json"),
            _atom("atom_prohibition.json"),
            _atom("atom_constraint.json"),
            _atom("atom_frontier_state.json"),
            _atom("atom_conflict.json"),
            _atom("atom_unknown.json"),
        ),
        required_atom_ids=("goal-foundation", "perm-plan-only", "prohibit-product-code"),
        readiness_probe_id="probe-foundation-compile",
    )
    bundle = compile_capsule(request)
    assert isinstance(bundle, CapsuleBundle)
    assert bundle.manifest_bytes == capsule_bytes(bundle.capsule)
    assert bundle.canon_md == render_canon_md(bundle.capsule)
    assert bundle.readiness_probe.probe_id == "probe-foundation-compile"
    assert bundle.readiness_probe.capsule_id == bundle.capsule.capsule_id
    assert list(bundle.readiness_probe.critical_sets["active_goal_ids"]) == ["goal-foundation"]


@pytest.mark.parametrize(
    "text",
    (
        "",
        "# CANON\n",
        "<!-- canon:capsule/v1 digest=sha256:bad payload=bad -->\n",
        "<!-- canon:capsule/v1 digest=sha256:"
        + "a" * 64
        + " payload=not-base64 -->\n",
        "<!-- canon:capsule/v1 digest=sha256:"
        + "a" * 64
        + " payload=eyJub3QiOiAiYSBjYXBzdWxlIn0 -->\n",
    ),
)
def test_verify_canon_md_is_total_for_malformed_markdown_and_carriers(text):
    problems = verify_canon_md(text)
    assert isinstance(problems, list)
    assert problems


def test_parse_canon_md_carrier_rejects_ambiguous_carriers():
    text = render_canon_md(_capsule_fixture())
    carrier = next(line for line in text.splitlines() if line.startswith("<!-- canon:capsule/v1 "))
    ambiguous = text + "\n" + carrier + "\n"
    with pytest.raises(CanonMdError, match="exactly one carrier"):
        parse_canon_md_carrier(ambiguous)
    assert any("exactly one carrier" in p for p in verify_canon_md(ambiguous))


def test_verify_canon_md_binds_carrier_digest_to_payload_capsule_id():
    text = render_canon_md(_capsule_fixture())
    tampered = text.replace(_capsule_fixture().capsule_id, "sha256:" + "b" * 64, 1)
    assert any("carrier digest" in p for p in verify_canon_md(tampered))


def test_render_canon_md_matches_locked_fixture():
    expected = (Path(__file__).parent / "fixtures" / "foundation" / "CANON.expected.md").read_text(encoding="utf-8")
    assert render_canon_md(_capsule_fixture()) == expected
