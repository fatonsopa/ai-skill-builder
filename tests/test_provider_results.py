"""Authored offline controls; these never invoke a real provider."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from runtime import adapters, benchmark, workflow
from runtime.common import Invalid
import test_host_coverage as coverage_controls
import host_coverage as matrix


def limited(started=False):
    return {'type': 'result', 'subtype': 'success', 'is_error': True,
            'terminal_reason': 'api_error', 'api_error': 'usage_limit_reached',
            'api_error_status': 429, 'result': 'Usage limit reached.',
            'usage': {'input_tokens': 1 if started else 0, 'output_tokens': 2 if started else 0}}


def good():
    return {'type': 'result', 'subtype': 'success', 'is_error': False,
            'structured_output': {'response_json': json.dumps({'id': '0042'})}}


class ProviderResultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def sample(self, event, exit_code=0):
        with patch.object(adapters, 'run_process', return_value=subprocess.CompletedProcess([], exit_code, json.dumps(event), '')) as call:
            result = adapters.sample('claude', 'fixture-model', {'id': '0042'}, 5)
        self.assertEqual(call.call_count, 1)
        return result

    def test_valid_envelope_remains_valid_but_cannot_override_an_error(self):
        self.assertEqual(self.sample(good())['response'], {'id': '0042'})
        error = {**limited(), 'structured_output': good()['structured_output']}
        with self.assertRaisesRegex(Invalid, 'Usage limit'):
            adapters.decode('claude', json.dumps(error), self.root / 'unused')
        result = self.sample(error)
        self.assertEqual(result['status'], 'infrastructure_failure')
        self.assertNotIn('response', result)

    def test_exit_codes_do_not_erase_unstarted_or_interrupted_provider_cause(self):
        for started in (False, True):
            for code in (0, 1):
                with self.subTest(started=started, exit_code=code):
                    result = self.sample(limited(started), code)
                    self.assertEqual(result['status'], 'failed' if started else 'infrastructure_failure')
                    self.assertEqual(result['provider_error']['task_started'], started)
                    self.assertEqual(result['provider_error']['http_status'], 429)
                    self.assertEqual(result['provider_error']['code'], 'usage_limit_reached')
                    self.assertIn('Usage limit reached.', result['stdout'])

    def test_missing_usage_is_unknown_and_nonprovider_errors_stay_failures(self):
        event = limited(); event.pop('usage')
        result = self.sample(event)
        self.assertIsNone(result['provider_error']['task_started'])
        self.assertEqual(result['status'], 'failed')
        result = self.sample({'type': 'result', 'subtype': 'error_max_turns', 'is_error': True,
                              'result': 'Turn limit reached.', 'structured_output': good()['structured_output']})
        self.assertEqual(result['status'], 'failed')
        self.assertNotIn('response', result)
        self.assertNotIn('provider_error', result)

    def test_timeout_retains_partial_provider_cause_without_erasing_failed_execution(self):
        error = subprocess.TimeoutExpired('authored-fixture', 5, output=json.dumps(limited()).encode())
        with patch.object(adapters, 'run_process', side_effect=error):
            result = adapters.sample('claude', 'fixture-model', {}, 5)
        self.assertEqual(result['status'], 'failed')
        self.assertTrue(result['timed_out'])
        self.assertEqual(result['provider_error']['code'], 'usage_limit_reached')
        self.assertIn('Usage limit reached.', result['stdout'])

    def test_phase_invocation_reserves_one_call_and_records_provider_cause(self):
        run = self.root / 'phase-run'
        workflow.start(run, {'operation': 'create', 'skill_name': 'fixture', 'brief': 'Authored fixture.',
                             'copyright_holder': 'Fixture', 'limits': {'max_live_calls': 1},
                             'host': {'platform': 'claude-code', 'model': 'fixture-model', 'code_execution': True, 'file_access': True, 'external_cli': True, 'allow_cross_provider': False}})
        with patch.object(adapters.shutil, 'which', return_value='/authored-claude'), patch.object(adapters, 'run_process', return_value=subprocess.CompletedProcess([], 0, json.dumps(limited()), '')) as call:
            result = adapters.invoke(run, 'claude', 'fixture-model')
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result['status'], 'infrastructure_failure')
        self.assertEqual(result['provider_error']['http_status'], 429)
        self.assertEqual(json.loads((run / 'state.json').read_text())['model_invocations'], 1)
        self.assertEqual(json.loads((run / 'model_results/001.json').read_text())['provider_error'], result['provider_error'])
        with self.assertRaises(Invalid):
            adapters.invoke(run, 'claude', 'fixture-model')

    def config(self):
        subject = self.root / 'subject'; subject.mkdir()
        (subject / 'SKILL.md').write_text('# Authored control\n')
        case = {'id': 'value', 'request': {'id': '0042'}, 'resources': [],
                'expected': {'id': '0042'}, 'semantic': False, 'critical': True, 'split': 'regression'}
        config = {'subject': str(subject),
                  'models': [{'provider': 'claude', 'model': 'fixture-claude', 'repetitions': 1},
                             {'provider': 'codex', 'model': 'fixture-codex', 'repetitions': 1}],
                  'cases': [{**case, 'id': name} for name in ('first', 'second', 'third')],
                  'compare_without_skill': False, 'max_invocations': 6, 'max_seconds': 30}
        path = self.root / 'benchmark.json'; path.write_text(json.dumps(config))
        return path

    def test_actual_adapter_chain_stops_before_later_cases_and_preserves_prior_pass(self):
        path = self.config()
        outputs = [good(), limited()]
        with patch.object(adapters, 'run_process', side_effect=[subprocess.CompletedProcess([], 0, json.dumps(x), '') for x in outputs]) as call:
            report = benchmark.benchmark(path, self.root / 'observations')
        self.assertEqual(call.call_count, 2)
        self.assertEqual(report['model_invocations'], 2)
        self.assertEqual([r['status'] for r in report['attempts']], ['passed', 'infrastructure_failure'] + ['not_run'] * 4)
        self.assertEqual(report['execution_block']['http_status'], 429)
        self.assertEqual(report['attempts'][1]['provider_error']['code'], 'usage_limit_reached')
        for row in report['attempts']:
            self.assertEqual(json.loads((self.root / 'observations' / (row['id'] + '.json')).read_text()), row)
        print(json.dumps({'process_trace': {'provenance': {'kind': 'authored_control', 'source': 'Real optional sample/benchmark functions with stubbed provider process, not model performance.'},
              'events': [{'phase': 'invoke', 'evidence': json.dumps({'actual_stub_calls': call.call_count})},
                         {'phase': 'classify', 'evidence': json.dumps(report['attempts'][1]['observation'])},
                         {'phase': 'retain', 'evidence': json.dumps({'saved_rows': len(report['attempts']), 'prior_status': report['attempts'][0]['status']})},
                         {'phase': 'stop', 'evidence': json.dumps({'not_run': 4, 'calls': report['model_invocations'], 'execution_block': report['execution_block']})}]}}))

    def test_interrupted_usage_limit_also_stops_the_batch(self):
        path = self.config()
        with patch.object(adapters, 'run_process', return_value=subprocess.CompletedProcess([], 0, json.dumps(limited(True)), '')) as call:
            report = benchmark.benchmark(path, self.root / 'interrupted')
        self.assertEqual(call.call_count, 1)
        self.assertEqual([r['status'] for r in report['attempts']], ['failed'] + ['not_run'] * 5)
        self.assertTrue(report['execution_block']['task_started'])

    def test_new_bounded_run_after_recovery_does_not_rewrite_unavailable_report(self):
        path = self.config()
        with patch.object(adapters, 'run_process', return_value=subprocess.CompletedProcess([], 0, json.dumps(limited()), '')):
            benchmark.benchmark(path, self.root / 'old')
        original = (self.root / 'old/report.json').read_bytes()
        with patch.object(benchmark, 'sample', return_value={'status': 'response_validated', 'response': {'id': '0042'}}) as call:
            report = benchmark.benchmark(path, self.root / 'new')
        self.assertEqual(call.call_count, 6)
        self.assertTrue(all(r['status'] == 'passed' for r in report['attempts']))
        self.assertEqual(original, (self.root / 'old/report.json').read_bytes())

    def test_process_checker_rejects_each_omission_and_wrong_order(self):
        from evaluate import grade_process
        trace = {'provenance': {'kind': 'authored_control', 'source': 'Corrupted control for provider workflow order only.'},
                 'events': [{'phase': name, 'evidence': 'Authored phase evidence.'} for name in ('invoke', 'classify', 'retain', 'stop')]}
        expected = {'order': ['invoke', 'classify', 'retain', 'stop'], 'visible': [], 'evidence': ['invoke', 'classify', 'retain', 'stop']}
        self.assertTrue(grade_process(trace, expected)['passed'])
        for i in range(4):
            bad = deepcopy(trace); bad['events'].pop(i)
            self.assertFalse(grade_process(bad, expected)['passed'])
        for i in range(3):
            bad = deepcopy(trace); bad['events'][i], bad['events'][i + 1] = bad['events'][i + 1], bad['events'][i]
            self.assertFalse(grade_process(bad, expected)['passed'])

    def fixture(self):
        fixture = coverage_controls.HostCoverageTests()
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        return fixture

    def test_favorable_review_cannot_accept_a_provider_error_as_task_output(self):
        fixture = self.fixture(); bundle = fixture.bundle('claude-code')
        report_path = Path(bundle['report']); report = json.loads(report_path.read_text())
        row = report['attempts'][0]; row['output'] = limited()['result']
        events = Path(row['public_events']); events.write_text(json.dumps([limited()]))
        report_path.write_text(json.dumps(report))
        review_path = Path(bundle['review']); review = json.loads(review_path.read_text())
        review['report_sha256'] = matrix.digest(report_path.read_bytes())
        review['cases'][0].update(capture_sha256=matrix.digest(row), public_events_sha256=matrix.digest(events.read_bytes()))
        review_path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'error result'):
            matrix.assess(fixture.plan, fixture.package, [bundle])

    def test_unstarted_or_unrun_attempt_cannot_hide_prior_observed_outcome(self):
        fixture = self.fixture()
        for previous in ('failed', 'pending_review'):
            before = fixture.bundle('codex', status=previous, accepted=True, name='before-' + previous)
            expected = 'failed' if previous == 'failed' else 'passed'
            for status in ('not_run', 'infrastructure_failure'):
                later = fixture.bundle('codex', status=status, name=previous + '-' + status)
                result = matrix.assess(fixture.plan, fixture.package, [before, later])
                cell = next(c for c in result['cells'] if c['host'] == 'codex')
                self.assertEqual(cell['status'], expected)
                self.assertEqual([r['status'] for r in result['attempt_history']], [expected, 'not_run'])


if __name__ == '__main__':
    unittest.main()
