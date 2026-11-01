"""Bound routine testing retries without requiring a new approval each time.

The calling workflow retains its task, acceptance criteria and attempt history.
These are conservative local defaults, not a billing or provider quota estimate.
"""

MAX_ROUNDS = 5
MAX_EXTENSIONS = MAX_ROUNDS - 1
MAX_ADDITION = {'attempts': 2, 'handoffs': 4, 'seconds': 900, 'invocations': 4}


def check_totals(current, hard_limits=None):
    hard_limits = {} if hard_limits is None else hard_limits
    if not isinstance(hard_limits, dict) or set(hard_limits) - MAX_ADDITION.keys() or any(type(value) is not int or value < 0 for value in hard_limits.values()):
        raise ValueError('Hard limits must be nonnegative integer totals.')
    for name, maximum in hard_limits.items():
        if current.get(name, 0) > maximum:
            raise ValueError('Routine continuation would exceed the explicit user hard limit: ' + name)


def extension(history, additions, reason, *, current=None, hard_limits=None, stalled=False):
    """Validate and describe a routine continuation; never change caller state."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Record a concrete reason for continuing the authorized task.')
    if not additions or set(additions) - MAX_ADDITION.keys() or any(type(value) is not int or value < 0 for value in additions.values()) or not any(additions.values()):
        raise ValueError('Specify positive bounded additional limits.')
    if stalled:
        raise ValueError('Testing has stalled; diagnose and report the gap before more retries.')
    if sum(row.get('automatic') is True for row in history) >= MAX_EXTENSIONS:
        raise ValueError('Routine retry ceiling reached; retain results and report the remaining gap.')
    if any(value > MAX_ADDITION[name] for name, value in additions.items()):
        raise ValueError('Routine extension exceeds the per-batch retry ceiling.')
    current = current or {}
    check_totals({name: current.get(name, 0) + additions.get(name, 0) for name in current.keys() | additions.keys()}, hard_limits)
    return {'automatic': True, 'round': 2 + sum(row.get('automatic') is True for row in history), 'max_rounds': MAX_ROUNDS, 'reason': reason.strip(), 'additions': dict(additions)}
