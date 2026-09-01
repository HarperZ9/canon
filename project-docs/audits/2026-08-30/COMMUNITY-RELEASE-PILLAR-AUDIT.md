# Canon community and release pillar audit

Date: 2026-08-30
Owner lane: Community and release
Repo: `C:/dev/public/canon`
Status: Evidence report only. No release, package reservation, publication,
deployment, external issue, external message, or code change was performed.

## Scope

This lane answers the community and release questions from
`project-docs/SPEC-CANON-PILLAR-20260830.md`: packaging, naming, licensing,
governance, documentation, CI, provenance, and adoption work required before
Canon can move from a tested prototype toward a community pillar.

The audit covers:

- positioning and category definition;
- name, trademark, package, import, and command collision risk;
- licensing and open-spec strategy;
- governance, maintainers, ownership, and retirement criteria;
- contribution, conduct, security, support, and issue/discussion surfaces;
- semver, migrations, CLI/MCP/SDK packaging, installers, containers, and
  reproducible builds;
- CI, SBOMs, signing, attestations, conformance, and "Canon Compatible" claims;
- tutorials, examples, troubleshooting, adoption loops, opt-in telemetry,
  accessibility gates, and provider partnership boundaries;
- a maturity ladder from prototype to ecosystem standard.

## Evidence

Local evidence:

- `C:/dev/AGENTS.md` was read. It requires verified claims, current-source
  research for external facts, protection of secrets, and no production deploy
  without explicit approval. C: verified.
- `C:/dev/public/canon/CLAUDE.md` was read. It defines Canon as a
  provider-neutral memory-bank and personality container, lists F0 through V4,
  and says later phases include verifier, migration legs, region installation,
  and global SOUL.md/GEMINI.md surfaces. C: verified.
- `C:/dev/public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md` was read.
  It assigns this lane to `COMMUNITY-RELEASE-PILLAR-AUDIT.md`, says the audit
  is read-only except reports, keeps product code and release state out of
  scope, requires current primary sources for external claims, and requires
  public releases to be reproducible, signed or attestable, secret-scanned,
  licensed, documented, and backed by conformance fixtures. C: verified.
- `C:/dev/public/canon/project-docs/audits/2026-08-30/README.md` was read. It
  lists this file as one of six expected reports and requires evidence labels
  plus Now/Next/Later work. C: verified.
- `git -C C:/dev/public/canon status --short --branch` returned
  `feat/v4-reconcile-loop` with untracked `project-docs/SPEC-CANON-PILLAR-20260830.md`
  and `project-docs/audits/`. C: verified.
- `git -C C:/dev/public/canon ls-files` shows tracked source, tests, phase
  docs, README, LICENSE, `.env.example`, `.gitignore`, and `.dockerignore`;
  it does not show `.github`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `GOVERNANCE.md`, `MAINTAINERS.md`, `CHANGELOG.md`,
  docs site config, Dockerfile, lockfile, SBOM, or release automation.
  C: verified.
- `python -m pytest -p no:cacheprovider` in `C:/dev/public/canon` passed
  `407 passed in 1.47s`. C: verified.
- The active I0 worktree at
  `C:/dev/worktrees/canon-full-history-memory-bank-20260830` was inspected
  read-only. It has untracked I0 design, plan, CLI, inventory, manifest,
  parser, and tests. C: verified.

External primary-source evidence was checked on 2026-08-30:

- GitHub API:
  `https://api.github.com/repos/HarperZ9/canon`,
  `https://api.github.com/repos/HarperZ9/canon/community/profile`,
  `https://api.github.com/repos/HarperZ9/canon/actions/workflows`,
  `https://api.github.com/repos/HarperZ9/canon/tags`.
- PyPI:
  `https://pypi.org/pypi/canon/json`,
  `https://pypi.org/pypi/canon-memory/json`,
  `https://pypi.org/project/canon/`,
  `https://pypi.org/project/canon-memory/`.
- npm registry:
  `https://registry.npmjs.org/canon`,
  `https://registry.npmjs.org/@journeykit%2fcanon`,
  `https://registry.npmjs.org/pi-canon`,
  `https://registry.npmjs.org/@canonmsg%2fagent-sdk`,
  `https://registry.npmjs.org/@canon-protocol%2fsdk`,
  `https://registry.npmjs.org/@canon-protocol%2fcli`.
- crates.io API:
  `https://crates.io/api/v1/crates/canon`,
  `https://crates.io/api/v1/crates/canon-json`,
  `https://crates.io/api/v1/crates/canon-store`,
  `https://crates.io/api/v1/crates/canon-embed`.
