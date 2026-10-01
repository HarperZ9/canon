# Canon local client

Canon keeps project context in a local database you choose and lets your assistant search and read it, scoped to one workspace and project.

## Try it

- Check that the Canon context store is healthy.
- Search Canon for decisions about the release checklist.
- Show the full Canon record behind the first search result.

## Marketplace source distribution

This folder packages the source plugin from release 0.6.0. It requires Python 3.11 or later, available as `python3`. It includes the tool source and no model or bundled runtime. The connected client supplies any model used in the conversation.

The separate [Windows x64 native download](https://github.com/HarperZ9/canon/releases/download/v0.6.0/canon-0.6.0-win-x64.mcpb) includes its runtime. That download is a manual MCPB package and is not part of this source plugin. Directory approval and availability remain unverified.

This branch contains the installable plugin. Build commands in the release README below apply to the [product source tag](https://github.com/HarperZ9/canon/tree/v0.6.0). DISTRIBUTION.json records the published asset digest and every packaging change; any SOURCE.json describes the original release payload.

On Windows, `python3` can resolve to the Microsoft Store alias instead of an installed Python. Install Python 3.11 or later from python.org or your package manager, and turn off the `python3.exe` App execution alias in Windows settings if the server does not start.

## Details

Canon supplies local context tools to an MCP client using the model the operator chooses. It includes no model, inference endpoint, network listener or background service.

## Bind the connection

In Claude Code setup, supply the context database file, workspace ID and project ID. For portable or generic MCP clients, supply `--context-db` with an absolute SQLite file path whose parent exists, and `--workspace-id` and `--project-id` with explicit nonempty IDs. Every request stays bound to that database and scope. IDs select data; they do not authenticate a user. Linked paths are refused, but path validation is not an OS sandbox.

The default profile exposes health, query and get. Add `--context-write=true` or `--allow-context-write` to permit ingestion. A tool call or environment variable cannot grant writes. Purge is unavailable in this client, including when the legacy purge environment variable is present.

Read access requires an existing identity-bearing Canon database. Reads use an in-memory snapshot capped at 256 MiB and require Python's SQLite `deserialize` support. Reads create no SQLite sidecar file and work in DELETE or WAL journal mode, also while another process changes the mode; a request retries for up to 5 seconds while a writer commits, then reports the store busy. This client does not repair or migrate the database. A writable launch can initialize a new selected database. See the [client guide](https://github.com/HarperZ9/canon/blob/main/docs/client-packages.md) for configuration and limits.

## Install

The source ZIP requires Python 3.11 or newer. Extract the complete ZIP. Configure a stdio client with a trusted absolute Python executable and arguments `-I -S -B /absolute/path/server/serve.py`, followed by the three binding flags. The checked-in plugin folder uses the repository's adjacent `src` directory; the source ZIP contains its own source tree.

Claude manifests use `${CLAUDE_PLUGIN_ROOT}`. Portable and Codex manifests use `${PLUGIN_ROOT}`. Portable and Codex binding placeholders use `CANON_CONTEXT_DB`, `CANON_WORKSPACE_ID` and `CANON_PROJECT_ID`; those clients must resolve them to explicit argument values. Claude Code uses the required setup fields in this distribution. Replace `python3` with a trusted absolute Python path where necessary. No client configuration is edited automatically.

The Windows x64 native ZIP includes the Python runtime. Extract all files and point the client at the absolute `server/canon-local.exe` path with the same binding flags. The MCPB offers the database, workspace and project settings and an **Allow context writes** option that defaults to off. Restart the connection after changing settings. Native ZIP and MCPB contain identical executable bytes.

## Troubleshooting and limits

A missing binding, relative database path, linked path component, unresolved placeholder or malformed boolean stops startup. Correct the binding and restart the client. A write refusal requires an operator decision about the launch grant. Keep the full archive together and verify its hashes against `SHA256SUMS`.

Local protocol checks do not establish installed-client compatibility, marketplace acceptance or clean-machine compatibility. Unsigned Windows artifacts may receive platform warnings. Build receipts distinguish development and release candidates and record source and native dependency hashes.

## Claude Code write permission

**Allow context writes** defaults to false. The default needs an existing, identity-bearing Canon database prepared as described above. Enable writes only to approve ingestion in the selected database and scope; an approved writable launch may initialize a new selected database. Purge remains unavailable. Restart the connection after changing this setting. No default database or scope is supplied. Cowork setup for the required fields is not established; use Claude Code for this source distribution.
