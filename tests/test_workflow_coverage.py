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
                'checks': [{'id': 'unit', 'kind': 'mechanical', 'dependencies': ['SKILL.md']}],
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


class NativeWorkflowCoverageTests(unittest.TestCase):
    def test_native_workflow_uses_actual_process_checks_without_invented_runtime(self):
        from runtime.artifacts import check_plan
        from runtime.common import validate,digest,Invalid
        from runtime import contracts
        flow={'id':'summary','purpose':'Summarize supplied facts','trigger':'A summary request','steps':['inspect','respond'],'boundaries':[],'branches':[],'recovery':[]}
        spec={'purpose':'Summarize supplied text','inputs':'Supplied facts','outputs':'Source-grounded bullets','requirements':[{'id':'R1','kind':'semantic','text':'Inspect source facts before responding.'},{'id':'R2','kind':'mechanical','text':'Provide a valid skill entry point.'}],'workflows':[flow],'assumptions':[],'ambiguities':[]}
        quality={'source_clauses':['R1'],'actor':'primary','feasibility':'Observe source inspection and response in actual public evidence.','input_validity':'Use supplied text or a bounded missing-input request.','runtime':'Current host native tools.','correction_obligations':[]}
        cases=[]
        for identifier,scenario,covers in [('native-success','behavior',['success']),('missing-inspection','omission',['inspect']),('premature-finish','omission',['respond']),('wrong-order','order',['inspect->respond'])]:
            cases.append({'id':identifier,'requirements':['R1'],'critical':True,'kind':'behavior','semantic':True,'request':{'instruction':'Summarize the supplied facts and preserve source limits.','source':'A bounded raw text fixture; branch variations must be source-reviewed before execution.'},'resources':['SKILL.md'],'expect':{'exit_code':0,'process':{'order':['inspect','respond'],'visible':['respond'],'evidence':['inspect','respond']}},'workflow':{'id':'summary','scenario':scenario,'covers':covers},'quality':quality})
        cases.append({'id':'entry-format','requirements':['R2'],'critical':True,'kind':'artifact','semantic':False,'expect':{'exit_code':0,'file':'SKILL.md','contains':['name: native-summary']},'quality':{**quality,'source_clauses':['R2'],'actor':'package checker'}})
        plan={'domains':[{'name':'native-summary','purpose':'Native source-grounded summaries','owned_paths':['SKILL.md'],'depends_on':[]}],'steps':['Inspect','Respond'],'automations':[],'ai_responsibilities':['Interpret facts and judge the summary.'],'dependencies':[],'resources':[],'cases':cases,'target_success_percent':100,'allowed_candidate_paths':['SKILL.md'],'execution':{'mode':'single','rationale':'One native task owner suffices.','file_workflow':False,'file_reason':'Inputs arrive as text.','bindings':[],'document_context':{'applicable':False,'reason':'No governing project documents.','sources':[]}},'authored_outputs':[{'path':name,'owner':'author','consumers':['primary']} for name in ['SKILL.md','README.md','AGENTS.md','CLAUDE.md']],'components':[],'package_profile':'native','case_review':{'reviewer':{'kind':'authored_control','identity':'test','method':'Schema/coverage control only; no AI observation is claimed.'},'cases_sha256':digest(cases),'accepted':True,'evidence':'Mechanical plan-acceptance fixture; actual scenario meaning and public process require separate review.'}}
        validate(plan,contracts.V6_PHASES['plan']);check_plan(spec,plan,require_workflows=True)
        self.assertEqual(plan['components'],[])
        del cases[0]['expect']['process'];plan['case_review']['cases_sha256']=digest(cases)
        with self.assertRaisesRegex(Invalid,'actual process evidence'):check_plan(spec,plan,require_workflows=True)


DECIDE = {'id': 'decide', 'purpose': 'Decide after reading the brief and example.', 'trigger': 'A decision request with a brief and an example.',
          'steps': ['read_brief', 'read_example', 'decide'], 'requires': {'decide': ['read_brief', 'read_example']},
          'boundaries': [], 'branches': [], 'recovery': []}
DECIDE_PROGRAM = '''import json, sys
order = sys.argv[1:] or ['read_example', 'read_brief', 'decide']
print(json.dumps({'provenance': {'kind': 'authored_control', 'source': 'Generated-package control, not model behavior.'},
                  'events': [{'phase': p, 'evidence': 'control:' + p, 'visible': p == 'decide'} for p in order]}))
'''


