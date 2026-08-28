# F0 — declared drops

A backend that cannot hold a field of the canonical record must **declare** the
drop, not silently lose it. This doc fixes the drops F0 already knows about,
each cited to real code read directly in the two engines canon assembles over.
The F1 MemoryBackend Protocol will carry a `declared_drops()` method; these are
its first entries. Confidence on each citation: high (verified by full read of
the cited file this session). Line numbers are from that read and may shift as
those upstream files change; the symbol names are the durable anchor.

## Drop 1 — a flywheel-backed record drops mneme's temporal history

**What is lost:** the `temporal` block. A record superseded in mneme (a
`valid_until` set, a `supersedes` pointer) cannot represent that history in the
flywheel store.

**Evidence.**
- flywheel `harness/store.py` — the schema in `_init` (store.py:47) defines
  `entities(eid, kind, project, data, sha256, created)` and
  `relations(...)` with no `valid_until`, no `superseded_by`, no temporal column
  anywhere. Rows are stamped with wall-clock `time.time()` (store.py:74, :92,
  :151), not an ordinal, so even ordering is clock-bound.
- mneme `src/mneme/store.py` — `supersede(old_id, new_id, reason="")`
  (store.py:387) sets `valid_until` (store.py:397) and `superseded_by` on the old
  memory. `memories(..., as_of=None, include_superseded=False)` (store.py:364)
  reads that history back.

**Declaration.** A flywheel-backed store holds only current records. A record
with a non-null `valid_until` is either refused or flattened to current-only;
either way the backend declares `temporal` dropped. mneme remains the backend of
record for anything whose history matters.

## Drop 2 — a mneme-backed record drops flywheel's arbitrary-kind graph

**What is lost:** arbitrary entity kinds and typed relation edges. mneme models
memory, not a general graph.

**Evidence.**
- mneme `src/mneme/schema.py` — the store's tables are `turns`, `memories`, a
  key/value `meta` table, and a hash-chained `audit` table (schema.py:13, :18,
  :28, :29); none is a relations table and none carries an arbitrary entity
  `kind`. A memory is added by `add_memory(memory_id, layer, text, source_ids,
  extractor, criterion, ...)` (store.py:323) and `layer` must be one of the four
  `LAYERS`.
- flywheel `harness/store.py` — `put_entity(kind, data, *, project="",
  eid=None)` (store.py:78) accepts any `kind` string, and `put_relation(src,
  dst, kind, *, project="")` (store.py:142) records a typed edge between two
  entities. mneme has no analogue of either.

**Declaration.** A mneme-backed store holds the memory kinds
(`episodic-memory`, `synthesized-persona-l3`) natively and declares
arbitrary-kind entities and typed relations dropped. A record whose meaning is a
graph edge belongs in the flywheel-backed store.

## Drop 3 — a plain-files backend drops the hash-chained audit

**What is lost:** chain verification. flywheel's store keeps a hash-chained
audit table; a net-new FilesBackend that writes JSON files has no equivalent
until it builds one.

**Evidence.**
- flywheel `harness/store.py` — `verify_chain()` (store.py:173) and
  `verify_records()` (store.py:192) validate a hash-chained `audit` table: each
  row commits to the prior, so tampering is detectable.
- mneme `src/mneme/store.py` — `verify_audit()` (store.py:476) is mneme's own
  analogue for its memory audit.
- The F1 FilesBackend is net-new and has neither table.

**Declaration.** A FilesBackend declares the audit chain dropped, or it adds its
own before claiming chain verification. It must not present unverifiable files
as if they carried a chain. Honest null: F0 ships no FilesBackend, so this drop
is declared in advance for the F1 slice that adds one.

## Why declared, not reconciled

canon is an assembly, not a superstore. The point of a declared drop is that a
record's home is chosen for what that record needs: temporal history goes to
mneme, graph edges to flywheel, and a backend never pretends to hold a field it
cannot. F1 makes `declared_drops()` executable and tests that each backend
refuses (or explicitly flattens) a record carrying a field it dropped.
