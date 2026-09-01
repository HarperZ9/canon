# Platform Adapter Matrix

Date: 2026-08-30

Lane: Platform adapters

Status: Evidence report only. No product-code changes, publication, deployment, or package registration are authorized by this report.

## Scope

This audit answers which provider, IDE, CLI, API, and protocol surfaces can truthfully carry a Canon continuity capsule, what they lose, and which ambient bootstrap tier each can advertise under the Canon Pillar support definitions:

- Enforced: the host or adapter-controlled runner can block ordinary work until bootstrap succeeds.
- Native advisory: the host can automatically load persistent instructions or a connector that asks the agent to bootstrap first, but cannot technically force compliance.
- Guided: Canon can provide a launcher, template, import flow, first message, MCP prompt, or A2A task that the user or controller initiates.
- Unsupported: no safe documented import path exists, so the adapter is export-only.

This report does not claim enforcement for prompt-level rules, project instructions, memory, RAG, or user-initiated import flows.

## Inspected Evidence

Local evidence:

- `C:/dev/AGENTS.md`: workspace rules require truth labels, current sources, and `index` before architecture assumptions.
- `C:/dev/public/canon/CLAUDE.md`: Canon is a provider-neutral record container and currently ships F0 through V4 surfaces and gates.
- `C:/dev/public/canon/project-docs/SPEC-CANON-PILLAR-20260830.md`: ambient bootstrap lifecycle, tier definitions, evidence handoff, and initial quality gates.
- `C:/dev/public/canon/project-docs/audits/2026-08-30/README.md`: expected lane reports and audit boundary.
- `C:/dev/public/canon/src/canon/schema.py`: provider-neutral record envelope, five record kinds, `global` and `workspace` scopes, provenance, and clock-free ordering.
- `C:/dev/public/canon/src/canon/registry.py`: current surface allow-list: Claude Code global `~/.claude/CLAUDE.md`, Claude Code workspace `CLAUDE.md`, Codex workspace `AGENTS.md`, and Hermes workspace `SOUL.md`.
- `C:/dev/public/canon/src/canon/region.py`: managed markdown region boundary, byte-exact outside-region preservation, and off-limits behavior for files with no Canon markers.
- `C:/dev/public/canon/src/canon/textblock.py`: text surface only represents current `personality-block` records and refuses unsupported or ambiguous records.
- `C:/dev/public/canon/src/canon/backends/base.py`: `MemoryBackend` protocol, capability-token `declared_drops()`, and `guard_put` fail-closed behavior.

Workspace tool evidence:

- `mcp__index.index_map` and `mcp__index.index_router` both timed out after 300 seconds. C: blocked. Bounded `rg` scans over `C:/dev/public/canon` were used as fallback. C: verified.
- `mcp__forum.route` could not select a single owner and escalated across validation/reviewer lanes. The direct assignment in this task remains authoritative for this report. C: verified.

Official primary sources inspected:

- Claude apps: projects, project knowledge/instructions, data export, and memory import/export at `support.claude.com`.
  - https://support.claude.com/en/articles/9517075-what-are-projects
  - https://support.claude.com/en/articles/9519177-how-can-i-create-and-manage-projects
  - https://support.claude.com/en/articles/9450526-export-your-claude-data
  - https://support.claude.com/en/articles/12123587-import-and-export-your-memory-from-claude
  - https://support.claude.com/en/articles/10185728-understanding-claude-s-personalization-features
- Claude Code: overview, settings, hooks, permissions, MCP, project memory.
  - https://code.claude.com/docs/en/overview
  - https://code.claude.com/docs/en/settings
  - https://code.claude.com/docs/en/hooks
  - https://code.claude.com/docs/en/permissions
  - https://code.claude.com/docs/en/mcp
  - https://code.claude.com/docs/en/memory
- ChatGPT and Codex: projects, personalization, Work, AGENTS.md, CLI, sandboxing, config reference, Codex MCP server, GPT Actions.
  - https://learn.chatgpt.com/docs/projects
  - https://learn.chatgpt.com/docs/personalize
  - https://learn.chatgpt.com/docs/get-started-with-work
  - https://learn.chatgpt.com/docs/agent-configuration/agents-md
  - https://learn.chatgpt.com/docs/codex/cli
  - https://learn.chatgpt.com/docs/sandboxing
  - https://learn.chatgpt.com/docs/config-file/config-reference
  - https://learn.chatgpt.com/docs/mcp-server
  - https://developers.openai.com/api/docs/actions/introduction
- OpenAI API: conversation state, function calling, file search, data controls.
  - https://developers.openai.com/api/docs/guides/conversation-state
  - https://developers.openai.com/api/docs/guides/function-calling
  - https://developers.openai.com/api/docs/guides/tools-file-search
  - https://developers.openai.com/api/docs/guides/your-data
