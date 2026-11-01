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
