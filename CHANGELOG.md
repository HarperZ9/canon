# Changelog

## 0.1.0 — 2026-09-07

First GitHub release candidate for Canon.

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
- This release candidate is prepared for GitHub release review only. No PyPI
  publication claim is made.
