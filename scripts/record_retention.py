#!/usr/bin/env python3
"""Retention for explicitly owned local record bundles; never app chat history."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import uuid

MARKER = '.record-retention.json'
DEFAULT_POLICY = {'routine_days': 30, 'investigation_days': 90, 'diagnostic_days': 7}


def _read(path):
    return json.loads(Path(path).read_text())


def _save(path, value):
    path = Path(path)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@contextlib.contextmanager
def _lock(parent, owner):
    if not re.fullmatch(r'[a-z0-9-]+', owner):
        raise ValueError('Use a stable lowercase record owner.')
    parent = Path(parent).resolve()
    parent.mkdir(parents=True, exist_ok=True)
    lock = parent / ('.record-retention-' + owner + '.lock')
    if lock.is_symlink():
        raise ValueError('Retention lock cannot be a symlink.')
    with os.fdopen(os.open(lock, os.O_CREAT | os.O_RDWR, 0o600), 'a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def _state(bundle):
    bundle = Path(bundle)
    if bundle.is_symlink() or (bundle / MARKER).is_symlink():
        raise ValueError('Never follow a record-bundle or marker symlink.')
    state = _read(bundle / MARKER)
    if state.get('schema_version') != 1 or state.get('bundle') != str(bundle.resolve()):
        raise ValueError('Record ownership does not match its location.')
    return state


def _fingerprint(bundle, children):
    digest = hashlib.sha256()
    for folder, dirs, files in os.walk(bundle, followlinks=False):
        relative = Path(folder).relative_to(bundle)
        if relative == Path('.'):
            dirs[:] = sorted(name for name in dirs if name not in children)
        else:
            dirs.sort()
        for name in sorted([*files, *[d for d in dirs if (Path(folder) / d).is_symlink()]]):
            path = Path(folder) / name
            if name == MARKER or name.startswith('.record-retention-'):
                continue
            digest.update(str(path.relative_to(bundle)).encode())
            if path.is_symlink():
                digest.update(('link:' + os.readlink(path)).encode())
            else:
                with path.open('rb') as stream:
                    for chunk in iter(lambda: stream.read(65536), b''):
                        digest.update(chunk)
    return digest.hexdigest()


def begin(bundle, owner, *, kind='routine', protected=(), outputs=(), policy=None, record_id=None):
    """Register a newly created/empty bundle; old directories are never adopted."""
    bundle = Path(bundle).absolute()
    if kind not in {'routine', 'investigation', 'diagnostic'} or bundle.is_symlink():
        raise ValueError('Use a real directory and supported record kind.')
    bundle = bundle.resolve()
    policy = dict(DEFAULT_POLICY if policy is None else policy)
    if set(policy) != set(DEFAULT_POLICY) or any(type(v) is not int or v < 1 for v in policy.values()):
        raise ValueError('Retention periods must be positive whole days.')
    protected = [str(Path(p).resolve()) for p in [Path(__file__).resolve().parents[1], *protected]]
    if any(bundle == Path(p) or bundle.is_relative_to(p) or Path(p).is_relative_to(bundle) for p in protected):
        raise ValueError('Record bundles must be separate from skills, sources and deliverables.')
    with _lock(bundle.parent, owner):
        if bundle.exists() and any(bundle.iterdir()):
            raise ValueError('Only a new empty bundle can opt in to retention; preserve historical records.')
        parent_state = _state(bundle.parent) if (bundle.parent / MARKER).exists() else None
        if parent_state and (parent_state['owner'] != owner or parent_state['closed_at'] is not None):
            raise ValueError('A child record needs an active parent with the same owner.')
        bundle.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(bundle, 0o700)
        state = {'schema_version': 1, 'record_id': record_id or str(uuid.uuid4()), 'bundle': str(bundle),
                 'owner': owner, 'kind': kind, 'policy': policy, 'created_at': time.time(),
                 'closed_at': None, 'resolved_at': None, 'outcome': None, 'pins': [],
                 'children': [], 'protected': [*protected, *[str(Path(p).resolve()) for p in outputs]], 'fingerprint': None}
        _save(bundle / MARKER, state)
        if parent_state:
            parent_state['children'].append(bundle.name)
            _save(bundle.parent / MARKER, parent_state)
    return state


def finish(bundle, *, outcome='success', resolved=False, pin=None):
    bundle = Path(bundle).absolute()
    state = _state(bundle)
    if outcome not in {'success', 'failed'}:
        raise ValueError('Record the observed success or failure.')
    with _lock(bundle.parent, state['owner']):
        state = _state(bundle)
        state['closed_at'] = state['closed_at'] or time.time()
        state['outcome'] = outcome
        if outcome == 'failed' and state['kind'] == 'routine':
            state['kind'] = 'investigation'
        if resolved and (outcome == 'failed' or state['kind'] in {'investigation', 'diagnostic'}):
            state['resolved_at'] = state['resolved_at'] or time.time()
        if pin and pin not in state['pins']:
            state['pins'].append(pin)
        if resolved:
            for child in state['children']:
                if Path(child).name != child or child in {'.', '..'}:
                    raise ValueError('Unsafe child record path.')
                child_path = bundle / child
                if (child_path / MARKER).is_file() and not child_path.is_symlink():
                    child_state = _state(child_path)
                    if child_state['closed_at'] is not None:
                        finish(child_path, outcome=child_state['outcome'], resolved=True)
        state['fingerprint'] = _fingerprint(bundle, state['children'])
        _save(bundle / MARKER, state)
    return state


def pin_reference(path, reference):
    """Protect every registered ancestor of a retained evidence file."""
    path = Path(path).resolve()
    protected = []
    for bundle in [path, *path.parents]:
        if not (bundle / MARKER).is_file():
            continue
        state = _state(bundle)
        with _lock(bundle.parent, state['owner']):
            state = _state(bundle)
            if reference not in state['pins']:
                state['pins'].append(reference)
                _save(bundle / MARKER, state)
        protected.append(str(bundle))
    return protected


def release(bundle, reference, reason):
    """Explicit retirement decision; age never releases acceptance evidence."""
    if not reason.strip():
        raise ValueError('Explain why this evidence is no longer relied upon.')
    bundle = Path(bundle).absolute()
    state = _state(bundle)
    with _lock(bundle.parent, state['owner']):
        state = _state(bundle)
        state['pins'].remove(reference)
        state.setdefault('releases', []).append({'reference': reference, 'reason': reason, 'at': time.time()})
        _save(bundle / MARKER, state)
    return state


def _eligible(bundle, state, now, inherited_hold):
    if inherited_hold or state['pins']:
        return 'protected_evidence'
    if state['closed_at'] is None:
        return 'active'
    if (state['kind'] == 'investigation' or state['outcome'] == 'failed') and state['resolved_at'] is None:
        return 'unresolved_investigation'
    anchor = state['resolved_at'] or state['closed_at']
    key = 'diagnostic_days' if state['kind'] == 'diagnostic' else 'investigation_days' if state['kind'] == 'investigation' else 'routine_days'
    if now < anchor + state['policy'][key] * 86400:
        return 'within_retention'
    if any(Path(p) == bundle or Path(p).is_relative_to(bundle) or bundle.is_relative_to(p) for p in state['protected']):
        return 'protected_path'
    if any((bundle / child).exists() or (bundle / child).is_symlink() for child in state['children']):
        return 'retained_child'
    if _fingerprint(bundle, state['children']) != state['fingerprint']:
        return 'changed_since_close'
    return 'expired'


def cleanup(parent, owner, *, dry_run=False, now=None):
    """First invocation previews; later invocations apply only owned expiry rules."""
    parent = Path(parent).resolve()
    now = time.time() if now is None else now
    with _lock(parent, owner):
        control = parent / ('.record-retention-' + owner + '.json')
        if control.is_symlink():
            raise ValueError('Cleanup control cannot be a symlink.')
        previous = _read(control) if control.exists() else {}
        first = not previous.get('previewed_at')
        preview = dry_run or first
        rows = []
        def visit_locked(bundle, inherited_hold=False):
            try:
                state = _state(bundle)
                if state['owner'] != owner:
                    return
                hold = inherited_hold or bool(state['pins']) or state['closed_at'] is None or ((state['kind'] == 'investigation' or state['outcome'] == 'failed') and state['resolved_at'] is None)
                for child in state['children']:
                    if Path(child).name != child or child in {'.', '..'}:
                        raise ValueError('Unsafe child record path.')
                    if (bundle / child).exists() or (bundle / child).is_symlink():
                        visit(bundle / child, hold)
                reason = _eligible(bundle, state, now, inherited_hold)
                row = {'record_id': state['record_id'], 'bundle': str(bundle), 'kind': state['kind'],
                       'outcome': state['outcome'], 'reason': reason, 'action': 'would_delete' if reason == 'expired' and preview else 'retained'}
                if reason == 'expired' and not preview:
                    # Recheck identity and contents immediately before the destructive step.
                    if _state(bundle) != state or _fingerprint(bundle, state['children']) != state['fingerprint']:
                        raise ValueError('Record changed during cleanup.')
                    shutil.rmtree(bundle)
                    row['action'] = 'deleted'
                rows.append(row)
            except (ValueError, OSError, KeyError, TypeError):
                rows.append({'bundle': str(bundle), 'action': 'retained', 'reason': 'invalid_or_unavailable_record'})
        def visit(bundle, inherited_hold=False):
            if bundle.parent == parent:
                visit_locked(bundle, inherited_hold)
            else:
                with _lock(bundle.parent, owner):
                    visit_locked(bundle, inherited_hold)
        for bundle in sorted(parent.iterdir()):
            if (bundle / MARKER).is_file() or (bundle / MARKER).is_symlink():
                visit(bundle)
        receipts = [r for r in previous.get('deletions', []) if r['at'] >= now - 90 * 86400]
        receipts += [{**r, 'at': now} for r in rows if r['action'] == 'deleted']
        report = {'mode': 'preview' if preview else 'apply', 'first_preview': first, 'at': now, 'records': rows}
        _save(control, {'previewed_at': previous.get('previewed_at') or now, 'first_preview': previous.get('first_preview') or (report if first else None), 'last_cleanup': report, 'deletions': receipts})
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['begin', 'finish', 'cleanup', 'pin', 'release'])
    parser.add_argument('--path', type=Path, required=True)
    parser.add_argument('--owner', default='skill-records')
    parser.add_argument('--kind', choices=['routine', 'investigation', 'diagnostic'], default='routine')
    parser.add_argument('--outcome', choices=['success', 'failed'], default='success')
    parser.add_argument('--resolved', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--reference')
    parser.add_argument('--reason', default='')
    args = parser.parse_args()
    try:
        if args.operation == 'begin':
            result = begin(args.path, args.owner, kind=args.kind)
        elif args.operation == 'finish':
            result = finish(args.path, outcome=args.outcome, resolved=args.resolved, pin=args.reference)
        elif args.operation == 'cleanup':
            result = cleanup(args.path, args.owner, dry_run=args.dry_run)
        elif args.operation == 'pin':
            if not args.reference:
                parser.error('pin needs --reference')
            result = pin_reference(args.path, args.reference)
        else:
            if not args.reference:
                parser.error('release needs --reference')
            result = release(args.path, args.reference, args.reason)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, json.dumps({'error': str(error)}) + '\n')


if __name__ == '__main__':
    main()
