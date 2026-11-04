"""Plan/CLI invariants for workflow tests, not model-performance evidence."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from runtime import contracts, workflow
from runtime.artifacts import check_plan, check_workflow_coverage, workflow_requirements
from runtime.common import Invalid, validate
from fixtures import PLAN, SPEC, RESEARCH, PRODUCE, writer_fixture, validate_fixture_documents
from evaluate import json_hash
from repository_files import inventory


def specification():
    spec = deepcopy(SPEC)
    spec['workflows'] = [{'id': 'rewrite', 'purpose': 'Audit and propose before drafting.', 'trigger': 'Substantial rewrite requested.', 'steps': ['research', 'audit', 'proposal', 'present', 'draft', 'validate'], 'boundaries': [{'id': 'before-draft', 'text': 'Do not draft before presenting the audit.'}], 'branches': [{'id': 'small-edit', 'text': 'Keep small edits out of the rewrite process.'}], 'recovery': [{'id': 'changed-source', 'text': 'Invalidate source-bound evidence after source changes.'}]}]
    return spec


def complete_plan(spec):
    plan = deepcopy(PLAN)
    plan['cases'] = []
    for label in workflow_requirements(spec)['rewrite']:
        scenario, _, covered = label.partition(':')
        row = {'id': 'rewrite-' + label, 'requirements': ['R-1', 'R-2', 'R-3'], 'critical': True, 'kind': 'command', 'command': ['{python}', 'scripts/control.py'], 'expect': {'exit_code': 0, 'stdout_json': {'blocked': True}}, 'semantic': False, 'workflow': {'id': 'rewrite', 'scenario': scenario, 'covers': [covered] if covered else []}}
        if scenario == 'behavior':
            row.update(kind='behavior', request='Rewrite the supplied source using the actual skill.', resources=['SKILL.md'], semantic=True)
            row['expect'] = {'exit_code': 0}
        if scenario == 'success':
            row['expect'] = {'exit_code': 0, 'process': {'order': spec['workflows'][0]['steps'], 'visible': ['present'], 'evidence': ['research', 'audit', 'proposal', 'present', 'validate']}}
            row['semantic'] = True
        plan['cases'].append(row)
    return plan


class WorkflowCoverageTests(unittest.TestCase):
    def setUp(self):
        writer_fixture(self)

    def normalizer(self):
        spec, plan = deepcopy(SPEC), deepcopy(PLAN)
        spec['workflows'] = [{'id': 'normalize', 'purpose': 'Normalize one record.', 'trigger': 'Customer JSON input.', 'steps': ['normalize'], 'boundaries': [], 'branches': [], 'recovery': []}]
        plan['cases'][0]['workflow'] = {'id': 'normalize', 'scenario': 'success', 'covers': []}
        plan['cases'][-1]['workflow'] = {'id': 'normalize', 'scenario': 'invalid_input', 'covers': []}
        plan['cases'].append({'id': 'model-use', 'requirements': ['R-1', 'R-2', 'R-3'], 'critical': True, 'kind': 'behavior', 'request': {'task': 'Normalize this record with the skill.', 'input': {'id': '0007', 'name': ' Ada '}}, 'resources': ['SKILL.md', 'scripts/normalize.py'], 'expect': {'exit_code': 0, 'stdout_json': {'customer_id': '0007', 'display_name': 'Ada'}}, 'semantic': True, 'workflow': {'id': 'normalize', 'scenario': 'behavior', 'covers': []}})
        return spec, plan

    def test_new_protocol_requires_workflow_inventory(self):
        spec = deepcopy(SPEC)
        spec.pop('workflows', None)
        packet = {'run_id': 'control', 'phase': 'specify', 'packet_sha256': 'a' * 64, 'data': spec}
        with self.assertRaises(Invalid):
            validate(packet, contracts.response_schema('specify'))
        validate(packet, contracts.response_schema('specify', 1))

    def test_every_declared_step_and_condition_needs_a_relevant_test(self):
        spec = specification()
        plan = complete_plan(spec)
        check_plan(spec, plan, require_workflows=True)
        for index, row in enumerate(plan['cases']):
            changed = deepcopy(plan)
            changed['cases'].pop(index)
            with self.subTest(missing=row['id']), self.assertRaisesRegex(Invalid, 'Missing workflow/process tests'):
                check_workflow_coverage(spec, changed)

    def test_successful_final_output_is_not_workflow_coverage(self):
        spec = specification()
        plan = deepcopy(PLAN)
        for row in plan['cases']:
            row.pop('workflow', None)
        with self.assertRaisesRegex(Invalid, 'Missing workflow/process tests'):
            check_plan(spec, plan, require_workflows=True)

    def test_multi_step_success_requires_trace_and_semantic_evidence_review(self):
        spec = specification()
        plan = complete_plan(spec)
        success = next(row for row in plan['cases'] if row['workflow']['scenario'] == 'success')
        success['semantic'] = False
        with self.assertRaisesRegex(Invalid, 'semantic evidence review'):
            check_workflow_coverage(spec, plan)
        success['semantic'] = True
        success['expect'].pop('process')
        with self.assertRaisesRegex(Invalid, 'ordered trace'):
            check_workflow_coverage(spec, plan)

    def test_optional_or_unknown_workflow_cases_do_not_satisfy_the_contract(self):
        spec = specification()
        for field, value in (('critical', False), ('workflow', {'id': 'unknown', 'scenario': 'success', 'covers': []})):
            plan = complete_plan(spec)
            plan['cases'][0][field] = value
            with self.subTest(field=field), self.assertRaises(Invalid):
                check_workflow_coverage(spec, plan)

    def test_simple_transformation_uses_relevant_input_output_tests(self):
        spec, plan = self.normalizer()
        check_plan(spec, plan, require_workflows=True)
        self.assertEqual(workflow_requirements(spec)['normalize'], ['behavior', 'invalid_input', 'success'])

    def test_cli_rejects_phase_skips_without_creating_a_candidate(self):
        root = Path(__file__).resolve().parents[1]
        cli = [sys.executable, str(root / 'scripts/skill_builder_cli.py')]
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            request = folder / 'request.json'
            run = folder / 'run'
            from runtime.completion import create
            policy = create(folder, {'objective_id': 'authored-cli-control', 'goal': 'Verify existing CLI behavior with the current contract.',
                'project': str(folder / 'phase-project'), 'scope': ['**'],
                'checks': [{'id': 'report', 'kind': 'report', 'dependencies': []}],
                'budget': {'runs': 1, 'revisions': 0, 'model_calls': 0, 'seconds': 600},
                'delivery': {'kind': 'report', 'authority': 'Authored unit control only.'}})['policy']
            request.write_text(json.dumps({'completion_policy': policy, 'operation': 'create', 'skill_name': 'phase-control', 'brief': 'Check process order.', 'copyright_holder': 'Fixture'}))
            result = subprocess.run(cli + ['start', '--request', str(request), '--run', str(run)], cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            before = (run / 'state.json').read_bytes()
            packet = json.loads(subprocess.run(cli + ['packet', '--run', str(run)], cwd=root, text=True, capture_output=True, check=True).stdout)
            for skipped in ('specify', 'plan', 'produce', 'review'):
                response = folder / (skipped + '.json')
                response.write_text(json.dumps({'run_id': packet['run_id'], 'phase': skipped, 'packet_sha256': packet['packet_sha256'], 'data': {}}))
                result = subprocess.run(cli + ['submit', '--run', str(run), '--response', str(response)], cwd=root, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((run / 'state.json').read_bytes(), before)
                self.assertFalse((run / 'candidate').exists())

    def test_favorable_output_review_cannot_waive_failed_workflow_evidence(self):
        spec = specification()
        state = {'protocol_version': 2, 'data': {'specify': spec}}
        # The evidence review is a separate required judgment for actual multi-step workflows.
        with self.assertRaisesRegex(Invalid, 'Review every workflow'):
            workflow.merge_review(Path('/not-used'), {**state, 'evaluation': {'package_hashes': {}}, 'request': {'operation': 'modify'}}, {'cases': [], 'resource_findings': []})

    def test_default_v2_readiness_requires_observation_and_actual_review(self):
        # Authored transport controls verify the gates, not model competence.
        for capture in (False, True):
            with self.subTest(capture=capture), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                run = root / 'run'
                workflow.start(run, {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'Normalize customer JSON.', 'copyright_holder': 'Fixture'}, protocol_version=2)
                spec, plan = self.normalizer()
                def submit(phase, data):
                    packet = workflow.packet(run)
                    return workflow.submit(run, {'run_id': packet['run_id'], 'phase': phase, 'packet_sha256': packet['packet_sha256'], 'data': data})
                for phase, data in (('research', RESEARCH), ('specify', spec), ('plan', plan), ('produce', PRODUCE)):
                    submit(phase, deepcopy(data))
                self.assertEqual(workflow.read_state(run)['protocol_version'], 2)
                observation_path = None
                if capture:
                    case = plan['cases'][-1]
                    observation_path = root / 'observation.json'
                    observation_path.write_text(json.dumps({'package_hashes': inventory(run / 'candidate'), 'observations': [{'case_id': case['id'], 'case_sha256': json_hash(case), 'provenance': {'kind': 'host_observation', 'host': 'fixture', 'model': None, 'source': 'Authored protocol transport control, not a real model run.'}, 'output': {'customer_id': '0007', 'display_name': 'Ada'}}]}))
                report = workflow.run_evaluation(run, allow_exec=True, observations=observation_path)
                self.assertEqual(report['attempts'][-1]['status'], 'pending_review' if capture else 'not_run')
                files = inventory(run / 'candidate')
                review = {'reviewer': {'kind': 'model', 'identity': 'fixture', 'method': 'Authored control of readiness, not quality judgment.'}, 'cases': [{'id': plan['cases'][-1]['id'], 'accepted': True, 'rationale': 'Favorable review cannot invent a missing observation.'}], 'resource_findings': [{'path': path, 'accepted': True, 'evidence': 'Fixture resource review.'} for path in sorted(workflow.review_resource_names(workflow.read_state(run)))], 'workflow_findings': [{'id': 'normalize', 'accepted': True, 'evidence': 'Fixture inventory and transport reviewed.'}], 'workflow_inventory': {'accepted': True, 'evidence': 'Single-step fixture workflow.'}}
                validate_fixture_documents(run)
                submit('review', review)
                state = workflow.read_state(run)
                self.assertEqual(state['status'] == 'ready', capture)
                if not capture:
                    self.assertEqual(state['evaluation']['behavioral_metrics']['coverage_percent'], 0)

    def test_behavior_cannot_be_replaced_by_a_command_with_the_same_label(self):
        spec, plan = self.normalizer()
        plan['cases'][-1].update(kind='command', command=['{python}', 'scripts/normalize.py'])
        with self.assertRaisesRegex(Invalid, 'real AI behavioral case'):
            check_plan(spec, plan, require_workflows=True)