- Standards and release references:
  Python package name normalization
  `https://packaging.python.org/en/latest/specifications/name-normalization/`,
  PEP 541 `https://peps.python.org/pep-0541/`,
  npm scopes `https://docs.npmjs.com/about-scopes/`,
  Functional Source License `https://fsl.software/`,
  Open Source Definition `https://opensource.org/osd/`,
  Semantic Versioning `https://semver.org/`,
  GitHub community profiles
  `https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories`,
  PyPI Trusted Publishers `https://docs.pypi.org/trusted-publishers/`,
  PyPI digital attestations `https://docs.pypi.org/attestations/`,
  SLSA `https://slsa.dev/`,
  OpenSSF Scorecard `https://scorecard.dev/`,
  SPDX specifications `https://spdx.dev/use/specifications/`,
  CycloneDX specifications `https://cyclonedx.org/specification/overview/`,
  WCAG 2.2 `https://www.w3.org/TR/WCAG22/`.

## Executive finding

Canon is a well-tested local prototype, not a release-ready community pillar.
The core engineering base is stronger than the release surface: 407 tests pass,
the package is stdlib-only, and the README explains F0 through R2. The public
project lacks the community, governance, supply-chain, installer, conformance,
support, and accessibility surfaces that would let outside implementers depend
on it.

The largest blocker is naming. The distribution name `canon` in
`pyproject.toml` is already taken on PyPI by an unrelated project, the unscoped
`canon` name is taken on npm and crates.io, and a same-name direct competitor is
already active as the `canon-memory` PyPI package and `Adarshk18/Canon` GitHub
repo. That competitor also exposes the public product/CLI as "Canon" in the AI
coding-agent memory category. C: verified.

Release recommendation: do not publish under the current `canon` distribution,
top-level import, command, or "Canon Compatible" mark until the operator decides
the public naming strategy, licensing split, governance model, and compatibility
program boundaries. C: inferred.

## Current local and public state

| Area | Current evidence | Maturity | Confidence |
| --- | --- | --- | --- |
| Product positioning | README says Canon is "One record for your memory bank and your personality, shared across every model and every tool." `CLAUDE.md` says it is a provider-neutral memory-bank and personality container over mneme, flywheel, and relay. | Strong thesis, not yet packaged as a public category. | C: verified |
| Implemented code | Source contains schema, validator, layering, backends, region/textblock/fidelity, surfaces, vault, drift, writing gate, persona thesis, reconcile, and tests. | Prototype to internal alpha. | C: verified |
| Tests | Current suite passes: 407 tests. | Good local engineering signal. | C: verified |
| Python package metadata | `pyproject.toml` uses `name = "canon"`, `version = "0.0.0"`, Python `>=3.11`, no runtime deps, dev extra `pytest>=8`, no project scripts. | Not publishable as-is. | C: verified |
| CLI | No tracked console script or CLI entry point in the main repo. I0 worktree contains an untracked history CLI. | Not release-ready. | C: verified |
| MCP/SDK | No tracked MCP package, protocol server, SDK package, or public adapter registry was found in the main repo. | Planned only. | C: verified |
| Docs | README, phase decision docs, schema/layering/backend docs exist. No dedicated docs site, tutorials, examples directory, troubleshooting guide, public API reference, migration guide, or release notes were found. | Good internal design record; incomplete external docs. | C: verified |
| License | Repo uses FSL-1.1-MIT with a competing-use restriction and MIT future license after two years. GitHub reports license `NOASSERTION`. | Source-available, not cleanly open-standard friendly. | C: verified |
| Community profile | GitHub API reports community health 42%, README and license only, no contributing guide, code of conduct, issue template, or pull request template. | Below public community bar. | C: verified |
| CI/releases | GitHub API reports zero workflows, zero tags, and no latest release. | Release blocker. | C: verified |
| Security policy | No `SECURITY.md` locally or through GitHub contents API. `.gitignore` excludes `.env`, `.env.*`, `.envrc`, local overrides, bytecode, and build outputs; `.env.example` says F0 has no runtime secrets and later OAuth credentials go in `.env`. | Secret hygiene started; vulnerability process absent. | C: verified |
| Containers/installers | `.dockerignore` exists. No Dockerfile, compose file, winget/Scoop/Homebrew metadata, MSI/pkg/deb/rpm, or container build workflow was found. | Absent. | C: verified |
| Reproducibility/provenance | Core code emphasizes deterministic records and receipts. Release artifacts, lockfiles, SBOMs, signing, attestations, and provenance workflows are absent. | Product principle exists; release supply chain absent. | C: verified |
| Public repo state | `HarperZ9/canon` is public, default branch `main`, 1 star, 0 forks, 0 open issues, not archived, pushed 2026-08-29. | New public repo. | C: verified |

## Naming, trademark, and package collision risk

