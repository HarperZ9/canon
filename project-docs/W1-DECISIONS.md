# W1-DECISIONS: the workspace backend

Decisions continue the repository numbering; M4 ended at D-100.

## D-101 The project binding lives in the stored row, not in the record

A record could carry its project in `data`, in `provenance`, or in a new
envelope field. Each of those changes a record that other readers already
parse: a personality block with an extra `data` key is refused by the text
renderer, a new provenance field changes every serialized record and every hash
over one, and a new envelope field is a `canon.record/v2`.

The binding goes one level up instead. The store keeps a `canon.project-row/v1`
row around the unchanged record, and the row names the project. A row copied
into another project's file still names where it came from, which is what lets
the read side refuse it.

## D-102 The identity comes from the remote, and a doubt splits rather than merges

A project with a remote is keyed on the normalized remote URL, so two clones,
two worktrees and a moved checkout are one project. The normalization drops
what does not name the repository (scheme, credentials, port, query, `.git`)
and lowercases the host, which DNS already treats as case-insensitive. It keeps
the path as written. Some hosts treat repository paths as case-sensitive, and a
wrong guess in the merging direction would show one project's records to
another, while a wrong guess in the splitting direction only hides records until
someone adopts them. Credentials are dropped before the key is formed, so no
token in a remote URL can reach a receipt.

A project with no remote is keyed on its resolved root path. A remote that is
itself a local path is digested, so the key never carries a local path.

## D-103 A `.git` in the home directory or a filesystem root claims only itself

The upward search for `.git` matches what git does, and git would place every
directory under a home-directory dotfiles repository inside that repository.
For canon that turns every unversioned project under the home directory into
one project, the exact mixing this band exists to stop. A `.git` found in a
ceiling directory therefore counts only when the workspace is that directory.
The test for it carries its own control: without the ceiling the same two
projects resolve to the dotfiles remote.

## D-104 Isolation is checked on read, and a misfiled row fails the whole file

Directory layout alone does not isolate projects: a copied file, a bad merge or
a bug in a writer can put a row where it does not belong. Reading a row file
therefore checks every row's `project_id` against the file's project and refuses
the file when one does not match. Filtering the stray row out would hide the
corruption and leave the next reader to trip on it, so the read fails and names
the foreign project.

## D-105 Another project is readable only when named, and never merged by id

A brief or a render may include another project's records when the caller names
that project. The pool then tags every record with its project, and the brief
labels them. When a named project carries a personality block with the same
scope and id as one of this project's blocks, the pool refuses, because the
layering rule (a later record with the same id wins) would otherwise let one
project override the other without anyone choosing it.

## D-106 New records are workspace records; global is reached by promotion only

`put` refuses a record in `global` scope. `promote` moves an accepted record
from a project to the global file, sets `promoted_from`, and writes a log entry
with the reason in both the project log and the global log. A record that every
project reads is one somebody chose to make global, and the log says who asked
for it and why.

## D-107 The store lives outside the repository by default

The default root is `~/.canon/store`, overridable with `CANON_STORE` or
`--store`. Inside the repository a store would ride along with a careless
commit, and the global file has no single repository to live in. A developer
who wants the state versioned with the code can point `--store` into the
repository and accept that trade.

## D-108 Adoption is the explicit answer to a rename

Renaming a remote or moving a repository with no remote changes the id, and the
old records stop appearing. Guessing that two ids are one project would be the
merge D-102 refuses to make. `adopt` copies another project's accepted records
into this project when a person names the old id and a reason, refuses before
writing when any record would overwrite one this project holds, and logs each
adopted record with its source project.

## D-109 The workspace-state kinds carry their own schema tag

Adding three kinds to the `canon.record/v1` vocabulary would have changed what
a v1 reader must accept: a 0.2.0 reader would meet `work-item` and report an
unknown kind. Bumping every record to a `canon.record/v2` would have changed
the bytes of every existing record, every vault note that carries one, and
every hash over them.

