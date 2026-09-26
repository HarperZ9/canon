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
mistaken purge permanent. The purge report says so.

## D-156 The command line applies only a plan the owner saw

`canon context purge` and `canon context retention` print the plan. `--dry-run`
stops there, `--yes` applies it, and with neither the command applies only when
the owner types `purge`. The database must already exist, so a mistyped path
does not create an empty store. `--json` needs `--dry-run` or `--yes`, so a
script never waits on a prompt. The terminal text shows each event's opening
words and the transcript paths it recorded, with control and format characters
escaped; plans and reports over MCP carry ids, roles, counts and digests only,
because an MCP result enters a model context.

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
computes that id the way ingest does and records in `coverage.pairing` whether
the prompt was in the store. A `Stop` with no `prompt_id` or `turn_id` stores
nothing, because an answer that names no prompt would survive the purge of the
prompt it restates. A different answer for the same prompt takes the next
segment, up to 16, and a redelivery of the same answer stays idempotent.

Tool calls and reasoning are not captured in either mode, and each answer says
so in its coverage. `--transcript-locator none` records no transcript path,
since the path names the client's project directory.
