"""The import project check resolves a session's working directory to the
checkout it sits in before comparing identities. A directory in this
project's own repository (its root, a subdirectory, a sibling worktree) is
this project under a `--remote` override too, and a subdirectory of a folder
with no `.git` is that folder's project. A nested repository and a
submodule stay other projects. Every session here is synthetic."""
from __future__ import annotations

import io
import json

import pytest

from canon.cli import run_cli
from canon.exit_codes import EX_OK
from canon.workspace.identity import derive_identity
from canon.workspace.import_common import ImportRefused
from canon.workspace.import_write import import_session
from canon.workspace.store import ProjectStore

from ._workspace_helpers import init_repo

REMOTE = "https://github.com/o/r"


def _session(tmp_path, cwd, name="s.jsonl"):
    row = {"type": "user", "uuid": "u1", "parentUuid": None, "isSidechain": False,
           "cwd": str(cwd), "sessionId": "5b0c7f1e-2a3b-4c5d-8e9f-0a1b2c3d4e5f",
           "message": {"role": "user", "content": "TODO: fix the parser"}}
    path = tmp_path / name
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")
    return path


def _cli_import(tmp_path, session, workspace, *extra):
    stdout, stderr = io.StringIO(), io.StringIO()
    code = run_cli(["--json", "workspace", "import", "--from", "claude-code", str(session),
                    "--workspace", str(workspace), "--store", str(tmp_path / "store"),
                    "--dry-run", *extra], stdin=None, stdout=stdout, stderr=stderr,
                   environ={})
    return code, json.loads(stdout.getvalue())


def _check(tmp_path, workspace, cwd, remote=None):
    ident = derive_identity(workspace, remote_url=remote)
    store = ProjectStore(tmp_path / "store", ident)
    report = import_session(ident, store, str(_session(tmp_path, cwd)),
                            source_format="claude-code", dry_run=True)
    return report["project_check"]


def test_a_session_at_the_root_of_a_repository_named_by_remote_is_this_project(tmp_path):
    repo = init_repo(tmp_path / "repo")
    code, payload = _cli_import(tmp_path, _session(tmp_path, repo), repo, "--remote", REMOTE)
    assert code == EX_OK, payload
    assert payload["data"]["report"]["project_check"] == {"status": "match",
                                                          "by": "working_directory"}


def test_a_subdirectory_of_a_repository_named_by_remote_is_this_project(tmp_path):
    repo = init_repo(tmp_path / "repo")
    (repo / "src").mkdir()
    assert _check(tmp_path, repo, repo / "src", REMOTE)["status"] == "match"


def test_a_subdirectory_of_a_folder_with_no_git_is_that_folders_project(tmp_path):
    plain = tmp_path / "plain"
    (plain / "src").mkdir(parents=True)
    code, payload = _cli_import(tmp_path, _session(tmp_path, plain / "src"), plain)
    assert code == EX_OK, payload
    assert payload["data"]["report"]["project_check"]["status"] == "match"


def test_a_sibling_worktree_is_this_project_under_a_remote_override(tmp_path):
    repo = init_repo(tmp_path / "repo")
    gitdir = repo / ".git" / "worktrees" / "feature"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = tmp_path / "feature"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    assert _check(tmp_path, repo, worktree, REMOTE)["status"] == "match"


def test_the_override_does_not_reach_a_nested_repository(tmp_path):
    repo = init_repo(tmp_path / "repo")
    inner = init_repo(repo / "vendor" / "inner")
    with pytest.raises(ImportRefused) as err:
        _check(tmp_path, repo, inner, REMOTE)
    assert err.value.code == "isolation_refused"


def test_a_nested_repository_inside_a_folder_with_no_git_is_another_project(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    inner = init_repo(plain / "vendor" / "inner", "https://github.com/o/inner")
    with pytest.raises(ImportRefused) as err:
        _check(tmp_path, plain, inner)
    assert err.value.code == "isolation_refused"


def test_a_submodule_stays_another_project_under_a_remote_override(tmp_path):
    repo = init_repo(tmp_path / "repo")
    module_git = repo / ".git" / "modules" / "lib"
    module_git.mkdir(parents=True)
    (module_git / "config").write_text('[remote "origin"]\n\turl = https://github.com/o/lib\n',
                                       encoding="utf-8")
    sub = repo / "lib"
    sub.mkdir()
    (sub / ".git").write_text("gitdir: ../.git/modules/lib\n", encoding="utf-8")
    with pytest.raises(ImportRefused):
        _check(tmp_path, repo, sub, REMOTE)
