"""Regression for contradictory assertions observed in an actual AI plan."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from runtime.artifacts import check_plan
from runtime.common import Invalid
from evaluate import check_case
from fixtures import PLAN, SPEC


class PlanConsistencyTests(unittest.TestCase):
    def control(self):
        plan = deepcopy(PLAN)
        case = next(c for c in plan['cases'] if c['kind'] == 'command')
        case.update(command=['{python}', '-c', 'print("control")'], semantic=True)
        case['expect'] = {'exit_code': 0, 'stdout_json': {'scenario': 'success', 'assertions_passed': True}, 'process': {'order': ['research', 'audit'], 'visible': ['audit'], 'evidence': ['research', 'audit']}}
        trace = {'provenance': {'kind': 'authored_control', 'source': 'Regression fixture, not model behavior.'}, 'events': [{'phase': 'research', 'evidence': 'Source inspected in this authored fixture.'}, {'phase': 'audit', 'visible': True, 'evidence': 'Located finding in this authored fixture.'}]}
        return plan, case, trace

    def test_exact_summary_json_cannot_also_be_the_missing_process_trace(self):
        plan, _, _ = self.control()
        with self.assertRaisesRegex(Invalid, 'contradictory exact stdout'):
            check_plan(SPEC, plan)

    def test_exact_non_json_text_cannot_supply_a_process_trace(self):
        plan, case, _ = self.control()
        del case['expect']['stdout_json']
        case['expect']['stdout_text'] = 'Passed.'
        with self.assertRaisesRegex(Invalid, 'contradictory exact stdout'):
            check_plan(SPEC, plan)

    def test_a_separate_captured_trace_allows_both_checks_to_run(self):
        plan, case, trace = self.control()
        case['expect']['process']['trace_file'] = 'captured-trace.json'
        case['command'] = ['{python}', '-c', 'print(' + repr(json.dumps(case['expect']['stdout_json'])) + ')']
        check_plan(SPEC, plan)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'captured-trace.json').write_text(json.dumps(trace))
            result = check_case(root, case, True)
        self.assertEqual(result['status'], 'pending_review')
        self.assertTrue(result['process']['passed'])

    def test_exact_trace_output_is_compatible_without_a_separate_file(self):
        plan, case, trace = self.control()
        case['expect']['stdout_json'] = trace
        check_plan(SPEC, plan)
