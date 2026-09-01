from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from canon.canonical_json import is_sha256_ref
from canon.omission import validate_omission
from canon.secret_quarantine import (
    SecretQuarantineError,
    quarantine_path,
    quarantine_text,
    scan_text,
)
from canon.transform import validate_transform_receipt


def _openai_key() -> str:
    return "sk-" + "live-" + "abcdefghijklmnopqrstuvwxyz012345"


def _aws_key() -> str:
    return "AKIA" + ("A" * 16)


def _private_key() -> str:
    return "-----BEGIN " + "PRIVATE KEY-----\nabc\n-----END " + "PRIVATE KEY-----"


def _ssn() -> str:
    return "123" + "-45-" + "6789"


def _email() -> str:
    return "jane" + "@example.com"


def _serialized_result(value: object) -> str:
    payload = asdict(value)
    if hasattr(value, "omissions"):
        payload["omissions_dicts"] = [item.to_dict() for item in value.omissions]
    if hasattr(value, "receipts"):
        payload["receipt_dicts"] = [item.to_dict() for item in value.receipts]
    return "\n".join((repr(value), repr(payload), json.dumps(payload, sort_keys=True)))


def test_secret_canary_is_not_serialized_in_quarantine_result() -> None:
    canary = _openai_key()
    result = quarantine_text(f"token={canary}", source_id="fixture-secret", critical=False)

    assert result.safe_text is None
    assert len(result.findings) == 1
    assert result.findings[0].code == "openai-api-key"
    assert is_sha256_ref(result.findings[0].sha256)
    assert result.reason_codes == ("secret",)
    assert canary not in _serialized_result(result)

    assert len(result.omissions) == 1
    omission = result.omissions[0]
    assert omission.reason == "secret"
    assert omission.count == 1
    assert omission.affected_ids == ("fixture-secret",)
    assert omission.affected_source_refs == ("fixture-secret",)
    assert omission.critical is False
    assert omission.decision == "omitted"
    assert validate_omission(omission) == []

    assert len(result.receipts) == 1
    receipt = result.receipts[0]
    assert receipt.transform == "redaction"
    assert receipt.input_refs == ("fixture-secret",)
    assert receipt.omissions == (omission,)
    assert receipt.lossy is True
    assert validate_transform_receipt(receipt) == []


def test_scan_text_reports_multiple_overlapping_findings_in_source_order() -> None:
    aws_email = _aws_key() + "@example.com"
    text = f"{aws_email} owner {_email()} ssn {_ssn()} token {_openai_key()}"

    findings = scan_text(text, source_id="fixture-pii")

    assert [f.code for f in findings] == [
        "aws-access-key",
        "email",
        "email",
        "ssn",
        "openai-api-key",
    ]
    assert [(f.start, f.end, f.code) for f in findings] == sorted(
        (f.start, f.end, f.code) for f in findings
    )
    assert len({(f.code, f.start, f.end) for f in findings}) == len(findings)
    serialized = "\n".join(repr(f) + str(asdict(f)) for f in findings)
    for raw in (aws_email, _email(), _ssn(), _openai_key()):
        assert raw not in serialized
    assert all(is_sha256_ref(f.sha256) for f in findings)


def test_critical_secret_error_does_not_expose_secret() -> None:
    canary = _private_key()

    with pytest.raises(SecretQuarantineError) as excinfo:
        quarantine_text(canary, source_id="fixture-key", critical=True)

    message = str(excinfo.value)
    assert "critical-secret" in message
    assert canary not in message


def test_clear_text_passthrough_uses_original_text_identity() -> None:
    clear = "ordinary continuity note with no quarantined material"

    result = quarantine_text(clear, source_id="fixture-clear")

    assert result.safe_text is clear
    assert result.findings == ()
    assert result.omissions == ()
    assert result.receipts == ()
    assert result.reason_codes == ()


def test_quarantine_path_refuses_protected_path_without_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protected = tmp_path / ".aws" / "credentials"
    read_attempts: list[Path] = []

    def fail_read(self: Path, *args: object, **kwargs: object) -> bytes:
        read_attempts.append(self)
        raise AssertionError("content read")

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    monkeypatch.setattr(Path, "read_text", fail_read)

    result = quarantine_path(protected, source_id="aws-config", critical=False)

    assert read_attempts == []
    assert result.safe_text is None
    assert len(result.findings) == 1
    assert result.findings[0].code == "protected-path"
    assert result.findings[0].start == 0
    assert result.findings[0].end == 0
    assert is_sha256_ref(result.findings[0].sha256)
    assert _openai_key() not in _serialized_result(result)


def test_relative_path_inside_protected_cwd_is_quarantined_without_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    protected = tmp_path / ".ssh"
    protected.mkdir()
    (protected / "note.txt").write_text(f"token={_openai_key()}", encoding="utf-8")
    read_attempts: list[Path] = []

    def fail_read(self: Path, *args: object, **kwargs: object) -> bytes:
        read_attempts.append(self)
        raise AssertionError("content read")

    monkeypatch.chdir(protected)
    monkeypatch.setattr(Path, "read_bytes", fail_read)
    monkeypatch.setattr(Path, "read_text", fail_read)

    result = quarantine_path("note.txt", source_id="relative-protected")

    assert read_attempts == []
    assert result.safe_text is None
    assert [finding.code for finding in result.findings] == ["protected-path"]


