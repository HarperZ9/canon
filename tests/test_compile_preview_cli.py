from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text, sha256_bytes
from canon.exit_codes import EX_CONFLICT, EX_OK, EX_SECURITY, EX_UNAVAILABLE, EX_USAGE


FIXTURES = Path(__file__).parent / "fixtures" / "bootstrap"
ARTIFACTS = ("canon.capsule.json", "CANON.md", "readiness-probe.json")


def _copy_inputs(workspace: Path) -> tuple[Path, Path]:
    records = workspace / "records.jsonl"
    atoms = workspace / "atoms.jsonl"
    records.write_bytes((FIXTURES / "records.jsonl").read_bytes())
    atoms.write_bytes((FIXTURES / "atoms.jsonl").read_bytes())
    return records, atoms


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


def _base_args(workspace: Path) -> list[str]:
    return [
        "--workspace",
        str(workspace),
        "--records",
        "records.jsonl",
        "--atoms",
        "atoms.jsonl",
        "--target",
        "codex-cli",
    ]


def _source_state_digest(workspace: Path, records: str, atoms: str) -> str:
    import hashlib

    items = []
    for rel in (records, atoms):
        raw = (workspace / rel).read_bytes()
        items.append({"path": rel, "sha256": sha256_bytes(raw), "size": len(raw)})
    body = json.dumps(sorted(items, key=lambda item: item["path"]), sort_keys=True, separators=(",", ":")) + "\n"
    return "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()


def _tree(root: Path) -> list[str]:
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


class _HostileChunkStream(io.StringIO):
    def read(self, size: int = -1) -> object:
        del size
        return _HostileChunk()


class _HostileChunk:
    def __repr__(self) -> str:
        return "leaked-secret-token"


def test_bootstrap_fixtures_use_authoritative_atom_and_record_schema() -> None:
    from canon.atom import load_atoms_jsonl
    from canon.schema import Record
    from canon.validator import validate_record

    records = [Record.from_json(line) for line in (FIXTURES / "records.jsonl").read_text().splitlines()]
    atoms = load_atoms_jsonl((FIXTURES / "atoms.jsonl").read_text())

    assert [record.id for record in records] == ["voice-canon"]
    assert all(validate_record(record) == [] for record in records)
    assert [atom.id for atom in atoms] == [
        "goal-foundation",
        "perm-plan-only",
        "prohibit-product-code",
        "frontier-foundation-next",
    ]
    assert all("atom_id" not in atom.to_dict() for atom in atoms)


def test_compile_without_json_or_out_emits_exact_markdown_and_no_result_noise(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["compile", *_base_args(workspace)])

    assert code == EX_OK
    assert stdout.startswith("# CANON\n<!-- canon:capsule/v1 digest=sha256:")
    assert "PASS compile" not in stdout
    assert stderr == ""
    assert _tree(workspace) == ["atoms.jsonl", "records.jsonl"]


def test_compile_json_after_subcommand_uses_canonical_envelope_and_exact_source_bytes(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    (workspace / "records.jsonl").write_bytes((FIXTURES / "records.jsonl").read_bytes().replace(b"\n", b"\r\n"))

    code, stdout, stderr = _run(["compile", "--json", *_base_args(workspace)])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    data = payload["data"]
    assert payload["message"] == "capsule compiled"
    assert data["source_state"]["records_digest"] == _source_state_digest(workspace, "records.jsonl", "atoms.jsonl")
    assert data["target"] == {
        "adapter": "codex-cli",
        "host_enforcement_observed": False,
        "integration_tier": "native-advisory",
        "surface": "CANON.md",
    }


def test_preview_json_never_mutates_filesystem_and_reports_bundle(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    before = _tree(workspace)

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace)])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    assert payload["command"] == "preview"
    assert payload["data"]["mode"] == "preview"
    assert set(payload["data"]["artifacts"]) == set(ARTIFACTS)
    assert _tree(workspace) == before


