# Canon UX, Accessibility, and Capability Blueprint Audit

Status: audit lane report, planning evidence only.  
Date: 2026-08-30.  
Lane: UX and accessibility.

## Scope

This report covers the user workflows and accessible surfaces needed for Canon to become an understandable continuity layer across agent providers and harnesses. It does not modify product code, tests, manifests, package metadata, release state, or parallel I0 work.

Evidence labels follow the audit contract:

- `C: verified`: directly supported by inspected local files, command output, or primary-source documentation.
- `C: inferred`: reasoned from verified evidence, but not directly implemented or platform-certified.
- `C: unknown`: evidence was not found or not inspected in this lane.
- `C: blocked`: evidence should exist, but could not be obtained within this run.

## Inspected Evidence

| Evidence | What it establishes | Claim state |
|---|---|---|
| `C:/dev/AGENTS.md` | Workspace method requires verified claims, model neutrality, public-clean surfaces, secret hygiene, and index-first orientation. | C: verified |
| `C:/dev/public/canon/CLAUDE.md` | Canon is a provider-neutral memory and personality container; current build spans F0 through V4 with schema, backends, region rendering, vault mirror, drift, persona thesis, and reconcile bands. | C: verified |
| `C:/dev/public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md` | Pillar objective, ambient bootstrap lifecycle, truthful support tiers, adoption promises, candidate capabilities, and lane output contract. | C: verified |
| `C:/dev/public/canon/project-docs/audits/2026-08-30/README.md` | This lane must create `UX-ACCESSIBILITY-FEATURE-BLUEPRINT.md`; reports are planning evidence and do not authorize product-code changes. | C: verified |
| `C:/dev/public/canon/pyproject.toml` | Package is `canon` version `0.0.0`, Python >= 3.11, no runtime dependencies, no `console_scripts` or other entry points. | C: verified |
| `C:/dev/public/canon/README.md` | Public README describes the record envelope, scopes, deterministic ordering, current F0-F1-R0-R1-R2 state, and `python -m pytest` as the run command. | C: verified |
| `C:/dev/public/canon/src/canon/schema.py:33-190` | Schema is `canon.record/v1`; five record kinds; two scopes, `global` and `workspace`; provenance includes source hash, session/model fields, and deterministic ordinal. | C: verified |
| `C:/dev/public/canon/src/canon/validator.py:84-190` | Validator reports all envelope, temporal, provenance, and kind-specific problems rather than failing at the first issue. | C: verified |
| `C:/dev/public/canon/src/canon/layering.py:77-100` | Layering resolves effective personality blocks by scope and rejects unknown scopes or non-personality records. | C: verified |
| `C:/dev/public/canon/src/canon/backends/base.py:34-150` | Backend protocol declares capability drops and refuses unsupported kinds or silent record-enforceable loss through `guard_put`. | C: verified |
| `C:/dev/public/canon/src/canon/region.py:35-151` | Managed host files use one canon marker pair; zero markers is off-limits; malformed markers are loud errors; splicing preserves bytes outside markers. | C: verified |
| `C:/dev/public/canon/src/canon/registry.py:46-51` | Current write catalog covers four instruction surfaces: Claude Code global `CLAUDE.md`, workspace `CLAUDE.md`, Codex workspace `AGENTS.md`, and workspace `SOUL.md`. | C: verified |
| `C:/dev/public/canon/src/canon/registry.py:87-180` | Surface writes are allow-listed, region-scoped, planned before writes, and report off-limits files without mutation. | C: verified |
| `C:/dev/public/canon/src/canon/drift.py:73-126` | Drift check is read-only and returns match, drift, off-limits, refused, or missing with sha256 hashes where both interiors exist. | C: verified |
| `C:/dev/public/canon/src/canon/reconcile.py:111-130`, `reconcile_gate.py:79-107`, `reconcile_run.py:91-172` | Reconcile has a classification lattice, human gates for conflict/held states, path-clean gate keys, and a pool-bound run witness. | C: verified |
| `C:/dev/public/canon/src/canon/vault.py:76-91`, `vault_mirror.py:77-101`, `vault_mirror.py:278-300` | Vault mirror derives safe note names, restricts writes to a vault shape, plans before writing, reports orphans, and never deletes them. | C: verified |
| `rg --files C:/dev/public/canon/scripts` and `rg --files C:/dev/public/canon/.claude` | No files were found under those directories during this run. | C: verified |
| `rg -n "console_scripts\|argparse\|click\|typer\|FastAPI\|mcp\|desktop\|browser\|IDE" C:/dev/public/canon` | No Canon product CLI, MCP server, desktop app, browser companion, or IDE extension implementation was found in the current repo. Mentions are docs/spec references. | C: verified |
| `python -m pytest` in `C:/dev/public/canon` | Existing test suite passed: 407 tests passed in 1.48 seconds. | C: verified |
| `mcp__index.index_router` and `mcp__index.index_map` for `C:/dev` | Both index calls timed out after 300 seconds, so index-backed workspace mapping is unavailable in this lane. | C: blocked |
| OpenAI Learn, "Import from another agent", lines 800-840, https://learn.chatgpt.com/docs/import | ChatGPT desktop and Codex CLI have an import flow for supported agents; import leaves existing setup unchanged; Codex CLI has `/import` limits. | C: verified |
| OpenAI Learn, "Get started with ChatGPT Work", lines 806-817, https://learn.chatgpt.com/docs/get-started-with-work | ChatGPT Work can use files, plugins, approved tools, and desktop local files/apps/browser when available; local/cloud choice affects availability. | C: verified |
| OpenAI Learn, "Plugins", lines 818-823, https://learn.chatgpt.com/docs/plugins | Plugins can include skills, connectors, MCP servers, browser extensions, and hooks. | C: verified |
| OpenAI Learn, "ChatGPT Work local security", lines 860-867, https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security | Connected systems require workspace allowance, plugin availability, authorization, and connector permissions; controls vary by integration. | C: verified |
| Claude Support, "How can I create and manage projects", lines 494-502, https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects | Claude projects can carry project instructions, and context is not shared across chats unless added to project knowledge. | C: verified |
| Claude Code docs, "Memory", lines 108-110, https://code.claude.com/docs/en/memory | Claude Code loads memory at conversation start but treats it as context, not enforced configuration. | C: verified |
| Claude Code docs, "Hooks", lines 1117-1187 and 1314-1351, https://code.claude.com/docs/en/hooks | Claude Code has SessionStart hooks that add startup context and UserPromptSubmit hooks that can block prompt processing. | C: verified |
| Claude Platform docs, "MCP connector", lines 159-192, https://platform.claude.com/docs/en/agents-and-tools/mcp-connector | Claude Messages API can connect directly to remote MCP servers with tool configuration and OAuth bearer support. | C: verified |
| W3C WCAG 2.2, https://www.w3.org/TR/WCAG22/ and WAI APG keyboard guidance, https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/ | Accessibility acceptance should align to WCAG 2.2 AA and APG keyboard patterns for web/app surfaces. | C: verified |

