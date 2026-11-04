"""Raw fixture integrity and matrix registration controls."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from case_inputs import prepare_inputs
from host_coverage import freeze

class CaseInputTests(unittest.TestCase):
    def test_inline_and_manifest_inputs_preserve_values_without_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'evals/fixtures/record.json';p.parent.mkdir(parents=True);p.write_text('{"id":"0042"}')
            c={'request':{'source':{'criteria.txt':'Preserve IDs'}},'fixtures':[{'path':'evals/fixtures/record.json','destination':'record.json','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}]}
            self.assertEqual(prepare_inputs(root,c)['source']['record.json'],'{"id":"0042"}')
            self.assertNotIn('record.json',c['request']['source'])
            p.write_text('changed')
            with self.assertRaisesRegex(ValueError,'changed'):prepare_inputs(root,c)

    def test_missing_escaping_grading_and_duplicate_inputs_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'evals/fixtures/input.txt';p.parent.mkdir(parents=True);p.write_text('Raw data')
            entry={'path':'evals/fixtures/input.txt','destination':'input.txt','sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
            for key,value in [('destination','../escape'),('path','evals/rubric.json'),('path','evals/fixtures/missing')]:
                bad={**entry,key:value}
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):prepare_inputs(root,{'request':{},'fixtures':[bad]})
            with self.assertRaisesRegex(ValueError,'Duplicate'):prepare_inputs(root,{'request':{'source':{'input.txt':'existing'}},'fixtures':[entry]})
            with self.assertRaises(ValueError):prepare_inputs(root,{'request':{},'resources':['SKILL.md']})

    def test_default_matrix_registers_advice_and_construction_tasks(self):
        config=json.loads((ROOT/'config/host_validation.json').read_text())
        plan=freeze(ROOT,config)
        ids={row['id'] for row in plan['cases']}
        advice=json.loads((ROOT/'evals/agent_guidance_cases.json').read_text())
        self.assertTrue({c['id'] for c in advice}<=ids)
        self.assertIn('agent-system-build',ids)
        self.assertIn('agent-contract-audit',ids)
        for case in json.loads((ROOT/'evals/agent_system_cases.json').read_text()):
            self.assertTrue(prepare_inputs(ROOT,case)['source'])

    def test_matrix_freeze_rejects_missing_runtime_resource_before_execution(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'cases.json').write_text(json.dumps([{'id':'broken','kind':'behavior','request':{},'resources':['missing.md']}]))
            with self.assertRaisesRegex(ValueError,'missing'):freeze(root,{'required_hosts':['codex'],'case_files':[{'path':'cases.json'}]})
