# Canon Security, Privacy, and Threat Model Audit

Date: 2026-08-30  
Lane: security and privacy  
Output status: planning evidence only. No product code, tests, manifests, package metadata, release state, deployment, or parallel I0 worktree files were edited.

## Scope and inspected evidence

This audit covers Canon plus adjacent local controls that would be used by a Canon ambient-bootstrap, capsule, receipt, or safe-IO design:

- Canon instructions, spec, audit contract, source, tests, and decisions. C: verified. P: `C:\dev\AGENTS.md`, `public/canon/CLAUDE.md`, `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md`, `public/canon/project-docs/audits/2026-08-30/README.md`, `public/canon/src/canon`, `public/canon/tests`, `public/canon/project-docs`.
- Secret Redact IO safe-IO/redaction package. C: verified. P: `public/secret-redact-io/src/secret_redact_io`, `public/secret-redact-io/tests`, `public/secret-redact-io/README.md`, `public/secret-redact-io/project-docs/public-boundary.md`.
- Emet witness/proof-surface receipt controls. C: verified. P: `public/emet/THREAT-MODEL.md`, `public/emet/SECURITY.md`, `public/emet/emet/witness_receipt.py`, `public/emet/adapters/proof_surface_receipt.py`, `public/emet/test_witness_receipt.py`, `public/emet/test_proof_surface_bundle.py`.
- Flywheel receipt, integrity, signing, and Relay local interfaces. C: verified. P: `public/flywheel/harness/receipt.py`, `public/flywheel/harness/tool_call_receipt.py`, `public/flywheel/harness/receipt_sign.py`, `public/flywheel/harness/receipt_signer.py`, `public/flywheel/harness/crypto/signatures.py`, `public/flywheel/harness/integrity.py`, `public/flywheel/relay/src/relay/local_tools.py`, `public/flywheel/relay/src/relay/hashline.py`, relevant tests.

Safety constraint followed: this report cites code/docs/tests and does not copy secrets, credentials, private databases, raw chat bodies, browser profiles, or protected material. C: verified by inspection boundary.

Index/forum note: the workspace instruction says to use `index` before architectural assumptions. `mcp__index.index_map(root=C:\dev)` and `mcp__index.index_router(root=C:\dev)` timed out within this turn, so this audit falls back to bounded filesystem and `rg` evidence. C: blocked for index evidence. Forum routing returned no decisive route and requested escalation, so it was not used to broaden scope. C: verified.

## Contract requirements that drive this threat model

- Ambient bootstrap must run before ordinary work, check freshness/trust/conflicts/budget/source reachability, present explicit unknowns/omissions, emit a bootstrap witness, and make the result visible before task execution. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:16-40`.
- A deterministic `canon.capsule/v1` manifest is expected to carry identity, authority, provenance, freshness, omissions, hashes, and compatibility metadata; `.canonpack` is optional; lossy synthesis needs addressable source spans and transformation receipts; normative instructions/permissions/goals/conflicts/unknowns may not be silently summarized away. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:45-52`.
- Initial gates include zero planted-secret transmission, 100% retention or explicit failure for planted active goals/permissions/prohibitions/conflicts, visible omissions, distinguishable stale/superseded/contradictory/untrusted/unknown facts, verified bootstrap tiers, visible mandatory bootstrap failure, and signed/attestable, secret-scanned public releases. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:111-123`.

## Trust zones

| Zone | Boundary | Primary threats | Current controls | C |
| --- | --- | --- | --- | --- |
| Z0 local sensitive state | `.env`, keys, private DBs, browser profiles, raw chats, protected material | secret/PII leakage, over-collection, right-to-forget failure | Workspace instruction forbids copying these into reports; Secret Redact IO can redact common secret-shaped output but does not authorize reads. | verified |
| Z1 Canon record pool | `Record` envelopes, validators, backends | poisoned records, stale/superseded facts, cross-scope contamination, plaintext retention | Pure schema, `validate_record`, temporal/drop guards, SQLite audit chain; FilesBackend has a path traversal gap if unvalidated records are stored. | verified/inferred |
| Z2 managed instruction surfaces | `CLAUDE.md`, `AGENTS.md`, `SOUL.md` catalog regions | prompt injection, over-broad startup instructions, symlink redirection, partial write | Fixed catalog and marker regions; writes only within managed markers; off-limits/no-marker skip; lexical allow-list only. | verified |
| Z3 vault mirror | Obsidian-style note files | poisoned visible body, path traversal, clobber, orphan deletion | Derived path names, canonical JSON carrier, no YAML loader, containment checks, orphan reporting only; plaintext. | verified |
| Z4 capsules and archives | future `CANON.md`, `canon.capsule/v1`, `.canonpack` | malicious archives, forged/replayed/stale capsules, selective disclosure failure | Spec exists; no Canon source/test implementation found in bounded search. | verified/inferred |
| Z5 receipts/signatures | Canon witnesses, Emet receipts, Flywheel receipts | self-signed trust laundering, missing TTL/replay defense, optional witness emission | Emet content addressing, optional HMAC; Flywheel signed receipts and tool-call seals; some paths are integrity receipts, not trust receipts. | verified/inferred |
| Z6 host adapters/startup hooks | Codex, Claude Code, ChatGPT, Cursor, Copilot, generic APIs, MCP/A2A | false "enforced" claims, fail-open startup, stale import, broad hooks | Spec requires truthful tiers; current Canon source has no bootstrap adapter implementation. | verified |
| Z7 model context | local/cloud model prompt windows | secret leakage, prompt injection, unsafe synthesis, dropped prohibitions | Canon V3 can measure persona basis freshness, not synthesis faithfulness; Secret Redact IO can redact output shapes before model exposure. | verified |
| Z8 local tool interfaces | Relay/Flywheel local file/exec tools | path traversal, exec escape, shell injection, poisoned history tool calls | Relay file tools use realpath root containment and default-deny write/exec; Relay explicitly says allowed shell can reach outside root. | verified |
| Z9 public release/supply chain | package metadata, deps, CI, fixtures | dependency takeover, unsigned artifacts, fixture poisoning | Canon/Secret Redact IO/Emet/Flywheel have small or zero runtime dependency surfaces; signed/attestable release and SBOM gates are not yet evidenced for Canon. | verified/inferred |

## Proposed trust labels and safe defaults

Trust labels should be carried in both machine manifests and human surfaces. The label must be a decision input, not decoration.

| Label | Meaning | Default behavior |
| --- | --- | --- |
| `trusted-local` | Produced from local Canon state and current source hashes on this machine. | May be loaded if freshness, secret scan, conflict, and budget gates pass. |
| `signed-pinned` | Signed by a key pinned in a Canon trust store for the target scope/principal. | May be treated as authenticated for that scope until expiry/replay gates fail. |
| `signed-unknown-key` | Signature verifies structurally, but key is not pinned for the scope. | Integrity-only. Quarantine as untrusted import. |
| `unsigned-local` | Locally produced without a signature. | Local advisory only. Do not export as trusted. |
| `imported-untrusted` | External capsule/archive or copied instruction body. | Quarantine. Never silently import into startup instructions. |
| `model-synthesized-unreviewed` | Generated or summarized by a model without source-span receipt review. | Cannot carry normative permissions, prohibitions, active goals, or conflicts. |
| `secret-quarantined` | Secret/PII detector, protected-path match, or policy block triggered. | Do not transmit to model or export; show typed omission only. |
| `stale` | Freshness TTL, source-state hash, supersession, or reachability check failed. | Fail enforced bootstrap; advisory/guided flows must visibly degrade. |
| `public-exportable` | Cleared for public docs/releases by secret scan, license/provenance gate, and selective-disclosure policy. | Exportable with receipt. |
| `private-local-only` | Safe to retain locally but not expose to cloud/provider/public surfaces. | Excluded from cloud prompts and public artifacts by default. |

Safe defaults:

- Default-deny import: no external record, capsule, archive entry, or generated instruction becomes active until schema, trust, freshness, conflict, source-reachability, secret/PII, and budget checks pass. C: inferred from spec requirements.
- Mandatory bootstrap failure must fail closed for an `Enforced` adapter and must visibly classify the failure for advisory/guided adapters. It must never continue with apparently fresh context. C: verified requirement. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:38-40`, `:119-120`.
- Unsigned or self-signed receipts prove at most internal integrity. They do not prove authority, currentness, non-replay, user consent, or safe disclosure. C: inferred from Emet/Flywheel receipt code.
- No `.canonpack` extraction should occur before manifest-only preflight rejects absolute paths, `..`, alternate data streams, symlinks/junctions/reparse points, duplicate normalized names, case-fold collisions, oversize files, decompression bombs, and unsupported compression. C: inferred because `.canonpack` is specified but no implementation was found.
- Redact before model exposure and before export, not after logging. Redaction is not permission to read a protected file. C: inferred from Secret Redact IO boundaries.
- Normative instructions, active goals, permissions, prohibitions, conflicts, and unknowns cannot pass through lossy model synthesis unless every statement has source identity and a transformation receipt. C: verified requirement. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:50-52`, `:113-117`.

## Findings

🔴 CRITICAL

File: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:16`

