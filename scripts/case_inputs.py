"""Resolve declared task fixtures before model execution; never load grading files."""
import copy
import hashlib
from pathlib import Path, PurePosixPath


def fixture_name(name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ValueError('Invalid fixture destination.')
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or str(path) != name or name == '.':
        raise ValueError('Fixture destination must be a normalized relative path.')
    return name


def prepare_inputs(package, case):
    package = Path(package).resolve()
    for name in case.get('resources', []):
        fixture_name(name)
        path = (package / name).resolve()
        if not path.is_relative_to(package) or not path.is_file():
            raise ValueError('Task resource is missing or outside the package: ' + name)
        rel = path.relative_to(package)
        if rel.parts[0] in {'evals', 'tests', 'tools'} or rel.suffix == '.py' and (rel.name.startswith('test_') or rel.name.endswith('.test.py')):
            raise ValueError('Task resources cannot expose grading or development controls.')
    request = copy.deepcopy(case['request'])
    manifest = case.get('fixtures', [])
    if not isinstance(manifest, list):
        raise ValueError('Fixture manifest must be an array.')
    if not manifest:
        return request
    if not isinstance(request, dict):
        raise ValueError('Fixture tasks need an object request.')
    source = request.setdefault('source', {})
    if not isinstance(source, dict):
        raise ValueError('Fixture tasks need a source file mapping.')
    package = Path(package).resolve()
    for row in manifest:
        if not isinstance(row, dict) or set(row) != {'path', 'destination', 'sha256'}:
            raise ValueError('Fixture entries need path, destination and sha256.')
        name = fixture_name(row['destination'])
        rel = fixture_name(row['path'])
        # A separate raw-fixture namespace keeps runtime guidance and grading
        # resources out of the file import route; inspect fixture contents too.
        if not rel.startswith('evals/fixtures/'):
            raise ValueError('Only raw evals/fixtures files may be imported as task inputs.')
        path = (package / rel).resolve()
        if not path.is_relative_to(package / 'evals/fixtures') or not path.is_file():
            raise ValueError('Task fixture is missing or escapes its raw-input directory.')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Task fixture changed; freeze a new case version.')
        if name in source:
            raise ValueError('Duplicate fixture destination.')
        source[name] = data.decode('utf-8')
    return request
