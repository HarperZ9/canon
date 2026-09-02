from __future__ import annotations

import json
from pathlib import Path

from .canonical_json import canonical_json_text, sha256_bytes
from .cli_artifacts import WorkspaceRoot
from .undo_io import (
    checked_receipt_target,
    ensure_undo_root,
    read_regular_file,
    receipt_path,
    replace_file_guarded,
    undo_root_path,
    write_new_or_same,
)
from .undo_receipts import UNDO_RECEIPT_SCHEMA, UndoApplyResult, UndoError, UndoReceipt, valid_receipt_id


class UndoStore:
    def __init__(self, workspace: str | Path | WorkspaceRoot) -> None:
        self._root = workspace.path if type(workspace) is WorkspaceRoot else Path(workspace)

    def write(self, receipt: UndoReceipt) -> str:
        data = canonical_json_text(receipt.to_dict()).encode("utf-8")
        root = ensure_undo_root(self._root)
        return write_new_or_same(receipt_path(root, receipt.receipt_id), data)

    def load(self, receipt_id: str) -> UndoReceipt:
        if not valid_receipt_id(receipt_id):
            raise UndoError("invalid_args")
        root = undo_root_path(self._root)
        data = read_regular_file(receipt_path(root, receipt_id))
        try:
            text = data.decode("utf-8")
            value = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise UndoError("conflict") from None
        if text != canonical_json_text(value):
            raise UndoError("conflict")
        return UndoReceipt.from_dict(value, expected_id=receipt_id)

    def list_metadata(self) -> list[dict[str, object]]:
        root = undo_root_path(self._root)
        if not _exists_or_link(root):
            return []
        return [self.load(path.stem).metadata() for path in sorted(root.glob("undo-*.json"))]

    def apply(self, receipt_id: str, *, workspace: WorkspaceRoot) -> UndoApplyResult:
        receipt = self.load(receipt_id)
        target = checked_receipt_target(receipt, workspace=workspace)
        current = read_regular_file(target)
        current_hash = sha256_bytes(current)
        if current_hash == receipt.preimage_sha256:
            return UndoApplyResult(receipt.receipt_id, receipt.target_path, False, True)
        if current_hash != receipt.postimage_sha256:
            raise UndoError("conflict")
        replace_file_guarded(target, receipt.postimage_sha256, receipt.preimage_text.encode("utf-8"))
        return UndoApplyResult(receipt.receipt_id, receipt.target_path, True, False)


def _exists_or_link(path: Path) -> bool:
    try:
        return path.exists() or path.is_symlink()
    except OSError:
        return True


__all__ = [
    "UNDO_RECEIPT_SCHEMA",
    "UndoApplyResult",
    "UndoError",
    "UndoReceipt",
    "UndoStore",
    "checked_receipt_target",
    "read_regular_file",
    "replace_file_guarded",
]