Issue: Ambient bootstrap and `canon.capsule/v1` are required by the spec, but no Canon source/test implementation was found for bootstrap, capsule, `.canonpack`, freshness, trust labels, telemetry, retention, or right-to-forget terms in the bounded source/test search.

Why: The highest-risk path is silent continuity import. If the product claims ambient bootstrap before fail-closed startup, freshness/security classification, and witness emission are implemented, a host can start ordinary work with stale, poisoned, untrusted, or secret-quarantined context while appearing fresh. This directly violates the spec's requirement that mandatory bootstrap failure never silently degrade.

Fix: Build a deterministic bootstrap state machine before adapter claims:

1. `detect -> resolve_layers -> preflight -> compile_capsule -> present -> readiness_probe -> witness -> release_to_work`.
2. Treat every required preflight failure as terminal for `Enforced`; advisory/guided flows must display `unsupported`, `stale`, `secret_quarantine`, `conflict`, `budget_incompatible`, `source_unreachable`, or `authority_untrusted`.
3. Make witness emission mandatory for enforced starts, with a hard error if the receipt cannot be written.
4. Add source/test coverage for `bootstrap`, `capsule`, `.canonpack`, freshness, trust labels, retention, deletion, and telemetry policy terms.

Evidence:

- Spec lifecycle and fail-closed ambient-bootstrap requirement. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:16-40`, `:111-120`.
- Bounded search `rg -n "bootstrap|capsule|canonpack|ambient|freshness|trust_label|retention|right[-_ ]?to[-_ ]?forget|telemetry|analytics|phone home|startup|start[-_ ]?up" public/canon/src public/canon/tests` returned no matches. C: verified.
- Canon reconcile witness is optional. C: verified. P: `public/canon/src/canon/reconcile_run.py:91-136`.
- Flywheel tool-call receipt emission is explicitly non-fatal, which is fine for ordinary tool telemetry but not acceptable for mandatory bootstrap witnessing. C: verified. P: `public/flywheel/harness/tool_call_receipt.py:190-207`.

Confidence: High.

🔴 CRITICAL

File: `public/canon/src/canon/backends/files.py:42`

Issue: `FilesBackend` constructs filesystem paths with an unvalidated `scope` segment. `record_key` returns `f"{record.scope}/{record.id}"`; `split_key` takes the first path segment as scope; `_path` joins `self._root / scope / quoted_id.json`; `put` calls `guard_put` but not `validate_record`.

Why: `validate_record` rejects unknown scopes, but the backend does not enforce it. If a hostile or malformed `Record` reaches `FilesBackend.put`, `scope=".."` or other path-control strings can cause writes outside the backend root. This is an implementation-level path traversal risk that becomes critical if future capsule import writes records from external manifests.

Fix: Enforce semantic validation before path derivation in every backend `put` path, or make `Record` construction impossible with invalid scopes. Minimum:

- Call `validate_record(record)` inside `guard_put` or each backend before `record_key(record)`.
- Reject absolute, drive-qualified, `.`/`..`, separator-bearing, or non-`SCOPES` scope values before any filesystem path is computed.
- Add tests where `Record(scope="..")`, `Record(scope="../x")`, `Record(scope="global/../../x")`, and Windows drive-shaped values fail and leave no file outside the temp backend root.

Evidence:

- Valid scopes are only `global` and `workspace`. C: verified. P: `public/canon/src/canon/schema.py:62-67`.
- `validate_record` flags unknown scopes. C: verified. P: `public/canon/src/canon/validator.py:84-105`.
- `record_key` and `split_key` use the raw scope/id string pair. C: verified. P: `public/canon/src/canon/backends/base.py:78-89`.
- `guard_put` checks kind and declared drops, not full record validity. C: verified. P: `public/canon/src/canon/backends/base.py:115-125`.
- `FilesBackend._path` joins raw `scope`; only `id` is URL-quoted. C: verified. P: `public/canon/src/canon/backends/files.py:42-50`.
- Existing files-backend scope test only covers valid scope placement. C: verified. P: `public/canon/tests/test_files_backend.py:66-71`.

Confidence: High.

🟡 WARNING

File: `public/emet/emet/witness_receipt.py:118`

Issue: Emet receipt re-derivation and proof-surface bundle re-derivation join manifest/receipt paths to a base directory without a visible containment check.

Why: A malicious receipt or bundle manifest can name `../...`, an absolute path, or a platform-specific escape path. If Canon reuses these routines to verify `.canonpack` evidence or capsule references, verification can unintentionally read and hash files outside the intended evidence directory. Hashing is less severe than copying contents, but it can still leak existence/timing metadata, consume protected paths, or turn private local state into evidence identifiers.

Fix: Add a shared safe-path resolver for receipt/bundle re-derivation:

- Reject absolute paths, drive-qualified paths, `..`, empty names, path separators where only names are expected, Windows alternate data streams, and symlink/junction escapes.
- Use `realpath`/commonpath containment on the resolved target.
- Return `UNVERIFIABLE` for unsafe path entries before opening files.
- Add red-team tests for `../outside`, absolute paths, case-fold duplicates, symlinks/junctions, and nested manifests.

Evidence:

- Emet `_recompute` resolves `full = path if base_dir is None else os.path.join(base_dir, path)` and opens it. C: verified. P: `public/emet/emet/witness_receipt.py:118-125`.
- Proof-surface `_rederive_files` calls `sha256(os.path.join(bundle_dir, name))`. C: verified. P: `public/emet/adapters/proof_surface_receipt.py:152-174`.
- Emet proof-surface adapter does refuse authority tokens in stdout/manifests, but that is separate from path containment. C: verified. P: `public/emet/adapters/proof_surface_receipt.py:79-87`, `:188-195`.

Confidence: High.

🟡 WARNING

File: `public/flywheel/harness/crypto/signatures.py:182`

Issue: Available receipt signing verifies structure, but Canon does not yet have a pinned trust-root, freshness, or replay model for capsules.

Why: A structurally valid signature over attacker-controlled content is not proof that the signer is trusted for a Canon scope, that the capsule is current, or that it has not been replayed after revocation/supersession. Flywheel's wrapper verifies using the embedded public key; Emet's HMAC is optional and only meaningful when producer and verifier already share a key channel. Without key pinning, expiry, nonce/session identity, and replay cache, signatures can launder untrusted capsules into apparently valid continuity artifacts.

Fix:

- Add a Canon trust store that pins key fingerprints to scope/principal/capability and declared purpose.
- Require `issued_at`, `expires_at`, `source_state_sha256`, `capsule_sha256`, `producer_key_fingerprint`, `sequence` or nonce, and adapter target in signed bootstrap/capsule receipts.
- Reject unknown-key signatures as `signed-unknown-key`, not trusted.
- Maintain a local replay cache for accepted capsule IDs/nonces per target surface and invalidate stale/superseded source-state hashes.
- Bind signatures to the canonical capsule bytes plus the declared `signed_over` coverage list.

Evidence:

- Emet receipts are content-addressed point-in-time snapshots; optional HMAC adds assurance only with a pre-shared key channel. C: verified. P: `public/emet/emet/witness_receipt.py:18-31`.
- Emet emits `issued_at` and optional signature but no expiry/replay field in the shown receipt construction. C: verified. P: `public/emet/emet/witness_receipt.py:211-228`.
- Emet check treats a signed receipt without a key as unverifiable, which is correct but not a trust-store design. C: verified. P: `public/emet/emet/witness_receipt.py:280-288`.
- Flywheel `wrap_signed_receipt` embeds the public key and fingerprint; `verify_signed` verifies with the embedded public key. C: verified. P: `public/flywheel/harness/crypto/signatures.py:149-177`, `:182-215`.

Confidence: High.

🟡 WARNING

File: `public/secret-redact-io/src/secret_redact_io/file_io.py:12`

Issue: Secret Redact IO is a useful redaction and hash-only receipt boundary, but it is not an authorization, PII-complete, root-confinement, or SSRF boundary.

Why: The package reads arbitrary file paths passed by the caller, writes arbitrary targets passed by the caller, fetches arbitrary HTTP(S) URLs up to `max_bytes`, and runs arbitrary argv passed by the caller. That is appropriate for a low-level safe-IO primitive, but Canon must not treat redaction as permission to read protected paths or call internal network resources. Pattern rules also cover common secret-shaped values, not all PII or confidential business content.

Fix:

- Wrap Secret Redact IO in Canon-specific policy before use: root allow-list, protected-path deny-list, `.env`/key/browser-profile/private-DB blocks, SSRF/private-network denial, max-size and content-type limits, and PII classifiers for export.
- Carry redaction counts and typed omissions into capsule manifests.
- Fail export if any secret detector hits in a field that is not explicitly omittable.

Evidence:

- Default rules cover common secret-shaped values including private keys, OpenAI keys, GitHub tokens, JWTs, bearer tokens, and credential assignments. C: verified. P: `public/secret-redact-io/src/secret_redact_io/redaction.py:28-83`.
- Receipts store byte counts and hashes for raw/redacted content, not raw values. C: verified. P: `public/secret-redact-io/src/secret_redact_io/receipts.py:18-23`, `:34-59`; `public/secret-redact-io/README.md:13-41`.
- File read/write accept caller-provided paths and do not apply Canon root/protected-material policy themselves. C: verified. P: `public/secret-redact-io/src/secret_redact_io/file_io.py:12-50`.
- Fetch allows only HTTP(S) and has `max_bytes`, but no private-host/SSRF denylist is visible. C: verified. P: `public/secret-redact-io/src/secret_redact_io/fetch_io.py:12-38`.
- Exec uses `subprocess.run(list(argv), shell=False)` and redacts stdout/stderr, but arbitrary command selection remains a caller policy problem. C: verified. P: `public/secret-redact-io/src/secret_redact_io/exec_io.py:12-41`.

Confidence: High.

🟡 WARNING

File: `public/canon/project-docs/F1-DECISIONS.md:11`

Issue: Canon currently stores memory/persona/decision material in plaintext and does not yet show retention, deletion, tombstone, purge, export-subject, or right-to-forget semantics.

Why: Plaintext storage is honestly documented, but a continuity system will hold sensitive memory, identity, provenance, and possibly authority records. Without data classification, retention periods, deletion semantics, and selective-disclosure filtering, Canon cannot safely support privacy promises or operator/user deletion requests. Vault notes and instruction surfaces can also replicate record content into multiple plaintext surfaces.

Fix:

- Add per-record sensitivity labels, retention policy, deletion/tombstone records, purge receipts, and export filters.
- Implement a cipher-wrapper backend before any deployment that needs at-rest confidentiality.
- Define right-to-forget behavior across SQLite, files backend, vault mirror, managed instruction surfaces, capsule manifests, `.canonpack`, receipts, and backups.
- Require privacy export tests that prove deletion removes or tombstones all derived surfaces and that typed omissions remain visible without leaking content.

Evidence:

- F1 explicitly stores plaintext and has no encryption-at-rest wrapper yet. C: verified. P: `public/canon/project-docs/F1-DECISIONS.md:11-19`.
- SQLite stores the canonical envelope text verbatim and appends hash-chained audit entries. C: verified. P: `public/canon/src/canon/backends/sqlite.py:1-8`, `:53-80`, `:95-107`.
- Vault note rendering projects records into Markdown and reconstructs from the `canon:` JSON carrier. C: verified. P: `public/canon/src/canon/vault.py:261-296`.
- Bounded Canon source/test search found no retention, right-to-forget, or deletion-policy implementation terms. C: verified.

Confidence: High.

🟡 WARNING

File: `public/canon/src/canon/registry.py:70`

Issue: Symlink/junction hardening is inconsistent across the relevant systems; Canon's instruction-surface allow-list is lexical, while Relay file tools use realpath containment.

Why: Canon's registry protects against string traversal to non-catalog paths, but a symlink/junction/reparse point planted at an allow-listed path could redirect reads or writes to a different location. The Canon decision docs explicitly scope this out for the deterministic guard. That is acceptable for a unit-tested pure path catalog, but not enough for release/bootstrap code that edits high-impact startup instruction files.

Fix:

- For bootstrap/release modes, reject symlinks, junctions, and reparse points at the target file and every parent under injected roots before reading or writing.
- Use realpath/commonpath containment in operational write paths while keeping pure lexical guards as deterministic preflight.
- Add Windows junction and symlink fixtures for `CLAUDE.md`, `AGENTS.md`, vault note targets, and `.canonpack` extraction.

Evidence:

- Registry allow-list uses `normpath`/`normcase` exact path comparison. C: verified. P: `public/canon/src/canon/registry.py:58-77`.
- R1 decision docs state symlink planted at an allow-listed path is out of scope for that guard. C: verified. P: `public/canon/project-docs/R1-DECISIONS.md:68-76`.
- Vault containment is also lexical/commonpath and the R2 docs discuss symlink tradeoff. C: verified. P: `public/canon/src/canon/vault_mirror.py:77-107`; `public/canon/project-docs/R2-DECISIONS.md:173-183`.
- Relay file tools use `realpath` root containment. C: verified. P: `public/flywheel/relay/src/relay/local_tools.py:117-122`.

Confidence: High.

🟡 WARNING

File: `public/canon/src/canon/registry.py:144`

Issue: Canon's current write/reconcile paths plan before writing, but do not provide durable transactionality, cross-process locks, compare-and-swap source-state checks, or concurrent-launch handling.

Why: The spec requires launch-time behavior when multiple chats start concurrently, a workspace is dirty, or a capsule changes during a session. Current surface writes protect against Canon's own planning refusals before the first write, but a filesystem fault after earlier writes is not rolled back. SQLite uses the default connection timeout and no visible source-generation compare-and-swap for a bootstrap capsule. Concurrent launches can therefore race to compile/use different source states or produce partial surface updates.

Fix:

- Add a bootstrap/reconcile run lock scoped by workspace and target surface.
- Bind every capsule and witness to `source_state_sha256`, working tree state, and run sequence.
- Before writing, compare current source-state hashes to the preflighted state; if they changed, abort as `source_changed`.
- Make witness emission idempotent per run and record partial-write outcomes explicitly.
- Add two-process tests for simultaneous bootstrap, mid-session capsule change, and filesystem write failure after first surface commit.

Evidence:

- `write_surfaces` plans all Canon checks before commit, but documents no rollback on filesystem fault during commit. C: verified. P: `public/canon/src/canon/registry.py:144-183`.
- `reconcile` classifies then writes/gates/witnesses, and the witness is optional. C: verified. P: `public/canon/src/canon/reconcile_run.py:91-136`.
- SQLite backend uses a local SQLite connection with `timeout=10`, but no Canon-level capsule/source compare-and-swap is visible. C: verified. P: `public/canon/src/canon/backends/sqlite.py:42-80`.
- Spec explicitly asks audit to cover concurrent launches, dirty workspace, different machine, offline/quota exhaustion, and capsule changes during session. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:38-40`.

