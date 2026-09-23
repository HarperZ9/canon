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

## Handoff

`canon handoff --to <target>` writes a resume brief for the next agent from the
project's pool (`canon.workspace.brief.make_brief`). It has four sections, in
priority order:

1. **Focus**: the goal, the branch, the active areas and any notes.
2. **Open work**: work items that are `in-progress`, `blocked` or `open`, in
   that order.
3. **Decisions**: current decisions, most recent first, each with the reason
   (`Why:`) and every rejected alternative with the reason it was dropped.
4. **Constraints and quirks**, oldest first.

Inside a section this project's records come first, then global records marked
`[global]`, then records of a named project marked `[from <project_id>]`. A
closed work item, a superseded decision, a personality block (it goes in the
instruction region instead) and any other kind are excluded by rule; the
receipt names each one and the rule.

### Budgets

| target | brief budget | host limit it sits inside |
|---|---|---|
| `claude-code` | 12,000 bytes, 120 lines | docs advise a `CLAUDE.md` under 200 lines (high); a 40,000-character warning is user-reported (moderate) |
| `codex` | 16,384 bytes, 400 lines | `AGENTS.md` files share a 32,768-byte budget and are truncated past it (high) |
| `gemini-cli` | 16,384 bytes, 400 lines | no documented limit |
| `cursor` | 16,384 bytes, 250 lines | docs advise a rule under 500 lines (high) |
| `copilot` | 16,384 bytes, 400 lines | about 1,000 lines per instruction file at most (high) |
| `markdown` | 16,384 bytes, 400 lines | none; a brief to paste |

The host figures were read from each tool's public documentation or source on
2026-09-23. The brief budgets are canon's choices inside them, leaving room for
the personality blocks that share the file, and `--budget-bytes` and
`--budget-lines` override them.

### Truncation

The brief is a strict prefix of the priority order. When the budget runs out,
every record after the cut is left out whole, and the brief ends with a
`Left out` section that counts them and names as many as fit, then
`and N more`. A lower-priority record never appears while a higher-priority one
is missing, and no record is shortened. A budget too small for the header and
the truncation report is refused (`budget_too_small`).

### Receipt

`--receipt <file>` writes a `canon.handoff-receipt/v1` object: the path-clean
project identity, the target and its budget with the basis for it, the brief's
sha256, size in bytes and lines, a sha256 over the pool it was built from, the
declared projects, every included and left-out record with its content hash,
every record excluded by rule with the rule, and a `does_not_prove` list. No
clock is read, so the same pool gives the same brief and the same receipt.

### Switch

`canon switch --to <target>` renders the target's workspace instruction file
region: this project's personality blocks, by the same authored-split rule the
rest of canon uses, followed by one generated block, `canon-workspace-brief`,
holding the brief. The target reads its instruction file at startup, so the
brief reaches it without a paste. The write follows the canon rules:

- only the catalog surface for that target, resolved under the repository root;
- only between the canon markers, every byte outside them kept;
- a file with no canon region is refused, and a missing file is created only
  with `--create`, holding an empty region;
- a file the host would truncate (Codex past 32,768 bytes) is refused before
  writing; a file past a host's line guidance writes with a warning;
- `--dry-run` plans and prints the region without writing;
- the file is read again just before the write, and the write is refused if it
  changed since the plan read it.

A target with no instruction surface (`markdown`) prints the brief alone.

## Targets and declared downgrades

W1 adds three surfaces to the write allow-list, each by exact path:

| harness | file | why this path |
|---|---|---|
| `gemini-cli` | `GEMINI.md` | Gemini CLI loads a project-root `GEMINI.md` (its global file is not on the list yet) |
| `copilot` | `.github/copilot-instructions.md` | Copilot's repository-wide instructions file; plain Markdown |
| `cursor` | `.cursor/rules/canon.mdc` | one canon-owned rule; canon writes no other file under `.cursor/rules` |

Each is a lone workspace surface, so it renders the full merged block set, the
same rule `AGENTS.md` follows. `canon switch --create` makes the Cursor rule
with YAML frontmatter (`alwaysApply: true`), because Cursor loads a rule on
every request only with that setting.

A personality block may carry `applies_to`, a list of glob patterns naming the
files it is meant for. No surface on the allow-list can load one block for some
files and not others, so each target declares what it does instead:

| feature | targets | what happens |
|---|---|---|
| `activation.glob` | all five | the block is written always-on; the patterns stay in the block's sentinel and reach the model as an `Applies to:` line, which is advice rather than a rule |
| `text.at-import` | `claude-code`, `gemini-cli` | a line with an `@path` token is read by the host as a file import, so the same text means more there than in `AGENTS.md` |

