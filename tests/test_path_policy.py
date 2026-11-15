from __future__ import annotations

import os
from pathlib import Path

import pytest

from canon.path_policy import (
    PathPolicyError,
    classify_protected_path,
    assert_not_protected,
    assert_operational_surface_path,
    assert_operational_vault_path,
    is_reparse_point,
    is_windows_ads_path,
    resolve_under_root,
)


def test_resolve_under_root_rejects_root_itself(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="root-target"):
        resolve_under_root(tmp_path, root=tmp_path)


def test_resolve_under_root_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="outside-root"):
        resolve_under_root(tmp_path / ".." / "escape.md", root=tmp_path)


def test_resolve_under_root_rejects_absolute_outside_path(tmp_path: Path) -> None:
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    with pytest.raises(PathPolicyError, match="outside-root"):
        resolve_under_root(outside / "note.md", root=root)


def test_resolve_under_root_rejects_missing_target_when_required(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="missing-target"):
        resolve_under_root(tmp_path / "missing.md", root=tmp_path, must_exist=True)


def test_resolve_under_root_allows_missing_parents_when_not_required(tmp_path: Path) -> None:
    target = tmp_path / "new" / "nested" / "note.md"
    assert resolve_under_root(target, root=tmp_path) == target.resolve()


@pytest.mark.parametrize(
    "name",
    [".env", ".env.local", "id_rsa", "id_ed25519", "cookies.sqlite", "Login Data"],
)
def test_assert_not_protected_rejects_sensitive_file_names(
    tmp_path: Path,
    name: str,
) -> None:
    with pytest.raises(PathPolicyError, match="protected-path"):
        assert_not_protected(tmp_path / name)


@pytest.mark.parametrize(
    "relative",
    [
        ".ssh/id_rsa",
        ".aws/credentials",
        ".config/gcloud/application_default_credentials.json",
    ],
)
def test_assert_not_protected_rejects_sensitive_directories(
    tmp_path: Path,
    relative: str,
) -> None:
    with pytest.raises(PathPolicyError, match="protected-path"):
        assert_not_protected(tmp_path / Path(relative))


def test_classify_protected_path_returns_deterministic_violations(
    tmp_path: Path,
) -> None:
    target = tmp_path / ".SSH" / "ID_RSA"

    first = classify_protected_path(target)
    second = classify_protected_path(target)

    assert first == second
    assert len(first) >= 2
    assert {v.code for v in first} == {"protected-path"}


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        (r"C:.env", "protected name"),
        (r"C:.ssh\config", "protected directory"),
        (r"C:.aws\credentials", "protected directory"),
    ],
)
def test_classify_protected_path_handles_leading_windows_drive_prefix(
    path: str,
    reason: str,
) -> None:
    violations = classify_protected_path(path)
    assert violations
    assert {v.code for v in violations} == {"protected-path"}
    assert any(v.reason == reason for v in violations)


def test_ads_detection_rejects_named_stream() -> None:
    assert is_windows_ads_path("AGENTS.md:secret")
    with pytest.raises(PathPolicyError, match="ads"):
        resolve_under_root("AGENTS.md:secret", root=".")


@pytest.mark.parametrize(
    "path",
    [
        "C:/tmp/file.txt",
        r"C:\tmp\file.txt",
        "C:relative-file.txt",
        r"\\server\share\file.txt",
    ],
)
def test_ads_detection_does_not_misclassify_drive_or_unc_paths(path: str) -> None:
    assert not is_windows_ads_path(path)


@pytest.mark.parametrize(
    "path",
    [
        "C:/tmp/file.txt:secret",
        r"C:\tmp\file.txt:secret",
        "C:relative-file.txt:secret",
        r"\\server\share\file.txt:secret",
    ],
)
def test_ads_detection_finds_streams_after_drive_or_unc_prefix(path: str) -> None:
    assert is_windows_ads_path(path)