- OpenCode: rules, MCP servers, troubleshooting/storage, web, plugins, server, providers.
  - https://opencode.ai/docs/rules/
  - https://opencode.ai/docs/mcp-servers/
  - https://opencode.ai/docs/troubleshooting/
  - https://opencode.ai/docs/web/
  - https://opencode.ai/docs/plugins/
  - https://opencode.ai/docs/server/
  - https://opencode.ai/docs/providers/
- Gemini CLI: README, GEMINI.md, configuration, MCP, auto-memory, commands.
  - https://github.com/google-gemini/gemini-cli
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/gemini-md.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/configuration.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/auto-memory.md
  - https://github.com/google-gemini/gemini-cli/blob/main/docs/reference/commands.md
- Cursor: documentation index, rules, MCP, CLI.
  - https://cursor.com/docs
  - https://cursor.com/docs/rules
  - https://cursor.com/docs/mcp
  - https://cursor.com/docs/cli/overview
- GitHub Copilot: custom-instruction support and project customization.
  - https://docs.github.com/en/copilot/reference/custom-instructions-support
  - https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-copilot-overview
- MCP: current specification architecture, resources, tools.
  - https://modelcontextprotocol.io/specification/2026-07-28/architecture
  - https://modelcontextprotocol.io/specification/2026-07-28/server/resources
  - https://modelcontextprotocol.io/specification/2026-07-28/server/tools
- A2A: latest specification, task lifecycle, key concepts, enterprise notes.
  - https://a2a-protocol.org/latest/specification/
  - https://a2aproject.github.io/A2A/latest/topics/key-concepts/
  - https://a2aproject.github.io/A2A/latest/topics/life-of-a-task/
  - https://a2aproject.github.io/A2A/latest/topics/enterprise-ready/
- Local OpenAI-compatible endpoints:
  - https://docs.vllm.ai/en/latest/getting_started/quickstart/
  - https://docs.vllm.ai/en/v0.8.3/serving/openai_compatible_server.html

## Verified Local Current State

Canon already has a durable internal core, but not yet platform bootstrap adapters. C: verified.

- Record semantics: one `canon.record/v1` envelope with five kinds, two scopes, provenance, optional temporal state, and deterministic `create_ord`. Evidence: `src/canon/schema.py`.
- Storage contract: backends must declare capability loss through `declared_drops()` and refuse record-enforceable silent temporal loss through `guard_put`. Evidence: `src/canon/backends/base.py`.
- Existing write surfaces: `SURFACE_CATALOG` currently contains only Claude Code `CLAUDE.md` global/workspace, Codex workspace `AGENTS.md`, and Hermes workspace `SOUL.md`. There is no current catalog row for Gemini, OpenCode, Cursor, Copilot, ChatGPT app projects, Claude app projects, MCP, A2A, OpenAI API, or local OpenAI-compatible endpoints. Evidence: `src/canon/registry.py`.
- Markdown region mechanics: Canon owns only bytes inside explicit `<!-- canon:begin scope=... -->` and `<!-- canon:end -->` markers; files with no markers are off-limits. Evidence: `src/canon/region.py`.
- Markdown surface loss: the R0 text block surface represents only current `personality-block` records. Ingest canonicalizes rendered blocks as `harness="canon-text"` and drops the original native/session/model timestamps from that text representation. Evidence: `src/canon/textblock.py`.
- Capsule architecture: `CANON.md`, `canon.capsule/v1`, `.canonpack`, budget profiles, bootstrap witness, readiness probe, and cross-adapter loss testing are approved design direction, not implemented local code in this branch. Evidence: `SPEC-CANON-PILLAR-20260830.md` plus `rg --files C:/dev/public/canon`. C: verified.

## Adapter Matrix

