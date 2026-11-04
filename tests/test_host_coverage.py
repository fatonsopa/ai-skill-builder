"""Authored host/matrix controls. Mock CLI captures are not model-quality evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tools'))
import host_coverage as matrix
from host_coverage import public_delivery_match, digest
import behavior_hosts
import run_behavioral_evals as harness
from repository_files import inventory


class HostCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'skill'
        self.package.mkdir()
        (self.package / 'SKILL.md').write_text('---\nname: example\ndescription: A fixture.\n---\nAudit the input.')
        (self.package / 'evals').mkdir()
        self.case = {'id': 'audit', 'kind': 'behavior', 'request': {'instruction': 'Audit only.'}, 'critical': True, 'semantic': True, 'expect': {'exit_code': 0}}
        (self.package / 'evals/cases.json').write_text(json.dumps([self.case]))
        self.config = {'required_hosts': ['codex', 'claude-code'], 'case_files': [{'path': 'evals/cases.json'}]}
        self.plan = matrix.freeze(self.package, self.config)

    def bundle(self, host, status='pending_review', accepted=True, name=None, model='fixture-model', effort=None):
        folder = self.root / (name or host)
        attempt = folder / '001-audit'
        work = attempt / 'workspace'
        work.mkdir(parents=True)
        (work / 'audit.md').write_text('Located findings; source preserved.')
        events = [{'type': 'thread.started', 'thread_id': 'authored-control'}] if host == 'codex' else [{'type': 'result', 'subtype': 'success', 'result': 'Authored control.'}]
        matrix.save_new(attempt / 'public-events.json', events)
        row = {'id': '001-audit', 'case_id': 'audit', 'case_sha256': matrix.digest(self.case), 'status': status, 'exit_code': 0, 'output': 'Located findings.', 'requested_model': model, 'resolved_model': None,
               'provenance': {'host': host, 'kind': 'authored_control'}, 'public_events': str(attempt / 'public-events.json'), 'workspace_hashes': inventory(work)}
        report = {'execution_host': host, 'requested_model': model, 'reasoning_effort': effort, 'package_hashes': inventory(self.package), 'attempts': [row]}
        matrix.save_new(folder / 'report.json', report)
        review = {'report_sha256': matrix.digest((folder / 'report.json').read_bytes()), 'reviewer': {'kind': 'authored_control', 'identity': 'unit test', 'method': 'A checker fixture, not actual semantic evaluation.'},
                  'cases': [{'attempt_id': row['id'], 'accepted': accepted, 'rationale': 'Authored grading control.', 'capture_sha256': matrix.digest(row), 'public_events_sha256': matrix.digest((attempt / 'public-events.json').read_bytes())}]}
        matrix.save_new(folder / 'review.json', review)
        return {'report': str(folder / 'report.json'), 'review': str(folder / 'review.json')}

    def test_frozen_model_and_effort_profiles_cannot_be_substituted(self):
        config = {**self.config, 'profiles': [{'host': 'codex', 'model': 'fixture-model', 'reasoning_effort': 'medium'}, {'host': 'claude-code', 'model': 'fixture-claude', 'reasoning_effort': 'high'}]}
        plan = matrix.freeze(self.package, config)
        valid = [self.bundle('codex', effort='medium'), self.bundle('claude-code', model='fixture-claude', effort='high')]
        self.assertTrue(matrix.assess(plan, self.package, valid)['accepted'])
        for model, effort in [('different-model', 'medium'), ('fixture-model', 'high')]:
            wrong = self.bundle('codex', name=model+'-'+effort, model=model, effort=effort)
            with self.assertRaisesRegex(ValueError, 'frozen host profile'):matrix.assess(plan, self.package, [wrong])

    def test_passed_subsets_from_different_profiles_cannot_fill_one_host(self):
        first = self.bundle('codex', name='first-model', model='first-model')
        second = self.bundle('codex', name='second-model', model='second-model')
        with self.assertRaisesRegex(ValueError, 'different model/effort'):matrix.assess(self.plan, self.package, [first, second])
        third = self.bundle('codex', name='different-effort', model='first-model', effort='high')
        with self.assertRaisesRegex(ValueError, 'different model/effort'):matrix.assess(self.plan, self.package, [first, third])

    def test_invalid_profile_declarations_fail_before_execution(self):
        for profiles in [{}, [None], [{'host':'codex','model':'fixture','reasoning_effort':'medium'}]]:
            with self.subTest(profiles=profiles), self.assertRaises(ValueError):matrix.freeze(self.package, {**self.config, 'profiles':profiles})

    def test_missing_required_host_blocks_an_otherwise_passing_matrix(self):
        result = matrix.assess(self.plan, self.package, [self.bundle('codex')])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['hosts']['codex']['task_success_percent'], 100)
        self.assertEqual(result['hosts']['claude-code']['coverage_percent'], 0)
        self.assertIsNone(result['hosts']['claude-code']['task_success_percent'])

    def test_declared_delivery_check_cannot_be_waived_by_favorable_review(self):
        config = deepcopy(self.config)
        config['case_files'][0]['verify_delivery'] = True
        plan = matrix.freeze(self.package, config)
        self.assertTrue(plan['cases'][0]['verify_delivery'])
        bundles = [self.bundle('codex'), self.bundle('claude-code')]
        with patch.object(matrix, 'public_delivery_match', return_value={'passed': False}) as check:
            self.assertFalse(matrix.assess(plan, self.package, bundles)['accepted'])
            self.assertEqual(check.call_count, 2)
        with patch.object(matrix, 'public_delivery_match', return_value={'passed': True}):
            self.assertTrue(matrix.assess(plan, self.package, bundles)['accepted'])
        config['case_files'][0]['verify_delivery'] = 'true'
        with self.assertRaisesRegex(ValueError, 'boolean'):
            matrix.freeze(self.package, config)

    def test_both_bound_reviewed_hosts_are_required_for_acceptance(self):
        result = matrix.assess(self.plan, self.package, [self.bundle('codex'), self.bundle('claude-code')])
        self.assertTrue(result['accepted'])
        print(json.dumps({'provenance': {'kind': 'authored_control', 'source': 'test_host_coverage.py: real freeze and assess calls over authored CLI fixtures, not model performance'}, 'events': [{'phase': 'freeze', 'evidence': self.plan['plan_sha256']}, {'phase': 'assess', 'evidence': json.dumps(result)}]}))

    def test_matrix_trace_rejects_each_omission_and_wrong_order(self):
        from evaluate import grade_process
        result = matrix.assess(self.plan, self.package, [self.bundle('codex'), self.bundle('claude-code')])
        trace = {'provenance': {'kind': 'authored_control', 'source': 'Actual fixture matrix calls'}, 'events': [{'phase': 'freeze', 'evidence': json.dumps(self.plan)}, {'phase': 'assess', 'evidence': json.dumps(result)}]}
        expected = {'order': ['freeze', 'assess'], 'visible': [], 'evidence': ['freeze', 'assess']}
        self.assertTrue(grade_process(trace, expected)['passed'])
        for index in range(2):
            bad = deepcopy(trace);bad['events'].pop(index)
            self.assertFalse(grade_process(bad, expected)['passed'])
        trace['events'].reverse()
        self.assertFalse(grade_process(trace, expected)['passed'])

    def test_no_review_leaves_actual_output_pending(self):
        bundle = self.bundle('codex'); bundle.pop('review')
        result = matrix.assess(self.plan, self.package, [bundle])
        self.assertEqual(result['hosts']['codex']['pending_review'], 1)
        self.assertFalse(result['accepted'])

    def test_favorable_review_cannot_waive_transport_failure(self):
        result = matrix.assess(self.plan, self.package, [self.bundle('codex', status='failed'), self.bundle('claude-code')])
        self.assertFalse(result['accepted'])
        self.assertEqual(result['hosts']['codex']['accepted'], 0)

    def test_old_failures_are_retained_when_a_new_attempt_passes(self):
        bundles = [self.bundle('codex', status='failed', name='old'), self.bundle('codex', name='new'), self.bundle('claude-code')]
        result = matrix.assess(self.plan, self.package, bundles)
        self.assertTrue(result['accepted'])
        self.assertEqual([r['status'] for r in result['attempt_history']], ['failed', 'passed', 'passed'])

    def test_duplicate_report_cannot_inflate_coverage(self):
        bundle = self.bundle('codex')
        with self.assertRaisesRegex(ValueError, 'twice'):
            matrix.assess(self.plan, self.package, [bundle, bundle])

    def test_changed_artifact_plan_review_trace_and_output_are_rejected(self):
        bundle = self.bundle('codex')
        for target in [Path(bundle['report']), Path(bundle['review']), Path(bundle['report']).parent / '001-audit/public-events.json', Path(bundle['report']).parent / '001-audit/workspace/audit.md', self.package / 'SKILL.md']:
            original = target.read_bytes()
            with self.subTest(path=target.name):
                if target.name == 'review.json':
                    data = json.loads(original); data['cases'][0]['capture_sha256'] = 'wrong';target.write_text(json.dumps(data))
                elif target.name == 'report.json':
                    data = json.loads(original);data['attempts'][0]['case_sha256'] = 'wrong';target.write_text(json.dumps(data))
                else:target.write_bytes(original + b' changed')
                with self.assertRaises((ValueError, json.JSONDecodeError)):
                    matrix.assess(self.plan, self.package, [bundle])
                target.write_bytes(original)
        changed = deepcopy(self.plan);changed['required_hosts'] = ['codex']
        with self.assertRaises(ValueError):matrix.assess(changed, self.package, [bundle])

    def test_duplicate_hosts_cases_and_unknown_case_selections_fail_before_running(self):
        for config in [{'required_hosts': ['codex', 'codex'], 'case_files': self.config['case_files']}, {'required_hosts': ['codex'], 'case_files': [{'path': 'evals/cases.json', 'ids': ['unknown']}]}, {'required_hosts': ['codex'], 'case_files': self.config['case_files'] * 2}]:
            with self.subTest(config=config), self.assertRaises(ValueError):matrix.freeze(self.package, config)

    def test_claude_transport_invokes_the_local_skill_with_tools_and_keeps_public_evidence(self):
        config = {'subject': str(self.package), 'cases': str(self.package / 'evals/cases.json'), 'host': 'claude-code', 'model': 'fixture-model', 'reasoning_effort': 'medium', 'max_invocations': 1, 'max_seconds': 30}
        (self.root / 'config.json').write_text(json.dumps(config))
        def perform(argv, *, input, cwd, timeout):
            self.assertNotIn('--bare', argv)
            self.assertNotIn('--disable-slash-commands', argv)
            self.assertNotIn('--sandbox', argv)
            self.assertIn('dontAsk', argv)
            self.assertIn('Skill', argv[argv.index('--tools') + 1])
            self.assertTrue((Path(cwd) / '.claude/skills/example').is_symlink())
            self.assertEqual((Path(cwd) / '.agents/skills/example').resolve(), (Path(cwd) / '.claude/skills/example').resolve())
            self.assertIn('Invoke /example', input)
            events = [{'type': 'system', 'subtype': 'init', 'model': 'fixture-model'}, {'type': 'assistant', 'message': {'content': [{'type': 'thinking', 'thinking': 'Excluded private reasoning.'}, {'type': 'tool_use', 'id': 'read', 'name': 'Read', 'input': {'file_path': 'input/document.md'}}, {'type': 'text', 'text': 'Audit findings.'}]}}, {'type': 'result', 'subtype': 'success', 'is_error': False, 'result': 'Audit findings.'}]
            return subprocess.CompletedProcess(argv, 0, '\n'.join(map(json.dumps, events)), '')
        with patch.object(harness.shutil, 'which', return_value='/fixture-claude'), patch.object(harness, 'run_process', side_effect=perform):
            result = harness.run(self.root / 'config.json', self.root / 'run')
        row = result['attempts'][0]
        self.assertEqual(result['execution_host'], 'claude-code')
        self.assertEqual(row['status'], 'pending_review')
        self.assertEqual(row['resolved_model'], 'fixture-model')
        self.assertNotIn('Excluded private reasoning', Path(row['public_events']).read_text())
        self.assertIn('tool_use', Path(row['public_events']).read_text())

    def test_an_actual_timeout_remains_failed_with_a_partial_trace(self):
        config = {'subject': str(self.package), 'cases': str(self.package / 'evals/cases.json'), 'host': 'claude-code', 'model': 'fixture-model', 'max_invocations': 1, 'max_seconds': 30}
        (self.root / 'timeout-config.json').write_text(json.dumps(config))
        partial = b'{"type":"assistant","message":{"content":[{"type":"text","text":"Started audit."}]}}'
        error = subprocess.TimeoutExpired('fixture-claude', 10, output=partial)
        with patch.object(harness.shutil, 'which', return_value='/fixture-claude'), patch.object(harness, 'run_process', side_effect=error):
            result = harness.run(self.root / 'timeout-config.json', self.root / 'timed-out-run')
        row = result['attempts'][0]
        self.assertEqual(result['model_invocations'], 1)
        self.assertEqual(row['status'], 'failed')
        self.assertIn('Started audit', Path(self.root / 'timed-out-run' / row['id'] / 'public-events.json').read_text())

    def test_workspace_capture_keeps_internal_target_skill_links_and_both_controlled_aliases(self):
        work = self.root / 'links-work';work.mkdir()
        installed = self.root / 'installed';installed.mkdir()
        (installed / 'SKILL.md').write_text('Controlled subject.')
        primary = work / '.claude/skills/example';primary.parent.mkdir(parents=True);primary.symlink_to(installed)
        alias = work / '.agents/skills/example';alias.parent.mkdir(parents=True);alias.symlink_to(primary)
        target = work / 'output/created-skill';target.mkdir(parents=True);(target/'SKILL.md').write_text('A created target skill.')
        (work / '.claude/skills/created-skill').symlink_to(target)
        env = work / '.venv/bin';env.mkdir(parents=True);(env/'python').symlink_to('/outside/python')
        links = {};files = harness.workspace_files(work,primary,installed,links)
        self.assertEqual(set(links), {'.agents/skills/example','.claude/skills/example','.claude/skills/created-skill'})
        self.assertIn('output/created-skill/SKILL.md', files)
        self.assertNotIn('.venv/bin/python',files)
        (work/'escape').symlink_to(self.package)
        with self.assertRaisesRegex(ValueError,'leaves the workspace'):harness.workspace_files(work,primary,installed,{})

    def test_matrix_rejects_modified_internal_and_controlled_links(self):
        bundle = self.bundle('codex')
        report_path = Path(bundle['report']);report = json.loads(report_path.read_text())
        row = report['attempts'][0];attempt = report_path.parent / row['id'];work = attempt / 'workspace'
        installed = attempt / 'runtime-skill';installed.mkdir();(installed/'SKILL.md').write_text('Controlled fixture skill.')
        alias = work/'.agents/skills/example';alias.parent.mkdir(parents=True);alias.symlink_to(installed)
        target = work/'child';target.mkdir();(target/'SKILL.md').write_text('Created fixture skill.')
        local = work/'child-alias';local.symlink_to(target)
        row['runtime_hashes'] = inventory(installed)
        row['workspace_links'] = {'.agents/skills/example':{'kind':'controlled_skill','target':str(installed.resolve())},'child-alias':{'kind':'workspace','target':str(target.resolve())}}
        report_path.write_text(json.dumps(report));review_path=Path(bundle['review']);review=json.loads(review_path.read_text());review['report_sha256']=matrix.digest(report_path.read_bytes());review['cases'][0]['capture_sha256']=matrix.digest(row);review_path.write_text(json.dumps(review))
        self.assertEqual(matrix.assess(self.plan,self.package,[bundle])['hosts']['codex']['accepted'],1)
        alias.unlink();alias.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'link changed'):matrix.assess(self.plan,self.package,[bundle])
        alias.unlink();alias.symlink_to(installed)
        local.unlink();local.symlink_to(self.package)
        with self.assertRaisesRegex(ValueError,'link changed'):matrix.assess(self.plan,self.package,[bundle])
        local.unlink();local.symlink_to(target)
        (installed/'SKILL.md').write_text('Altered controlled runtime.')
        with self.assertRaisesRegex(ValueError,'runtime changed'):matrix.assess(self.plan,self.package,[bundle])

    def test_capture_failure_keeps_earlier_case_results_and_the_actual_public_trace(self):
        config = {'subject': str(self.package), 'cases': str(self.package/'evals/cases.json'), 'model':'fixture-model','max_invocations':2,'max_seconds':30,'repetitions':2}
        (self.root/'capture-config.json').write_text(json.dumps(config));calls=[]
        def perform(argv, *, input, cwd, timeout):
            calls.append(str(cwd));Path(argv[argv.index('--output-last-message')+1]).write_text('Actual fixture response.')
            if len(calls)==2:(Path(cwd)/'escape').symlink_to(self.package)
            return subprocess.CompletedProcess(argv,0,json.dumps({'type':'thread.started','thread_id':'authored-control'}),'')
        with patch.object(harness.shutil,'which',return_value='/fixture-codex'),patch.object(harness,'run_process',side_effect=perform):
            result=harness.run(self.root/'capture-config.json',self.root/'captured-run')
        self.assertEqual([r['status'] for r in result['attempts']],['pending_review','failed'])
        self.assertIn('artifact capture failed',result['attempts'][1]['reason'])
        self.assertTrue((self.root/'captured-run/002-audit/public-events.json').is_file())
        self.assertTrue(result['controller_hashes'])

    def test_provider_limit_stops_following_calls_and_distinguishes_unstarted_from_interrupted(self):
        for started in [False,True]:
            with self.subTest(started=started):
                config={'subject':str(self.package),'cases':str(self.package/'evals/cases.json'),'host':'claude-code','model':'fixture-model','max_invocations':3,'max_seconds':30,'repetitions':3}
                config_path=self.root/('limit-'+str(started)+'.json');config_path.write_text(json.dumps(config))
                result={'type':'result','subtype':'success','is_error':True,'terminal_reason':'api_error','api_error_status':429,'api_error':'usage_limit_reached','result':'Weekly usage limit reached; resets Wednesday at07:00.','usage':{'input_tokens':0,'output_tokens':12 if started else 0}}
                def perform(argv,**kwargs):return subprocess.CompletedProcess(argv,0,json.dumps(result),'')
                with patch.object(harness.shutil,'which',return_value='/fixture-claude'),patch.object(harness,'run_process',side_effect=perform) as invoke:
                    report=harness.run(config_path,self.root/('limited-'+str(started)))
                self.assertEqual(invoke.call_count,1);self.assertEqual(report['model_invocations'],1)
                self.assertEqual([x['status'] for x in report['attempts']],['failed' if started else 'infrastructure_failure','not_run','not_run'])
                row=report['attempts'][0];self.assertIn('Weekly usage limit',row['reason']);self.assertEqual(row['provider_error']['task_started'],started)
                self.assertEqual(report['execution_block']['code'],'usage_limit_reached')
                self.assertIn('usage_limit_reached',Path(row['public_events']).read_text())
                self.assertFalse((self.root/('limited-'+str(started))/'002-audit/workspace').exists())

    def test_provider_recovery_uses_new_records_after_the_limit_clears(self):
        config={'subject':str(self.package),'cases':str(self.package/'evals/cases.json'),'host':'claude-code','model':'fixture-model','max_invocations':1,'max_seconds':30}
        config_path=self.root/'recovery-config.json';config_path.write_text(json.dumps(config))
        blocked={'type':'result','subtype':'success','is_error':True,'api_error':'usage_limit_reached','api_error_status':429,'result':'Weekly usage limit reached.','usage':{'input_tokens':0,'output_tokens':0}}
        clear={'type':'result','subtype':'success','is_error':False,'result':'Actual authored-control response.'}
        old=self.root/'provider-old';new=self.root/'provider-new'
        with patch.object(harness.shutil,'which',return_value='/fixture-claude'),patch.object(harness,'run_process',side_effect=[subprocess.CompletedProcess([],0,json.dumps(blocked),''),subprocess.CompletedProcess([],0,json.dumps(clear),'')]) as invoke:
            first=harness.run(config_path,old);before=(old/'report.json').read_bytes()
            with self.assertRaisesRegex(ValueError,'Preserve earlier'):harness.run(config_path,old)
            second=harness.run(config_path,new)
        self.assertEqual(invoke.call_count,2);self.assertEqual((old/'report.json').read_bytes(),before)
        self.assertEqual(first['attempts'][0]['status'],'infrastructure_failure');self.assertEqual(second['attempts'][0]['status'],'pending_review');self.assertIsNone(second['execution_block'])

    def test_matrix_retains_provider_limit_cause_without_accepting_blocked_work(self):
        bundle=self.bundle('claude-code',status='infrastructure_failure');path=Path(bundle['report']);report=json.loads(path.read_text());row=report['attempts'][0];row.update(failure_kind='provider_usage_limit',reason='Weekly usage limit reached',provider_error={'kind':'usage_limit','task_started':False});path.write_text(json.dumps(report));bundle.pop('review')
        result=matrix.assess(self.plan,self.package,[bundle]);self.assertFalse(result['accepted']);self.assertEqual(result['hosts']['claude-code']['evaluated'],0)
        self.assertEqual(result['attempt_history'][0]['provider_error']['task_started'],False)
        self.assertEqual(result['attempt_history'][0]['failure_kind'],'provider_usage_limit')

    def test_claude_zero_exit_error_results_are_failures(self):
        result = behavior_hosts.capture(json.dumps({'type': 'result', 'subtype': 'error_during_execution', 'is_error': True, 'result': 'Failed.'}))
        self.assertIsNotNone(result['failure'])
        self.assertIsNone(result['final'])

    def test_claude_timeout_keeps_partial_public_tools_without_private_reasoning(self):
        output = b'{"type":"assistant","message":{"content":[{"type":"thinking","thinking":"private"},{"type":"tool_use","name":"Read","input":{}}]}}'
        result = behavior_hosts.capture(output)
        self.assertIn('tool_use', json.dumps(result['events']))
        self.assertNotIn('thinking', json.dumps(result['events']))
        self.assertIsNotNone(result['failure'])

    def test_generated_skills_receive_the_shared_matrix_and_guard(self):
        from runtime import workflow
        from fixtures import RESEARCH, PRODUCE
        from test_workflow_coverage import WorkflowCoverageTests
        run = self.root / 'generated'
        spec, plan = WorkflowCoverageTests().normalizer()
        workflow.start(run, {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'A generated control.', 'copyright_holder': 'Fixture'}, protocol_version=2)
        for phase, data in [('research', RESEARCH), ('specify', spec), ('plan', plan), ('produce', PRODUCE)]:
            packet = workflow.packet(run)
            workflow.submit(run, {**{k: packet[k] for k in ('run_id', 'phase', 'packet_sha256')}, 'data': deepcopy(data)})
        config = json.loads((run / 'candidate/config/host_validation.json').read_text())
        self.assertEqual(config['required_hosts'], ['codex', 'claude-code'])
        self.assertEqual((run / 'candidate/scripts/host_coverage.py').read_bytes(), (ROOT / 'scripts/host_coverage.py').read_bytes())
        self.assertIn('host_coverage.py', (run / 'candidate/SKILL.md').read_text())
        self.assertEqual((run / 'candidate/scripts/provider_results.py').read_bytes(), (ROOT / 'scripts/provider_results.py').read_bytes())
        own = run / 'candidate'
        result = subprocess.run([sys.executable, str(own / 'scripts/host_coverage.py'), 'freeze', '--package', str(own), '--config', str(own / 'config/host_validation.json'), '--output', str(self.root / 'generated-plan.json')], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


class PublicDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.case = self.root / '001-case'
        self.work = self.case / 'workspace'
        self.work.mkdir(parents=True)
        self.document = self.work / 'output.md'
        self.document.write_text('Reviewed draft.')
        self.message = 'Saved the reviewed document.\n'
        self.receipt = self.work / 'session/delivery.json'
        self.receipt.parent.mkdir()
        self.receipt.write_text(json.dumps({'message': self.message, 'message_sha256': digest(self.message.encode()),
            'destination': str(self.document), 'output_sha256': digest(self.document.read_bytes())}))
        self.report = self.root / 'report.json'
        self.events = self.case / 'public-events.json'
        self.row = {'id': '001-case', 'status': 'pending_review', 'workspace_hashes': {
            'output.md': digest(self.document.read_bytes()), 'session/delivery.json': digest(self.receipt.read_bytes())}}

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, host='codex', text=None):
        text = self.message if text is None else text
        event = ({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': text}} if host == 'codex' else
                 {'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': text}]}})
        self.events.write_text(json.dumps([event]))
        self.report.write_text(json.dumps({'execution_host': host, 'attempts': [self.row]}))
        return public_delivery_match(self.report, '001-case')

    def test_matching_handoff_on_both_host_formats(self):
        for host in ['codex', 'claude-code']:
            self.assertTrue(self.capture(host)['passed'])
        print(json.dumps({'provenance': {'kind': 'authored_control', 'source': 'Actual capture-file comparison; not model quality.'},
            'events': [{'phase': 'verify', 'evidence': 'Both actual capture parsers compared the stored receipt and delivered bytes.'}]}))

    def test_changed_final_text_cannot_pass_a_checked_local_copy(self):
        self.assertFalse(self.capture(text=self.message + 'No target has been set.')['passed'])
        self.assertTrue(self.capture()['passed'])

    def test_missing_or_conflicting_receipt_is_rejected(self):
        self.row['workspace_hashes'].pop('session/delivery.json')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            self.capture()
        self.row['workspace_hashes']['session/delivery.json'] = digest(self.receipt.read_bytes())
        other = self.work / 'other/delivery.json';other.parent.mkdir();other.write_bytes(self.receipt.read_bytes())
        self.row['workspace_hashes']['other/delivery.json'] = digest(other.read_bytes())
        self.assertTrue(self.capture()['passed'])
        data = json.loads(other.read_text());data['message'] = 'A different final message.'
        data['message_sha256'] = digest(data['message'].encode());other.write_text(json.dumps(data))
        self.row['workspace_hashes']['other/delivery.json'] = digest(other.read_bytes())
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            self.capture()

    def test_changed_document_or_receipt_is_rejected(self):
        self.document.write_text('Newer content.')
        with self.assertRaisesRegex(ValueError, 'document changed'):
            self.capture()
        self.document.write_text('Reviewed draft.')
        self.receipt.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'receipt changed'):
            self.capture()

    def test_unattempted_work_and_missing_public_message_cannot_pass(self):
        self.row['status'] = 'not_run'
        with self.assertRaisesRegex(ValueError, 'completed actual'):
            self.capture()
        self.row['status'] = 'pending_review';self.capture();self.events.write_text('[]')
        with self.assertRaisesRegex(ValueError, 'No actual public'):
            public_delivery_match(self.report, '001-case')

if __name__ == "__main__":
    unittest.main()