`canon.workspace.target_fidelity.target_roundtrip` renders a block set into a
new host file for a target, runs the R0 round-trip verdict on it, checks the
host's own requirement (the Cursor frontmatter), and classifies every feature a
block asked for that the target handles differently. A difference the target
did not declare fails the verdict. `canon switch` lists each difference as a
warning, and `canon workspace targets` prints the table.

### Region grammar v1

The scope rides in the region grammar as an optional `applies` attribute on
the block sentinel, the authoritative copy, followed by a generated
`Applies to:` line:

```
<!-- canon:block id="react" applies="src/**/*.tsx|src/**/*.ts" -->
## React rules
Applies to: src/**/*.tsx, src/**/*.ts
Use function components and hooks.
```

On ingest the line must match the attribute and is removed; an edited line is a
refusal. A pattern may not contain `"`, `<`, `>` or `|`. A region with no
scoped block is byte-identical to the v0 grammar, and a block's source hash
changes only when it has a scope. The `textblock-grammar` pin moves to
`canon.textblock/v1`.

## Edits made inside a rendered region

Agents and people edit instruction files. When they edit inside canon's region,
the next `switch` must not overwrite that work, and it must not guess what the
edit meant either.

`switch` records the interior it wrote for each surface in the project's render
ledger (`projects/<id>/renders.json`, a `canon.render-ledger/v1` object keyed by
the surface's relative path). Before the next write it compares the region on
disk with that last render:

- equal: the file is canon's own, possibly stale; the switch overwrites it.
- different: the region was edited in place. Each edit becomes a proposed
  record, and the switch refuses with `edits_pending` until every proposal is
  accepted or rejected. After that the switch writes, carrying the accepted
  edits and dropping the rejected ones.

What an edit becomes:

| edit | proposal |
|---|---|
| a block's title, body or scope changed | the same block with the new content |
| a new block | a new personality block |
| a block removed | the block, retired (`valid_until` set) |
| `Goal:` changed in the brief | the focus with the new goal, other fields kept |
| a work line's status or title changed | that work item, updated |
| a new work line, or a new constraint line | a new work item or constraint |
| a work line removed | that work item with status `dropped` |
| any other changed line | one memory record holding the lines as written |
| an edit that broke the region grammar | one memory record holding the changed lines |

Lines labelled `[global]` or `[from <project>]` belong to another scope and are
kept as text rather than mapped. With no ledger entry (canon never wrote this
file for this project) the region is compared with what canon would write now,
and only additions and changes count, since an absent block says nothing when
canon never put it there. Every proposal is scrubbed like an import, carries an
origin naming the surface, the file digest, the line and the rule, keeps an
existing record's ordinal, and is skipped when the same content was already
accepted or rejected. `canon workspace pull --from <target>` runs the same read
without switching.

## Importers

`canon workspace import --from claude-code|codex <file>` reads one session file
another tool wrote and proposes records from it. It never writes an accepted
record: every result is a proposed row that `canon workspace accept <id>` or
`canon workspace reject <id> --reason <text>` settles, and nothing renders
until it is accepted.

### Formats

| source | file | what is read | confirmed against |
|---|---|---|---|
| Claude Code | a session `.jsonl` | `user` and `assistant` entries (`message.content` as text or blocks), `summary`, `sessionId`, `cwd`, `gitBranch`, `TodoWrite` inputs, `Edit`/`Write`/`MultiEdit`/`NotebookEdit` file paths | two public parsers of the format and Anthropic's note that the format is internal and changes between versions |
| Codex CLI | a rollout `.jsonl` (Codex 0.32 or later) | `session_meta` (id, cwd, `git.repository_url`, `git.branch`), `response_item` messages (`input_text`, `output_text`), `update_plan` calls, file names in `apply_patch` | the openai/codex source |

Both formats were read from public sources on 2026-09-23, and the test fixtures
in `tests/fixtures/transcripts/` follow them. Neither is a stable public
interface. A Codex rollout from before 0.32, where lines are bare items, is
refused as `unsupported_format`.

### Extraction rules

Fixed patterns, not a model, so the same file always gives the same proposals:

| rule | reads | proposes |
|---|---|---|
| `plan-tool` | the last `TodoWrite` (Claude Code) or `update_plan` (Codex) call | a work item per pending or in-progress step |
| `todo-marker` | `TODO: ...` or an unchecked `- [ ] ...` in a message | an open work item |
| `decision-phrase` | "we decided to X (because Y)", "we went with X" | a decision with status `proposed` |
| `failed-phrase` | "I tried X but Y", "X did not work (because Y)" | a decision with status `rejected` and X as a rejected alternative with Y as its reason |
| `session-summary` | Claude Code's summary line | the focus goal |
| `first-prompt` | the first line of the first user prompt, when there is no summary | the focus goal |

The focus proposal carries the session's branch and up to ten edited files as
areas, as paths inside the project; an edited path outside the project is
dropped and counted.

### Declared loss

Each importer names every category of content it drops, and the report counts
every one, including the zero counts. Common categories: text that matched no
rule, a repeated candidate, plan calls before the last, completed plan steps,
paths outside the project, a truncated last line, a candidate that failed
validation, images, tool calls and tool output. Claude Code adds thinking
blocks, sidechain entries, `isMeta` messages, message metadata and the entry
types that carry no conversation. Codex adds session state, `event_msg` lines,
reasoning, injected environment context, developer and system messages, and the
response items it does not read.

Content no category covers (an entry type, content block or message role the
importer has not seen) is an undeclared loss and refuses the import with
`undeclared_loss`, naming the label and the lines. `--drop-type <label>`
declares that drop for one run, and the report lists it under the drops the
person declared. A malformed last line is a declared truncation; a malformed
line anywhere else refuses the import.

### Secrets

Every string that becomes part of a proposal passes through
`canon.workspace.scrub` first. It redacts provider key formats (Anthropic,
OpenAI, GitHub, GitLab, Slack, AWS, Google, Stripe, Hugging Face, npm), JSON web
tokens, private key blocks, bearer and API-key headers, the password in a
connection URL, `password=` fields, JSON fields named like a secret, and
`NAME=value` assignments whose name says key, token, secret, password or
credential (for these name-based rules the value must be at least four
characters), and replaces each with `[REDACTED:<rule>]`. The report counts the
hits by rule; it never stores the value or a digest of it. Two more checks sit
behind the scrubber: the store refuses any record that still matches
(`secret_quarantine`), and a brief or an instruction region that would carry a
match is refused before it is written. The control test plants a canary for
each rule in both fixtures and asserts none reaches the store files, the
reports, the brief or the region; with all three checks removed the same test
finds the canaries.

### Project check

A Codex rollout names its repository in `git.repository_url`; a Claude Code
session names its working directory in `cwd`. When the source names a
different project than the one being imported into, the import is refused with
`isolation_refused` unless `--accept-foreign-source` is given, and the report
records the check either way. A source that names neither is recorded as
`unverified`.

### Provenance

A proposed record carries `harness` (`claude-code` or `codex`), `source_hash`
(the sha256 of the source line), `native_id` (`<importer>:<file name>:<line>`)
and the session id. Its row's `origin` names the importer, the file name, the
file's sha256, the line, the rule and a hash of the proposed content. Ids are
derived from the session, line and rule, so importing the same file again
proposes the same ids; a proposal already accepted with the same content, or
rejected before, is reported and not proposed again. The report is a
`canon.import-report/v1` object.

## The store

The store root defaults to `~/.canon/store` and can be set with `CANON_STORE`
or `--store`. It sits outside the repository so a commit never carries it by
accident.

```
projects/<project_id>/records.jsonl    accepted rows
projects/<project_id>/proposed.jsonl   proposed rows awaiting a decision
projects/<project_id>/log.jsonl        every write, decision, promotion, adoption
projects/<project_id>/project.json     the path-clean identity
projects/<project_id>/renders.json     what switch last wrote to each surface
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
  file with `promoted_from` set, and logs the move in both logs. It refuses,
  writing nothing, when global already holds a record with that id, because
  ids are per-project ordinals and two projects meet on `constraint-1`. The
  ordinal of a promoted record is never issued again in its project.
- `accept` refuses a proposal whose accepted record changed after the proposal
  was made (the proposal's origin carries `base_record_sha256`), so a later
  `set-status` or a second accepted edit is not erased. `--force` accepts it
  anyway.

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
canon workspace decide --title "Row format" --decision "JSONL rows" \
    --context "Stores must diff in review" --reject SQLite "binary diffs"
canon workspace constraint "CI runs on Windows and Linux" --quirk
canon workspace promote <id> --reason "applies to every project"
canon workspace adopt --from <prj_id> --reason "moved the checkout"
canon workspace import --from codex rollout.jsonl [--dry-run] [--drop-type LABEL]
canon workspace accept <id> [--force] | reject <id> --reason "not a real task"
canon handoff --to codex [--receipt brief.receipt.json] [--out BRIEF.md]
canon switch --to claude-code [--dry-run] [--create]
canon workspace targets                  # files, budgets and declared downgrades
canon workspace pull --from claude-code [--dry-run]   # edits in a region -> proposals
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