| Surface | Strongest truthful bootstrap tier | Import/export state | Instruction hierarchy | Session/history availability | Startup lifecycle hooks | Local-file or connector access | Limits, privacy, auth boundary | Representable capsule semantics | Declared loss cases |
|---|---|---|---|---|---|---|---|---|---|
| Claude apps: Claude web, desktop, mobile | Native advisory. C: verified for project instructions/knowledge, inferred for capsule use. | Import: project knowledge upload, text/code snippets, project instructions, memory import flow. Export: individual data export includes conversation and account data for Free/Pro/Max; organization export is owner-controlled; memory export/import exists on web and Desktop. Mobile export is unavailable. | Profile instructions, project instructions, project knowledge, and skills exist, but no documented Canon-specific precedence. Project instructions apply only within the project. | Projects have self-contained chat histories and knowledge bases. Context is not shared across chats unless added to project knowledge. | No official startup hook or blocking readiness gate found for Claude apps in this bounded audit. C: unknown. | Uploads and project knowledge can carry `CANON.md`. Connector availability is plan and org dependent. | Claude account and plan gates apply. Team/Enterprise export is controlled by the organization's Primary Owner. Project sharing can expose knowledge/instructions to members. | Human `CANON.md` and a JSON manifest can be uploaded as knowledge or pasted as first message. Memory import can absorb a summarized personal context, but not the whole typed Canon record model. | No enforced pre-work bootstrap, no typed round-trip guarantee, RAG may retrieve partial knowledge, mobile export gap, project chat privacy/sharing boundaries differ from project knowledge. |
| Claude Code | Native advisory. C: verified. | Import: `CLAUDE.md`, settings, memory files, hooks, MCP. Export: local file writes, memory files, transcripts subject to retention settings, and any user-created files. | Claude Code docs identify `CLAUDE.md` as the standard static convention file. Settings are loaded from multiple JSON scopes, including local and managed settings. Working-directory moves load the new directory's `CLAUDE.md`, settings, MCP, plugins, skills, subagents, and env values after trust. | Auto memory uses `~/.claude/projects/<project>/memory/`; `MEMORY.md` and topic files are machine-local and not shared across machines or cloud environments. `MEMORY.md` startup load is limited to the first 200 lines or 25KB; `CLAUDE.md` loads up to 4 MiB and skips larger files. | Hooks can inject or block at specific events and `PreToolUse` can deny/force prompts for tool calls, but official docs warn resumed sessions replay saved hook text for past turns rather than re-running hooks. No audited proof that a startup hook blocks all ordinary reasoning before work. | Reads the launch directory by default, can add directories during startup or session, and can use MCP servers for external tools/data. | Workspace trust, permission rules, org managed settings, local/cloud session machine boundaries, and MCP server auth bound what is reachable. Hook decisions do not bypass deny/ask rules. | Existing Canon `CLAUDE.md` region is directly representable for current personality blocks. A launcher or hook can also produce a bootstrap witness file, and MCP can expose typed capsule resources. | Markdown surface loses typed non-personality records unless linked through manifest/archive. Text-region ingest normalizes provenance to `canon-text`. Memory is local-machine scoped. Hook-injected dynamic facts can become stale on resume. |
| ChatGPT apps: web, desktop, mobile, projects, Work | Native advisory. C: verified for projects/custom instructions/local Work, inferred for capsule use. | Import: project files, project instructions, local projects on desktop, Work local files/apps/browser when available, plugins/connectors, GPT Actions for Custom GPTs. Export: finished files and ChatGPT project/chat artifacts through product UI; current official export mechanics were not fully audited here. C: unknown. | Custom instructions apply across chats. Projects and repositories can add their own instructions. ChatGPT projects provide uploaded files, project instructions, and connected sources to chats in that project. | ChatGPT projects carry project files and context across related chats; each chat remains a separate outcome thread. Work cloud can continue after the local app is closed; local Work is needed for local files/apps. | No official app-level startup hook or blocking readiness gate found in this bounded audit. | Desktop local projects can access one or more local folders. Work can use files, plugins, approved tools, local apps, and browser when available. GPT Actions bridge natural language to REST APIs with configured auth. | Account, workspace, connector approvals, local-vs-cloud mode, and third-party connector/GPT Action auth apply. | `CANON.md` can be a project file, local-project file, connector result, GPT Action response, or first message. A plugin/connector can expose a capsule preview and readiness probe. | No host-enforced bootstrap, no guaranteed line-level owned region in project files, local files unavailable to cloud/mobile modes, connector retention/auth policies vary, and project/RAG retrieval may omit archive details. |
| Codex CLI, IDE extension, cloud/local Codex | Native advisory. C: verified. | Import: `AGENTS.md`, optional fallback instruction files, config, local repository files, MCP. Export: local file edits, commands, diffs, Codex cloud handoff/apply flows, MCP server conversations. | Codex builds an instruction chain once per run/session: global Codex home, project root to cwd, one file per directory, merge root-to-leaf, closer files override earlier guidance, and default combined cap is 32 KiB. Project-local config cannot override provider/auth/telemetry keys such as `model_provider`; user-level config controls those. | TUI sessions are launched runs. Codex MCP server exposes `codex()` and `codex-reply()` and keeps Codex alive across multiple agent turns. | No official blocking startup hook was verified for Codex itself in this bounded audit. `AGENTS.md` loads before work, but that is prompt/context loading, not a technical gate. | CLI can inspect local repos, edit files, and run local tools. Sandbox and approval policy bound filesystem and network autonomy. MCP extends tools. | Sandbox defines technical boundaries, approvals decide when Codex asks to cross them. Provider/base URL/auth are machine-level config. | Existing Canon catalog has `codex` workspace `AGENTS.md`, so a current personality-block surface is directly writable. A `codex exec` wrapper can run deterministic capsule compile and readiness probe before invoking ordinary Codex. | No current global `AGENTS.md` catalog row in Canon. Default instruction cap can omit content. No native typed capsule channel beyond files/MCP. Enforced behavior requires an external runner, not ordinary Codex UI alone. |
| OpenAI API: Responses, Conversations, function calling, file search | Enforced when Canon owns the application request pipeline; Unsupported as an ambient provider feature by itself. C: verified/inferred. | Import: instructions/messages, conversation items, file uploads/vector stores, tool/function outputs, MCP/connector tools where the host app supports them. Export: response items, tool outputs, conversation objects, application logs under caller control. | The API has no built-in project instruction hierarchy. The caller constructs system/developer/user instructions and conversation state. | Individual text generation requests are independent unless the caller sends previous messages. Conversations API can persist conversation state with durable identifiers across sessions, devices, or jobs. | Provider API does not define a user-facing startup hook. The caller can enforce bootstrap by refusing to call `/v1/responses` or `/v1/chat/completions` until Canon readiness passes. | File Search provides hosted vector stores. Function calling connects to caller-defined external systems. Local files are available only through caller code, uploads, or tools. | API key, org/project settings, endpoint data retention, and third-party tool policies apply. OpenAI's inspected data-controls table marks listed API endpoints as not used for training. ZDR makes `store` false for Responses and Chat Completions, while Conversations/vector stores retain application state until deleted and are not ZDR-eligible. | Full typed `canon.capsule/v1` is representable as JSON in the controlled runner. `CANON.md` can be sent as developer/user content, a file-search document, or tool result. The runner can require witness emission. | No native ambient bootstrap outside the caller app. Hosted retrieval can omit details. Retention differs by endpoint. Third-party tools have separate policies. Model token budget can force profile downgrade or refusal. |
| OpenCode | Native advisory. C: verified. | Import: project/global `AGENTS.md`, Claude `CLAUDE.md` fallbacks, `opencode.json` instructions, remote instruction URLs, plugins, custom tools, MCP. Export: local file edits, session/application data, public share links, server API. | On startup, OpenCode looks for local rules by traversing from current directory using `AGENTS.md` then `CLAUDE.md`, then global `~/.config/opencode/AGENTS.md`, then `~/.claude/CLAUDE.md` unless disabled. First matching file wins in each category. Extra `instructions` files and remote URLs can be combined with AGENTS files. | Session and message data are stored under `~/.local/share/opencode/` or equivalent Windows path. Web and terminal clients can share the same sessions/state when attached to the same server. | Plugins can hook into events and modify behavior, but no official blocking startup gate was verified in this audit. C: unknown for enforced bootstrap. | MCP, custom tools, local plugins, local repository files, and an OpenAPI server surface exist. Server can be protected with HTTP basic auth. | Remote instruction URLs have a 5 second fetch timeout. MCP servers add context and can exceed context limits. Shared conversations are public to anyone with the link. | `CANON.md` can be rendered as `AGENTS.md` or loaded through `opencode.json` instructions. Typed capsule can be exposed as an MCP resource/tool or through the OpenCode server. | No current Canon catalog row. First-match behavior can ignore a sibling `CLAUDE.md` when `AGENTS.md` exists. Remote instructions can fail or stale. Share links are public. Plugin hook enforcement remains unverified. |
| Gemini CLI | Native advisory. C: verified. | Import: hierarchical `GEMINI.md`, configurable context file names, `@file.md` imports, `/memory reload`, MCP servers, experimental Auto Memory candidates. Export: generated files, local transcripts, memory update patches/skills from Auto Memory, clipboard copy of last output. | Gemini CLI loads global, workspace/ancestor, and just-in-time `GEMINI.md` context files and sends the concatenated content with every prompt. `context.fileName` can include names such as `AGENTS.md`, `CONTEXT.md`, and `GEMINI.md`. Settings precedence runs from defaults to system/user/project/system override/env/CLI args. | `/clear` starts a new active conversation. `/compress` replaces chat context with a summary. Auto Memory records sessions locally as transcripts and proposes reviewable memory patches; it is experimental and disabled by default. | `/hooks` exists for lifecycle event customization, but this audit did not verify a startup hook that can block all ordinary work. C: unknown. | Built-in file operations, shell commands, web fetching, Google Search grounding, workspace directories, and MCP servers/resources are documented. | README advertises personal-account free-tier request limits. MCP servers connect via settings and can access resources. Auth depends on Google account/API key/provider and MCP server config. | Human `CANON.md` can be imported from `GEMINI.md` or `@file.md`; `canon.capsule/v1` can be referenced as an imported JSON file or MCP resource. | No current Canon `GEMINI.md` catalog row. `/memory reload` is manual. Auto Memory is experimental and not automatically applied. Context file concatenation does not preserve typed provenance without a manifest. |
| Cursor | Native advisory. C: verified. | Import: Project Rules in `.cursor/rules`, User Rules, Team Rules, AGENTS.md, MCP. Export: rules files and repository changes; chat/session export was not verified. C: unknown. | Cursor supports Project Rules, User Rules, Team Rules, and AGENTS.md. Project rules are `.mdc` files with frontmatter and can be version-controlled/scoped by path. Plain `.md` under `.cursor/rules` is ignored; AGENTS.md is the plain-markdown alternative. Team Rules can be enforced so users cannot disable them in Customize, but this is still prompt/context control, not a bootstrap block. | Official rules docs state large language models do not retain memory between completions. Current chat-history portability was not verified from official docs in this bounded pass. | Cursor docs include customization surfaces, but no verified startup hook that blocks ordinary work before Agent proceeds. C: unknown. | Cursor can work with codebases, integrations, CLI, and MCP. MCP supports stdio, SSE, and Streamable HTTP transports plus tools, prompts, resources, roots, elicitation, and apps. | Cursor account/team policy and MCP auth apply. Specific privacy/data-retention controls were not verified in this bounded audit. C: unknown. | `CANON.md` can be represented as AGENTS.md or as `.cursor/rules/*.mdc`; typed capsule can be carried by MCP resources/tools. | No current Canon catalog row. `.mdc` frontmatter and globs are Cursor-specific. Team-rule enforcement does not prove a readiness witness. Session-memory claims remain unknown. |
| GitHub Copilot: GitHub.com, IDEs, Copilot CLI, cloud agent, code review | Native advisory on supported surfaces. C: verified. | Import: repo-wide `.github/copilot-instructions.md`, path-specific `.github/instructions/**/*.instructions.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` on selected cloud-agent/CLI/IDE surfaces, personal and organization instructions where supported. Export: repository files, generated PRs/reviews, IDE edits; chat transcript export not audited. C: unknown. | GitHub's support matrix differs by environment. GitHub.com Copilot Chat supports personal, repo-wide, and org instructions; Copilot cloud agent supports repo-wide, path-specific, agent instruction files, and org instructions; VS Code Copilot Chat supports repo-wide, path-specific, and `AGENTS.md`; CLI supports repo-wide, path-specific, AGENTS/CLAUDE/GEMINI, and personal files. | Cloud agent/project interaction state exists in GitHub workflows, but portable session history behavior was not verified in official docs here. C: unknown. | No official blocking startup hook was verified. | Access is through GitHub repositories, supported IDE workspaces, Copilot CLI, and GitHub cloud-agent infrastructure. MCP support was not verified from the inspected official pages. C: unknown. | GitHub account, repository permissions, plan gates, organization policy, and IDE environment support determine access. | Canon can render `.github/copilot-instructions.md`, path-specific instruction files, or AGENTS.md/GEMINI.md/CLAUDE.md depending on target. | Support is inconsistent across environments. Plain markdown instruction files cannot carry full typed semantics without linked manifest/archive. No verified readiness witness or blocking bootstrap. |
| MCP hosts and Canon MCP server | Guided generically; Enforced only inside a host that explicitly gates on Canon before model work. C: verified/inferred. | Import/export: server resources, prompts, tools, and client roots/elicitation depending on host support. A Canon server can expose capsule resources and bootstrap tools. | MCP itself has client-host-server architecture, not an instruction hierarchy. The host aggregates context and manages permissions/lifecycle. | The 2026-07-28 MCP architecture is stateless at request level, with each request carrying protocol version/capabilities. Host applications can run multiple client instances and aggregate context. | MCP has no universal "run this before ordinary work" requirement. Host lifecycle controls determine whether bootstrap is enforced. | Resources expose context such as files/databases/application data; tools perform actions; prompts provide reusable workflows. | Host controls permissions, consent, and security boundaries. Each client has a 1:1 relationship with one server. Server data retention/auth is external to MCP and must be declared per deployment. | Best fit for typed `canon.capsule/v1`: `canon://capsule/current` resource, `canon.bootstrap` prompt, `canon.bootstrap/check` tool, and `canon.bootstrap/witness` result. | MCP can deliver semantics but cannot compel the LLM or host to use them. Hosts may omit resources/prompts, truncate context, or require user approval. Multi-server context can exceed model budget. |
| A2A agents | Guided generically; Enforced only when the A2A client/controller refuses ordinary task dispatch until bootstrap completes. C: verified/inferred. | Import/export: Agent Cards, Messages with Parts, Tasks, Artifacts, streaming task/status/artifact updates. | A2A discovery uses Agent Cards for identity, capabilities, skills, endpoints, auth, and interaction metadata. It does not define host prompt hierarchy. | Tasks can be polled with optional `historyLength`; streaming may return direct Message or Task lifecycle events, including artifacts. | No universal startup hook. Bootstrap is a first task/message convention unless a Canon controller enforces it before normal work. | A2A carries messages and artifacts between agents. Local files/connectors are agent-specific capabilities, not protocol defaults. | Agent Card auth and transport security apply. Enterprise docs emphasize sensitivity awareness, compliance, and data minimization for messages/artifacts. | Capsule can be a named Artifact with manifest and `CANON.md` part, followed by a readiness task whose completion artifact is the bootstrap witness. | Content-type support may reject capsule parts. `historyLength` can truncate history. Terminal tasks cannot receive further messages. No native Canon precedence or local filesystem boundary. |
| Generic local OpenAI-compatible endpoints, including vLLM | Enforced only through a Canon-owned wrapper or harness; endpoint alone is Guided/Unsupported for ambient bootstrap. C: verified/inferred. | Import: OpenAI-format chat/completions requests, selected provider-specific `extra_body`, local server command-line configuration. Export: API response bodies and wrapper logs. | No native instruction hierarchy beyond message order and model chat template. The wrapper must construct the effective system/developer/user content. | vLLM online server implements OpenAI-compatible endpoints and hosts one model at a time. It does not provide native durable conversation objects in the inspected docs. | No endpoint startup hook for per-conversation Canon bootstrap. A harness can enforce bootstrap before calling the endpoint. | Local files are available only through the wrapper/tools, not the endpoint. vLLM can be run locally and queried through OpenAI clients by setting `base_url`. | vLLM supports API-key checking via `--api-key` or `VLLM_API_KEY`. Compatibility is partial: docs note unsupported or ignored parameters such as `suffix`, `parallel_tool_calls`, and `user`; model repository `generation_config.json` can override sampling defaults unless disabled. | Full typed capsule can be included by a wrapper in the request; `CANON.md` can be system/developer content if the chat template preserves it. | OpenAI-compatible does not mean OpenAI-identical. Tool calling, roles, retention, context limits, tokenizer behavior, chat templates, and ignored params must be fixture-tested per endpoint. |

