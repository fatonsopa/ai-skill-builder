#!/usr/bin/env python3
"""Plan impacted checks by default; run a full batch only with bound user authorization."""
import argparse
import ast
import fnmatch
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from repository_files import inventory

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def state_path(root):
    return Path.home() / '.cache/skill-test-runs' / (digest(str(Path(root).resolve())) + '.json')


def changed_files(root):
    current = inventory(root)
    checkpoint = state_path(root)
    if checkpoint.exists():
        previous = json.loads(checkpoint.read_text())
        if Path(previous.get('root', '')).resolve() != Path(root).resolve():
            raise ValueError('The test checkpoint belongs to another repository.')
        before = previous['files']
        return sorted(name for name in before.keys() | current.keys() if before.get(name) != current.get(name))
    result = subprocess.run(['git', 'diff', '--name-only', '--no-renames', '-z', 'HEAD'], cwd=root, capture_output=True)
    if result.returncode:
        raise ValueError('No checkpoint or Git baseline; provide the exact changed paths.')
    untracked = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard', '-z'], cwd=root, capture_output=True, check=True)
    return sorted(set(name for name in (result.stdout + untracked.stdout).decode().split('\0') if name))


def broad_command(argv):
    values = [str(value) for value in argv]
    if '-m' in values and 'unittest' in values:
        tail = values[values.index('unittest') + 1:]
        if not tail:
            return True
        if 'discover' in tail:
            return '-p' not in tail or tail.index('-p') + 1 >= len(tail) or any(mark in tail[tail.index('-p') + 1] for mark in '*?[')
    if '-m' in values and 'pytest' in values:
        tail = values[values.index('pytest') + 1:]
        return not any(not item.startswith('-') for item in tail)
    return False


def authorize_full(root, authorization):
    if authorization is None:
        raise ValueError('Full suites are disabled during iteration. Supply the actual user authorization after the batch is finished.')
    record = json.loads(Path(authorization).read_text())
    if record.get('batch_complete') is not True or not isinstance(record.get('user_instruction'), str) or not record['user_instruction'].strip():
        raise ValueError('Final testing requires the actual user instruction confirming this batch is finished.')
    if record.get('artifact_sha256') != digest(inventory(root)):
        raise ValueError('Changes after authorization invalidate final testing approval.')
    return record


def changed_test_methods(root, path):
    current = Path(root) / path
    if not current.is_file() or not current.name.startswith('test_') or current.suffix != '.py':
        return None
    checkpoint = state_path(root)
    before = json.loads(checkpoint.read_text()).get('test_sources', {}).get(path) if checkpoint.exists() else None
    def parts(text):
        tree = ast.parse(text)
        methods = {}
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                kept = []
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name.startswith('test_'):
                        methods[node.name + '.' + child.name] = ast.dump(child, include_attributes=False)
                    else:
                        kept.append(child)
                node.body = kept
        return methods, ast.dump(tree, include_attributes=False)
    after, context = parts(current.read_text())
    if not after:
        return None
    old, old_context = parts(before) if before is not None else ({}, None)
    selected = sorted(after) if context != old_context else sorted(name for name in after if after[name] != old.get(name))
    if not selected:
        return None
    return selected


