from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text
from canon.exit_codes import EX_CONFLICT, EX_OK, EX_SECURITY, EX_UNSUPPORTED, EX_USAGE

FIXTURES = Path(__file__).parent / "fixtures" / "bootstrap"
BEGIN = "<!-- canon:begin scope=workspace -->"
END = "<!-- canon:end -->"
SECRET = "sk-" + ("a" * 24)


def _copy_inputs(workspace: Path, *, atoms: str = "atoms.jsonl") -> None:
    (workspace / "records.jsonl").write_bytes((FIXTURES / "records.jsonl").read_bytes())
    (workspace / "atoms.jsonl").write_bytes((FIXTURES / atoms).read_bytes())


def _run(argv: list[str], *, stdin: io.StringIO | None = None) -> tuple[int, str, str]:
    from canon.cli import run_cli

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_cli(argv, stdin=stdin, stdout=stdout, stderr=stderr, environ={})
    return code, stdout.getvalue(), stderr.getvalue()


def _json(stdout: str) -> dict[str, object]:
    payload = json.loads(stdout)
    assert stdout == canonical_json_text(payload)
    assert "\r" not in stdout
    return payload


def _base_args(workspace: Path, *, target: str = "codex-cli") -> list[str]:
    return [
        "--workspace",
        str(workspace),
        "--records",
        "records.jsonl",
        "--atoms",
        "atoms.jsonl",
        "--target",
        target,
    ]


def _host(inner: str = "OLD\n", *, crlf: bool = False) -> str:
    newline = "\r\n" if crlf else "\n"
    return newline.join(["preface", BEGIN, inner.rstrip("\n"), END, "tail", ""])


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _write_expected_bundle(workspace: Path, target: Path) -> None:
    target.mkdir()
    for fmt, name in (
        ("capsule-json", "canon.capsule.json"),
        ("canon-md", "CANON.md"),
        ("readiness-json", "readiness-probe.json"),
    ):
        code, stdout, stderr = _run(["export", *_base_args(workspace), "--format", fmt])
        assert code == EX_OK
        assert stderr == ""
        (target / name).write_text(stdout, encoding="utf-8", newline="\n")


def _skip_windows_mutation_disabled() -> None:
    if os.name == "nt":
        pytest.skip("Task10 local mutation safely fails closed on Windows")


def test_export_canon_md_raw_stdout_has_no_result_prose(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["export", *_base_args(workspace), "--format", "canon-md"])

    assert code == EX_OK
    assert stderr == ""
    assert stdout.startswith("# CANON\n<!-- canon:capsule/v1 digest=sha256:")
    assert "PASS export" not in stdout


@pytest.mark.parametrize(
    ("fmt", "schema"),
    (("capsule-json", "canon.capsule/v1"), ("readiness-json", "canon.readiness-probe/v1")),
)
def test_export_json_payload_formats_are_canonical_stdout(tmp_path: Path, fmt: str, schema: str) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["export", *_base_args(workspace), "--format", fmt])

    assert code == EX_OK
    assert stderr == ""
    payload = json.loads(stdout)
    assert stdout == canonical_json_text(payload)
    assert payload["schema"] == schema


def test_export_json_mode_reports_metadata_not_raw_payload(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "canon-md"])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    data = payload["data"]
    assert data["command"] == "export"
    assert data["format"] == "canon-md"
    assert data["target"] == "codex-cli"
    assert data["canon_md_sha256"].startswith("sha256:")
    assert data["canon_md_bytes"] > 0
    assert "# CANON" not in stdout
    assert "Feature-first. Words with weight." not in stdout


@pytest.mark.parametrize(
    "extra",
    (
        (),
        ("--format", "unknown"),
        ("--format", "canon-md", "--out", "out.md", "--apply-region", "AGENTS.md"),
        ("--format", "bundle"),
        ("--format", "region"),
    ),
)
def test_export_argument_errors_return_invalid_args(tmp_path: Path, extra: tuple[str, ...]) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), *extra])

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"


def test_export_unknown_target_returns_invalid_args(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace, target="ghost"), "--format", "canon-md"])

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"


def test_export_bundle_new_directory_keeps_task7_publish_lockout(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "bundle", "--out", "bundle"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert not (workspace / "bundle").exists()
    assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())


def test_export_bundle_existing_exact_artifacts_are_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    _write_expected_bundle(workspace, workspace / "bundle")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "bundle", "--out", "bundle"])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    assert payload["data"]["write_status"] == "idempotent"
    assert _tree(workspace / "bundle") == ["CANON.md", "canon.capsule.json", "readiness-probe.json"]


def test_export_bundle_existing_mismatch_conflicts_without_overwrite(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    _write_expected_bundle(workspace, workspace / "bundle")
    (workspace / "bundle" / "CANON.md").write_text("user draft\n", encoding="utf-8")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "bundle", "--out", "bundle"])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert (workspace / "bundle" / "CANON.md").read_text(encoding="utf-8") == "user draft\n"


def test_export_region_codex_writes_only_agents_region_and_receipt(tmp_path: Path) -> None:
    _skip_windows_mutation_disabled()
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    target.write_text(_host(crlf=True), encoding="utf-8", newline="")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    data = payload["data"]
    after = target.read_bytes()
    assert data["changed"] is True
    assert data["target_path"] == "AGENTS.md"
    assert data["receipt_id"].startswith("undo-")
    assert after.startswith(f"preface\r\n{BEGIN}\r\n".encode())
    assert after.endswith(f"{END}\r\ntail\r\n".encode())
    assert b"OLD" not in after
    assert b'<!-- canon:block id="voice-canon"' in after
    assert len(list((workspace / ".canon" / "undo").glob("undo-*.json"))) == 1


