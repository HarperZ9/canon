"""identity.py -- a stable identity for the project a record belongs to.

A developer who moves one repository between Claude Code, Codex, Cursor and a
local model wants every tool to see that repository's records and no other
repository's. The store keys everything on a project id, so the id has to be
stable across the things that do not change the project (a second clone, a new
working directory, a different tool) and different across the things that do.

Derivation, in order:

  1. The repository root is the nearest directory at or above the workspace that
     holds a `.git` entry (a directory, or the file a worktree or submodule
     carries). A workspace with no `.git` above it is its own root.
  2. With a remote, the id is derived from the normalized remote URL alone:
     scheme, credentials, port, query and a trailing `.git` are dropped and the
     host is lowercased. Two clones of one repository share an id wherever they
     sit on disk. The remote is `origin` when present, else the first remote by
     name, so the choice does not depend on file order.
  3. With no remote, the id is derived from the resolved root path. Moving such
     a repository changes its id.

The path of a case-sensitive repository host is kept as written. Two remotes
that differ only by path case therefore get two ids. That split is deliberate:
when in doubt the derivation separates two projects rather than merging them,
because a merge shows one project's records to another and a split only hides
records until they are adopted explicitly.

The id is a digest, so nothing in it names a local path, a user name or a
credential. `label` is the human name shown in a brief: the normalized remote,
or the root directory's name for the path method.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from canon.versions import PIN_PROJECT_ID

ID_SCHEMA = PIN_PROJECT_ID.kind_tag
METHOD_REMOTE = "remote"
METHOD_PATH = "path"
_ID_PREFIX = "prj_"
PROJECT_ID_RE = re.compile(r"^prj_[0-9a-f]{32}$")

_SECTION_RE = re.compile(r'^\[\s*remote\s+"((?:[^"\\]|\\.)*)"\s*\]$')
_ANY_SECTION_RE = re.compile(r"^\[.*\]$")
_URL_RE = re.compile(r"^url\s*=\s*(.*)$", re.IGNORECASE)
_SCP_RE = re.compile(r"^(?:[^@/\s]+@)?([^:/\s]+):(?!//)(.+)$")


class ProjectIdentityError(ValueError):
    """The workspace cannot be given a project identity: it is not a
    directory, or its remote URL cannot be normalized."""


@dataclass(frozen=True, slots=True)
class ProjectIdentity:
    """One project. `project_id` is the storage key; `method` says how it was
    derived; `key` is the derivation input with no local path in it (the
    normalized remote, or `path-sha256:<digest>`); `label` is the display name.
    `root` is the local repository root and is never written to a receipt."""

    project_id: str
    method: str
    key: str
    label: str
    root: Path

    def to_public(self) -> dict:
        """The path-clean form a receipt or a brief may carry."""
        return {"project_id": self.project_id, "method": self.method,
                "key": self.key, "label": self.label, "schema": ID_SCHEMA}


def is_project_id(value: object) -> bool:
    return isinstance(value, str) and PROJECT_ID_RE.match(value) is not None


def default_ceilings() -> frozenset[Path]:
    """Directories whose `.git` never claims a workspace below them: the home
    directory (a dotfiles repository often lives there) and filesystem roots."""
    ceilings: set[Path] = set()
    try:
        home = Path.home().resolve()
        ceilings.add(home)
        ceilings.add(Path(home.anchor))
    except (RuntimeError, OSError):
        pass
    return frozenset(ceilings)


def find_repo_root(start: Path, *,
                   ceilings: frozenset[Path] | None = None) -> Path | None:
    """The nearest directory at or above `start` holding a `.git` entry.

    A `.git` in a ceiling directory (home, a drive root) counts only when
    `start` is that directory. Without this rule a dotfiles repository in the
    home directory would give every unversioned project below it one shared
    identity, which is the cross-project mixing this module exists to prevent.
    """
    stops = default_ceilings() if ceilings is None else ceilings
    current = start
    while True:
        if (current / ".git").exists():
            if current != start and current in stops:
                return None
            return current
        if current.parent == current:
            return None
        current = current.parent


def _git_dir(root: Path) -> Path:
    """The git directory for `root`: `.git` itself, or the directory a
    worktree's or submodule's `.git` file points at."""
    dot_git = root / ".git"
    if dot_git.is_dir():
        return dot_git
    text = dot_git.read_text(encoding="utf-8").strip()
    if not text.startswith("gitdir:"):
        raise ProjectIdentityError("a .git file without a gitdir line")
    target = Path(text[len("gitdir:"):].strip())
    return target if target.is_absolute() else (root / target)


def _config_path(root: Path) -> Path:
    """A worktree keeps its remotes in the common directory named by its
    `commondir` file; a submodule and a plain repository keep them in the git
    directory itself."""
    git_dir = _git_dir(root)
    common = git_dir / "commondir"
    if common.is_file():
        rel = Path(common.read_text(encoding="utf-8").strip())
        git_dir = rel if rel.is_absolute() else (git_dir / rel)
    return git_dir / "config"


def parse_remotes(config_text: str) -> dict[str, str]:
    """Remote name to URL from a git config file's text. The first `url` in a
    remote section wins. `include` directives and `insteadOf` rewrites are not
    followed (a declared limit)."""
    remotes: dict[str, str] = {}
    current: str | None = None
    for raw in config_text.splitlines():
        line = raw.strip()
        if not line or line[0] in "#;":
            continue
        section = _SECTION_RE.match(line)
        if section:
            current = section.group(1)
            continue
        if _ANY_SECTION_RE.match(line):
            current = None
            continue
        match = _URL_RE.match(line)
        if current is not None and match and current not in remotes:
            remotes[current] = _unquote_value(match.group(1))
    return remotes


def _unquote_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    for marker in (" #", " ;", "\t#", "\t;"):
        if marker in value:
            value = value.split(marker, 1)[0]
    return value.strip()


def read_remote_url(root: Path) -> str | None:
    """The chosen remote's URL for the repository at `root`, or None."""
    if not (root / ".git").exists():
        return None
    config = _config_path(root)
    if not config.is_file():
        return None
    remotes = parse_remotes(config.read_text(encoding="utf-8"))
    if not remotes:
        return None
    name = "origin" if "origin" in remotes else sorted(remotes)[0]
    return remotes[name]


