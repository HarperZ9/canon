"""The project identity: stable where the project is the same, different where
it is not, and never carrying a credential or a local path into a receipt."""
from __future__ import annotations

import json

import pytest

from canon.workspace.identity import (
    METHOD_PATH,
    METHOD_REMOTE,
    ProjectIdentityError,
    derive_identity,
    is_project_id,
    normalize_remote,
    parse_remotes,
)

from ._workspace_helpers import init_repo


@pytest.mark.parametrize("url", [
    "https://github.com/HarperZ9/canon.git",
    "https://github.com/HarperZ9/canon",
    "https://github.com/HarperZ9/canon/",
    "git@github.com:HarperZ9/canon.git",
    "ssh://git@github.com:22/HarperZ9/canon.git",
    "https://GitHub.COM/HarperZ9/canon.git",
    "git://github.com/HarperZ9/canon",
])
def test_every_spelling_of_one_remote_normalizes_to_one_key(url):
    assert normalize_remote(url) == "github.com/HarperZ9/canon"


def test_credentials_in_a_remote_never_reach_the_key_or_the_receipt(tmp_path):
    secret = "ghp_" + "a" * 36
    url = f"https://someone:{secret}@github.com/o/r.git?token={secret}"
    assert normalize_remote(url) == "github.com/o/r"
    repo = init_repo(tmp_path / "r", url)
    public = json.dumps(derive_identity(repo).to_public())
    assert secret not in public
    assert "someone" not in public


def test_path_case_is_kept_so_two_case_variants_split_rather_than_merge():
    assert normalize_remote("https://example.org/Team/Repo") != \
        normalize_remote("https://example.org/team/repo")


def test_a_windows_drive_path_is_a_local_remote_not_an_scp_host(tmp_path):
    assert normalize_remote("C:/repos/x.git").startswith("local:")


@pytest.mark.parametrize("bad", ["", "   ", "https:///nopath", "https://host.example/"])
def test_an_unusable_remote_is_refused(bad):
    with pytest.raises(ProjectIdentityError):
        normalize_remote(bad)


def test_origin_wins_and_otherwise_the_first_remote_by_name():
    text = ('[remote "zeta"]\n\turl = https://h.example/z\n'
            '[remote "origin"]\n\turl = "https://h.example/o" \n'
            '[branch "main"]\n\turl = https://h.example/not-a-remote\n')
    assert parse_remotes(text) == {"zeta": "https://h.example/z",
                                   "origin": "https://h.example/o"}


def test_two_clones_of_one_remote_share_an_id(tmp_path):
    a = derive_identity(init_repo(tmp_path / "one", "git@github.com:o/r.git"))
    b = derive_identity(init_repo(tmp_path / "two", "https://github.com/o/r"))
    assert a.project_id == b.project_id
    assert a.method == METHOD_REMOTE
    assert is_project_id(a.project_id)


def test_two_remotes_get_two_ids(tmp_path):
    a = derive_identity(init_repo(tmp_path / "a", "https://github.com/o/a"))
    b = derive_identity(init_repo(tmp_path / "b", "https://github.com/o/b"))
    assert a.project_id != b.project_id


def test_without_a_remote_the_path_decides_and_a_move_changes_the_id(tmp_path):
    first = derive_identity(init_repo(tmp_path / "local-a"))
    moved = derive_identity(init_repo(tmp_path / "moved" / "local-a"))
    assert first.method == METHOD_PATH
    assert first.project_id != moved.project_id
    assert first.label == moved.label == "local-a"
    assert str(tmp_path) not in json.dumps(first.to_public())


def test_a_subdirectory_resolves_to_its_repository(tmp_path):
    repo = init_repo(tmp_path / "r", "https://github.com/o/r")
    nested = repo / "src" / "pkg"
    nested.mkdir(parents=True)
    assert derive_identity(nested).project_id == derive_identity(repo).project_id


def test_a_worktree_reads_the_remote_from_its_common_directory(tmp_path):
    main = init_repo(tmp_path / "main", "https://github.com/o/r")
    gitdir = main / ".git" / "worktrees" / "wt"
    gitdir.mkdir(parents=True)
    (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    worktree = tmp_path / "wt"
    worktree.mkdir()
    (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    assert derive_identity(worktree).project_id == derive_identity(main).project_id


def test_a_directory_with_no_git_is_its_own_root(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    ident = derive_identity(plain)
    assert ident.method == METHOD_PATH
    assert ident.root == plain.resolve()


def test_a_dotfiles_repository_in_home_does_not_claim_projects_below_it(tmp_path):
    home = init_repo(tmp_path / "home", "https://github.com/me/dotfiles")
    one, two = home / "proj-one", home / "proj-two"
    one.mkdir()
    two.mkdir()
    ceilings = frozenset({home.resolve()})
    a = derive_identity(one, ceilings=ceilings)
    b = derive_identity(two, ceilings=ceilings)
    assert a.project_id != b.project_id
    assert a.method == METHOD_PATH
    assert derive_identity(home, ceilings=ceilings).method == METHOD_REMOTE
    # Without the ceiling both would resolve to the dotfiles remote and merge.
    merged = derive_identity(one, ceilings=frozenset())
    assert merged.key == "github.com/me/dotfiles"


def test_a_path_remote_keeps_the_local_path_out_of_the_key(tmp_path):
    repo = init_repo(tmp_path / "r", str(tmp_path / "bare.git"))
    ident = derive_identity(repo)
    assert ident.key.startswith("local-sha256:")
    assert str(tmp_path.name) not in ident.key


def test_an_explicit_remote_overrides_the_config(tmp_path):
    repo = init_repo(tmp_path / "r", "https://github.com/o/old")
    moved = derive_identity(repo, remote_url="https://github.com/o/new")
    assert moved.key == "github.com/o/new"


def test_the_drive_root_ceiling_holds_even_without_a_home_directory(tmp_path, monkeypatch):
    from pathlib import Path

    from canon.workspace import identity

    def no_home():
        raise RuntimeError("no home directory")

    monkeypatch.setattr(identity.Path, "home", staticmethod(no_home))
    start = tmp_path.resolve()
    assert Path(start.anchor) in identity.default_ceilings(start)
