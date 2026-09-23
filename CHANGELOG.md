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
- Registers three new version pins: `project-id`, `project-row` and
  `workspace-state`.

Limits:

- The identity reader does not follow git `include` directives or `insteadOf`
  rewrites.
- Renaming a remote, or moving a project that has no remote, changes its id.
  The old records are kept and can be adopted; nothing merges them on its own.
- The four storage adapters still hold only the five original kinds. The
  workspace-state kinds live in the per-project store.

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

## 0.1.0 — 2026-09-07

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
