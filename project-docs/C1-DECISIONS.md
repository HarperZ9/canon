# C1-DECISIONS: owning the shared context store

Decisions continue the repository numbering; W1 ended at D-145. This band lets
the owner of a context database remove what it holds, keeps the audit chain
verifiable after a removal, and stops the audit rows from confirming what was
removed.

## D-146 A purge is an audit row, and the latest row for a key decides

Before this band a missing record failed every read of the context store,
because the store reconciles every record against the audit chain. A plain
DELETE would have disabled the database. A purge now appends one audit row per
removed record, with op `purge`. A key whose latest row is a put must be
present and match that row; a key whose latest row is a purge must be absent,
so a record put back under a purged key, even the exact original row with its
salt, is an integrity failure. An event captured again after a purge is a new
put and is present again (D-155).

A put keeps the original chain step, sha256(prev + key + sha). A purge row uses
sha256(prev + "purge" + 0x1f + key + sha), so an op cannot be relabelled without
breaking the chain. The generic SQLite backend, which also stores authored
blocks, walks the same op-aware chain but writes only puts with plain digests,
so a blocks database it writes still verifies under canon 0.3.0, and one 0.3.0
wrote verifies here with no schema change. An unknown op or a malformed row now
fails that walk closed instead of raising.

## D-147 A context put stores a salted commitment

A put row held sha256(envelope). After a purge that digest would stay in the
append-only audit table and confirm a guess of a short record, such as a
two-word prompt. New rows store sha256("canon.context.put.v1" || 0x00 || salt
|| envelope) with 32 random bytes of salt in a `salt` column beside the
envelope, and the audit row keeps the same commitment. A purge deletes the row
and its salt, so the commitment no longer opens. Verification recomputes each
row from its own salt; a salt that is missing, malformed or changed fails.

Rows 0.3.0 wrote have no salt and keep their plain digests. Rewriting them would
break the chain, so they stay, verify as before, and a purge counts each one it
removes as a legacy fingerprint in its report. The generic backend does not
salt: blocks are authored text, not captured traces, and its ledgers have to
stay readable by older readers.

## D-148 The first purge or salted put raises the identity version to 2

An older reader walks every row with the put formula, so it would read a purge
row as tampering. The identity marker `context_store_identity_version` moves
from 1 to 2 in the same transaction as the first purge or salted put, and canon
0.3.0 refuses a version 2 database as "identity invalid" before it walks the
chain. Reading never raises the marker, so a database this version only reads
stays usable by 0.3.0. This version reads 1 and 2. A marker still at 1 over
rows that need 2 is an integrity failure, which catches a hand-edited or
rolled-back marker. The cost is that a database shared with a 0.3.0 reader
stops working for that reader after its first write here, so a release carrying
this change is a decision for whoever runs both versions.

## D-149 The schema migrates by ALTER TABLE at the first write

CREATE TABLE IF NOT EXISTS never adds a column to a table that exists. The
first write of this version adds `audit.op` (NOT NULL DEFAULT 'put'),
`records.salt` and the `context_tombstones` table inside the writer's own
transaction, so two writers cannot both add a column. Reads select a missing
column as its default, so reading changes no schema. An older writer's inserts
still work on a migrated table, since both new columns have defaults, but the
raised identity marker already stops that writer.

## D-150 A tombstone names the key, the reason and the ordinal, and nothing else

Each purge row's digest is the sha256 of a canonical tombstone,
`{"schema": "canon.context-tombstone/v1", "key", "reason_code", "ordinal"}`,
stored in `context_tombstones` at the purge row's sequence number, which is
also the ordinal. The chain walk checks that every purge row has its tombstone
and that the tombstone hashes to the row. A tombstone holds no content hash, no
path and no session id. The key is derived from the event's identity (scope,
client, session and native id), not from its content, and the audit rows
already held it.

## D-151 The closure is the event, what ingest derived from it, and its answer

A purge removes each selected event, the extraction and interpretation records
ingest created with it, and, by default, the answer paired with it: an event
with `message_role: "assistant"` whose `responds_to` names the prompt. An
answer often restates its prompt, so leaving it would keep the content the
owner removed. `keep_responses` keeps the answer. Other events
that cite a purged event through `canon_event_ref` keep their own text, and
their query and get results carry `cited_events_purged`. Citations link by
event record id and never copy the cited event's `capture_hash`.

## D-152 A plan digest binds what is shown to what is applied

