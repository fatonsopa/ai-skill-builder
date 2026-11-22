"""Release installer and host-setup controls in disposable homes; no network or model calls."""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import release_cli


class HostSetupTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.home = self.root / 'home'
        self.payload = self.payload_version('0.1.0', 'rev-a')
        for patcher in (patch.object(Path, 'home', return_value=self.home), patch.dict(os.environ, {'SKILL_BUILDER_HOME': str(self.root / 'state')}),
                        patch.object(release_cli, 'PAYLOAD', self.payload)):
            patcher.start(); self.addCleanup(patcher.stop)

    def payload_version(self, version, revision):
        payload = self.root / ('payload-' + version)
        (payload / 'config').mkdir(parents=True)
        (payload / 'SKILL.md').write_text('---\nname: skill-builder\ndescription: Fixture payload.\n---\nVersion ' + version + '.\n')
        (payload / 'config/release.json').write_text(json.dumps({'version': version, 'revision': revision}))
        (payload / '.venv/bin').mkdir(parents=True)
        return payload

    def test_init_is_idempotent_and_refuses_an_installation_it_does_not_own(self):
        codex = self.home / '.agents/skills/skill-builder'
        self.assertEqual(release_cli.init(['codex'])[0]['status'], 'installed')
        self.assertEqual(release_cli.init(['codex'])[0]['status'], 'unchanged')
        self.assertEqual(list(release_cli.read_manifest()['hosts']), ['codex'])
        self.assertTrue((codex / '.venv').is_symlink())
        foreign = self.home / '.claude/skills/skill-builder'
        foreign.mkdir(parents=True)
        (foreign / 'SKILL.md').write_text('A source installation with local edits.\n')
        with self.assertRaisesRegex(release_cli.Conflict, 'not installed by skill-builder'):
            release_cli.init(['claude'])
        self.assertEqual((foreign / 'SKILL.md').read_text(), 'A source installation with local edits.\n')

    def test_update_keeps_edits_on_conflict_carries_foreign_files_and_removal_keeps_unowned_content(self):
        release_cli.init(['codex', 'claude'])
        codex = self.home / '.agents/skills/skill-builder'
        (codex / 'notes.md').write_text('A user file beside the skill.\n')
        (codex / 'SKILL.md').write_text('A local edit.\n')
        with patch.object(release_cli, 'PAYLOAD', self.payload_version('0.2.0', 'rev-b')):
            with self.assertRaisesRegex(release_cli.Conflict, 'Local edits.*SKILL.md.*0.1.0 was left unchanged'):
                release_cli.update(['codex'])
            self.assertEqual((codex / 'SKILL.md').read_text(), 'A local edit.\n')
            self.assertEqual(release_cli.read_manifest()['hosts']['codex']['version'], '0.1.0')
            (codex / 'SKILL.md').write_text((self.payload / 'SKILL.md').read_text())
            result = release_cli.update(['codex'])[0]
        self.assertEqual((result['status'], result['previous_version'], result['version'], result['kept_foreign_files']), ('updated', '0.1.0', '0.2.0', ['notes.md']))
        self.assertIn('Version 0.2.0', (codex / 'SKILL.md').read_text())
        self.assertEqual((codex / 'notes.md').read_text(), 'A user file beside the skill.\n')
        (codex / 'SKILL.md').write_text('Edited again.\n')
        removed = release_cli.remove(['codex'])[0]
        self.assertEqual(removed['kept'], ['SKILL.md', 'notes.md'])
        self.assertEqual(sorted(p.name for p in codex.iterdir()), ['SKILL.md', 'notes.md'])
        self.assertTrue((self.home / '.claude/skills/skill-builder/SKILL.md').is_file())
        self.assertEqual(list(release_cli.read_manifest()['hosts']), ['claude'])


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.assets = self.root / 'assets'
        self.assets.mkdir()
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
            data = json.dumps({'version': '0.1.0'}).encode()
            info = tarfile.TarInfo('config/release.json'); info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        tarball = self.assets / 'skill-builder-0.1.0.tar.gz'
        tarball.write_bytes(buffer.getvalue())
        (self.assets / 'SHA256SUMS').write_text(hashlib.sha256(b'different bytes').hexdigest() + '  ' + tarball.name + '\n')
        self.home = self.root / 'home'
        self.home.mkdir()

    def install(self, path):
        environment = {'HOME': str(self.home), 'PATH': path, 'SKILL_BUILDER_RELEASE_BASE': 'file://' + str(self.assets)}
        return subprocess.run(['/bin/sh', str(ROOT / 'tools/release/install.sh')], env=environment, capture_output=True, text=True)

    def test_checksum_mismatch_stops_before_any_change(self):
        result = self.install(str(Path(sys.executable).parent) + ':/usr/bin:/bin')
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertIn('checksum mismatch for skill-builder-0.1.0.tar.gz', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_python_names_the_prerequisite(self):
        fake = self.root / 'fake-bin'
        fake.mkdir()
        for name in ('python3.14', 'python3.13', 'python3.12', 'python3.11', 'python3'):
            (fake / name).write_text('#!/bin/sh\nexit 1\n')
            (fake / name).chmod(stat.S_IRWXU)
        result = self.install(str(fake) + ':/usr/bin:/bin')
        self.assertEqual(result.returncode, 1)
        self.assertIn('Python 3.11 or later is required', result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])
