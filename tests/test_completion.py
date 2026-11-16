"""Executed local policy controls; no model-performance observations are fabricated."""
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
from runtime import completion, workflow
from runtime.common import Invalid, digest, inventory, load, save
import run_tests
from fixtures import RESEARCH, writer_fixture


class CompletionTests(unittest.TestCase):
    def setUp(self):
        writer_fixture(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.project = self.workspace / 'project'
        self.project.mkdir()
        (self.project / 'run.py').write_text('assert 2 * 3 == 6\nprint("checked")\n')
        (self.project / 'notes.md').write_text('Original guide.\n')
        (self.project / 'config').mkdir()
        save(self.project / 'config/test_impact.json', {'schema_version': 1,
             'tests': {'unit': {'argv': ['{python}', 'run.py']}},
             'rules': [{'paths': ['run.py'], 'tests': ['unit']}],
             'final_checks': {'unit': {'argv': ['{python}', 'run.py']}}})
        self.definition = {'objective_id': 'policy-control', 'goal': 'Verify a bounded local change.',
             'project': str(self.project), 'scope': ['run.py', 'notes.md'],
             'checks': [{'id': 'unit', 'kind': 'mechanical', 'dependencies': ['run.py', 'config/test_impact.json']}],
             'budget': {'runs': 2, 'revisions': 2, 'model_calls': 2, 'seconds': 600},
             'delivery': {'kind': 'local', 'authority': 'Authored test scope; no user publication.'}}

    def policy(self, **changes):
        definition = deepcopy(self.definition)
        definition.update(changes)
        return Path(completion.create(self.workspace, definition)['policy'])

    def request(self, policy, **changes):
        value = {'operation': 'modify', 'source': str(self.project), 'skill_name': 'policy-control',
                 'brief': 'Make the agreed bounded change.', 'allowed_paths': ['run.py'],
                 'completion_policy': str(policy)}
        value.update(changes)
        return value

    def evidence(self):
        report = run_tests.execute(run_tests.plan(self.project, ['run.py']))
        self.assertTrue(report['passed'])
        path = self.workspace / ('executed-' + digest(report) + '.json')
        save(path, report)
        return path

    def test_unrelated_executed_selection_cannot_satisfy_a_required_check(self):
        policy = self.policy()
        config = load(self.project / 'config/test_impact.json')
        config['tests']['unrelated'] = {'argv': ['{python}', '-c', 'print("unrelated")']}
        config['rules'].append({'paths': ['notes.md'], 'tests': ['unrelated']})
        save(self.project / 'config/test_impact.json', config)
        report = run_tests.execute(run_tests.plan(self.project, ['notes.md']))
        evidence = self.workspace / 'unrelated.json'; save(evidence, report)
        with self.assertRaisesRegex(Invalid, 'required test selection'):
            completion.record(policy, 'unit', self.project, evidence)
        self.assertEqual(completion.read(policy)['phase'], 'working')
        completion.record(policy, 'unit', self.project, self.evidence())
        self.assertEqual(completion.read(policy)['phase'], 'delivery_pending')

    def test_host_task_binding_and_retained_raw_trace(self):
        from test_host_coverage import HostCoverageTests
        import host_coverage
        fixture = HostCoverageTests(); fixture.setUp(); self.addCleanup(fixture.doCleanups)
        expected = deepcopy(fixture.case)
        policy = self.policy(project=str(fixture.package), checks=[{'id': 'audit', 'kind': 'behavior', 'dependencies': ['SKILL.md']}])
        completion.authorize_case(policy, 'audit', fixture.package, case=expected)
        fixture.case['request'] = {'instruction': 'A different task with the same case id.'}
        save(fixture.package / 'evals/cases.json', [fixture.case])
        manifest = self.workspace / 'host-manifest.json'; plan = self.workspace / 'host-plan.json'; bundles = self.workspace / 'host-bundles.json'
        save(plan, host_coverage.freeze(fixture.package, fixture.config))
        save(bundles, [fixture.bundle('codex', name='wrong-codex'), fixture.bundle('claude-code', name='wrong-claude')])
        save(manifest, {'plan': str(plan), 'bundles': str(bundles)})
        with self.assertRaisesRegex(Invalid, 'frozen authorized task'):
            completion.record_hosts(policy, fixture.package, manifest)
        fixture.case = expected; save(fixture.package / 'evals/cases.json', [expected])
        save(plan, host_coverage.freeze(fixture.package, fixture.config))
        valid = [fixture.bundle('codex', name='valid-codex'), fixture.bundle('claude-code', name='valid-claude')]
        save(bundles, valid)
        result = completion.record_hosts(policy, fixture.package, manifest)
        self.assertTrue(result['checks'][0]['valid'])
        events = Path(valid[0]['report']).parent / '001-audit/public-events.json'
        events.write_text('[]')
        self.assertFalse(completion.status(policy, fixture.package)['checks'][0]['valid'])
        with self.assertRaises(Invalid):
            completion.delivered(policy, fixture.package)

    def test_git_delivery_requires_exact_committed_and_pushed_artifact(self):
        remote = self.workspace / 'local-remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        subprocess.run(['git', '-C', str(self.project), 'init', '-q'], check=True)
        policy = self.policy(delivery={'kind': 'git_push', 'authority': 'Authored local Git control only.',
                                      'remote': str(remote), 'ref': 'refs/heads/policy-control'})
        completion.record(policy, 'unit', self.project, self.evidence())
        subprocess.run(['git', '-C', str(self.project), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.project), '-c', 'user.name=Authored control', '-c', 'user.email=control@example.invalid', 'commit', '-qm', 'Authored test artifact'], check=True)
        with self.assertRaisesRegex(Invalid, 'remote branch'):
            completion.delivered(policy, self.project)
        subprocess.run(['git', '-C', str(self.project), 'push', '-q', str(remote), 'HEAD:refs/heads/policy-control'], check=True)
        self.assertEqual(completion.delivered(policy, self.project)['phase'], 'delivered')

    def test_new_protocol_cannot_start_without_policy(self):
        with self.assertRaises(Invalid):
            workflow.start(self.workspace / 'run', {'operation': 'create', 'skill_name': 'x', 'brief': 'Do work.'})

    def test_new_run_directories_share_one_budget(self):
        definition = deepcopy(self.definition)
        definition['budget']['runs'] = 1
        policy = self.policy(budget=definition['budget'])
        workflow.start(self.workspace / 'v1', self.request(policy))
        with self.assertRaisesRegex(Invalid, 'runs budget'):
            workflow.start(self.workspace / 'v2', self.request(policy))
        self.assertEqual(completion.read(policy)['usage']['runs'], 1)

    def test_new_objective_id_cannot_reset_unfinished_project(self):
        policy = self.policy()
        completion.reserve(policy, 'model_calls', detail='controlled reservation')
        changed = deepcopy(self.definition); changed['objective_id'] = 'new-version-name'
        with self.assertRaisesRegex(Invalid, 'unfinished objective'):
            completion.create(self.workspace, changed)
        self.assertEqual(completion.read(policy)['usage']['model_calls'], 1)

    def test_scope_and_goal_cannot_expand_through_new_start(self):
        policy = self.policy()
        workflow.start(self.workspace / 'v1', self.request(policy))
        for change in ({'allowed_paths': ['unrelated.py']}, {'brief': 'Also implement a new product.'}):
            with self.subTest(change=change), self.assertRaises(Invalid):
                workflow.start(self.workspace / 'v2', self.request(policy, **change))
        self.assertEqual(completion.read(policy)['usage']['runs'], 1)

    def test_time_budget_survives_new_run(self):
        policy = self.policy()
        created = completion.read(policy)['created_unix']
        with patch.object(completion.time, 'time', return_value=created + 601):
            with self.assertRaisesRegex(Invalid, 'time budget'):
                workflow.start(self.workspace / 'later', self.request(policy))
        self.assertEqual(completion.read(policy)['usage']['runs'], 0)

    def test_contract_and_definition_of_done_cannot_drift(self):
        policy = self.policy()
        state = {'completion': {'path': str(policy)}, 'request': {'operation': 'modify'}}
        spec = {'requirements': [{'id': 'R1', 'text': 'Bounded task.'}]}
        plan = {'cases': [{'id': 'unit'}], 'steps': ['Do the task.']}
        completion.freeze_plan(state, spec, plan)
        altered = deepcopy(plan); altered['steps'].append('Add another feature.')
        with self.assertRaisesRegex(Invalid, 'frozen requirements'):
            completion.freeze_plan(state, spec, altered)
        altered = deepcopy(self.definition); altered['checks'].append({'id': 'extra', 'kind': 'mechanical', 'dependencies': ['run.py']})
        with self.assertRaisesRegex(Invalid, 'unfinished objective'):
            completion.create(self.workspace, altered)

    def test_small_guide_edit_retains_exact_unchanged_code_evidence(self):
        policy = self.policy()
        completion.record(policy, 'unit', self.project, self.evidence())
        (self.project / 'notes.md').write_text('Corrected one guide sentence.\n')
        result = completion.status(policy, self.project)['checks'][0]
        self.assertTrue(result['valid'])
        self.assertEqual(result['action'], 'retain_evidence')
        self.assertFalse(result['fresh_current_artifact'])
        (self.project / 'run.py').write_text('print("changed runtime")\n')
        self.assertFalse(completion.status(policy, self.project)['checks'][0]['valid'])

    def test_evidence_changes_invalidate_a_receipt(self):
        policy = self.policy(); evidence = self.evidence()
        completion.record(policy, 'unit', self.project, evidence)
        evidence.write_text('{}\n')
        self.assertFalse(completion.status(policy, self.project)['checks'][0]['valid'])
        with self.assertRaises(Invalid):completion.delivered(policy, self.project)

    def test_new_broad_model_case_is_rejected_before_reservation(self):
        policy = self.policy()
        with self.assertRaisesRegex(Invalid, 'outside the frozen'):
            completion.authorize_case(policy, 'unrelated-full-benchmark', self.project)
        self.assertEqual(completion.read(policy)['usage']['model_calls'], 0)

    def test_model_budget_and_task_binding_are_cumulative(self):
        policy = self.policy(checks=[{'id': 'review', 'kind': 'behavior', 'dependencies': ['run.py']}])
        case = {'kind': 'behavior', 'critical': True, 'semantic': True, 'request': {'instruction': 'Review only.'}, 'resources': ['run.py'], 'expect': {'exit_code': 0}}
        completion.authorize_case(policy, 'review', self.project, case=case)
        different = deepcopy(case); different['request']['instruction'] = 'Implement instead.'
        with self.assertRaisesRegex(Invalid, 'criteria changed'):
            completion.authorize_case(policy, 'review', self.project, case=different)
        completion.authorize_case(policy, 'review', self.project, case=case)
        with self.assertRaisesRegex(Invalid, 'model_calls budget'):
            completion.authorize_case(policy, 'review', self.project, case=case)
        self.assertEqual(completion.read(policy)['usage']['model_calls'], 2)

    def test_summary_flags_do_not_approve_behavior(self):
        policy = self.policy(checks=[{'id': 'review', 'kind': 'behavior', 'dependencies': ['run.py']}])
        with self.assertRaisesRegex(Invalid, 'semantic-review gate'):
            completion.record(policy, 'review', self.project, self.evidence())

    def test_followups_do_not_reopen_delivery_and_blockers_need_requirement(self):
        policy = self.policy()
        state = {'completion': {'path': str(policy)}, 'request': {'operation': 'modify'}}
        completion.freeze_plan(state, {'requirements': [{'id': 'R1', 'text': 'Do the task.'}]}, {'cases': [{'id': 'unit'}]})
        completion.record(policy, 'unit', self.project, self.evidence())
        completion.finding(policy, 'follow_up', '', 'Consider a future cleanup.')
        self.assertEqual(completion.read(policy)['phase'], 'delivery_pending')
        with self.assertRaisesRegex(Invalid, 'agreed requirement'):
            completion.finding(policy, 'blocker', 'new-goal', 'Unrelated improvement.', ['unit'])
        completion.finding(policy, 'blocker', 'R1', 'Located required regression.', ['unit'])
        self.assertEqual(completion.read(policy)['phase'], 'working')
        self.assertFalse(completion.status(policy, self.project)['checks'][0]['valid'])

    def test_delivery_boundary_blocks_more_runs_revisions_and_model_calls(self):
        policy = self.policy()
        completion.record(policy, 'unit', self.project, self.evidence())
        for unit in ('runs', 'revisions', 'model_calls'):
            with self.subTest(unit=unit), self.assertRaisesRegex(Invalid, 'Deliver now'):
                completion.reserve(policy, unit, detail='unnecessary improvement')
        completion.delivered(policy, self.project)
        self.assertEqual(completion.read(policy)['phase'], 'delivered')

    def test_explicit_replan_keeps_counts_clock_and_history(self):
        policy = self.policy()
        completion.reserve(policy, 'revisions', detail='first version')
        original = completion.read(policy)
        amended = deepcopy(self.definition); amended['scope'].append('new.py'); amended['budget']['revisions'] = 3
        with self.assertRaises(Invalid):completion.amend(policy, amended, '')
        completion.amend(policy, amended, 'Actual new user scope instruction in this authored control.')
        current = completion.read(policy)
        self.assertEqual(current['usage'], original['usage'])
        self.assertEqual(current['created_unix'], original['created_unix'])
        self.assertEqual(current['amendments'][0]['previous_sha256'], original['contract_sha256'])

    def test_real_cli_readonly_objective_reaches_delivery_without_batch_approval(self):
        (self.project / 'SKILL.md').write_text('---\nname: policy-control\ndescription: Authored audit fixture.\n---\nInspect supplied facts.\n')
        policy = self.policy(checks=[{'id': 'audit-result', 'kind': 'report', 'dependencies': []}],
                             delivery={'kind': 'report', 'authority': 'Read-only authored fixture.'})
        request = self.request(policy, operation='audit'); request.pop('allowed_paths')
        run = self.workspace / 'audit-run'
        workflow.start(run, request)
        for data in (RESEARCH, {'recommendation': 'retain', 'rationale': 'Authored read-only transport control; no defect or model-quality claim.', 'findings': [], 'dimensions': [{'dimension': d, 'status':'compliant', 'evidence':'Authored read-only gate control; no semantic performance claim.', 'repair':'Retain.', 'preservation':'Keep source bytes.', 'regression':'This read-only transport check.'} for d in ('authorship_execution','over_engineering','over_testing','over_validation','avoidable_complexity')]}):
            packet = workflow.packet(run)
            workflow.submit(run, {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)})
        self.assertEqual(completion.read(policy)['phase'], 'delivery_pending')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'completion-delivered', '--policy', str(policy), '--package', str(self.project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['phase'], 'delivered')


class IncrementalCompletionTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy
    evidence = CompletionTests.evidence
    def test_checkpoint_opens_dependent_work_without_waiving_final_checks(self):
        checks = [*self.definition['checks'], {'id':'final-doc','kind':'document','dependencies':['notes.md']}]
        policy = self.policy(checks=checks, checkpoints=[{'id':'code','checks':['unit'],'depends_on':[],'lessons':['existing-repair']}, {'id':'docs','checks':['final-doc'],'depends_on':['code'],'lessons':[]}])
        with self.assertRaisesRegex(Invalid, 'missing'):
            completion.checkpoint(policy, 'code', self.project, ['existing-repair'])
        with self.assertRaisesRegex(Invalid, 'dependency'):
            completion.component_eligible(completion.read(policy), 'docs', self.project)
        completion.record(policy, 'unit', self.project, self.evidence())
        with self.assertRaisesRegex(Invalid, 'lessons'):
            completion.checkpoint(policy, 'code', self.project, [])
        current = completion.checkpoint(policy, 'code', self.project, ['existing-repair'])
        self.assertEqual(current['phase'], 'working')
        self.assertFalse(next(c for c in current['checks'] if c['id']=='final-doc')['valid'])
        completion.component_eligible(completion.read(policy), 'docs', self.project)
        (self.project/'run.py').write_text('changed')
        with self.assertRaisesRegex(Invalid, 'dependency'):
            completion.component_eligible(completion.read(policy), 'docs', self.project)

    def test_real_wait_excludes_wait_time_and_keeps_usage_and_wall_cap(self):
        policy = self.policy(budget={**self.definition['budget'],'wall_seconds': 900})
        created = completion.read(policy)['created_unix']
        with patch.object(completion.time, 'time', return_value=created+10):
            completion.reserve(policy, 'revisions', detail='active failure')
            completion.user_wait(policy, 'decision', ['unit'], 'The task requires a user scope decision.')
        with patch.object(completion.time, 'time', return_value=created+700):
            state = completion.read(policy)
            self.assertEqual(completion.elapsed(state)['active_seconds'], 10)
            with self.assertRaises(Invalid):
                completion.user_resume(policy, 'decision', {'origin':'source','instruction':'Approved','message_reference':'quoted file'})
            completion.user_resume(policy, 'decision', {'origin':'user','instruction':'Approved this scope','message_reference':'actual fixture user message'})
            self.assertEqual(completion.read(policy)['usage']['revisions'], 1)
        with patch.object(completion.time, 'time', return_value=created+901), self.assertRaisesRegex(Invalid, 'wall-clock'):
            completion.reserve(policy, 'revisions', detail='late')


