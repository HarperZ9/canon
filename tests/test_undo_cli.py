from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from canon.canonical_json import canonical_json_text, sha256_bytes
from canon.exit_codes import EX_CONFLICT, EX_OK, EX_SECURITY, EX_USAGE

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
    assert "\r" not in stdout
    return payload


def _base_args(workspace: Path) -> list[str]:
    return ["--workspace", str(workspace), "--records", "records.jsonl", "--atoms", "atoms.jsonl", "--target", "codex-cli"]


def _host(inner: str = "OLD\n") -> str:
    return f"preface\n{BEGIN}\n{inner}{END}\ntail\n"


def _apply_region(workspace: Path) -> tuple[str, str]:
    _skip_windows_mutation_disabled()
    _copy_inputs(workspace)
    target = workspace / "AGENTS.md"
    preimage = _host()
    target.write_text(preimage, encoding="utf-8", newline="")
    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    assert code == EX_OK
    assert stderr == ""
    return _json(stdout)["data"]["receipt_id"], preimage  # type: ignore[return-value]


def _skip_windows_mutation_disabled() -> None:
    if os.name == "nt":
        pytest.skip("Task10 local mutation safely fails closed on Windows")


def test_region_apply_creates_canonical_receipt_and_cli_never_prints_preimage(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    receipt_id, preimage = _apply_region(workspace)

    receipt_path = workspace / ".canon" / "undo" / f"{receipt_id}.json"
    body = receipt_path.read_text(encoding="utf-8")
    receipt = json.loads(body)
    assert body == canonical_json_text(receipt)
    assert receipt["schema"] == "canon.undo-receipt/v1"
    assert receipt["receipt_id"] == receipt_id
    assert receipt["target_path"] == "AGENTS.md"
    assert receipt["target_adapter"] == "codex-cli"
    assert receipt["target_surface"] == "AGENTS.md"
    assert receipt["scope"] == "workspace"
    assert receipt["preimage_text"] == preimage
    assert receipt["preimage_sha256"] == sha256_bytes(preimage.encode("utf-8"))
    assert receipt["postimage_sha256"].startswith("sha256:")
    assert receipt["postimage_region_sha256"].startswith("sha256:")
    assert receipt["manifest_sha256"].startswith("sha256:")
    assert receipt["created_by"] == "canon export --apply-region"
    assert receipt["does_not_prove"]
    assert not Path(receipt["target_path"]).is_absolute()

    code, stdout, stderr = _run(["--json", "export", *_base_args(workspace), "--format", "region", "--apply-region", "AGENTS.md"])
    assert code == EX_OK
    assert stderr == ""
    assert "preimage_text" not in stdout
    assert preimage not in stdout


def test_undo_list_returns_receipt_metadata_only(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    receipt_id, preimage = _apply_region(workspace)

    code, stdout, stderr = _run(["--json", "undo", "list", "--workspace", str(workspace)])

    assert code == EX_OK
    assert stderr == ""
    payload = _json(stdout)
    receipts = payload["data"]["receipts"]
    assert len(receipts) == 1
    assert receipts[0]["receipt_id"] == receipt_id
    assert receipts[0]["target_path"] == "AGENTS.md"
    assert "preimage_text" not in stdout
    assert preimage not in stdout


def test_undo_apply_restores_preimage_and_is_idempotent(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    receipt_id, preimage = _apply_region(workspace)
    target = workspace / "AGENTS.md"
    postimage = target.read_text(encoding="utf-8")

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt_id, "--workspace", str(workspace)])

    assert code == EX_OK
    assert stderr == ""
    data = _json(stdout)["data"]
    assert data["changed"] is True
    assert data["receipt_id"] == receipt_id
    assert target.read_text(encoding="utf-8") == preimage

    again = _run(["--json", "undo", "apply", receipt_id, "--workspace", str(workspace)])
    assert again[0] == EX_OK
    assert _json(again[1])["data"]["already_restored"] is True
    assert target.read_text(encoding="utf-8") == preimage
    assert postimage != preimage


def test_undo_apply_conflicts_when_target_drifted(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    receipt_id, _preimage = _apply_region(workspace)
    target = workspace / "AGENTS.md"
    drifted = f"human edit\n{BEGIN}\nmanual\n{END}\n"
    target.write_text(drifted, encoding="utf-8")

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt_id, "--workspace", str(workspace)])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert target.read_text(encoding="utf-8") == drifted


