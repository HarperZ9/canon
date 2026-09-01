from __future__ import annotations

import hashlib
import json
import stat
import zipfile
from pathlib import Path

import pytest

from canon.canonpack import (
    CanonpackError,
    CanonpackLimits,
    normalize_manifest_path,
    preflight_manifest,
    preflight_zip,
)


def _digest(body: bytes) -> str:
    return "sha256:" + hashlib.sha256(body).hexdigest()


def _manifest_entry(path: str, *, body: bytes = b"{}") -> dict:
    return {
        "path": path,
        "sha256": _digest(body),
        "size": len(body),
        "compressed_size": len(body),
        "compression": "stored",
        "kind": "record",
    }


def _manifest(entries: list[dict]) -> dict:
    return {"schema": "canonpack.manifest/v1", "entries": entries}


def _write_pack(path: Path, manifest: object, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as zf:
        if manifest is not None:
            if isinstance(manifest, bytes):
                zf.writestr("manifest.json", manifest)
            else:
                zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
        for name, body in members.items():
            zf.writestr(name, body)


def _set_encrypted_flag(path: Path, name: str) -> None:
    data = bytearray(path.read_bytes())
    raw_name = name.encode("utf-8")
    pos = 0
    while True:
        pos = data.find(b"PK\x03\x04", pos)
        if pos == -1:
            break
        size = int.from_bytes(data[pos + 26:pos + 28], "little")
        if data[pos + 30:pos + 30 + size] == raw_name:
            flags = int.from_bytes(data[pos + 6:pos + 8], "little") | 1
            data[pos + 6:pos + 8] = flags.to_bytes(2, "little")
        pos += 30 + size
    pos = 0
    while True:
        pos = data.find(b"PK\x01\x02", pos)
        if pos == -1:
            break
        size = int.from_bytes(data[pos + 28:pos + 30], "little")
        extra = int.from_bytes(data[pos + 30:pos + 32], "little")
        comment = int.from_bytes(data[pos + 32:pos + 34], "little")
        if data[pos + 46:pos + 46 + size] == raw_name:
            flags = int.from_bytes(data[pos + 8:pos + 10], "little") | 1
            data[pos + 8:pos + 10] = flags.to_bytes(2, "little")
        pos += 46 + size + extra + comment
    path.write_bytes(data)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "../records/a.json",
        "/abs/a.json",
        "C:/tmp/a.json",
        "//server/share/a.json",
        "records\\a.json",
        "records/a.json:ads",
        "records/./a.json",
        "records/a//b.json",
        "records/a.json\0x",
        "records/a.json\n",
        "records/CON",
        "records/a.",
        "records/a ",
    ],
)
def test_manifest_rejects_unsafe_names(name: str) -> None:
    with pytest.raises(CanonpackError):
        preflight_manifest(_manifest([_manifest_entry(name)]))


def test_normalize_manifest_path_accepts_canonical_relative_posix_name() -> None:
    assert normalize_manifest_path("records/a.json") == "records/a.json"


def test_manifest_rejects_duplicate_case_fold_names() -> None:
    manifest = _manifest([
        _manifest_entry("records/A.json"),
        _manifest_entry("records/a.json"),
    ])

    with pytest.raises(CanonpackError, match="duplicate-path"):
        preflight_manifest(manifest)


def test_manifest_rejects_decompression_ratio() -> None:
    entry = _manifest_entry("records/a.json")
    entry["size"] = 10_000
    entry["compressed_size"] = 1

    with pytest.raises(CanonpackError, match="compression-ratio"):
        preflight_manifest(_manifest([entry]), limits=CanonpackLimits(max_compression_ratio=10))


