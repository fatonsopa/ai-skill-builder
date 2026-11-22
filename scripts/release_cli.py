#!/usr/bin/env python3
"""Installed `skill-builder` command: report the release and connect hosts to the same skill.

The GitHub installer and the npm package both run this file from their versioned
payload. Host setup copies that payload into each selected host's user skill
folder and records what it wrote, so updates and removal touch only owned files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from repository_files import inventory, skill_name

PAYLOAD = Path(__file__).resolve().parents[1]
HOSTS = {'codex': '.agents/skills', 'claude': '.claude/skills'}
INVOCATION = {'codex': '$skill-builder', 'claude': '/skill-builder'}


class Conflict(Exception):
    """A path the installer does not own, or a managed file with local edits."""


def release():
    value = json.loads((PAYLOAD / 'config/release.json').read_text())
    return {'name': skill_name(PAYLOAD), 'version': value['version'], 'revision': value.get('revision')}


def state_root():
    return Path(os.environ.get('SKILL_BUILDER_HOME') or Path.home() / '.local/share/skill-builder')


def manifest_path():
    return state_root() / 'hosts.json'


def read_manifest():
    path = manifest_path()
    return json.loads(path.read_text()) if path.is_file() else {'schema_version': 1, 'hosts': {}}


def write_manifest(value):
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def destination(host):
    return Path.home() / HOSTS[host] / release()['name']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_changes(entry):
    """Managed files that differ from what setup wrote, and files setup never wrote."""
    target = Path(entry['destination'])
    actual = inventory(target) if target.is_dir() and not target.is_symlink() else {}
    edited = sorted(name for name, digest in entry['files'].items() if actual.get(name) != digest)
    foreign = sorted(set(actual) - set(entry['files']))
    return edited, foreign


def stage(target, carry=()):
    """Copy the payload beside the target, carrying foreign files and linking the payload environment."""
    staging = target.with_name('.' + target.name + '.staging')
    if staging.exists():
        shutil.rmtree(staging)
    files = dict(inventory(PAYLOAD))
    staging.mkdir(parents=True)
    for name in files:
        (staging / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAYLOAD / name, staging / name)
    for name in carry:
        (staging / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target / name, staging / name)
    environment = PAYLOAD / '.venv'
    if environment.is_dir():
        (staging / '.venv').symlink_to(environment, target_is_directory=True)
    return staging, files


def swap(staging, target):
    backup = target.with_name('.' + target.name + '.previous')
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        os.replace(target, backup)
    try:
        os.replace(staging, target)
    except OSError:
        if backup.exists():
            os.replace(backup, target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def init(hosts):
    manifest, results = read_manifest(), []
    for host in hosts:
        target = destination(host)
        entry = manifest['hosts'].get(host)
        if entry is None and (target.exists() or target.is_symlink()):
            raise Conflict(f'{target} already exists and was not installed by skill-builder. Move it or remove it yourself, then repeat setup.')
        if entry and entry['version'] == release()['version'] and entry['revision'] == release()['revision'] and not local_changes(entry)[0]:
            results.append({'host': host, 'status': 'unchanged', 'destination': str(target), 'invoke': INVOCATION[host]})
            continue
        results.append(refresh(manifest, host, target) if entry else create(manifest, host, target))
    return results


def create(manifest, host, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    staging, files = stage(target)
    swap(staging, target)
    manifest['hosts'][host] = {'destination': str(target), **release(), 'files': files}
    write_manifest(manifest)
    return {'host': host, 'status': 'installed', 'destination': str(target), **release(), 'invoke': INVOCATION[host] + ' in a new session'}


def refresh(manifest, host, target):
    entry = manifest['hosts'][host]
    edited, foreign = local_changes(entry)
    if edited:
        raise Conflict(f'Local edits in {target}: {", ".join(edited)}. The installed version {entry["version"]} was left unchanged; keep or move those edits, then repeat the update.')
    staging, files = stage(target, carry=foreign)
    swap(staging, target)
    manifest['hosts'][host] = {'destination': str(target), **release(), 'files': files}
    write_manifest(manifest)
    return {'host': host, 'status': 'updated', 'previous_version': entry['version'], 'destination': str(target), **release(), 'kept_foreign_files': foreign, 'invoke': INVOCATION[host] + ' in a new session'}


def update(hosts):
    manifest = read_manifest()
    selected = hosts or sorted(manifest['hosts'])
    return [refresh(manifest, host, Path(manifest['hosts'][host]['destination'])) for host in selected if host in manifest['hosts']]


def remove(hosts):
    manifest, results = read_manifest(), []
    for host in hosts or sorted(manifest['hosts']):
        entry = manifest['hosts'].get(host)
        if entry is None:
            continue
        target = Path(entry['destination'])
        edited, foreign = local_changes(entry)
        for name, digest in entry['files'].items():
            path = target / name
            if name not in edited and path.is_file() and sha(path) == digest:
                path.unlink()
        link = target / '.venv'
        if link.is_symlink():
            link.unlink()
        for folder in sorted((p for p in target.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(folder.iterdir()):
                folder.rmdir()
        if target.is_dir() and not any(target.iterdir()):
            target.rmdir()
        del manifest['hosts'][host]
        write_manifest(manifest)
        results.append({'host': host, 'status': 'removed', 'destination': str(target), 'kept': sorted(set(edited) | set(foreign))})
    if not manifest['hosts'] and manifest_path().is_file():
        manifest_path().unlink()
        if not any(state_root().iterdir()):
            state_root().rmdir()
    return results


def tools(value):
    names = [name.strip() for name in value.split(',') if name.strip()]
    if not names or set(names) - set(HOSTS):
        raise argparse.ArgumentTypeError('Choose from: ' + ', '.join(HOSTS))
    return names


def main(argv=None):
    parser = argparse.ArgumentParser(prog='skill-builder', description=__doc__.splitlines()[0])
    parser.add_argument('--version', action='store_true', help='Print the installed release, revision and executable paths.')
    commands = parser.add_subparsers(dest='command')
    host = commands.add_parser('host', help='Connect Codex or Claude Code to this release.')
    actions = host.add_subparsers(dest='action', required=True)
    actions.add_parser('init').add_argument('--tools', type=tools, required=True, help='Comma-separated hosts: codex, claude.')
    for name in ('update', 'remove'):
        actions.add_parser(name).add_argument('--tools', type=tools, help='Hosts to change; defaults to every connected host.')
    args = parser.parse_args(argv)
    try:
        if args.version:
            result = {**release(), 'executable': os.environ.get('SKILL_BUILDER_LAUNCHER', shutil.which('skill-builder')), 'payload': str(PAYLOAD), 'python': sys.executable}
        elif args.command == 'host':
            result = {'init': init, 'update': update, 'remove': remove}[args.action](args.tools)
        else:
            parser.print_help()
            return 0
    except Conflict as error:
        print(json.dumps({'error': str(error), 'kind': 'conflict'}), file=sys.stderr)
        return 3
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps({'error': str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
