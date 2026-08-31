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
    build_capsule,
    capsule_bytes,
    compile_capsule,
)
from canon.atom import CanonAtom
from canon.omission import Omission
from canon.transform import TransformReceipt
from tests.test_capsule import _atom, _budget, _capsule_fixture, _source_state, _target, load_fixture


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


def test_parse_canon_md_carrier_requires_canonical_line_two():
    lines = render_canon_md(_capsule_fixture()).splitlines()
    carrier = lines.pop(1)
    moved = "\n".join(lines) + "\n" + carrier + "\n"
    with pytest.raises(CanonMdError, match="immediately after # CANON"):
        parse_canon_md_carrier(moved)
    assert any("immediately after # CANON" in p for p in verify_canon_md(moved))


def test_render_canon_md_escapes_capsule_sourced_visible_markdown():
    text = render_canon_md(_hostile_visible_capsule())
    assert _h2_lines(text) == ["## " + section for section in CANON_MD_SECTIONS]
    assert text.splitlines()[1].startswith("<!-- canon:capsule/v1 digest=sha256:")
    assert text.count("<!-- canon:capsule/v1 ") == 1
    assert verify_canon_md(text) == []
    assert "## Spoofed" not in text
    assert "\n- injected" not in text
    assert "```" not in text
    assert "<script>" not in text
    assert "<b>" not in text
    assert "&lt;script&gt;" in text
    assert "&#96;tick&#96;" in text


def test_render_canon_md_matches_locked_fixture():
    expected = (Path(__file__).parent / "fixtures" / "foundation" / "CANON.expected.md").read_text(encoding="utf-8")
    assert render_canon_md(_capsule_fixture()) == expected


def _h2_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.startswith("## ")]


def _hostile_visible_capsule() -> Capsule:
    hostile = (
        "fake <!-- canon:capsule/v1 digest=sha256:" + "c" * 64 + " payload=bad -->"
        "\r\n## Spoofed\r\n- injected\r\n```fence``` <script>alert(1)</script> `tick` <b>bold</b>"
    )
    atoms = (
        _hostile_atom("atom_active_goal.json", "summary", hostile),
        _hostile_atom("atom_permission.json", "allows", [hostile]),
        _atom("atom_prohibition.json"),
        _atom("atom_constraint.json"),
        _atom("atom_frontier_state.json"),
        _atom("atom_conflict.json"),
        _atom("atom_unknown.json"),
    )
    return build_capsule(
        profile="handoff",
        target=_target(),
        source_state=_source_state(),
        budget=_budget(),
        atoms=atoms,
        omissions=(_hostile_omission(hostile),),
        lossy_transforms=(_hostile_transform(hostile),),
        does_not_prove=(hostile,),
        required_atom_ids=("goal-foundation", "perm-plan-only", "prohibit-product-code"),
    )


def _hostile_atom(fixture_name: str, key: str, value: object) -> CanonAtom:
    data = _atom(fixture_name).to_dict()
    data["value"][key] = value
    data["source_refs"] = [{"ref": value if isinstance(value, str) else value[0]}]
    return CanonAtom.from_dict(data)


def _hostile_omission(hostile: str) -> Omission:
    data = load_fixture("omission_budget_noncritical.json")
    data["affected_ids"] = [hostile]
    data["affected_source_refs"] = [hostile]
    data["does_not_prove"] = [hostile]
    return Omission.from_dict(data)


def _hostile_transform(hostile: str) -> TransformReceipt:
    data = load_fixture("transform_summary.json")
    data["method_id"] = hostile
    data["output_ref"] = hostile
    data["retained_critical_atom_ids"] = [hostile]
    data["does_not_prove"] = [hostile]
    return TransformReceipt.from_dict(data)