| Surface | Current fact | Release implication | Confidence |
| --- | --- | --- | --- |
| PyPI `canon` | Current PyPI project `canon` is owned by `ketnipz`, version `0.0.1`, summary "Canon is a tool for emulating the compression found in two of the Club Penguin mini-games.", homepage `https://github.com/ketnipz/Canon`. | `pyproject.toml` cannot be published to PyPI as `canon` without a name transfer or rename. PEP 541 governs name retention and transfer; no transfer action is authorized. | C: verified |
| PyPI `canon-memory` | Current PyPI project `canon-memory` is version `1.3.0`, requires Python `>=3.11`, uses MIT, summary "Canon - governed project decision memory for AI coding agents.", homepage `https://github.com/Adarshk18/Canon`. | Direct category/name collision. Users searching for "Canon AI agent memory" will encounter another active "Canon" first in the same use case. | C: verified |
| GitHub same-name competitor | `Adarshk18/Canon` is public, MIT, description "A governed, self-updating decision memory layer for AI coding agents.", created 2026-08-15, latest release `v1.3.0` on 2026-08-22, with CI, publish, and `canon-check` workflows. | Competitor is currently more externally packaged despite narrower architecture. Differentiation must be explicit before launch. | C: verified |
| npm `canon` | Current npm package `canon` is version `0.4.1`, description "Canonical object notation", repository `davidchambers/CANON`, published 2014-08-29. | Unscoped npm package `canon` is unavailable. A scoped package can avoid the hard registry collision but not brand confusion. | C: verified |
| npm adjacent names | `@journeykit/canon` version `0.6.0` describes "canon - harness knowledge substrate"; `pi-canon` version `0.3.0` describes canonical project memory for the Pi coding agent; `@canonmsg/agent-sdk` version `9.1.0` describes a Canon Agent SDK; `@canon-protocol/sdk` and `@canon-protocol/cli` exist. | The word "Canon" is already crowded in agent, document, protocol, and canonicalization contexts. Use a distinctive package family and compatibility mark. | C: verified |
| crates.io `canon` | Current crate `canon` version `0.1.1` canonicalizes JSON; `canon-json`, `canon-store`, and `canon-embed` also exist. | Rust cannot use the unscoped crate name `canon`. Prefix or rename is required. | C: verified |
| Top-level import and CLI | Local package exposes top-level Python package `canon`. The same-name competitor documents itself as Canon and its release body says `pip install -U canon-memory`, `canon add`, `canon query`, `canon check`, and `canon mcp`. | Installing both projects may create import or command ambiguity if both expose `canon`. The local package should not claim the `canon` command without a deliberate collision policy. | C: inferred |
| Trademark | Canon is also a globally famous brand name outside this category. This audit did not perform legal clearance or a full trademark search. | Public launch needs trademark counsel or a conservative rename, especially before "Canon Compatible" claims or partnership outreach. | C: unknown |

Naming gate before any public package:

1. Decide whether the public project remains "Canon" or moves to a distinctive
   name such as a "Continuity Capsule" family. C: blocked on operator.
2. Pick distribution names, import names, binary names, MCP server IDs, and
   SDK scopes that do not collide with current registry occupants. C: blocked
   on operator.
3. Document a compatibility mark policy that avoids implying endorsement by
   Canon Inc., `canon-memory`, `@canonmsg`, `@canon-protocol`, or provider
   partners. C: blocked on operator.

## Positioning

Best truthful category today: "local-first continuity capsule and record
format for AI agent work." This is narrower and clearer than "memory bank" and
less collision-prone than "Canon" alone. C: inferred.

What is already defensible:

- Canon can claim a deterministic canonical record envelope, scoped layering,
  storage adapters, text region round-trip, surface rendering, vault mirror,
  drift checks, persona thesis adapter, and reconcile loop. C: verified.
- Canon can claim no runtime dependencies in the tracked package and Python
  3.11+ support. C: verified.
- Canon can claim local test evidence from this audit run: 407 passing tests.
  C: verified.

What must not be claimed yet:

- A public ecosystem standard, provider-standard bootstrap protocol, or
  "Canon Compatible" program. C: verified by absence.
- Enforced ambient bootstrap across Claude, ChatGPT, Codex, Cursor, Copilot,
  Gemini CLI, OpenCode, APIs, MCP hosts, or A2A agents. C: verified by absence.
- Production-grade CLI/MCP/SDK/installers. C: verified by absence.
- Open-source status under OSI terms while the core runtime is FSL with a
  competing-use restriction. C: inferred from FSL terms and Open Source
  Definition field-of-endeavor/non-discrimination principles.

Positioning gate:

- The public README must have a one-sentence category, a "not this" section
  distinguishing Canon from `canon-memory`, `pi-canon`, `@journeykit/canon`,
  `@canonmsg`, and generic canonical JSON packages, and a verified feature
  matrix that marks shipped, experimental, and planned surfaces. C: inferred.