A plan lists every record it removes with its role, reason code and ordinal,
and its digest covers the store id, the scope, the selection, `keep_responses`
and those entries. Apply plans again inside its write transaction and refuses a
digest that no longer matches, so an event captured between the plan and the
confirmation is never removed unseen. Over MCP, `canon.context.purge` returns
the plan unless the call carries `confirm_plan_sha256`. The model that asked
for the plan can send the digest back, so canon alone cannot tell the owner
from a model; a harness that launches canon should require an owner grant for
this tool.

## D-153 Apply scrubs the files and scans them, and names what it cannot remove

The purge connection sets `secure_delete` and `temp_store=MEMORY`, deletes and
appends in one transaction, commits, and runs VACUUM; a database another tool
switched to WAL is checkpointed with TRUNCATE before and after VACUUM, and a
checkpoint a reader blocks is reported as busy. The residual scan then reads
the database and its journal, WAL and shared-memory files for 16-byte windows
of every purged value in the forms an envelope stores it. Needle windows and
file offsets use coprime strides sized to keep memory and time bounded; any
surviving run of at least `min_detectable_bytes` of a purged value is found.
That bound is 16 bytes while the purged values total under 1 MB and the
database files under 10 MB, grows past those sizes, and is stated in every
report. Occurrences that kept rows account for are not residue. Every report names freed disk clusters, since
canon stores plaintext (D-7), and the legacy fingerprint count, and lists the
copies canon cannot reach: client transcripts, excerpts earlier queries
returned into model contexts, the model provider, backups and copies.

## D-154 Retention runs the retention planner and applies its actions as a purge

`canon context retention --policy <file>` validates each entry through
`plan_retention`. `tombstone` and `purge-all` remove the event and its closure,
`purge-derived` removes the derived records only and must name the `sqlite`
store the planner checks coverage against, and `retain` keeps. A run is one
purge plan with one digest, and each tombstone's reason code names the rule. A
policy with `retain_content_hash: true` is refused, because a context tombstone
keeps no content hash.

## D-155 A purged event sent again is stored again

The latest row decides, so a client that sends the same event again after a
purge stores it again, under a fresh salt. Blocking the key forever would not
stop a tool from sending the same text under a new id, and it would make a
mistaken purge permanent. The purge report says so, the ingest result says
`stored_after_purge` instead of `stored`, and the capture hook returns a
`systemMessage` telling the owner the event is back. Whether a purged event
should be refused instead, as the design's "deleted content does not come
back" invariant asks, is an open decision for the owner.

## D-156 The command line applies a plan the owner saw, or says it did not

`--dry-run` prints the plan and its digest. `--confirm-plan <digest>` applies
that plan only and refuses it as stale when the store moved past it, which is
how the owner applies exactly what a dry run showed. `--yes` prints the plan it
computes at run time and applies it; it applies whatever matches then, which
can be more than an earlier dry run listed, and the docs say so. With none of
these the command prints the plan and applies it only when the owner types
`purge`. `--json` needs `--dry-run`, `--confirm-plan` or `--yes`, so a script
never waits on a prompt.

The database must already be a canon context store: the command reads its
schema through a read-only connection first, so a missing file, a file that is
not SQLite, or another SQLite file is refused as `not_found` or
`store_invalid` with no byte written to it. The terminal text shows each
event's opening words, run through the secret scrubber, and the transcript
paths it recorded, with control and format characters escaped. `--json` output
carries the previews only with `--show-preview`, because a command an agent
runs lands in the agent's transcript. Plans and reports over MCP carry ids,
roles, counts and digests only, because an MCP result enters a model context.

## D-157 An interrupted purge finishes on the next run

A purge commits its deletes before it runs VACUUM, so a crash between the two
leaves the rows gone and their bytes still in freed pages. The purge
transaction therefore sets a `scrub_pending` row in `context_store_meta`, and
the purge clears it only after VACUUM and any WAL checkpoint finished.
`canon.context.health` reports the mark. A plan shows it, and confirming a plan
that removes nothing finishes the scrub and reports `scrub_finished` without a
residual scan, since the purged values are no longer known. A scrub that a
reader blocks leaves the mark set and reports `scrub_incomplete`.

Running a purge or a retention policy again after it applied lists each
selected event whose latest audit row is a purge under `already_purged` and
removes nothing, instead of refusing the event as unknown, so the owner can
rerun the command that was interrupted. The list is part of the plan digest;
the scrub mark is not, because a scrub that finishes between plan and
confirmation changes nothing the owner confirms. A tombstone holds no scope,
so an event id purged in another workspace also reads as already purged.