Confidence: High.

🟡 WARNING

File: `public/canon/src/canon/schema.py:35`

Issue: The current Canon record schema has only five memory/decision/artifact record kinds and only `global`/`workspace` scopes. It does not yet model explicit authority/permission/prohibition records, tenant/project/device boundaries, or cloud/local disclosure classes.

Why: The capsule spec requires typed authority, permissions, active goals, unresolved conflicts, and unknowns. Without first-class records and policy evaluation for those concepts, Canon cannot prove 100% retention, prevent authority laundering, or prevent cross-tenant/project contamination. A `workspace` scope is too broad for multi-repo, multi-client, or cloud/local separation when capsules move between machines or hosts.

Fix:

- Add explicit typed records for authority grants, prohibitions, active goals, unresolved conflicts, unknowns, disclosure labels, tenant/project/device identities, and cloud/local eligibility.
- Add a precedence/policy evaluator that can retain or fail on conflicts deterministically.
- Add cross-tenant fixtures proving records from workspace A cannot enter workspace B unless a signed, scoped import policy allows it.

Evidence:

- Current kinds are `personality-block`, `episodic-memory`, `synthesized-persona-l3`, `adr-decision`, and `research-artifact-ref`. C: verified. P: `public/canon/src/canon/schema.py:35-48`.
- Current render scopes are `global` and `workspace`; `repo` is deliberately absent. C: verified. P: `public/canon/src/canon/schema.py:62-67`.
- Bounded source/test search for `authz|authority|permission|approval|operator` returned no Canon implementation matches. C: verified.
- Spec requires retention of active goals, permissions, prohibitions, and conflicts. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:111-117`.

Confidence: High.

🟡 WARNING

File: `public/canon/src/canon/persona_thesis.py:1`

Issue: Canon has structural checks for synthesized-persona basis freshness, but no implemented guard for semantic prompt injection, poisoned histories, or unsafe model-assisted synthesis.

Why: V3 explicitly says Canon cannot judge whether synthesized persona text is faithful to source memories; it measures only whether sources are present and not superseded. That is an honest control, not a prompt-injection defense. Future capsules can carry poisoned visible prose, malicious instructions embedded in memory text, or lossy summaries that drop prohibitions unless synthesis outputs are quarantined and source-span receipts are enforced.

Fix:

- Treat all imported visible prose and model-synthesized summaries as `model-synthesized-unreviewed` until reviewed or mechanically linked to source spans and transformation receipts.
- Add prompt-injection detectors and policy checks for instruction-like content in non-instruction records.
- Require lossless retention or explicit failure for normative instructions, permissions, prohibitions, active goals, conflicts, and unknowns.
- Add tests where poisoned histories attempt to override system/developer/user instructions, request secret exfiltration, or remove prohibitions from small-budget capsules.

Evidence:

- Canon states it cannot re-run or judge synthesis faithfulness, only structural basis health. C: verified. P: `public/canon/src/canon/persona_thesis.py:1-18`.
- Empty or absent persona basis becomes honest null/UNVERIFIABLE, which is good but not semantic safety. C: verified. P: `public/canon/src/canon/persona_thesis.py:112-146`, `:167-189`.
- Vault ingest reconstructs from `canon:` JSON, not visible body, which protects integrity but does not classify hostile authoritative text inside the JSON payload. C: verified/inferred. P: `public/canon/src/canon/vault.py:282-296`.
- Spec requires lossy synthesis source spans and transformation receipts. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:50-52`.

