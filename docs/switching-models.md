# Moving a project between models and tools

You work on one repository with Claude Code in the morning and Codex in the
afternoon, try Cursor for a refactor, and paste context into a chat app or a
local model when you need a second opinion. Each of them starts from nothing,
and you explain the project again: what you are doing, what is still open, what
you decided and what you already tried, and which quirks of the environment
bite. canon keeps that state as records bound to the repository and writes it
into the file each tool reads when it starts.

This guide covers the commands. The specification is
`project-docs/W1-WORKSPACE.md` and the reasoning behind each rule is in
`project-docs/W1-DECISIONS.md`.

## Install

The workspace commands are not in a release yet. `flywheel-canon` 0.2.0 on PyPI
does not have them. Install from a checkout of the repository:

```bash
python -m pip install -e .
```

canon has no runtime dependencies and needs Python 3.11 or newer.

## One project, one store

```bash
cd your-repo
canon workspace id
```

canon derives the project's id from its git remote, so two clones of one
repository share their records and a fork has its own. A repository with no
remote is identified by its path. Records live outside the repository, in
`~/.canon/store` unless `CANON_STORE` or `--store` points elsewhere.

Every stored record names its project. A read that finds another project's
record in this project's file fails rather than mixing the two, and another
project's records appear in a brief only when you name that project with
`--include-project`. Promoting a record to global scope, where every project
reads it, is an explicit, logged command:

```bash
canon workspace promote decision-7 --reason "house rule for every repository"
```

If you rename the remote or move a repository that has no remote, its id
changes. The old records stay in the store; copy them over with
`canon workspace adopt --from <old-id> --reason "moved the checkout"`.

## Record the state you would otherwise re-explain

```bash
canon workspace focus --goal "Ship the JSON export" --area src/export
canon workspace task "Add the --json flag" --status in-progress
canon workspace task "Update the changelog"
canon workspace decide --title "Keep the CSV writer" \
    --decision "Add JSON beside CSV" --context "Downstream scripts parse CSV" \
    --reject "Replace CSV with JSON" "breaks three downstream scripts"
canon workspace constraint "The Windows runner times out after 10 minutes" --quirk
canon workspace set-status task-2 done
canon workspace list
```

A decision's rejected alternatives cannot be recorded without a reason, because
an option with no recorded reason is the one the next agent tries again.

## Or import what the last session knew

```bash
canon workspace import --from claude-code path/to/session.jsonl
canon workspace import --from codex path/to/rollout.jsonl
canon workspace list --proposed
canon workspace accept imp-task-4de430285521
canon workspace reject imp-decision-8a1f0c2b9e77 --reason "quoted, not decided"
```

The importer reads a Claude Code session file or a Codex rollout (Codex 0.32 or
later) and proposes the session's focus, the open steps of its last plan,
`TODO` markers, sentences like "we decided to X because Y", and failed
approaches like "I tried X but Y". Every proposal names the file and line it
came from, and nothing reaches a brief until you accept it.

Before anything is stored, API keys and tokens, private keys, bearer headers,
connection-string passwords and secret-named assignments are replaced with
`[REDACTED:<rule>]`. The store also refuses any record that still looks like
one.

Each importer lists what it drops (thinking blocks, tool output, system
entries and more) and counts it in its report. A session with content the
importer has not seen is refused until you declare that drop with
`--drop-type`, so a change in a tool's format cannot lose data quietly. A
session that names a different repository is refused unless you pass
`--accept-foreign-source`.

## Hand off to the next agent

```bash
canon handoff --to codex
canon handoff --to markdown --out BRIEF.md --receipt brief.receipt.json
```

The brief lists the focus first, then open work, then recent decisions with
the alternatives dropped and why, then constraints and quirks. It fits the
target's size budget; anything that does not fit is left out whole and named
in a `Left out` section at the end. The receipt holds digests of the brief and
of the records behind it.

## Switch in one command

```bash
canon switch --to claude-code --dry-run
canon switch --to codex --create
canon workspace targets
```

`switch` writes your blocks and the brief into the target's own instruction
file, between canon's markers only, so the agent reads it at startup:

| target | file |
|---|---|
| `claude-code` | `CLAUDE.md` |
| `codex` | `AGENTS.md` |
| `gemini-cli` | `GEMINI.md` |
| `copilot` | `.github/copilot-instructions.md` |
| `cursor` | `.cursor/rules/canon.mdc` |
| `markdown` | none; the brief is printed to paste anywhere |

A file with no canon region is left alone until you add the markers, and
`--create` makes a missing file with an empty region. canon refuses to write an
`AGENTS.md` larger than Codex reads, because Codex would cut its tail.

If you or an agent edit inside canon's region, the next `switch` does not
overwrite the edit. Each edit becomes a proposal and the switch waits until
you accept or reject it. `canon workspace pull --from claude-code` reads the
edits back without switching.

## What canon does not do

- The importers use fixed text patterns, not a model. A decision phrased
  another way is not proposed, and a proposal is a candidate, not a fact.
- Neither session format is a stable public interface. The importers were
  checked against public sources on 2026-09-23 and refuse what they do not
  recognise rather than guess. Gemini CLI, Cursor, ChatGPT and Claude web
  histories have no importer yet.
- The scrubber recognises secrets by their shape. A secret with no recognisable
  shape passes through, a value shorter than four characters after a
  secret-named key is not redacted, and email addresses are not redacted.
- None of the instruction files can load a rule for some files only. A block
  scoped to files with `applies_to` is written for every file, with an
  `Applies to:` line the model reads as advice.
- The size budgets come from each tool's public documentation and can change.
  Override them with `--budget-bytes` and `--budget-lines`.
- The store trusts the local filesystem. Isolation keeps projects from mixing;
  it does not defend against someone who can write the store directly.
- The brief shows what was recorded or imported. It does not know about work in
  a session nobody recorded.
