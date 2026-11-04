"""Real CLI output-size and data-preservation regressions."""
import json
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from runtime import workflow
from fixtures import payload, writer_fixture, validate_fixture_documents


class CliOutputTests(unittest.TestCase):
    def setUp(self):
        writer_fixture(self)

    def produce_control(self, run):
        workflow.start(run, {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'Normalize JSON.', 'copyright_holder': 'Fixture Author'}, protocol_version=1)
        for phase in ('research', 'specify', 'plan', 'produce'):
            packet = workflow.packet(run)
            workflow.submit(run, {key: packet[key] for key in ('run_id', 'phase', 'packet_sha256')} | {'data': payload(phase)})

    def review_control(self, run, accepted):
        validate_fixture_documents(run)
        packet = workflow.packet(run)
        state = workflow.read_state(run)
        data = {'reviewer': {'kind': 'human', 'identity': 'fixture', 'method': 'Authored protocol control, not model performance.'},
                'cases': [{'id': row['id'], 'accepted': accepted, 'rationale': 'Authored protocol control.'} for row in state['evaluation']['attempts'] if row['semantic']],
                'resource_findings': [{'path': name, 'accepted': accepted, 'evidence': 'Authored coverage control.'} for name in packet['candidate_resources']]}
        workflow.submit(run, {key: packet[key] for key in ('run_id', 'phase', 'packet_sha256')} | {'data': data})
        return packet

    def test_phase_guides_do_not_copy_the_complete_authoring_reference(self):
        authoring = (ROOT / 'references/authoring.md').read_text().strip()
        for name in ('maintenance.md', 'evaluation.md'):
            with self.subTest(reference=name):
                self.assertNotIn(authoring, (ROOT / 'references' / name).read_text())

    def test_repeated_evaluations_preserve_reports_and_their_review_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            run = Path(folder) / 'run'
            self.produce_control(run)
            build_record = json.loads((run / 'candidate/config/build_record.json').read_text())
            self.assertEqual(list(build_record['managed_hashes']), sorted(build_record['managed_hashes']))
            workflow.run_evaluation(run, allow_exec=False)
            first = {p.name: p.read_bytes() for p in (run / 'evaluations').glob('*.json')}
            self.assertEqual(len(first), 1)
            self.review_control(run, False)
            workflow.run_evaluation(run, allow_exec=True)
            reports = {p.name: p.read_bytes() for p in (run / 'evaluations').glob('*.json')}
            self.assertEqual(len(reports), 2)
            self.assertTrue(all(reports[name] == content for name, content in first.items()))
            packet = self.review_control(run, True)
            self.assertEqual(workflow.read_state(run)['status'], 'ready')
            cli = [sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'replay', '--run', str(run)]
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['rebuilt_status'], 'ready')
            archive = run / 'packets' / (packet['packet_sha256'] + '.json')
            corrupted = json.loads(archive.read_text())
            corrupted['evaluation']['metrics']['accepted'] += 1
            archive.write_text(json.dumps(corrupted))
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Archived review packet changed', result.stderr)
            archive.unlink()
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Archived review packet is missing', result.stderr)

    def test_installation_check_distinguishes_copies_links_drift_and_missing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, active = root / 'source', root / 'active'
            source.mkdir()
            (source / 'SKILL.md').write_text('---\nname: installation-control\ndescription: Installation control.\n---\nReviewed source.\n')
            shutil.copytree(source, active)
            cli = [sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'check-installation', '--package', str(source), '--installed', str(active)]
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(json.loads(result.stdout)['linked'])
            (active / 'SKILL.md').write_text('Older installed instructions.')
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['changed'], ['SKILL.md'])
            shutil.rmtree(active)
            active.symlink_to(source, target_is_directory=True)
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)['linked'])
            self.assertEqual(json.loads(result.stdout)['resolved_path'], str(source.resolve()))
            active.unlink()
            result = subprocess.run(cli, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)['missing'], ['SKILL.md'])

    def test_review_packet_supplies_every_required_resource_including_missing_files(self):
        for missing in (False, True):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as folder:
                run = Path(folder) / 'run'
                self.produce_control(run)
                if missing:
                    (run / 'candidate/AGENTS.md').unlink()
                workflow.run_evaluation(run, allow_exec=False)
                packet = workflow.packet(run)
                state = workflow.read_state(run)
                status = subprocess.run([sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'status', '--run', str(run)], capture_output=True, text=True, check=True)
                summary = json.loads(status.stdout)
                for name in ('mechanical_metrics', 'behavioral_metrics', 'process_metrics'):
                    self.assertEqual(summary[name], state['evaluation'][name])
                self.assertLess(len(status.stdout), 4096)
                expected = workflow.review_resource_names(state)
                self.assertEqual(set(packet['candidate_resources']), expected)
                if missing:
                    self.assertTrue(packet['candidate_resources']['AGENTS.md']['missing'])
                else:
                    self.assertIn('text', packet['candidate_resources']['AGENTS.md'])
                review = {'reviewer': {'kind': 'human', 'identity': 'fixture', 'method': 'Authored coverage control; no model observation.'},
                          'cases': [{'id': row['id'], 'accepted': False, 'rationale': 'No execution or actual model behavior in this control.'} for row in state['evaluation']['attempts'] if row['semantic']],
                          'resource_findings': [{'path': name, 'accepted': False, 'evidence': 'Authored review coverage control.'} for name in packet['candidate_resources']]}
                workflow.merge_review(run, state, review)
                self.assertFalse(state['resource_review_passed'])

    def test_lifecycle_summaries_preserve_state_without_dumping_captured_content(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            run = root / 'run'
            request = root / 'request.json'
            secret = 'A long user brief retained in state. ' * 5000
            from runtime.completion import create
            policy = create(root, {'objective_id': 'authored-cli-control', 'goal': 'Verify existing CLI behavior with the current contract.',
                'project': str(root / 'summary-project'), 'scope': ['**'],
                'checks': [{'id': 'report', 'kind': 'report', 'dependencies': []}],
                'budget': {'runs': 1, 'revisions': 0, 'model_calls': 0, 'seconds': 600},
                'delivery': {'kind': 'report', 'authority': 'Authored unit control only.'}})['policy']
            request.write_text(json.dumps({'completion_policy': policy, 'operation': 'specify', 'skill_name': 'summary-control', 'brief': secret}))
            cli = [sys.executable, str(ROOT / 'scripts/skill_builder_cli.py')]
            result = subprocess.run(cli + ['start', '--request', str(request), '--run', str(run)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(len(result.stdout), 4096)
            summary = json.loads(result.stdout)
            self.assertEqual(summary['phase'], 'research')
            self.assertEqual(summary['status'], 'awaiting_ai')
            self.assertNotIn('request', summary)
            self.assertEqual(json.loads((run / 'state.json').read_text())['request']['brief'], secret)
            packet_result = subprocess.run(cli + ['packet', '--run', str(run)], capture_output=True, text=True, check=True)
            packet = json.loads(packet_result.stdout)
            self.assertEqual(packet['request']['brief'], secret)
            response = root / 'response.json'
            response.write_text(json.dumps({'run_id': packet['run_id'], 'phase': 'research', 'packet_sha256': packet['packet_sha256'], 'data': {'sources': [], 'findings': secret, 'gaps': []}}))
            result = subprocess.run(cli + ['submit', '--run', str(run), '--response', str(response)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertLess(len(result.stdout), 4096)
            self.assertEqual(json.loads(result.stdout)['phase'], 'specify')
            state = json.loads((run / 'state.json').read_text())
            self.assertEqual(state['data']['research']['findings'], secret)
            status = subprocess.run(cli + ['status', '--run', str(run)], capture_output=True, text=True, check=True)
            self.assertLess(len(status.stdout), 4096)
            self.assertEqual(json.loads(status.stdout)['run_id'], state['run_id'])