## Licensing and open-spec strategy

Current runtime license is FSL-1.1-MIT. The local license grants use for any
purpose other than competing use and converts each released version to MIT two
years after release. GitHub reports the license as `NOASSERTION`, which is
expected for a nonstandard/source-available license surface. C: verified.

This is acceptable for a commercial source-available runtime, but it is weak for
an ecosystem standard because third-party implementers, competitors, package
maintainers, standards bodies, and Linux distributions need permission to
implement compatible systems without a competing-use cloud over them. C: inferred.

Recommended split:

- Normative specs: Apache-2.0 or CC-BY-4.0 with explicit patent posture. C:
  inferred.
- JSON Schema, conformance fixtures, compatibility test harness, example
  capsules, and reference vectors: Apache-2.0 or MIT. C: inferred.
- Runtime library: operator decision. Keep FSL only if the priority is
  commercial control; move to Apache-2.0/MIT if the priority is standardization
  and broad adapter adoption. C: blocked on operator.
- Documentation: CC-BY-4.0 or Apache-2.0 to permit reuse in implementer docs.
  C: inferred.

License gates:

- Every file family has an explicit license policy in `LICENSE`, `NOTICE`, and
  docs front matter. C: inferred.
- `pyproject.toml` uses SPDX-compatible metadata when the chosen license allows
  it. C: inferred.
- The README stops using "open" without qualifier unless the relevant surface is
  actually under an open license. C: inferred.

## Governance, ownership, and retirement

Current state: there is no tracked `GOVERNANCE.md`, `MAINTAINERS.md`, `SUPPORT.md`,
public roadmap, RFC process, security response process, or compatibility council.
C: verified.

Minimum governance for public alpha:

- `GOVERNANCE.md`: project scope, decision process, maintainer authority,
  escalation path, release authority, and compatibility-spec change process.
- `MAINTAINERS.md`: owner list, reviewed domains, response expectations, backup
  maintainer, and key rotation owner.
- `SUPPORT.md`: supported versions, channels, vulnerability/non-vulnerability
  routing, enterprise boundary, and non-goals.
- `ROADMAP.md`: Now/Next/Later with explicit non-promises.
- Retirement criteria: deprecate adapters, SDKs, package names, or
  compatibility levels when maintenance falls below a documented threshold,
  upstream host APIs vanish, security posture cannot be sustained, or
  conformance cannot be verified.

Measurable gates:

- At least two maintainers or one maintainer plus a documented continuity backup
  before beta. C: inferred.
- All compatibility-impacting changes require an issue/RFC, conformance fixture
  update, migration note, and release note. C: inferred.
- Every adapter has owner, support tier, last verified date, host API source,
  and retirement trigger. C: inferred.

## Contribution, conduct, issue, and discussion surfaces

Current state: GitHub community profile reports no contribution guide, no code of
conduct, no issue template, and no pull request template. Local and GitHub
contents checks found none. C: verified.

Required before inviting contributors:

- `CONTRIBUTING.md` with local setup, test command, docs command, change
  categories, issue-first expectations for compatibility changes, and secret
  handling rules.
- `CODE_OF_CONDUCT.md` with enforcement contact and scope.
- Pull request template with checkboxes for tests, docs, compatibility impact,
  migration impact, security/privacy impact, accessibility impact, and release
  notes.
- Issue forms for bug, adapter request, conformance failure, documentation gap,
  security report redirection, and design/RFC.
- Discussions categories for implementer support, adapter requests, release
  planning, and conformance reports.

Gates:

- New external contributor can run the full suite from a fresh clone using no
  more than three commands after installing Python 3.11+. C: inferred.
- Issue forms must tell users not to paste secrets, raw transcripts, private
  capsules, or provider export bodies. C: inferred.

## Security policy and privacy

Current positive signals:

- `.gitignore` and `.dockerignore` exclude `.env`, `.env.*`, Python caches,
  build outputs, and local override files. C: verified.
- `.env.example` says F0 has no runtime secrets and later OAuth credentials go
  in `.env`. C: verified.
- I0 design keeps raw artifacts in original protected locations, refuses output
  under the public repository, excludes credential-bearing path classes before
  content open, and emits references rather than transcript bodies. C: verified
  in the untracked worktree.

Current gaps:

- No `SECURITY.md` or private vulnerability channel. C: verified.
- No documented threat model in this lane yet; separate security/privacy audit
  should own the full threat model. C: inferred.
- No secret-scan CI, dependency audit, SAST, release-signing key policy, or
  maintainer credential policy found. C: verified.

Security gates:

- A public `SECURITY.md` exists before alpha, with supported versions,
  vulnerability reporting contact, expected response timeline, embargo policy,
  and instruction not to attach secrets or raw private capsules. C: inferred.
- CI fails on committed `.env`, common token patterns, private capsule content,
  oversized transcript fixtures, and protected path leaks. C: inferred.
- Release artifacts are built from a clean tree and pass secret scanning before
  signing/attestation. C: inferred.

## Semver and migrations

Current state: package version is `0.0.0`, no changelog, no tags, no releases,
and no migration policy. C: verified.

Recommended versioning:

- Treat the capsule manifest, record schema, CLI output, conformance fixture
  layout, MCP resource names, and SDK public APIs as semver-governed public
  contracts.
- Use explicit schema versions such as `canon.capsule/v1` and preserve
  forward/backward compatibility tables per release.
- Require a migration plan for any breaking change: fixture diff, upgrader or
  refusal mode, rollback path, and docs.

Gates:

- `CHANGELOG.md` and release notes exist before the first tag. C: inferred.
- Every release has a migration section, even when it says "none." C: inferred.
- `0.x` releases may break, but every break is named, tested, and visible. C:
  inferred.
- `1.0.0` requires stable capsule schema, conformance fixtures, CLI contract,
  security policy, and at least one independent or clean-room implementation
  pass. C: inferred.

## Packaging: CLI, MCP, SDKs, installers, and containers

Current state:

- Python package metadata exists but uses the unavailable distribution name
  `canon` and has no console scripts. C: verified.
- Main repo has no tracked CLI. I0 worktree has an untracked
  `src/canon/history_cli.py` that writes `manifest.json`, `canon-records.jsonl`,
  and `receipt.json` for protected local history inventory. C: verified.
- No MCP server, SDK packages, installer manifests, or Dockerfile were found.
  C: verified.

Recommended package family:

- Python distribution: choose a non-colliding name. Avoid publishing as `canon`.
  Consider separating import package from distribution package if preserving
  internal import paths is important, but avoid a public `canon` command until
  the collision policy is decided. C: inferred.
- CLI command: prefer a distinctive command such as `continuity-capsule`,
  `ccapsule`, or another operator-approved name. Avoid `canon` unless the
  operator accepts collision and support costs. C: inferred.
- npm: use a scoped package under an operator-owned scope. Do not attempt
  unscoped `canon`. C: inferred.
- Rust: use a prefixed crate name because `canon` is taken. C: inferred.
- MCP: publish a server ID and resource namespace tied to the final package
  family, with fixture-backed compatibility tests. C: inferred.
- SDKs: stage after the CLI and conformance format are stable. Python and
  TypeScript are first due target harnesses; Rust/Go are later unless adapter
  demand appears. C: inferred.

Installer gates:

- Public alpha: `pipx`/`uv tool` install path plus source install from a tag.
- Beta: signed wheels/sdists and documented `pipx`, Homebrew, Scoop, and
  container image paths.
- Stable: Windows winget/Scoop, macOS Homebrew package and signed universal
  binary if a native binary exists, Linux deb/rpm/AppImage or distro-friendly
  package metadata, and OCI image with digest-pinned base images.

Container gates:

- Dockerfile or OCI build only after the CLI contract exists.
- Container image must run without secrets by default, mount input/output
  directories explicitly, run as non-root, and emit the same deterministic
  receipts as the host CLI.

## Reproducible builds, CI, SBOMs, signing, and attestations

Current state: no workflow, tag, release, lockfile, SBOM, signing, or attestation
artifact was found locally or through GitHub API. C: verified.

Required CI lanes:

- Unit and fixture tests across Windows, macOS, and Linux.
- Python version matrix beginning with 3.11.
- Formatting/linting and source-size gates already described in `CLAUDE.md`.
- Docs link check and example execution.
- Package build check for sdist/wheel.
- Secret scanning and protected-path leakage fixtures.
- License detection.
- OpenSSF Scorecard or equivalent posture report.
- Conformance fixture run.
- Accessibility checks for docs/site surfaces once those exist.

Release provenance gates:

- Build from a clean tag in CI using trusted publishing where supported.
- Emit sdist, wheel, checksums, SBOM in SPDX or CycloneDX, and provenance
  attestation.
- Sign or attest artifacts through Sigstore/PyPI attestations/GitHub provenance
  rather than local long-lived signing keys where possible.
- Store release command, commit SHA, tag, artifact digest, SBOM digest, and
  conformance report in release notes.
- Rebuild the same tag in a second job and compare artifact digests before
  stable release.

## Conformance and "Canon Compatible"

Current state: the spec calls for SDKs, JSON Schema, fixture zoo, conformance
CLI, and a `Canon Compatible` program. No tracked implementation or policy exists
yet. C: verified.