Confidence: High.

🟡 WARNING

File: `public/flywheel/relay/src/relay/local_tools.py:75`

Issue: Relay/Flywheel local exec controls are honest, but any Canon startup hook or capsule adapter must not inherit broad `run`/exec power by default.

Why: Relay correctly defaults writes and exec off and documents that allowing exec implies write and can reach outside root. Ambient bootstrap code tends to run at session start, where user intent may only be "load context", not "grant shell". If bootstrap adapters reuse local tools with exec enabled, poisoned histories or generated instructions could escalate from continuity import to arbitrary local actions.

Fix:

- Bootstrap adapters should run with read-only, root-confined capabilities by default.
- Require explicit operator action for write/exec/network/plugin/secrets scopes, with scope recorded in the bootstrap witness.
- For any readiness probe, use deterministic local checks rather than shell commands unless a signed adapter policy permits specific argv.

Evidence:

- Relay `ToolGate` defaults `allow_write=False`, `allow_exec=False`; enabling exec implies write. C: verified. P: `public/flywheel/relay/src/relay/local_tools.py:75-90`.
- Relay documents that `run` sets cwd only and allowed shell can reach outside root. C: verified. P: `public/flywheel/relay/src/relay/local_tools.py:1-8`, `:296-300`.
- Relay file tools are root-confined via realpath, so the risk is specifically the exec path and any over-broad bootstrap hook. C: verified. P: `public/flywheel/relay/src/relay/local_tools.py:117-122`.

