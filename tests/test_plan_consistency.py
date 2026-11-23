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


class AuthoredCaseReviewTests(unittest.TestCase):
    def test_impossible_or_stale_case_judgment_stops_before_assembly(self):
        from runtime.common import digest
        plan={**deepcopy(PLAN), 'package_profile':'maintained','components':[], 'authored_outputs':[{'path':p,'owner':'author','consumers':['primary']} for p in ['SKILL.md','README.md','AGENTS.md','CLAUDE.md']]}
        plan['case_review']={'reviewer':{'kind':'authored_control','identity':'test','method':'Bound rejection control'},'cases_sha256':digest(plan['cases']),'accepted':False,'evidence':'The requested boundary cannot occur under this fixture.'}
        with self.assertRaisesRegex(Invalid,'feasibility'):check_plan(SPEC,plan)
        plan['case_review']['accepted']=True
        plan['cases'][0]['stdin']={'id':'changed'}
        with self.assertRaisesRegex(Invalid,'bound to their actual bytes'):check_plan(SPEC,plan)


class ScopedOwnershipTests(unittest.TestCase):
    def test_narrow_maintenance_requires_only_authorized_root_outputs_while_full_creation_stays_strict(self):
        from runtime.common import digest
        plan={**deepcopy(PLAN),'package_profile':'maintained','components':[], 'resources':[], 'authored_outputs':[{'path':'SKILL.md','owner':'repair author','consumers':['primary']}]}
        plan['case_review']={'reviewer':{'kind':'authored_control','identity':'test','method':'Scope regression; not model performance.'},'cases_sha256':digest(plan['cases']),'accepted':True,'evidence':'Preserve frozen cases while correcting ownership scope.'}
        check_plan(SPEC,plan,required_root_outputs={'SKILL.md'})
        with self.assertRaisesRegex(Invalid,'README.md'):check_plan(SPEC,plan)
        plan['authored_outputs']=[]
        with self.assertRaisesRegex(Invalid,'SKILL.md'):check_plan(SPEC,plan,required_root_outputs={'SKILL.md'})


def current_plan(spec, assignments, decisions=None, reviewer_source='Specification requirement text'):
    """A protocol-7 normalization plan; authored control, not model performance."""
    from runtime.common import digest
    plan = deepcopy(PLAN)
    for case in plan['cases']:
        case['quality'] = {'source_clauses': case['requirements'], 'actor': 'executor', 'feasibility': 'Authored fixture.', 'input_validity': 'Controlled JSON.', 'runtime': 'Python standard library.', 'correction_obligations': []}
    plan['cases'][0]['workflow'] = {'id': 'normalize', 'scenario': 'success', 'covers': []}
    plan['cases'][3]['workflow'] = {'id': 'normalize', 'scenario': 'invalid_input', 'covers': []}
    plan['cases'].append({'id': 'native-use', 'kind': 'behavior', 'critical': True, 'semantic': True, 'requirements': ['R-1'], 'request': {'instruction': 'Normalize the supplied record.'}, 'resources': ['SKILL.md'], 'expect': {'exit_code': 0}, 'workflow': {'id': 'normalize', 'scenario': 'behavior', 'covers': []}, 'quality': deepcopy(plan['cases'][0]['quality'])})
    plan.update(package_profile='maintained', components=[], authored_outputs=[{'path': p, 'owner': 'author', 'consumers': ['primary']} for p in ['SKILL.md', 'README.md', 'AGENTS.md', 'CLAUDE.md']],
                execution={'mode': 'single', 'rationale': 'One task owner.', 'file_workflow': False, 'file_reason': 'JSON arrives on stdin.', 'bindings': [], 'document_context': {'applicable': False, 'reason': 'Synthetic fixture.', 'sources': []}})
    plan['case_review'] = {'reviewer': {'kind': 'authored_control', 'identity': 'test', 'method': 'Fixture.'}, 'cases_sha256': digest(plan['cases']), 'accepted': True, 'evidence': 'Feasible fixture.'}
    plan['assignments'] = assignments
    plan['assignment_review'] = {'reviewer': {'kind': 'authored_control', 'identity': 'plan reviewer', 'method': 'Compare each entry with its cited requirement.'},
                                 'assignments_sha256': digest(assignments),
                                 'decisions': decisions or [{'id': a['id'], 'accepted': True, 'source': reviewer_source, 'rationale': 'The entry serves its cited criterion or safeguard.'} for a in assignments]}
    return plan