Risk: "Canon Compatible" currently implies a brand and compliance program before
there is a trademark policy, test suite, badge contract, revocation process, or
neutral governance body. With the same-name competitor and broader Canon brand
risk, this mark should not be used publicly yet. C: inferred.

Minimum compatible-program shape:

- Rename or approve the mark after legal/name review.
- Define compatibility levels by artifact, not by broad product identity:
  capsule-v1 reader, capsule-v1 writer, capsule-v1 round-trip, bootstrap witness
  producer, adapter tier reporter, redaction verifier.
- Publish JSON Schema and fixture zoo under open terms.
- Publish a conformance CLI that emits machine-readable results, artifact
  digests, tool version, and failure reasons.
- Require vendors to state tested Canon spec version, conformance CLI version,
  fixture version, unsupported features, and known declared losses.
- Disallow use of the mark for advisory/guided ambient bootstrap as if it were
  enforced.
- Use "compatible" only for passing artifacts. Use "experimental adapter" for
  partial or vendor-specific behavior.

Acceptance gates:

- At least 30 positive fixtures and 30 negative fixtures spanning records,
  capsules, omissions, source receipts, secret quarantines, lossy synthesis,
  migrations, conflicts, and adapter tier reports. C: inferred.
- A clean-room reader can pass the read-only fixture suite without importing
  Canon runtime code. C: inferred.
- Every compatibility badge links to a signed conformance report. C: inferred.

## Documentation, tutorials, examples, and troubleshooting

Current state: README and internal decision docs exist. There is no external docs
site, tutorial set, example capsule, troubleshooting page, migration guide,
adapter matrix, threat-model summary, accessibility guide, or conformance guide.
C: verified.

Required docs before public alpha:

- "What Canon is" with precise category and shipped/planned matrix.
- Install and quickstart using the final package name.
- One guided rescue handoff tutorial with local files only.
- `CANON.md` and `canon.capsule/v1` format overview.
- CLI reference once a CLI exists.
- Adapter tier definitions and truthful host capability language.
- Privacy and redaction guide.
- Troubleshooting for missing sources, stale capsules, secret quarantine,
  unsupported hosts, dirty worktrees, provider quota exhaustion, and offline use.
- Migration and compatibility policy.

Docs gates:

- Every code block that is labeled executable is tested in CI. C: inferred.
- Every tutorial states inputs, outputs, privacy boundary, and cleanup behavior.
  C: inferred.
- Docs distinguish verified current behavior from planned roadmap. C: inferred.

## Adoption and community loops

Current adoption surface is thin: one public repo, one star, no discussions
setup observed through local files, no issue templates, and no release. C:
verified.

Recommended loops:

- Dogfood Canon on its own phase/audit handoffs and publish sanitized receipts.
- Publish a small example fixture zoo that users can run without private data.
- Create an adapter request process that records host, lifecycle support tier,
  import/export surface, semantic loss, owner, and last verified date.
- Publish a monthly compatibility status page only after conformance is
  automated.
- Invite implementers through issues/discussions only after contribution and
  security policies are live.

Metrics:

- Fresh clone success rate.
- Time to first verified capsule.
- Conformance pass rate by implementation.
- Docs task completion rate.
- Adapter recency and breakage count.
- Security report response time.
- Percentage of issues closed with a fixture, docs update, or explicit non-goal.

## Privacy-respecting opt-in telemetry

Current state: no telemetry code or policy was found. C: verified.

Telemetry should remain absent until there is a written data contract. If added,
it must be off by default and opt-in, with local preview of every event class.
C: inferred.

Telemetry gates:

- No transcript text, capsule body, secret detector match, local absolute path,
  username, repo private URL, provider account ID, or raw prompt is collected.
- Event schema is public, versioned, and testable.
- User can disable telemetry through config, env var, and CLI flag.
- Enterprise policy can force telemetry off.
- Telemetry failures never block local continuity work.
- Deletion/export process exists for any collected identifiers.

Useful opt-in events after approval:

- command name, duration bucket, exit code, platform family, Canon version,
  feature flag, anonymized adapter type, conformance fixture version, and typed
  failure category.

## Accessibility release gates

Current state: no UI or docs-site accessibility tests were found. CLI exists
only in an untracked I0 branch. C: verified.

Accessibility gates by surface:

- CLI: works with screen readers through plain stdout/stderr, has stable exit
  codes, avoids color-only signals, supports `--no-color`, offers JSON output,
  and documents all prompts and noninteractive flags.
- Markdown: readable heading order, descriptive links, no image-only
  instructions, printable command references.
- HTML/docs site: WCAG 2.2 AA target, keyboard navigation, visible focus,
  contrast checks, reduced motion, semantic landmarks, and tested mobile
  viewport.
