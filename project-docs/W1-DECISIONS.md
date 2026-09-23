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

## D-128 Findings from the branch review, folded in

An independent review of the band found three gaps and one tradeoff:

- A removed brief line labelled `[from <project>]` was mapped by id alone, so
  deleting another project's `task-3` could propose dropping this project's
  `task-3`. Removed lines with a scope label are now skipped, as added ones
  already were; a test pins it.
- The filesystem-root ceiling (D-103) was computed from the home directory, so
  it vanished where the home directory cannot be resolved. It is now taken from
  the workspace's own anchor as well, and a test removes the home directory.
- `switch` wrote the plan's text without looking at the file again, so an edit
  made between planning and writing was lost. The commit now re-reads the file
  and refuses when it changed (or appeared, for a create). The window between
  that read and the write remains and is disclosed.
- The name-based secret rules redacted any value after a secret-named key,
  including `RETRY_TOKEN_COUNT=5`. They now need a value of at least four
  characters. A secret shorter than that after such a key is not redacted; the
  provider-format rules are unaffected.

## D-129 promote refuses a clash, and accept refuses a stale base

Record ids are per-project ordinals, so project A's `constraint-1` and project
B's `constraint-1` are different records with one id. `promote` used to replace
any global row with the same id, and since the promoted record has already left
its project file, the record another project put there survived nowhere. It now
refuses before writing, the same rule `adopt` follows. `next_ord` also counts
the records a project promoted, so the next `workspace task` never reissues a
promoted id and a second promotion cannot meet the first.

A proposal is a snapshot. Accepting it replaced the accepted record whole, so a
`set-status` run between the proposal and the accept was erased with no
warning. Each proposal now records the digest of the accepted record it was
built from (null when there was none), and `accept` refuses with `conflict`
when the current accepted record differs. `--force` accepts anyway, for the
person who compared the two. The store's secret check now covers the whole row,
provenance included, because an importer copies a session id from the source
verbatim.

## D-130 A non-default port splits, a nonce keys a local repository, and a new checkout is announced

D-102 says a doubt splits. Dropping every port merged two servers on one host
(a staging and a production forge) into one project, so a port now stays in
the key unless it is the scheme's default.

Two merges were silent. A repository with no remote was keyed on its path, so
one deleted and re-created at the same path inherited the old records, and two
apps cloned from one starter keep its remote and share an id. canon now writes a
random nonce once into the shared git directory of a repository with no remote
and keys on that; it moves with `.git`, which also removes the old "moving it
changes its id" limit. For the starter case the rules cannot tell a second clone
of the same project from an unrelated repository, so the store records a
path-clean digest of each checkout root and a command from a new root prints a
notice. `git config canon.project <name>` names a project explicitly and wins
over the remote, so a split survives every command without a flag. Writing the
nonce is the one place identity derivation writes a file; a git directory canon
cannot write falls back to the path key.

## D-131 The scrubber covers the everyday forms, runs before extraction, and anchors placeholders

The first rule set named its categories correctly and missed their everyday
spellings: `db_password=`, `password: x` in YAML, a quoted password, a
lower-case `aws_secret_access_key` from `~/.aws/credentials`, `DB_PASS=`, a PGP
key block, a URL password holding `/`, a token as a URL's user, escaped JSON.
Common carriers had no rule at all (basic auth, cookies, URL query tokens,
Azure keys, PyPI tokens, webhooks, `.npmrc`). An end-to-end run found each one
in the store and in all five rendered files. The rules now cover those forms,
and a new test runs every form through import, accept and switch and asserts
on the rendered files.

A broader name rule risks redacting code. The name-based rules therefore skip
a value that reads as code or as a type name, and a name whose only secret
segment is `key` or `auth` needs a value that looks random. A false positive
here is a redaction, which loses a word; a false negative publishes a secret,
so where the two conflict the rule redacts.

Scrubbing ran on the captured fragment, so a 200-character cap or a line break
could cut a token below its rule's minimum and store most of it. Each source
string is now scrubbed whole before extraction, and the prefix rules take short
minimums so a cut token is still caught. A placeholder test that matched a
prefix skipped `$2b$12$...` and a value that joined an earlier redaction to
more text; placeholders are now matched against the whole value.

