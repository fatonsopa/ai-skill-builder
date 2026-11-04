"""Controls for impacted selection, implementation completion and checkpoint integrity."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_tests
from repository_files import inventory


class TestScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'repo'
        (self.root / 'config').mkdir(parents=True)
        (self.root / 'source.txt').write_text('before')
        self.config = {'schema_version': 1, 'tests': {'related': {'argv': ['{python}', '-c', 'print("related-only")']}, 'unrelated': {'argv': ['{python}', '-c', 'print("unrelated")']}}, 'rules': [{'paths': ['source.txt'], 'tests': ['related']}], 'final_checks': {'all': {'argv': ['{python}', '-m', 'unittest', 'discover']}}}
        self.write_config()
        self.checkpoint = self.base / 'checkpoint.json'
        self.checkpoint.write_text(json.dumps({'root': str(self.root), 'files': inventory(self.root), 'test_sources': {}}))
        mocked = patch.object(run_tests, 'state_path', return_value=self.checkpoint)
        mocked.start()
        self.addCleanup(mocked.stop)

    def write_config(self):
        (self.root / 'config/test_impact.json').write_text(json.dumps(self.config))

    def completion_record(self, **updates):
        record = {
            'artifact_sha256': run_tests.digest(inventory(self.root)),
            'implementation_complete': True,
            'implementation_plan': {'source': 'Authored unit-control plan, not a real delivery claim',
                                    'steps': [{'id': 'I1', 'result': 'Preserve the control source'}]},
            'delivered_steps': [{'id': 'I1', 'status': 'delivered',
                                 'evidence': ['Authored fixture source, not fresh model evidence']}],
            'remaining_implementation_work': [],
            'verified_by': {'identity': 'Unit control', 'method': 'Declared synthetic delivery for guard testing'},
        }
        record.update(updates)
        path = self.base / 'completion.json'
        path.write_text(json.dumps(record))
        return path

    def test_default_uses_changed_files_and_runs_only_related_check(self):
        (self.root / 'source.txt').write_text('after')
        selection = run_tests.plan(self.root)
        self.assertEqual(selection['mode'], 'impacted')
        self.assertEqual([row['id'] for row in selection['checks']], ['related'])
        self.assertEqual(selection['checks'][0]['because'], ['source.txt'])
        result = run_tests.execute(selection)
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['results']), 1)
        self.assertEqual(result['results'][0]['stdout'].strip(), 'related-only')
        self.assertEqual(run_tests.changed_files(self.root), [])

    def test_unmapped_change_blocks_execution_without_full_fallback(self):
        selection = run_tests.plan(self.root, ['unknown.txt'])
        self.assertFalse(selection['executable'])
        with patch.object(run_tests.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'no full-suite fallback'):
                run_tests.execute(selection)
            process.assert_not_called()

    def test_full_suite_without_implementation_verification_is_refused(self):
        with patch.object(run_tests.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'Full suites are disabled'):
                run_tests.plan(self.root, [], full=True)
            process.assert_not_called()

    def test_verified_implementation_needs_no_user_approval(self):
        completion = self.completion_record()
        self.assertNotIn('user_instruction', json.loads(completion.read_text()))
        selection = run_tests.plan(self.root, [], full=True, completion_record=completion)
        self.assertEqual(selection['mode'], 'full')
        self.assertEqual(selection['implementation_completion']['record'], str(completion.resolve()))
        self.assertIn('author verified', selection['checks'][0]['because'][0])

    def test_completion_is_bound_to_the_exact_artifact(self):
        completion = self.completion_record()
        run_tests.plan(self.root, [], full=True, completion_record=completion)
        (self.root / 'source.txt').write_text('changed after the control verification')
        with self.assertRaisesRegex(ValueError, 'invalidate'):
            run_tests.plan(self.root, [], full=True, completion_record=completion)

    def test_final_execution_rechecks_implementation_and_completion_evidence(self):
        completion = self.completion_record()
        selection = run_tests.plan(self.root, [], full=True, completion_record=completion)
        record = json.loads(completion.read_text())
        record['verified_by']['method'] = 'Changed control review after planning'
        completion.write_text(json.dumps(record))
        with patch.object(run_tests.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'changed after final-test planning'):
                run_tests.execute(selection)
            process.assert_not_called()
        selection = run_tests.plan(self.root, [], full=True, completion_record=self.completion_record())
        (self.root / 'source.txt').write_text('Implementation changed before execution')
        with patch.object(run_tests.subprocess, 'run') as process:
            with self.assertRaisesRegex(ValueError, 'invalidate'):
                run_tests.execute(selection)
            process.assert_not_called()

    def test_verified_final_selection_executes_without_user_confirmation(self):
        selection = run_tests.plan(self.root, [], full=True, completion_record=self.completion_record())
        result = run_tests.subprocess.CompletedProcess([], 0, 'Authored full-run control', '')
        with patch.object(run_tests.subprocess, 'run', return_value=result) as process:
            report = run_tests.execute(selection)
            self.assertTrue(report['passed'])
            process.assert_called_once()

    def test_remaining_implementation_or_false_completion_blocks_final_testing(self):
        for change in [{'implementation_complete': False}, {'implementation_complete': 1},
                       {'remaining_implementation_work': ['Implement the missing branch']}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_tests.plan(self.root, [], full=True, completion_record=self.completion_record(**change))

    def test_every_planned_step_needs_delivery_evidence(self):
        for delivered in [[], [{'id': 'other', 'status': 'delivered', 'evidence': ['Control']}],
                          [{'id': 'I1', 'status': 'planned', 'evidence': ['Control']}],
                          [{'id': 'I1', 'status': 'delivered', 'evidence': []}],
                          [{'id': [], 'status': 'delivered', 'evidence': ['Control']}]]:
            with self.subTest(delivered=delivered), self.assertRaises(ValueError):
                run_tests.plan(self.root, [], full=True, completion_record=self.completion_record(delivered_steps=delivered))

    def test_duplicate_plan_steps_or_delivery_assessments_are_refused(self):
        for change in [
            {'implementation_plan': {'source': 'Control', 'steps': [{'id': 'I1', 'result': 'First'}, {'id': 'I1', 'result': 'Second'}]}},
            {'delivered_steps': [{'id': 'I1', 'status': 'delivered', 'evidence': ['Control']}] * 2},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_tests.plan(self.root, [], full=True, completion_record=self.completion_record(**change))

    def test_plan_and_actual_verifier_are_required(self):
        for change in [{'implementation_plan': {}}, {'implementation_plan': {'source': 'Control', 'steps': []}},
                       {'verified_by': {}}, {'verified_by': {'identity': 'Control', 'method': ''}}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                run_tests.plan(self.root, [], full=True, completion_record=self.completion_record(**change))

    def test_legacy_user_approval_does_not_assert_implementation_delivery(self):
        legacy = self.base / 'legacy-approval.json'
        legacy.write_text(json.dumps({'batch_complete': True, 'user_instruction': 'Authored approval control',
                                      'artifact_sha256': run_tests.digest(inventory(self.root))}))
        with self.assertRaisesRegex(ValueError, 'Verify implementation completion'):
            run_tests.plan(self.root, [], full=True, authorization=legacy)
        # The old argument name remains an alias for the new completion contract.
        self.assertEqual(run_tests.plan(self.root, [], full=True, authorization=self.completion_record())['mode'], 'full')

    def test_completion_record_must_be_an_external_object(self):
        inside = self.root / 'completion.json'
        inside.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'outside'):
            run_tests.plan(self.root, [], full=True, completion_record=inside)
        bad = self.base / 'invalid.json'
        bad.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'must be an object'):
            run_tests.plan(self.root, [], full=True, completion_record=bad)

    def test_hidden_full_discovery_cannot_be_an_impacted_group(self):
        self.config['tests']['related']['argv'] = ['{python}', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py']
        self.write_config()
        with self.assertRaisesRegex(ValueError, 'unrestricted full discovery'):
            run_tests.plan(self.root, ['source.txt'])

    def test_test_file_edits_select_changed_methods_only(self):
        name = 'tests/test_output.py'
        path = self.root / name
        path.parent.mkdir()
        before = 'import unittest\nclass OutputTests(unittest.TestCase):\n    def test_same(self):\n        self.assertTrue(True)\n    def test_changed(self):\n        self.assertEqual(1, 1)\n'
        path.write_text(before)
        self.checkpoint.write_text(json.dumps({'root': str(self.root), 'files': inventory(self.root), 'test_sources': {name: before}}))
        path.write_text(before.replace('self.assertEqual(1, 1)', 'self.assertEqual(2, 2)'))
        selection = run_tests.plan(self.root)
        self.assertEqual(len(selection['checks']), 1)
        self.assertIn('OutputTests.test_changed', selection['checks'][0]['argv'])
        self.assertNotIn('OutputTests.test_same', selection['checks'][0]['argv'])

    def test_partial_explicit_check_cannot_mark_other_changes_tested(self):
        before = json.loads(self.checkpoint.read_text())
        (self.root / 'source.txt').write_text('after')
        (self.root / 'unrelated.txt').write_text('still untested')
        result = run_tests.execute(run_tests.plan(self.root, ['source.txt']))
        self.assertTrue(result['passed'])
        self.assertEqual(json.loads(self.checkpoint.read_text())['files'], before['files'])

    def test_selective_discovery_is_distinct_from_an_entire_suite(self):
        self.assertFalse(run_tests.broad_command(['{python}', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_output.py']))
        self.assertTrue(run_tests.broad_command(['{python}', '-m', 'unittest', 'discover']))
        self.assertTrue(run_tests.broad_command(['{python}', '-m', 'unittest', 'discover', '-p']))

    def test_overlapping_module_selection_runs_the_module_once(self):
        path = self.root / 'tests/test_output.py'
        path.parent.mkdir()
        before = 'import unittest\nclass OutputTests(unittest.TestCase):\n    def test_changed(self):\n        self.assertEqual(1, 1)\n'
        path.write_text(before)
        self.config['tests']['related']['argv'] = ['{python}', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_output.py']
        self.write_config()
        self.checkpoint.write_text(json.dumps({'root': str(self.root), 'files': inventory(self.root), 'test_sources': {'tests/test_output.py': before}}))
        path.write_text(before.replace('self.assertEqual(1, 1)', 'self.assertEqual(2, 2)'))
        (self.root / 'source.txt').write_text('changed too')
        selection = run_tests.plan(self.root)
        self.assertEqual(len(selection['checks']), 1)
        self.assertNotIn('-k', selection['checks'][0]['argv'])

    def test_explicit_scope_works_without_git_or_a_checkpoint(self):
        self.checkpoint.unlink()
        result = run_tests.execute(run_tests.plan(self.root, ['source.txt']))
        self.assertTrue(result['passed'])
        self.assertFalse(self.checkpoint.exists())