- Capsule preview: every omission, conflict, secret quarantine, and compatibility
  warning is visible in text, not only color or icons.
- Release gate: every public user workflow has keyboard-only and screen-reader
  acceptance coverage before stable.

## Provider partnership boundaries

Canon's strongest defensible public stance is provider-neutral interoperability.
C: verified from local README/CLAUDE positioning.

Boundaries:

- Do not imply official provider support unless a provider has publicly
  documented the hook, API, or partnership.
- Do not label advisory/guided startup flows as enforced.
- Do not use provider logos, marks, or compatibility claims without permission.
- Keep provider adapters as capability facts with source links, last-verified
  dates, and failure modes.
- Avoid vendor-specific private APIs unless the adapter is explicitly marked
  experimental and the risk is documented.
- Provider partnerships should not receive private capsules, raw transcripts,
  or telemetry beyond the opt-in policy.

Gate:

- Every adapter page includes support tier, source evidence, data flow, secret
  exposure, offline behavior, quota failure behavior, and tested version/date.
  C: inferred.

## Gaps and failure modes

| Severity | Gap or failure mode | Impact | Proposed control | Confidence |
| --- | --- | --- | --- | --- |
| Critical | Current package name `canon` is unavailable on PyPI and collides across npm/crates. | Publish failure, user confusion, command/import ambiguity. | Rename or choose a unique package family before packaging. | C: verified |
| Critical | Same-name active competitor in AI coding-agent memory category. | Search confusion, install confusion, community fragmentation, possible mark conflict. | Public differentiation, legal/name review, and non-colliding CLI/import/package names. | C: verified |
| Critical | No CI or release provenance. | No trustworthy public artifact chain. | Add CI, package build, secret scan, SBOM, signatures/attestations, conformance run. | C: verified |
| High | FSL core license conflicts with open-standard adoption goals. | Third-party implementers may avoid or be unable to implement. | Split spec/fixtures/conformance under permissive/open terms; decide runtime license. | C: inferred |
| High | No security policy. | Vulnerability reports may land in public issues with sensitive data. | Add `SECURITY.md`, private contact, supported versions, response process. | C: verified |
| High | No governance or maintainer model. | Compatibility decisions appear unilateral and unstable. | Add governance, maintainer, RFC, release, retirement, and support docs. | C: verified |
| High | No CLI/MCP/SDK in tracked mainline. | Users cannot exercise the adoption promises. | Stage CLI first, then MCP and SDKs after conformance contract. | C: verified |
| High | "Canon Compatible" not defined. | Mark can overpromise and create legal/support risk. | Delay mark, define levels, fixture-backed reports, and usage policy. | C: inferred |
| Medium | Docs are internal-design heavy and tutorial-light. | New users cannot evaluate value quickly. | Add quickstart, examples, troubleshooting, adapter matrix, migration guide. | C: verified |
| Medium | No installer/container strategy. | Cross-platform adoption burden stays high. | Stage pipx/uv, then Homebrew/Scoop/winget/container/deb/rpm as demand warrants. | C: inferred |
| Medium | No telemetry policy. | Future telemetry could erode trust or leak metadata. | Keep absent until opt-in event schema and disable controls exist. | C: verified |
| Medium | Accessibility gates absent. | Broad access promise is untested. | Add CLI/docs/site WCAG and assistive-tech gates. | C: verified |
| Low | Public repo is new and has little visible adoption. | Standardization claims would be premature. | Publish evidence, examples, and conformance first; measure adoption later. | C: verified |

## Operator decisions required

1. Naming: keep "Canon" publicly, adopt a sub-brand, or rename the project and
   compatibility mark. C: blocked.
2. Package family: choose distribution names, import names, CLI binary names,
   npm scope, crate prefix, MCP server ID, and SDK namespaces. C: blocked.
3. Legal/trademark: decide whether to obtain trademark counsel before public
   launch and compatibility-mark use. C: blocked.
4. License split: decide whether runtime stays FSL, moves permissive, or splits
   runtime from open specs/fixtures/conformance. C: blocked.
5. Governance: decide maintainer model, RFC authority, release authority, and
   compatibility-mark authority. C: blocked.
6. Support: decide public support expectations, security response timeline,
   enterprise boundary, and LTS policy. C: blocked.
7. Telemetry: decide whether telemetry is allowed at all. If yes, approve an
   off-by-default event schema before implementation. C: blocked.
8. Provider partnerships: decide whether adapter pages can mention providers
   only descriptively or whether formal partner outreach is desired later. C:
   blocked.

## Now / Next / Later

