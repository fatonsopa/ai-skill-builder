"""Delegate document acceptance to the installed Technical Writer skill."""
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

from .common import Invalid, digest, inventory, load, save, inside, copy_package, source_reference

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_SUFFIXES = {'.md', '.markdown', '.mdown', '.rst', '.adoc', '.asciidoc', '.txt', '.html', '.htm', '.tex', '.svg', '.xml', '.pdf', '.docx', '.odt', '.mdx', '.text', '.qmd', '.rmd', '.rtf', '.doc', '.prompt', '.j2', '.jinja', '.jinja2', '.tmpl', '.template', '.ipynb'}
CODE_SUFFIXES = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.sh', '.json', '.yaml', '.yml', '.csv', '.tsv', '.toml', '.lock'}


# The canonical identity first, then the legacy name kept through the writer rename.
IDENTITIES = ('specdev', 'technical-writer')


def capture(request):
    explicit = request.get('technical_writer') or os.environ.get('SKILL_BUILDER_TECHNICAL_WRITER')
    choices = [Path(explicit)] if explicit else [folder / name for name in IDENTITIES for folder in (ROOT.parent, Path.home() / '.agents/skills', Path.home() / '.codex/skills', Path.home() / '.claude/skills')]
    for choice in choices:
        root = choice.parent if choice.name == 'SKILL.md' else choice
        if (root / 'SKILL.md').is_file():
            root = root.resolve()
            parts = (root / 'SKILL.md').read_text().split('---\n', 2)
            metadata = yaml.safe_load(parts[1]) if len(parts) == 3 else None
            name = metadata.get('name') if isinstance(metadata, dict) else None
            if name not in IDENTITIES:
                raise Invalid('The document dependency must be the specdev skill or its legacy technical-writer identity; found ' + repr(name) + ' at ' + str(root) + '.')
            for required in ('scripts/validate_document.py', 'references/writing_style.md'):
                if not (root / required).is_file():
                    raise Invalid('Incomplete ' + name + ' dependency at ' + str(root) + ': ' + required)
            return {'path': str(root), 'name': name, 'files': inventory(root)}
    return {'path': str(choices[0]), 'files': None, 'error': 'Install SpecDev (specdev) or the legacy technical-writer skill, or set request.technical_writer / SKILL_BUILDER_TECHNICAL_WRITER. Document delivery is blocked.'}


def dependency(state):
    value = state.get('technical_writer')
    if not value or not value.get('files'):
        raise Invalid('Technical Writer is unavailable; start a new run with the required skill installed.')
    if inventory(value['path']) != value['files']:
        raise Invalid('Technical Writer changed after capture; start a new run.')
    return Path(value['path'])


def guidance(state):
    if not state['technical_writer'].get('files'):
        return state['technical_writer']
    root = dependency(state)
    return {'path': str(root), 'guidance': {name: source_reference(root / name) if state.get('protocol_version', 1) >= 5 else (root / name).read_text() for name in ('SKILL.md', 'references/writing_style.md')},
            'validation': 'Use this skill and its applicable references for every document. Supply accepted validate_document.py sessions with validate-documents before delivery. Writing rules belong to Technical Writer.'}


def documents(state, files):
    baseline = state['source_snapshot'] if state['request']['operation'] in {'modify', 'refactor'} else {}
    declared = set(state['request'].get('document_paths', []))
    result = {}
    for name, sha in files.items():
        if baseline.get(name) == sha:
            continue
        path = Path(name)
        is_document = path.suffix.lower() in DOCUMENT_SUFFIXES
        is_document |= name == 'config/documentation.json' or name.startswith('agents/') and path.suffix.lower() in {'.yaml', '.yml'}
        is_document |= path.parts[0] not in {'scripts', 'tests', 'evals', 'config', 'assets'} and path.suffix.lower() not in CODE_SUFFIXES and path.name != 'LICENSE' and not path.name.startswith('.')
        is_document |= path.parts[0] in {'docs', 'references', 'examples', 'templates', 'assets'} and path.suffix.lower() not in {'.py', '.js', '.mjs', '.ts', '.sh', '.png', '.jpg', '.jpeg', '.webp', '.gif', '.ico', '.woff', '.woff2', '.ttf'}
        is_document |= path.name in {'LICENSE', 'NOTICE', 'README', 'CHANGELOG', 'CONTRIBUTING'}
        is_document |= name in declared
        if is_document:
            result[name] = sha
    return result


