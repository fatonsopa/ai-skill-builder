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


class LiveProcessCaptureTests(unittest.TestCase):
    def test_output_is_available_before_the_child_can_finish(self):
        from evaluate import run_process
        with tempfile.TemporaryDirectory() as directory:
            flag = Path(directory) / 'received'
            code = "import pathlib,time; print('public progress',flush=True); p=pathlib.Path('received'); deadline=time.monotonic()+3\nwhile not p.exists() and time.monotonic()<deadline: time.sleep(0.01)\nassert p.exists(), 'output was buffered until exit'"
            result = run_process([sys.executable, '-u', '-c', code], input='', cwd=directory, timeout=5,
                                 on_stdout_line=lambda line: flag.write_text(line))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, 'public progress\n')
            self.assertEqual(flag.read_text(), result.stdout)

    def test_timeout_preserves_streamed_output_and_the_deadline(self):
        from evaluate import run_process
        commands = ["import time; print('started',flush=True); time.sleep(10)",
                    "import subprocess,sys; subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); print('started',flush=True)"]
        for code in commands:
            seen = []
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory, self.assertRaises(subprocess.TimeoutExpired) as error:
                run_process([sys.executable, '-u', '-c', code], input='', cwd=directory, timeout=0.5, on_stdout_line=seen.append)
            self.assertEqual(seen, ['started\n'])
            self.assertEqual(error.exception.output, 'started\n')


class NeutralExportTests(unittest.TestCase):
    """T36: the performer sees an ordinary request; the controller keeps the case identity."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'skill'
        (self.package / 'evals').mkdir(parents=True)
        (self.package / 'SKILL.md').write_text('---\nname: summary-control\ndescription: Summarize supplied notes.\n---\nSummarize only what the notes state.\n')
        self.case = {'id': 'builder-no-mechanical-only-claim', 'requirements': ['R-1'], 'critical': True, 'kind': 'behavior', 'semantic': True,
                     'request': {'text': 'Summarize quarterly-notes.md for the team.', 'source': {'quarterly-notes.md': 'Revenue rose; one test was not run.'}},
                     'resources': ['SKILL.md'], 'expect': {'exit_code': 0, 'contains': ['GRADER-ONLY: report the unrun test as not run']}}
        (self.package / 'evals/cases.json').write_text(json.dumps([self.case]))

    def export(self, binding):
        process = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'scripts/evaluate.py'), '--package', str(self.package),
                                  '--behavior-packet', self.case['id'], '--binding', str(binding)], capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout), json.loads(binding.read_text())

    def test_t36a_performer_view_keeps_request_and_file_without_grader_material(self):
        view, binding = self.export(self.root / 'controller/binding.json')
        text = json.dumps(view)
        self.assertEqual(view['request'], self.case['request'])
        self.assertIn('quarterly-notes.md', text)
        for clue in (self.case['id'], 'GRADER-ONLY', 'evals/cases.json', 'case_sha256', 'package_hashes'):
            self.assertNotIn(clue, text)
        self.assertEqual(binding['task_id'], view['task_id'])
        self.assertEqual(binding['case_id'], self.case['id'])
        self.assertIn('evals/cases.json', binding['package_hashes'])

    def test_binding_must_be_a_new_file_outside_the_package(self):
        script = str(Path(__file__).resolve().parents[1] / 'scripts/evaluate.py')
        for binding in (None, self.package / 'binding.json'):
            args = [sys.executable, script, '--package', str(self.package), '--behavior-packet', self.case['id']] + (['--binding', str(binding)] if binding else [])
            with self.subTest(binding=binding):
                self.assertNotEqual(subprocess.run(args, capture_output=True, text=True).returncode, 0)

    def test_t36b_only_the_matching_binding_is_eligible(self):
        from evaluate import controller_binding
        current = controller_binding(self.package, self.case)
        stale_case = deepcopy(self.case); stale_case['request']['text'] = 'An earlier frozen request.'
        stale = controller_binding(self.package, stale_case)
        def observed(binding):
            return {'package_hashes': inventory(self.package), 'bindings': [binding], 'observations': [{'task_id': binding['task_id'], 'output': 'Revenue rose. One test was not run.',
                    'provenance': {'kind': 'host_observation', 'host': 'fixture', 'model': None, 'source': 'Authored transport control; no model invocation.'}}]}
        matching = check_case(self.package, self.case, False, observations=observed(current))
        self.assertIn('observation', matching)  # eligible: graded against the case, not rejected at binding
        self.assertEqual(matching['failures'], ["Missing required literal in output: 'GRADER-ONLY: report the unrun test as not run'."])
        stale_result = check_case(self.package, self.case, False, observations=observed({**stale, 'case_id': self.case['id']}))
        self.assertEqual(stale_result['status'], 'failed')
        self.assertTrue(any('stale case binding' in error for error in stale_result['failures']))
        unbound = observed(current); unbound['bindings'] = []
        self.assertEqual(check_case(self.package, self.case, False, observations=unbound)['status'], 'failed')