## Verified Current State

Canon today is a tested Python library prototype, not yet a user-facing continuity product. The implemented surface is API-level: records, validation, scope layering, storage seams, managed-file rendering, vault projection, drift detection, persona-basis checks, and reconcile gates. `pyproject.toml` exposes no console script or application entry point. Local search did not find a Canon MCP server, desktop launcher, browser companion, IDE extension, import wizard, capsule compiler, or preview UI. C: verified.

The existing primitives are strong foundations for the UX work:

- The record model already has a deterministic schema, five kinds, two scopes, provenance, temporal fields, and field-identical JSON round trips. C: verified.
- Rendering is conservative: Canon owns only bytes inside a single marker region and treats files without markers as off-limits. C: verified.
- The write catalog is small and fixed: Claude Code `CLAUDE.md`, Codex `AGENTS.md`, and Hermes `SOUL.md` surfaces. C: verified.
- Drift and reconcile already speak in user-meaningful states: match, drift, off-limits, missing, refused, conflict, held, fast-forward, overridden, and in-sync. C: verified.
- Reconcile already creates path-clean receipts bound to a pool digest and per-surface hashes. C: verified.
- The vault mirror is readable Markdown, but body edits are intentionally not authoritative; the carrier JSON is. C: verified.

The UX gap is equally clear: users cannot yet run "switch provider", compile a capsule, preview the next model's context, review imports, recover from quota exhaustion, operate offline through a supported CLI, or see a first-run guided experience from the current Canon repo. C: verified.

## UX Principle

Canon should not present continuity as magic. It should present continuity as a checkable handoff with three plain answers:

1. What will the next model know?
2. What did Canon omit or compress, and why?
3. What proof says this context is fresh enough to rely on?

Every surface should expose the same state model, but with different interaction density. CLI and CI get terse machine-readable output; desktop and IDE get guided review; accessible HTML and Markdown get durable human review; clipboard/stdin/stdout get emergency portability.

## Honest Integration-Tier Language

Do not advertise "ambient", "automatic", or "enforced" unless the host can actually run Canon before ordinary model work and block or visibly fail the start. Closed app lifecycles must use conservative language.

| Host or route | Truthful tier language for UX copy | Evidence and confidence |
|---|---|---|
| Canon local Python API | "Library foundation only. No user-facing host lifecycle yet." | Current repo has APIs and tests but no CLI/MCP/app entry point. C: verified |
| Generic API wrapper controlled by Canon or a third-party implementer | "Enforced when the wrapper refuses to send the first model request until bootstrap passes and records a witness." | This follows from controlled request flow, not current Canon code. C: inferred |
| MCP host controlled by Canon integration | "Enforced only if the host calls Canon as a mandatory startup or pre-prompt tool and blocks on failure; otherwise native advisory." | Claude MCP connector supports tool access, but host lifecycle enforcement is host-specific. C: inferred |
| A2A agents controlled by Canon integration | "Enforced only if the agent protocol requires a capsule and readiness proof before accepting work." | No A2A implementation inspected in Canon. C: unknown |
| Claude Code | "Enforced candidate for prompt processing after hook installation; startup context is native advisory unless the adapter proves a blocking pre-first-work gate." | Memory is context, not enforced; SessionStart can add context; UserPromptSubmit can block prompt processing. C: verified for primitives, inferred for combined Canon adapter |
| Claude web/desktop projects | "Native advisory for project instructions and project knowledge. Guided for export/import. Do not call it enforced." | Claude project instructions apply to chats, but context is not shared across chats unless placed in project knowledge. No blocking startup hook was verified for the closed app. C: verified/inferred |
| ChatGPT web/desktop Chat and Work | "Native advisory or guided, depending on whether Canon ships as plugin/instructions/import flow. Do not call it enforced until OpenAI exposes and documents a blocking startup lifecycle for that surface." | ChatGPT Work supports files/plugins/tools and desktop local capabilities; OpenAI docs show import and plugin mechanisms but this lane did not verify a closed ChatGPT app blocking startup hook. C: verified/inferred |
| Codex CLI and Codex in ChatGPT desktop | "Native advisory now from existing import/plugin/config surfaces; possible enforced tier only after platform lane verifies Codex hook decision control on first prompt." | OpenAI docs show `/import`, plugin capability, and Codex surfaces; current Canon repo has no Codex plugin or hook implementation. C: verified/unknown |
| OpenCode | "Guided until an audited startup hook or config lifecycle proves stronger." | No OpenCode source or docs inspected in this lane. C: unknown |
| Gemini CLI | "Guided until an audited startup hook or instruction lifecycle proves stronger." | No Gemini CLI source or docs inspected in this lane. C: unknown |
| Cursor | "Guided import/export unless the platform-adapter lane proves a startup lifecycle with blocking behavior." | OpenAI import docs identify Cursor as an import source, but no Cursor lifecycle docs were inspected here. C: verified/unknown |
| GitHub Copilot | "Guided or unsupported until audited." | No Copilot lifecycle docs inspected here. C: unknown |
| Local endpoints | "Enforced when Canon owns the launcher or endpoint proxy; guided when the user manually pastes a capsule into a generic UI." | Controlled local launch/proxy can gate requests; no Canon endpoint proxy exists today. C: inferred/verified |