def source_text(state):
    return json.dumps({'request': state['request'], 'specification': state['data'].get('specify'), 'plan': state['data'].get('plan')}, ensure_ascii=False, sort_keys=True)


def call(state, *args):
    root = dependency(state)
    try:
        process = subprocess.run([sys.executable, str(root / 'scripts/validate_document.py'), *map(str, args)], cwd=root, capture_output=True, text=True, timeout=120)
        if process.returncode:
            raise Invalid('Technical Writer validation failed: ' + (process.stderr or process.stdout).strip())
        value = json.loads(process.stdout)
        if not isinstance(value, dict) or 'error' in value:
            raise ValueError('Expected a successful validator result.')
        return value
    except (OSError, subprocess.TimeoutExpired, ValueError) as error:
        raise Invalid('Technical Writer could not validate the document: ' + str(error)) from error


def validate_documents(root, manifest, document_root=None):
    from .workflow import read_state
    root = Path(root).resolve()
    state = read_state(root)
    planning = state['request']['operation'] in {'plan', 'specify'}
    if planning:
        if state['phase'] != 'complete' or not state['request'].get('document_paths'):
            raise Invalid('Complete the planning phases and declare actual document_paths first.')
        package = root / 'documents'
        if document_root is not None:
            if package.exists():
                raise Invalid('Planning document snapshot already exists; preserve it and start a versioned run for changed content.')
            copy_package(document_root, package)
        if not package.is_dir():
            raise Invalid('Supply --document-root with the authored planning files.')
        files = inventory(package)
        if set(files) != set(state['request']['document_paths']):
            raise Invalid('Planning documents must match declared document_paths exactly.')
    else:
        if state['phase'] != 'review' or state['status'] != 'awaiting_ai':
            raise Invalid('Validate documents after candidate evaluation and before review.')
        if document_root is not None:
            raise Invalid('Evaluated candidates use their captured document root.')
        package = root / 'candidate'
        files = inventory(package)
        if files != state['evaluation']['package_hashes']:
            raise Invalid('Candidate changed after evaluation; reevaluate it.')
    dependency(state)
    expected = documents(state, files)
    rows = load(manifest)
    attempt = {'manifest_sha256': digest(Path(manifest).read_bytes()), 'status': 'not_accepted', 'previous_validation': state.pop('document_validation', None)}
    state.setdefault('document_validation_attempts', []).append(attempt)
    save(root / 'state.json', state)
    if not isinstance(rows, list) or any(not isinstance(row, dict) or set(row) != {'path', 'session', 'review'} for row in rows):
        raise Invalid('Document manifest needs path, session and accepted review for every document.')
    if len(rows) != len(expected) or {row['path'] for row in rows} != set(expected):
        raise Invalid('Technical Writer validation must cover every created or changed document exactly once: ' + repr(sorted(expected)))
    evidence = []
    for row in rows:
        name = row['path']
        session, review = Path(row['session']).resolve(), Path(row['review']).resolve()
        if session.is_relative_to(package) or review.is_relative_to(package):
            raise Invalid('Keep Technical Writer validation evidence outside the candidate.')
        request = load(session / 'state.json')['frozen']['request']
        if request.get('scope') != 'complete':
            raise Invalid('Document acceptance requires validation of the complete output: ' + name)
        if not any(source.get('text') == source_text(state) for source in request['sources']):
            raise Invalid('Technical Writer session is not bound to this Skill Builder request and objective: ' + name)
        required_kind = 'skill' if Path(name).name == 'SKILL.md' else 'readme' if Path(name).name == 'README.md' else 'agent' if Path(name).name == 'AGENTS.md' else None
        role_hosts = [asset['host'] for role in state['data'].get('plan', {}).get('execution', {}).get('roles', []) for asset in role['assets'] if asset['path'] == name]
        expected_format = 'project' if Path(name).name == 'AGENTS.md' else 'codex-toml' if 'codex' in role_hosts else 'subagent' if 'claude-code' in role_hosts else None
        if role_hosts:
            required_kind = 'agent'
        if expected_format and request.get('context', {}).get('instruction_format') != expected_format:
            raise Invalid('Select the actual instruction format ' + expected_format + ' for ' + name)
        if required_kind and (request['kind'] != required_kind or request['operation'] == 'review'):
            raise Invalid('Use the complete Technical Writer document contract for ' + name)
        destination = Path(request['destination']).resolve()
        if destination.is_relative_to(package) or state.get('source') and destination.is_relative_to(Path(state['source'])):
            raise Invalid('Technical Writer must finalize to a separate validation copy, preserving the candidate and source.')
        result = call(state, 'finalize', '--session', session, '--draft', package / name, '--review', review)
        if result.get('status') != 'delivered' or result.get('output_sha256') != expected[name] or digest(destination.read_bytes()) != expected[name]:
            raise Invalid('Technical Writer did not accept these exact document bytes: ' + name)
        evidence.append({'path': name, 'session': str(session), 'review': str(review), 'files': {str(path): digest(path.read_bytes()) for path in (session / 'state.json', session / 'delivery.json', session / 'message.md', review)}, 'destination': str(destination)})
    if inventory(package) != files:
        raise Invalid('Candidate changed during document validation.')
    receipt = {'documents': expected, 'objective_sha256': state.get('objective_sha256'), 'evidence': evidence}
    record = root / 'document-validations' / (digest(receipt) + '.json')
    save(record, receipt)
    state['document_validation'] = {'record': str(record), 'sha256': digest(record.read_bytes())}
    attempt.update(status='accepted', validation=state['document_validation'])
    if planning:
        state['document_artifact'] = {'root': str(package), 'files': files}
        state['document_check'] = gate(root, state, files)
        if not state['document_check']['passed']:
            raise Invalid('Planning document acceptance failed.')
    save(root / 'state.json', state)
    if planning:
        from . import completion
        completion.sync_native(root, state)
    return {'passed': True, 'documents': sorted(expected), 'record': str(record)}


