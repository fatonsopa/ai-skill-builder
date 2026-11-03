"""Static routing/packaging controls; these do not establish model behavior."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from runtime.artifacts import check_package
from repository_layout import check

REFERENCE = 'references/agents_and_skills.md'


class AgentGuidanceTests(unittest.TestCase):
    def test_authoring_consumers_resolve_the_single_reference(self):
        for name in ('SKILL.md', 'references/authoring.md', 'references/skill_structure.md'):
            path = ROOT / name
            links = re.findall(r'\]\(([^)]+)\)', path.read_text())
            resolved = [(path.parent / link).resolve() for link in links if '://' not in link]
            self.assertIn((ROOT / REFERENCE).resolve(), resolved, name)
        owners = [d['name'] for d in json.loads((ROOT / 'config/domains.json').read_text())['domains'] if REFERENCE in d['owned_paths']]
        self.assertEqual(owners, ['agent-authoring'])

    def test_missing_reference_is_a_located_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'SKILL.md').write_text('---\nname: control\ndescription: Control.\n---\nRead [rules](references/agents_and_skills.md).\n')
            result = check_package(root, full=False)
            self.assertFalse(result['passed'])
            self.assertTrue(any('references/agents_and_skills.md' in finding for finding in result['findings']))

    def test_simple_skill_needs_no_specialist_resources(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('README.md', 'AGENTS.md', 'LICENSE'):
                (root / name).write_text('A nonempty packaging control.\n')
            (root / 'CLAUDE.md').write_text('@AGENTS.md\n')
            (root / 'SKILL.md').write_text('---\nname: trim-names\ndescription: Trim supplied names.\n---\nTrim surrounding whitespace and preserve string identifiers.\n')
            self.assertTrue(check(root)['passed'])
            self.assertTrue(check_package(root, full=False)['passed'])

    def test_one_package_can_bundle_guidance_and_agent_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for name in ('README.md', 'AGENTS.md', 'LICENSE'):
                (root / name).write_text('A nonempty packaging control.\n')
            (root / 'CLAUDE.md').write_text('@AGENTS.md\n')
            (root / 'SKILL.md').write_text('---\nname: review-module\ndescription: Review supplied modules.\n---\nRead [rules](references/rules.md) and load [reviewer](assets/reviewer.md) when eligible.\n')
            (root / 'references').mkdir(); (root / 'assets').mkdir()
            (root / 'references/rules.md').write_text('Shared domain rules.\n')
            (root / 'assets/reviewer.md').write_text('Reviewer source asset; host activation requires validation.\n')
            self.assertTrue(check(root)['passed'])
            self.assertTrue(check_package(root, full=False)['passed'])

    def test_behavior_tasks_remain_distinct_and_runtime_resources_exist(self):
        cases = json.loads((ROOT / 'evals/agent_guidance_cases.json').read_text())
        self.assertEqual({c['id'] for c in cases}, {'agent-simple', 'agent-bundle', 'agent-recovery', 'agent-host', 'agent-authoring', 'agent-evidence', 'agent-client'})
        self.assertEqual(len(cases), 7)
        for case in cases:
            self.assertEqual(case['kind'], 'behavior')
            self.assertTrue(case['critical'] and case['semantic'])
            self.assertEqual(case['workflow']['scenario'], 'behavior')
            self.assertTrue(case['request']['instruction'].startswith('/skill-builder'))
            self.assertEqual(case['expect'], {'exit_code': 0})
            for resource in case['resources']:
                self.assertTrue((ROOT / resource).is_file())
                self.assertNotIn(resource.split('/')[0], {'evals', 'tests'})
        impact = json.loads((ROOT / 'config/test_impact.json').read_text())
        self.assertTrue(any('evals/agent_guidance_cases.json' in rule['paths'] and 'agent-guidance' in rule['tests'] for rule in impact['rules']))

    def test_reference_retains_authority_recovery_and_host_sections(self):
        text = (ROOT / REFERENCE).read_text()
        for heading in ('Define each delegation contract', 'Bound execution and recovery', 'Package guidance and host configuration', 'Verify the authored behavior', 'Source review'):
            self.assertIn('## ' + heading, text)
        urls = re.findall(r'\]\((https://[^)]+)\)', text)
        for host in ('learn.chatgpt.com', 'developers.openai.com', 'platform.claude.com', 'code.claude.com', 'www.anthropic.com'):
            self.assertTrue(any('/' + host + '/' in url for url in urls))


class AgentSkillsSourceTests(unittest.TestCase):
    """Check source ownership and routes, not the quality of their prose."""

    contracts = {
        'authoring': ('references/authoring.md', [
            'https://agentskills.io/skill-creation/best-practices',
            'https://agentskills.io/skill-creation/optimizing-descriptions',
            'https://agentskills.io/skill-creation/using-scripts',
            'https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions',
            'evaluation.md#test-activation-separately-from-performance']),
        'evaluation': ('references/evaluation.md', [
            'https://agentskills.io/skill-creation/optimizing-descriptions',
            'https://agentskills.io/skill-creation/evaluating-skills']),
        'host': ('references/host_support.md', [
            'https://agentskills.io/client-implementation/adding-skills-support',
            'https://learn.chatgpt.com/docs/build-skills',
            'agents_and_skills.md']),
    }

    def missing_links(self, text, expected):
        links = set(re.findall(r'\]\(([^)]+)\)', text))
        return [url for url in expected if url not in links]

    def test_owner_sources_and_routes_resolve(self):
        for owner, (name, expected) in self.contracts.items():
            path = ROOT / name
            text = path.read_text()
            self.assertEqual(self.missing_links(text, expected), [], owner)
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target:
                    continue
                relative, _, anchor = target.partition('#')
                destination = (path.parent / relative).resolve()
                self.assertTrue(destination.is_file(), (name, target))
                if anchor:
                    headings = re.findall(r'^#+ (.+)$', destination.read_text(), re.M)
                    anchors = {re.sub(r'[^a-z0-9 -]', '', h.lower()).replace(' ', '-') for h in headings}
                    self.assertIn(anchor, anchors, (name, target))

    def test_missing_source_in_each_owner_is_detected(self):
        for owner, (name, expected) in self.contracts.items():
            original = (ROOT / name).read_text()
            for link in expected:
                damaged = original.replace('](' + link + ')', '](missing-resource)')
                self.assertEqual(self.missing_links(damaged, expected), [link], owner)

    def test_guidance_routes_and_eval_impact_are_preserved(self):
        routes = (ROOT / REFERENCE).read_text()
        for target in ('authoring.md#describe-when-the-skill-applies', 'host_support.md#discovery-and-loading'):
            self.assertEqual(self.missing_links(routes, [target]), [])
        impact = json.loads((ROOT / 'config/test_impact.json').read_text())
        for path in ('references/evaluation.md', 'references/host_support.md'):
            self.assertTrue(any(path in r['paths'] and 'agent-guidance' in r['tests'] for r in impact['rules']), path)