Required product wording for closed ChatGPT and Claude apps:

> Canon can prepare and review a continuity handoff for this app, but this app does not currently expose a Canon-verified blocking startup lifecycle. Treat the handoff as advisory unless the receiving surface shows a Canon readiness witness.

## Surface Blueprint

| Surface | Minimum lovable workflow | Accessibility and platform requirements | Priority |
|---|---|---|---|
| CLI | `canon init`, `canon doctor`, `canon preview`, `canon switch`, `canon import`, `canon export`, `canon undo`; JSON output with `--json`; stdin/stdout support; deterministic exit codes. | Works in PowerShell, cmd, bash, zsh, fish; no color-only meaning; supports `NO_COLOR`; text fits 80 columns; all actions have dry-run and undo receipt. | Now |
| MCP server | Resources for current capsule, manifest, omissions, receipts, and preview; tools for compile, doctor, import review, readiness probe, and export; read-only default. | Tool schemas use plain labels and typed errors; no secret values in tool descriptions or results; supports low-token summaries and full references by URI. | Now |
| Desktop/launcher | First-run wizard, provider switch card, Context Doctor, preview, selective disclosure, undo timeline, cross-machine status. | Keyboard-only navigation, visible focus, screen-reader landmarks, high contrast, reduced motion, resumable steps, no timed-only actions. | Next |
| Browser/app companion | Capture visible chat/project state where allowed, show "what the next model will know", export clipboard/file bundle, guide import into closed apps. | Browser extension popup must not trap focus; status announced with ARIA live regions; all capture/export commands have text alternatives and confirmation. | Next |
| IDE extension | Branch/session continuity panel, semantic diff, readiness proof before starting task, merge conflict review next to source control. | Tree/grid widgets follow APG keyboard conventions; all badges have text labels; diff is navigable by heading and changed item. | Next |
| Accessible HTML | Static report and interactive local page for capsule preview, omissions, receipts, and readiness proof. | WCAG 2.2 AA baseline; server optional; printable; works without JavaScript for review mode; language and direction attributes set. | Now |
| Printable Markdown | Human-readable `CANON.md`, import review, and readiness proof that survive copy/paste. | Headings are semantic; tables have simple fallbacks; no information depends on color or icon; plain-language summaries before detail. | Now |
| Clipboard | Emergency "copy handoff" with visible token count, omissions, and receiving-surface instructions. | Copies both rich and plain text where possible; confirms length and destination; provides chunking for small-context models. | Now |
| stdin/stdout | `canon compile < input.json > CANON.md`, `canon doctor --stdin`, `canon preview --json`. | Stable exit codes and line-oriented errors; progress goes to stderr; output stays parseable. | Now |
| Team/CI | Freshness gate, conformance fixtures, policy-layer diff, PR comment, audit receipt artifact. | CI annotations include text descriptions and links to accessible HTML/Markdown artifacts; no reliance on colored terminal output. | Next |
| Mobile/view-only | Readiness proof, preview, omissions, and import checklist as responsive static HTML/Markdown. | Touch targets >= 44 CSS px for interactive HTML; no hover-only controls; readable in narrow view; download/share actions degrade to copy text. | Later |

## Candidate Feature Cards

### 1. Ambient Bootstrap

Priority: Now.

- User problem: Users start work in a new model or harness without knowing whether it received current instructions, decisions, active goals, conflicts, and omissions.
- Job story: When I open a supported session, I want Canon to refresh and prove continuity before normal work starts, so I do not discover context loss after damage is done.
- Minimum lovable workflow: Detect host entry, resolve layers, run freshness/trust/budget checks, compile or reuse a capsule, inject or present it, run a readiness probe, and write a bootstrap witness.
- Accessibility acceptance criteria: CLI prints a one-screen summary plus `--json`; desktop shows a keyboard-focusable status card; screen readers hear "ready", "advisory", or "blocked" with reason; no spinner-only state; reduced-motion mode disables progress animation.
- Risks: False "enforced" claims on closed apps; stale local state; user fatigue if every session blocks on low-risk changes; host quota or offline failures.
- Dependencies: Capsule schema, Context Doctor, readiness probe, host adapter tier proofs, secret quarantine, witness store. C: inferred.
- Metric: 100 percent of supported enforced starts produce a witness before first task execution; 0 silent bootstrap failures in fixture runs.
- Evidence: Ambient lifecycle and support tiers are required by `SPEC-CANON-PILLAR-20260830.md`; current Canon has no bootstrap implementation. C: verified.

### 2. First Run and Nontechnical Onboarding

Priority: Now.