def test_manifest_rejects_malformed_shapes_and_values() -> None:
    bad_entry = _manifest_entry("records/a.json")
    bad_entry["size"] = True
    bad_entry["sha256"] = "sha256:" + "A" * 64

    with pytest.raises(CanonpackError, match="entry-size"):
        preflight_manifest(_manifest([bad_entry]))
    with pytest.raises(CanonpackError, match="invalid-manifest"):
        preflight_manifest({"schema": "canonpack.manifest/v1", "entries": {}})
    with pytest.raises(CanonpackError, match="invalid-limit"):
        preflight_manifest(_manifest([]), limits=CanonpackLimits(max_entries=True))  # type: ignore[arg-type]


def test_manifest_orders_entries_and_hashes_canonical_manifest() -> None:
    body_a = b"a"
    body_b = b"b"
    first = preflight_manifest(_manifest([
        _manifest_entry("records/b.json", body=body_b),
        _manifest_entry("records/a.json", body=body_a),
    ]))
    second = preflight_manifest(_manifest([
        _manifest_entry("records/a.json", body=body_a),
        _manifest_entry("records/b.json", body=body_b),
    ]))

    assert [entry.path for entry in first.entries] == ["records/a.json", "records/b.json"]
    assert first.manifest_sha256 == second.manifest_sha256
    assert first.ok


