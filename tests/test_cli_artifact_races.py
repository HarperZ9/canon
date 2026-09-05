from __future__ import annotations

from pathlib import Path

import pytest

import canon.cli_artifacts as cli_artifacts
import canon.source_safe_read as source_safe_read
from canon.cli_artifacts import ArtifactError, checked_workspace, read_source_file


def _swap_dir_to_symlink(directory: Path, target: Path, displaced: Path) -> None:
    try:
        directory.rename(displaced)
        try:
            directory.symlink_to(target, target_is_directory=True)
        except OSError:
            displaced.rename(directory)
            pytest.skip("current platform or privileges do not allow directory symlinks")
    except OSError:
        pytest.skip("current platform cannot swap the source parent directory")


def _restore_swapped_dir(directory: Path, displaced: Path) -> None:
    if directory.is_symlink():
        directory.unlink()
    if displaced.exists():
        displaced.rename(directory)


def test_source_read_does_not_follow_nested_parent_swap_outside_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_dir = tmp_path / "workspace"
    source_parent = workspace_dir / "inputs"
    outside_parent = tmp_path / "outside-inputs"
    displaced = tmp_path / "displaced-inputs"
    source_parent.mkdir(parents=True)
    outside_parent.mkdir()
    source_path = source_parent / "records.jsonl"
    inside_bytes = b'{"inside":true}\n'
    outside_bytes = b'{"outside":true}\n'
    source_path.write_bytes(inside_bytes)
    (outside_parent / "records.jsonl").write_bytes(outside_bytes)
    workspace = checked_workspace(str(workspace_dir))
    real_resolve = cli_artifacts.resolve_under_root
    attempted = False

    def swap_after_validation(path: object, **kwargs: object) -> Path:
        nonlocal attempted
        resolved = real_resolve(path, **kwargs)
        if resolved == source_path.resolve() and not attempted:
            attempted = True
            _swap_dir_to_symlink(source_parent, outside_parent, displaced)
        return resolved

    monkeypatch.setattr(cli_artifacts, "resolve_under_root", swap_after_validation)

    try:
        try:
            result = read_source_file("inputs/records.jsonl", workspace=workspace)
        except ArtifactError as exc:
            assert exc.code == "unsafe_path"
        else:
            assert result.data != outside_bytes
            assert result.data == inside_bytes
    finally:
        _restore_swapped_dir(source_parent, displaced)

    assert attempted


def test_source_read_fails_closed_when_safe_backend_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    source_path = workspace_dir / "records.jsonl"
    source_path.write_bytes(b'{"inside":true}\n')
    workspace = checked_workspace(str(workspace_dir))
    monkeypatch.setattr(source_safe_read, "_safe_backend_supported", lambda: False)

    with pytest.raises(ArtifactError) as caught:
        read_source_file("records.jsonl", workspace=workspace)

    assert caught.value.code == "unsafe_path"


def test_windows_source_read_rejects_replaced_relative_open_before_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if cli_artifacts.os.name != "nt":
        pytest.skip("Windows handle-relative primitive replacement is platform-specific")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    source_path = workspace_dir / "records.jsonl"
    source_path.write_bytes(b'{"inside":true}\n')
    workspace = checked_workspace(str(workspace_dir))
    calls: list[str] = []

    def forbidden_create(*args: object, **kwargs: object) -> int:
        del args, kwargs
        calls.append("nt_create_relative")
        raise OSError("relative open primitive was replaced")

    monkeypatch.setattr(source_safe_read._win, "nt_create_relative", forbidden_create)

    with pytest.raises(ArtifactError) as caught:
        read_source_file("records.jsonl", workspace=workspace)

    assert caught.value.code == "unsafe_path"
    assert calls == []


def test_windows_source_read_rejects_spoofed_reader_replacement_before_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if cli_artifacts.os.name != "nt":
        pytest.skip("Windows primitive replacement is platform-specific")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "records.jsonl").write_bytes(b'{"inside":true}\n')
    workspace = checked_workspace(str(workspace_dir))
    calls: list[str] = []

    def hostile_read(handle: int, size: int) -> bytes:
        del handle
        calls.append("read_file")
        return b"x" * (size - 1)

    hostile_read.__module__ = source_safe_read._win.__name__
    monkeypatch.setattr(source_safe_read._win, "read_file", hostile_read)

    with pytest.raises(ArtifactError) as caught:
        read_source_file("records.jsonl", workspace=workspace)

    assert caught.value.code == "unsafe_path"
    assert calls == []


def test_windows_source_read_rejects_replaced_support_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if cli_artifacts.os.name != "nt":
        pytest.skip("Windows support probe is platform-specific")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "records.jsonl").write_bytes(b'{"inside":true}\n')
    workspace = checked_workspace(str(workspace_dir))
    monkeypatch.setattr(source_safe_read._win, "supported", None)

    with pytest.raises(ArtifactError) as caught:
        read_source_file("records.jsonl", workspace=workspace)

    assert caught.value.code == "unsafe_path"


@pytest.mark.parametrize(
    ("module", "values", "name"),
    (
        (source_safe_read._win, source_safe_read._WIN_VALUES, "FILE_SHARE_READ"),
        (source_safe_read.os, source_safe_read._POSIX_FLAGS, "O_RDONLY"),
    ),
)
def test_backend_constant_check_does_not_invoke_replacement_equality(
    monkeypatch: pytest.MonkeyPatch,
    module: object,
    values: dict[str, object],
    name: str,
) -> None:
    calls: list[str] = []

    class HostileConstant:
        def __eq__(self, other: object) -> bool:
            del other
            calls.append(name)
            raise RuntimeError("hostile equality was invoked")

    monkeypatch.setattr(module, name, HostileConstant())

    assert source_safe_read._constant_bound(module, values, name) is False
    assert calls == []


@pytest.mark.parametrize("name", ("open", "fstat", "pread", "close"))
def test_posix_backend_capability_rejects_replaced_primitive(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setattr(source_safe_read.os, name, lambda *args, **kwargs: None, raising=False)

    assert source_safe_read._posix_primitive_bound(name) is False


@pytest.mark.parametrize("name", ("fstat", "pread"))
def test_posix_source_read_rejects_replaced_primitive_before_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    if cli_artifacts.os.name == "nt":
        pytest.skip("POSIX primitive replacement is platform-specific")

    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / "records.jsonl").write_bytes(b'{"inside":true}\n')
    workspace = checked_workspace(str(workspace_dir))
    calls: list[str] = []

    def forbidden(*args: object, **kwargs: object) -> object:
        del args, kwargs
        calls.append(name)
        raise OSError(f"{name} primitive was replaced")

    monkeypatch.setattr(source_safe_read.os, name, forbidden)

    with pytest.raises(ArtifactError) as caught:
        read_source_file("records.jsonl", workspace=workspace)

    assert caught.value.code == "unsafe_path"
    assert calls == []