## Minimal Adapter Contract

Every Canon platform adapter should expose this contract. C: inferred from local Canon loss model and official surface docs.

### Descriptor

```json
{
  "adapter_schema": "canon.adapter/v1",
  "surface_id": "codex-cli",
  "surface_version": "observed or unknown",
  "tier": "Enforced | Native advisory | Guided | Unsupported",
  "tier_evidence": ["official URL", "local path"],
  "import_channels": ["file", "project-instructions", "mcp-resource", "api-message"],
  "export_channels": ["file", "api-object", "artifact", "data-export"],
  "instruction_hierarchy": [{"name": "workspace AGENTS.md", "precedence": 30}],
  "session_state": {"available": true, "scope": "local-machine", "retention": "declared or unknown"},
  "lifecycle_hooks": [{"event": "startup", "can_block": false, "evidence": "URL"}],
  "access": {"local_files": "read/write/none", "connectors": ["mcp"], "network": "host-controlled"},
  "limits": [{"name": "startup instruction bytes", "value": "32768", "behavior": "truncate/skip/refuse"}],
  "auth_boundary": ["account", "workspace", "org policy", "local OS permissions"],
  "privacy_boundary": ["provider retention", "third-party connector retention", "local-only"],
  "known_unknowns": ["chat export semantics not audited"]
}
```

