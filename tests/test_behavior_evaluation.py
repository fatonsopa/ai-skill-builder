"""Behavior-observation transport controls. No live model calls occur in this module."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate import behavior_packet, check_case, evaluate, json_hash
from repository_files import inventory


class BehaviorEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'skill'
        self.package.mkdir()
        (self.package / 'SKILL.md').write_text('---\nname: rewrite-control\ndescription: Audit and propose before rewriting.\n---\nRead the supplied source, present an audit and recommendations before drafting.\n')
        self.case = {'id': 'rewrite-first-reply', 'requirements': ['R-1'], 'critical': True, 'kind': 'behavior', 'request': {'text': 'Rewrite the supplied project instructions.', 'source': '# Instructions\nUse the reviewed command only.'}, 'resources': ['SKILL.md'], 'expect': {'exit_code': 0}, 'semantic': True, 'workflow': {'id': 'rewrite', 'scenario': 'behavior', 'covers': []}}

    def observations(self):
        # Emulates a transport result to test binding/review gates, not model quality.
        return {'package_hashes': inventory(self.package), 'observations': [{'case_id': self.case['id'], 'case_sha256': json_hash(self.case), 'provenance': {'kind': 'host_observation', 'host': 'fixture', 'model': None, 'source': 'Authored unit transport control; no actual model invocation.'}, 'output': 'Audit: the source repeats an instruction. Recommendation: retain the command and consolidate repetition before drafting.'}]}

    def test_performing_packet_contains_task_and_skill_but_no_expected_answers(self):
        self.case['expect']['contains'] = ['A hidden grading condition']
        packet = behavior_packet(self.package, self.case)
        self.assertEqual(packet['request'], self.case['request'])
        self.assertIn('Audit and propose', packet['skill'])
        self.assertNotIn('expect', packet)
        self.assertNotIn('A hidden grading condition', json.dumps(packet))

    def test_without_a_model_observation_the_case_is_not_run(self):
        result = check_case(self.package, self.case, False)
        self.assertEqual(result['status'], 'not_run')
        self.assertNotEqual(result['status'], 'passed')

    def test_a_declared_transport_failure_cannot_reach_favorable_semantic_review(self):
        for status in ('failed', 'timed_out', 'cancelled', 'not_run', 'unknown'):
            observations = self.observations()
            observations['observations'][0]['execution_status'] = status
            observations['observations'][0]['output'] = 'A plausible but incomplete audit.'
            with self.subTest(status=status):
                result = check_case(self.package, self.case, False, observations=observations)
                self.assertEqual(result['status'], 'failed')
                self.assertNotEqual(result['status'], 'pending_review')

    def test_completed_native_capture_can_be_reviewed(self):
        observations = self.observations()
        observations['observations'][0]['execution_status'] = 'completed'
        self.assertEqual(check_case(self.package, self.case, False, observations=observations)['status'], 'pending_review')

    def test_performing_resources_cannot_expose_evaluation_answers(self):
        (self.package / 'evals').mkdir()
        (self.package / 'references').mkdir()
        (self.package / 'scripts').mkdir()
        (self.package / 'evals/answer.json').write_text('Hidden acceptance criteria')
        for name in ('scripts/test_control.py', 'scripts/words.test.py'):
            (self.package / name).write_text('Hidden authored control')
        for name in ('evals/answer.json', 'references/../evals/answer.json', 'scripts/test_control.py', 'scripts/words.test.py'):
            self.case['resources'] = [name]
            with self.subTest(path=name), self.assertRaisesRegex(ValueError, 'grading|evaluation|development'):
                behavior_packet(self.package, self.case)

    def test_runtime_test_plan_guidance_is_available_to_the_performer(self):
        (self.package / 'references').mkdir()
        (self.package / 'references/test_plan.md').write_text('Explain scope and test approach.')
        self.case['resources'] = ['references/test_plan.md']
        packet = behavior_packet(self.package, self.case)
        self.assertEqual(packet['resources']['references/test_plan.md'], 'Explain scope and test approach.')

    def test_captured_output_needs_semantic_review_not_self_reported_success(self):
        observations = self.observations()
        observations['observations'][0]['accepted'] = True
        result = check_case(self.package, self.case, False, observations=observations)
        self.assertEqual(result['status'], 'pending_review')
        self.assertIn('Audit:', result['observation']['output'])

    def test_an_observation_from_a_different_input_is_rejected(self):
        source = self.observations()
        self.case['request']['text'] = 'Now implement an unrelated feature.'
        result = check_case(self.package, self.case, False, observations=source)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('frozen input' in error for error in result['failures']))

    def test_an_observation_from_another_skill_version_is_rejected(self):
        source = self.observations()
        (self.package / 'SKILL.md').write_text('Changed workflow')
        result = check_case(self.package, self.case, False, observations=source)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('another skill version' in error for error in result['failures']))

    def test_controls_replays_and_missing_identity_cannot_be_fresh_behavior(self):
        for kind in ('authored_control', 'historical_replay', 'instrumented_execution'):
            source = self.observations()
            source['observations'][0]['provenance']['kind'] = kind
            with self.subTest(kind=kind):
                self.assertEqual(check_case(self.package, self.case, False, observations=source)['status'], 'failed')
        for field in ('source', 'host', 'model'):
            source = self.observations()
            source['observations'][0]['provenance'].pop(field)
            with self.subTest(field=field):
                self.assertEqual(check_case(self.package, self.case, False, observations=source)['status'], 'failed')

    def test_mechanical_passes_do_not_hide_absent_behavioral_coverage(self):
        (self.package / 'good.txt').write_text('A correct mechanical artifact')
        mechanical = {'id': 'file-control', 'requirements': ['R-1'], 'critical': True, 'kind': 'artifact', 'semantic': False, 'expect': {'exit_code': 0, 'file': 'good.txt'}}
        report = evaluate(self.package, [mechanical, self.case], False)
        self.assertEqual(report['mechanical_metrics']['task_success_percent'], 100)
        self.assertEqual(report['behavioral_metrics']['coverage_percent'], 0)
        self.assertIsNone(report['behavioral_metrics']['task_success_percent'])
        self.assertEqual(report['metrics']['coverage_percent'], 50)

    def test_explicit_process_failures_survive_favorable_output(self):
        source = self.observations()
        self.case['expect']['process'] = {'order': ['research', 'audit', 'present', 'draft'], 'visible': ['present'], 'evidence': ['audit']}
        source['observations'][0]['case_sha256'] = json_hash(self.case)
        source['observations'][0]['trace'] = {'provenance': {'kind': 'host_observation', 'source': 'Transport control'}, 'events': [{'phase': 'draft', 'evidence': 'Correct final document', 'visible': True}]}
        result = check_case(self.package, self.case, False, observations=source)
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['process']['passed'])

    def test_duplicate_observations_do_not_inflate_success_counts(self):
        source = self.observations()
        source['observations'].append(deepcopy(source['observations'][0]))
        result = check_case(self.package, self.case, False, observations=source)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(any('Duplicate' in error for error in result['failures']))

    def test_malformed_observations_fail_as_data_instead_of_crashing(self):
        for malformed in ('bad', [None], [{'provenance': 'bad'}]):
            observations = self.observations()
            observations['observations'] = malformed
            if isinstance(malformed, list) and isinstance(malformed[0], dict):
                observations['observations'][0] = {**observations['observations'][0], 'case_id': self.case['id'], 'case_sha256': json_hash(self.case)}
            with self.subTest(value=malformed):
                self.assertEqual(check_case(self.package, self.case, False, observations=observations)['status'], 'failed')

    def test_builder_suite_has_critical_intent_cases_and_matching_rubric(self):
        root = Path(__file__).resolve().parents[1]
        suite = json.loads((root / 'evals/cases.json').read_text())
        rubric = json.loads((root / 'evals/behavior_rubric.json').read_text())
        behaviors = [case for case in suite if case['kind'] == 'behavior']
        self.assertGreaterEqual(len(behaviors), 4)
        self.assertTrue(all(case['semantic'] and case['critical'] and case['request'] and case['resources'] for case in behaviors))
        rubric_text = json.dumps(rubric)
        self.assertTrue(all(case['id'] in rubric_text for case in behaviors))
