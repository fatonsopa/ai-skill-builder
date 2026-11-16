"""Claude Code transport for real, tool-enabled skill evaluation.

Permission allowlists are not an operating-system sandbox. The host must already
authorize the task's file/command access. No fallback widens those permissions.
"""
import json
import hashlib
from pathlib import Path
import tomllib
import yaml
from provider_results import claude_result_error, codex_public_capture

CLAUDE_TOOLS = ['Read', 'Glob', 'Grep', 'Write', 'Edit', 'Bash', 'Skill', 'WebSearch', 'WebFetch', 'Agent']


def command(executable, model, effort):
    args = [executable, '-p', '--model', model, '--output-format', 'stream-json',
            '--verbose', '--no-session-persistence', '--permission-mode', 'dontAsk',
            '--allowedTools', ','.join(CLAUDE_TOOLS), '--tools', ','.join(CLAUDE_TOOLS),
            '--setting-sources', 'project,local', '--strict-mcp-config',
            '--mcp-config', '{"mcpServers":{}}', '--settings', '{"disableAllHooks":true}']
    if effort:
        args += ['--effort', effort]
    return args


def capture(stdout):
    """Retain actual public text/tools/results; never private thinking blocks."""
    if isinstance(stdout, bytes):
        stdout = stdout.decode('utf-8', errors='replace')
    events, final, model, failure, provider_error = [], None, None, None, None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        kind = event.get('type')
        if kind == 'system' and event.get('subtype') == 'init':
            model = event.get('model')
            events.append({k: event[k] for k in ('type', 'subtype', 'model', 'tools', 'permissionMode', 'session_id', 'skills') if k in event})
        elif kind in {'assistant', 'user'}:
            message = event.get('message', {})
            content = [block for block in message.get('content', []) if isinstance(block, dict) and block.get('type') in {'text', 'tool_use', 'tool_result'}]
            if content:
                events.append(public_value({'type': kind, **{k:event[k] for k in ('uuid','session_id','parent_tool_use_id') if k in event}, 'message': {**{k:message[k] for k in ('id','model') if k in message}, 'role': message.get('role', kind), 'content': content}}))
        elif kind == 'result':
            events.append(public_value(event))
            observed = any(block.get('type') == 'tool_use' for prior in events
                           for block in prior.get('message', {}).get('content', []))
            error = claude_result_error(event, task_observed=observed)
            if error or event.get('subtype') != 'success':
                failure = 'Claude error: ' + (error['error'] if error else str(event.get('subtype')))
                cause = (error or {}).get('provider_error')
                if cause and cause['kind'] == 'usage_limit':
                    provider_error = cause
            else:
                final = event.get('result')
        elif kind == 'error':
            events.append(public_value(event))
            failure = 'Claude emitted an error event.'
    if not isinstance(final, str) or not final.strip():
        failure = failure or 'Claude returned no successful final response.'
    return {'events': events, 'final': final, 'resolved_model': model, 'failure': failure, 'provider_error': provider_error}


def stage_roles(installed, workspace, host, declarations=()):
    installed, workspace = Path(installed).resolve(), Path(workspace).resolve()
    record = installed / 'config/build_record.json'
    if record.is_file():
        roles = json.loads(record.read_text()).get('source', {}).get('execution', {}).get('roles', [])
        declarations = [*declarations, *[{'id': role['id'], **asset} for role in roles for asset in role['assets'] if asset['host'] == host]]
    result, names = [], set()
    for row in declarations:
        if row.get('host', host) != host:
            continue
        relative = Path(row['path'])
        path = (installed / relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(installed) or not path.is_file():
            raise ValueError('Candidate role asset is missing or outside the task-only installation.')
        raw = path.read_bytes()
        if row.get('sha256') is not None and row['sha256'] != hashlib.sha256(raw).hexdigest():
            raise ValueError('Candidate role asset changed before startup.')
        if host == 'codex':
            header = tomllib.loads(raw.decode('utf-8'))
            if any(not isinstance(header.get(k), str) or not header[k].strip() for k in ('name', 'description', 'developer_instructions')):
                raise ValueError('Codex role needs a standalone TOML name, description and developer_instructions.')
            name = header['name']
            destination = workspace / '.codex/agents' / (name + '.toml')
        else:
            parts = raw.decode('utf-8').split('---\n', 2)
            header = yaml.safe_load(parts[1]) if len(parts) == 3 and not parts[0] else None
            if not isinstance(header, dict) or any(not isinstance(header.get(k), str) or not header[k].strip() for k in ('name', 'description')):
                raise ValueError('Claude role needs named YAML frontmatter.')
            name = header['name']
            destination = workspace / '.claude/agents' / (name + '.md')
        if not name or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-_' for c in name) or name in names:
            raise ValueError('Duplicate or unsafe candidate role name.')
        names.add(name)
        if destination.exists():
            raise ValueError('Candidate role destination already exists; never use a global fallback.')
        for loaded in row.get('loaded_paths', []):
            target = (installed / loaded).resolve()
            if not target.is_relative_to(installed) or not target.is_file():
                raise ValueError('Missing candidate loaded instruction source.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        result.append({'role': row['id'], 'name': name, 'source': str(path), 'registered': str(destination),
                       'sha256': hashlib.sha256(raw).hexdigest(), 'host': host})
    return result


def public_value(value):
    """Filter private blocks even when nested in public tool return envelopes."""
    if isinstance(value, list):
        return [public_value(v) for v in value if not isinstance(v, dict) or v.get('type') not in {'thinking', 'reasoning', 'analysis', 'redacted_thinking'}]
    if isinstance(value, dict):
        return {k: public_value(v) for k, v in value.items() if k not in {'thinking', 'reasoning', 'analysis', 'encrypted_content', 'signature'}}
    return value
