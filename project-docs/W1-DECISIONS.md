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