class DeclaredDependencyGenerationTests(unittest.TestCase):
    """T25: authoring emits only declared prerequisites and the generated evaluator honors them."""

    def setUp(self):
        from runtime import completion
        writer_fixture(self)
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.spec = {**deepcopy(SPEC), 'workflows': [deepcopy(DECIDE)]}
        self.plan = self.dependency_plan()
        mechanical = [c['id'] for c in self.plan['cases'] if c['kind'] != 'behavior']
        self.policy = completion.create(self.root, {'objective_id': 'dependency-control', 'goal': 'Generate declared dependency checks.', 'project': str(self.root / 'target'), 'scope': ['**'],
            'checks': [{'id': 'mechanical', 'kind': 'mechanical', 'test_ids': mechanical, 'dependencies': ['scripts/decide.py']}, {'id': 'decide-use', 'kind': 'behavior', 'dependencies': ['SKILL.md']}],
            'budget': {'runs': 4, 'revisions': 2, 'model_calls': 2, 'seconds': 600}, 'delivery': {'kind': 'local', 'authority': 'Authored test scope; no publication.'}})['policy']

    def dependency_plan(self):
        from runtime.common import digest
        quality = {'source_clauses': ['R-1'], 'actor': 'executor', 'feasibility': 'Authored control.', 'input_validity': 'Controlled order arguments.', 'runtime': 'Python standard library.', 'correction_obligations': []}
        plan = deepcopy(PLAN)
        for case in plan['cases']:
            case['quality'] = deepcopy(quality)
        def flow_case(identifier, scenario, covers, argv):
            return {'id': identifier, 'requirements': ['R-1'], 'critical': True, 'kind': 'command', 'command': ['{python}', 'scripts/decide.py', *argv],
                    'expect': {'exit_code': 0}, 'semantic': False, 'timeout_seconds': 5, 'workflow': {'id': 'decide', 'scenario': scenario, 'covers': covers}, 'quality': deepcopy(quality)}
        success = flow_case('decide-either-read-order', 'success', [], [])
        success.update(semantic=True)
        success['expect']['process'] = {'order': DECIDE['steps'], 'requires': DECIDE['requires'], 'visible': ['decide'], 'evidence': DECIDE['steps']}
        plan['cases'] += [success] + [flow_case('omit-' + s, 'omission', [s], [p for p in DECIDE['steps'] if p != s]) for s in DECIDE['steps']] + [
            flow_case('early-after-' + b, 'order', [b + '->decide'], []) for b in ('read_brief', 'read_example')]
        plan['cases'].append({'id': 'decide-use', 'kind': 'behavior', 'critical': True, 'semantic': True, 'requirements': ['R-1'], 'request': {'instruction': 'Decide from the supplied brief and example.'},
                              'resources': ['SKILL.md'], 'expect': {'exit_code': 0}, 'workflow': {'id': 'decide', 'scenario': 'behavior', 'covers': []}, 'quality': deepcopy(quality)})
        reason = 'Distributed evaluator and its supported dependencies.'
        plan.update(package_profile='maintained', authored_outputs=[{'path': p, 'owner': 'author', 'consumers': ['primary']} for p in ['SKILL.md', 'README.md', 'AGENTS.md', 'CLAUDE.md']],
                    components=[{'path': 'scripts/normalize.py', 'requirements': ['R-1', 'R-2', 'R-3'], 'reason': 'Planned transformation.'},
                                {'path': 'scripts/decide.py', 'requirements': ['R-1'], 'reason': 'Emits the decision trace.'}] +
                               [{'path': p, 'requirements': ['R-1'], 'reason': reason} for p in ('scripts/evaluate.py', 'scripts/continuation.py', 'scripts/repository_files.py', 'scripts/case_inputs.py')],
                    execution={'mode': 'single', 'rationale': 'One task owner.', 'file_workflow': False, 'file_reason': 'Inputs arrive as arguments.', 'bindings': [], 'document_context': {'applicable': False, 'reason': 'Synthetic fixture.', 'sources': []}},
                    allowed_candidate_paths=['scripts/normalize.py', 'scripts/decide.py'])
        plan['domains'][0]['owned_paths'] = ['scripts/normalize.py', 'scripts/decide.py']
        plan['case_review'] = {'reviewer': {'kind': 'authored_control', 'identity': 'test', 'method': 'Fixture.'}, 'cases_sha256': digest(plan['cases']), 'accepted': True, 'evidence': 'Feasible fixture.'}
        return plan

    def start(self, name, spec):
        run = self.root / name
        workflow.start(run, {'operation': 'create', 'skill_name': 'decide-control', 'brief': 'Decide after both reads.', 'copyright_holder': 'Fixture', 'completion_policy': self.policy}, protocol_version=7)
        self.submit(run, RESEARCH)
        self.submit(run, spec)
        return run

    def submit(self, run, data):
        packet = workflow.packet(run)
        workflow.submit(run, {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)})
        return packet

    def test_t25a_emitted_case_requires_both_reads_and_the_generated_evaluator_accepts_either_order(self):
        from runtime.artifacts import execution_logging_rules
        from runtime.common import digest
        run = self.start('generate', self.spec)
        packet = workflow.packet(run)
        self.assertEqual(packet['required_workflow_tests']['decide'], ['behavior', 'omission:decide', 'omission:read_brief', 'omission:read_example',
                                                                         'order:read_brief->decide', 'order:read_example->decide', 'success'])
        revision = packet['governing_revision']
        plan = deepcopy(self.plan)
        plan['assignments'] = [{'id': 'W' + r[-1], 'outcome': 'Deliver ' + r, 'owner_role': 'author', 'criterion': r, 'governing_revision': revision, 'prerequisites': [],
                                'permitted_effects': ['Edit scripts/decide.py and scripts/normalize.py'], 'failure_behavior': 'Report the failed case.', 'proof': ['Its frozen cases pass.']} for r in ('R-1', 'R-2', 'R-3')]
        plan['assignment_review'] = {'reviewer': {'kind': 'authored_control', 'identity': 'plan reviewer', 'method': 'Fixture.'}, 'assignments_sha256': digest(plan['assignments']),
                                     'decisions': [{'id': a['id'], 'accepted': True, 'source': a['criterion'], 'rationale': 'Serves its criterion.'} for a in plan['assignments']]}
        self.submit(run, plan)
        rules = execution_logging_rules(); text = '# Fixture guide\n\nA protocol control only.\n'
        produced = {**deepcopy(PRODUCE), 'files': {'scripts/normalize.py': PRODUCE['files']['scripts/normalize.py'], 'scripts/decide.py': DECIDE_PROGRAM},
                    'instructions': 'Use scripts/decide.py and follow AGENTS.md.', 'repository_instructions': '# Repository instructions\n\n' + rules,
                    'documentation': {'schema_version': 2, 'owner': 'author', 'profiles': {'source': text, 'runtime': text}, 'commands': []},
                    'execution_logging': {'mode': 'host_public', 'owner': 'host', 'record_location': 'Task public tool history', 'rules_sha256': digest(rules.encode())}}
        self.submit(run, produced)
        candidate = run / 'candidate'
        emitted = next(c for c in json.loads((candidate / 'evals/cases.json').read_text()) if c['id'] == 'decide-either-read-order')
        self.assertEqual(emitted['expect']['process']['requires'], {'decide': ['read_brief', 'read_example']})
        result = subprocess.run([sys.executable, 'scripts/evaluate.py', '--package', '.', '--allow-exec', '--case', 'decide-either-read-order'], cwd=candidate, capture_output=True, text=True)
        verdict = json.loads(result.stdout)['attempts'][0]
        self.assertEqual(verdict['process']['observed_order'], ['read_example', 'read_brief', 'decide'])
        self.assertTrue(verdict['process']['passed'], verdict)

    def test_t25b_invalid_relations_stop_at_admission_and_legacy_declarations_stay_strict(self):
        for requires, message in (({'decide': ['read_brief'], 'read_brief': ['decide']}, 'cycle: read_brief -> decide -> read_brief'),
                                  ({'decide': ['read_brief', 'read_notes']}, "Unknown prerequisite 'read_notes' for step 'decide'")):
            spec = deepcopy(self.spec); spec['workflows'][0]['requires'] = requires
            with self.subTest(requires=requires), self.assertRaisesRegex(Invalid, 'invalid dependency relation.*' + message):
                self.start('invalid-' + str(len(requires)), spec)
        strict = {key: value for key, value in DECIDE.items() if key != 'requires'}
        self.assertIn('order:read_brief->read_example', workflow_requirements({'workflows': [strict]})['decide'])
        with self.assertRaises(Invalid):
            validate({'run_id': 'r', 'phase': 'specify', 'packet_sha256': 'a' * 64, 'data': self.spec}, contracts.response_schema('specify', 6))