def test_export_region_claude_code_writes_only_claude_region(tmp_path: Path) -> None:
    _skip_windows_mutation_disabled()
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    (workspace / "CLAUDE.md").write_text(_host(), encoding="utf-8")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace, target="claude-code"), "--format", "region", "--apply-region", "CLAUDE.md"])

    assert code == EX_OK
    assert stderr == ""
    assert _json(stdout)["data"]["target_path"] == "CLAUDE.md"
    assert "<!-- canon:block id=\"voice-canon\"" in (workspace / "CLAUDE.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("body", ("ordinary host\n", f"{BEGIN}\nold\n{END}\n{BEGIN}\nold\n{END}\n", "<!-- canon:begin scope=repo -->\nold\n<!-- canon:end -->\n"))
def test_export_region_missing_duplicate_or_malformed_markers_conflict(tmp_path: Path, body: str) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    target.write_text(body, encoding="utf-8")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert target.read_text(encoding="utf-8") == body
    assert not (workspace / ".canon" / "undo").exists()


def test_export_region_idempotent_current_region_creates_no_duplicate_receipt(tmp_path: Path) -> None:
    _skip_windows_mutation_disabled()
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    target.write_text(_host(), encoding="utf-8")
    first = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    before = target.read_bytes()

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert first[0] == EX_OK
    assert code == EX_OK
    assert stderr == ""
    assert _json(stdout)["data"]["changed"] is False
    assert target.read_bytes() == before
    assert len(list((workspace / ".canon" / "undo").glob("undo-*.json"))) == 1


def test_export_region_windows_identical_region_remains_read_only_noop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name != "nt":
        pytest.skip("Windows fail-closed no-op contract")
    import canon.cli_export as cli_export

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    target.write_text(_host(), encoding="utf-8", newline="")
    monkeypatch.setattr(cli_export, "render_region_inner", lambda *_args, **_kwargs: "OLD\n")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert code == EX_OK
    assert stderr == ""
    assert _json(stdout)["data"]["changed"] is False
    assert target.read_text(encoding="utf-8") == _host()
    assert not (workspace / ".canon" / "undo").exists()


def test_export_region_disallowed_adapter_is_unsupported_lifecycle(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    before = _host()
    (workspace / "AGENTS.md").write_text(before, encoding="utf-8")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace, target="chatgpt-app"), "--format", "region", "--apply-region", "AGENTS.md"])

    assert code == EX_UNSUPPORTED
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsupported_lifecycle"
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == before


def test_export_region_adapter_surface_mismatch_conflicts_without_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    before = _host()
    (workspace / "CLAUDE.md").write_text(before, encoding="utf-8")

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "CLAUDE.md"])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert (workspace / "CLAUDE.md").read_text(encoding="utf-8") == before


@pytest.mark.parametrize("target_path", (".env", ".git/config", "../outside/AGENTS.md", "AGENTS.md:secret"))
def test_export_region_unsafe_paths_fail_before_mutation(tmp_path: Path, target_path: str) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    (workspace / ".git").mkdir()
    (workspace / ".git" / "config").write_text(_host(), encoding="utf-8")
    (workspace / ".env").write_text(_host(), encoding="utf-8")
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", target_path])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"


def test_export_region_current_hash_drift_conflicts_without_command_mutation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _skip_windows_mutation_disabled()
    import canon.cli_export as cli_export

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    target.write_text(_host(), encoding="utf-8")
    drifted = f"human edit\n{BEGIN}\nstill human\n{END}\n"
    real_replace = cli_export.replace_region_file

    def drift_before_replace(path: Path, expected_hash: str, postimage: bytes, **kwargs: object) -> None:
        target.write_text(drifted, encoding="utf-8")
        real_replace(path, expected_hash, postimage, **kwargs)

    monkeypatch.setattr(cli_export, "replace_region_file", drift_before_replace)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert target.read_text(encoding="utf-8") == drifted


def test_export_secret_in_source_host_or_postimage_quarantines_without_leak(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import canon.cli_export as cli_export

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace, atoms="secret_atoms.jsonl")
    source_result = _run(["--json", "export", *_base_args(workspace), "--format", "canon-md"])
    assert source_result[0] == EX_SECURITY
    assert _json(source_result[1])["failure_code"] == "secret_quarantine"

    _copy_inputs(workspace)
    (workspace / "AGENTS.md").write_text(f"{BEGIN}\n{SECRET}\n{END}\n", encoding="utf-8")
    host_result = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    assert host_result[0] == EX_SECURITY
    assert _json(host_result[1])["failure_code"] == "secret_quarantine"

    monkeypatch.setattr(cli_export, "render_region_inner", lambda *args, **kwargs: SECRET + "\n")
    (workspace / "AGENTS.md").write_text(_host(), encoding="utf-8")
    post_result = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    assert post_result[0] == EX_SECURITY
    assert _json(post_result[1])["failure_code"] == "secret_quarantine"
    combined = "".join(part for result in (source_result, host_result, post_result) for part in result[1:])
    assert SECRET not in combined
    assert not (workspace / ".canon" / "undo").exists()