Confidence: High.

🟡 WARNING

File: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:47`

Issue: Malicious archive handling for `.canonpack` is not yet evidenced.

Why: The spec introduces `.canonpack`, which implies archive parsing and reference preservation. Archive formats create a separate attack surface: zip-slip paths, absolute paths, symlink entries, duplicate normalized filenames, case-fold collisions, decompression bombs, embedded private files, and poisoned manifests. Because no implementation was found, the safest current state is "not implemented"; any future implementation must be designed as hostile-input parsing.

Fix:

- Parse manifests before extracting.
- Extract only into a newly created, empty, explicit temp directory.
- Reject unsafe names and symlinks/junctions/reparse points before writing.
- Enforce file count, total uncompressed size, compression ratio, MIME/extension allow-list, and per-entry digest checks.
- Do not include raw evidence by default; use by-reference evidence identities and typed omissions.

Evidence:

- Spec introduces optional `.canonpack`. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:47-48`.
- Bounded Canon source/test search found no `canonpack` implementation. C: verified.
- Existing Canon vault/archive-adjacent path controls are for known generated paths, not arbitrary hostile archive entries. C: inferred from `public/canon/src/canon/vault.py:72-91` and `public/canon/src/canon/vault_mirror.py:77-107`.

Confidence: High.

🟡 WARNING

File: `public/canon/pyproject.toml:13`

Issue: The current local dependency surface is small, but Canon release/supply-chain gates are not yet evidenced at the level the spec requires.

Why: Zero or low runtime dependencies reduce dependency-confusion and transitive risk. They do not by themselves provide reproducible builds, signed or attestable releases, SBOM/provenance, package-name control, conformance fixtures, or secret scanning. The spec makes public releases a security gate, not a documentation afterthought.

Fix:

- Add a release gate that produces reproducible artifacts, hashes, signed attestations, SBOM, license/provenance check, secret scan, fixture conformance run, and publish dry-run.
- Pin optional dependency ranges for signing/test extras and document minimum crypto backend versions.
- Ensure Canon-compatible fixtures cannot silently drift by hash-tracking fixture inputs and outputs.

Evidence:

- Canon runtime dependencies are empty; dev dependency includes pytest. C: verified. P: `public/canon/pyproject.toml:6-16`.
- Secret Redact IO and Emet also have small/zero runtime dependency surfaces. C: verified. P: `public/secret-redact-io/pyproject.toml:6-13`, `public/emet/pyproject.toml:6-24`.
- Flywheel runtime dependencies are empty and signing is optional via `cryptography`. C: verified. P: `public/flywheel/pyproject.toml:20-41`.
- Spec requires public releases to be reproducible, signed/attestable, secret-scanned, licensed, documented, and backed by conformance fixtures. C: verified. P: `public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md:123`.

