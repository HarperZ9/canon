# M4 — decisions of record

The decisions that frame the M4 wave, continuing the log in F0-DECISIONS.md,
F1-DECISIONS.md, R0-DECISIONS.md, R1-DECISIONS.md, R2-DECISIONS.md,
V2-DECISIONS.md, V3-DECISIONS.md, and V4-DECISIONS.md, and recorded in the same
shape the `adr-decision` kind captures. Each is accepted unless marked
otherwise.

M4 lifts canon out of the local file. It ships the transport seam (`M4.1`, this
file's first block of decisions), the vault reader that closes R2's write leg
(`M4.2`, to be appended), a version-pin registry that names every schema and
prose contract canon speaks (`M4.3`), and an optional composition module
(`M4.4`). This file grows with each landed band.

## D-69 — transport is a Protocol seam; every wire stays in its own package
**Status:** accepted (M4.1, 2026-08-31).
**Context:** canon needs to ship records across processes and hosts. The Wave
0 record and the Wave 1 storage seam are complete; a wire (relay, MCP, HTTP,
gRPC, stdio pipe) is the next honest surface. A wire pulled into canon would
carry a socket, a TLS stack, a possible OAuth flow, and an HTTP or gRPC
library, and would end the stdlib-only invariant that keeps the container
portable.
**Decision:** canon adds a `Transport` Protocol and never a wire. Every live
wire lives in its own package (`relay` for the first one) and satisfies this
Protocol against an injected duck-typed handle. Canon imports no socket, no
`http`, no `urllib.request`, no `ssl`, no third-party client. The test suite
pins the import set with a grep-shape assertion.
**Consequence:** a new wire is a new package that wraps canon's contract. A
canon-side change never breaks a wire the way a coupled library rewrite would;
a wire-side change never rewrites canon's refusal semantics. The relay repo
carries the first live wire; MCP, HTTP, gRPC, stdio pipe adapters land in
theirs.

## D-70 — three record-enforceable capability tokens; the rest declare-but-never-block
**Status:** accepted (M4.1).
**Context:** F1 fixed one record-enforceable capability (`temporal`) and
declared the other four (`audit-chain`, `relations`, `arbitrary-kind`,
`foreign-provenance`) as structural. A transport ships more properties than a
store does (delivery guarantees, ordering, replay safety, offline safety), so
the vocabulary is larger.
**Decision:** the transport vocabulary is seventeen tokens, split three ways.
Three tokens are record-enforceable and `guard_push` refuses a record that
exercises one the wire dropped: `temporal-preserving`, `provenance-preserving`,
`sized-payload-limit`. Eleven are structural: declared, machine-readable, and
never triggered by a lone record. Three are reserved for Wave 2 (`tombstones`,
`streamable`, `remote-batch`), present so a later band adds behavior without
renumbering the vocabulary.
**Consequence:** a wire's `caps()` and `declared_drops()` are a lossless
description of what round-trips through it and what does not. A record whose
fields would suffer a silent drop refuses at `push`, never mid-flight. The
descriptor is machine-checkable in one place (`__post_init__`).

## D-71 — refuse-not-flatten on the transport side, mirroring F1 D-8
**Status:** accepted (M4.1).
**Context:** F1's D-8 refuses a record that would lose a field silently: the
caller `flatten()`s first and thereby opts into the loss. A transport can
reasonably want the same rule, or it can want an implicit strip.
**Decision:** the transport side holds refuse-not-flatten. `guard_push`
raises `DropError` when a record exercises a record-enforceable cap the wire
declared dropped. Callers who want the loss call `transport.flatten(record)`
first, exactly the way F1 callers call `backend.flatten(record)`.
`default_flatten` maps the tokens onto backend-side removals where the removal
exists; `provenance-preserving` and `sized-payload-limit` are honest nulls (see
D-72).
**Consequence:** a wire cannot drop a field a record carries without the
caller knowing. The two seams (storage, transport) share one flatten idiom, so
a caller does not learn a second one to talk to a wire.

## D-72 — external transport engines reached through an injected duck-typed handle
**Status:** accepted (M4.1).
**Context:** the relay is a running service, the MCP transport is a client
library, and future transports will each carry their own runtime dependency.
Importing any of them into canon ends the stdlib-only invariant.
**Decision:** every transport that fronts an external engine takes an injected
handle, duck-typed to the smallest verb set the adapter needs. Canon imports no
transport library. `FakeRelayHandle` in the test suite mimics the shape a real
relay handle would carry; a live relay adapter substitutes its own handle
against the same contract.
**Consequence:** the adapter package (`relay`, `mcp_relay`, and so on) owns
the runtime dependency; canon does not. `provenance-preserving` and
`sized-payload-limit` are non-removable at record level, so `default_flatten`
folds only `temporal-preserving`; the two other honest nulls are named here
rather than hidden in the code.

## D-73 — TransportEnvelope, TransportReceipt, TransportDescriptor are runtime dataclasses, not Wave 1 schemas
**Status:** accepted (M4.1).
**Context:** the wire carries three shapes that could reasonably be pinned as
schemas (`canon.envelope/v1`, `canon.receipt/v1`, `canon.adapter/v1`).
Promoting them to schemas would fix the wire vocabulary and buy schema
verification on it. It would also lock in a wire trust model, a freshness
enum, and a disclosure profile before the second and third adapters land.
**Decision:** M4.1 keeps all three as runtime frozen dataclasses. The wire
carries record bytes; the envelope, receipt, and descriptor are the shape of
canon's runtime speaking about that transport, not of the data on the wire.
Every name carries the `Transport` prefix so a future
`canon.transform-envelope/v1` or `canon.adapter/v1` does not collide.
**Consequence:** the wire vocabulary is not locked in before a second and
third adapter land against it. Wave 2 promotes the shapes it needs once the
lessons are in: `canon.tombstone/v1` for the delete verb, `canon.adapter/v1`
for trust labels, and so on. The runtime shape is a machine-readable summary
today, not a wire promise.

## D-74 — the idempotency key is domain-separated from the vault digest
**Status:** accepted (M4.1).
**Context:** R2 identifies a note file by `sha256("canon-vault/v1\n" +
record_key)`. The transport needs its own idempotency key. A shared hash would
mean a transport key could collide with a vault filename in a way that would
be indistinguishable at the byte level.
**Decision:** the transport idempotency key is
`sha256("canon-transport/v1\n" + record.to_json()).hexdigest()`, sharing the
`domain_prefix` helper R2 uses but under a distinct namespace. The record's
canonical JSON is the payload; two runs of the same record produce the same
key. The prefix and the vault prefix are byte-distinct; neither is a substring
of the other; the two hash spaces are cryptographically independent.
**Consequence:** the wire and the vault never share a hash space. A wire is
free to deduplicate on the key; a vault note is free to be named by its key.
Neither reads the other's namespace.

## D-75 — fetch on a missing key returns None; it never raises on miss
**Status:** accepted (M4.1).
**Context:** a fetch of a key the wire does not hold could raise a canon
`NotFound`, or it could return `None`. F1's `MemoryBackend.get` returns `None`.
**Decision:** `Transport.fetch(scope, id)` returns `None` on miss. Only a
transport-level failure raises a `TransportError`. The caller pattern-matches
one thing (a None return) for missing data and one hierarchy for failure,
never a mixed set.
**Consequence:** the read-side is total against missing keys, the way the
storage-side is. A miss is data, not an error.

## D-76 — list_keys and list_all return unordered lists; determinism is the caller's job
**Status:** accepted (M4.1).
**Context:** a wire holding thousands of records may not have a natural
ordering, or its natural ordering may be its own insertion order and not
canon's. Forcing an order on the seam would fix an arbitrary sort into the
Protocol.
**Decision:** `list_keys(scope)` and `list_all()` return `list[str]` with no
order guarantee. Callers that need determinism sort the result on the field
they care about (idempotency key, scope, id, ord). `FakeRelayHandle` happens
to sort its return for readability, and the conformance test asserts sort on
the fake, not on the Protocol.
**Consequence:** a live wire is not forced to hold an index it does not
otherwise carry. Callers that reproduce byte-identical output sort the result;
callers that stream a large listing do not pay for an unneeded sort.

## D-77 — sha256 idempotency-key collisions are an honest null
**Status:** accepted (M4.1).
**Context:** the idempotency key is a truncation-free sha256 digest.
Astronomically improbable, but not zero.
**Decision:** canon does not detect a collision. A collision would require an
attacker to author a second record with the same 256-bit digest as an existing
record. The container names the null here rather than adding a mitigation for a
non-threat.
**Consequence:** a wire that observes a matching key with different bytes
raises `DuplicatePush`, which addresses the real threat (a tampered replay).
Fresh identical bytes are accepted as an idempotent replay. The honest null is
disclosed here rather than hidden.

## D-78 — CAP_TEMPORAL_PRESERVING is a deliberate rename of F1's CAP_TEMPORAL
**Status:** accepted (M4.1).
**Context:** F1 named the token `CAP_TEMPORAL` because a store either holds
the temporal block or drops it. A transport carries a preservation contract:
a wire that carries the block declares `temporal-preserving` in `caps()`; a
wire that drops it declares `temporal-preserving` in `declared_drops()`. The
name reads differently on the two seams for a reason.
**Decision:** the transport token is `CAP_TEMPORAL_PRESERVING`, spelled out
so a reader sees the preservation framing at the point of use.
`default_flatten` bridges the rename: a transport that dropped
`CAP_TEMPORAL_PRESERVING` maps onto the backend-side `CAP_TEMPORAL` and strips
the temporal block through `backends.flatten_for_drops`, unchanged.
**Consequence:** two names for what a naive reader might think is one
capability, disclosed here rather than left as a puzzle. The bridge is one
line; the code cost of the rename is zero and the reader cost is a decision
paragraph.

## D-79 — the read leg mirrors the write leg through one lexical containment gate
**Status:** accepted (M4.2, 2026-08-31).
**Context:** R2's write leg refuses to touch a path that is not under the
vault, not `{scope}/<name>.md`, or the vault root itself.
`vault_mirror.is_vault_write_allowed` is the one function that decides. A read
leg that used its own rule could drift over time from what the write leg would
touch, and the two legs would then disagree on what a canon note is.
**Decision:** the read leg imports `is_vault_write_allowed` verbatim and calls
it as its own containment gate. A single edit to the write-side rule flows to
the read side with no code change. Any path the write leg refuses to touch is a
path the read leg refuses to source.
**Consequence:** the two legs cannot disagree on what a canon note is. A
caller reading a vault the write leg populated sees a pool that the write leg
would recognize as its own on a rewrite. `SKIPPED_NOT_ALLOWED` is the reader's
name for the write-leg predicate returning `False`.

## D-80 — the read leg is total; every refusal is a NoteVerdict
**Status:** accepted (M4.2).
**Context:** the write leg's `plan_vault` raises `VaultError` on refusal; a
read leg that raised on hostile input would force every caller to wrap
`read_vault` in a `try` block, and one un-caught branch would surface as a
crash inside a build gate.
**Decision:** the read leg raises nothing on data. Every hostile input, every
malformed frontmatter, every spoofed name, every mis-scoped file, every
containment failure, every encoding surprise folds into a `NoteVerdict` that
carries the relpath and the reason. `read_vault` returns the whole verdict
list; `ok` is false iff any verdict's status is outside `OK_STATUSES`.
`read_exit_code(result)` mirrors `drift_exit_code` and `reconcile_exit_code`.
**Consequence:** the reader composes into a build gate the same way the
existing two verify gates compose. A caller pattern-matches on
`VaultReadResult.ok` and never on exception hierarchies. The one exception the
API does raise (`ValueError` from `read_vault_scope` on an unknown scope
string) is a wiring fault, separated by design (D-87).

## D-81 — two-phase classify_vault + load_from_plan mirrors V4 D-62
**Status:** accepted (M4.2).
**Context:** V4's `reconcile` runs classify in one pass over the surfaces and
commits in a second, so a caller can inspect every classification before any
write happens. A monolithic `read_vault` would hide the same split.
**Decision:** the reader ships the same two phases. `classify_vault` reads
every file and returns a `ReadPlan` carrying one verdict per relpath;
`load_from_plan` folds the plan into a `VaultReadResult` with the pool,
refusals, and counts. `read_vault` is the convenience composition. A caller
who wants to inspect verdicts before assembling a pool uses the two-phase form
directly.
**Consequence:** the reader's shape reads the same as V4's orchestrator. A
caller who has learned V4's two-phase idiom applies it here unchanged.

## D-82 — the hub file is skipped without a content read
**Status:** accepted (M4.2).
**Context:** the top-level `MEMORY.md` is a projection R2's write leg
regenerates from the pool (R2 D-34). The hub is not a record source; a
`canon:` fence inside it would still be write-leg output, not a hand-authored
carrier. Reading the hub's body and classifying it would either duplicate
records already loaded from the scope directories or invent verdicts for hub
content the write leg owns.
**Decision:** `MEMORY.md` at the vault root becomes `SKIPPED_HUB` on the
containment step, before any content read. The reader never opens the hub's
body.
**Consequence:** the hub stays the write leg's projection surface with no
read-side authority. A hand-edited hub does not shift the pool the reader
returns; a hub deleted between listing and read does not become a
`SKIPPED_ABSENT`. The write leg regenerates it on the next `plan_vault` run.

## D-83 — dedupe by (scope, id) first-wins under sorted iteration
**Status:** accepted (M4.2).
**Context:** two files under different relpaths that both parse to a record
with the same `(scope, id)` key would produce a pool with a duplicate record.
The write leg cannot create this state (identity names the file), so it is a
sign of external tampering, a hand-authored file with an off-identity name, or
a race with a rename. The reader has to decide which record wins.
**Decision:** the read leg iterates `sorted(list_dir(root))` and folds
verdicts through `_dedupe_verdicts` in that order. First LOADED for a
`(scope, id)` key wins; the second folds to `REFUSED_DUPLICATE_KEY` with the
first entry's relpath cited in the reason. The name-collision branch
(`REFUSED_NAME_COLLISION`) fires on the second of two loaded verdicts sharing
a `normcase`d relpath, a defensive backstop for a hash-truncation collision
that is astronomically improbable (D-77 for the transport twin).
**Consequence:** a rerun on the same filesystem returns the same verdicts.
No wall-clock heuristic, no filesystem enumeration order dependency. A caller
who sees `REFUSED_DUPLICATE_KEY` reads the reason to learn which relpath won,
resolves the collision on disk, and reruns.

## D-84 — the scope-directory match refusal is REFUSED_MIS_SCOPE
**Status:** accepted (M4.2).
**Context:** a record whose `scope` is `workspace` living under a `global/`
directory is a scope mismatch. R1 D-18 names the same rule on the surface
renderer: a region's declared scope has to match the target scope. Reusing the
name here holds the rule under one label across the two legs.
**Decision:** the read leg emits `REFUSED_MIS_SCOPE` when the scope segment of
the on-disk relpath fails to match `record.scope` under `normcase`. The
`normcase` fold covers the case-insensitive-filesystem case where the write
leg would have created the same file at a case-variant path.
**Consequence:** a caller reading a mis-scoped vault sees the same refusal
label the surface renderer emits on the same defect. The `normcase` fold means
a Windows filesystem returning `Workspace/foo.md` is not spuriously refused.

## D-85 — no per-note byte-size ceiling in M4.2
**Status:** accepted (M4.2).
**Context:** an oversized note could exhaust memory on a hostile vault. The
transport seam ships `sized-payload-limit` for the same threat. A vault reader
ceiling would fix a byte number into the container.
**Decision:** the read leg ships no per-note ceiling. A caller who needs one
imposes it by returning `None` from `read_text` above a threshold, or by
raising there and catching outside. The reader classifies `None` as
`SKIPPED_ABSENT` (D-83's neighbor); a caller-side raise never reaches the
reader.
**Consequence:** the container carries no arbitrary size number. Callers
running against untrusted vaults wrap the injected IO with their own gate.
Named as an honest null here rather than hidden as a defensive default.

## D-86 — DECLARED_READ_DROPS is frozenset(); symmetric to DECLARED_NOTE_DROPS
**Status:** accepted (M4.2).
**Context:** R2's `vault_fidelity` gate declares an empty drop set: the
one-note codec is lossless, so any observed field difference is UNDECLARED and
fails the verdict closed. The read-leg fidelity gate has to make the same
claim symmetrically, so a future contributor extending one but not the other
trips a shared-asymmetry check.
**Decision:** `vault_read_fidelity.DECLARED_READ_DROPS = frozenset()`. The
symmetric report field-diffs pool_out against pool_in with the exact
`classify_note_losses` helper R2's fidelity gate uses. Any diff is UNDECLARED;
the verdict fails closed.
**Consequence:** the two fidelity gates carry the same claim in the same
shape. A codec regression on the write leg or a side-channel drop on the read
leg surfaces as an UNDECLARED loss in the same taxonomy.

## D-87 — read_vault_scope on an unknown scope raises ValueError; a missing scope directory is SKIPPED_NOT_ALLOWED
**Status:** accepted (M4.2).
**Context:** a caller passing `read_vault_scope(root, "workspaec", ...)` (a
typo) and a filesystem that carries no `workspace/` directory look the same
from a naive gate. Folding both into one verdict would hide a wiring fault
behind a runtime data condition; raising on both would make an empty scope
directory a build-gate failure.
**Decision:** the API-level check on `scope in SCOPES` raises `ValueError`, a
wiring fault distinct from data. The runtime pathway that visits a scope
directory that happens to be empty classifies each of its (zero) entries and
returns an empty pool with `ok=True`. A path under a directory that names a
non-canon scope is a `SKIPPED_NOT_ALLOWED` verdict, not a raise.
**Consequence:** a caller who miswires a scope string hears about it at the
call site. A vault whose `global/` directory happens to hold no records reads
as an empty pool with no refusals. The two failure modes are separately
diagnosable.

## D-88 — the read leg is additive-only; no edit to any existing module
**Status:** accepted (M4.2).
**Context:** the read leg touches concerns the write leg already models
(containment, identity, frontmatter, one-note codec, single-record fidelity).
Editing R2's modules to share more surface with the read leg would risk a
regression in R2's landed guarantees.
**Decision:** M4.2 ships two new source files (`vault_reader.py`,
`vault_read_fidelity.py`) and two new test files. It edits nothing under
`vault.py`, `vault_mirror.py`, `vault_fidelity.py`, `frontmatter.py`,
`schema.py`, `backends/base.py`, or `validator.py`. The reader imports
`is_vault_write_allowed` from `vault_mirror`, `derive_note_name` and
`ingest_note` from `vault`, `parse_frontmatter` from `frontmatter`,
`classify_note_losses` from `vault_fidelity`, and `_normalize_newlines` from
`textutil`. No re-export is added anywhere.
**Consequence:** every landed R2 guarantee holds unchanged. A future
contributor extending the read leg lands on `vault_reader.py` and
`vault_read_fidelity.py`; the R2 surfaces stay under R2's own decisions.

<!-- M4.3 versions and M4.4 canon_check decisions append below in later commits. -->
