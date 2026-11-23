"""Interpret explicit Claude result errors without starting a provider process."""
import json


def claude_result_error(result, task_observed=False):
    if not isinstance(result, dict):
        return None
    subtype = result.get('subtype')
    if not (result.get('is_error') or result.get('api_error') or
            result.get('terminal_reason') == 'api_error' or
            subtype not in (None, 'success')):
        return None
    message = str(result.get('result') or result.get('api_error') or subtype or 'Claude reported an error.')
    error = {'status': 'failed', 'error': message}
    code = result.get('api_error')
    if code or result.get('terminal_reason') == 'api_error':
        usage = result.get('usage') or {}
        keys = ('input_tokens', 'output_tokens', 'cache_read_input_tokens', 'cache_creation_input_tokens')
        numeric = lambda v: type(v) in (int, float)
        if task_observed or any(numeric(usage.get(k)) and usage[k] > 0 for k in keys):
            started = True
        elif all(numeric(usage.get(k)) and usage[k] == 0 for k in keys[:2]):
            started = False
        else:
            started = None
        kind = 'usage_limit' if code == 'usage_limit_reached' else 'api_error'
        error.update(
            status='infrastructure_failure' if started is False else 'failed',
            failure_kind='provider_usage_limit' if kind == 'usage_limit' else 'provider_error',
            provider_error={'kind': kind, 'code': code, 'http_status': result.get('api_error_status'),
                            'message': message, 'task_started': started})
    return error


def claude_stdout_error(stdout):
    try:
        value = json.loads(stdout)
    except (ValueError, TypeError):
        return None
    return claude_result_error(value)



def codex_public_capture(captures, parent_thread, workspace):
    """Normalize the observed public read_thread surface, excluding reasoning."""
    from pathlib import Path
    if not isinstance(captures, list) or not captures:
        raise ValueError('Supply actual public thread API captures.')
    by_id = {}
    allowed = {'userMessage', 'agentMessage', 'commandExecution', 'fileChange',
               'mcpToolCall', 'collabAgentToolCall', 'subAgentActivity', 'imageView', 'webSearch'}
    for capture in captures:
        thread = capture.get('thread', {})
        identifier = thread.get('id')
        if not identifier or identifier in by_id or Path(thread.get('cwd', '')).resolve() != Path(workspace).resolve():
            raise ValueError('Public capture belongs to another thread workspace or repeats a thread.')
        if capture.get('page', {}).get('hasMore'):
            raise ValueError('Recover omitted public turns before importing a complete capture.')
        turns = capture.get('turns')
        if not isinstance(turns, list):
            raise ValueError('Public thread capture is missing its actual turns.')
        events = [{'thread_id':identifier, 'turn_id':turn['id'], 'turn_status':turn.get('status'), 'item':item}
                  for turn in turns for item in turn.get('items', []) if item.get('type') in allowed]
        by_id[identifier] = {'thread': {'id':identifier, 'cwd':thread['cwd']}, 'events':events}
    if parent_thread not in by_id:
        raise ValueError('Public supplement lacks the actual execution parent.')
    linked, pending = {parent_thread}, [parent_thread]
    while pending:
        current = pending.pop()
        for event in by_id[current]['events']:
            item = event['item']
            children = [item.get('agentThreadId')] if item['type'] == 'subAgentActivity' else item.get('receiverThreadIds', []) if item['type']=='collabAgentToolCall' else []
            for child in children:
                if child in by_id and child not in linked:
                    linked.add(child);pending.append(child)
    if set(by_id) - linked:
        raise ValueError('Unrelated or inherited threads cannot be attributed to this execution.')
    return {'schema_version':1, 'origin':'codex_app.read_thread', 'parent_thread':parent_thread,
            'workspace':str(Path(workspace).resolve()), 'threads':[by_id[k] for k in sorted(linked)],
            'limits':['Only the supplied public API surface is captured; private reasoning is excluded. Truncated outputs retain their truncation markers. Tool and reviewer identities are reported host observations.']}