def gate(root, state, files):
    try:
        dependency(state)
        expected = documents(state, files)
        if not expected:
            return {'passed': True, 'documents': {}, 'findings': []}
        binding = state.get('document_validation', {})
        record = Path(binding.get('record', ''))
        if not record.is_file() or digest(record.read_bytes()) != binding.get('sha256'):
            raise Invalid('Required Technical Writer validation is missing or changed.')
        receipt = load(record)
        if receipt['documents'] != expected or receipt['objective_sha256'] != state.get('objective_sha256'):
            raise Invalid('Technical Writer validation is stale for this candidate or objective.')
        if state.get('replay_only'):
            return {'passed': True, 'documents': expected, 'findings': [], 'mode': 'historical_replay'}
        if len(receipt['evidence']) != len(expected) or {row['path'] for row in receipt['evidence']} != set(expected):
            raise Invalid('Technical Writer evidence is incomplete.')
        for row in receipt['evidence']:
            for name, sha in row['files'].items():
                if digest(Path(name).read_bytes()) != sha:
                    raise Invalid('Technical Writer validation evidence changed: ' + name)
            if digest(Path(row['destination']).read_bytes()) != expected[row['path']]:
                raise Invalid('Technical Writer accepted copy changed: ' + row['path'])
            result = call(state, 'verify-message', '--session', row['session'], '--message', Path(row['session']) / 'message.md')
            if result.get('passed') is not True:
                raise Invalid('Technical Writer validation no longer passes: ' + row['path'])
        return {'passed': True, 'documents': expected, 'findings': []}
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {'passed': False, 'findings': [str(error)]}