class ActiveWaitAccountingTests(unittest.TestCase):
    def test_independent_active_failure_is_not_charged_as_waiting(self):
        state={'created_unix':0,'user_gates':[{'started_unix':10,'resumed_unix':None}], 'activity_intervals':[{'checkpoint':'independent','started_unix':20,'ended_unix':40}]}
        measured=completion.elapsed(state,now=100)
        self.assertEqual(measured,{'wall_seconds':100,'waiting_seconds':70,'active_seconds':30})


class NativeCheckBindingTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy

    def test_declared_group_members_freeze_and_only_complete_results_accept(self):
        policy=self.policy(checks=[{'id':'group','kind':'mechanical','test_ids':['case-a','case-b'],'dependencies':['run.py']}])
        state={'completion':{'path':str(policy)},'request':{'operation':'create'},'run_id':'authored-native-control','source':str(self.project),'data':{},'phase':'review'}
        spec={'requirements':[]};plan={'cases':[{'id':'case-a','kind':'command'},{'id':'case-b','kind':'artifact'}],'allowed_candidate_paths':['run.py']}
        with self.assertRaisesRegex(Invalid,'outside the frozen') as failure:
            completion.freeze_plan(state,spec,{**plan,'cases':[*plan['cases'],{'id':'unplanned','kind':'command'}]})
        self.assertIn('"unbound_case_ids": ["unplanned"]', str(failure.exception))
        self.assertIn('The plan was not frozen', str(failure.exception))
        with self.assertRaisesRegex(Invalid,'invalid mechanical completion_check'):
            completion.freeze_plan(state,spec,{**plan,'cases':[{'id':'unplanned','kind':'command','completion_check':'group'}]})
        completion.freeze_plan(state,spec,plan)
        run=self.workspace/'native-run';run.mkdir()
        state['evaluation']={'package_hashes':inventory(self.project),'attempts':[{'id':'case-a','status':'passed'},{'id':'case-b','status':'not_run'}]}
        completion.sync_native(run,state);self.assertFalse(completion.status(policy,self.project)['checks'][0]['valid'])
        state['evaluation']['attempts'][1]['status']='passed'
        completion.sync_native(run,state);self.assertTrue(completion.status(policy,self.project)['checks'][0]['valid'])

    def test_artifact_result_cannot_substitute_for_document_acceptance(self):
        policy=self.policy(checks=[{'id':'doc-case','kind':'document','dependencies':['notes.md']}])
        state={'completion':{'path':str(policy)},'request':{'operation':'create'},'run_id':'authored-document-control','source':str(self.project),'data':{},'phase':'review','document_check':{'passed':False},'evaluation':{'package_hashes':inventory(self.project),'attempts':[{'id':'doc-case','status':'passed'}]}}
        run=self.workspace/'document-run';run.mkdir()
        completion.sync_native(run,state)
        self.assertFalse(completion.status(policy,self.project)['checks'][0]['valid'])


class PlanningRecoveryTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy
    request = CompletionTests.request
    def test_phase_correction_retains_checkpoint_history_and_budget_and_rejects_stale_packets(self):
        from fixtures import SPEC
        policy = self.policy()
        run = self.workspace / 'recoverable-run'
        state = workflow.start(run, self.request(policy, limits={'max_experiments': 2}))
        def submit(data):
            packet = workflow.packet(run)
            response = {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)}
            workflow.submit(run, response)
            return response
        submit(RESEARCH)
        spec = {**deepcopy(SPEC), 'workflows': [{'id':'transform', 'purpose':'One atomic transformation', 'trigger':'A supplied record', 'steps':['transform'], 'boundaries':[], 'branches':[], 'recovery':[]}]}
        original = submit(spec)
        records = {p.name:p.read_bytes() for p in (run/'responses').glob('*.json')}
        before = completion.read(policy)
        fixed = workflow.revise(run, 'Correct the workflow definition; preserve accepted research.', phase='specify')
        self.assertEqual(fixed['run_id'], state['run_id'])
        self.assertEqual(fixed['data'], {'research':RESEARCH})
        self.assertEqual(fixed['source_snapshot'], state['source_snapshot'])
        self.assertEqual({p.name:p.read_bytes() for p in (run/'responses').glob('*.json')}, records)
        self.assertEqual(completion.read(policy)['usage'], {**before['usage'], 'revisions':1})
        self.assertEqual(completion.read(policy)['created_unix'], before['created_unix'])
        with self.assertRaisesRegex(Invalid,'superseded'):workflow.submit(run, original)
        with self.assertRaisesRegex(Invalid,'Experiment limit'):workflow.revise(run, 'Repeat unchanged work.', phase='specify')
        submit(spec)
        completion.freeze_plan(workflow.read_state(run), spec, {'cases':[{'id':'unit','kind':'command'}]})
        with self.assertRaisesRegex(Invalid,'already frozen'):workflow.revise(run, 'Change accepted criteria.', phase='specify')

    def test_explicit_mechanical_group_membership_freezes_once_and_requires_every_case(self):
        policy = self.policy(checks=[{'id':'normalization','kind':'mechanical','dependencies':['run.py']}])
        state={'completion':{'path':str(policy)}, 'request':{'operation':'create'}, 'run_id':'group-control', 'source':str(self.project), 'data':{}, 'phase':'review'}
        cases=[{'id':name,'kind':'command','completion_check':'normalization'} for name in ['positive','reject-invalid']]
        plan={'cases':cases, 'allowed_candidate_paths':['run.py']}
        completion.freeze_plan(state, {'requirements':[]}, plan)
        with self.assertRaisesRegex(Invalid,'frozen requirements'):
            completion.freeze_plan(state, {'requirements':[]}, {**plan,'cases':[*cases,{'id':'extra','kind':'command','completion_check':'normalization'}]})
        run=self.workspace/'group-run';run.mkdir()
        state['evaluation']={'package_hashes':inventory(self.project),'attempts':[{'id':'positive','status':'passed'},{'id':'reject-invalid','status':'not_run'}]}
        completion.sync_native(run,state);self.assertFalse(completion.status(policy,self.project)['checks'][0]['valid'])
        state['evaluation']['attempts'][1]['status']='passed'
        completion.sync_native(run,state);self.assertTrue(completion.status(policy,self.project)['checks'][0]['valid'])


class FrozenMetadataRecoveryTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy

    def test_missing_component_metadata_can_be_corrected_without_changing_cases_or_restarting(self):
        from fixtures import SPEC, PLAN, PROGRAM, PRODUCE
        from runtime.artifacts import execution_logging_rules
        from skill_builder_cli import replay
        spec={**deepcopy(SPEC),'workflows':[{'id':'normalize','purpose':'Atomic transformation','trigger':'Supplied JSON','steps':['normalize'],'boundaries':[],'branches':[],'recovery':[]}]}
        plan=deepcopy(PLAN)
        for case in plan['cases']:
            case['quality']={'source_clauses':case['requirements'],'actor':'executor','feasibility':'Authored state-machine fixture, not model performance.','input_validity':'Controlled JSON or deliberate malformed input.','runtime':'Python standard library.','correction_obligations':[]}
        plan['cases'][0]['workflow']={'id':'normalize','scenario':'success','covers':[]}
        plan['cases'][3]['workflow']={'id':'normalize','scenario':'invalid_input','covers':[]}
        behavior={'id':'native-use','kind':'behavior','critical':True,'semantic':True,'requirements':['R-1'],'request':{'instruction':'Use the supplied normalizer and report actual output.'},'resources':['SKILL.md'],'expect':{'exit_code':0},'workflow':{'id':'normalize','scenario':'behavior','covers':[]},'quality':deepcopy(plan['cases'][0]['quality'])}
        plan['cases'].append(behavior)
        plan.update(package_profile='maintained',components=[],authored_outputs=[{'path':p,'owner':'author','consumers':['primary']} for p in ['SKILL.md','README.md','AGENTS.md','CLAUDE.md']],execution={'mode':'single','rationale':'One task owner.','file_workflow':False,'file_reason':'JSON arrives on stdin.','bindings':[],'document_context':{'applicable':False,'reason':'Synthetic protocol fixture.','sources':[]}})
        plan['case_review']={'reviewer':{'kind':'authored_control','identity':'test','method':'State-machine control only.'},'cases_sha256':digest(plan['cases']),'accepted':True,'evidence':'Feasible fixture; no actual model result is claimed.'}
        target=self.workspace/'target'
        policy=self.policy(project=str(target),scope=['**'],checks=[{'id':'mechanical','kind':'mechanical','test_ids':[c['id'] for c in plan['cases'] if c['kind']!='behavior'],'dependencies':['scripts/normalize.py']},{'id':'native-use','kind':'behavior','dependencies':['SKILL.md']}])
        run=self.workspace/'run'
        state=workflow.start(run,{'operation':'create','skill_name':'normalize-customers','brief':'Verify bounded metadata correction.','copyright_holder':'Fixture','completion_policy':str(policy)})
        def submit(data):
            packet=workflow.packet(run)
            response={**{k:packet[k] for k in ['run_id','phase','packet_sha256']},'data':deepcopy(data)}
            workflow.submit(run,response)
            return response
        submit(RESEARCH);submit(spec);original=submit(plan)
        original_cases=digest(plan['cases']);original_run=state['run_id']
        workflow.revise(run,'Declare the already planned normalization executable.',phase='plan')
        corrected=deepcopy(plan);corrected['components']=[{'path':'scripts/normalize.py','requirements':['R-1','R-2','R-3'],'reason':'The already planned deterministic transformation.'}]
        with self.assertRaisesRegex(Invalid,'superseded'):workflow.submit(run,original)
        changed=deepcopy(corrected);changed['target_success_percent']=99
        with self.assertRaisesRegex(Invalid,'Frozen plan criteria'):submit(changed)
        changed=deepcopy(corrected);changed['components'][0]['path']='unplanned.py'
        with self.assertRaisesRegex(Invalid,'unplanned output'):submit(changed)
        submit(corrected)
        current=workflow.read_state(run)
        self.assertEqual(current['run_id'],original_run)
        self.assertEqual(digest(current['data']['plan']['cases']),original_cases)
        self.assertEqual(completion.read(policy)['usage']['runs'],1)
        self.assertEqual(completion.read(policy)['usage']['revisions'],1)
        rules=execution_logging_rules();text='# Fixture guide\n\nA protocol control only.\n'
        produced={**deepcopy(PRODUCE),'instructions':'Use scripts/normalize.py and follow AGENTS.md.','repository_instructions':'# Repository instructions\n\n'+rules,'documentation':{'schema_version':2,'owner':'author','profiles':{'source':text,'runtime':text},'commands':[]},'execution_logging':{'mode':'host_public','owner':'host','record_location':'Task public tool history','rules_sha256':digest(rules.encode())}}
        submit(produced)
        self.assertTrue((run/'candidate/scripts/normalize.py').is_file())
        with self.assertRaises(Invalid):workflow.revise(run,'Change metadata after implementation.',phase='plan')
        with patch('subprocess.run',side_effect=AssertionError('Replay cannot run commands.')):
            self.assertEqual(replay(run)['rebuilt_files'],inventory(run/'candidate'))


class BudgetOnlyAmendmentTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy
    request = CompletionTests.request
    evidence = CompletionTests.evidence

    def test_budget_extension_retains_run_plan_receipts_and_usage_but_scope_change_does_not(self):
        checks=[*deepcopy(self.definition['checks']),{'id':'document','kind':'document','dependencies':['notes.md']}]
        policy=self.policy(checks=checks)
        run=self.workspace/'active-run';state=workflow.start(run,self.request(policy))
        completion.freeze_plan(state,{'requirements':[]},{'cases':[{'id':'unit','kind':'command'}]})
        completion.record(policy,'unit',self.project,self.evidence())
        completion.reserve(policy,'model_calls',detail='Authored bounded retry control.')
        before=completion.read(policy);definition=deepcopy(before['contract'])
        definition['budget']['runs']+=1;definition['budget']['model_calls']+=1
        completion.amend(policy,definition,'Authored authorized budget-only control; no actual user permission or model result is claimed.')
        current=completion.read(policy);completion.guard(state)
        self.assertEqual(current['plan'],before['plan'])
        self.assertEqual(current['receipts'],before['receipts'])
        self.assertEqual(current['usage'],before['usage'])
        self.assertEqual(current['created_unix'],before['created_unix'])
        self.assertTrue(next(c for c in completion.status(policy,self.project)['checks'] if c['id']=='unit')['valid'])
        definition['scope'].append('extra.py')
        completion.amend(policy,definition,'Authored scope-change rejection control, not real authority.')
        with self.assertRaisesRegex(Invalid,'binding changed'):completion.guard(state)


class AuditRepairCheckpointTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy
    request = CompletionTests.request

    def test_audit_then_repair_keeps_bound_report_and_budget_under_one_objective(self):
        (self.project/'SKILL.md').write_text('---\nname: policy-control\ndescription: Authored checkpoint fixture.\n---\nInspect supplied facts.\n')
        checks=[{'id':'audit-result','kind':'report','dependencies':[]},
                {'id':'unit','kind':'mechanical','dependencies':['run.py']}]
        policy=self.policy(checks=checks, checkpoints=[
            {'id':'audit','checks':['audit-result'],'depends_on':[],'lessons':[]},
            {'id':'repair','checks':['unit'],'depends_on':['audit'],'lessons':[]}])
        with self.assertRaisesRegex(Invalid,'dependency'):
            workflow.start(self.workspace/'too-early', self.request(policy,checkpoint='repair'))
        run=self.workspace/'audit-run'
        request=self.request(policy,operation='audit',checkpoint='audit');request.pop('allowed_paths')
        workflow.start(run,request)
        audit={'recommendation':'retain','rationale':'Authored checkpoint transport control; no model performance claim.',
               'findings':[], 'dimensions':[{'dimension':d,'status':'compliant','evidence':'Controlled source for checkpoint preservation.',
               'repair':'Retain.','preservation':'Keep original source in the report baseline.','regression':'This checkpoint transport control.'}
               for d in ('authorship_execution','over_engineering','over_testing','over_validation','avoidable_complexity')]}
        for data in (RESEARCH,audit):
            packet=workflow.packet(run)
            workflow.submit(run,{**{k:packet[k] for k in ('run_id','phase','packet_sha256')},'data':deepcopy(data)})
        self.assertEqual([c['valid'] for c in completion.status(policy,self.project)['checks']],[True,False])
        completion.checkpoint(policy,'audit',self.project,[])
        before=completion.read(policy)
        repair=self.workspace/'repair-run';state=workflow.start(repair,self.request(policy,checkpoint='repair'))
        dependency=workflow.packet(repair)['accepted_dependencies']['audit']['audit-result']
        self.assertEqual(dependency['sha256'],digest(Path(before['receipts']['audit-result']['evidence']).read_bytes()))
        self.assertEqual(completion.read(policy)['created_unix'],before['created_unix'])
        self.assertEqual(completion.read(policy)['usage']['runs'],2)
        spec={'requirements':[]};plan={'cases':[{'id':'unit','kind':'command'}]}
        completion.freeze_plan(state,spec,plan)
        self.assertEqual(completion.read(policy)['checkpoint_plans']['repair'],{'spec':spec,'plan':plan})
        with self.assertRaisesRegex(Invalid,'outside the frozen'):
            completion.freeze_plan({**state,'request':{**state['request'],'checkpoint':'audit'}},spec,plan)
        (self.project/'run.py').write_text('print("repaired")\n')
        state.update(phase='review',evaluation={'package_hashes':inventory(self.project),'attempts':[{'id':'unit','status':'passed'}]})
        completion.sync_native(repair,state)
        self.assertEqual([c['valid'] for c in completion.status(policy,self.project)['checks']],[True,True])
        self.assertFalse(completion.status(policy,self.project)['checks'][0]['fresh_current_artifact'])
        self.assertEqual(completion.read(policy)['receipts']['audit-result'],before['receipts']['audit-result'])
        (run/'baseline/run.py').write_text('tampered baseline\n')
        self.assertFalse(completion.status(policy,self.project)['checks'][0]['valid'])


