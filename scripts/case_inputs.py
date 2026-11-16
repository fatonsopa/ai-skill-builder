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
    destinations = list(source) + [row.get('destination', '') for row in manifest if isinstance(row, dict)]
    for name in destinations:
        fixture_name(name)
    if len(set(destinations)) != len(destinations) or any(a != b and b.startswith(a + '/') for a in destinations for b in destinations):
        raise ValueError('Duplicate or colliding fixture destination.')
    if any(not isinstance(value, str) for value in source.values()):
        raise ValueError('Inline sources must be UTF-8 text; declare binary files through the fixture manifest.')
    for row in manifest:
        if not isinstance(row, dict) or not {'path', 'destination', 'sha256'} <= set(row) or set(row) - {'path', 'destination', 'sha256', 'media_type'}:
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
        media = row.get('media_type', 'text/plain')
        verify_media(data, media)
        if media.startswith('image/'):
            source[name] = {'fixture_path': str(path), 'sha256': row['sha256'], 'media_type': media}
        else:
            source[name] = data.decode('utf-8')
    return request


def verify_media(data, media):
    if media == 'image/png':
        if len(data) < 33 or not data.startswith(b'\x89PNG\r\n\x1a\n') or data[12:16] != b'IHDR' or b'IEND' not in data[-12:]:
            raise ValueError('Invalid PNG fixture type/header.')
    elif media == 'image/jpeg':
        if len(data) < 4 or not data.startswith(b'\xff\xd8') or not data.endswith(b'\xff\xd9'):
            raise ValueError('Invalid JPEG fixture type/header.')
    elif media in {'text/plain', 'text/markdown', 'application/json', 'application/yaml', 'application/toml'}:
        data.decode('utf-8')
    else:
        raise ValueError('Unsupported fixture media_type: ' + str(media))


def stage_sources(root, source):
    root = Path(root).resolve()
    metadata = []
    names = list(source)
    if any(a != b and b.startswith(a + '/') for a in names for b in names):
        raise ValueError('Colliding fixture destinations.')
    for name, value in source.items():
        fixture_name(name)
        destination = root / name
        if not destination.resolve().is_relative_to(root) or destination.exists() or any(p.is_symlink() for p in [destination, *destination.parents] if p.is_relative_to(root)):
            raise ValueError('Fixture destination exists or escapes its staging root.')
        if isinstance(value, str):
            data, media = value.encode('utf-8'), 'text/plain'
        elif isinstance(value, dict) and set(value) == {'fixture_path', 'sha256', 'media_type'}:
            data = Path(value['fixture_path']).read_bytes()
            if hashlib.sha256(data).hexdigest() != value['sha256']:
                raise ValueError('Binary fixture changed before staging.')
            media = value['media_type']
            verify_media(data, media)
        else:
            raise ValueError('Invalid staged fixture descriptor.')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        metadata.append({'path': str(destination), 'media_type': media, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})
    return metadata