def test_compile_out_publishes_three_canonical_artifacts_and_is_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    argv = ["--json", "compile", *_base_args(workspace), "--out", "bundle"]

    first = _run(argv)
    if os.name != "nt":
        assert first[0] == EX_SECURITY
        assert first[2] == ""
        assert _json(first[1])["failure_code"] == "unsafe_path"
        assert not (workspace / "bundle").exists()
        assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
        return
    second = _run(argv)

    assert first[0] == second[0] == EX_OK
    assert first[2] == second[2] == ""
    assert _json(first[1]) == _json(second[1])
    bundle = workspace / "bundle"
    assert set(_tree(bundle)) == set(ARTIFACTS)
    for name in ("canon.capsule.json", "readiness-probe.json"):
        text = (bundle / name).read_text(encoding="utf-8")
        assert text == canonical_json_text(json.loads(text))
    assert (bundle / "CANON.md").read_text(encoding="utf-8").startswith("# CANON\n")


def test_existing_mixed_output_state_conflicts_without_overwrite(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    out = workspace / "bundle"
    out.mkdir()
    (out / "CANON.md").write_text("user draft\n", encoding="utf-8")

    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert (out / "CANON.md").read_text(encoding="utf-8") == "user draft\n"


def test_stdin_may_be_consumed_once_and_only_from_injected_stream(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    record_text = (FIXTURES / "records.jsonl").read_text(encoding="utf-8")

    code, _stdout, stderr = _run(["--json", "preview", *_base_args(workspace), "--records", "-"], stdin=io.StringIO(record_text))
    assert code == EX_OK
    assert stderr == ""

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace), "--records", "-", "--atoms", "-"], stdin=io.StringIO(record_text))
    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace), "--records", "-"])
    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["message"] == "invalid compile input"


def test_stdin_is_rejected_once_utf8_bytes_exceed_source_limit(tmp_path: Path) -> None:
    from canon.cli_artifacts import MAX_SOURCE_BYTES

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(
        ["--json", "preview", *_base_args(workspace), "--records", "-"],
        stdin=io.StringIO("\n" * (MAX_SOURCE_BYTES + 1)),
    )

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"


def test_stdin_hostile_read_chunk_is_sanitized(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(
        ["--json", "preview", *_base_args(workspace), "--records", "-"],
        stdin=_HostileChunkStream(),
    )

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"
    assert "leaked-secret-token" not in stdout + stderr


@pytest.mark.parametrize(
    "body",
    [
        b"\xef\xbb\xbf{\"canon_schema\":\"canon.record/v1\"}\n",
        b"{\"canon_schema\":\"canon.record/v1\",\"canon_schema\":\"canon.record/v1\"}\n",
        b"[]\n",
        b"{bad-json leaked-secret-token\n",
    ],
)
def test_malformed_jsonl_inputs_are_invalid_args_and_sanitized(tmp_path: Path, body: bytes) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    (workspace / "records.jsonl").write_bytes(body)

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace)])

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"
    assert "leaked-secret-token" not in stdout


def test_atom_id_fallback_is_rejected_when_authoritative_id_is_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    atom = json.loads((FIXTURES / "atoms.jsonl").read_text(encoding="utf-8").splitlines()[0])
    atom["atom_id"] = "stale-goal"
    del atom["id"]
    (workspace / "atoms.jsonl").write_text(json.dumps(atom, sort_keys=True) + "\n", encoding="utf-8")

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace)])

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"


def test_source_path_failures_map_to_unreachable_or_unsafe_without_leaking_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    outside = tmp_path / "leaked-secret-token.jsonl"
    outside.write_text("[]\n", encoding="utf-8")

    missing = _run(["--json", "preview", *_base_args(workspace), "--records", "missing.jsonl"])
    outside_result = _run(["--json", "preview", *_base_args(workspace), "--records", str(outside)])

    assert missing[0] == EX_UNAVAILABLE
    assert _json(missing[1])["failure_code"] == "source_unreachable"
    assert outside_result[0] == EX_SECURITY
    assert _json(outside_result[1])["failure_code"] == "unsafe_path"
    assert "leaked-secret-token" not in outside_result[1] + outside_result[2]


def test_symlink_source_is_rejected_before_read_when_platform_allows(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    records, _atoms = _copy_inputs(workspace)
    link = workspace / "records-link.jsonl"
    try:
        link.symlink_to(records)
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace), "--records", "records-link.jsonl"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"


