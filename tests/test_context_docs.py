"""The shared-context docs, held against the code they describe.

Every flag and environment variable the capture hook reads is named in
docs/client-capture.md, every purge and retention flag in
docs/shared-context.md, and the README states the identity version change a
0.3.0 reader meets. The flags are read from the modules that parse them, so a
new flag without a doc line fails here.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path

import canon
from canon import client_capture, context_mcp, local_mcp

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return re.sub(r"\s+", " ", (ROOT / relative).read_text(encoding="utf-8"))


def _flags(module_path: str) -> set[str]:
    source = (ROOT / module_path).read_text(encoding="utf-8")
    return set(re.findall(r'add_argument\(\s*"(--[a-z][a-z-]*)"', source))


def test_client_capture_doc_names_every_capture_flag_and_variable() -> None:
    doc = _text("docs/client-capture.md")
    flags = _flags("src/canon/client_capture.py")
    variables = {value for name, value in vars(client_capture).items()
                 if name.startswith("ENV_") and isinstance(value, str)}

    assert {"--capture", "--transcript-locator"} <= flags
    assert [flag for flag in sorted(flags) if f"`{flag}`" not in doc] == []
    assert [name for name in sorted(variables) if f"`{name}`" not in doc] == []
    for value in ("prompts", "prompts+responses", "path", "none"):
        assert f"`{value}`" in doc


def test_shared_context_doc_names_every_purge_and_retention_flag() -> None:
    doc = _text("docs/shared-context.md")
    flags = _flags("src/canon/cli_context_purge.py") - {"--db"}

    assert {"--event-id", "--before-ord", "--all", "--keep-responses", "--policy"} <= flags
    assert [flag for flag in sorted(flags) if flag not in doc] == []
    assert "canon.context.purge" in doc and "confirm_plan_sha256" in doc


def test_shared_context_doc_states_plaintext_residue_and_the_cipher_wrapper_path() -> None:
    doc = _text("docs/shared-context.md")

    assert "plaintext" in doc and "D-7" in doc
    assert "cipher-wrapper" in doc
    assert "freed disk clusters" in doc or "disk clusters" in doc


def test_the_readme_states_the_identity_version_change() -> None:
    readme = _text("README.md")

    assert "identity version to 2" in readme
    assert "canon 0.3.0 and older refuse" in readme
    assert "canon context purge" in readme
    assert "--capture prompts+responses" in readme


def test_the_version_is_0_4_1_everywhere_it_is_declared() -> None:
    declared = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = declared["project"]["version"]
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+?)\r?$", changelog, re.MULTILINE)

    assert version == "0.4.1"
    assert canon.__version__ == context_mcp.__version__ == local_mcp.__version__ == version
    # An Unreleased stub on top, then the dated 0.4.1 entry, then 0.4.0.
    assert headings[0] == "Unreleased"
    assert re.fullmatch(r"0\.4\.1 - \d{4}-\d{2}-\d{2}", headings[1]), headings[1]
    assert headings[2].startswith("0.4.0 - ")
