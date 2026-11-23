#!/usr/bin/env python3
"""Build Skill Builder release assets from one committed revision.

Writes the payload tarball, install.sh, the npm package tarball and SHA256SUMS
to a new folder outside the repository. Both channels carry the same payload.
Publishing those assets is a separate release-owner action.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def payload(revision, version=None):
    """Committed files at the revision, plus the revision recorded in config/release.json."""
    archive = subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', revision], check=True, capture_output=True).stdout
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', revision + '^{commit}'], check=True, capture_output=True, text=True).stdout.strip()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        for member in source.getmembers():
            if member.isfile():
                files[member.name] = (source.extractfile(member).read(), member.mode)
    release = json.loads(files['config/release.json'][0])
    release['revision'] = commit
    if version:
        release['version'] = version
    files['config/release.json'] = ((json.dumps(release, indent=2) + '\n').encode(), 0o644)
    return release, files


def write_tarball(path, files):
    """A reproducible gzip tarball: sorted names, fixed times and owners."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for name in sorted(files):
            data, mode = files[name]
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), mode & 0o755 or 0o644, 0
            archive.addfile(info, io.BytesIO(data))
    with open(path, 'wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as stream:
        stream.write(buffer.getvalue())


def npm_package(output, release, files):
    """Pack the same payload as an npm package; the launcher builds its Python environment on first run."""
    folder = output / 'npm-package'
    for name, (data, mode) in files.items():
        target = folder / 'payload' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(mode & 0o755 or 0o644)
    manifest = json.loads((ROOT / 'tools/release/npm/package.json').read_text())
    manifest['version'] = release['version']
    (folder / 'package.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (folder / 'bin').mkdir()
    shutil.copy2(ROOT / 'tools/release/npm/bin/skill-builder.js', folder / 'bin/skill-builder.js')
    shutil.copy2(ROOT / 'LICENSE', folder / 'LICENSE')
    packed = subprocess.run(['npm', 'pack', '--json', '--pack-destination', str(output)], cwd=folder, check=True, capture_output=True, text=True)
    shutil.rmtree(folder)
    return json.loads(packed.stdout)[0]['filename']


def build(revision, output, version=None):
    output = Path(output).resolve()
    if output.exists() or output.is_relative_to(ROOT):
        raise ValueError('Choose a new output folder outside the repository.')
    release, files = payload(revision, version)
    output.mkdir(parents=True)
    tarball = output / f"skill-builder-{release['version']}.tar.gz"
    write_tarball(tarball, files)
    shutil.copy2(ROOT / 'tools/release/install.sh', output / 'install.sh')
    assets = [tarball.name, 'install.sh', npm_package(output, release, files)]
    (output / 'SHA256SUMS').write_text(''.join(f'{sha(output / name)}  {name}\n' for name in assets))
    return {'version': release['version'], 'revision': release['revision'], 'output': str(output),
            'assets': {name: sha(output / name) for name in assets}}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--revision', default='HEAD', help='Committed revision to package.')
    parser.add_argument('--output', type=Path, required=True, help='New folder outside the repository.')
    parser.add_argument('--version', help='Label a staged candidate with a different version, for example to test an upgrade.')
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.revision, args.output, args.version), indent=2))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
