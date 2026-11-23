"""Runner acceptance boundaries using authored Technical Writer transport controls."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from runtime import technical_writer as writer, workflow
from runtime.common import Invalid, inventory, load, save
from fixtures import payload, writer_fixture, validate_fixture_documents


class TechnicalWriterTests(unittest.TestCase):
    def setUp(self):
        self.dependency = writer_fixture(self)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = self.root / 'run'

    def produce(self, request=None, extra=None):
        args = {'operation': 'create', 'skill_name': 'normalize-customers', 'brief': 'Normalize customer JSON.', 'copyright_holder': 'Fixture'}
        args.update(request or {})
        workflow.start(self.run, args, protocol_version=1)
        for phase in ('research', 'specify', 'plan', 'produce'):
            data = payload(phase)
            if phase == 'produce' and extra:
                data['files'].update(extra)
            packet = workflow.packet(self.run)
            workflow.submit(self.run, {key: packet[key] for key in ('run_id', 'phase', 'packet_sha256')} | {'data': data})
        workflow.run_evaluation(self.run, allow_exec=True)

    def accept(self):
        packet = workflow.packet(self.run)
        data = {'reviewer': {'kind': 'human', 'identity': 'unit control', 'method': 'Authored transport control; not a real quality judgment.'}, 'cases': [], 'resource_findings': [{'path': name, 'accepted': True, 'evidence': 'Authored positive control.'} for name in packet['candidate_resources']]}
        return workflow.submit(self.run, {key: packet[key] for key in ('run_id', 'phase', 'packet_sha256')} | {'data': data})

    def ready(self):
        self.produce()
        validate_fixture_documents(self.run)
        state = self.accept()
        self.assertEqual(state['status'], 'ready')
        return state

    def test_perfect_evaluations_cannot_waive_missing_document_validation(self):
        self.produce()
        state = self.accept()
        self.assertEqual(state['evaluation']['metrics']['task_success_percent'], 100)
        self.assertFalse(state['document_check']['passed'])
        self.assertIsNone(state['best'])
        self.assertEqual(state['phase'], 'review')
        with self.assertRaises(Invalid):
            workflow.apply(self.run, self.root / 'delivered')
        validate_fixture_documents(self.run)
        self.assertEqual(self.accept()['status'], 'ready')

    def test_failed_checks_style_or_review_cannot_be_overridden(self):
        self.produce()
        validate_fixture_documents(self.run)
        for field in ('checks_passed', 'style_passed', 'accepted'):
            with self.subTest(field=field), self.assertRaisesRegex(Invalid, 'validation failed'):
                validate_fixture_documents(self.run, changes={field: False})
            self.assertNotIn('document_validation', workflow.read_state(self.run))
        self.assertNotEqual(self.accept()['status'], 'ready')
        attempts = workflow.read_state(self.run)['document_validation_attempts']
        self.assertEqual([row['status'] for row in attempts], ['accepted', 'not_accepted', 'not_accepted', 'not_accepted'])

    def test_missing_duplicate_or_unexpected_document_is_rejected(self):
        self.produce()
        validate_fixture_documents(self.run)
        manifest = next((self.run / 'writer-controls').glob('*/manifest.json'))
        original = load(manifest)
        for rows in (original[:-1], original + original[:1], [{**original[0], 'path': 'other.md'}, *original[1:]]):
            save(manifest, rows)
            with self.assertRaisesRegex(Invalid, 'every created or changed document exactly once'):
                writer.validate_documents(self.run, manifest)

    def test_undeclared_references_templates_metadata_and_custom_paths_are_required(self):
        state = {'request': {'operation': 'create', 'document_paths': ['scripts/prompt.custom', 'LICENSE', 'references/schema.json']}, 'source_snapshot': {}}
        names = ['AGENTS.md', 'CLAUDE.md', 'SKILL.md', 'README.md', 'references/guide.md', 'references/contract.rst', 'docs/help', 'assets/prompt.txt', 'assets/template.md', 'assets/template.yaml', 'assets/template', 'agents/openai.yaml', 'config/documentation.json', 'scripts/prompt.custom', 'LICENSE', 'references/schema.json']
        files = {name: 'sha' for name in [*names, 'scripts/code.py', 'config/data.json', 'assets/logo.png']}
        self.assertEqual(set(writer.documents(state, files)), set(names))

    def test_narrow_maintenance_requires_only_created_or_changed_documents(self):
        self.produce()
        state = workflow.read_state(self.run)
        state['request']['operation'] = 'modify'
        files = {'SKILL.md': 'same', 'references/changed.md': 'new', 'references/deleted.md': 'old', 'README.md': 'same'}
        state['source_snapshot'] = files
        after = {**files, 'references/changed.md': 'updated', 'docs/new.md': 'new'}
        del after['references/deleted.md']
        self.assertEqual(set(writer.documents(state, after)), {'references/changed.md', 'docs/new.md'})

    def test_wrong_kind_excerpt_review_bypass_and_unrelated_sources_are_rejected(self):
        self.produce()
        validate_fixture_documents(self.run)
        manifest = next((self.run / 'writer-controls').glob('*/manifest.json'))
        row = next(row for row in load(manifest) if row['path'] == 'SKILL.md')
        path = Path(row['session']) / 'state.json'
        original = load(path)
        for key, value in (('kind', 'explanation'), ('scope', 'excerpt'), ('operation', 'review'), ('sources', [{'text': 'Another request'}])):
            data = deepcopy(original)
            data['frozen']['request'][key] = value
            save(path, data)
            with self.subTest(key=key), self.assertRaises(Invalid):
                writer.validate_documents(self.run, manifest)
        save(path, original)

    def test_validated_documents_allow_ready_and_application(self):
        state = self.ready()
        destination = self.root / 'delivered'
        workflow.apply(self.run, destination)
        self.assertEqual(inventory(destination), state['best']['files'])
        self.assertEqual(workflow.apply(self.run)['status'], 'applied')

    def test_application_rechecks_missing_or_changed_receipts_and_copies(self):
        state = self.ready()
        binding = state['best']['document_validation']
        receipt = load(binding['record'])
        paths = [Path(binding['record']), *[Path(p) for p in receipt['evidence'][0]['files']], Path(receipt['evidence'][0]['destination'])]
        for path in paths:
            raw = path.read_bytes()
            try:
                path.write_bytes(raw + b' changed')
                with self.subTest(path=path), self.assertRaisesRegex(Invalid, 'delivery is blocked'):
                    workflow.apply(self.run, self.root / 'delivered')
                self.assertFalse((self.root / 'delivered').exists())
            finally:
                path.write_bytes(raw)

    def test_dependency_change_or_disappearance_blocks_delivery(self):
        self.ready()
        path = self.dependency / 'references/writing_style.md'
        path.write_text('Changed dependency guidance.')
        with self.assertRaisesRegex(Invalid, 'Technical Writer changed'):
            workflow.apply(self.run, self.root / 'delivered')

    def test_unavailable_dependency_cannot_deliver(self):
        with patch.dict(os.environ, {'SKILL_BUILDER_TECHNICAL_WRITER': str(self.root / 'missing')}):
            self.produce()
        state = self.accept()
        self.assertFalse(state['document_check']['passed'])
        self.assertNotEqual(state['status'], 'ready')

    def test_candidate_and_objective_changes_invalidate_document_evidence(self):
        self.ready()
        state = workflow.read_state(self.run)
        files = inventory(self.run / 'candidate')
        files['SKILL.md'] = 'different'
        self.assertFalse(writer.gate(self.run, state, files)['passed'])
        state['objective_sha256'] = 'another objective'
        self.assertFalse(writer.gate(self.run, state, inventory(self.run / 'candidate'))['passed'])

    def test_actual_validator_failure_and_unavailable_process_block_delivery(self):
        self.ready()
        for response in (subprocess.CompletedProcess([], 1, '', 'Validation failed'), subprocess.CompletedProcess([], 0, '{}', '')):
            with self.subTest(response=response), patch.object(writer.subprocess, 'run', return_value=response):
                with self.assertRaisesRegex(Invalid, 'delivery is blocked'):
                    workflow.apply(self.run, self.root / 'delivered')

    def test_replay_cannot_apply_changes(self):
        self.ready()
        state = workflow.read_state(self.run)
        state['replay_only'] = True
        save(self.run / 'state.json', state)
        with self.assertRaisesRegex(Invalid, 'replay cannot authorize delivery'):
            workflow.apply(self.run, self.root / 'delivered')

    def test_phase_packets_use_dependency_guidance_and_inventory_is_not_author_declared(self):
        self.produce()
        packet = workflow.packet(self.run)
        self.assertEqual(packet['technical_writer']['guidance']['references/writing_style.md'], (self.dependency / 'references/writing_style.md').read_text())
        self.assertNotIn('writing_style.md', packet['guidance'])
        self.assertEqual(set(packet['documents']), {'SKILL.md', 'README.md', 'AGENTS.md', 'CLAUDE.md', 'LICENSE', 'config/documentation.json'})
        self.assertEqual(set(packet['documents']) - set(packet['candidate_resources']), set())

    def test_generated_navigation_works_without_custom_repository_links(self):
        from runtime.readme import check
        self.produce()
        candidate = self.run / 'candidate'
        readme = (candidate / 'README.md').read_text()
        self.assertIn('## Documentation', readme)
        self.assertIn('[SKILL.md](SKILL.md)', readme)
        self.assertIn('[evals/cases.json](evals/cases.json)', readme)
        self.assertEqual(readme.count('## Documentation'), 1)
        self.assertTrue(check(candidate)['passed'])

    def test_archive_delivery_requires_validated_document_evidence(self):
        from runtime.delivery import package
        self.ready()
        source = self.run / 'candidate'
        with self.assertRaisesRegex(Invalid, 'validated run'):
            package(source, self.root / 'missing.zip')
        result = package(source, self.root / 'accepted.zip', run=self.run)
        self.assertTrue(Path(result['path']).is_file())
        state = workflow.read_state(self.run)
        Path(state['best']['document_validation']['record']).unlink()
        with self.assertRaisesRegex(Invalid, 'delivery is blocked'):
            package(source, self.root / 'rejected.zip', run=self.run)
        self.assertFalse((self.root / 'rejected.zip').exists())

    def test_cli_validates_documents_without_weakening_existing_checks(self):
        self.produce()
        validate_fixture_documents(self.run)
        manifest = next((self.run / 'writer-controls').glob('*/manifest.json'))
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/skill_builder_cli.py'), 'validate-documents', '--run', str(self.run), '--manifest', str(manifest)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['passed'])
        (self.run / 'candidate/scripts/normalize.py').write_text('Changed after evaluation')
        with self.assertRaisesRegex(Invalid, 'Candidate changed after evaluation'):
            writer.validate_documents(self.run, manifest)



class PlanningDocumentTests(unittest.TestCase):
    setUp = TechnicalWriterTests.setUp

    def test_planning_acceptance_uses_actual_documents_without_a_candidate(self):
        from fixtures import RESEARCH,SPEC
        from runtime.common import digest
        source=self.root/'source';source.mkdir();(source/'SKILL.md').write_text('Captured planning source.')
        workflow.start(self.run,{'operation':'specify','skill_name':'plan-control','brief':'Specify the scoped change.','source':str(source),'document_paths':['plan.md']},protocol_version=1)
        for data in (RESEARCH,SPEC):
            packet=workflow.packet(self.run)
            workflow.submit(self.run,{**{k:packet[k] for k in ('run_id','phase','packet_sha256')},'data':deepcopy(data)})
        authored=self.root/'authored';authored.mkdir();draft=authored/'plan.md';draft.write_text('# Scoped plan\n\nPreserve the supplied requirements.\n')
        state=workflow.read_state(self.run);session=self.root/'document-session'
        save(session/'state.json',{'frozen':{'request':{'kind':'explanation','operation':'review','scope':'complete','context':{},'sources':[{'id':'builder','text':writer.source_text(state)}],'destination':str(self.root/'accepted-plan.md')}}})
        review=session/'review.json';save(review,{'output_sha256':digest(draft.read_bytes()),'accepted':True,'checks_passed':True,'style_passed':True})
        manifest=self.root/'manifest.json';save(manifest,[{'path':'plan.md','session':str(session),'review':str(review)}])
        result=writer.validate_documents(self.run,manifest,authored)
        self.assertTrue(result['passed']);self.assertFalse((self.run/'candidate').exists())
        current=workflow.read_state(self.run)
        self.assertNotIn('evaluation',current)
        self.assertEqual((self.root/'accepted-plan.md').read_bytes(),draft.read_bytes())
        (self.run/'documents/plan.md').write_text('Changed after acceptance.')
        self.assertFalse(writer.gate(self.run,current,inventory(self.run/'documents'))['passed'])

if __name__ == '__main__':
    unittest.main()


class WriterIdentityTests(unittest.TestCase):
    """T50: resolve SpecDev and its legacy identity without silent fallback."""

    def setUp(self):
        import os
        from unittest.mock import patch
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        environment = {k: v for k, v in os.environ.items() if k != 'SKILL_BUILDER_TECHNICAL_WRITER'}
        for patcher in (patch.dict(os.environ, environment, clear=True), patch.object(Path, 'home', return_value=self.root / 'home'),
                        patch.object(writer, 'ROOT', self.root / 'workspace/skill-builder')):
            patcher.start(); self.addCleanup(patcher.stop)

    def writer(self, folder, name, validator=True):
        (folder / 'scripts').mkdir(parents=True)
        (folder / 'references').mkdir()
        (folder / 'SKILL.md').write_text('---\nname: ' + name + '\ndescription: Staged writer.\n---\nStaged copy.\n')
        (folder / 'references/writing_style.md').write_text('Style.\n')
        if validator:
            (folder / 'scripts/validate_document.py').write_text('print("{}")\n')
        return folder

    def test_t50_default_prefers_canonical_and_explicit_legacy_path_wins(self):
        canonical = self.writer(self.root / 'home/.agents/skills/specdev', 'specdev')
        self.writer(self.root / 'home/.claude/skills/technical-writer', 'technical-writer')
        selected = writer.capture({})
        self.assertEqual((selected['name'], selected['path']), ('specdev', str(canonical.resolve())))
        legacy = self.writer(self.root / 'explicit/technical-writer', 'technical-writer')
        for request in ({'technical_writer': str(legacy)}, {'technical_writer': str(legacy / 'SKILL.md')}):
            self.assertEqual(writer.capture(request)['path'], str(legacy.resolve()))
        import os
        os.environ['SKILL_BUILDER_TECHNICAL_WRITER'] = str(legacy)
        self.assertEqual(writer.capture({})['name'], 'technical-writer')

    def test_t50_explicit_unrelated_identity_or_missing_validator_is_rejected_without_fallback(self):
        self.writer(self.root / 'home/.agents/skills/specdev', 'specdev')
        unrelated = self.writer(self.root / 'explicit/notes-writer', 'notes-writer')
        with self.assertRaisesRegex(Invalid, "found 'notes-writer'"):
            writer.capture({'technical_writer': str(unrelated)})
        incomplete = self.writer(self.root / 'explicit/specdev', 'specdev', validator=False)
        with self.assertRaisesRegex(Invalid, 'Incomplete specdev dependency.*validate_document.py'):
            writer.capture({'technical_writer': str(incomplete)})
