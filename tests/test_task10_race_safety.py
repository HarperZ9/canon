from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text, sha256_bytes
from canon.exit_codes import EX_OK, EX_SECURITY

FIXTURES = Path(__file__).parent / "fixtures" / "bootstrap"
BEGIN = "<!-- canon:begin scope=workspace -->"
END = "<!-- canon:end -->"


def _copy_inputs(workspace: Path) -> None:
    (workspace / "records.jsonl").write_bytes((FIXTURES / "records.jsonl").read_bytes())
    (workspace / "atoms.jsonl").write_bytes((FIXTURES / "atoms.jsonl").read_bytes())


def _run(argv: list[str]) -> tuple[int, str, str]:
    from canon.cli import run_cli

    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_cli(argv, stdout=stdout, stderr=stderr, environ={})
    return code, stdout.getvalue(), stderr.getvalue()


def _json(stdout: str) -> dict[str, object]:
    payload = json.loads(stdout)
    assert stdout == canonical_json_text(payload)
    return payload


def _base_args(workspace: Path) -> list[str]:
    return ["--workspace", str(workspace), "--records", "records.jsonl", "--atoms", "atoms.jsonl", "--target", "codex-cli"]


def _host(inner: str = "OLD\n") -> str:
    return f"preface\n{BEGIN}\n{inner}{END}\ntail\n"


def _tree(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))


def _swap_dir_to_replacement(path: Path, replacement: Path, displaced: Path) -> bool:
    try:
        path.rename(displaced)
        replacement.rename(path)
        return True
    except OSError:
        return False


def test_export_region_rejects_workspace_swap_after_target_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.cli_export as cli_export

    workspace = tmp_path / "work"
    outside = tmp_path / "outside-work"
    displaced = tmp_path / "displaced-work"
    workspace.mkdir()
    outside.mkdir()
    _copy_inputs(workspace)
    (workspace / "AGENTS.md").write_text(_host(), encoding="utf-8", newline="")
    (outside / "AGENTS.md").write_text(_host(), encoding="utf-8", newline="")
    (outside / ".canon" / "undo").mkdir(parents=True)
    real_checked = cli_export.checked_region_path
    swapped = False

    def swap_after_validation(*args: object, **kwargs: object) -> Path:
        nonlocal swapped
        target = real_checked(*args, **kwargs)
        if not swapped:
            swapped = _swap_dir_to_replacement(workspace, outside, displaced)
        return target

    monkeypatch.setattr(cli_export, "checked_region_path", swap_after_validation)

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])

    assert swapped
    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == _host()
    assert (displaced / "AGENTS.md").read_text(encoding="utf-8") == _host()
    assert _tree(workspace / ".canon" / "undo") == []
    assert _tree(displaced / ".canon" / "undo") == []


def test_undo_apply_rejects_workspace_swap_after_target_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name == "nt":
        pytest.skip("Windows restore mutation safely fails closed before this race point")
    import canon.undo as undo

    workspace = tmp_path / "work"
    outside = tmp_path / "outside-work"
    displaced = tmp_path / "displaced-work"
    workspace.mkdir()
    outside.mkdir()
    _copy_inputs(workspace)
    (workspace / "AGENTS.md").write_text(_host(), encoding="utf-8", newline="")
    first = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    assert first[0] == EX_OK
    receipt_id = _json(first[1])["data"]["receipt_id"]
    postimage = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    (outside / "AGENTS.md").write_text(postimage, encoding="utf-8", newline="")
    real_checked = undo.checked_receipt_target
    swapped = False

    def swap_after_validation(*args: object, **kwargs: object) -> Path:
        nonlocal swapped
        target = real_checked(*args, **kwargs)
        if not swapped:
            swapped = _swap_dir_to_replacement(workspace, outside, displaced)
        return target

    monkeypatch.setattr(undo, "checked_receipt_target", swap_after_validation)

    code, stdout, stderr = _run(["--json", "undo", "apply", str(receipt_id), "--workspace", str(workspace)])

    assert swapped
    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == postimage
    assert (displaced / "AGENTS.md").read_text(encoding="utf-8") == postimage


def test_undo_receipt_write_rejects_undo_dir_swap_after_creation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import canon.undo as undo

    workspace = tmp_path / "work"
    outside_undo = tmp_path / "outside-undo"
    displaced_undo = tmp_path / "displaced-undo"
    workspace.mkdir()
    outside_undo.mkdir()
    receipt = undo.UndoReceipt.for_region(
        target_path="AGENTS.md",
        target_adapter="codex-cli",
        target_surface="AGENTS.md",
        scope="workspace",
        preimage_text=_host(),
        postimage_sha256=sha256_bytes(b"post\n"),
        postimage_region_sha256=sha256_bytes(b"region\n"),
        capsule_id="sha256:" + ("1" * 64),
        manifest_sha256="sha256:" + ("2" * 64),
        source_state={"records_digest": "sha256:" + ("3" * 64)},
    )
    swapped = False

    if os.name == "nt":
        with pytest.raises(undo.UndoError, match="unsafe_path"):
            undo.UndoStore(workspace).write(receipt)
        assert not (workspace / ".canon").exists()
        return

    import canon.undo_posix_files as undo_posix_files

    real_verify = undo_posix_files.verify
    name = f"{receipt.receipt_id}.json"

    def swap_after_undo_dir_open(cap: object) -> None:
        nonlocal swapped
        real_verify(cap)
        if getattr(cap, "path", None) == workspace / ".canon" / "undo" and not swapped:
            swapped = _swap_dir_to_replacement(workspace / ".canon" / "undo", outside_undo, displaced_undo)

    monkeypatch.setattr(undo_posix_files, "verify", swap_after_undo_dir_open)

    with pytest.raises(undo.UndoError, match="unsafe_path"):
        undo.UndoStore(workspace).write(receipt)

    assert swapped
    name = f"{receipt.receipt_id}.json"
    assert not (workspace / ".canon" / "undo" / name).exists()
    assert not (displaced_undo / name).exists()


def test_posix_replace_rolls_back_if_parent_swapped_after_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if os.name == "nt":
        pytest.skip("Windows replacement mutation safely fails closed before this race point")
    from canon.cli_artifacts import checked_workspace
    from canon.undo import UndoError
    from canon.undo_io import replace_workspace_file
    import canon.undo_posix_files as undo_posix_files

    workspace = tmp_path / "work"
    outside = tmp_path / "outside-work"
    displaced = tmp_path / "displaced-work"
    workspace.mkdir()
    outside.mkdir()
    before = _host()
    replacement = _host("NEW\n").encode("utf-8")
    (workspace / "AGENTS.md").write_text(before, encoding="utf-8", newline="")
    (outside / "AGENTS.md").write_text("outside\n", encoding="utf-8", newline="")
    checked = checked_workspace(str(workspace))
    real_fsync_dir = undo_posix_files.fsync_dir
    swapped = False

    def swap_after_rename(dir_fd: int) -> None:
        nonlocal swapped
        real_fsync_dir(dir_fd)
        if not swapped:
            swapped = _swap_dir_to_replacement(workspace, outside, displaced)

    monkeypatch.setattr(undo_posix_files, "fsync_dir", swap_after_rename)

    with pytest.raises(UndoError, match="unsafe_path"):
        replace_workspace_file(checked, "AGENTS.md", sha256_bytes(before.encode("utf-8")), replacement)

    assert swapped
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == "outside\n"
    assert (displaced / "AGENTS.md").read_text(encoding="utf-8") == before