The new kinds instead share the envelope and carry their own tag,
`canon.workspace-state/v1`, pinned as the `workspace-state` seam.
`schema_tag_for(kind)` chooses the tag and `Record.from_dict` refuses a
mismatch in either direction. A record of the five F0 kinds keeps its tag and
its bytes, which the fixture test checks; an old reader refuses a
workspace-state record by its tag instead of misreading it. `KINDS` stays the v1
vocabulary and `ALL_KINDS` is what the validator admits.

## D-110 Rejected alternatives are an additive field on the decision record

A decision's rejected alternatives are the part a new tool most needs and the
part no session format records as data. They are a list of `{option, reason}`
objects on `adr-decision`, optional and validated only when present. An
alternative without its reason is refused, because an option with no reason
is the thing a later tool retries. The field is additive, so the decision
record keeps `canon.record/v1`: an old decision stays valid and an old reader
ignores the field.

## D-111 The storage adapters keep holding the five v1 kinds

The files, SQLite, mneme and flywheel adapters declare `KINDS` as what they
hold, and their round-trip proofs are written against it. The workspace-state
kinds live in the per-project store (D-101), so the adapters are unchanged and a
workspace-state record offered to one is refused as an unsupported kind rather
than stored under a contract that was never proved for it.

## D-112 The pin type moves to `versions_pin.py`

`versions.py` was already over the 300-line gate before W1 added three pins.
The error classes, the closed `SEAM_PINS` vocabulary and `SchemaPin` moved to
`versions_pin.py`, which imports nothing from canon, and `versions.py`
re-exports every name, so no caller changes an import.

## D-113 The brief is a strict prefix of the priority order, with a report

A brief that fits its budget by dropping whatever is largest would show a
constraint while hiding the current focus. The brief is built in priority order
(focus, open work, recent decisions, constraints) and cut at one point: every
record after the cut is left out whole and named in a `Left out` section and in
the receipt. No record is shortened, because a half decision reads as a whole
one. The receipt pins the budget, the brief's digest and a digest of the pool,
so the same records give the same brief, and a reader can tell what was cut
from what never existed.

## D-114 The brief rides in the instruction region as one reserved block

The point of a handoff is that the next agent reads it without being told to.
Every target already loads its instruction file at startup, so `switch` puts
the brief there, as one personality block with the reserved id
`canon-workspace-brief`, after the project's own blocks. The region grammar
carries it unchanged, so the region still round-trips through the R0 codec, and
a stored block that tries to use the reserved id is refused.

## D-115 Budgets come from the host's documentation, with a margin

Each target's numbers were read from the host's own documentation or source and
labelled with a confidence. Where the host truncates (Codex), `switch` refuses a
file past the limit, because a truncated instruction file loses its tail without
telling anyone. Where the host only advises (Claude Code, Cursor, Copilot), the
write goes ahead with a warning. The brief budgets sit well inside those
figures so the personality blocks that share the file still fit, and every
budget can be overridden on the command line.

## D-116 `--create` makes a missing file, never an existing one

The rule that a file is opted in by its owner adding the markers still holds.
`switch --create` writes a new file only when none exists, holding an empty
canon region; an existing file without a region is refused and left as it is.

## D-117 An importer proposes; a person accepts

A transcript is evidence of what was said, not a record of what was decided. A
pattern that reads "we decided to X" cannot tell a decision from a quoted
option or a joke. Every imported record is therefore a proposed row with an
origin naming the file, its digest, the line and the rule, and nothing renders
it until someone accepts it. A rejection is logged with a hash of the proposed
content, so re-importing the same file does not offer the same proposal again.

## D-118 Declared loss at the import boundary refuses what it cannot name

The R0 gate fails a round-trip on a loss nobody declared. The importers apply
the same rule at the boundary where content enters canon: each names every
category it drops, counts each one, and refuses when it meets content no
category covers. Both session formats change without notice, so the refusal is
the signal that the importer needs updating. `--drop-type` lets a person
declare the drop for one run, and the report says it was the person who
declared it.

## D-119 Scrub before storing, and check again at the store and at the render

