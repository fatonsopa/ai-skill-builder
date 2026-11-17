"""Controlled local deletion cases; no model-performance claim."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import record_retention as records


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.now = 1000000.0

    def bundle(self, name, **kwargs):
        path = self.root / name
        with patch.object(records.time, 'time', return_value=self.now):
            records.begin(path, 'fixture', **kwargs)
        (path / 'events.jsonl').write_text('observed event\n')
        return path

    def close(self, path, **kwargs):
        with patch.object(records.time, 'time', return_value=self.now):
            return records.finish(path, **kwargs)

    def sweep(self, days, **kwargs):
        return records.cleanup(self.root, 'fixture', now=self.now + days * 86400, **kwargs)

    def test_first_preview_then_expiry_leaves_unmanaged_and_active_files(self):
        old = self.bundle('old');self.close(old)
        active = self.bundle('active')
        legacy = self.root/'legacy';legacy.mkdir();(legacy/'events.jsonl').write_text('historical')
        preview = self.sweep(31)
        self.assertEqual(preview['mode'], 'preview');self.assertTrue(old.exists())
        self.assertEqual(next(r['action'] for r in preview['records'] if r.get('bundle')==str(old)), 'would_delete')
        applied = self.sweep(31)
        self.assertFalse(old.exists());self.assertTrue(active.exists());self.assertTrue(legacy.exists())
        self.assertEqual([r['action'] for r in applied['records'] if r.get('bundle')==str(old)], ['deleted'])
        receipt = json.loads((self.root/'.record-retention-fixture.json').read_text())['deletions'][0]
        self.assertEqual(receipt['record_id'],preview['records'][1]['record_id'] if preview['records'][1]['bundle']==str(old) else preview['records'][0]['record_id'])
        self.assertNotIn('observed event', json.dumps(receipt))

    def test_failed_clock_starts_at_resolution_and_pins_survive(self):
        failed=self.bundle('failed');self.close(failed,outcome='failed')
        accepted=self.bundle('accepted');self.close(accepted,pin='accepted-version')
        self.sweep(400);self.sweep(400)
        self.assertTrue(failed.exists());self.assertTrue(accepted.exists())
        with patch.object(records.time,'time',return_value=self.now+400*86400):
            records.finish(failed,outcome='failed',resolved=True)
        self.sweep(489);self.assertTrue(failed.exists())
        self.sweep(491);self.assertFalse(failed.exists());self.assertTrue(accepted.exists())

    def test_details_expire_separately_but_ancestor_evidence_protects_them(self):
        parent=self.bundle('run')
        child=parent/'diagnostics'
        with patch.object(records.time,'time',return_value=self.now):records.begin(child,'fixture',kind='diagnostic')
        (child/'tool-bodies.json').write_text('{"result":"synthetic"}')
        self.close(child);self.close(parent)
        self.sweep(8);self.sweep(8)
        self.assertFalse(child.exists());self.assertTrue(parent.exists())
        self.sweep(31);self.assertFalse(parent.exists())
        parent=self.bundle('pinned-run');child=parent/'diagnostics'
        records.begin(child,'fixture',kind='diagnostic');(child/'body').write_text('synthetic')
        self.close(child);self.close(parent)
        records.pin_reference(child/'body','accepted-proof')
        self.sweep(500);self.assertTrue(child.exists());self.assertTrue(parent.exists())

    def test_changed_bundle_symlink_and_protected_source_are_never_deleted(self):
        changed=self.bundle('changed');self.close(changed);(changed/'events.jsonl').write_text('new information')
        outside=self.root/'outside';outside.mkdir();(outside/'keep').write_text('user content')
        link=self.root/'alias';link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError):records.begin(link,'fixture')
        with self.assertRaises(ValueError):records.begin(self.root/'protected','fixture',protected=[self.root])
        with self.assertRaises(ValueError):records.begin(outside,'fixture')
        self.sweep(500);self.sweep(500)
        self.assertTrue(changed.exists());self.assertEqual((outside/'keep').read_text(),'user content')

    def test_owned_symlink_only_unlinks_pointer_and_explicit_dry_run_never_deletes(self):
        outside=self.root/'source';outside.mkdir();(outside/'keep').write_text('user')
        bundle=self.bundle('closed');(bundle/'source-link').symlink_to(outside,target_is_directory=True);self.close(bundle)
        self.sweep(31,dry_run=True);self.sweep(31,dry_run=True);self.assertTrue(bundle.exists())
        self.sweep(31);self.assertFalse(bundle.exists());self.assertEqual((outside/'keep').read_text(),'user')

    def test_real_builder_start_and_readonly_completion_manage_and_pin_new_records(self):
        from test_completion import CompletionTests
        from runtime import workflow
        from fixtures import RESEARCH
        fixture=CompletionTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        (fixture.project/'SKILL.md').write_text('---\nname: policy-control\ndescription: Retention lifecycle fixture.\n---\nInspect.\n')
        policy=fixture.policy(checks=[{'id':'audit','kind':'report','dependencies':[]}],delivery={'kind':'report','authority':'Authored lifecycle control.'})
        request=fixture.request(policy,operation='audit');request.pop('allowed_paths')
        run=fixture.workspace/'run';workflow.start(run,request)
        self.assertTrue((run/records.MARKER).is_file())
        audit={'recommendation':'retain','rationale':'Authored lifecycle control; not model evidence.','findings':[],
               'dimensions':[{'dimension':d,'status':'compliant','evidence':'Fixture only.','repair':'Retain.','preservation':'Retain.','regression':'This lifecycle control.'} for d in ['authorship_execution','over_engineering','over_testing','over_validation','avoidable_complexity']]}
        for data in [RESEARCH,audit]:
            packet=workflow.packet(run);workflow.submit(run,{**{k:packet[k] for k in ['run_id','phase','packet_sha256']},'data':data})
        meta=json.loads((run/records.MARKER).read_text())
        self.assertIsNotNone(meta['closed_at']);self.assertIn('accepted_read_only_result',meta['pins'])
        self.assertTrue(any(str(policy) in pin for pin in meta['pins']))

    def test_investigation_is_an_explicit_class_even_without_program_failure(self):
        case=self.bundle('investigation',kind='investigation');self.close(case)
        self.sweep(400);self.sweep(400);self.assertTrue(case.exists())
        with patch.object(records.time,'time',return_value=self.now+400*86400):
            records.finish(case,resolved=True)
        self.sweep(491);self.assertFalse(case.exists())

    def test_generated_file_record_skill_receives_the_same_mechanic_and_host_mode_stays_native(self):
        from copy import deepcopy
        from fixtures import PLAN, PRODUCE, SPEC
        from runtime.artifacts import render, execution_logging_rules
        plan=deepcopy(PLAN)
        plan.update(package_profile='maintained',components=[{'path':'scripts/record_retention.py','requirements':['R-1'],'reason':'Expire owned structured execution records.'},{'path':'scripts/normalize.py','requirements':['R-1'],'reason':'Transform supplied JSON.'}],authored_outputs=[],execution={})
        rules=execution_logging_rules();pro=deepcopy(PRODUCE)
        pro.update(instructions='Follow AGENTS.md and use scripts/record_retention.py from the existing executor.',repository_instructions='# Repository instructions\n\n'+rules,documentation={'schema_version':2,'owner':'author','profiles':{'source':'# Fixture guide\n','runtime':'# Fixture guide\n'},'commands':[]},execution_logging={'mode':'structured_file','owner':'executor','record_location':'Authorized task workspace','rules_sha256':__import__('runtime.common',fromlist=['digest']).digest(rules.encode())})
        request={'operation':'create','skill_name':'normalize-customers','copyright_holder':'Fixture Author'}
        target=self.root/'generated';render(target,request,deepcopy(SPEC),plan,pro)
        self.assertEqual((target/'scripts/record_retention.py').read_bytes(),(Path(records.__file__)).read_bytes())
        record=json.loads((target/'config/build_record.json').read_text())
        self.assertEqual(record['source']['execution_logging']['retention']['mode'],'managed_files')
        pro['execution_logging']['mode']='host_public';plan['components']=[{'path':'scripts/normalize.py','requirements':['R-1'],'reason':'Transform supplied JSON.'}];plan['package_profile']='native';plan['automations']={}
        target=self.root/'native';render(target,request,deepcopy(SPEC),plan,pro)
        self.assertFalse((target/'scripts/record_retention.py').exists())
        self.assertEqual(json.loads((target/'config/build_record.json').read_text())['source']['execution_logging']['retention']['mode'],'host_managed')

    def test_resolved_investigation_starts_the_diagnostic_seven_day_clock(self):
        parent=self.bundle('case',kind='investigation');child=parent/'diagnostics'
        records.begin(child,'fixture',kind='diagnostic');(child/'body').write_text('synthetic')
        self.close(child);self.close(parent,outcome='failed')
        self.sweep(100);self.sweep(100);self.assertTrue(child.exists())
        with patch.object(records.time,'time',return_value=self.now+100*86400):
            records.finish(parent,outcome='failed',resolved=True)
        self.sweep(106);self.assertTrue(child.exists())
        self.sweep(108);self.assertFalse(child.exists());self.assertTrue(parent.exists())