- User problem: A new user cannot tell what Canon will touch, whether it will read private files, or what "continuity" means in practical terms.
- Job story: When I run Canon for the first time, I want a guided setup that uses plain language and defaults to preview-only, so I can trust it before it writes anything.
- Minimum lovable workflow: `canon init` detects supported local surfaces, explains "review only" vs "install markers", shows a sample capsule from fixture records, asks for explicit write consent, and saves a local undo checkpoint.
- Accessibility acceptance criteria: Wizard works fully in terminal text mode; no forced mouse; all terms have "What does this mean?" help; instructions are at an eighth-grade reading level where possible; localization keys cover every user-facing string.
- Risks: Over-explaining technical schema; accidental writes to personal instruction files; secrets in sample output; friction for expert users.
- Dependencies: CLI, marker installer, preview, undo, secret scanner, localization string catalog. C: inferred.
- Metric: New user can produce a preview and decline writes in under five minutes in a moderated usability test; zero writes occur before explicit confirmation.
- Evidence: Current `apply_surface` refuses unmarked files and `write_surfaces` reports off-limits files; marker installation is later phase per README/CLAUDE. C: verified.

### 3. One-Click Provider Switching

Priority: Now for CLI and clipboard; Next for desktop/browser/IDE.

- User problem: Provider switching is currently manual and lossy; users paste ad hoc summaries and lose prohibitions, decisions, and active frontier.
- Job story: When my current provider is unavailable or the next provider is better for a task, I want one command or button that prepares a target-specific handoff without hiding loss.
- Minimum lovable workflow: Choose source and target, run Context Doctor, select budget profile, preview target knowledge, export `CANON.md` plus `canon.capsule/v1`, copy or open target instructions, and record a switch receipt.
- Accessibility acceptance criteria: Target picker is a native select/listbox with keyboard search; all provider statuses have text labels; clipboard success is announced; errors include next action and fallback command.
- Risks: Overstated adapter parity; target context budget mismatch; source transcript unavailable; connector authorization failures.
- Dependencies: Platform adapter matrix, budget compiler, semantic diff, selective disclosure, provider import/export recipes. C: inferred.
- Metric: In benchmark handoffs, planted active goals, permissions, prohibitions, and unresolved conflicts are retained or the build fails explicitly.
- Evidence: OpenAI import docs show ChatGPT desktop/Codex CLI import from supported agents, but Canon has no provider-switch command today. C: verified.

### 4. Emergency Quota-Exhaustion Handoff

Priority: Now.

- User problem: A user can lose model access mid-task and need a usable handoff from local state without relying on the exhausted provider.
- Job story: When quota or session access disappears, I want Canon to rescue the current state locally and package it for another model, so work can continue with known omissions.
- Minimum lovable workflow: `canon rescue --target <provider-or-budget>` compiles from local records, recent receipts, reachable instruction files, and optional user-pasted transcript; it produces a small handoff, a full archive reference, and a "missing because quota was exhausted" omission.
- Accessibility acceptance criteria: Works offline after installed; terminal output uses plain text and clear recovery commands; desktop offers "Copy emergency handoff" without requiring account sign-in; mobile view can display the final handoff.
- Risks: Missing freshest remote-only context; accidental transcript secret copying; user may assume complete recovery when evidence is partial.
- Dependencies: Local flight recorder, secret quarantine, omission taxonomy, clipboard chunker, import checklist. C: inferred.
- Metric: Rescue fixture succeeds with network disabled and produces typed omissions for every unreachable source.
- Evidence: Pillar spec explicitly names immediate rescue; current Canon can operate stdlib-only and has deterministic local primitives, but no rescue command. C: verified/inferred.

### 5. Import Review

Priority: Now.

- User problem: Imports from other agents can bring stale settings, unsafe hooks, conflicting instructions, or unreviewed permissions.
- Job story: When I import another agent's setup, I want a review screen that explains what will change and what still needs authorization, so I can accept only what I understand.
- Minimum lovable workflow: Show detected source, items, trust state, conflicts, hooks/actions, secrets quarantined, permission changes, and unchanged existing setup; allow accept/reject per group; write import receipt and undo checkpoint.
- Accessibility acceptance criteria: Review is navigable as headings and checkboxes; keyboard users can select all/none and inspect detail; screen readers hear counts and severity; color badges have text.
- Risks: Hook behavior differs after import; source-specific settings do not map; imported connection needs manual sign-in; review can become too long.
- Dependencies: Adapter parsers, permission diff, secret scanner, undo, team policy layers. C: inferred.
- Metric: 100 percent of imported hooks/connectors/settings in fixture zoo get one of accepted, rejected, unsupported, needs-auth, or quarantined.
- Evidence: OpenAI import docs say imported setup is unchanged and review is recommended for permissions, MCP auth, hooks, plugins, and prompt templates; current Canon has no import review. C: verified.

### 6. "What Will The Next Model Know?" Preview

Priority: Now.

- User problem: Users cannot inspect the exact context a receiving model will see, especially after compression or target-budget trimming.
- Job story: Before I hand off work, I want to preview the next model's context and omissions, so I can fix gaps before the new model starts.
- Minimum lovable workflow: Show target, budget profile, included records, exact rendered `CANON.md`, omitted sources with reasons, lossy summaries with source spans, token/byte estimates, and copy/export actions.
- Accessibility acceptance criteria: Preview is linearizable as Markdown; diff controls have keyboard shortcuts and non-color markers; long sections collapse with accessible disclosure widgets; screen readers can jump by included, compressed, omitted, unknown.
- Risks: Token estimates differ from actual provider tokenizer; preview may expose sensitive content to shoulder-surfing; user might edit generated output instead of canonical records.
- Dependencies: Capsule compiler, budget estimator, omission taxonomy, semantic diff, selective disclosure, HTML/Markdown renderer. C: inferred.
- Metric: Preview hash matches exported handoff bytes; every omitted record has a typed reason and count.
- Evidence: Existing `render_surface`, `drift`, and `run_witness_payload` already use deterministic rendered interiors and hashes, but no capsule preview UI exists. C: verified.