def test_drive_qualified_path_is_outside_root_not_ads(tmp_path: Path) -> None:
    assert not is_windows_ads_path("C:/tmp/file.txt")
    with pytest.raises(PathPolicyError, match="outside-root"):
        resolve_under_root("C:/tmp/file.txt", root=tmp_path)


def test_symlink_file_refused_and_reject_reparse_false_allows_it(
    tmp_path: Path,
) -> None:
    target = tmp_path / "root" / "real.md"
    target.parent.mkdir()
    target.write_text("body", encoding="utf-8")
    link = tmp_path / "root" / "link.md"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")

    assert is_reparse_point(link)
    with pytest.raises(PathPolicyError, match="reparse"):
        resolve_under_root(link, root=tmp_path / "root")
    assert resolve_under_root(
        link,
        root=tmp_path / "root",
        reject_reparse=False,
    ) == target.resolve()


def test_reparse_detection_fails_closed_without_windows_attributes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    if os.name != "nt":
        pytest.skip("Windows-only reparse attribute fail-closed probe")

    class BareStat:
        pass

    target = tmp_path / "opaque"
    target.write_text("body", encoding="utf-8")
    monkeypatch.setattr(Path, "is_symlink", lambda self: False)
    monkeypatch.setattr(Path, "lstat", lambda self: BareStat())

    assert is_reparse_point(target)


def test_symlink_parent_refused_before_operational_write(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "root" / "link"
    link.parent.mkdir()
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(PathPolicyError, match="reparse"):
        assert_operational_surface_path(link / "AGENTS.md", root=tmp_path / "root")


def test_reject_reparse_false_still_enforces_resolved_root(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "root" / "link"
    link.parent.mkdir()
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow directory symlinks")

    with pytest.raises(PathPolicyError, match="outside-root"):
        resolve_under_root(link / "note.md", root=tmp_path / "root", reject_reparse=False)


def test_must_exist_rejects_broken_symlink_when_reparse_allowed(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    link = root / "broken.md"
    try:
        link.symlink_to(root / "missing.md")
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")

    with pytest.raises(PathPolicyError, match="missing-target"):
        resolve_under_root(link, root=root, must_exist=True, reject_reparse=False)


def test_operational_surface_rejects_protected_paths(tmp_path: Path) -> None:
    target = tmp_path / "surface" / ".env"
    target.parent.mkdir()
    target.write_text("SECRET=1", encoding="utf-8")

    with pytest.raises(PathPolicyError, match="protected-path"):
        assert_operational_surface_path(target, root=tmp_path / "surface")


def test_operational_vault_allows_regular_scope_note(tmp_path: Path) -> None:
    target = tmp_path / "vault" / "workspace" / "note.md"
    target.parent.mkdir(parents=True)
    target.write_text("body", encoding="utf-8")

    assert assert_operational_vault_path(target, vault=tmp_path / "vault") == target.resolve()


def test_operational_vault_rejects_hub_root_directory(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    with pytest.raises(PathPolicyError, match="root-target"):
        assert_operational_vault_path(vault, vault=vault)


@pytest.mark.parametrize("bad", [None, 123])
def test_resolve_under_root_rejects_non_path_inputs(
    tmp_path: Path,
    bad: object,
) -> None:
    with pytest.raises(PathPolicyError, match="invalid-path"):
        resolve_under_root(bad, root=tmp_path)  # type: ignore[arg-type]


def test_resolve_under_root_rejects_non_path_root() -> None:
    with pytest.raises(PathPolicyError, match="invalid-root"):
        resolve_under_root("note.md", root=None)  # type: ignore[arg-type]


def test_resolve_under_root_rejects_nul_path(tmp_path: Path) -> None:
    with pytest.raises(PathPolicyError, match="invalid-path"):
        resolve_under_root("bad\0name", root=tmp_path)


def test_assert_not_protected_rejects_non_path_input() -> None:
    with pytest.raises(PathPolicyError, match="invalid-path"):
        assert_not_protected(None)  # type: ignore[arg-type]
