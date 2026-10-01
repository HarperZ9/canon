# Canon local client packages

Canon keeps context under your control when you change models or clients. The
local client profile exposes one database, workspace and project selected at
launch. Flywheel remains the full native application; this package supplies
Canon tools to another client using the model you choose there.

## Choose a package

- The source plugin ZIP requires Python 3.11 or later. It includes Claude Code,
  Codex and portable stdio manifests, the server source and a usage skill.
- The Windows x64 ZIP includes a Python runtime and a console executable.
- The Windows MCPB contains the same executable for clients that support binary
  desktop extensions. Enter the database file, workspace ID and project ID during
  setup. **Allow context writes** starts off.

Download assets from the [versioned releases](https://github.com/HarperZ9/canon/releases)
and verify the supplied SHA256SUMS before extraction. Keep the complete package
together. Local MCP compatibility does not establish admission to a marketplace
or availability in a browser-only ChatGPT or Claude session.

## Launch and permissions

Use an absolute executable path in your MCP client's command setting. For the
native package, select `server/canon-local.exe`. Pass these arguments, replacing
the placeholders with your own approved values:

```text
--context-db <absolute-database-file>
--workspace-id <workspace-id>
--project-id <project-id>
--context-write=false
```

For the source package, use an absolute Python executable and pass
`-I -S -B <absolute-package-directory>/server/serve.py` before those arguments.
For an installed Python package, `canon-client` or `python -m canon.client_mcp` accepts the same
binding arguments. No command changes your client's settings automatically.

The default profile offers context health, query and get. It reads an existing
Canon context database into an audited in-memory snapshot without initializing or
migrating the on-disk store. A launch with
`--context-write=true` or `--allow-context-write` adds ingest and may create a
database. Change that setting outside the conversation and restart the server.
A tool call, retrieved instruction or ambient legacy purge setting cannot enable
the grant. Workspace and project identifiers are scope selectors, not user
authentication.

This profile does not expose purge, automatic client capture, export into
instruction files, or reconcile. The existing Canon CLI and legacy MCP entrypoints
retain their separate behavior. Use the documented CLI workflow when you need
those actions; installing this client package does not enable them.

## Privacy and troubleshooting

Canon runs locally and includes no model, hosted endpoint or publisher inference
compute. A client may send returned context to its configured model provider.
Review that client's data policy before connecting a private context store.
Context ingest and retrieval retain the redaction and provenance protections from
0.4.2; redaction is pattern based and cannot identify every sensitive fact.

The selected database remains under the operating system's file permissions.
Restrict it to your account. Launch grants constrain this adapter's tools; they
are not an operating-system sandbox and do not constrain another process with
filesystem access. Store identity checks reject replacement by a different Canon
store. Stop the connection before moving the selected database.

Missing or relative bindings, unknown flags and malformed permission values stop
startup. Select an existing store for read-only use. A newly approved writable
store needs a writable parent directory. If a tool refuses a different workspace
or project, change the launch binding only after deciding to grant that scope.
If integrity checks fail, preserve the files and investigate before further use.
A read-only launch copies the database file into memory for each request and
never opens the file through SQLite, so it creates no `-journal`, `-wal` or
`-shm` file and takes no lock. It reads a store in DELETE or WAL journal mode,
including a store whose journal mode another process changes while the client
runs. For a WAL store it applies the committed frames of the `-wal` file to the
copy in memory, by the same rules SQLite uses to recover a WAL. Each request
sees the records an authorized writer committed before it started. While a
writer is committing, or a file changes during the copy, the client retries for
up to 5 seconds and then refuses the request as busy; a journal left by a writer
that crashed keeps the store busy until a writer opens it. Read snapshots,
database and WAL together, are limited to 256 MiB and require a Python SQLite
build with `Connection.deserialize`; the native package includes that support.
Larger stores require a different authorized retrieval workflow.
Windows binaries are unsigned; signing and clean-machine client acceptance remain
limits of this release.

## Reproduce a package

From a checkout, run the full test suite with `python -m pytest`. The client
builder accepts a new output directory:

```text
python scripts/build_client_package.py <new-output-directory>
python scripts/build_client_package.py <other-output-directory> --native
```

Native builds require Windows x64 and PyInstaller. Use canonical absolute TEMP
and TMP paths. Release builds add `--mode release` and require a clean checkout
whose exact HEAD is tagged with the declared version. Source digests, runtime
dependency digests, payload hashes and qualification limits accompany the assets.
The synthetic native acceptance checks use isolated temporary state, restart the
process between operations and verify retrieval, provenance and refusals. Passing
them does not measure recall quality, establish adoption or prove every client
can install the package.

Report reproducible setup issues through [Canon issues](https://github.com/HarperZ9/canon/issues).
Include the version, platform and a synthetic reproduction. Do not attach private
databases, credentials or conversation contents.