### Operations

- `discover(surface_root) -> Descriptor`: inspect local files/config and attach official-doc source IDs.
- `capture_native_state() -> NativeState`: read allowed local instruction files, state handles, and connector metadata without copying secrets.
- `compile_capsule(profile) -> CapsuleBundle`: produce `CANON.md`, `canon.capsule/v1`, optional `.canonpack`, typed omissions, declared losses, hashes, and source identities.
- `preview_import(bundle, target) -> ImportPlan`: show exact target content, budget fit, lost semantics, redactions, and unsupported fields.
- `import_capsule(plan) -> ImportReceipt`: write or submit only the approved target surface.
- `bootstrap(target) -> BootstrapWitness`: run freshness checks and a readiness probe before normal work where enforceable; otherwise emit an advisory or guided witness.
- `export_native_state(target) -> CapsuleBundle`: extract records from the platform surface without claiming support for fields the platform cannot represent.
- `conformance(target) -> ConformanceReport`: execute the fixture zoo and fail on undeclared loss or overclaimed tier.

### Invariants

- No adapter may silently summarize away active goals, prohibitions, permissions, unresolved conflicts, or explicit unknowns. C: verified from SPEC quality gates.
- Every lossy transformation must record `loss_type`, `source_record`, `target_surface`, `reason`, and `receipt_hash`. C: inferred.
- Every advertised tier must be backed by a conformance fixture. If the fixture cannot prove blocking behavior, the maximum tier is Native advisory. C: inferred.
- Files without Canon markers are off-limits for region splices; adapters may create a separate guided export file but must not rewrite host prose as if owned. C: verified from `region.py`.
- Provider-specific auth, retention, and connector terms stay outside the capsule and are referenced by boundary metadata, not embedded secrets. C: inferred.