class AssignmentAdmissionTests(unittest.TestCase):
    """T17: bounded assignments reach production only through admission."""

    def setUp(self):
        from fixtures import writer_fixture
        from runtime import completion
        writer_fixture(self)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        project = self.root / 'target'
        self.policy = completion.create(self.root, {'objective_id': 'assignment-control', 'goal': 'Admit bounded work.', 'project': str(project), 'scope': ['**'],
            'checks': [{'id': 'mechanical', 'kind': 'mechanical', 'test_ids': ['leading-zero', 'new-identifier', 'unicode', 'malformed', 'numeric'], 'dependencies': ['scripts/normalize.py']}, {'id': 'native-use', 'kind': 'behavior', 'dependencies': ['SKILL.md']}],
            'budget': {'runs': 3, 'revisions': 2, 'model_calls': 2, 'seconds': 600}, 'delivery': {'kind': 'local', 'authority': 'Authored test scope; no publication.'}})['policy']
        self.spec = {**deepcopy(SPEC), 'workflows': [{'id': 'normalize', 'purpose': 'Atomic transformation', 'trigger': 'Supplied JSON', 'steps': ['normalize'], 'boundaries': [], 'branches': [], 'recovery': []}]}

    def start(self, name):
        from fixtures import RESEARCH
        from runtime import workflow
        run = self.root / name
        workflow.start(run, {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'Normalize customer JSON.', 'copyright_holder': 'Fixture', 'completion_policy': self.policy}, protocol_version=7)
        for data in (RESEARCH, self.spec):
            self.submit(run, data)
        return run

    def submit(self, run, data):
        from runtime import workflow
        packet = workflow.packet(run)
        workflow.submit(run, {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)})
        return packet

    def entries(self, revision):
        base = {'governing_revision': revision, 'prerequisites': [], 'failure_behavior': 'Reject the record and report the field; never coerce an identifier.'}
        return [
            {**base, 'id': 'W1', 'outcome': 'Preserve string identifiers exactly.', 'owner_role': 'normalizer author', 'criterion': 'R-1',
             'permitted_effects': ['Edit scripts/normalize.py'], 'proof': ['Cases leading-zero and unicode pass.']},
            {**base, 'id': 'W2', 'outcome': 'Trim names and keep missing names null.', 'owner_role': 'normalizer author', 'criterion': 'R-2',
             'permitted_effects': ['Edit scripts/normalize.py'], 'proof': ['Cases leading-zero and new-identifier pass.']},
            {**base, 'id': 'W3', 'outcome': 'Reject malformed JSON and numeric identifiers.', 'owner_role': 'normalizer author', 'criterion': 'R-3',
             'permitted_effects': ['Edit scripts/normalize.py'], 'proof': ['Cases malformed and numeric exit with status 2.']},
            {**base, 'id': 'S1', 'outcome': 'Keep supplied records out of logs.', 'owner_role': 'normalizer author', 'prerequisites': ['W1'],
             'safeguard': {'rationale': 'Customer records are personal data; diagnostics must not copy them.'},
             'permitted_effects': ['Edit scripts/normalize.py'], 'proof': ['Error output names the field without the record.']},
        ]

    def test_t17a_admitted_contribution_and_safeguard_reach_the_next_work_packet(self):
        from runtime import workflow
        from runtime.artifacts import governing_revision
        run = self.start('admit')
        revision = workflow.packet(run)['governing_revision']
        self.assertEqual(revision, governing_revision(self.spec))
        submitted = self.entries(revision)
        self.submit(run, current_plan(self.spec, submitted))
        consumed = workflow.packet(run)
        self.assertEqual(consumed['phase'], 'produce')
        self.assertEqual(consumed['assignments']['entries'], submitted)
        self.assertEqual(consumed['assignments']['governing_revision'], revision)
        self.assertIn('grants no publication', consumed['assignments']['authority'])

    def test_t17b_unknown_criterion_and_unrelated_publication_stop_before_production(self):
        from runtime import workflow
        run = self.start('reject')
        revision = workflow.packet(run)['governing_revision']
        unknown = self.entries(revision)
        unknown[0]['criterion'] = 'R-9'
        with self.assertRaisesRegex(Invalid, r'unknown criterion.*"criterion": "R-9".*"row": 0'):
            self.submit(run, current_plan(self.spec, unknown))
        publish = self.entries(revision)
        publish.append({**publish[0], 'id': 'P1', 'outcome': 'Publish the customer list externally.', 'permitted_effects': ['Upload the customer list to a public site']})
        decisions = [{'id': 'W1', 'accepted': True, 'source': 'R-1', 'rationale': 'Serves R-1.'},
                     {'id': 'W2', 'accepted': True, 'source': 'R-2', 'rationale': 'Serves R-2.'},
                     {'id': 'W3', 'accepted': True, 'source': 'R-3', 'rationale': 'Serves R-3.'},
                     {'id': 'S1', 'accepted': True, 'source': 'Plan safeguard rationale', 'rationale': 'Necessary safeguard.'},
                     {'id': 'P1', 'accepted': False, 'source': 'R-1: Preserve the string identifier exactly.', 'rationale': 'Publishing records does not serve identifier preservation and no requirement authorizes it.'}]
        with self.assertRaisesRegex(Invalid, r'rejected assignment meaning.*P1.*R-1: Preserve'):
            self.submit(run, current_plan(self.spec, publish, decisions))
        self.assertEqual(workflow.read_state(run)['phase'], 'plan')

    def test_entry_without_exactly_one_authority_or_with_a_stale_revision_is_located(self):
        from runtime.artifacts import check_assignments, governing_revision
        rows = self.entries(governing_revision(self.spec))
        both = deepcopy(rows); both[-1]['criterion'] = 'R-2'
        with self.assertRaisesRegex(Invalid, r'exactly one agreed criterion.*S1'):
            check_assignments(self.spec, current_plan(self.spec, both))
        stale = deepcopy(rows); stale[0]['governing_revision'] = 'spec-sha256:old'
        with self.assertRaisesRegex(Invalid, r'different specification revision.*W1'):
            check_assignments(self.spec, current_plan(self.spec, stale))