def normalize_remote(url: str, *, root: Path | None = None) -> str:
    """The comparison form of a remote URL: `host/path` for a network remote,
    `local:<path>` for a path remote. Credentials never survive."""
    text = url.strip() if isinstance(url, str) else ""
    if not text:
        raise ProjectIdentityError("empty remote URL")
    if "://" in text:
        return _normalize_scheme_url(text)
    scp = _SCP_RE.match(text)
    if scp and len(scp.group(1)) > 1:
        return _join_host_path(scp.group(1), scp.group(2))
    return _normalize_local(text, root)


def _normalize_scheme_url(text: str) -> str:
    parts = urlsplit(text)
    if parts.scheme.lower() == "file":
        return _normalize_local(parts.path, None)
    host = parts.hostname
    if not host:
        raise ProjectIdentityError("remote URL has no host")
    return _join_host_path(host, parts.path)


def _join_host_path(host: str, path: str) -> str:
    clean = re.sub(r"/+", "/", path.strip().strip("/"))
    if clean.endswith(".git"):
        clean = clean[: -len(".git")].rstrip("/")
    if not clean:
        raise ProjectIdentityError("remote URL has no repository path")
    return f"{host.lower()}/{clean}"


def _normalize_local(path: str, root: Path | None) -> str:
    candidate = Path(path)
    if not candidate.is_absolute() and root is not None:
        candidate = root / candidate
    resolved = os.path.normcase(os.path.normpath(str(candidate)))
    return "local:" + resolved.replace("\\", "/")


def _digest_id(method: str, key: str) -> str:
    payload = f"{ID_SCHEMA}\n{method}\n{key}".encode("utf-8")
    return _ID_PREFIX + hashlib.sha256(payload).hexdigest()[:32]


def derive_identity(workspace: str | Path, *, remote_url: str | None = None,
                    ceilings: frozenset[Path] | None = None) -> ProjectIdentity:
    """Derive the identity of the project containing `workspace`. Pass
    `remote_url` to override the remote read from the git config."""
    start = Path(workspace).resolve()
    if not start.is_dir():
        raise ProjectIdentityError("workspace is not a directory")
    root = find_repo_root(start, ceilings=ceilings) or start
    url = remote_url if remote_url is not None else read_remote_url(root)
    label = root.name or "project"
    if url:
        method = METHOD_REMOTE
        key = normalize_remote(url, root=root)
        if key.startswith("local:"):
            # A path remote names a local directory; keep the path out of the key.
            key = "local-sha256:" + _sha256(key)
        else:
            label = key
    else:
        method = METHOD_PATH
        key = "path-sha256:" + _sha256(os.path.normcase(str(root)))
    return ProjectIdentity(_digest_id(method, key), method, key, label, root)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
