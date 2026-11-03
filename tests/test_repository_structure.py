"""Root structure, licensing, domain ownership and complete repository delivery."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from repository_layout import check
from runtime.artifacts import check_plan
from runtime.common import Invalid
from fixtures import PLAN, SPEC


class RepositoryStructureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ("SKILL.md", "README.md", "LICENSE", "AGENTS.md"):
            (self.root / name).write_text("A nonempty authored control.\n")
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n")

    def test_minimal_root_uses_only_needed_folders(self):
        self.assertTrue(check(self.root)["passed"])

    def test_missing_license_is_a_located_failure(self):
        (self.root / "LICENSE").unlink()
        self.assertFalse(check(self.root)["passed"])
        self.assertIn("LICENSE", {row["path"] for row in check(self.root)["findings"]})

    def test_nested_skill_entry_point_is_rejected(self):
        nested = self.root / "examples/archive/SKILL.md"
        nested.parent.mkdir(parents=True)
        nested.write_text("An archived entry point.\n")
        self.assertTrue(any("Nested skill" in row["problem"] for row in check(self.root)["findings"]))

    def test_root_bookkeeping_and_dist_have_clear_destinations(self):
        for name in ("requirements.txt", "documentation.json", "host_policy.json"):
            (self.root / name).write_text("old location")
        (self.root / "dist").mkdir()
        rows = check(self.root)["findings"]
        self.assertTrue(any("scripts/requirements.txt" in row["recommendation"] for row in rows))
        self.assertTrue(any("config/documentation.json" in row["recommendation"] for row in rows))
        self.assertTrue(any(row["path"] == "dist" for row in rows))

    def test_unowned_reference_blocks_a_plan(self):
        plan = deepcopy(PLAN)
        plan["resources"] = [{"path": "references/rules.md", "purpose": "Rules", "when": "Writing", "outputs": ["result"]}]
        with self.assertRaisesRegex(Invalid, "No domain owns"):
            check_plan(SPEC, plan)

    def test_overlapping_ownership_and_cycles_are_rejected(self):
        plan = deepcopy(PLAN)
        plan["domains"].append({"name": "second", "purpose": "Conflicting owner", "owned_paths": ["scripts/"], "depends_on": []})
        with self.assertRaisesRegex(Invalid, "Overlapping"):
            check_plan(SPEC, plan)
        plan = deepcopy(PLAN)
        plan["domains"][0]["depends_on"] = [plan["domains"][0]["name"]]
        with self.assertRaisesRegex(Invalid, "Cyclic"):
            check_plan(SPEC, plan)

    def test_checker_reports_declared_domain_cycle(self):
        (self.root / "config").mkdir()
        value = {"domains": [{"name": "one", "purpose": "A control", "owned_paths": ["SKILL.md"], "depends_on": ["one"]}]}
        (self.root / "config/domains.json").write_text(json.dumps(value))
        self.assertTrue(any("Cyclic" in row["problem"] for row in check(self.root)["findings"]))

    def test_root_mit_license_uses_the_generation_template(self):
        import re
        license_text = (ROOT / "LICENSE").read_text()
        template = (ROOT / "assets/MIT-LICENSE.txt").read_text()
        normalized = re.sub(r"(?m)^Copyright \(c\) \d{4} .+$", "Copyright (c) {year} {copyright_holder}", license_text)
        self.assertEqual(template, normalized)

    def test_copy_rejects_a_destination_aliased_back_into_the_source(self):
        from repository_files import copy_repository, inventory
        alias = self.root.parent / (self.root.name + "-alias")
        alias.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(alias.unlink)
        before = inventory(self.root)
        with self.assertRaises(ValueError):
            copy_repository(self.root, alias / "new-copy")
        self.assertEqual(before, inventory(self.root))
        self.assertFalse((self.root / "new-copy").exists())

    def test_claude_import_and_shared_instructions_are_required(self):
        (self.root / "CLAUDE.md").write_text("A separate set of rules.\n")
        self.assertTrue(any(row["path"] == "CLAUDE.md" for row in check(self.root)["findings"]))
        (self.root / "CLAUDE.md").write_text("@AGENTS.md\n")
        (self.root / "AGENTS.md").unlink()
        self.assertFalse(check(self.root)["passed"])

    def test_repository_copy_keeps_both_instruction_entry_points(self):
        from repository_files import copy_repository
        target = self.root.parent / (self.root.name + "-copy")
        import shutil
        self.addCleanup(shutil.rmtree, target, True)
        copy_repository(self.root, target)
        self.assertEqual((target / "AGENTS.md").read_text(), (self.root / "AGENTS.md").read_text())
        self.assertEqual((target / "CLAUDE.md").read_text(), "@AGENTS.md\n")

    def test_shared_root_rules_match_the_generation_template(self):
        template = (ROOT / "assets/AGENTS.md").read_text()
        instructions = (ROOT / "AGENTS.md").read_text()
        self.assertTrue(instructions.startswith(template))
        self.assertEqual((ROOT / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        # Builder-specific maintenance guidance must not leak into new skills.
        import re
        reference = "references/agents_and_skills.md"
        self.assertNotIn(reference, template)
        project_links = re.findall(r"\]\(([^)]+)\)", instructions[len(template):])
        self.assertIn(reference, project_links)
        self.assertTrue((ROOT / reference).is_file())