Confidence: Medium.

🔵 INFO

File: `public/canon/src/canon/surface.py:39`

Issue: Existing Canon region and surface controls are strong for their current scope.

Why: Managed instruction writes are confined to explicit marker regions, no-marker files are off-limits, scope mismatches fail, and bytes outside markers are preserved. This materially reduces accidental prompt-surface clobbering.

Fix: Keep these invariants as release gates for any future bootstrap adapter and require conformance fixtures for every adapter surface.

Evidence:

- `apply_surface` refuses no-region and scope mismatch before writing and preserves outside bytes by splicing only the rendered interior. C: verified. P: `public/canon/src/canon/surface.py:39-54`.
- `write_surfaces` rejects non-catalog surfaces and plans Canon refusals before commit. C: verified. P: `public/canon/src/canon/registry.py:144-183`.
- Canon instructions summarize R0/R1/V2/V4 fail-closed drift and surface behavior. C: verified. P: `public/canon/CLAUDE.md:41-78`, `:114-123`, `:162-202`.

Confidence: High.

🔵 INFO

File: `public/canon/src/canon/frontmatter.py:1`

Issue: Vault note codec avoids general YAML loading and uses a canonical JSON carrier.

Why: This is a good control against YAML object-construction attacks and visible-body tampering. It also keeps the authoritative payload mechanically reconstructable.

Fix: Preserve this design, but add trust labels and disclosure labels to the carrier before using vault notes as import inputs.

Evidence:

- Frontmatter reader runs no YAML loader and reconstructs from `canon:` JSON. C: verified. P: `public/canon/src/canon/frontmatter.py:1-18`.
- Vault note path derives from scope/id digest and never uses raw id as a path segment. C: verified. P: `public/canon/src/canon/vault.py:72-91`.
- `render_note` validates records and refuses unprojectable content before emitting. C: verified. P: `public/canon/src/canon/vault.py:223-279`.
- Orphans are reported and never deleted. C: verified. P: `public/canon/src/canon/vault_mirror.py:278-300`.

Confidence: High.

🔵 INFO

File: `public/secret-redact-io/src/secret_redact_io/receipts.py:18`

Issue: Secret Redact IO correctly keeps receipts hash-only for covered cases.

Why: Hash-only receipts allow downstream systems to prove a redacted boundary ran without embedding the raw secret-shaped payload in logs or artifacts.

Fix: Use it as a primitive inside a broader Canon policy wrapper; do not weaken the receipt format by adding raw excerpts.

Evidence:

- Receipt fields store `raw_bytes`, `redacted_bytes`, input/redacted hashes, redaction counts, and metadata. C: verified. P: `public/secret-redact-io/src/secret_redact_io/receipts.py:18-23`, `:34-59`.
- Tests assert secrets do not appear in receipts and outputs are redacted for file/exec/fetch paths. C: verified. P: `public/secret-redact-io/tests/test_file_io.py:6-18`, `:32-42`; `public/secret-redact-io/tests/test_exec.py:8-18`; `public/secret-redact-io/tests/test_fetch.py:22-37`; `public/secret-redact-io/tests/test_receipts.py:8-27`.

Confidence: High.

🔵 INFO

File: `public/emet/THREAT-MODEL.md:35`

Issue: Emet's no-actuation and authority-laundering posture is a useful pattern for Canon.

Why: Emet separates verification from authority/action. It emits hashes/verdicts rather than target contents, treats denial/unreadability as UNVERIFIABLE, and refuses authority-shaped tokens in proof-surface receipts.

Fix: Reuse the pattern for Canon capsule receipts: receipts can say what was checked and what they do not prove, but cannot by themselves grant permission or start tool actions.

Evidence:

- Emet threat model says receipts emit hashes/verdicts, not artifact contents, and DoS becomes UNVERIFIABLE. C: verified. P: `public/emet/THREAT-MODEL.md:35-39`.
- Emet threat model calls out authority laundering and a zero-actuation boundary. C: verified. P: `public/emet/THREAT-MODEL.md:42-54`.
- Proof-surface receipt adapter refuses authority tokens before forming a trusted verdict. C: verified. P: `public/emet/adapters/proof_surface_receipt.py:79-87`, `:188-195`.

Confidence: High.

🔵 INFO

File: `public/flywheel/harness/receipt.py:197`

Issue: Flywheel receipts and integrity controls provide useful release-gate primitives.

Why: Flywheel separates subject identity from claim identity, derives `does_not_prove`, hashes raw tool output instead of carrying it, and has reward-hacking/integrity scans. Those mechanics fit Canon's need to avoid receipts becoming fake passports.

Fix: Reuse the primitives only with Canon-specific trust, freshness, disclosure, and fail-closed bootstrap policy layered on top.

Evidence:

- Receipt design separates `subject_sha256` and `claim_sha256` and derives `does_not_prove`. C: verified. P: `public/flywheel/harness/receipt.py:4-15`, `:197-230`.
- Tool-call receipts hash args/output and include no raw content. C: verified. P: `public/flywheel/harness/tool_call_receipt.py:113-143`.
- Verification checks seal before interpreting sealed fields. C: verified. P: `public/flywheel/harness/tool_call_receipt.py:219-263`.
- Integrity guard detects protected test edits and reward-hacking patterns. C: verified. P: `public/flywheel/harness/integrity.py:78-117`, `:140-229`.

Confidence: High.

🔵 INFO

File: `public/flywheel/relay/src/relay/hashline.py:1`

Issue: Relay's file-tool and hashline controls are good patterns for Canon adapter test fixtures.

Why: Realpath root confinement and content-addressed line anchors directly address path traversal and stale-edit classes in local tool use.

Fix: Add comparable stale/cross-root fixtures to Canon bootstrap and capsule import tests.

Evidence:

- Relay file tools use realpath root containment. C: verified. P: `public/flywheel/relay/src/relay/local_tools.py:117-122`.
- Hashline anchors include line position and content; stale anchors fail closed. C: verified. P: `public/flywheel/relay/src/relay/hashline.py:1-6`, `:42-49`.
- Relay tests cover read escape denial and stale edit failure. C: verified. P: `public/flywheel/relay/tests/test_local_agentic.py:33-40`; `public/flywheel/relay/tests/test_hashline_edits.py:114-141`.