## D-132 The importers read the host's own text as the host's, and compare projects by identity

Both hosts put text in the user role that the person never typed: Claude Code's
slash commands, local command output, bash-mode output and compaction
summaries, and Codex's shell command output, skills and sub-agent notices. The
importers mined it as typed text, so a `cat NOTES.md` became a decision. Each
now drops that text by its marker under a named category. A rolled-back Codex
turn and a rewound Claude Code branch are dropped the same way, and a Claude
Code summary is used only when it describes this file, since a summary line
routinely describes another session. The Claude Code task tools that replaced
TodoWrite are read as the plan.

The project check compared paths, so a session from a nested repository passed
as this project and a session from a sibling worktree was refused. It now
compares project identities, derived without writing anything into the other
repository. A Codex sub-agent's rollout shares the root's `session_id`, so ids
now key on the thread id, and an accepted record from another file is never
replaced by a new proposal with the same id.

A malformed last line was always read as a truncation. A writer appends a line
and its newline together, so only an unterminated last line is a truncation;
a malformed line that ends in a newline is corruption and refuses.

## D-133 Back-flow reads a checkout against its own render and keeps every edit

The ledger kept one render per project and surface, but worktrees and clones
share a project id and each has its own file, so one checkout read another's
newer render as its base and proposed dropping live work. The last render is
now kept per checkout, and a region equal to any render canon remembers writing
to the surface is stale, whichever checkout wrote it or whichever branch
restored it. An empty region has no base, so opting a file in never proposes a
retirement. A file is written and its ledger entry recorded under one lock, so
a held lock can no longer leave a written file with an old ledger entry.

An edited line was mapped whole, so a title edit also carried the status the
file showed, and reverted a newer status set elsewhere. Each line is now paired
with the line canon rendered for the same id, and only the changed fields are
proposed. A tick written `[x]` or `[Done]`, or a trailing space, used to read as
a removal; a line that still names an id never does now. Removed constraint,
decision, goal and detail lines, a changed brief heading and a changed sentinel
ordinal were silently overwritten; each is now proposed or kept in the note.
A rejection was remembered by content forever, so a later real edit with the
same content was discarded; it is now tied to the render it was made against.

An edit of a block another project or global owns was proposed as this
project's record, and accepting it blocked every later `--include-project`
switch. The ledger records each rendered block's owner, and such an edit is
kept in the note, naming the owner. A retired copy of a block no longer counts
in the collision check.

## D-134 switch checks the host as it is, and the brief is measured as it lands

The allow-list check was lexical, so a `.cursor` junction or a `GEMINI.md`
symlink carried the write outside the repository, and a `CLAUDE.md` linked to
`AGENTS.md` let one target bypass the other's size refusal. Every directory on
the way to a surface is now checked for a link, at plan time and again at write
time, and a created file is opened in exclusive mode. The batch writer gets
the same check where its root exists.

Codex reads `AGENTS.override.md` instead of `AGENTS.md`, so a switch that
writes `AGENTS.md` beside an override is refused rather than reported as a
success Codex never reads. Codex applies one budget to all AGENTS files from
the root down, and a user can raise it; canon reads the budget from the Codex
config and names a nested file the chain would cut.

Claude Code, Gemini CLI and Cursor read `@path` as an import or as context,
bare names included. The brief was never checked, so a work item that
mentioned `@config/prod.yaml` turned into a file import. Brief lines for those
hosts now put every such token in a code span, which the hosts read as text,
and the detector matches the hosts' parsers and skips code spans.

A switched surface always read as drift, and reconcile then erased the brief,
because neither knew the reserved block. Both now carry it through. The brief
was fitted without its sentinel line, so the block that landed overran its
budget; it is now measured as it lands and the receipt names the block's
digest. The footer promised a receipt no switch wrote; switch now writes one
on request and keeps the last one, and the footer names the command that lists
every left-out record. A CRLF host got a mixed file, and a byte-order mark hid
the begin marker; both now read as the host wrote them.
