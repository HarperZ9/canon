# W1: the workspace backend

A developer who moves one repository between Claude Code, Codex, Cursor, Gemini
CLI and a local model loses the working state that lived in the old tool: what
they were doing, what is still open, what was decided and what was tried and
dropped, and which quirks of the environment bite. The next tool starts from
nothing, and the developer explains the project again. A second failure sits
next to the first: memory tools that key on a user or an agent rather than a
project show one repository's history inside another.

W1 keeps that state as canon records bound to one project, and renders it for
whichever tool comes next. This document is the specification. The decisions
behind it are in `W1-DECISIONS.md`.

## Project identity

`canon.workspace.identity.derive_identity(workspace)` returns a
`ProjectIdentity`: a `project_id` (`prj_` and 32 hex digits), the `method` that
derived it, a path-clean `key`, a display `label`, and the local `root`.

1. The root is the nearest directory at or above the workspace that holds a
   `.git` entry. A `.git` file (a worktree or a submodule) is followed to its
   git directory, and a worktree's `commondir` is followed to the shared config.
2. A `.git` in the home directory or a filesystem root claims only that
   directory itself. A dotfiles repository in the home directory would
   otherwise give every unversioned project below it one shared identity.
3. With a remote (`origin`, else the first remote by name), the key is the
   normalized remote URL: scheme, credentials, port, query, fragment and a
   trailing `.git` are dropped, the host is lowercased, and the path is kept as
   written. `git@github.com:o/r.git`, `https://github.com/o/r` and
   `ssh://git@github.com:22/o/r` all give `github.com/o/r`.
4. A remote that is a local path gives `local-sha256:<digest>`, so the key
   carries no local path.
5. With no remote, the key is `path-sha256:<digest of the resolved root>`.

The id is `prj_` plus the first 32 hex digits of
`sha256("canon.project-id/v1\n<method>\n<key>")`.

### Collisions

Two checkouts get one id, and so share records, when:

- they have the same normalized remote. Two clones of one repository in two
  directories are one project on purpose. A fork has its own remote URL and so
  its own id.
- they have no remote and sit at the same resolved path at different times. A
  repository deleted and replaced by an unrelated one at the same path inherits
  the old records. Adding a remote to the new repository separates them.
- their remote URLs differ only in the parts normalization drops (scheme,
  credentials, port, host case, `.git`).

Two remotes that differ only by path case get two ids. That is deliberate: a
split hides records until they are adopted, while a merge shows one project's
records to another. A digest collision between unrelated keys needs a 128-bit
prefix collision and is not handled.

### Renames and moves

- Moving or renaming the local directory of a project with a remote keeps its
  id.
- Renaming the remote repository, or transferring it to another owner, changes
  the key and so the id.
- Moving a project with no remote changes its id.

In the two changing cases the old records stay in the store under the old id
and are not shown under the new one. Nothing merges them automatically.
`canon workspace adopt --from <old-id> --reason <text>` copies the old
project's accepted records to the new id, refuses before writing if any
record id would overwrite one the new project already holds, and logs each
adopted record with the project it came from.

## Workspace state

Four kinds of record carry the working state a developer would otherwise
explain again to every new tool. The schema is in `F0-SCHEMA.md` (W1
addendum); the builders are in `canon.workspace.authoring`.

| what | kind | id | written by |
|---|---|---|---|
| current focus: goal, active areas, branch | `workspace-focus` | `focus` (one per project) | `canon workspace focus` |
| open work and its status | `work-item` | `task-<n>` | `canon workspace task`, `set-status` |
| decisions, with the alternatives dropped and why | `adr-decision` | `decision-<n>` | `canon workspace decide --reject OPTION REASON` |
| constraints and environment quirks | `environment-constraint` | `constraint-<n>` | `canon workspace constraint [--quirk]` |

Every builder validates before it returns, stamps a provenance receipt
(`harness: canon-cli`, a content hash of the kind and payload, and the next
clock-free ordinal from the project's store), and writes a workspace record.
`set-status` keeps a work item's id and ordinal, so its place in a brief does
not move when its status changes. `focus` reads the branch from the
repository's `HEAD` file when `--branch` is not given, and runs no git command.

## The store

The store root defaults to `~/.canon/store` and can be set with `CANON_STORE`
or `--store`. It sits outside the repository so a commit never carries it by
accident.

```
projects/<project_id>/records.jsonl    accepted rows
projects/<project_id>/proposed.jsonl   proposed rows awaiting a decision
projects/<project_id>/log.jsonl        every write, decision, promotion, adoption
projects/<project_id>/project.json     the path-clean identity
global/records.jsonl                   rows promoted to global scope
global/log.jsonl                       every promotion into global
```

Each line of a row file is a `canon.project-row/v1` object:

```
{"schema": "canon.project-row/v1", "project_id": "prj_...", "state": "accepted",
 "record": { ...the record, unchanged... },
 "origin": null, "promoted_from": null}
```

The record inside is the F0 envelope byte for byte, with its own schema tag. The binding to a project
lives in the row, so every existing reader of a record keeps working, and a row
copied into another project's file still names the project it came from.

Rows are written sorted by `(scope, id)` through a temporary file and a rename,
under the run lock for the project, so the same row set always produces the
same bytes and two writers cannot interleave.

## Isolation

- Every new record is a `workspace` record of the store's project. `put`
  refuses a `global` record.
- Reading a row file refuses the whole file when any row names another project.
  A misfiled row is corruption, so it is reported and never filtered away.
- A render or a brief reads the pool from `canon.workspace.pool`: global rows,
  the project's own accepted rows, and the accepted rows of each other project
  the caller names in `include_projects`. Every record in the pool carries the
  project it came from. A proposed row is never in a pool.
- When a named project carries a personality block with the same scope and id
  as this project's block, the pool refuses, because layering would otherwise
  let one silently override the other.
- `canon workspace promote <id> --reason <text>` is the only path into global
  scope. It moves the record out of the project file, writes it to the global
  file with `promoted_from` set, and logs the move in both logs.

The contamination controls in `tests/test_workspace_store.py` write a phrase
into project A and assert it never reaches project B's render or pool, that a
row of A copied into B's file makes B's read fail, and that A becomes readable
from B only when named. Each control was checked by removing the rule it
protects and watching the test fail.

## Commands

```bash
canon workspace id                      # this project's identity and record counts
canon workspace list [--proposed]       # this project's records
canon workspace focus --goal "Ship the handoff" --area src/canon/workspace
canon workspace task "Write the Codex importer" [--status in-progress]
canon workspace set-status task-4 done
canon workspace decide --title "Row format" --decision "JSONL rows"     --context "Stores must diff in review" --reject SQLite "binary diffs"
canon workspace constraint "CI runs on Windows and Linux" --quirk
canon workspace promote <id> --reason "applies to every project"
canon workspace adopt --from <prj_id> --reason "moved the checkout"
```

Every command takes `--workspace` (default `.`), `--store`, and `--remote` to
override the remote used for the identity. `--json` gives the machine-readable
result.

## Limits

- The git config reader follows `commondir` and `gitdir`, not `include`
  directives or `insteadOf` rewrites.
- The store trusts the local filesystem. A process that can write the store can
  write any project's rows; isolation protects against mixing, not against a
  hostile local user.
- The log records wall-clock time as a convenience. Ordering inside the store
  uses the clock-free `create_ord`, and no render reads the log.
