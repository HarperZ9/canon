# Changelog

## Unreleased

Canon starts to carry a project's working state between models and tools.

- Adds a stable project identity (`canon workspace id`). A project with a
  remote is keyed on the normalized remote URL, so two clones or a moved
  checkout stay one project; a project with no remote is keyed on its path.
  Credentials in a remote URL never reach the key. A `.git` in the home
  directory or a filesystem root claims only itself, so a dotfiles repository
  does not merge every project below it.
- Adds a per-project record store (default `~/.canon/store`, or
  `CANON_STORE`). Each stored row names its project, and reading a file that
  holds another project's row fails instead of mixing the two. Another
  project's records are readable only when named.
- New records are workspace records. `canon workspace promote` is the only way
  into global scope, and `canon workspace adopt` is the only way to copy another
  project's records in; both need a reason and both are logged.
- Adds three workspace-state record kinds under their own schema tag,
  `canon.workspace-state/v1`: `workspace-focus` (goal, active areas, branch),
  `work-item` (title and status), and `environment-constraint` (a constraint or
  a quirk). Decision records gain an optional `rejected_alternatives` list, each
  entry an option and the reason it was dropped. Records of the five existing
  kinds keep the `canon.record/v1` tag and their exact bytes.
- Adds `canon workspace focus`, `task`, `set-status`, `decide` (with
  `--reject OPTION REASON`) and `constraint` (with `--quirk`) to write that
  state by hand.
- Adds `canon handoff --to <target>`, a resume brief for `claude-code`,
  `codex`, `gemini-cli`, `cursor`, `copilot` or plain `markdown`: focus, open
  work, recent decisions with their rejected alternatives, then constraints.
  The brief fits the target's budget as a strict prefix of that order and ends
  with a `Left out` report; `--receipt` writes a `canon.handoff-receipt/v1`
  receipt with digests of the brief and of the records it came from.
- Adds `canon switch --to <target>`, which writes the target's instruction file
  region with the project's blocks and the brief, through the write allow-list
  and only between the canon markers. `--dry-run` writes nothing, `--create`
  makes a missing file, and a file Codex would truncate is refused.
- Adds `canon workspace import --from claude-code|codex <file>`. It reads a
  Claude Code session or a Codex rollout (0.32 or later) and proposes focus,
  work items (from the last plan tool call and `TODO` markers), decisions and
  failed approaches, each with an origin naming the file, its digest, the line
  and the rule. Proposals render nothing until `canon workspace accept`;
  `reject` needs a reason and is remembered.
- Each importer declares what it drops and counts it; content it has not seen
  refuses the import unless declared with `--drop-type`. A source that names a
  different repository or working directory is refused unless
  `--accept-foreign-source` is given.
- Adds a secret scrubber in front of every import. Provider keys, tokens, JWTs,
  private keys, bearer and API-key headers, connection-string passwords and
  secret-named assignments are replaced with `[REDACTED:<rule>]`. The store
  also refuses any record that still matches, including one typed by hand, and
  a brief or instruction region that would carry one is refused.
- Adds three surfaces to the write allow-list: `GEMINI.md`,
  `.github/copilot-instructions.md`, and one canon-owned Cursor rule,
  `.cursor/rules/canon.mdc` (created with `alwaysApply: true` frontmatter).
  The allow-list is now seven exact paths.
- Personality blocks may carry `applies_to` glob patterns. No surface can load
  a block for some files only, so each target declares the downgrade: the block
  is written always-on with an `Applies to:` line the model reads as advice.
  Claude Code and Gemini CLI also declare that an `@path` line is a file import
  there. A per-target round-trip verdict fails on any difference a target did
  not declare; `canon workspace targets` prints the table.
- The region grammar moves to `canon.textblock/v1` for the optional `applies`
  attribute. A region with no scoped block is byte-identical to v0.
- `write_surfaces` reports a missing file as `missing` and does not create it.
- Registers five new version pins: `project-id`, `project-row`,
  `workspace-state`, `handoff-receipt` and `import-report`.

Limits:

- The identity reader does not follow git `include` directives or `insteadOf`
  rewrites.
- Renaming a remote, or moving a project that has no remote, changes its id.
  The old records are kept and can be adopted; nothing merges them on its own.
- The four storage adapters still hold only the five original kinds. The
  workspace-state kinds live in the per-project store.
- The per-target budgets come from each host's public documentation, read on
  2026-09-23. Hosts change; the numbers are defaults and can be overridden.
- The brief lists what was recorded. It does not know about work that happened
  in a session nobody recorded or imported.
- The importers use fixed text patterns. A decision or task phrased another
  way is not proposed, and a proposal is a candidate, not a fact.
- Neither session format is a stable public interface. The importers were
  checked against public sources on 2026-09-23 and refuse content they do not
  recognise rather than guess.
- The scrubber recognises secrets by shape. A secret with no recognisable shape
  passes through; email addresses are not redacted.
- Gemini CLI, Cursor, ChatGPT and Claude web exports have no importer yet.

## 0.2.0 - 2026-09-22

- Publishes to PyPI as `flywheel-canon`. The bare name `canon` belongs to an
  unrelated project, so the distribution carries the prefix while the console
  script stays `canon`.
- Adds an OIDC trusted-publishing release workflow with tag/version, artifact
  digest, clean-venv entry-point resolution, and sdist-rebuild gates.
- Adds run-lock concurrency control, and fixes POSIX run-lock descriptor release.
- Adds doctor diagnostics, retention planning, replay checks, rescue handoff, and
  an import review policy.
- Hardens Canon source reads.

## 0.1.0 - 2026-09-07

First GitHub release for Canon.

- Keeps the existing read-only MCP surface: `canon.status`, `canon.doctor`,
  `canon.blocks`, `canon.render`, `canon.validate`, and `canon.check`.
- Adds provider-neutral continuity preview and export from explicit
  `records.jsonl` and `atoms.jsonl` inputs.
- Exports Canon Markdown, capsule JSON, readiness JSON, or a three-file bundle
  containing `CANON.md`, `canon.capsule.json`, and `readiness-probe.json`.
- Records source-state hashes, artifact hashes, target tier, omissions, and
  does-not-prove limits in the generated capsule outputs.
- Uses confined bundle publication or fails closed. On Windows, the final bundle
  directory rename is parent-handle-relative and leaf-only.

Limits:

- Canon does not import ChatGPT web conversations, Codex task databases, Claude
  web history, Claude Code sessions, provider auth caches, or credentials.
- The `codex-cli` and `claude-code` targets are native-advisory. App and web
  targets remain guided until their hosts provide stronger startup evidence.
- Bundle export proves the command's publication boundary, not immutability
  after the command returns.
- New bundle creation currently requires the supported Windows native backend.
  Linux and macOS refuse new bundle creation without writing. Preview and stdout
  exports remain available there.
- Release downloads are distributed through GitHub. No PyPI publication claim
  is made.