def plan(root=ROOT, changed=None, full=False, authorization=None):
    root = Path(root).resolve()
    config = json.loads((root / 'config/test_impact.json').read_text())
    if config.get('schema_version') != 1 or not isinstance(config.get('tests'), dict):
        raise ValueError('Invalid test impact configuration.')
    paths = changed_files(root) if changed is None else sorted(set(changed))
    for name in paths:
        if not name or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Changed files must be repository-relative paths.')
    selected, skipped, unmapped = {}, {}, []
    if full:
        authorize_full(root, authorization)
        selected = {name: ['User confirmed this batch is finished.'] for name in config['final_checks']}
        config = {**config, 'tests': config['final_checks']}
    else:
        for path in paths:
            methods = changed_test_methods(root, path)
            if methods is not None:
                identifier = 'changed:' + path
                argv = ['{python}', '-m', 'unittest', 'discover', '-s', str(Path(path).parent), '-p', Path(path).name]
                for method in methods:
                    argv += ['-k', method]
                config['tests'][identifier] = {'argv': argv}
                selected[identifier] = [path]
                continue
            matched = False
            for rule in config.get('rules', []):
                if any(fnmatch.fnmatchcase(path, pattern) for pattern in rule['paths']):
                    matched = True
                    for name in rule.get('tests', []):
                        selected.setdefault(name, []).append(path)
                    if not rule.get('tests'):
                        skipped[path] = rule.get('reason', 'No executable behavior changed.')
            if not matched:
                unmapped.append(path)
    checks = []
    for name, reasons in selected.items():
        if name not in config['tests']:
            raise ValueError('Impact rule names an unknown test: ' + name)
        test = config['tests'][name]
        argv = test['argv']
        if not isinstance(argv, list) or not argv or argv[0] != '{python}' or any(not isinstance(value, str) for value in argv):
            raise ValueError('Tests need an explicit Python argv array.')
        if not full and broad_command(argv):
            raise ValueError('An impacted check contains unrestricted full discovery: ' + name)
        checks.append({'id': name, 'argv': [sys.executable if value == '{python}' else value for value in argv], 'because': sorted(set(reasons)), 'timeout_seconds': test.get('timeout_seconds', 180)})
    merged = {}
    for check in checks:
        argv = check['argv']
        if 'unittest' not in argv or 'discover' not in argv:
            merged[tuple(argv)] = check
            continue
        split = argv.index('-k') if '-k' in argv else len(argv)
        key = tuple(argv[:split])
        filters = argv[split + 1::2]
        if key not in merged:
            merged[key] = {**check, '_filters': filters, '_whole_module': not filters}
        else:
            saved = merged[key]
            saved['id'] += ' + ' + check['id']
            saved['because'] = sorted(set(saved['because'] + check['because']))
            saved['_whole_module'] = saved['_whole_module'] or not filters
            saved['_filters'] = sorted(set(saved['_filters'] + filters))
    checks = []
    for key, check in merged.items():
        if '_filters' in check:
            check['argv'] = list(key)
            if not check.pop('_whole_module'):
                for pattern in check['_filters']:
                    check['argv'] += ['-k', pattern]
            check.pop('_filters')
        checks.append(check)
    return {'mode': 'full' if full else 'impacted', 'root': str(root), 'changed_files': paths, 'artifact_sha256': digest(inventory(root)), 'checks': checks, 'skipped': skipped, 'unmapped': unmapped, 'executable': not unmapped}


def execute(selection):
    if not selection['executable']:
        raise ValueError('Unmapped changes require an impact rule; no full-suite fallback: ' + ', '.join(selection['unmapped']))
    results = []
    for check in selection['checks']:
        started = time.monotonic()
        try:
            process = subprocess.run(check['argv'], cwd=selection['root'], capture_output=True, text=True, timeout=check['timeout_seconds'])
            results.append({'id': check['id'], 'passed': process.returncode == 0, 'exit_code': process.returncode, 'stdout': process.stdout, 'stderr': process.stderr, 'elapsed_seconds': round(time.monotonic() - started, 3)})
        except subprocess.TimeoutExpired:
            results.append({'id': check['id'], 'passed': False, 'error': 'Test runtime exceeded its declared limit.'})
    current = inventory(selection['root'])
    passed = all(row['passed'] for row in results) and digest(current) == selection['artifact_sha256']
    if passed:
        try:
            pending = changed_files(selection['root'])
        except ValueError:
            pending = None
        if selection['mode'] == 'full' or pending is not None and set(pending) <= set(selection['changed_files']):
            checkpoint = state_path(selection['root'])
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            checkpoint.write_text(json.dumps({'schema_version': 1, 'root': selection['root'], 'files': current, 'mode': selection['mode'], 'tested_files': selection['changed_files'], 'passed': True, 'test_sources': {p.relative_to(Path(selection['root'])).as_posix(): p.read_text() for folder in ('tests', 'scripts') if (Path(selection['root']) / folder).exists() for p in (Path(selection['root']) / folder).glob('test_*.py')}}, indent=2))
    return {**selection, 'passed': passed, 'results': results, 'limits': 'Impact rules select related checks. This runner does not authorize a push.'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT)
    parser.add_argument('--changed', action='append', help='Exact changed path; otherwise compare the last tested checkpoint or Git HEAD.')
    parser.add_argument('--execute', action='store_true', help='Without this flag, print the selected checks without running them.')
    parser.add_argument('--full', action='store_true')
    parser.add_argument('--authorization', type=Path, help='User-approved final-testing record bound to artifact_sha256.')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        result = plan(args.package, args.changed, args.full, args.authorization)
        if args.execute:
            result = execute(result)
        text = json.dumps(result, indent=2)
        if args.report:
            target = args.report.resolve()
            if target.is_relative_to(args.package.resolve()):
                raise ValueError('Keep test reports outside the repository.')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text + '\n')
        print(text)
        return 0 if result.get('passed', result['executable']) else 1
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