@pytest.mark.parametrize(
    "body",
    (
        "{not-json\n",
        '{"schema":"wrong","receipt_id":"undo-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}\n',
        '{"schema":"canon.undo-receipt/v1","receipt_id":"undo-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}\n',
        '{"schema":"canon.undo-receipt/v1","receipt_id":"undo-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","target_path":"C:/escape/AGENTS.md","target_adapter":"codex-cli","target_surface":"AGENTS.md","scope":"workspace","preimage_sha256":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","postimage_sha256":"sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","preimage_text":"","postimage_region_sha256":"sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","manifest_sha256":"not-a-sha","source_state":{},"created_by":"canon export --apply-region","does_not_prove":[]}\n',
    ),
)
def test_undo_apply_malformed_receipts_conflict_without_traceback(tmp_path: Path, body: str) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    undo_dir = workspace / ".canon" / "undo"
    undo_dir.mkdir(parents=True)
    receipt_id = "undo-" + ("a" * 64)
    (undo_dir / f"{receipt_id}.json").write_text(body, encoding="utf-8")

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt_id, "--workspace", str(workspace)])

    assert code == EX_CONFLICT
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "conflict"
    assert "C:/escape" not in stdout


def test_undo_apply_rejects_receipt_ids_not_paths(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()

    code, stdout, stderr = _run(["--json", "undo", "apply", "../undo-" + ("a" * 64), "--workspace", str(workspace)])

    assert code == EX_USAGE
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "invalid_args"


def test_windows_undo_apply_fails_closed_before_restore_write(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows fail-closed mutation contract")
    from canon.undo import UndoReceipt

    workspace = tmp_path / "work"
    workspace.mkdir()
    preimage = _host()
    postimage = _host("NEW\n")
    (workspace / "AGENTS.md").write_text(postimage, encoding="utf-8", newline="")
    receipt = UndoReceipt.for_region(
        target_path="AGENTS.md",
        target_adapter="codex-cli",
        target_surface="AGENTS.md",
        scope="workspace",
        preimage_text=preimage,
        postimage_sha256=sha256_bytes(postimage.encode("utf-8")),
        postimage_region_sha256=sha256_bytes(b"NEW\n"),
        capsule_id="sha256:" + ("1" * 64),
        manifest_sha256="sha256:" + ("2" * 64),
        source_state={"records_digest": "sha256:" + ("3" * 64)},
    )
    undo_dir = workspace / ".canon" / "undo"
    undo_dir.mkdir(parents=True)
    (undo_dir / f"{receipt.receipt_id}.json").write_text(
        canonical_json_text(receipt.to_dict()), encoding="utf-8", newline="\n"
    )

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt.receipt_id, "--workspace", str(workspace)])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == postimage


def test_windows_undo_apply_already_restored_stays_read_only(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows read-only undo no-op contract")
    from canon.undo import UndoReceipt

    workspace = tmp_path / "work"
    workspace.mkdir()
    preimage = _host()
    postimage = _host("NEW\n")
    (workspace / "AGENTS.md").write_text(preimage, encoding="utf-8", newline="")
    receipt = UndoReceipt.for_region(
        target_path="AGENTS.md",
        target_adapter="codex-cli",
        target_surface="AGENTS.md",
        scope="workspace",
        preimage_text=preimage,
        postimage_sha256=sha256_bytes(postimage.encode("utf-8")),
        postimage_region_sha256=sha256_bytes(b"NEW\n"),
        capsule_id="sha256:" + ("1" * 64),
        manifest_sha256="sha256:" + ("2" * 64),
        source_state={"records_digest": "sha256:" + ("3" * 64)},
    )
    undo_dir = workspace / ".canon" / "undo"
    undo_dir.mkdir(parents=True)
    (undo_dir / f"{receipt.receipt_id}.json").write_text(
        canonical_json_text(receipt.to_dict()), encoding="utf-8", newline="\n"
    )

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt.receipt_id, "--workspace", str(workspace)])

    assert code == EX_OK
    assert stderr == ""
    data = _json(stdout)["data"]
    assert data["already_restored"] is True
    assert data["changed"] is False
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == preimage


