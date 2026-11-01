"""Authored transport controls for late real-result import and honest stagnation."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from runtime import workflow
from runtime.common import Invalid
from repository_files import inventory
from evaluate import json_hash, maintenance
from fixtures import RESEARCH,PRODUCE
from test_workflow_coverage import WorkflowCoverageTests

class PendingObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);self.run=self.root/'run'
        self.spec,self.plan=WorkflowCoverageTests().normalizer()
        workflow.start(self.run,{'operation':'create','skill_name':'normalize-customers','brief':'Normalize customer input.','copyright_holder':'Fixture','limits':{'max_stagnant_experiments':1}})
        for phase,data in [('research',RESEARCH),('specify',self.spec),('plan',self.plan),('produce',PRODUCE)]:self.submit(phase,deepcopy(data))

    def submit(self,phase,data):
        p=workflow.packet(self.run);return workflow.submit(self.run,{**{k:p[k] for k in ('run_id','phase','packet_sha256')},'data':data})

    def observation(self,correct=True):
        case=self.plan['cases'][-1];p=self.root/'observations.json';p.write_text(json.dumps({'package_hashes':inventory(self.run/'candidate'),'observations':[{'case_id':case['id'],'case_sha256':json_hash(case),'execution_status':'completed','provenance':{'kind':'host_observation','host':'fixture','model':None,'source':'Authored transport control, not an actual model result.'},'output':{'customer_id':'0007' if correct else 'wrong','display_name':'Ada'}}]}));return p

    def review(self):
        state=workflow.read_state(self.run)
        return {'reviewer':{'kind':'model','identity':'unit fixture','method':'Authored readiness control, not real semantic evidence.'},'cases':[{'id':self.plan['cases'][-1]['id'],'accepted':True,'rationale':'Authored control cannot make absent/failed observations pass.'}],'resource_findings':[{'path':n,'accepted':True,'evidence':'Authored resource control.'} for n in sorted(workflow.review_resource_names(state))],'workflow_findings':[{'id':'normalize','accepted':True,'evidence':'Authored workflow control.'}],'workflow_inventory':{'accepted':True,'evidence':'Single-step authored fixture.'}}

    def test_pending_reviews_do_not_consume_stagnation_or_claim_readiness(self):
        for unused in range(4):
            workflow.run_evaluation(self.run,allow_exec=True);self.submit('review',self.review());state=workflow.read_state(self.run)
            self.assertEqual(state['stagnant_experiments'],0);self.assertNotEqual(state['status'],'ready')
        self.assertEqual(len(list((self.run/'evaluations').glob('*.json'))),4)

    def test_actual_result_import_can_refresh_review_directly(self):
        workflow.run_evaluation(self.run,allow_exec=True);first=(self.run/'evaluations/000.json').read_bytes()
        report=workflow.run_evaluation(self.run,allow_exec=True,observations=self.observation())
        self.assertEqual(report['attempts'][-1]['status'],'pending_review');self.assertEqual((self.run/'evaluations/000.json').read_bytes(),first)
        state=self.submit('review',self.review());self.assertEqual(state['status'],'ready');self.assertEqual(state['stagnant_experiments'],0)

    def test_review_cannot_repeat_evaluation_without_new_observations(self):
        workflow.run_evaluation(self.run,allow_exec=True);before=(self.run/'state.json').read_bytes()
        with self.assertRaisesRegex(Invalid,'prerequisites'):workflow.run_evaluation(self.run,allow_exec=True)
        self.assertEqual((self.run/'state.json').read_bytes(),before)

    def test_new_results_invalidate_old_review_packet(self):
        workflow.run_evaluation(self.run,allow_exec=True);old=workflow.packet(self.run)
        workflow.run_evaluation(self.run,allow_exec=True,observations=self.observation())
        with self.assertRaises(Invalid):workflow.submit(self.run,{**{k:old[k] for k in ('run_id','phase','packet_sha256')},'data':self.review()})

    def test_complete_failed_result_still_exhausts_stagnation(self):
        workflow.run_evaluation(self.run,allow_exec=True,observations=self.observation(False));state=self.submit('review',self.review())
        self.assertEqual(state['stagnant_experiments'],1);self.assertNotEqual(state['status'],'ready')
        with self.assertRaisesRegex(Invalid,'Stagnation'):workflow.revise(self.run,'Retry without a supported improvement.')

    def test_import_never_skips_production_prerequisites(self):
        run=self.root/'early';workflow.start(run,{'operation':'create','skill_name':'early-control','brief':'A test.','copyright_holder':'Fixture'})
        with self.assertRaisesRegex(Invalid,'prerequisites'):workflow.run_evaluation(run,observations=self.observation())

    def test_generated_maintenance_refresh_preserves_reports_and_tuning_allowance(self):
        package=self.run/'candidate';session=self.root/'portable'
        first=maintenance(package,session,self.plan['cases'],allow_exec=True)
        self.assertEqual(first['status'],'awaiting_observations');self.assertEqual(first['stagnant_attempts'],0)
        original=(session/first['attempts'][0]['report']).read_bytes()
        second=maintenance(package,session,self.plan['cases'],allow_exec=True,observations=json.loads(self.observation().read_text()))
        self.assertEqual(second['status'],'awaiting_review');self.assertEqual(second['stagnant_attempts'],0)
        self.assertTrue(second['attempts'][-1]['evidence_refresh']);self.assertEqual((session/first['attempts'][0]['report']).read_bytes(),original)
        report=json.loads((session/second['attempts'][-1]['report']).read_text());review={'report_sha256':json_hash(report),'reviewer':{'kind':'model','identity':'fixture','method':'Authored transport control.'},'cases':[{'id':row['id'],'accepted':True,'rationale':'Authored control.'} for row in report['attempts'] if row['status']=='pending_review']}
        final=maintenance(package,session,self.plan['cases'],allow_exec=True,review=review)
        self.assertEqual(final['status'],'target_met');self.assertEqual(final['stagnant_attempts'],0)

    def test_generated_maintenance_complete_failure_still_stops(self):
        package=self.run/'candidate';session=self.root/'portable'
        first=maintenance(package,session,self.plan['cases'],allow_exec=True,observations=json.loads(self.observation(False).read_text()))
        self.assertEqual(first['stagnant_attempts'],1)
        stopped=maintenance(package,session,self.plan['cases'],allow_exec=True,observations=json.loads(self.observation().read_text()))
        self.assertEqual(stopped['status'],'needs_continuation');self.assertFalse(stopped['proposal']['automatic_extension'])