| Horizon | Work | Exit gate |
| --- | --- | --- |
| Now | Freeze public package/release work until naming decision. | Operator chooses name/package/CLI/mark policy or records intentional risk. |
| Now | Add governance, contribution, code of conduct, security, support, changelog, roadmap, and PR/issue templates in a design plan before implementation. | Community profile can reach at least GitHub's README/license/contributing/conduct/security/template baseline. |
| Now | Define license split for specs, fixtures, conformance, docs, and runtime. | Public docs can say exactly which surfaces are open, source-available, or proprietary. |
| Now | Define conformance levels without using "Canon Compatible" publicly. | Fixture-backed level names and badge policy are approved. |
| Now | Convert I0 untracked CLI work into an integration dependency, not a release promise. | Main design records what I0 provides and what still lacks packaging/security review. |
| Next | Build release CI: tests on Windows/macOS/Linux, build, secret scan, docs checks, conformance, SBOM, attestations. | A dry-run release from a tag produces checksummed artifacts and a signed/attested provenance record. |
| Next | Ship a renamed alpha CLI with deterministic local example fixtures. | Fresh clone install plus example run succeeds in CI and on a clean Windows/macOS/Linux machine. |
| Next | Publish docs: concept, quickstart, capsule format, adapter tiers, troubleshooting, migration, privacy. | Docs examples are executable and link-checked. |
| Next | Publish JSON Schema and fixture zoo under the approved open license. | Clean-room read-only implementation passes fixture suite. |
| Next | Define MCP and SDK contracts after CLI/conformance stabilize. | SDK generated examples pass conformance and no package names collide. |
| Later | Cross-platform installers and OCI images. | Signed packages/images with SBOMs and reproducible-build receipts. |
| Later | Public implementer program and compatibility badge. | At least two external or clean-room implementations pass published fixtures. |
| Later | Provider adapter registry. | Each adapter has support tier, evidence source, last verified date, failure modes, and owner. |
| Later | Optional telemetry. | Operator-approved opt-in schema, no sensitive content, enterprise disable, deletion/export path. |
| Later | Foundation-style governance or standards-track stewardship. | Multi-maintainer or neutral body can evolve spec without runtime lock-in. |

## Maturity ladder

| Level | Name | Gates | Current status |
| --- | --- | --- | --- |
| 0 | Local prototype | Tests pass, internal docs exist, no public release claims. | Current mainline fits here: 407 tests pass and docs exist. C: verified |
| 1 | Public alpha | Non-colliding name, security/contribution/governance docs, alpha CLI, permissive spec/fixtures, CI dry run, example capsule. | Not met. C: verified |
| 2 | Implementer beta | JSON Schema, fixture zoo, conformance CLI, signed prereleases, docs site, adapter tier matrix, migration policy. | Not met. C: verified |
| 3 | Stable toolchain | Semver 1.0 contracts, stable CLI/MCP/SDK, cross-platform installers, SBOM/signing/attestations, security response process, accessibility gates. | Not met. C: verified |
| 4 | Ecosystem standard | Multiple implementations, public compatibility reports, neutral governance or published RFC process, provider-neutral adapter registry, documented retirement criteria. | Not met. C: inferred |
| 5 | Durable standard | Long-term maintenance policy, LTS/security branches, independent conformance lab or foundation-style custody, broad package/distro availability, sustained adoption metrics. | Not met. C: inferred |

## Acceptance gates for this pillar

The community/release pillar is ready to move from audit to implementation plan
when these are specified with owners and tests:

- Naming decision recorded and all proposed registry names checked without
  reservation or publication.
- License policy approved for runtime, specs, fixtures, docs, examples, SDKs,
  and conformance tooling.
- GitHub community files drafted with no secrets and no private corpus references.
- Release CI design covers tests, docs, package build, secret scan, SBOM,
  signing/attestation, conformance, and accessibility where applicable.
- CLI package contract has a non-colliding binary name, install path, exit codes,
  JSON output, and privacy boundary.
- Semver and migration policy covers record schema, capsule manifest, CLI JSON,
  MCP resources, SDK APIs, and conformance fixtures.
- "Canon Compatible" is renamed, deferred, or governed by a mark policy and
  fixture-backed levels.
- Provider-adapter claims are tiered and source-linked, with no unsupported
  enforcement claims.
- Telemetry remains absent or is governed by an approved off-by-default event
  schema.

## Deeper research deferred

These are deliberately deferred to keep this lane bounded:

- Full trademark clearance and legal opinion for "Canon", alternate names, and
  compatibility marks. C: unknown.
- Current availability checks for every proposed replacement package name across
  PyPI, npm, crates.io, Homebrew, winget, Scoop, Docker Hub/GHCR, and domain
  names. C: unknown.
- Detailed competitor teardown beyond the same-name/category/package evidence
  above. C: unknown.
- Cross-lane reconciliation with platform, security, benchmark, and UX reports
  after all six audit files exist. C: blocked on other lanes.