Confidence: High.

## Threat coverage matrix

| Threat | Current control | Honest gap | Severity | Confidence |
| --- | --- | --- | --- | --- |
| Secret leakage | Secret Redact IO redacts common secret-shaped outputs and uses hash-only receipts. | Canon lacks product-level protected-path, PII, cloud/export, and deletion policy. | High | High |
| PII leakage | None found beyond generic redaction primitives. | No PII taxonomy, consent, minimization, or export deletion model found. | High | High |
| Prompt injection | Region markers, off-limits surfaces, Emet authority-token refusal. | No Canon poisoned-history classifier, no semantic synthesis guard, no quarantine labels. | High | High |
| Authority laundering | Emet refuses authority-shaped proof tokens and has no-actuation boundary. | Canon lacks first-class authority/permission/prohibition records and trust-root evaluation. | High | High |
| Forged capsules | Flywheel/Emet provide integrity primitives. | No Canon capsule implementation, key pinning, or unknown-key downgrade found. | High | High |
| Replayed/stale capsules | Canon temporal records and drift checks exist for current surfaces. | No capsule expiry, nonce, replay cache, source-state CAS, or host-start freshness gate found. | High | High |
| Over-broad startup hooks | Spec requires truthful tiers and visible failure. | No implemented adapters; risk of claiming enforced lifecycle without host control. | Critical | High |
| Cross-tenant contamination | Current scopes distinguish global/workspace. | No tenant/project/device/cloud-local boundary records. | High | High |
| Symlink/path traversal | Canon lexical gates; Relay realpath file gate; vault derived names. | FilesBackend traversal via unvalidated scope; Canon symlink out-of-scope for registry/vault. | Critical/High | High |
| Malicious archives | No extraction code found. | `.canonpack` design must handle hostile archives before implementation. | High | High |
| Unsafe model-assisted synthesis | Persona basis freshness checked structurally. | Faithfulness and prompt-injection safety are not judged; source-span receipts not implemented. | High | High |
| Supply chain | Low dependency surface. | No evidenced Canon signed release/SBOM/reproducibility/conformance release pipeline. | Medium | Medium |
| Selective disclosure | Spec names selective-disclosure capsules. | No implemented labels/export filters found. | High | High |
| Retention/deletion/right-to-forget | Orphans are reported not deleted; plaintext is honest. | No retention, tombstone, purge, or derived-surface deletion model found. | High | High |
| Concurrent launches | SQLite timeout and plan-before-write reduce some local conflicts. | No bootstrap locks/source-state compare-and-swap/concurrent session policy found. | High | High |
| Cloud/local boundary | Local-first design and safe IO primitives exist. | No per-record cloud eligibility, provider prompt policy, or telemetry policy implementation found. | High | High |
| Signatures/encryption/key handling | Emet HMAC optional; Flywheel Ed25519/HMAC support; Canon plaintext disclosed. | No Canon trust store, no key rotation/revocation, no encryption wrapper, no passphrase-backed key policy found. | High | High |
| Telemetry | No Canon source/test telemetry implementation found. | No explicit product telemetry policy found in Canon source; future telemetry must be opt-in and content-free. | Medium | High |
| Denial/fail-open | Canon drift/reconcile tends to fail closed; Emet unreadable becomes UNVERIFIABLE. | Flywheel tool receipt emission is non-fatal; bootstrap witness must not inherit that fail-open posture. | High | High |

## Red-team fixtures and acceptance tests

These are release-blocking fixtures for the security lane.

| ID | Fixture | Expected result | Evidence target |
| --- | --- | --- | --- |
| SEC-001 | `FilesBackend.put(Record(scope="..", id="escape", ...))` | Raises validation error; no file outside backend root. | Fixes critical FilesBackend traversal. |
| SEC-002 | `FilesBackend.get("../x")` and imported capsule record with separator/drive-shaped scope | Rejects before path open/write. | Backend key parser hardened. |
| SEC-003 | Allow-listed `AGENTS.md` path replaced by symlink/junction to outside root | Operational bootstrap/release write refuses before read/write. | Symlink release guard. |
| SEC-004 | `.canonpack` with `../`, absolute paths, Windows drive paths, alternate data streams, duplicate case-fold names, symlink entries, and decompression bomb | Manifest preflight rejects; no extraction outside temp dir; typed failure. | Malicious archive gate. |
| SEC-005 | Capsule signed by unknown key with valid Ed25519 signature | Classified `signed-unknown-key`; not imported as trusted. | Trust-store gate. |
| SEC-006 | Previously valid capsule replayed after expiry/source-state supersession | Fails as `stale` or `replay`; enforced bootstrap stops before ordinary work. | Freshness/replay gate. |
| SEC-007 | Two sessions compile capsules concurrently while source state changes mid-run | One canonical source-state wins; stale run aborts with visible `source_changed`. | Concurrent launch gate. |
| SEC-008 | Poisoned history record says to ignore current instructions or exfiltrate secrets | Record remains data, not instruction; capsule marks injection risk or quarantines; no startup instruction import. | Prompt-injection gate. |
| SEC-009 | Small-budget capsule tries to drop a planted prohibition, active goal, permission limit, unresolved conflict, or unknown | Build fails explicitly; no silent summary. | 100% retention gate. |
| SEC-010 | Secret-shaped values, private key fixture, `.env`, browser-profile path, private DB path, SSN/email/phone PII fixture | Secret transmission is zero; protected paths not read; PII redacted/omitted per policy. | Privacy/export gate. |
| SEC-011 | Secret Redact fetch attempts `127.0.0.1`, link-local, RFC1918, metadata IP, and DNS rebinding | Canon wrapper blocks before request. | SSRF gate. |
| SEC-012 | Emet/proof bundle file entry points outside bundle directory | Verification returns UNVERIFIABLE without opening outside target. | Receipt path gate. |
| SEC-013 | Bootstrap witness directory unwritable in enforced tier | Startup fails visibly as `witness_unavailable`; ordinary work does not begin. | No fail-open bootstrap gate. |
| SEC-014 | Cloud-target capsule includes `private-local-only` record | Build omits content, includes typed omission/count/hash, and fails if omission is non-omittable. | Cloud/local disclosure gate. |
| SEC-015 | Model-assisted summary changes or drops a normative instruction | Transformation receipt diff fails; synthesized text remains untrusted. | Unsafe synthesis gate. |
| SEC-016 | Telemetry enabled attempt with transcript text, capsule body, local absolute path, secret detector match, or subject identifier | Telemetry event rejected; default remains off. | Telemetry gate. |