### 7. Semantic Continuity Diff

Priority: Now.

- User problem: Byte diffs are not enough; users need to know whether intent, authority, goals, decisions, and conflicts changed.
- Job story: When a capsule changes, I want a semantic diff that groups changes by meaning, so I can decide whether the next model has the right operating state.
- Minimum lovable workflow: Compare previous and next capsule by record id/kind/scope, show added/removed/changed records, identify changed active goals, permissions, prohibitions, conflicts, decisions, unknowns, and lossy synthesis receipts.
- Accessibility acceptance criteria: Diff has text prefixes such as Added, Removed, Changed; no red/green-only meaning; screen-reader table summaries explain columns; keyboard can move by changed item.
- Risks: Semantic classification may overclaim if record kinds lack enough data; conflicts with security lane redaction requirements; too much detail for nontechnical users.
- Dependencies: Capsule schema extension, classifier rules, fixture zoo, accessible diff component. C: inferred.
- Metric: Golden semantic-diff fixtures match expected changed categories and do not collapse unknown vs contradictory vs stale.
- Evidence: Existing drift is byte-level with sha256 interiors; V4 deliberately has no recorded base for three-way merge. Semantic diff is not implemented. C: verified.

### 8. Context Doctor

Priority: Now.

- User problem: Users need one place to diagnose why continuity is unsafe: stale records, conflicts, secret risk, unreachable evidence, unsupported target, or budget overflow.
- Job story: When a handoff looks risky, I want Canon to explain the exact issue and the smallest next action, so I can fix it without reading schema internals.
- Minimum lovable workflow: `canon doctor` runs checks for schema validity, freshness, drift, reconcile state, source reachability, secret quarantine, budget fit, adapter tier, host offline status, dirty workspace, and concurrent capsule changes.
- Accessibility acceptance criteria: Findings are grouped by severity with text labels; every finding has "why it matters" and "fix"; CLI supports `--plain`, `--json`, and `--sarif` or equivalent CI annotation format.
- Risks: Too many warnings; false positives on secrets; network checks hang; provider-specific failures leak credentials.
- Dependencies: Validator, drift, reconcile, security scanner, adapter probes, timeout policy, CI reporter. C: inferred.
- Metric: Fixture set covers every doctor finding type; command exits 0 clean, 1 warning-gated, 2 blocked/refused, with documented meanings.
- Evidence: Existing validator, drift, writing gate, and reconcile provide reusable check primitives; no `canon doctor` entry point exists. C: verified.

### 9. Continuity Readiness Proof

Priority: Now.

- User problem: A receiving model may appear to accept a handoff without actually using the critical constraints and frontier.
- Job story: When a session starts from Canon, I want the receiving model or harness to prove it recovered critical state, so I can catch failures before real work starts.
- Minimum lovable workflow: Canon selects planted critical facts from the capsule, asks the receiving model/harness a short structured probe, verifies answers against source ids, and records pass/fail in the bootstrap witness.
- Accessibility acceptance criteria: Results are shown as pass/fail/unknown with plain explanations; screen-reader announcements do not require reading hidden JSON; manual-review fallback is available when model probing is unavailable.
- Risks: Prompt injection against probe; model passes by parroting without operational use; closed apps cannot expose probe result programmatically; privacy exposure if probe includes sensitive facts.
- Dependencies: Probe schema, critical-fact tagging, target adapter, witness store, security review. C: inferred.
- Metric: Continuity benchmarks measure resumed-task correctness and correction burden, not just probe pass rate.
- Evidence: Spec requires a small readiness probe and witness; no readiness proof implementation exists. C: verified.

### 10. Branch and Session Merge

Priority: Next.

- User problem: Parallel worktrees, sessions, and chats diverge; users need to merge continuity without losing decisions or silently overwriting active constraints.
- Job story: When two sessions changed Canon state, I want a merge review that shows compatible updates and real conflicts, so I can reconcile them deliberately.
- Minimum lovable workflow: Detect base capsule if available, compare branch/session heads, auto-merge independent records, gate conflicting ids/scopes, preserve source receipts, and write a merge witness with undo.
- Accessibility acceptance criteria: Merge list is keyboard navigable; conflicts have side-by-side and linear text views; screen readers get source labels and selected resolution; touch/mobile view is read-only unless conflict resolution is accessible.
- Risks: V4 currently has no recorded base for surface drift; concurrent sessions may write witnesses out of order; conflict rules for team/org layers are not yet defined.
- Dependencies: Base capsule identity, session id model, precedence policy, undo log, semantic diff. C: inferred.
- Metric: Merge fixtures cover independent edits, same-id conflict, stale base, no base, and concurrent writes.
- Evidence: V4 explicitly scopes out git-style recorded-base three-way merge for current surface drift; gate keys are path-clean across machines. C: verified.

### 11. Selective Disclosure

Priority: Next.

