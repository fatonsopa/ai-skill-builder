"""Execution contracts reject omitted responsibilities and stale instruction reviews."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from runtime import contracts
from runtime.common import Invalid, validate
from runtime.execution import check_execution, instruction_bundles, review_execution, EVENTS


def sample():
    spec={'requirements':[{'id':'R1','text':'Preserve identity','kind':'semantic'}]}
    roles=[]
    for name,recipient in [('lead','user'),('identity','lead')]:
        roles.append({'id':name,'eligibility':'Assigned identity review','exclusions':'No external writes',
                      'inputs':['record and source hash'],'outputs':['evidence-backed result'],'recipient':recipient,
                      'authority':{'tools':['read'],'read_roots':['source'],'write_roots':[], 'external_actions':[], 'may_delegate':name=='lead'},
                      'dispatch':'native host tools','limits':'one bounded task','recovery':'retain failed result',
                      'method':'references/identity.md','assets':[{'host':'claude-code','path':'assets/'+name+'.md','loaded_paths':['references/shared.md']}]})
    design={'mode':'multi','rationale':'Independent bounded review','file_workflow':True,'file_reason':'Read supplied source',
            'bindings':[{'id':'source','origin':'source','root':'source','access':'read','version_binding':'content hash'},
                        {'id':'evidence','origin':'output','root':'evidence','access':'write','version_binding':'review ID'}],
            'document_context':{'applicable':True,'reason':'Current user criteria supply intent','sources':[]},
            'final_owner':'lead','roles':roles,
            'coverage':[{'requirement':'R1','status':'covered','roles':['lead','identity'],'cases':['actual'],'reason':'Both inspect identity evidence'}],
            'lifecycle':[{'event':event,'applicable':True,'reason':'Worker may return after state changes','record_outcome':'retain original attempt','accept_evidence':'reject stale or revoked evidence','cases':['transition']} for event in sorted(EVENTS)]}
    plan={'execution':design,'resources':[{'path':p} for p in ['references/identity.md','references/shared.md','assets/lead.md','assets/identity.md']],
          'cases':[{'id':'actual','kind':'behavior','requirements':['R1'],'critical':True,'semantic':True},
                   {'id':'transition','kind':'command','requirements':['R1'],'critical':True,'semantic':False}]}
    return spec,plan


class ExecutionContractTests(unittest.TestCase):
    def test_complete_design_and_simple_skill(self):
        spec,plan=sample();check_execution(spec,plan)
        plan['execution']={'mode':'single','rationale':'No isolation needed','file_workflow':False,'file_reason':'Inline text', 'bindings':[], 'document_context':{'applicable':False,'reason':'Text transformation','sources':[]}}
        check_execution(spec,plan)

    def test_missing_role_coverage_and_ownership_are_rejected(self):
        edits=[lambda p:p['execution'].update(final_owner='unknown'),
               lambda p:p['execution']['roles'][1].update(recipient='user'),
               lambda p:p['execution'].update(coverage=[]),
               lambda p:p['execution']['coverage'][0].update(cases=['unknown']),
               lambda p:p['execution']['roles'][0].update(recipient='identity'),
               lambda p:p['execution']['roles'][1].update(method='missing.md'),
               lambda p:p['execution']['coverage'][0].update(roles=['lead']),
               lambda p:p['execution']['coverage'][0].update(status='unresolved')]
        for edit in edits:
            spec,plan=sample();edit(plan)
            with self.subTest(edit=edits.index(edit)),self.assertRaises(Invalid): check_execution(spec,plan)

    def test_lifecycle_omissions_and_behavior_only_controls_fail(self):
        for event in EVENTS:
            spec,plan=sample();plan['execution']['lifecycle']=[r for r in plan['execution']['lifecycle'] if r['event']!=event]
            with self.subTest(event=event),self.assertRaises(Invalid):check_execution(spec,plan)
        spec,plan=sample();plan['execution']['lifecycle'][0]['cases']=['actual']
        with self.assertRaises(Invalid):check_execution(spec,plan)

    def test_optional_missing_documents_do_not_become_approved_requirements(self):
        spec,plan=sample()
        doc={'id':'plan','kind':'implementation-plan','status':'missing','authority':'unknown','origin':'requested project document','version':'unknown','sections':[],'roles':['lead'],'requirements':[]}
        plan['execution']['document_context']['sources']=[doc];check_execution(spec,plan)
        doc['requirements']=['R1']
        with self.assertRaises(Invalid):check_execution(spec,plan)
        doc.update(status='available',authority='agreed',sections=['Acceptance']);check_execution(spec,plan)
        doc['roles']=['unregistered']
        with self.assertRaises(Invalid):check_execution(spec,plan)

    def test_effective_instructions_require_exact_complete_bound_reviews(self):
        _,plan=sample()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for row in plan['resources']:
                p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Assigned bounded instructions.\n')
            bundles=instruction_bundles(root,plan)
            rows=[{'role':b['role'],'host':b['host'],'bundle_sha256':b['bundle_sha256'],'accepted':True,'evidence':'Inspected identity, authority and return ownership together.'} for b in bundles]
            review={'execution_review':{'accepted':True,'evidence':'Actual loaded resources inspected','instruction_reviews':rows}}
            self.assertTrue(review_execution(root,plan,review))
            review['execution_review']['instruction_reviews']=rows[:-1]
            with self.assertRaises(Invalid):review_execution(root,plan,review)
            review['execution_review']['instruction_reviews']=rows
            (root/'references/shared.md').write_text('Changed shared authority.\n')
            with self.assertRaisesRegex(Invalid,'stale'):review_execution(root,plan,review)

    def test_claude_root_preload_cannot_be_hidden(self):
        _,plan=sample()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for row in plan['resources']:
                p=root/row['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Shared instructions.\n')
            (root/'SKILL.md').write_text('---\nname: fixture\ndescription: Review records.\n---\nAct as lead.\n')
            (root/'assets/identity.md').write_text('---\nname: identity\nskills: [fixture]\n---\nReturn to lead.\n')
            with self.assertRaisesRegex(Invalid,'omits'):instruction_bundles(root,plan)
            plan['execution']['roles'][1]['assets'][0]['loaded_paths'].append('SKILL.md')
            self.assertEqual(len(instruction_bundles(root,plan)),2)

    def test_protocol_versions_preserve_historical_plan_contracts(self):
        self.assertNotIn('execution',contracts.response_schema('plan',2)['properties']['data']['required'])
        self.assertIn('execution',contracts.response_schema('plan',3)['properties']['data']['required'])
        self.assertIn('execution_review',contracts.response_schema('review',3)['properties']['data']['required'])

    def test_new_run_requires_execution_plan_and_retains_single_agent_route(self):
        from runtime import workflow
        from fixtures import writer_fixture, RESEARCH, PRODUCE
        from test_workflow_coverage import WorkflowCoverageTests
        writer_fixture(self)
        spec,plan=WorkflowCoverageTests.normalizer(self)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            workflow.start(root,{'operation':'create','skill_name':'normalize-customers','brief':'Normalize supplied records','copyright_holder':'Fixture'}, protocol_version=3)
            def submit(data):
                packet=workflow.packet(root)
                return workflow.submit(root,{**{k:packet[k] for k in ('run_id','phase','packet_sha256')},'data':deepcopy(data)})
            submit(RESEARCH);submit(spec)
            with self.assertRaisesRegex(Invalid,'execution'):submit(plan)
            plan['execution']={'mode':'single','rationale':'One transformation','file_workflow':False,'file_reason':'Inline JSON input','bindings':[], 'document_context':{'applicable':False,'reason':'Supplied task defines normalization','sources':[]}}
            self.assertEqual(submit(plan)['phase'],'produce')
            self.assertEqual(submit(PRODUCE)['phase'],'evaluate')
            workflow.run_evaluation(root,allow_exec=True)
            packet=workflow.packet(root)
            self.assertEqual(packet['instruction_bundles'],[])
            self.assertEqual(packet['artifact_contract']['process_trace_schema'], contracts.PROCESS_TRACE)
            self.assertIn('execution_review',packet['response_schema']['properties']['data']['required'])

    def test_role_file_authority_must_resolve_declared_binding_access(self):
        for field,value in [('read_roots',['unknown']),('write_roots',['source']),('read_roots',['evidence'])]:
            spec,plan=sample();plan['execution']['roles'][1]['authority'][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(Invalid):check_execution(spec,plan)


    def test_authoring_packet_exposes_the_actual_process_trace_contract(self):
        validate(contracts.PROCESS_TRACE_EXAMPLE, contracts.PROCESS_TRACE)
        malformed = {"events": [{"step": "capture", "evidence": ["manifest"]}]}
        with self.assertRaises(Invalid):validate(malformed, contracts.PROCESS_TRACE)
        from evaluate import grade_process
        result = grade_process(contracts.PROCESS_TRACE_EXAMPLE, {"order": ["validate"], "visible": [], "evidence": ["validate"]})
        self.assertTrue(result['passed'])


    def test_claude_delegation_contract_matches_explicit_tools(self):
        _, plan = sample()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for row in plan['resources']:
                path = root / row['path']; path.parent.mkdir(parents=True, exist_ok=True); path.write_text('Shared instructions.\n')
            lead = root / 'assets/lead.md'
            lead.write_text('---\nname: lead\ntools: Read, Grep\n---\nDelegate assigned work.\n')
            with self.assertRaisesRegex(Invalid, 'omits the Agent tool'): instruction_bundles(root, plan)
            lead.write_text('---\nname: lead\ntools: Read, Grep, Agent(identity)\n---\nDelegate assigned identity review.\n')
            self.assertEqual(len(instruction_bundles(root, plan)), 2)


    def test_new_host_assets_use_package_roots_but_narrow_legacy_paths_survive(self):
        spec, plan = sample()
        old = plan['execution']['roles'][0]['assets'][0]['path']
        path = '.claude/agents/lead.md'
        plan['execution']['roles'][0]['assets'][0]['path'] = path
        next(row for row in plan['resources'] if row['path'] == old)['path'] = path
        with self.assertRaisesRegex(Invalid, 'package root responsibility'):check_execution(spec, plan)
        check_execution(spec, plan, legacy_paths={path})
