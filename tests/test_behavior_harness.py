"""Optional model-harness safety/provenance controls; no real model is invoked."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('behavior_harness', ROOT / 'tools/run_behavioral_evals.py')
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class BehaviorHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.subject = self.root / 'skill'
        self.subject.mkdir()
        (self.subject / 'SKILL.md').write_text('---\nname: test-skill\ndescription: Test the harness.\n---\nAudit before editing.')
        (self.subject / 'evals').mkdir()
        (self.subject / 'evals/private-rubric.json').write_text('An expected answer must not reach the performer.')
        (self.subject / 'scripts').mkdir()
        (self.subject / 'scripts/test_control.py').write_text('Hidden development control')
        (self.subject / 'scripts/words.test.py').write_text('Another hidden development control')
        self.cases = [{'id': 'audit', 'kind': 'behavior', 'critical': True, 'semantic': True, 'request': {'instruction': 'Audit the source only.', 'source': '# Source\nKeep this command.'}, 'resources': ['SKILL.md'], 'expect': {'exit_code': 0, 'contains': ['A hidden answer']}}]
        (self.root / 'cases.json').write_text(json.dumps(self.cases))
        self.config = {'subject': str(self.subject), 'cases': 'cases.json', 'model': 'fixture-model', 'max_invocations': 1, 'max_seconds': 30, 'repetitions': 2}
        self.config['reasoning_effort'] = 'medium'

    def run_harness(self):
        path = self.root / 'config.json'
        path.write_text(json.dumps(self.config))
        return harness.run(path, self.root / 'output', executable='fixture-codex')

    def test_zero_allowance_makes_no_model_call(self):
        self.config['max_invocations'] = 0
        self.config['preflight_command'] = ['{python}', '-c', 'print("ready")']
        with patch.object(harness, 'run_process') as call:
            result = self.run_harness()
        call.assert_not_called()
        self.assertEqual(result['model_invocations'], 0)
        self.assertTrue(all(row['status'] == 'not_run' for row in result['attempts']))

    def test_a_model_and_limits_must_be_explicit(self):
        for field in ('model', 'max_invocations', 'max_seconds'):
            value = self.config.pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError), patch.object(harness, 'run_process') as call:
                self.run_harness()
                call.assert_not_called()
            self.config[field] = value

    def test_fresh_attempts_use_local_skill_and_do_not_expose_answers(self):
        def perform(argv, *, input, cwd, timeout):
            self.assertIn('--sandbox', argv)
            self.assertIn('workspace-write', argv)
            self.assertEqual(argv[argv.index('--model') + 1], 'fixture-model')
            link = Path(cwd) / '.agents/skills/test-skill'
            self.assertTrue(link.is_symlink())
            self.assertFalse((link / 'evals').exists())
            self.assertFalse((link / 'scripts/test_control.py').exists())
            self.assertFalse((link / 'scripts/words.test.py').exists())
            self.assertIn('model_reasoning_effort="medium"', argv)
            self.assertNotIn('A hidden answer', input)
            final = Path(argv[argv.index('--output-last-message') + 1])
            final.write_text('Audit findings and recommended fixes.')
            return subprocess.CompletedProcess(argv, 0, json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Audit findings.'}}), '')
        with patch.object(harness.shutil, 'which', return_value='/fixture-codex'), patch.object(harness, 'run_process', side_effect=perform) as call:
            result = self.run_harness()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result['attempts'][0]['status'], 'pending_review')
        self.assertEqual(result['attempts'][1]['status'], 'not_run')
        self.assertEqual(result['attempts'][0]['provenance']['kind'], 'provider_cli')

    def test_invalid_reasoning_settings_do_not_invoke_a_model(self):
        for effort in ({}, [], False, 'unknown'):
            self.config['reasoning_effort'] = effort
            with self.subTest(effort=effort), patch.object(harness, 'run_process') as call:
                with self.assertRaises(ValueError):
                    self.run_harness()
                call.assert_not_called()

    def test_failed_preflight_uses_the_task_sandbox_and_spends_no_model_calls(self):
        self.config['preflight_command'] = ['{python}', '-c', 'print("probe")']
        def fail(argv, *, input, cwd, timeout):
            self.assertIn('sandbox', argv)
            self.assertIn('sandbox_mode="workspace-write"', argv)
            self.assertEqual(Path(cwd).name, 'preflight')
            return subprocess.CompletedProcess(argv, 2, '', 'Browser launch blocked.')
        with patch.object(harness, 'run_process', side_effect=fail) as call:
            result = self.run_harness()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result['model_invocations'], 0)
        self.assertEqual(result['preflight']['status'], 'failed')
        self.assertTrue(all(row['status'] == 'not_run' for row in result['attempts']))
        self.assertIn('workspace-write', result['sandbox_mode'])

    def completed_preflight_control(self):
        self.config.update(sandbox_mode='danger-full-access', preflight_command=['{python}', '-c', 'print("ready")'])
        order = []
        def perform(argv, *, input, cwd, timeout):
            if not order:
                self.assertEqual(argv[0], sys.executable)
                self.assertEqual(Path(cwd).name, 'preflight')
                order.append('preflight')
                return subprocess.CompletedProcess(argv, 0, 'ready', '')
            self.assertEqual(argv[argv.index('--sandbox') + 1], 'danger-full-access')
            order.append('model')
            Path(argv[argv.index('--output-last-message') + 1]).write_text('Audit findings.')
            return subprocess.CompletedProcess(argv, 0, json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Audit findings.'}}), '')
        with patch.object(harness.shutil, 'which', return_value='/fixture-codex'), patch.object(harness, 'run_process', side_effect=perform):
            result = self.run_harness()
        return result, order

    def preflight_trace(self, result):
        row = result['attempts'][0]
        captured = json.loads(Path(row['public_events']).read_text())
        self.assertEqual(captured[0]['item']['text'], 'Audit findings.')
        return {'provenance': {'kind': 'authored_control', 'source': 'test_behavior_harness.py: actual mocked-CLI execution and persisted capture, not model-quality evidence'},
                'events': [{'phase': 'preflight', 'evidence': json.dumps(result['preflight'])},
                           {'phase': 'perform', 'evidence': row['output']},
                           {'phase': 'capture', 'evidence': json.dumps(captured)}]}

    def test_preflight_precedes_model_calls_and_honors_the_declared_host_mode(self):
        result, order = self.completed_preflight_control()
        self.assertEqual(order, ['preflight', 'model'])
        self.assertEqual(result['model_invocations'], 1)
        self.assertEqual(result['preflight']['status'], 'passed')
        self.assertEqual(result['sandbox_mode'], 'danger-full-access')
        print(json.dumps({'process_trace': self.preflight_trace(result)}))

    def test_preflight_workflow_rejects_each_omission_and_adjacent_swap(self):
        from evaluate import grade_process
        result, _ = self.completed_preflight_control()
        trace = self.preflight_trace(result)
        expected = {'order': ['preflight', 'perform', 'capture'], 'visible': [], 'evidence': ['preflight', 'perform', 'capture']}
        self.assertTrue(grade_process(trace, expected)['passed'])
        for index in range(3):
            omitted = deepcopy(trace)
            omitted['events'].pop(index)
            with self.subTest(omitted=index):
                self.assertFalse(grade_process(omitted, expected)['passed'])
        for index in range(2):
            swapped = deepcopy(trace)
            swapped['events'][index:index + 2] = reversed(swapped['events'][index:index + 2])
            with self.subTest(swapped=index):
                self.assertFalse(grade_process(swapped, expected)['passed'])

    def test_invalid_preflight_or_permission_settings_never_start_a_child(self):
        initial = dict(self.config)
        for fields in ({'sandbox_mode': {}}, {'sandbox_mode': 'automatic-fallback'}, {'preflight_command': []}, {'preflight_command': 'shell text'}, {'preflight_command': [1]}, {'preflight_seconds': True}, {'preflight_seconds': 61}):
            self.config = {**initial, **fields}
            with self.subTest(fields=fields), patch.object(harness, 'run_process') as call:
                with self.assertRaises(ValueError):
                    self.run_harness()
                call.assert_not_called()

    def test_preflight_timeout_retains_output_without_starting_a_model(self):
        self.config['preflight_command'] = ['{python}', '-c', 'print("probe")']
        failure = subprocess.TimeoutExpired('probe', 1, output=b'partial probe output', stderr=b'launch stalled')
        with patch.object(harness, 'run_process', side_effect=failure) as call:
            result = self.run_harness()
        self.assertEqual(call.call_count, 1)
        self.assertEqual(result['model_invocations'], 0)
        self.assertEqual(result['preflight']['stdout'], 'partial probe output')
        self.assertEqual(result['preflight']['stderr'], 'launch stalled')

    def test_preflight_cannot_change_the_subject_before_invocation(self):
        self.config['preflight_command'] = ['{python}', '-c', 'print("probe")']
        def change(argv, **kwargs):
            (self.subject / 'SKILL.md').write_text('Changed subject')
            return subprocess.CompletedProcess(argv, 0, '', '')
        with patch.object(harness, 'run_process', side_effect=change) as call:
            with self.assertRaisesRegex(ValueError, 'Subject changed during dependency preflight'):
                self.run_harness()
        self.assertEqual(call.call_count, 1)

    def test_input_fixture_paths_cannot_escape_the_workspace(self):
        (self.root / 'workspace').mkdir()
        with self.assertRaises(ValueError):
            harness.stage_inputs(self.root / 'workspace', {'source': {'../../outside.md': 'bad'}})

    def test_only_public_task_events_are_collected(self):
        events = [
            {'type': 'item.completed', 'item': {'type': 'reasoning', 'text': 'Not evaluation evidence.'}},
            {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Visible audit.'}},
            {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'read source', 'exit_code': 0}},
        ]
        result = harness.public_events('\n'.join(json.dumps(row) for row in events))
        self.assertEqual([row['item']['type'] for row in result], ['agent_message', 'command_execution'])

    def test_claude_construction_transport_exposes_native_agent_dispatch(self):
        argv = harness.behavior_hosts.command('claude', 'fixture-model', None)
        for flag in ('--tools', '--allowedTools'):
            self.assertIn('Agent', argv[argv.index(flag) + 1].split(','))
        self.assertEqual(argv[argv.index('--permission-mode') + 1], 'dontAsk')
        self.assertIn('--strict-mcp-config', argv)

    def test_public_collaboration_lifecycle_is_retained_without_reasoning(self):
        events = [
            {'type':'item.started','item':{'id':'dispatch-1','type':'collab_tool_call','tool':'spawn_agent','status':'in_progress','receiver_thread_ids':[]}},
            {'type':'item.completed','item':{'id':'dispatch-1','type':'collab_tool_call','tool':'spawn_agent','status':'completed','receiver_thread_ids':['leaf-1']}},
            {'type':'item.completed','item':{'type':'reasoning','text':'Excluded private analysis.'}},
        ]
        captured = harness.public_events('\n'.join(json.dumps(event) for event in events))
        self.assertEqual(len(captured),2)
        self.assertEqual([row['item']['id'] for row in captured],['dispatch-1','dispatch-1'])
        self.assertEqual(captured[-1]['item']['receiver_thread_ids'],['leaf-1'])
