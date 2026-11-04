"""Claude Code transport for real, tool-enabled skill evaluation.

Permission allowlists are not an operating-system sandbox. The host must already
authorize the task's file/command access. No fallback widens those permissions.
"""
import json
from provider_results import claude_result_error

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
                events.append({'type': kind, 'message': {'role': message.get('role', kind), 'content': content}})
        elif kind == 'result':
            events.append(event)
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
            events.append(event)
            failure = 'Claude emitted an error event.'
    if not isinstance(final, str) or not final.strip():
        failure = failure or 'Claude returned no successful final response.'
    return {'events': events, 'final': final, 'resolved_model': model, 'failure': failure, 'provider_error': provider_error}