## Measurable release gates

Release candidates should not claim ambient bootstrap or Canon-compatible capsule handling until these gates pass in CI and local reproducible runs:

1. Deterministic capsule build: same normalized inputs/config produce byte-identical `canon.capsule/v1` and human `CANON.md` outputs on Windows, macOS, and Linux. C: inferred.
2. Mandatory bootstrap gate: every successful enforced start produces a verified bootstrap witness before ordinary work; unwritable witness store fails closed. C: inferred.
3. Failure classification gate: missing authority, unavailable local state, stale evidence, secret quarantine, conflict, incompatible budget, unsupported host lifecycle, provider quota/offline, and source change each have a distinct visible code. C: inferred from spec.
4. Secret/PII gate: planted secret transmission across export/model boundary is zero; protected paths are denied before read; redaction receipts contain no raw secret values. C: inferred/verified primitive.
5. Authority retention gate: planted active goals, permissions, prohibitions, unresolved conflicts, and unknowns are retained 100% in the selected budget profile or the build fails. C: inferred from spec.
6. Trust gate: signed capsules from unknown keys are not trusted; pinned keys are scoped; revoked/expired/replayed capsules fail. C: inferred.
7. Archive gate: malicious `.canonpack` fixture zoo is rejected without unsafe extraction or outside reads. C: inferred.
8. Path gate: invalid scopes, traversal, symlink/junction/reparse escape, and case-fold collisions fail before read/write. C: inferred.
9. Concurrency gate: simultaneous launches and mid-session capsule changes either serialize or abort stale runs; no partial success is presented as clean. C: inferred.
10. Synthesis gate: every lossy statement has source identity and transformation receipt; model-synthesized unreviewed content cannot carry normative instructions. C: inferred from spec.
11. Telemetry gate: telemetry is absent by default; if added, it is opt-in, content-free, path-minimized, enterprise-disableable, and deletion/exportable. C: inferred.
12. Supply-chain gate: release artifacts are reproducible, signed/attestable, secret-scanned, licensed, SBOM-backed, and fixture-conformant. C: inferred from spec.

## Explicit unknowns and operator decisions

- Whether telemetry is allowed at all. C: unknown. No Canon source/test telemetry implementation was found, but product policy is not decided in the inspected source.
- Which principals/keys may sign trusted Canon capsules, how keys are rotated/revoked, and whether trust is per-person, per-org, per-device, per-project, or per-scope. C: unknown.
- Exact cloud/local disclosure policy for each host type and model provider. C: unknown.
- Required retention periods, deletion semantics, backup purge scope, and whether receipts may retain content hashes after right-to-forget requests. C: unknown.
- Whether future `.canonpack` should carry content, only by-reference evidence identities, or both. C: unknown.
- Whether adapter hooks can be truthfully `Enforced` for each host. This must be verified against actual host capabilities before marketing or release claims. C: unknown/blocked until platform-adapter lane evidence lands.
- Whether Canon should add repo/tenant/device scopes directly to the record schema or model them as metadata/policy records. C: unknown.
- Whether Emet/Flywheel receipt primitives should be vendored, depended on, or reimplemented in Canon's stdlib-only floor. C: unknown.
- Whether encryption-at-rest is required for first public release or only for enterprise/local-sensitive deployments. C: unknown.

## Dependencies, conflicts, and sequencing

- Core schema/I0 lane must define capsule schema, precedence model, authority/prohibition/goal/conflict records, and budget profiles before this lane can finalize policy fixtures. C: inferred.
- Platform adapter lane must verify host startup capabilities before any adapter can claim `Enforced`. C: inferred from spec.
- Continuity benchmark lane should include SEC-009 and SEC-015 retention/synthesis fixtures so security gates are measured alongside quality. C: inferred.
- Community/release lane should wire supply-chain gates, release signing/attestation, and public disclosure docs. C: inferred.
- Security implementation should precede public packaging of ambient bootstrap; otherwise public docs can overstate lifecycle control. C: inferred.

## Now / Next / Later

| Priority | Work | Release gate |
| --- | --- | --- |
| Now | Add fail-closed bootstrap state machine design and tests before any adapter claim. | SEC-006, SEC-007, SEC-009, SEC-013 pass. |
| Now | Fix FilesBackend semantic validation before path derivation. | SEC-001 and SEC-002 pass with no outside-root artifact. |
| Now | Define trust labels, disclosure labels, and mandatory failure codes in capsule schema. | Machine/human capsule fixtures preserve labels and typed omissions. |
| Now | Add secret/protected-path policy wrapper around Secret Redact IO for Canon usage. | SEC-010 and SEC-011 pass. |
| Now | Add symlink/junction/reparse operational guard for instruction-surface and archive paths. | SEC-003 and SEC-004 pass on Windows and POSIX where supported. |
| Next | Add pinned key trust store, expiry, source-state hash, nonce/replay cache, and key revocation model. | SEC-005 and SEC-006 pass. |
| Next | Add `.canonpack` manifest-only preflight, safe extraction, digest verification, and hostile archive fixture zoo. | SEC-004 and SEC-012 pass. |
| Next | Add explicit authority/prohibition/active-goal/conflict/unknown records and policy evaluator. | SEC-008 and SEC-009 pass. |
| Next | Add retention/deletion/tombstone/purge semantics across stores, vault, surfaces, capsules, and receipts. | Deletion fixture proves derived-surface behavior. |
| Next | Add model-assisted synthesis quarantine and source-span transformation receipts. | SEC-015 pass. |
| Later | Add encryption-at-rest wrapper and key-management docs for sensitive deployments. | At-rest confidentiality gate passes without half-encryption claims. |
| Later | Decide telemetry policy; if allowed, implement opt-in content-free event schema and deletion/export controls. | SEC-016 pass. |
| Later | Add SBOM/reproducible-build/release-attestation pipeline and Canon-compatible conformance kit. | Supply-chain gate passes. |
| Later | Add cross-machine/cloud-local workspace handoff policy and tenant/device scoping after adapter evidence lands. | Cross-tenant/cloud fixture suite passes. |

## Summary

2 critical, 11 warnings, 6 info items.