def test_windows_existing_receipt_write_keeps_read_only_append_contract(tmp_path: Path) -> None:
    if os.name != "nt":
        pytest.skip("Windows read-only receipt contract")
    from canon.undo import UndoError, UndoReceipt, UndoStore

    workspace = tmp_path / "work"
    workspace.mkdir()
    receipt = UndoReceipt.for_region(
        target_path="AGENTS.md",
        target_adapter="codex-cli",
        target_surface="AGENTS.md",
        scope="workspace",
        preimage_text=_host(),
        postimage_sha256="sha256:" + ("2" * 64),
        postimage_region_sha256="sha256:" + ("3" * 64),
        capsule_id="sha256:" + ("4" * 64),
        manifest_sha256="sha256:" + ("5" * 64),
        source_state={"records_digest": "sha256:" + ("6" * 64)},
    )
    undo_dir = workspace / ".canon" / "undo"
    undo_dir.mkdir(parents=True)
    receipt_path = undo_dir / f"{receipt.receipt_id}.json"
    receipt_path.write_text(canonical_json_text(receipt.to_dict()), encoding="utf-8", newline="\n")

    assert UndoStore(workspace).write(receipt) == "idempotent"
    divergent = json.loads(receipt_path.read_text(encoding="utf-8"))
    divergent["target_adapter"] = "claude-code"
    receipt_path.write_text(canonical_json_text(divergent), encoding="utf-8", newline="\n")

    with pytest.raises(UndoError, match="conflict"):
        UndoStore(workspace).write(receipt)


def test_undo_apply_uses_path_policy_from_receipt_target(tmp_path: Path) -> None:
    _skip_windows_mutation_disabled()
    from canon.undo import UndoReceipt, UndoStore

    workspace = tmp_path / "work"
    workspace.mkdir()
    target = workspace / ".env"
    preimage = "OLD=1\n"
    postimage = "NEW=1\n"
    target.write_text(postimage, encoding="utf-8")
    receipt = UndoReceipt.for_region(
        target_path=".env",
        target_adapter="codex-cli",
        target_surface="AGENTS.md",
        scope="workspace",
        preimage_text=preimage,
        postimage_sha256=sha256_bytes(postimage.encode("utf-8")),
        postimage_region_sha256=sha256_bytes(b"NEW=1\n"),
        capsule_id="sha256:" + ("1" * 64),
        manifest_sha256="sha256:" + ("2" * 64),
        source_state={"records_digest": "sha256:" + ("3" * 64)},
    )
    UndoStore(workspace).write(receipt)

    code, stdout, stderr = _run(["--json", "undo", "apply", receipt.receipt_id, "--workspace", str(workspace)])

    assert code == EX_SECURITY
    assert stderr == ""
    assert _json(stdout)["failure_code"] == "unsafe_path"
    assert target.read_text(encoding="utf-8") == postimage


def test_undo_store_is_append_only_and_detects_divergent_same_id(tmp_path: Path) -> None:
    _skip_windows_mutation_disabled()
    from canon.undo import UndoError, UndoReceipt, UndoStore

    workspace = tmp_path / "work"
    workspace.mkdir()
    store = UndoStore(workspace)
    kwargs = {
        "target_path": "AGENTS.md",
        "target_adapter": "codex-cli",
        "target_surface": "AGENTS.md",
        "scope": "workspace",
        "preimage_text": _host(),
        "postimage_sha256": "sha256:" + ("2" * 64),
        "postimage_region_sha256": "sha256:" + ("3" * 64),
        "capsule_id": "sha256:" + ("4" * 64),
        "manifest_sha256": "sha256:" + ("5" * 64),
        "source_state": {"records_digest": "sha256:" + ("6" * 64)},
    }
    receipt = UndoReceipt.for_region(**kwargs)

    assert store.write(receipt) == "created"
    assert store.write(receipt) == "idempotent"
    path = workspace / ".canon" / "undo" / f"{receipt.receipt_id}.json"
    divergent = json.loads(path.read_text(encoding="utf-8"))
    divergent["target_surface"] = "CLAUDE.md"
    path.write_text(canonical_json_text(divergent), encoding="utf-8")

    with pytest.raises(UndoError, match="conflict"):
        store.write(receipt)