def test_workspace_directory_swap_during_source_resolution_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_artifacts as cli_artifacts

    anchor = tmp_path / "anchor"
    workspace = anchor / "work"
    outside_anchor = tmp_path / "outside-anchor"
    outside_workspace = outside_anchor / "work"
    displaced = tmp_path / "displaced-work"
    workspace.mkdir(parents=True)
    outside_workspace.mkdir(parents=True)
    _copy_inputs(workspace)
    _copy_inputs(outside_workspace)
    real_resolve = cli_artifacts.resolve_under_root
    attempted = False

    def swap_once(path: object, **kwargs: object) -> Path:
        nonlocal attempted
        if not attempted:
            attempted = True
            workspace.rename(displaced)
            outside_workspace.rename(workspace)
        return real_resolve(path, **kwargs)

    monkeypatch.setattr(cli_artifacts, "resolve_under_root", swap_once)

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace)])

    assert attempted
    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"


def test_critical_ids_and_guided_target_are_reported_honestly(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)

    code, stdout, stderr = _run(["--json", "preview", *_base_args(workspace), "--target", "chatgpt-app"])

    assert code == EX_OK
    assert stderr == ""
    data = _json(stdout)["data"]
    probe = data["readiness_probe"]
    assert probe["critical_sets"]["active_goal_ids"] == ["goal-foundation"]
    assert probe["critical_sets"]["permission_ids"] == ["perm-plan-only"]
    assert probe["critical_sets"]["prohibition_ids"] == ["prohibit-product-code"]
    assert data["target"]["integration_tier"] == "guided"
    assert data["target"]["host_enforcement_observed"] is False


def test_compile_publish_parent_swap_does_not_create_outside_bundle_or_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_publish as cli_publish
    if os.name != "nt":
        pytest.skip("Windows handle-pinned publish race coverage")

    anchor = tmp_path / "anchor"
    workspace = anchor / "work"
    outside_workspace = tmp_path / "outside-work"
    displaced = tmp_path / "displaced-work"
    workspace.mkdir(parents=True)
    outside_workspace.mkdir()
    _copy_inputs(workspace)
    attempted = False
    swapped = False

    def attempt_swap() -> None:
        nonlocal attempted, swapped
        attempted = True
        try:
            workspace.rename(displaced)
            outside_workspace.rename(workspace)
            swapped = True
        except OSError:
            pass

    if os.name == "nt":
        real_create = cli_publish._win.nt_create_relative

        def swap_before_stage_create(
            dir_handle: int,
            name: str,
            access: int,
            share: int,
            disposition: int,
            options: int,
        ) -> int:
            if name.startswith(".canon-compile-") and not attempted:
                attempt_swap()
            return real_create(dir_handle, name, access, share, disposition, options)

        monkeypatch.setattr(cli_publish._win, "nt_create_relative", swap_before_stage_create)
    else:
        real_mkdir = cli_publish.os.mkdir

        def swap_before_stage_mkdir(path: object, *args: object, **kwargs: object) -> object:
            if isinstance(path, str) and path.startswith(".canon-compile-") and not attempted:
                attempt_swap()
            return real_mkdir(path, *args, **kwargs)

        monkeypatch.setattr(cli_publish.os, "mkdir", swap_before_stage_mkdir)

    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert attempted
    if swapped:
        assert code == EX_SECURITY
        assert _json(stdout)["failure_code"] == "unsafe_path"
        assert not (workspace / "bundle").exists()
        assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
        assert not any(path.name.startswith(".canon-compile-") for path in displaced.iterdir())
    else:
        assert code == EX_OK
        assert (workspace / "bundle").is_dir()
    assert stderr == ""


def test_compile_publish_without_safe_backend_fails_before_stage_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_publish as cli_publish
    if os.name != "nt":
        pytest.skip("Windows handle-pinned publish race coverage")

    workspace = tmp_path / "work"
    workspace.mkdir()
    _copy_inputs(workspace)
    if os.name == "nt":
        monkeypatch.setattr(cli_publish._win, "supported", lambda: False)

    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert not (workspace / "bundle").exists()
    assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())