## Conformance Fixtures

Fixtures are named here for implementation planning only.

| Fixture | Purpose | Required assertion |
|---|---|---|
| `fixture_bootstrap_blocking` | Distinguish Enforced from advisory. | A normal task cannot reach the model/tool loop until Canon bootstrap either succeeds or visibly fails. |
| `fixture_instruction_precedence` | Verify hierarchy mapping. | A planted conflict across global, org, project, workspace, and session layers resolves exactly as the adapter descriptor says. |
| `fixture_must_keep_semantics` | Prevent lossy active-state summaries. | Active goal, permission, prohibition, unresolved conflict, and latest frontier survive in Needle and Handoff profiles or compilation fails. |
| `fixture_declared_loss` | Prove loss honesty. | Nonrepresentable fields, such as provenance on markdown-only surfaces, appear in the loss ledger with source hashes. |
| `fixture_secret_quarantine` | Protect export boundaries. | Planted tokens, `.env` content, browser profiles, and private key shapes are redacted or blocked with zero leakage in `CANON.md`, manifest, logs, and witness. |
| `fixture_budget_fit` | Test constrained models and app caps. | Capsule compiler selects a valid profile or refuses with typed omissions when target budget cannot fit mandatory fields. |
| `fixture_offline_rescue` | Verify immediate rescue. | With provider offline, local state can still produce `CANON.md`, manifest, omission ledger, and a failed-refresh witness. |
| `fixture_quota_exhaustion` | Separate provider failure from context loss. | Import/export records quota exhaustion without rewriting the capsule as stale or complete. |
| `fixture_concurrent_chats` | Exercise race handling. | Two simultaneous bootstraps write distinct witnesses and do not corrupt the capsule pointer or loss ledger. |
| `fixture_cross_machine` | Verify portability boundary. | Machine-local memories/files are marked unreachable on another machine and replaced by references or omissions. |
| `fixture_dirty_worktree` | Preserve user work. | Dirty repo state is hashed and reported; adapter does not overwrite, reset, or hide uncommitted files. |
| `fixture_mid_session_change` | Handle capsule mutation during work. | If capsule identity changes mid-session, the adapter detects it, emits a stale-session warning, and requires refresh/reprobe before critical work. |
| `fixture_mcp_capsule` | Test typed connector semantics. | MCP resource, prompt, tool, and witness round-trip the manifest without undeclared loss under the current MCP protocol. |
| `fixture_a2a_artifact` | Test remote-agent handoff. | A2A bootstrap task returns a capsule artifact and witness; content-type or history truncation failures are typed. |
| `fixture_openai_compat_subset` | Test local endpoints. | Each local/OpenAI-compatible endpoint declares unsupported or ignored request fields and proves role/tool/capsule behavior with golden prompts. |