class ReverseCoverageTests(unittest.TestCase):
    """T18: a requirement with tests but no owning work blocks complete coverage."""
    setUp = AssignmentAdmissionTests.setUp
    start = AssignmentAdmissionTests.start
    submit = AssignmentAdmissionTests.submit
    entries = AssignmentAdmissionTests.entries

    def test_t18a_orphaned_requirement_is_named_and_the_same_plan_recovers(self):
        from runtime import workflow
        run = self.start('orphan')
        revision = workflow.packet(run)['governing_revision']
        complete = self.entries(revision)
        orphaned = [row for row in complete if row.get('criterion') != 'R-3']
        plan = current_plan(self.spec, orphaned)
        self.assertIn('R-3', {r for case in plan['cases'] for r in case['requirements']})
        with self.assertRaisesRegex(Invalid, r'no owning assignment.*"R-3": \{"cases": \["malformed", "numeric"\]\}'):
            self.submit(run, plan)
        self.assertEqual(workflow.read_state(run)['phase'], 'plan')
        self.submit(run, current_plan(self.spec, complete))
        coverage = workflow.packet(run)['assignments']['coverage']
        self.assertEqual(coverage['R-3'], {'assignments': ['W3'], 'cases': ['malformed', 'numeric']})
        self.assertTrue(all(row['assignments'] for row in coverage.values()))

    def test_t18b_captured_protocol_6_plan_keeps_its_original_meaning(self):
        from fixtures import RESEARCH
        from runtime import contracts, workflow
        run = self.root / 'historical'
        workflow.start(run, {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'Normalize customer JSON.', 'copyright_holder': 'Fixture', 'completion_policy': self.policy}, protocol_version=6)
        plan = current_plan(self.spec, [])
        for field in ('assignments', 'assignment_review'):
            plan.pop(field)
        for data in (RESEARCH, self.spec, plan):
            self.submit(run, data)
        state = workflow.read_state(run)
        self.assertEqual(state['protocol_version'], 6)
        self.assertEqual(state['data']['plan'], plan)
        packet = workflow.packet(run)
        self.assertNotIn('assignments', packet)
        self.assertNotIn('assignments', packet['response_schema']['properties']['data']['properties'].get('plan', {}))
        self.assertEqual(contracts.response_schema('plan', 6)['properties']['data'], contracts.V6_PHASES['plan'])
