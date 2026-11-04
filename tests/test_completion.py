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
        for data in (RESEARCH, {'recommendation': 'retain', 'rationale': 'Authored read-only transport control; no defect or model-quality claim.', 'findings': []}):
            packet = workflow.packet(run)
            workflow.submit(run, {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)})
        self.assertEqual(completion.read(policy)['phase'], 'delivery_pending')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'completion-delivered', '--policy', str(policy), '--package', str(self.project)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['phase'], 'delivered')