class CompletionFeasibilityTests(unittest.TestCase):
    setUp = CompletionTests.setUp
    policy = CompletionTests.policy
    request = CompletionTests.request

    def test_impossible_native_checks_fail_before_build_and_budget_then_correct_in_place(self):
        checks=[*deepcopy(self.definition['checks']),
                {'id':'package-report','kind':'report','dependencies':[]},
                {'id':'native-use','kind':'behavior','case_id':'native-use','dependencies':['run.py'],
                 'profile':{'host':'codex','model':None,'reasoning_effort':None}}]
        policy=self.policy(checks=checks)
        host={'platform':'codex','model':None,'code_execution':True,'file_access':True,'external_cli':False,'allow_cross_provider':False}
        run=self.workspace/'native-run'
        with self.assertRaisesRegex(Invalid,'cannot be fulfilled') as failure:
            workflow.start(run,self.request(policy,host=host))
        self.assertIn('package-report',str(failure.exception));self.assertIn('native-use',str(failure.exception))
        self.assertFalse(run.exists())
        before=completion.read(policy)
        self.assertEqual(before['usage']['runs'],0)
        definition=deepcopy(before['contract']);definition['checks'].pop(1);definition['checks'][1].pop('profile')
        completion.amend(policy,definition,'Authored feasibility control correcting unsupported declarations, not actual user authority or a model result.')
        state=workflow.start(run,self.request(policy,host=host))
        self.assertEqual(state['phase'],'research')
        self.assertEqual(completion.read(policy)['usage']['runs'],1)
        self.assertEqual(completion.read(policy)['created_unix'],before['created_unix'])