def test_symlink_ancestor_is_rejected_without_reading(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "note.txt").write_text("clear text", encoding="utf-8")
    link_dir = tmp_path / "link-dir"
    try:
        link_dir.symlink_to(real_dir, target_is_directory=True)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")
    read_attempts: list[Path] = []

    def fail_read(self: Path, *args: object, **kwargs: object) -> bytes:
        read_attempts.append(self)
        raise AssertionError("content read")

    monkeypatch.setattr(Path, "read_bytes", fail_read)
    monkeypatch.setattr(Path, "read_text", fail_read)

    with pytest.raises(SecretQuarantineError, match="reparse-path"):
        quarantine_path(link_dir / "note.txt", source_id="symlink-ancestor")
    assert read_attempts == []


def test_path_resolution_errors_fail_closed_without_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "note.txt"
    source.write_text("clear text", encoding="utf-8")
    read_attempts: list[Path] = []

    def fail_resolve(self: Path, *args: object, **kwargs: object) -> Path:
        raise OSError("resolution failed")

    def fail_read(self: Path, *args: object, **kwargs: object) -> bytes:
        read_attempts.append(self)
        raise AssertionError("content read")

    monkeypatch.setattr(Path, "resolve", fail_resolve)
    monkeypatch.setattr(Path, "read_bytes", fail_read)
    monkeypatch.setattr(Path, "read_text", fail_read)

    with pytest.raises(SecretQuarantineError, match="invalid-path"):
        quarantine_path(source, source_id="resolve-error")
    assert read_attempts == []


def test_quarantine_path_scans_unprotected_utf8_file(tmp_path: Path) -> None:
    canary = _openai_key()
    source = tmp_path / "note.txt"
    source.write_text(f"token={canary}", encoding="utf-8")

    result = quarantine_path(source, source_id="note-file")

    assert result.safe_text is None
    assert [finding.code for finding in result.findings] == ["openai-api-key"]
    assert canary not in _serialized_result(result)


def test_multi_finding_quarantine_uses_one_source_level_omission() -> None:
    text = f"{_openai_key()} {_email()} {_ssn()}"

    result = quarantine_text(text, source_id="multi-source")

    assert len(result.findings) == 3
    omission = result.omissions[0]
    assert omission.count == 1
    assert omission.affected_ids == ("multi-source",)
    assert omission.affected_source_refs == ("multi-source",)
    assert validate_omission(omission) == []
    assert validate_transform_receipt(result.receipts[0]) == []
    assert _openai_key() not in _serialized_result(result)


def test_invalid_text_source_and_path_fail_closed_without_raw_leak() -> None:
    source_canary = _openai_key()

    with pytest.raises(SecretQuarantineError, match="invalid-text"):
        scan_text(object(), source_id="fixture")  # type: ignore[arg-type]

    with pytest.raises(SecretQuarantineError, match="invalid-source-id"):
        quarantine_text("clear", source_id="")

    with pytest.raises(SecretQuarantineError) as excinfo:
        quarantine_text("clear", source_id=source_canary)
    assert "invalid-source-id" in str(excinfo.value)
    assert source_canary not in str(excinfo.value)

    with pytest.raises(SecretQuarantineError, match="invalid-path"):
        quarantine_path(123, source_id="fixture")  # type: ignore[arg-type]


def test_non_utf8_text_source_and_path_fail_closed() -> None:
    non_utf8 = "\udcff"

    with pytest.raises(SecretQuarantineError, match="invalid-text"):
        scan_text(non_utf8, source_id="fixture")

    with pytest.raises(SecretQuarantineError, match="invalid-source-id"):
        quarantine_text("clear", source_id=non_utf8)

    with pytest.raises(SecretQuarantineError, match="invalid-path"):
        quarantine_path(non_utf8, source_id="fixture")


def test_unreadable_binary_and_invalid_utf8_paths_fail_closed(tmp_path: Path) -> None:
    invalid_utf8 = tmp_path / "invalid.txt"
    invalid_utf8.write_bytes(b"\xff")
    binary = tmp_path / "binary.txt"
    binary.write_bytes(b"clear\x00text")

    with pytest.raises(SecretQuarantineError, match="unreadable-source"):
        quarantine_path(tmp_path, source_id="directory")

    with pytest.raises(SecretQuarantineError, match="invalid-utf8-source"):
        quarantine_path(invalid_utf8, source_id="invalid-utf8")

    with pytest.raises(SecretQuarantineError, match="binary-source"):
        quarantine_path(binary, source_id="binary")


def test_symlink_path_fails_closed_before_content_read(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    link = tmp_path / "link.txt"
    target.write_text("clear text", encoding="utf-8")
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    with pytest.raises(SecretQuarantineError, match="reparse-path"):
        quarantine_path(link, source_id="link-file")