## D-158 Answers are captured only on request, and each one names its prompt

The capture hook stores prompts by default, as 0.3.0 did. `--capture
prompts+responses` (or `CANON_CONTEXT_CAPTURE`) makes a `Stop` delivery store
`last_assistant_message` as an assistant event. Answers restate prompts and
often quote files and tool output, so storing them is the owner's choice, and
a hook mounted on `Stop` without that choice returns a message saying nothing
was stored instead of failing silently.

The answer's id is `<native_id>-response-<segment>`. The prompt's id is derived
from the same native id, so reusing it would give the answer the prompt's
identity with different content and raise `ContextCollision`. The answer names
the prompt's record id twice: in a `canon_event_ref` source, which related-event
queries follow, and in `responds_to`, which a purge follows (D-151). The hook
computes that id the way ingest does and stores the answer only when that
prompt event is in the store; `coverage.pairing` then reads
`prompt_event_found`. A `Stop` with no `prompt_id` or `turn_id`, a `Stop`
whose prompt was purged, and a `Stop` whose prompt was never captured store
nothing and say which, because an answer that names no stored prompt would
survive the purge of the prompt it restates. A different answer for the same
prompt takes the next segment, up to 16, and a redelivery of the same answer
stays idempotent.

Tool calls and reasoning are not captured in either mode, and each answer says
so in its coverage. `--transcript-locator none` records neither the transcript
path nor the working directory, since both name the client's project
directory, and marks `coverage.cwd: not_recorded`.

## D-159 The schema holds only what canon creates

Every read, write and purge first lists `sqlite_master`. The tables canon
creates, SQLite's `sqlite_sequence` and `sqlite_stat*` tables, and the
`sqlite_autoindex_*` indexes on canon's tables are allowed; any other table,
index, view or trigger fails integrity. Anything that can write the file can
add a trigger that copies each deleted row into a table of its own, and a
purge would then report success while the text survived. The residual scan
subtracts only text held by the records, audit and tombstone tables, so text
in any other table counts as residue rather than as kept.

## D-160 Captured text is scrubbed, and answers are not replayed by default

The hook runs prompt and answer text through the workspace secret scrubber
before it stores them and records the hit count per rule in
`coverage.redactions`, only when there were hits, so a prompt without a
secret-shaped value stores the same bytes as 0.3.0 and a redelivery stays
idempotent across the upgrade. Excerpts the hook returns, and query excerpts
and get results over MCP, are scrubbed again at egress, which covers records
stored before this version. The context the hook returns leaves out hits from
assistant events unless `--replay-answers on` is set, and says how many it
left out, because a returned excerpt enters the prompt another client sends to
its provider. The scrubber is pattern-based; a secret with no recognisable
shape passes through.

## D-161 A purge over MCP is a plan unless the owner enabled apply

The model that asked for a plan can send its digest straight back, and an
allow rule covering the whole `canon-context` server would approve the purge
tool with the rest. So `canon.context.purge` applies a confirmed plan only when
the server process was started with `CANON_CONTEXT_MCP_PURGE=apply`; otherwise
it refuses and names `canon context purge --confirm-plan`. Every plan and
report carries `presence: none` and a `does_not_prove` line saying any process
that can reach the command or an apply-enabled server, agents included, can
apply a purge. An owner-presence check is not built in canon.

## D-162 A purge that did not finish cleanly fails the command

A report whose status is `residue_found`, `scrub_incomplete` or
`audit_failed`, or which leaves the scrub mark set, exits with `EX_GATE` and a
failure code of the same name; `--json` output says `ok: false` and keeps the
report under `data`. A script or a scheduled retention run can then tell a
clean purge from one that left text behind. A file that is not a database is
`store_invalid` and a malformed scope is `invalid_args`, never a traceback.

## D-163 keep_responses holds for every selector, and reruns take late answers

With `keep_responses`, `before_ord` and `all` leave out each answer whose
prompt they also select or an earlier purge removed; before this, a bulk
selector named the answers as events of their own and removed them. An answer
named by its own event id is removed as named. A rerun that finds its target
already purged still removes answers stored after that purge, so a `Stop` that
raced the purge leaves nothing behind. A retention policy that retains an
answer, or purges only its derived records, while another entry removes the
answer with its prompt is refused and points at `keep_responses`.