- User problem: Users need to hand off enough context for a task without exposing secrets, private notes, unrelated projects, or team-only policy.
- Job story: When I export to another model or teammate, I want to choose a disclosure profile, so the recipient receives only necessary context with visible omissions.
- Minimum lovable workflow: Offer profiles such as Full local, Project only, No secrets, Public-safe, Team-safe, and Need-to-know; show included/excluded counts; require review of high-risk records; seal evidence by reference where needed.
- Accessibility acceptance criteria: Disclosure choices are radio buttons or CLI enum values with descriptions; warnings are text-first; preview updates are announced; selected profile is in the exported Markdown.
- Risks: False negatives in secret detection; policy conflicts between personal/team/org layers; user may over-redact critical prohibitions.
- Dependencies: Security/privacy lane, layer precedence, record sensitivity labels, sealed archive format, preview. C: inferred.
- Metric: Secret fixture set has zero planted-secret transmission across export boundary; every redaction has reason and source id.
- Evidence: Workspace and spec forbid copying secrets/raw conversation bodies into reports and require zero planted-secret transmission; current Canon has no selective-disclosure model. C: verified.

### 12. Personal, Team, and Organization Layers

Priority: Next.

- User problem: Canon currently has global and workspace scopes, but product adoption needs personal preferences, project facts, team policy, organization policy, and session intent without ambiguity.
- Job story: When multiple policy layers apply, I want Canon to show precedence and conflicts, so I know whose rule wins and why.
- Minimum lovable workflow: Resolve layers into target context with a visible precedence ladder, conflict markers, source ownership, expiry, and governance controls for team/org records.
- Accessibility acceptance criteria: Layer visualization has a text equivalent; precedence can be read as an ordered list; every conflict has owner/source/age; screen readers can filter by layer.
- Risks: Governance overreach; private personal records leaking to teams; unclear override authority; small-context models losing lower-priority but still useful context.
- Dependencies: Schema expansion beyond `global`/`workspace`, enterprise governance model, role/permission mapping, adapter support. C: inferred.
- Metric: Layer fixtures prove deterministic resolution, conflict visibility, and no leakage from higher-sensitivity layers to lower-trust exports.
- Evidence: Current schema admits only `global` and `workspace`, and no `repo` scope; requested layers are future design. C: verified.

### 13. Offline and Small-Context Use

Priority: Now.

- User problem: Users may be offline, on local models, or constrained by tiny context windows, especially during emergency handoff.
- Job story: When the target model has limited context or no network, I want Canon to produce a useful exact-budget capsule with references, so work can continue without pretending completeness.
- Minimum lovable workflow: Build Needle, Handoff, and Archive profiles; estimate target budget; require critical records; emit typed omissions; keep archive references local; support `--offline` to skip network probes and mark reachability unknown.
- Accessibility acceptance criteria: Low-bandwidth mode suppresses remote fetches and heavy assets; static Markdown is enough to proceed; CLI progress is concise; mobile view can read Needle profile.
- Risks: Token estimates vary by model; local model may need simpler wording; archive references may be unreachable on another machine; offline mode can hide stale evidence.
- Dependencies: Budget profiles, token estimator abstraction, local archive, cross-machine sync state, readiness proof. C: inferred.
- Metric: Exact-budget fixture never exceeds configured byte/token ceiling; critical facts are retained or compilation fails.
- Evidence: Spec requires deterministic floor without hosted model and budget profiles; current Canon has deterministic stdlib primitives but no budget compiler. C: verified.

### 14. Error Recovery

Priority: Now.

- User problem: Continuity workflows fail for predictable reasons, but raw exceptions or vague errors leave users stuck.
- Job story: When Canon cannot complete a handoff, I want a classified failure with a safe fallback, so I can keep moving without corrupting state.
- Minimum lovable workflow: Normalize failures as missing authority, unavailable local state, stale evidence, secret quarantine, conflict, incompatible budget, unsupported lifecycle, offline target, dirty workspace, concurrent change, or internal fault.
- Accessibility acceptance criteria: Error messages start with the problem and next step; screen readers announce only the current blocking error, not a noisy log; CLI has stable exit codes; logs redact paths when requested.
- Risks: Over-normalizing real faults; leaking sensitive file paths; fallback path may be mistaken for successful handoff.
- Dependencies: Error taxonomy, logging policy, secret redaction, support tier registry, undo. C: inferred.
- Metric: Every fixture failure maps to one public error code, one user-facing explanation, and one recovery action.
- Evidence: Existing drift/reconcile already expose refused/missing/off-limits/held/conflict states; spec requires failed bootstrap classification. C: verified.

### 15. Undo and Reversible Control

Priority: Now.

- User problem: Users will not trust a continuity tool that edits instruction files, imports settings, or changes disclosure state without a clear rollback path.
- Job story: When Canon changes anything, I want an undo checkpoint and preview of rollback, so I can recover from mistakes.
- Minimum lovable workflow: Every write creates a before/after receipt with path-clean ids, hashes, source capsule, and restore command; `canon undo` lists reversible operations and restores only Canon-owned regions unless explicitly asked.
- Accessibility acceptance criteria: Undo history is readable as CLI table and Markdown; restore confirmation names exact surfaces; color is not required to identify destructive actions; keyboard focus lands on safest action.
- Risks: Cross-seam writes are not fully transactional; external app imports may not be reversible; undo could overwrite legitimate later changes.
- Dependencies: Operation log, receipt store, region-scoped restore, external adapter rollback capabilities, conflict detection. C: inferred.
- Metric: Undo fixtures restore pre-operation bytes for Canon-owned regions and refuse when target drifted since checkpoint unless user explicitly resolves.
- Evidence: Current region model preserves outside bytes; V4 states write batch atomicity but gate/witness seams are not cross-transactional. C: verified.

## Cross-Cutting Accessibility Requirements

These requirements apply to every candidate feature that exposes UI, terminal output, web output, or generated review artifacts.