def test_zip_preflight_rejects_symlink_entry(tmp_path: Path) -> None:
    pack = tmp_path / "bad.canonpack"
    with zipfile.ZipFile(pack, "w") as zf:
        info = zipfile.ZipInfo("records/link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        zf.writestr(info, "target")

    with pytest.raises(CanonpackError, match="symlink-entry"):
        preflight_zip(pack)


def test_zip_preflight_rejects_special_entry(tmp_path: Path) -> None:
    pack = tmp_path / "bad.canonpack"
    with zipfile.ZipFile(pack, "w") as zf:
        info = zipfile.ZipInfo("records/fifo")
        info.external_attr = (stat.S_IFIFO | 0o644) << 16
        zf.writestr(info, b"")

    with pytest.raises(CanonpackError, match="special-entry"):
        preflight_zip(pack)


def test_zip_preflight_checks_digest_without_extracting(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = tmp_path / "ok.canonpack"
    body = b'{"canon_schema":"canon.record/v1"}'
    _write_pack(pack, _manifest([_manifest_entry("records/a.json", body=body)]), {"records/a.json": body})

    def fail_extract(*args: object, **kwargs: object) -> None:
        raise AssertionError("preflight_zip must not extract archive members")

    monkeypatch.setattr(zipfile.ZipFile, "extract", fail_extract)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", fail_extract)

    result = preflight_zip(pack)

    assert result.ok
    assert result.entries[0].path == "records/a.json"


def test_zip_preflight_rejects_member_ratio_before_opening_members(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pack = tmp_path / "bomb.canonpack"
    body = b"0" * 50_000
    manifest = _manifest([_manifest_entry("records/a.json", body=body)])
    manifest["entries"][0]["compressed_size"] = 66
    manifest["entries"][0]["compression"] = "deflated"
    with zipfile.ZipFile(pack, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True), compress_type=zipfile.ZIP_STORED)
        zf.writestr("records/a.json", body, compress_type=zipfile.ZIP_DEFLATED)

    def fail_open(*args: object, **kwargs: object) -> None:
        raise AssertionError("ratio preflight must reject before ZipFile.open")

    monkeypatch.setattr(zipfile.ZipFile, "open", fail_open)

    with pytest.raises(CanonpackError, match="compression-ratio"):
        preflight_zip(pack, limits=CanonpackLimits(max_compression_ratio=2))


def test_zip_preflight_rejects_malformed_manifest_json_and_duplicate_keys(tmp_path: Path) -> None:
    pack = tmp_path / "bad-json.canonpack"
    _write_pack(pack, b'{"schema":"canonpack.manifest/v1","schema":"x","entries":[]}', {})

    with pytest.raises(CanonpackError, match="duplicate-json-key"):
        preflight_zip(pack)


def test_zip_preflight_rejects_extra_and_missing_members(tmp_path: Path) -> None:
    extra = tmp_path / "extra.canonpack"
    body = b"{}"
    _write_pack(extra, _manifest([_manifest_entry("records/a.json", body=body)]), {
        "records/a.json": body,
        "records/b.json": body,
    })
    with pytest.raises(CanonpackError, match="extra-member"):
        preflight_zip(extra)

    missing = tmp_path / "missing.canonpack"
    _write_pack(missing, _manifest([_manifest_entry("records/a.json", body=body)]), {})
    with pytest.raises(CanonpackError, match="missing-member"):
        preflight_zip(missing)


def test_zip_preflight_rejects_duplicate_missing_and_wrong_manifest_members(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.canonpack"
    with zipfile.ZipFile(duplicate, "w") as zf:
        zf.writestr("manifest.json", "{}")
        with pytest.warns(UserWarning, match="Duplicate name"):
            zf.writestr("manifest.json", "{}")
    with pytest.raises(CanonpackError, match="multiple-manifest"):
        preflight_zip(duplicate)

    missing = tmp_path / "no-manifest.canonpack"
    _write_pack(missing, None, {"records/a.json": b"{}"})
    with pytest.raises(CanonpackError, match="missing-manifest"):
        preflight_zip(missing)


def test_zip_preflight_rejects_central_case_duplicates_encryption_and_unsupported_compression(tmp_path: Path) -> None:
    body = b"{}"
    duplicate = tmp_path / "dupe.canonpack"
    _write_pack(duplicate, _manifest([_manifest_entry("records/A.json", body=body)]), {
        "records/A.json": body,
        "records/a.json": body,
    })
    with pytest.raises(CanonpackError, match="duplicate-path"):
        preflight_zip(duplicate)

    encrypted = tmp_path / "encrypted.canonpack"
    _write_pack(encrypted, _manifest([_manifest_entry("records/a.json", body=body)]), {"records/a.json": body})
    _set_encrypted_flag(encrypted, "records/a.json")
    with pytest.raises(CanonpackError, match="encrypted-entry"):
        preflight_zip(encrypted)

    unsupported = tmp_path / "unsupported.canonpack"
    with zipfile.ZipFile(unsupported, "w") as zf:
        zf.writestr("manifest.json", json.dumps(_manifest([])), compress_type=zipfile.ZIP_STORED)
        zf.writestr("records/a.json", body, compress_type=zipfile.ZIP_BZIP2)
    with pytest.raises(CanonpackError, match="unsupported-compression"):
        preflight_zip(unsupported)


def test_zip_preflight_rejects_metadata_mismatch_and_digest_tamper(tmp_path: Path) -> None:
    body = b"{}"
    mismatch = tmp_path / "mismatch.canonpack"
    manifest = _manifest([_manifest_entry("records/a.json", body=body)])
    manifest["entries"][0]["compression"] = "deflated"
    _write_pack(mismatch, manifest, {"records/a.json": body})
    with pytest.raises(CanonpackError, match="metadata-mismatch"):
        preflight_zip(mismatch)

    tampered = tmp_path / "tampered.canonpack"
    _write_pack(tampered, _manifest([_manifest_entry("records/a.json", body=b"expect")]), {"records/a.json": b"actual"})
    with pytest.raises(CanonpackError, match="digest-mismatch"):
        preflight_zip(tampered)


def test_zip_preflight_rejects_archive_symlink_before_opening(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target.canonpack"
    target.write_bytes(b"not used")
    link = tmp_path / "link.canonpack"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("current platform or privileges do not allow symlinks")

    def fail_init(*args: object, **kwargs: object) -> None:
        raise AssertionError("archive path guard must run before ZipFile opens")

    monkeypatch.setattr(zipfile.ZipFile, "__init__", fail_init)

    with pytest.raises(CanonpackError, match="archive-reparse"):
        preflight_zip(link)