def test_posix_publish_backend_rejects_before_mkdir_open_write_or_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_publish as cli_publish

    workspace = tmp_path / "work"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*args: object, **kwargs: object) -> None:
            del args, kwargs
            calls.append(name)
            raise AssertionError(f"{name} must not be called")
        return fail

    monkeypatch.setattr(cli_publish.os, "name", "posix")
    monkeypatch.setattr(cli_publish, "_posix_supported", lambda: True, raising=False)
    monkeypatch.setattr(cli_publish.os, "O_DIRECTORY", 0, raising=False)
    monkeypatch.setattr(cli_publish.os, "O_NOFOLLOW", 0, raising=False)
    for name in ("mkdir", "open", "write", "rename"):
        monkeypatch.setattr(cli_publish.os, name, forbidden(name))

    with pytest.raises(cli_publish.PublishError) as excinfo:
        cli_publish.publish_new_bundle(
            workspace / "bundle",
            tuple((name, b"artifact\n") for name in ARTIFACTS),
            workspace_path=workspace,
            workspace_key=(0, 0),
        )

    assert excinfo.value.code == "unsafe_path"
    assert calls == []
    assert not (workspace / "bundle").exists()
    assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
    assert _tree(outside) == []


def test_compile_out_safe_publish_rejection_is_sanitized_and_mutates_no_stage_or_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_artifacts as cli_artifacts
    import canon.cli_publish as cli_publish

    workspace = tmp_path / "work"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    _copy_inputs(workspace)

    def reject_publish(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise cli_publish.PublishError("unsafe_path")

    monkeypatch.setattr(cli_artifacts, "publish_new_bundle", reject_publish)

    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert not (workspace / "bundle").exists()
    assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
    assert _tree(outside) == []


def test_compile_publish_stage_swap_does_not_write_outside_or_publish_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_publish as cli_publish

    if os.name != "nt":
        pytest.skip("Windows handle-pinned publish race coverage")

    workspace = tmp_path / "work"
    outside = tmp_path / "outside"
    moved_stage = tmp_path / "moved-stage"
    workspace.mkdir()
    outside.mkdir()
    _copy_inputs(workspace)
    attempted = False
    swapped = False

    def attempt_stage_swap() -> None:
        nonlocal attempted, swapped
        attempted = True
        try:
            stage = next(path for path in workspace.iterdir() if path.name.startswith(".canon-compile-"))
            stage.rename(moved_stage)
            stage.symlink_to(outside, target_is_directory=True)
            swapped = True
        except (OSError, StopIteration):
            pass

    real_create = cli_publish._win.nt_create_relative

    def swap_before_stage_file_create(
        dir_handle: int,
        name: str,
        access: int,
        share: int,
        disposition: int,
        options: int,
    ) -> int:
        if name in ARTIFACTS and not attempted:
            attempt_stage_swap()
        return real_create(dir_handle, name, access, share, disposition, options)

    monkeypatch.setattr(cli_publish._win, "nt_create_relative", swap_before_stage_file_create)

    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert attempted
    if swapped:
        assert code == EX_SECURITY
        assert _json(stdout)["failure_code"] == "unsafe_path"
        assert _tree(outside) == []
        assert not (workspace / "bundle").exists()
        assert not any(path.is_symlink() for path in workspace.iterdir())
        if moved_stage.exists():
            assert not any(path.name in ARTIFACTS for path in moved_stage.rglob("*"))
    else:
        assert code == EX_OK
        assert _tree(outside) == []
        assert (workspace / "bundle").is_dir()
    assert stderr == ""


def test_output_path_rejects_symlink_parent_and_cleans_stage_on_publish_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_publish as cli_publish

    workspace = tmp_path / "work"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    _copy_inputs(workspace)
    try:
        (workspace / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    blocked = _run(["--json", "compile", *_base_args(workspace), "--out", "link/bundle"])
    assert blocked[0] == EX_SECURITY
    assert _json(blocked[1])["failure_code"] == "unsafe_path"
    assert _tree(outside) == []
    if os.name != "nt":
        disabled = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])
        assert disabled[0] == EX_SECURITY
        assert _json(disabled[1])["failure_code"] == "unsafe_path"
        assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
        return

    def fail_rename(parent: object, stage: object, target_name: object) -> None:
        del parent, stage, target_name
        raise OSError("leaked-secret-token")

    monkeypatch.setattr(cli_publish, "_rename_stage", fail_rename)
    code, stdout, stderr = _run(["--json", "compile", *_base_args(workspace), "--out", "bundle"])

    assert code == 8
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "io_error"
    assert not any(path.name.startswith(".canon-compile-") for path in workspace.iterdir())
    assert "leaked-secret-token" not in stdout