| Dimension | Acceptance criteria | Priority |
|---|---|---|
| Keyboard-only use | Every command and desktop/browser/IDE action is reachable without a mouse; focus order follows visual order; focus is visible; modal dialogs trap and restore focus correctly; listbox/tree/grid patterns follow WAI APG. | Now |
| Screen-reader behavior | Status changes use ARIA live regions only when timely; headings and landmarks structure long reports; tables have captions or summaries; icons and badges have text equivalents; JSON is never the only human surface. | Now |
| Low vision and color independence | Minimum WCAG 2.2 AA contrast; no state depends on red/green/yellow alone; supports zoom to 200 percent without horizontal scrolling for prose; terminal supports `NO_COLOR` and plain labels. | Now |
| Cognitive accessibility | Use concrete verbs: Preview, Export, Review, Undo, Continue; avoid schema jargon in primary UI; every warning says what happened, why it matters, and what to do next; progressive disclosure hides internals until requested. | Now |
| Reduced motion | Progress and diffs work without animation; animated transitions obey reduced-motion settings; no auto-advancing review steps. | Next |
| Localization and RTL | All product strings are externalized; dates/times/numbers are locale-aware; HTML sets `lang` and `dir`; diagrams and ordering have text equivalents for RTL readers. | Next |
| Low bandwidth | No remote asset dependency for core flows; static HTML and Markdown review artifacts work offline; network probes have timeouts and can be skipped with visible `unknown` labels. | Now |
| Nontechnical onboarding | First-run defaults to preview-only; terms like "capsule", "witness", and "omission" get one-sentence explanations; advanced flags stay available but not required. | Now |
| Windows/macOS/Linux | CLI path handling uses platform-native examples; PowerShell and POSIX command snippets are both tested; file locking and newline handling are fixture-tested. | Now |
| Mobile/view-only | Preview and readiness proof are readable on mobile; mutation workflows can be disabled on small screens if an accessible alternative exists; copy/download remain available. | Later |
| Concurrent sessions | Capsule changes during a session raise a visible stale-context notice; conflict resolution never silently picks newest by wall clock; witnesses include session ids where available. | Next |
| Cross-machine state | Receipts avoid absolute host paths; cross-machine warnings distinguish missing local path from missing record; archive references show whether they are portable. | Next |
| Enterprise governance | Team/org policy edits require role-aware review, audit receipts, and clear owner/source labels; connector setup and data access follow workspace/admin controls. | Next |

## Failure Modes and Gaps

| Gap or failure mode | Severity | Confidence | Proposed control |
|---|---:|---:|---|
| No CLI or entry point exists for any user workflow. | Critical | High | Build CLI first with preview, doctor, compile/export, import review, rescue, and undo. |
| No capsule compiler or `canon.capsule/v1` manifest exists in current repo. | Critical | High | Define deterministic manifest and compile floor before desktop/IDE polish. |
| Closed ChatGPT/Claude app lifecycles may not permit enforced startup bootstrap. | Critical | High | Use Guided or Native advisory wording unless platform-specific primary evidence proves a blocking hook. |
| Current schema has only `global` and `workspace` scopes, not personal/team/org/session layers. | High | High | Extend schema and precedence model in design before implementing governance UX. |
| Surface drift is byte-level, not semantic. | High | High | Add semantic diff over records and capsule claims; keep byte hashes as receipt anchors. |
| V4 lacks recorded base for three-way merge. | High | High | Add branch/session merge as a new continuity-merge band, not as a silent extension of current V4. |
| Secret quarantine and selective disclosure are not implemented. | High | High | Block export until security lane defines scanner fixtures and redaction receipts. |
| No local flight recorder exists for emergency rescue. | High | Moderate | Add append-only local event receipts for decisions, corrections, evidence, branch/session state, and handoff events. |
| No accessibility test harness exists. | High | High | Add CLI snapshot tests, axe or equivalent HTML checks where web UI exists, screen-reader name checks, keyboard traversal tests, and plain-language lint. |
| Index MCP mapping was unavailable during this lane due timeout. | Medium | High | Record as blocked evidence; platform/core lanes should refresh workspace map with a narrower index scope or cached index. |
| No provider-specific adapter proofs for OpenCode, Gemini CLI, Cursor, GitHub Copilot, local endpoints, or A2A were inspected here. | Medium | High | Route to platform-adapter lane; UX copy must label these as unknown/guided until proven. |
| Undo cannot be assumed for external app imports. | Medium | High | Split undo language into local region undo, Canon receipt rollback, and external-manual recovery. |

## Acceptance Tests and Measurable Gates

These gates should become executable fixtures before public adoption claims:

1. Deterministic capsule: same normalized records, config, disclosure profile, target, and budget produce byte-identical `CANON.md`, manifest, omissions, and receipt hashes.
2. Critical retention: planted active goals, permissions, prohibitions, and unresolved conflicts are retained in Needle and Handoff profiles or compilation fails with typed omissions.
3. Secret boundary: planted secrets in records, transcript snippets, file paths, environment-like strings, and connector configs never cross export under public/team-safe profiles.
4. Omission visibility: every omitted, unreachable, stale, unsupported, redacted, or budget-cut item is typed, counted, and visible in Markdown, HTML, JSON, CLI, and MCP resource output.
5. Preview fidelity: preview hash equals exported `CANON.md` bytes for the same target profile.
6. Import review: every imported setting, instruction, hook, connector, project, and chat summary has an accepted/rejected/needs-auth/unsupported/quarantined state before write.
7. Context Doctor: fixture failures map to stable error codes and recovery text; no unclassified exception reaches the user in expected workflows.
8. Readiness proof: receiving model/harness must answer critical-state probes; failures block enforced tiers and downgrade advisory/guided tiers with visible warning.
9. Offline rescue: network-disabled fixture can produce a handoff from local state and marks all unreachable sources as `unknown` or `blocked`.
10. Exact budget: target profiles never exceed configured token/byte ceilings using the selected estimator; if estimator is unavailable, output states estimator unknown.
11. Undo: local Canon-owned region writes restore exact previous bytes and refuse rollback if the region changed since checkpoint.
12. Keyboard traversal: first-run, preview, doctor, import review, diff, and undo screens pass scripted keyboard traversal without inaccessible traps.
13. Screen-reader names: every action, badge, status, and disclosure control has a computed accessible name and role.
14. Low-vision review: all states remain distinguishable without color, at high contrast, and at 200 percent zoom.
15. Plain-language lint: primary UI copy avoids unexplained schema terms and gives a next action for every blocking error.
16. RTL/localization smoke: generated HTML renders correctly with `dir=rtl`; no hard-coded English-only layout assumptions in controls.
17. Cross-machine receipt: bootstrap, switch, merge, and reconcile witnesses never expose absolute host paths in portable artifacts.
18. Concurrent session: when source capsule changes between preview and export, export blocks or forces explicit re-preview.
19. Closed app tier audit: every adapter advertised above Guided has a current primary-source proof or local integration test showing lifecycle behavior.
20. CI gate: pull request check fails when instructions/decisions change without updated capsule/witness artifacts.

## Sequencing

Now should build the narrow local spine:

1. Canon CLI with `init`, `compile`, `preview`, `doctor`, `export`, `import review`, `rescue`, and `undo`.
2. `canon.capsule/v1` manifest, `CANON.md`, omission taxonomy, and deterministic budget profiles.
3. Accessible Markdown/HTML preview with semantic diff, Context Doctor findings, and readiness proof artifact.
4. MCP resources/tools that expose the same read-only preview and doctor state.
5. Closed-app language baked into adapter metadata so UX cannot overclaim enforcement.

Next should add richer host surfaces:

1. Desktop/launcher workflow for first run, provider switch, import review, undo timeline, and emergency rescue.
2. Browser/app companion for closed-app guided handoffs and copy/paste verification.
3. IDE extension for branch/session merge, source-control-adjacent continuity diff, and per-branch readiness proof.
4. Team/CI freshness gate and enterprise policy review.

Later should add broader reach:

1. Mobile/view-only review.
2. Localization/RTL completeness.
3. Rich cross-machine state sync.
4. Third-party compatibility badge and public conformance program after fixtures exist.

R&D should stay explicitly experimental:

1. Model-assisted synthesis refinement, because the deterministic floor must work first.
2. Automated closed-app screen capture or companion automation, because app lifecycles and terms may limit this.
3. Semantic importance scoring for budget compression, because critical records cannot be silently summarized away.
4. Multi-party organization governance, because role and retention models need legal/security input.

## Prioritized Capability Table

| Capability | Priority | Why this priority |
|---|---|---|
| CLI deterministic compile/export/preview | Now | Needed for every other surface and for offline rescue. |
| Omission taxonomy and manifest | Now | Prevents silent loss and supports preview, doctor, and readiness proof. |
| Context Doctor | Now | Centralizes staleness, conflict, secret, budget, and unsupported-lifecycle diagnosis. |
| Emergency handoff | Now | Directly satisfies immediate rescue adoption promise. |
| Import review | Now | Existing platform import flows already warn users to review permissions/hooks; Canon needs equivalent review before relying on imports. |
| Readiness proof | Now | Makes "fresh before work" measurable rather than aspirational. |
| Undo | Now | Required for trust before Canon writes instruction regions or imports setup. |
| Semantic continuity diff | Now | Required for "what changed in meaning" before handoff. |
| MCP read-only preview/doctor | Now | Lets capable hosts consume Canon without inventing UI first. |
| Desktop/launcher | Next | Improves nontechnical adoption once local spine is testable. |
| Browser/app companion | Next | Useful for closed apps but cannot be the core enforcement path. |
| IDE extension | Next | Natural home for branch/session merge and worktree state. |
| Personal/team/org layers | Next | Required for enterprise readiness but depends on schema/preference decisions. |
| Team/CI gates | Next | Needed before multi-user governance claims. |
| Mobile/view-only | Later | Valuable for review and approval, but not needed to prove core continuity. |
| Third-party badge/program | Later | Should follow conformance fixtures and adoption evidence. |
| Automated closed-app lifecycle control | R&D | Must not be promised without primary-source host lifecycle support. |

## Operator Decisions Needed

1. Should Canon extend scopes directly to personal/team/org/session, or keep `global`/`workspace` records and add an external policy-layer manifest?
2. Which surfaces are allowed to install markers or write generated files in F1/I0 implementation: instruction files only, vault only, or capsule artifacts too?
3. What is the default disclosure profile for emergency handoff: Project only, No secrets, or Team-safe?
4. Should readiness proof be mandatory for all provider switches or only for critical handoffs?
5. Which closed-app wording is acceptable for public copy: "guided handoff" only, or "native advisory" when project instructions/plugins are configured?
6. What local event sources may the flight recorder capture by default without explicit per-source consent?

## Boundary Notes

- This lane did not verify full platform-adapter capabilities for OpenCode, Gemini CLI, Cursor, GitHub Copilot, local endpoints, or A2A. Those remain platform-adapter dependencies. C: unknown.
- This lane used official OpenAI and Anthropic documentation only for minimal closed-lifecycle tier language. Deep provider matrices belong to `PLATFORM-ADAPTER-MATRIX.md`. C: verified.
- The index MCP route was attempted as required by workspace instructions but timed out for both router and inventory calls. This report therefore uses targeted filesystem inspection and labels the index route blocked. C: blocked.
- No product code was changed. C: verified.
