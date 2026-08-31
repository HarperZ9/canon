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

<!-- M4.2 vault-reader and M4.3 versions decisions append below in later commits. -->
