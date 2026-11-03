"""Delegate document acceptance to the installed Technical Writer skill."""
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml

from .common import Invalid, digest, inventory, load, save

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_SUFFIXES = {'.md', '.markdown', '.mdown', '.rst', '.adoc', '.asciidoc', '.txt', '.html', '.htm', '.tex', '.svg', '.xml', '.pdf', '.docx', '.odt', '.mdx', '.text', '.qmd', '.rmd', '.rtf', '.doc', '.prompt', '.j2', '.jinja', '.jinja2', '.tmpl', '.template', '.ipynb'}
CODE_SUFFIXES = {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.sh', '.json', '.yaml', '.yml', '.csv', '.tsv', '.toml', '.lock'}


def capture(request):
    explicit = request.get('technical_writer') or os.environ.get('SKILL_BUILDER_TECHNICAL_WRITER')
    choices = [Path(explicit)] if explicit else [ROOT.parent / 'technical-writer', Path.home() / '.agents/skills/technical-writer', Path.home() / '.codex/skills/technical-writer', Path.home() / '.claude/skills/technical-writer']
    for choice in choices:
        root = choice.parent if choice.name == 'SKILL.md' else choice
        if (root / 'SKILL.md').is_file():
            root = root.resolve()
            parts = (root / 'SKILL.md').read_text().split('---\n', 2)
            metadata = yaml.safe_load(parts[1]) if len(parts) == 3 else None
            if not isinstance(metadata, dict) or metadata.get('name') != 'technical-writer':
                raise Invalid('The document dependency must be the technical-writer skill.')
            for name in ('scripts/validate_document.py', 'references/writing_style.md'):
                if not (root / name).is_file():
                    raise Invalid('Incomplete Technical Writer dependency: ' + name)
            return {'path': str(root), 'files': inventory(root)}
    return {'path': str(choices[0]), 'files': None, 'error': 'Install Technical Writer or set request.technical_writer / SKILL_BUILDER_TECHNICAL_WRITER. Document delivery is blocked.'}


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
    return {'path': str(root), 'guidance': {name: (root / name).read_text() for name in ('SKILL.md', 'references/writing_style.md')},
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


def validate_documents(root, manifest):
    from .workflow import read_state
    root = Path(root).resolve()
    state = read_state(root)
    if state['phase'] != 'review' or state['status'] != 'awaiting_ai':
        raise Invalid('Validate documents after candidate evaluation and before review.')
    dependency(state)
    files = inventory(root / 'candidate')
    if files != state['evaluation']['package_hashes']:
        raise Invalid('Candidate changed after evaluation; reevaluate it.')
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
        if session.is_relative_to(root / 'candidate') or review.is_relative_to(root / 'candidate'):
            raise Invalid('Keep Technical Writer validation evidence outside the candidate.')
        request = load(session / 'state.json')['frozen']['request']
        if request.get('scope') != 'complete':
            raise Invalid('Document acceptance requires validation of the complete output: ' + name)
        if not any(source.get('text') == source_text(state) for source in request['sources']):
            raise Invalid('Technical Writer session is not bound to this Skill Builder request and objective: ' + name)
        required_kind = 'skill' if Path(name).name == 'SKILL.md' else 'readme' if Path(name).name == 'README.md' else 'agent' if Path(name).name == 'AGENTS.md' else None
        if required_kind and (request['kind'] != required_kind or request['operation'] == 'review'):
            raise Invalid('Use the complete Technical Writer document contract for ' + name)
        destination = Path(request['destination']).resolve()
        if destination.is_relative_to(root / 'candidate') or state.get('source') and destination.is_relative_to(Path(state['source'])):
            raise Invalid('Technical Writer must finalize to a separate validation copy, preserving the candidate and source.')
        result = call(state, 'finalize', '--session', session, '--draft', root / 'candidate' / name, '--review', review)
        if result.get('status') != 'delivered' or result.get('output_sha256') != expected[name] or digest(destination.read_bytes()) != expected[name]:
            raise Invalid('Technical Writer did not accept these exact document bytes: ' + name)
        evidence.append({'path': name, 'session': str(session), 'review': str(review), 'files': {str(path): digest(path.read_bytes()) for path in (session / 'state.json', session / 'delivery.json', session / 'message.md', review)}, 'destination': str(destination)})
    if inventory(root / 'candidate') != files:
        raise Invalid('Candidate changed during document validation.')
    receipt = {'documents': expected, 'objective_sha256': state.get('objective_sha256'), 'evidence': evidence}
    record = root / 'document-validations' / (digest(receipt) + '.json')
    save(record, receipt)
    state['document_validation'] = {'record': str(record), 'sha256': digest(record.read_bytes())}
    attempt.update(status='accepted', validation=state['document_validation'])
    save(root / 'state.json', state)
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
