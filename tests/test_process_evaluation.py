"""Process-grader controls; these are not independent model observations."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate import check_case, evaluate, grade_process

ORDER = ['research', 'audit', 'proposal', 'present', 'draft', 'validate']
CONTRACT = {'order': ORDER, 'visible': ['present'], 'evidence': ['research', 'audit', 'proposal', 'present', 'validate']}


def trace(order=ORDER, kind='authored_control'):
    return {'provenance': {'kind': kind, 'source': 'Authored grader control, not a live model run.'}, 'events': [{'phase': stage, 'evidence': 'control:' + stage, 'visible': stage == 'present'} for stage in order]}


class ProcessEvaluationTests(unittest.TestCase):
    def test_valid_order_retains_evidence_and_provenance_for_review(self):
        source = trace(kind='historical_replay')
        result = grade_process(source, CONTRACT)
        self.assertTrue(result['passed'], result)
        self.assertEqual(result['trace'], source)
        self.assertEqual(result['provenance']['kind'], 'historical_replay')

    def test_every_missing_phase_is_a_failure(self):
        for phase in ORDER:
            with self.subTest(phase=phase):
                self.assertFalse(grade_process(trace([stage for stage in ORDER if stage != phase]), CONTRACT)['passed'])

    def test_each_adjacent_phase_swap_is_a_failure(self):
        for index in range(len(ORDER) - 1):
            order = list(ORDER)
            order[index:index + 2] = reversed(order[index:index + 2])
            with self.subTest(pair=index):
                self.assertFalse(grade_process(trace(order), CONTRACT)['passed'])

    def test_early_draft_stays_a_failure_after_later_repair(self):
        result = grade_process(trace(['draft', *ORDER]), CONTRACT)
        self.assertFalse(result['passed'])
        self.assertEqual(result['observed_order'][0], 'draft')

    def test_a_private_audit_does_not_satisfy_a_visible_handoff(self):
        source = trace()
        source['events'][3]['visible'] = False
        result = grade_process(source, CONTRACT)
        self.assertFalse(result['passed'])
        self.assertTrue(any('user-visible' in error for error in result['failures']))
        source['events'][3]['visible'] = 'true'
        self.assertFalse(grade_process(source, CONTRACT)['passed'])

    def test_missing_stage_evidence_is_not_a_pass(self):
        for phase in CONTRACT['evidence']:
            source = trace()
            next(row for row in source['events'] if row['phase'] == phase)['evidence'] = ' '
            with self.subTest(phase=phase):
                self.assertFalse(grade_process(source, CONTRACT)['passed'])

    def test_malformed_or_unattributed_trace_cannot_claim_compliance(self):
        for source in (None, [], {}, {'passed': True}, {'provenance': {'kind': 'fresh', 'source': 'claimed'}, 'events': []}, {'provenance': {'kind': 'authored_control', 'source': 'fixture'}, 'events': [True]}):
            with self.subTest(source=source):
                self.assertFalse(grade_process(source, CONTRACT)['passed'])

    def test_recovery_repetitions_need_the_frozen_expected_path(self):
        order = ['research', 'audit', 'proposal', 'present', 'draft', 'validate', 'draft', 'validate']
        expected = {**CONTRACT, 'order': order}
        self.assertTrue(grade_process(trace(order), expected)['passed'])
        self.assertFalse(grade_process(trace(order), CONTRACT)['passed'])

    def test_correct_final_artifact_cannot_override_bad_process(self):
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder)
            raw = trace(['research', 'draft', 'audit', 'proposal', 'present', 'validate'])
            (package / 'work.py').write_text("from pathlib import Path\nimport json\nPath('document.md').write_text('Correct finished document')\nprint(" + repr(json.dumps(raw)) + ")\n")
            case = {'id': 'early-draft', 'requirements': ['R-1'], 'critical': True, 'kind': 'command', 'command': ['{python}', 'work.py'], 'semantic': True, 'workflow': {'id': 'rewrite', 'scenario': 'success', 'covers': []}, 'expect': {'exit_code': 0, 'file': 'document.md', 'process': CONTRACT}}
            result = check_case(package, case, True)
            self.assertTrue((package / 'document.md').is_file())
            self.assertEqual(result['status'], 'failed')
            self.assertFalse(result['process']['passed'])

    def test_trace_file_cannot_escape_the_case_package(self):
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / 'package'
            package.mkdir()
            outside = Path(folder) / 'trace.json'
            outside.write_text(json.dumps(trace()))
            case = {'id': 'escape', 'requirements': ['R-1'], 'critical': True, 'kind': 'artifact', 'semantic': False, 'expect': {'exit_code': 0, 'file': 'inside.json', 'process': {**CONTRACT, 'trace_file': '../trace.json'}}}
            (package / 'inside.json').write_text('{}')
            result = check_case(package, case, False)
            self.assertEqual(result['status'], 'failed')
            self.assertTrue(any('inside the evaluated package' in error for error in result['failures']))

    def test_no_execution_means_no_workflow_pass_percentage(self):
        with tempfile.TemporaryDirectory() as folder:
            case = {'id': 'unrun', 'requirements': ['R-1'], 'critical': True, 'kind': 'command', 'command': ['{python}', 'missing.py'], 'semantic': False, 'workflow': {'id': 'rewrite', 'scenario': 'success', 'covers': []}, 'expect': {'exit_code': 0, 'process': CONTRACT}}
            report = evaluate(Path(folder), [case], False)
            self.assertEqual(report['process_metrics']['evaluated'], 0)
            self.assertIsNone(report['process_metrics']['success_percent'])
            self.assertEqual(report['process_metrics']['coverage_percent'], 0)

    def test_cli_returns_failure_for_an_out_of_order_trace(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            trace_file, expected_file = Path(folder) / 'trace.json', Path(folder) / 'expected.json'
            expected_file.write_text(json.dumps(CONTRACT))
            for raw, code in ((trace(), 0), (trace(['draft', *ORDER]), 1)):
                trace_file.write_text(json.dumps(raw))
                result = subprocess.run([sys.executable, str(root / 'scripts/skill_builder_cli.py'), 'check-process', '--trace', str(trace_file), '--expect', str(expected_file)], cwd=root, text=True, capture_output=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(json.loads(result.stdout)['passed'], code == 0)