## Cross-Platform Failure Cases

| Failure | Expected adapter behavior | Severity | Confidence |
|---|---|---|---|
| Offline provider or connector | Compile from local records where available; mark refresh `blocked/offline`; produce a witness that says work did not receive fresh remote context. | High | C: inferred |
| Provider quota exhaustion | Preserve last known capsule, mark provider call `blocked/quota`, and do not downgrade facts to current. Offer export-only or local endpoint path. | High | C: inferred |
| Concurrent chats or agents | Use capsule identity and source-state digest in every witness; require compare-and-swap or append-only witness writes; never let one chat overwrite another's frontier silently. | High | C: inferred |
| Cross-machine use | Treat local memories, local paths, local MCP auth, and local transcripts as unreachable unless packed, synced, or referenced. Claude Code explicitly documents machine-local auto memory. | High | C: verified/inferred |
| Dirty worktree | Hash and summarize git status; refuse destructive rewrite; for file-surface imports, require preview and write only managed regions. | High | C: verified/inferred |
| Mid-session capsule changes | Adapter should detect changed manifest hash before critical actions and run a readiness reprobe. Claude Code hook replay on resume shows why timestamps/SHAs injected earlier can stale. | High | C: verified/inferred |
| Host context cap or app RAG omission | Downgrade to smaller profile only if mandatory semantics survive; otherwise refuse. OpenCode warns MCP context can exceed limits; Codex and Claude Code publish instruction/memory caps. | High | C: verified |
| Unsupported content type | Fall back from `.canonpack` to `CANON.md` plus manifest, or refuse if mandatory source references cannot be carried. | Medium | C: inferred |
| Remote instruction fetch timeout | For OpenCode remote instructions, classify as `blocked/remote-instruction-timeout` after the documented 5 second timeout and use local fallback only if policy permits. | Medium | C: verified |
| Public share/export link exposure | Warn before creating public OpenCode share links or broad project sharing; never include secrets or private transcripts in public artifacts. | High | C: verified/inferred |
| Partial OpenAI-compatible behavior | Run endpoint-specific conformance before advertising tool calling, role fidelity, or request-field preservation; vLLM documents ignored/unsupported fields. | High | C: verified |

## Gaps

| Gap | Severity | Confidence | Evidence |
|---|---:|---|---|
| No implemented `canon.capsule/v1`, `.canonpack`, bootstrap witness, readiness probe, or platform adapter descriptors in the local Canon branch. | Critical | C: verified | `rg --files C:/dev/public/canon`; SPEC marks these as approved architecture. |
| No current Canon registry rows for Gemini, OpenCode, Cursor, Copilot, ChatGPT app projects, Claude app projects, MCP, A2A, OpenAI API, or local endpoints. | Critical | C: verified | `src/canon/registry.py`. |
| Existing markdown region surface cannot represent episodic memories, synthesized personas, ADR decisions, research refs, full provenance, relations, or audit chains inline. | High | C: verified | `src/canon/textblock.py`; `src/canon/backends/base.py`. |
| Platform support varies sharply by app, plan, IDE, and cloud/local mode, especially for Copilot and Claude/ChatGPT apps. | High | C: verified | Official support matrices and product docs above. |
| Blocking startup lifecycle hooks are not verified for Claude apps, ChatGPT apps, Codex UI, OpenCode, Gemini CLI, Cursor, or Copilot. | High | C: verified/unknown | Official docs inspected do not prove full pre-work blocking. |
| Privacy and data-retention boundaries are incomplete for Cursor, Copilot, OpenCode providers, and non-vLLM local endpoints in this bounded pass. | Medium | C: unknown | Not all official privacy/admin pages were in scope/time. |
| `index` tool timeout prevented a full workspace-level graph map. | Medium | C: blocked | MCP timeout after 300 seconds. |

