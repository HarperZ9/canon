"""Client manifests share one explicit binding and permission contract."""
import json


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def bindings(prefix):
    names = ('context_db', 'workspace_id', 'project_id')
    return [item for name in names for item in (
        '--' + name.replace('_', '-'), '${' + prefix + name + '}')]


def manifests(version, native=False):
    plugin = {'name': 'canon-local', 'version': version,
              'description': 'Canon local context with explicit database and scope bindings.',
              'author': {'name': 'Zain Dana Harper'}, 'license': 'FSL-1.1-MIT'}
    command = '${PLUGIN_ROOT}/server/canon-local.exe' if native else 'python3'
    args = [] if native else ['-I', '-S', '-B', '${PLUGIN_ROOT}/server/serve.py']
    args += [item for flag, env in (('context-db', 'CANON_CONTEXT_DB'),
        ('workspace-id', 'CANON_WORKSPACE_ID'), ('project-id', 'CANON_PROJECT_ID'))
        for item in ('--' + flag, '${' + env + '}')]
    config = {'mcpServers': {'canon': {'command': command, 'args': args, 'type': 'stdio'}}}
    files = {'plugin.json': encoded(plugin), '.claude-plugin/plugin.json': encoded(plugin),
             '.codex-plugin/plugin.json': encoded({**plugin, 'skills': './skills/', 'mcpServers': './mcp.json'}),
             'mcp.json': encoded(config),
             '.mcp.json': encoded(config).replace(b'${PLUGIN_ROOT}', b'${CLAUDE_PLUGIN_ROOT}')}
    if native:
        files['manifest.json'] = encoded(native_manifest(plugin))
    return files


def native_manifest(plugin):
    settings = {}
    for key, kind, title in (('context_db', 'file', 'Canon context database'),
                             ('workspace_id', 'string', 'Workspace ID'),
                             ('project_id', 'string', 'Project ID')):
        settings[key] = {'type': kind, 'title': title, 'required': True,
                         'description': 'Explicit absolute SQLite file path with an existing parent.'
                         if key == 'context_db' else 'Bind every request to this nonempty scope ID.'}
    settings['context_write'] = {'type': 'boolean', 'title': 'Allow context writes',
        'description': 'Allow storing context in the selected database and scope. Purge is unavailable.',
        'default': False, 'required': False}
    return {'manifest_version': '0.3', **plugin, 'display_name': 'Canon Local',
        'server': {'type': 'binary', 'entry_point': 'server/canon-local.exe',
                   'mcp_config': {'command': '${__dirname}/server/canon-local.exe',
                    'args': bindings('user_config.') + ['--context-write=${user_config.context_write}']}},
        'compatibility': {'platforms': ['win32']}, 'user_config': settings}
