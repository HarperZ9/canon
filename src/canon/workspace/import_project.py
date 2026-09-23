"""import_project.py -- does a session belong to this project, and which of its
files are this project's.

The source names its repository (Codex `git.repository_url`) or its working
directories (`cwd`). A repository URL is compared with this project's key. A
working directory is compared by project identity, not by path prefix: a
nested repository or a submodule sits inside this checkout's root but is its
own project, and a sibling worktree sits outside the root but is this one. The
identity of a working directory is derived without writing anything, so a
nested repository with no remote gets no nonce from an import. A working
directory that no longer exists falls back to containment, and a `.git` entry
between it and the root makes it another project.
"""
from __future__ import annotations

import os
from pathlib import Path

from canon.workspace.identity import (
    METHOD_REMOTE,
    ProjectIdentity,
    ProjectIdentityError,
    derive_identity,
    normalize_remote,
)


def _norm(path: str | Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("\\/") + os.sep)


def _nested_repo_between(path: str, root: str) -> bool:
    """True when a directory strictly between `path` and `root` (or `path`
    itself) holds a `.git` entry, so the path belongs to another repository."""
    current = Path(path)
    root_path = Path(root)
    while _norm(current) != _norm(root_path) and current.parent != current:
        if (current / ".git").exists():
            return True
        current = current.parent
    return False


def _cwd_status(cwd: str, identity: ProjectIdentity) -> str:
    if os.path.isdir(cwd):
        try:
            other = derive_identity(cwd, write_nonce=False)
        except ProjectIdentityError:
            return "mismatch"
        return "match" if other.project_id == identity.project_id else "mismatch"
    root = _norm(identity.root)
    target = _norm(cwd)
    if _inside(target, root) and not _nested_repo_between(target, root):
        return "match"
    return "mismatch"


def project_check(identity: ProjectIdentity, extraction) -> dict:
    """Whether the source says it belongs to this project. The report names
    the check and never a local path."""
    url = extraction.repository_url
    if url and identity.method == METHOD_REMOTE:
        try:
            key = normalize_remote(url)
        except ProjectIdentityError:
            key = None
        if key and not key.startswith("local:"):
            status = "match" if key == identity.key else "mismatch"
            return {"status": status, "by": "repository_url", "source_key": key}
    if extraction.cwds:
        statuses = {_cwd_status(c, identity) for c in extraction.cwds}
        status = "mismatch" if "mismatch" in statuses else "match"
        return {"status": status, "by": "working_directory"}
    return {"status": "unverified", "by": "none"}


def relative_area(path: str, identity: ProjectIdentity) -> str | None:
    """A file path as a path inside the project, or None when it is outside
    the root or inside a nested repository under it."""
    root = _norm(identity.root)
    target = os.path.normpath(path if os.path.isabs(path) else os.path.join(root, path))
    normal = os.path.normcase(target)
    if not _inside(normal, root) or normal == root:
        return None
    if _nested_repo_between(os.path.dirname(normal), root):
        return None
    return os.path.relpath(target, str(identity.root)).replace("\\", "/")