## Acceptance Gates

The platform-adapter work is acceptable only when these gates pass:

1. Each adapter has a checked-in `canon.adapter/v1` descriptor with official source URLs, local evidence paths, support tier, loss ledger vocabulary, and auth/privacy boundary.
2. Every platform advertised above Native advisory has an executable blocking fixture. No fixture, no Enforced tier.
3. Existing Canon markdown surfaces continue to pass byte-stable region tests and refuse unmanaged files.
4. A generated `CANON.md` plus `canon.capsule/v1` manifest is byte-identical from identical normalized inputs and config.
5. Needle and Handoff profiles retain 100 percent of planted active goals, permissions, prohibitions, unresolved conflicts, and explicit unknowns or fail compilation.
6. Secret-quarantine fixture leaks zero planted secrets across file output, API payload, MCP resource, A2A artifact, logs, and bootstrap witnesses.
7. Cross-adapter round trips produce a machine-readable declared-loss report and fail on undeclared semantic loss.
8. Offline, quota, concurrent-chat, cross-machine, dirty-worktree, and mid-session-change fixtures produce classified visible failures, not silent continuation.
9. Local/OpenAI-compatible endpoints pass role, tool, context-budget, stop/streaming, and ignored-parameter fixtures before being marked compatible.
10. Every bootstrap witness records capsule identity, source-state identity, target surface, timestamp, checks performed, omissions, support tier, readiness result, and failure class.

## Now / Next / Later

| Priority | Work | Outcome |
|---|---|---|
| Now | Implement `canon.adapter/v1` descriptor schema and golden descriptor fixtures for Claude Code, Codex, OpenAI API runner, MCP, A2A, and local OpenAI-compatible endpoint wrapper. | Prevents overclaiming and creates the adapter evidence spine. |
| Now | Add `CANON.md` plus `canon.capsule/v1` compiler floor with loss ledger and mandatory-field refusal. | Gives every surface a minimal portable artifact before native integrations exist. |
| Now | Add conformance fixtures for bootstrap blocking, instruction precedence, declared loss, offline, quota, concurrent chats, cross-machine, dirty worktree, and mid-session capsule changes. | Converts the audit claims into executable gates. |
| Now | Add read-only generated adapter report command that outputs this matrix from descriptors and fixture results. | Reduces manual drift in future audits. |
| Next | Add registry rows or separate adapter modules for Gemini `GEMINI.md`, OpenCode `AGENTS.md`/`opencode.json`, Cursor AGENTS/rules, and Copilot instruction files. | Expands native advisory coverage while preserving host-specific semantics. |
| Next | Build Canon MCP server resources/prompts/tools and A2A bootstrap task/artifact flow. | Provides typed interop channels for hosts that can adopt them. |
| Next | Build a Codex/Claude Code/OpenCode/Gemini launcher that compiles capsule, writes witness, starts the target, and marks tier as Guided unless a host-specific blocker is proven. | Gives immediate rescue without overstating host lifecycle control. |
| Next | Complete official privacy/admin research for Cursor, Copilot, OpenCode providers, Claude/ChatGPT enterprise controls, and additional local endpoints such as llama.cpp/Ollama/LM Studio/LocalAI. | Fills current C: unknown boundary rows. |
| Later | Define a public `Canon Compatible` test suite with per-surface badges: Export, Import, Advisory Bootstrap, Enforced Bootstrap, Typed Capsule, Loss Ledger, Secret Quarantine. | Makes third-party adoption testable. |
| Later | Negotiate or contribute upstream host hooks where projects lack blocking startup lifecycle support. | Moves selected surfaces from advisory/guided to enforceable without wrapper-only claims. |
| Later | Add UI/UX capsule preview and semantic diff for nontechnical users and accessibility test coverage. | Supports visible truth and broad access promises. |

## Operator Decisions Required

- Decide whether wrapper-enforced OpenAI/API/local endpoint flows may be labeled Enforced with a qualifier, or whether the Canon public copy should reserve Enforced only for native host hooks.
- Decide which surfaces get first implementation: recommended order is OpenAI API runner, Codex, Claude Code, MCP, A2A, local OpenAI-compatible endpoint, then file-based advisory adapters for Gemini/OpenCode/Cursor/Copilot.
- Decide whether `CANON.md` should be rendered as a single universal file plus target-native thin shims, or as distinct host-native files whose first section links to a shared manifest.
- Decide the minimal public privacy baseline for connector surfaces whose provider retention policies are not fully audited yet.