A transcript holds whatever passed through the terminal. The scrubber runs on
every string before it becomes a record, and replaces a match with a marker
naming the rule. It stores no value and no digest of one, since a digest of a
short password can be reversed by guessing. The store refuses a record that
still matches, which also covers a secret typed by hand, and the brief and the
instruction region are checked once more, which covers a store file edited by
hand. The scrubber is pattern-based and documented as such: a secret with no
recognisable shape passes.

## D-120 The source must name this project, or the person must say otherwise

An import is the easiest place to mix projects: a rollout from one repository
imported while standing in another. When the source names a repository or a
working directory that is not this project, the import refuses unless
`--accept-foreign-source` is given, and the report records the check.

## D-121 Fixtures follow the public formats and plant canaries at run time

The owner's own session files are not read. The fixtures were written from the
formats as public sources describe them on 2026-09-23 (the openai/codex source
for rollouts, two public parsers for Claude Code sessions), with placeholders
for the project root and for secrets. The tests build each planted value at run
time, so no committed file carries a string a secret scanner would flag.

## D-122 A block's scope rides in the sentinel and is shown as a line

Cursor, Copilot and Continue can scope a rule to matching files; the plain
instruction files cannot. A block's `applies_to` is carried in the region
grammar as an `applies` attribute on the sentinel, which round-trips exactly,
and shown to the model as a generated `Applies to:` line, so the scope is not
lost on a host that loads everything. Ingest checks the line against the
attribute and removes it; a hand-edited line is refused rather than read as
body text. The grammar change is additive but an older reader refuses the new
attribute, so the `textblock-grammar` pin moves to v1. Unscoped blocks render
and hash exactly as before.

## D-123 Each new surface is one exact path, chosen for how its host loads it

The allow-list stays a list of exact paths. `GEMINI.md` at the workspace root
is what Gemini CLI loads for a project; the global `~/.gemini/GEMINI.md` is left
for a later change, like the global `SOUL.md`. For Copilot the surface is the
repository-wide `.github/copilot-instructions.md`; the path-specific
`.github/instructions/*.instructions.md` files are not on the list. For Cursor
canon owns one rule, `.cursor/rules/canon.mdc`, and no other file in that
directory, so a team's own rules are never canon's to write.

## D-124 A target declares what it cannot express, and the verdict holds it to that

The storage adapters declare their drops in advance and the round-trip gate
fails on anything undeclared. The render targets follow the same rule for host
semantics. Each target names the features it handles differently
(`activation.glob` everywhere, `text.at-import` on Claude Code and Gemini CLI)
and what it does instead. `target_roundtrip` classifies every such feature a
block asks for; an undeclared one fails the verdict, and the test that removes
the declaration watches it fail.

## D-125 `write_surfaces` reports a missing file instead of failing

With seven surfaces, most projects will lack some of the files. The batch
writer already skipped a file with no region; it now also reports a file that
does not exist as `missing` and never creates it, the same verdict the drift
check gives. Creating a file is `switch --create`'s job, for one named target.

## D-126 switch records what it wrote, so a stale file and an edit differ

V4 decided drift against what is on disk with no recorded base (D-51), which
suits a region only canon writes. A region an agent is invited to edit needs to
tell canon's own stale render apart from an edit, because only the first is
safe to overwrite. `switch` therefore records the interior it wrote per
surface, with a digest, in the project's render ledger. A ledger entry whose
digest fails is refused rather than trusted.

## D-127 An in-place edit becomes a proposal, and switch waits for the decision

Overwriting an edit loses work; applying it automatically lets any tool that
can write the file change the project's records. Each edit is read back into
the record it most plausibly means, by a fixed rule per line shape, and written
as a proposal; a line that fits no rule is kept verbatim as a memory proposal
instead of being guessed at. `switch` refuses while any proposal from the
region is undecided, and proceeds once each is accepted or rejected. Without a
ledger entry only additions and changes count, so the first switch into a file
never proposes to retire blocks canon did not write.
