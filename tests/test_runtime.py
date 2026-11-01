import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from runtime import contracts, workflow
from runtime.adapters import command, decode, invoke
from runtime.artifacts import check_package, check_plan
from runtime.common import Invalid, digest, inventory, load, save, validate
from runtime.examples import development_packet, ingest
from evaluate import evaluate, metrics, run_process, maintenance
from continuation import MAX_EXTENSIONS
from skill_builder_cli import main, replay
from fixtures import PLAN, PRODUCE, PROGRAM, SPEC, payload


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.run = self.root / "run"

    def start(self, **changes):
        request = {"operation": "create", "skill_name": "normalize-customers", "brief": "Normalize JSON records.", "copyright_holder": "Fixture Author"}
        request.update(changes)
        # These authored fixtures exercise the captured v1 protocol; v2 coverage is in test_workflow_coverage.
        return workflow.start(self.run, request, protocol_version=1)

    def submit(self, phase, data=None):
        packet = workflow.packet(self.run)
        self.assertEqual(packet["phase"], phase)
        return workflow.submit(self.run, {
            "run_id": packet["run_id"], "phase": phase,
            "packet_sha256": packet["packet_sha256"],
            "data": payload(phase) if data is None else data,
        })

    def produced(self, request=None, plan=None, produce=None, spec=None):
        self.start(**(request or {}))
        self.submit("research")
        self.submit("specify", spec)
        self.submit("plan", plan)
        self.submit("produce", produce)

    def review(self, accepted=True):
        state = workflow.read_state(self.run)
        resources = {"SKILL.md", "README.md", "AGENTS.md", "CLAUDE.md"} | {r["path"] for r in state["data"]["plan"]["resources"]}
        if state["request"]["operation"] in {"modify", "refactor"}:
            resources &= set(inventory(self.run / "candidate"))
        return {
            "reviewer": {"kind": "human", "identity": "fixture-author", "method": "Authored control; not independent human calibration."},
            "cases": [
                {"id": case["id"], "accepted": accepted, "rationale": "Fixture label for protocol testing."}
                for case in state["data"]["plan"]["cases"] if case["semantic"]
            ],
            "resource_findings": [
                {"path": path, "accepted": accepted, "evidence": "Inspected generated resource in this offline control."}
                for path in sorted(resources)
            ],
        }

    def ready(self):
        self.produced()
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit("review", self.review())
        self.assertEqual(workflow.read_state(self.run)["status"], "ready")

    def legacy(self):
        source = self.root / "legacy"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: normalize-customers\ndescription: Normalize records.\n---\n\nKeep policy EXACT.\n")
        (source / "keep.txt").write_text("original")
        (source / "scripts").mkdir()
        (source / "scripts/normalize.py").write_text(PROGRAM)
        return source

    def test_new_skill_has_mit_license_and_root_repository_contract(self):
        self.produced()
        target = self.run / "candidate"
        self.assertIn("Copyright (c)", (target / "LICENSE").read_text())
        self.assertIn("Fixture Author", (target / "LICENSE").read_text())
        self.assertTrue((target / "config/domains.json").is_file())
        self.assertTrue((target / "config/repository_layout.json").is_file())
        self.assertFalse((target / "documentation.json").exists())
        self.assertFalse((target / "host_policy.json").exists())
        self.assertFalse((target / "distribution.json").exists())
        self.assertFalse((target / "dist").exists())

    def test_generated_repository_keeps_testing_and_push_approval_rules(self):
        self.produced()
        root = self.run / "candidate"
        instructions = (root / "AGENTS.md").read_text()
        self.assertIn("scripts/run_tests.py --execute", instructions)
        self.assertIn("Do not push to GitHub without the user's explicit approval", instructions)
        self.assertEqual((root / "CLAUDE.md").read_text(), "@AGENTS.md\n")
        self.assertTrue(check_package(root)["passed"])
        workflow.run_evaluation(self.run, allow_exec=True)
        report = self.review()
        report["resource_findings"] = [row for row in report["resource_findings"] if row["path"] != "AGENTS.md"]
        with self.assertRaisesRegex(Invalid, "every declared"):
            self.submit("review", report)

    def test_broad_development_tests_are_blocked_before_execution(self):
        plan = deepcopy(PLAN)
        plan["cases"][0]["command"] = ["{python}", "-m", "unittest", "discover", "-s", "tests"]
        with self.assertRaisesRegex(Invalid, "Unrestricted test discovery"):
            check_plan(SPEC, plan)
        with patch("runtime.workflow.check_plan"):
            self.produced(plan=plan)
        with patch("runtime.workflow.evaluate") as execute:
            with self.assertRaisesRegex(Invalid, "blocked during iteration"):
                workflow.run_evaluation(self.run, allow_exec=True)
            execute.assert_not_called()

    def test_generated_impacted_runner_executes_selected_case_ids(self):
        self.produced()
        package = self.run / "candidate"
        result = subprocess.run([sys.executable, "scripts/run_tests.py", "--changed", "scripts/normalize.py", "--execute"], cwd=package, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["mode"], "impacted")
        self.assertEqual({row["id"] for row in report["checks"]}, {case["id"] for case in PLAN["cases"]})
        self.assertTrue(all("--case" in row["argv"] for row in report["checks"]))
        blocked = subprocess.run([sys.executable, "scripts/run_tests.py", "--changed", "scripts/normalize.py", "--full"], cwd=package, text=True, capture_output=True)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("Full suites are disabled", blocked.stderr)

    def test_creation_requires_actual_copyright_holder(self):
        self.start()
        state = workflow.read_state(self.run)
        del state["request"]["copyright_holder"]
        save(self.run / "state.json", state)
        self.submit("research")
        self.submit("specify")
        self.submit("plan")
        with self.assertRaisesRegex(Invalid, "copyright_holder"):
            self.submit("produce")

    def test_audit_exposes_automatic_structure_findings(self):
        source = self.legacy()
        self.start(operation="audit", source=str(source))
        packet = workflow.packet(self.run)
        self.assertFalse(packet["structure_review"]["passed"])
        self.assertIn("LICENSE", {row["path"] for row in packet["structure_review"]["findings"]})

    def test_structural_refactor_migrates_files_and_removes_empty_old_directories(self):
        source = self.legacy()
        (source / "old").mkdir()
        (source / "old/requirements.txt").write_text("# no third-party dependencies\n")
        plan = deepcopy(PLAN)
        plan["domains"][0]["owned_paths"].extend(["assets/keep.txt", "scripts/requirements.txt"])
        files = {
            "README.md": "# Normalize customers\n\nRun scripts/normalize.py.\n",
            "AGENTS.md": (SCRIPTS.parent / "assets/AGENTS.md").read_text(),
            "CLAUDE.md": "@AGENTS.md\n",
            "LICENSE": (SCRIPTS.parent / "LICENSE").read_text(),
            "assets/keep.txt": "original",
            "scripts/requirements.txt": (source / "old/requirements.txt").read_text(),
            "config/domains.json": json.dumps({"domains": plan["domains"]}),
        }
        removed = ["keep.txt", "old/requirements.txt"]
        allowed = list(files) + removed
        plan["allowed_candidate_paths"] = allowed
        produce = deepcopy(PRODUCE)
        produce["files"] = files
        produce["remove"] = removed
        self.produced(request={"operation": "refactor", "source": str(source), "allowed_paths": allowed, "repair_structure": True}, plan=plan, produce=produce)
        workflow.run_evaluation(self.run, allow_exec=True)
        self.assertEqual(self.submit("review", self.review())["status"], "ready")
        workflow.apply(self.run)
        self.assertFalse((source / "old").exists())
        self.assertEqual((source / "scripts/requirements.txt").read_text(), "# no third-party dependencies\n")
        self.assertTrue(check_package(source, full=False, structure=True)["passed"])
        workflow.recover(self.run)
        self.assertTrue((source / "old/requirements.txt").exists())

    def test_real_transformation_and_clean_export(self):
        self.ready()
        state = workflow.read_state(self.run)
        self.assertEqual(state["evaluation"]["metrics"]["accepted"], 5)
        destination = self.root / "installed"
        workflow.apply(self.run, destination)
        process = subprocess.run(
            [sys.executable, "scripts/normalize.py"], cwd=destination,
            input='{"id":"0007","name":"  Zoe  "}', capture_output=True, text=True,
        )
        self.assertEqual(json.loads(process.stdout), {"customer_id": "0007", "display_name": "Zoe"})
        self.assertEqual(inventory(destination), state["best"]["files"])
        self.assertTrue(check_package(destination)["passed"])

    def test_bad_schema_and_real_date_rejected(self):
        self.start()
        with self.assertRaises(Invalid):
            self.submit("research", {"sources": [{"url": "bad", "checked": "2026-99-12", "decision": "test", "provenance": "user_supplied"}], "findings": "test", "gaps": []})
        with self.assertRaises(Invalid):
            validate({"operation": "create", "skill_name": "../escape", "brief": "x"}, contracts.REQUEST)

    def test_stale_response_and_repeat_submission(self):
        self.start()
        packet = workflow.packet(self.run)
        response = {"run_id": packet["run_id"], "phase": "research", "packet_sha256": "0" * 64, "data": payload("research")}
        with self.assertRaises(Invalid):
            workflow.submit(self.run, response)
        response["packet_sha256"] = packet["packet_sha256"]
        workflow.submit(self.run, response)
        workflow.submit(self.run, response)
        self.assertEqual(len(workflow.read_state(self.run)["history"]), 1)

    def test_unresolved_ambiguity_cannot_advance(self):
        self.start()
        self.submit("research")
        spec = deepcopy(SPEC)
        spec["ambiguities"] = ["Is a numeric identifier valid?"]
        with self.assertRaises(Invalid):
            self.submit("specify", spec)

    def test_all_requirements_need_actual_cases(self):
        plan = deepcopy(PLAN)
        plan["cases"] = plan["cases"][:1]
        with self.assertRaises(Invalid):
            check_plan(SPEC, plan)
        plan = deepcopy(PLAN)
        plan["cases"].append(deepcopy(plan["cases"][0]))
        with self.assertRaises(Invalid):
            check_plan(SPEC, plan)

    def test_specification_only_stops_without_implementation(self):
        self.start(operation="specify")
        self.submit("research")
        result = self.submit("specify")
        self.assertEqual(result["status"], "complete")
        self.assertFalse((self.run / "candidate").exists())
        with self.assertRaises(Invalid):
            workflow.apply(self.run, self.root / "target")

    def test_audit_has_no_candidate_or_source_mutations(self):
        source = self.legacy()
        before = inventory(source)
        self.start(operation="audit", source=str(source))
        self.submit("research")
        result = self.submit("audit", {"findings": [], "recommendation": "retain", "rationale": "No demonstrated defect in this control."})
        self.assertEqual(result["status"], "complete")
        self.assertEqual(inventory(source), before)
        self.assertFalse((self.run / "candidate").exists())

    def test_path_escape_and_symlink_rejected(self):
        bad = deepcopy(PRODUCE)
        bad["files"] = {"../escape": "bad"}
        with self.assertRaises(Invalid):
            self.produced(produce=bad)
        self.assertFalse((self.run / "escape").exists())
        folder = self.root / "linked"
        folder.mkdir()
        (folder / "outside").symlink_to(self.root / "run")
        with self.assertRaises(Invalid):
            inventory(folder)

    def test_managed_file_override_rejected(self):
        bad = deepcopy(PRODUCE)
        bad["files"]["evals/cases.json"] = "[]"
        with self.assertRaises(Invalid):
            self.produced(produce=bad)

    def test_schema_valid_wrong_answer_cannot_be_graded_away(self):
        bad = deepcopy(PRODUCE)
        bad["files"]["scripts/normalize.py"] = PROGRAM.replace('record["id"],', 'str(len(record["id"])),')
        self.produced(produce=bad)
        report = workflow.run_evaluation(self.run, allow_exec=True)
        self.assertGreater(report["metrics"]["critical_failures"], 0)
        result = self.submit("review", self.review(accepted=True))
        self.assertNotEqual(result["status"], "ready")
        with self.assertRaises(Invalid):
            workflow.apply(self.run, self.root / "target")

    def test_command_execution_is_explicit(self):
        self.produced()
        report = workflow.run_evaluation(self.run)
        self.assertEqual(report["metrics"]["coverage_percent"], 0)
        self.assertTrue(all(case["status"] == "not_run" for case in report["attempts"]))

    def test_revision_repairs_failure_under_same_objective(self):
        bad = deepcopy(PRODUCE)
        bad["files"]["scripts/normalize.py"] = "print('{}')\n"
        self.produced(produce=bad)
        objective = workflow.read_state(self.run)["objective_sha256"]
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit("review", self.review())
        workflow.revise(self.run, "Replace the broken transformation with the agreed identifier-preserving logic.")
        self.submit("produce")
        workflow.run_evaluation(self.run, allow_exec=True)
        result = self.submit("review", self.review())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["objective_sha256"], objective)
        self.assertFalse(load(self.run / "experiments/000/decision.json")["keep"])
        self.assertTrue(load(self.run / "experiments/001/decision.json")["keep"])

    def test_target_met_prevents_unbounded_optimization(self):
        self.ready()
        with self.assertRaises(Invalid):
            workflow.revise(self.run, "Run forever.")

    def test_trial_budget_enforced(self):
        self.produced(request={"limits": {"max_experiments": 1}})
        with self.assertRaises(Invalid):
            workflow.revise(self.run, "Another trial.")

    def test_frozen_objective_tamper_detected(self):
        self.produced()
        state = load(self.run / "state.json")
        state["data"]["plan"]["target_success_percent"] = 0
        save(self.run / "state.json", state)
        with self.assertRaises(Invalid):
            workflow.run_evaluation(self.run, allow_exec=True)

    def test_managed_document_drift_detected(self):
        self.produced()
        (self.run / "candidate/README.md").write_text("Unrelated replacement")
        result = check_package(self.run / "candidate")
        self.assertFalse(result["passed"])
        self.assertIn("Managed-file drift: README.md", result["findings"])

    def test_semantic_review_is_required_and_cannot_override_execution(self):
        spec = deepcopy(SPEC)
        spec["requirements"][0]["kind"] = "semantic"
        plan = deepcopy(PLAN)
        for case in plan["cases"]:
            if "R-1" in case["requirements"]:
                case["semantic"] = True
        self.produced(spec=spec, plan=plan)
        report = workflow.run_evaluation(self.run, allow_exec=True)
        self.assertEqual(report["metrics"]["pending_review"], 3)
        bad = self.review()
        bad["cases"] = []
        with self.assertRaises(Invalid):
            self.submit("review", bad)
        self.assertEqual(self.submit("review", self.review())["status"], "ready")

    def test_candidate_changed_after_evaluation_blocks_review(self):
        self.produced()
        workflow.run_evaluation(self.run, allow_exec=True)
        (self.run / "candidate/scripts/normalize.py").write_text("print('tampered')")
        with self.assertRaises(Invalid):
            self.submit("review", self.review())

    def test_narrow_change_rejects_unrelated_file(self):
        source = self.legacy()
        with self.assertRaises(Invalid):
            self.produced(request={"operation": "modify", "source": str(source), "allowed_paths": ["scripts/normalize.py"]}, produce={**deepcopy(PRODUCE), "files": {"keep.txt": "overwritten"}})
        self.assertEqual((source / "keep.txt").read_text(), "original")

    def test_stale_source_prevents_application(self):
        self.ready()
        destination = self.root / "target"
        destination.mkdir()
        (destination / "user.txt").write_text("new work")
        with self.assertRaises(Invalid):
            workflow.apply(self.run, destination)
        self.assertEqual((destination / "user.txt").read_text(), "new work")

    def test_recovery_does_not_overwrite_newer_user_work(self):
        self.ready()
        target = self.root / "target"
        workflow.apply(self.run, target)
        (target / "README.md").write_text("User's newer work")
        result = workflow.recover(self.run)
        self.assertEqual(result["status"], "recovery_conflict")
        self.assertEqual(result["conflicts"], ["README.md"])
        self.assertEqual((target / "README.md").read_text(), "User's newer work")

    def test_complete_recovery_and_repeat_recovery(self):
        self.ready()
        target = self.root / "target"
        workflow.apply(self.run, target)
        self.assertEqual(workflow.recover(self.run)["status"], "recovered")
        self.assertEqual(inventory(target), {})
        self.assertEqual(workflow.recover(self.run)["status"], "recovered")

    def test_capture_feedback_preserves_output_scope(self):
        self.start()
        record = workflow.feedback(self.run, "The title is unclear.")
        self.assertEqual(record["scope"], "current_output")
        self.assertEqual(record["reproduction"], "not_run")
        maintained = workflow.feedback(self.run, "Fix future titles too.", maintenance=True)
        self.assertEqual(maintained["scope"], "persistent_maintenance")
        self.assertEqual(workflow.read_state(self.run)["phase"], "research")

    def test_mechanical_replay_rebuilds_without_fresh_processes(self):
        self.ready()
        files = inventory(self.run / "candidate")
        with patch("evaluate.run_process", side_effect=AssertionError("Replay must not call a process")):
            result = replay(self.run)
        self.assertEqual(result["rebuilt_files"], files)
        self.assertEqual(result["rebuilt_status"], "ready")
        self.assertEqual(result["fresh_model_calls"], 0)

    def test_metric_denominators_and_no_observations(self):
        rows = [{"status": "passed"}] * 8 + [{"status": "failed"}] * 2 + [{"status": "infrastructure_failure"}] * 2
        score = metrics(rows, 12)
        self.assertEqual(score["task_success_percent"], 80)
        self.assertAlmostEqual(score["coverage_percent"], 83.3333333333)
        self.assertIsNone(metrics([], 0)["task_success_percent"])
        self.assertIsNone(metrics([], 0)["coverage_percent"])

    def test_model_calls_disabled_by_default(self):
        self.start()
        with patch("subprocess.run", side_effect=AssertionError("No live call permitted")):
            with self.assertRaises(Invalid):
                invoke(self.run, "codex", "test-model")

    def test_model_identifier_and_missing_structured_result(self):
        with self.assertRaises(Invalid):
            command("codex", "--unsafe", self.root / "schema", self.root / "out")
        with self.assertRaises(Invalid):
            decode("claude", '{"result":"looks successful"}', self.root / "out")

    def test_model_failure_record_and_no_silent_substitution(self):
        self.start(limits={"max_live_calls": 1})
        fake = subprocess.CompletedProcess([], 2, "", "model unavailable")
        with patch("shutil.which", return_value="/test/codex"), patch("runtime.adapters.run_process", return_value=fake) as call:
            result = invoke(self.run, "codex", "requested-exact-model")
        self.assertEqual(result["status"], "failed")
        self.assertIn("requested-exact-model", call.call_args.args[0])
        self.assertEqual(load(self.run / "model_results/001.json")["requested_model"], "requested-exact-model")
        with self.assertRaises(Invalid):
            invoke(self.run, "codex", "different-model")

    def example_manifest(self, rows):
        save(self.root / "input.json", {"id": "0042"})
        save(self.root / "output.json", {"customer_id": "0042"})
        save(self.root / "pairs.json", rows)
        return self.root / "pairs.json"

    def example_row(self, identifier="one", family="source-one", split="development"):
        return {"id": identifier, "source_family": family, "input": "input.json", "output": "output.json", "split": split, "provenance": "real"}

    def test_example_preservation_and_no_claim_of_holdout(self):
        result = ingest(self.example_manifest([self.example_row()]), self.root / "examples")
        self.assertEqual(result["independent_protected_families"], 0)
        self.assertEqual(load(self.root / "examples/originals/000-input.json")["id"], "0042")
        self.assertEqual(len(development_packet(self.root / "examples")["development_pairs"]), 1)

    def test_related_and_duplicate_examples_cannot_cross_splits(self):
        for same_family in [True, False]:
            rows = [self.example_row(), self.example_row("two", "source-one" if same_family else "source-two", "protected")]
            with self.subTest(same_family=same_family), self.assertRaises(Invalid):
                ingest(self.example_manifest(rows), self.root / "examples")

    def test_unsupported_documents_reported(self):
        (self.root / "scan.pdf").write_bytes(b"%PDF-not-a-parser-test")
        row = self.example_row()
        row["input"] = "scan.pdf"
        with self.assertRaisesRegex(Invalid, "Unsupported example format"):
            ingest(self.example_manifest([row]), self.root / "examples")

    def test_cli_errors_are_json_and_nonzero(self):
        with contextlib.redirect_stderr(io.StringIO()) as stream:
            code = main(["status", "--run", str(self.root / "missing")])
        self.assertEqual(code, 2)
        self.assertIn("error", json.loads(stream.getvalue()))

    def test_structured_writing_family_and_resource_review(self):
        spec = {
            "purpose": "Render a bug report from supplied facts.",
            "inputs": "JSON containing the report facts.", "outputs": "A Markdown bug report.",
            "requirements": [
                {"id": "B-1", "text": "Separate expected and actual results; include reproduction and relevant files.", "kind": "semantic"}
            ],
            "assumptions": [], "ambiguities": [],
        }
        plan = deepcopy(PLAN)
        plan["domains"] = [{"name": "bug-reports", "purpose": "Render sourced bug reports.", "owned_paths": ["scripts/report.py", "references/bug_report.md"], "depends_on": []}]
        plan["resources"] = [{"path": "references/bug_report.md", "purpose": "Define report content and unknown values.", "when": "preparing report facts", "outputs": ["bug-report"]}]
        plan["cases"] = [{
            "id": "bug-report", "requirements": ["B-1"], "critical": True,
            "kind": "command", "command": ["{python}", "scripts/report.py"],
            "stdin": {"title": "Save fails", "expected": "The name is saved.", "actual": "An error appears.", "steps": "1. Change the name.\n2. Click Save."},
            "expect": {"exit_code": 0, "contains": ["## Expected results", "## Actual results", "## How to reproduce", "## Relevant files", "Not provided."]},
            "semantic": True,
        }]
        plan["allowed_candidate_paths"] = ["scripts/report.py", "references/bug_report.md"]
        program = '''import json, sys
r = json.load(sys.stdin)
print("# " + r["title"])
for title, field in [("How to reproduce", "steps"), ("Expected results", "expected"), ("Actual results", "actual"), ("Relevant files", "relevant_files")]:
    print("\\n## " + title + "\\n\\n" + r.get(field, "Not provided."))
'''
        produce = deepcopy(PRODUCE)
        produce["files"] = {
            "scripts/report.py": program,
            "references/bug_report.md": "# Bug report\n\nUse supplied facts. Separate expected and actual results. Include How to reproduce and Relevant files. Leave unknown information explicit.\n",
        }
        self.produced(spec=spec, plan=plan, produce=produce)
        report = workflow.run_evaluation(self.run, allow_exec=True)
        self.assertEqual(report["metrics"]["pending_review"], 1)
        self.assertEqual(report["attempts"][0]["failures"], [])
        result = self.submit("review", self.review())
        self.assertEqual(result["status"], "ready")

    def test_narrow_rename_updates_links_and_preserves_unrelated_files(self):
        source = self.legacy()
        (source / "references").mkdir()
        (source / "references/old.md").write_text("# Old guide\n")
        skill = (source / "SKILL.md").read_text()
        (source / "SKILL.md").write_text(skill + "\n[Old guide](references/old.md)\n")
        allowed = ["SKILL.md", "references/old.md", "references/new.md"]
        plan = deepcopy(PLAN)
        plan["allowed_candidate_paths"] = allowed
        plan["domains"][0]["owned_paths"].append("references/new.md")
        plan["resources"] = [{"path": "references/new.md", "purpose": "Explain this task.", "when": "needed", "outputs": ["normalized-record"]}]
        produce = deepcopy(PRODUCE)
        produce["files"] = {
            "SKILL.md": skill + "\n[New guide](references/new.md)\n",
            "references/new.md": "# New guide\n\nKeep policy EXACT.\n",
        }
        produce["remove"] = ["references/old.md"]
        self.produced(request={"operation": "refactor", "source": str(source), "allowed_paths": allowed, "preserve_literals": ["Keep policy EXACT."]}, plan=plan, produce=produce)
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit("review", self.review())
        workflow.apply(self.run)
        self.assertFalse((source / "references/old.md").exists())
        self.assertTrue((source / "references/new.md").exists())
        self.assertEqual((source / "keep.txt").read_text(), "original")
        self.assertNotIn("Old guide", (source / "SKILL.md").read_text())
        workflow.recover(self.run)
        self.assertTrue((source / "references/old.md").exists())

    def test_best_candidate_survives_worse_experiment_and_stagnation(self):
        plan = deepcopy(PLAN)
        for case in plan["cases"]:
            case["critical"] = False
        bad = deepcopy(PRODUCE)
        bad["files"]["scripts/normalize.py"] = PROGRAM.replace("name.strip()", "name")
        self.produced(plan=plan, produce=bad, request={"limits": {"max_stagnant_experiments": 1}})
        workflow.run_evaluation(self.run, allow_exec=True)
        initial = self.submit("review", self.review())
        self.assertEqual(initial["status"], "needs_improvement")
        best_files = initial["best"]["files"]
        workflow.revise(self.run, "Deliberately worse control.")
        worse = deepcopy(PRODUCE)
        worse["files"]["scripts/normalize.py"] = "print('{}')"
        self.submit("produce", worse)
        workflow.run_evaluation(self.run, allow_exec=True)
        result = self.submit("review", self.review())
        self.assertFalse(result["last_decision"]["keep"])
        self.assertEqual(inventory(self.run / "candidate"), best_files)
        with self.assertRaisesRegex(Invalid, "Stagnation"):
            workflow.revise(self.run, "Another worse trial.")

    def test_timeout_kills_child_group_and_budget_stops_other_cases(self):
        import time
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            run_process(
                [sys.executable, "-c", "import subprocess,time; subprocess.Popen(['sleep','10']); time.sleep(10)"],
                input="", cwd=self.root, timeout=0.1,
            )
        self.assertLess(time.monotonic() - started, 3)
        self.produced()
        with patch("evaluate.run_process", side_effect=AssertionError("No budget remains")):
            result = evaluate(self.run / "candidate", PLAN["cases"], True, max_seconds=0)
        self.assertEqual(result["metrics"]["evaluated"], 0)

    def test_missing_frontmatter_close_is_invalid(self):
        source = self.legacy()
        (source / "SKILL.md").write_text("---\nname: normalize-customers\ndescription: Broken\n")
        self.assertFalse(check_package(source, full=False)["passed"])

    def test_feedback_closure_requires_applied_passing_case(self):
        self.ready()
        record = workflow.feedback(self.run, "Preserve identifiers.", maintenance=True)
        with self.assertRaises(Invalid):
            workflow.resolve_feedback(self.run, record["id"], "defect", self.run, "leading-zero")
        workflow.apply(self.run, self.root / "target")
        result = workflow.resolve_feedback(self.run, record["id"], "defect", self.run, "leading-zero")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["resolution"]["case_id"], "leading-zero")

    def test_protected_examples_are_not_in_author_packet(self):
        save(self.root / "private-input.json", {"id": "private-27"})
        save(self.root / "private-output.json", {"customer_id": "secret-answer-27"})
        row = self.example_row("private", "private-family", "protected")
        row.update(input="private-input.json", output="private-output.json")
        path = self.example_manifest([self.example_row(), row])
        ingest(path, self.root / "examples")
        self.start(examples=str(self.root / "examples"))
        packet = workflow.packet(self.run)
        self.assertEqual(packet["examples"]["independent_protected_families"], 1)
        self.assertNotIn("secret-answer-27", json.dumps(packet))

    def test_replay_detects_corrupted_event_history(self):
        self.ready()
        path = self.run / "events.jsonl"
        path.write_text(path.read_text().replace("response_accepted", "not_accepted", 1))
        with self.assertRaises(Invalid):
            replay(self.run)

    def benchmark_config(self, **changes):
        source = self.legacy()
        config = {
            "subject": str(source),
            "models": [
                {"provider": "codex", "model": "model-a", "repetitions": 2},
                {"provider": "claude", "model": "model-b", "repetitions": 1},
            ],
            "cases": [{
                "id": "extract", "request": {"id": "0042"}, "resources": [],
                "expected": {"id": "0042"}, "semantic": False, "critical": True,
                "split": "regression",
            }],
            "compare_without_skill": False, "max_invocations": 3, "max_seconds": 30,
        }
        config.update(changes)
        save(self.root / "benchmark.json", config)
        return self.root / "benchmark.json"

    def test_model_matrix_keeps_counts_and_failures_separate(self):
        from runtime.benchmark import benchmark
        results = [
            {"status": "response_validated", "response": {"id": "0042"}},
            {"status": "response_validated", "response": {"id": "42"}},
            {"status": "infrastructure_failure", "error": "unavailable"},
        ]
        with patch("runtime.benchmark.sample", side_effect=results):
            report = benchmark(self.benchmark_config(), self.root / "observations")
        first = report["by_model_and_condition"]["codex:model-a:with_skill"]
        second = report["by_model_and_condition"]["claude:model-b:with_skill"]
        self.assertEqual(first["task_success_percent"], 50)
        self.assertEqual(first["evaluated"], 2)
        self.assertEqual(second["coverage_percent"], 0)
        self.assertIsNone(second["task_success_percent"])

    def test_model_matrix_does_not_send_expected_answers(self):
        from runtime.benchmark import benchmark
        path = self.benchmark_config(max_invocations=1)
        data = load(path)
        data["cases"][0]["expected"] = "PRIVATE EXPECTED ANSWER"
        save(path, data)
        with patch("runtime.benchmark.sample", return_value={"status": "response_validated", "response": "wrong"}) as call:
            report = benchmark(path, self.root / "observations")
        self.assertNotIn("PRIVATE EXPECTED ANSWER", json.dumps(call.call_args.args[2]))
        self.assertEqual(report["model_invocations"], 1)
        self.assertEqual(sum(row["status"] == "not_run" for row in report["attempts"]), 2)

    def test_protected_matrix_cannot_be_reused_for_tuning(self):
        from runtime.benchmark import benchmark
        path = self.benchmark_config(max_invocations=1, acceptance_ledger="acceptance.json")
        data = load(path)
        data["cases"][0]["split"] = "protected"
        save(path, data)
        with patch("runtime.benchmark.sample", return_value={"status": "response_validated", "response": {"id": "0042"}}):
            benchmark(path, self.root / "observations")
        with self.assertRaisesRegex(Invalid, "exposed"):
            benchmark(path, self.root / "new-observations")

    def test_semantic_matrix_grades_retain_original_observations(self):
        from runtime.benchmark import benchmark, grade
        path = self.benchmark_config(max_invocations=1)
        data = load(path)
        data["models"] = data["models"][:1]
        data["models"][0]["repetitions"] = 1
        data["cases"][0]["semantic"] = True
        save(path, data)
        with patch("runtime.benchmark.sample", return_value={"status": "response_validated", "response": "acceptable alternative"}):
            report = benchmark(path, self.root / "observations")
        original = (self.root / "observations/report.json").read_bytes()
        reviews = {
            "report_sha256": digest(report),
            "reviewer": {"kind": "human", "identity": "fixture-author", "method": "Authored control."},
            "cases": [{"id": "OBS-0001", "accepted": True, "rationale": "Control label."}],
        }
        save(self.root / "reviews.json", reviews)
        graded = grade(self.root / "observations/report.json", self.root / "reviews.json")
        self.assertEqual(graded["attempts"][0]["status"], "passed")
        self.assertEqual((self.root / "observations/report.json").read_bytes(), original)

    def test_model_matrix_zero_allowance_never_calls_models(self):
        from runtime.benchmark import benchmark
        with patch("runtime.benchmark.sample", side_effect=AssertionError("No call permitted")):
            report = benchmark(self.benchmark_config(max_invocations=0), self.root / "observations")
        self.assertTrue(all(row["status"] == "not_run" for row in report["attempts"]))

    def test_interrupted_application_can_be_recovered(self):
        self.ready()
        destination = self.root / "target"
        actual_replace = Path.replace
        count = 0
        def interrupt(path, target):
            nonlocal count
            if path.name.endswith(".skill-builder-write"):
                count += 1
                if count == 2:
                    raise OSError("Simulated interruption")
            return actual_replace(path, target)
        with patch.object(Path, "replace", interrupt):
            with self.assertRaises(OSError):
                workflow.apply(self.run, destination)
        result = workflow.recover(self.run)
        self.assertEqual(result["status"], "recovered")
        self.assertEqual(inventory(destination), {})

    def test_host_native_route_works_without_provider_cli(self):
        from runtime.hosts import route
        for platform in ["chatgpt", "claude", "codex", "claude-code"]:
            with self.subTest(platform=platform):
                context = {"platform": platform, "model": None, "external_cli": False}
                result = route(context)
                self.assertEqual(result["route"], "host_agent")
                self.assertEqual(result["model"], "current_host_model")
                self.assertFalse(result["requires_external_cli"])
                with self.assertRaises(Invalid):
                    route(context, "codex", "some-model")

    def test_cross_provider_route_requires_explicit_configuration(self):
        from runtime.hosts import route
        context = {"platform": "claude", "model": "host-model", "external_cli": True}
        with self.assertRaises(Invalid):
            route(context, "codex", "gpt-6.1-sol")
        self.assertEqual(route({**context, "allow_cross_provider": True}, "codex", "gpt-6.1-sol")["route"], "codex")

    def test_default_model_command_is_host_handoff(self):
        self.start()
        with patch("runtime.adapters.run_process", side_effect=AssertionError("No CLI call")), contextlib.redirect_stdout(io.StringIO()) as stream:
            code = main(["model", "--run", str(self.run)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stream.getvalue())["status"], "host_handoff")
        self.assertEqual(workflow.read_state(self.run)["model_invocations"], 0)

    def test_exhausted_budget_allows_bounded_routine_extension_without_new_approval(self):
        bad = deepcopy(PRODUCE)
        bad["files"]["scripts/normalize.py"] = "print('{}')"
        self.produced(request={"limits": {"max_experiments": 1}}, produce=bad)
        self.assertFalse(workflow.budget(self.run)["ask_user_for_extension"])
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit("review", self.review())
        advice = workflow.budget(self.run)
        self.assertFalse(advice["ask_user_for_extension"])
        self.assertTrue(advice["automatic_extension"])
        with self.assertRaises(Invalid):
            workflow.extend_budget(self.run, 2, 60, 0, "")
        old = workflow.read_state(self.run)["objective_sha256"]
        state = workflow.extend_budget(self.run, 2, 60, 0, "Retest the corrected transformation under the same task and criteria.")
        self.assertEqual(state["objective_sha256"], old)
        self.assertEqual(state["request"]["limits"]["max_experiments"], 3)
        state = workflow.extend_budget(self.run, 2, 60, 0, "Retest the corrected transformation under the same task and criteria.")
        self.assertEqual(state["request"]["limits"]["max_experiments"], 3)

    def test_generated_skill_declares_host_native_policy(self):
        self.produced()
        policy = load(self.run / "candidate/config/host_policy.json")
        self.assertEqual(policy["designed_hosts"], ["chatgpt", "claude", "codex", "claude-code"])
        self.assertFalse(policy["external_cli_required"])
        self.assertIn("without asking for each extra test", (self.run / "candidate/SKILL.md").read_text())
        self.assertTrue((self.run / "candidate/scripts/continuation.py").is_file())

    def test_routine_budget_extension_preserves_explicit_hard_limits(self):
        bad = deepcopy(PRODUCE)
        bad['files']['scripts/normalize.py'] = "print('{}')"
        self.produced(request={'limits': {'max_experiments': 1}, 'hard_limits': {'attempts': 1}}, produce=bad)
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit('review', self.review())
        original = workflow.read_state(self.run)
        self.assertFalse(workflow.budget(self.run)['automatic_extension'])
        with self.assertRaisesRegex(Invalid, 'hard limit'):
            workflow.extend_budget(self.run, 1, 0, 0, 'Retest the scoped repair.')
        self.assertEqual(workflow.read_state(self.run), original)

    def test_routine_budget_extensions_stop_without_resetting_stagnation(self):
        self.produced()
        original = workflow.read_state(self.run)
        for index in range(MAX_EXTENSIONS):
            workflow.extend_budget(self.run, 1, 60, 1, f'Validate scoped repair {index + 1}.')
        state = workflow.read_state(self.run)
        self.assertEqual(state['request']['limits'].get('max_stagnant_experiments'), original['request'].get('limits', {}).get('max_stagnant_experiments'))
        with self.assertRaisesRegex(Invalid, 'ceiling'):
            workflow.extend_budget(self.run, 1, 60, 1, 'Try another routine repair.')
        self.assertEqual(workflow.read_state(self.run), state)

    def test_declared_target_cannot_be_lowered_by_plan(self):
        self.start(target_success_percent=100)
        self.submit("research")
        self.submit("specify")
        plan = deepcopy(PLAN)
        plan["target_success_percent"] = 10
        with self.assertRaises(Invalid):
            self.submit("plan", plan)

    def test_user_can_repeat_application_without_duplicate_writes(self):
        self.ready()
        workflow.apply(self.run, self.root / "target")
        with patch.object(Path, "replace", side_effect=AssertionError("No duplicate writes")):
            self.assertEqual(workflow.apply(self.run)["status"], "applied")

    def test_child_skill_maintenance_is_executable_without_builder(self):
        self.produced()
        package = self.run / "candidate"
        (package / "scripts/normalize.py").write_text("print('{}')")
        records = self.root / "maintenance"
        first = maintenance(package, records, PLAN["cases"], True)
        self.assertEqual(first["status"], "active")
        (package / "scripts/normalize.py").write_text(PROGRAM)
        result = maintenance(package, records, PLAN["cases"], True)
        self.assertEqual(result["status"], "target_met")
        exported = maintenance(package, records, PLAN["cases"], export=self.root / "repaired")
        self.assertEqual(exported["status"], "exported")
        self.assertEqual(inventory(self.root / "repaired"), inventory(package))

    def test_child_skill_budget_allows_routine_extension_without_builder_or_approval(self):
        self.produced(request={"limits": {"max_experiments": 1}})
        package = self.run / "candidate"
        (package / "scripts/normalize.py").write_text("print('{}')")
        records = self.root / "maintenance"
        maintenance(package, records, PLAN["cases"], True)
        paused = maintenance(package, records, PLAN["cases"], True)
        self.assertEqual(paused["status"], "needs_continuation")
        self.assertTrue(paused["proposal"]["automatic_extension"])
        self.assertFalse(paused["proposal"]["ask_user"])
        extension = {"iterations": 1, "seconds": 60, "authorization_note": "Recheck the repaired normalization under frozen criteria."}
        maintenance(package, records, PLAN["cases"], extension=extension)
        (package / "scripts/normalize.py").write_text(PROGRAM)
        self.assertEqual(maintenance(package, records, PLAN["cases"], True)["status"], "target_met")

    def test_child_skill_rejects_objective_or_unrelated_edits(self):
        self.produced()
        package = self.run / "candidate"
        (package / "scripts/normalize.py").write_text("print('{}')")
        records = self.root / "maintenance"
        maintenance(package, records, PLAN["cases"], True)
        state = load(records / "state.json")
        state["policy"]["target_success_percent"] = 0
        save(records / "state.json", state)
        with self.assertRaisesRegex(ValueError, "objective"):
            maintenance(package, records, PLAN["cases"], True)

    def test_repository_install_keeps_tests_and_excludes_local_records(self):
        from evaluate import copy_package
        self.produced()
        source = self.run / "candidate"
        (source / "tests").mkdir()
        (source / "tests/test_extra.py").write_text("# Public regression control\n")
        (source / "docs/internal").mkdir(parents=True)
        (source / "docs/internal/private.txt").write_text("PRIVATE_SENTINEL")
        (source / ".venv").mkdir()
        (source / ".venv/private.txt").write_text("not public")
        target = self.root / "copy"
        copy_package(source, target)
        self.assertTrue((target / "tests/test_extra.py").is_file())
        self.assertTrue((target / "LICENSE").is_file())
        self.assertFalse((target / "docs/internal").exists())
        self.assertFalse((target / ".venv").exists())
        self.assertFalse((target / "distribution.json").exists())
        self.assertTrue(check_package(target)["passed"])
        with self.assertRaises(ValueError):
            copy_package(source, target)

    def test_artifact_literals_are_checked_in_the_file(self):
        self.produced()
        case = {
            "id": "readme-content", "requirements": ["R-1"], "critical": True,
            "kind": "artifact", "expect": {"exit_code": 0, "file": "README.md", "contains": ["## Verification"]},
            "semantic": False,
        }
        result = evaluate(self.run / "candidate", [case])
        self.assertEqual(result["attempts"][0]["status"], "passed")
        case["expect"]["contains"] = ["ABSENT TEXT"]
        self.assertEqual(evaluate(self.run / "candidate", [case])["attempts"][0]["status"], "failed")

    def test_failed_first_candidate_still_has_frozen_edit_surface(self):
        bad = deepcopy(PRODUCE)
        bad["files"]["scripts/normalize.py"] = "print('{}')"
        self.produced(produce=bad)
        workflow.run_evaluation(self.run, allow_exec=True)
        self.submit("review", self.review())
        workflow.revise(self.run, "Repair only the permitted executable.")
        changed = deepcopy(PRODUCE)
        changed["instructions"] += " Rewrite unrelated instructions."
        with self.assertRaisesRegex(Invalid, "outside frozen"):
            self.submit("produce", changed)

    def test_phase_packet_passes_the_actual_writing_guide(self):
        self.start()
        packet = workflow.packet(self.run)
        guide = (SCRIPTS.parent / "references/writing_style.md").read_text()
        self.assertEqual(packet["guidance"]["writing_style.md"], guide)
        self.assertEqual(load(self.run / "packets" / f"{packet['packet_sha256']}.json"), packet)

    def test_pending_review_is_not_an_established_critical_failure(self):
        score = metrics([{"status": "pending_review", "critical": True}], 1)
        self.assertEqual(score["critical_failures"], 0)
        self.assertEqual(score["unresolved_critical"], 1)

    def test_uri_is_validated_independently_of_date(self):
        source = {"url": "not a uri", "checked": "2026-10-31", "decision": "test", "provenance": "user_supplied"}
        with self.assertRaises(Invalid):
            validate(source, contracts.SOURCE)
        source["url"] = "https://example.com/guide"
        validate(source, contracts.SOURCE)

    def test_missing_format_dependency_cannot_silently_pass(self):
        from jsonschema import FormatChecker
        with patch("runtime.common.FormatChecker", return_value=FormatChecker(formats=["date"])):
            with self.assertRaisesRegex(Invalid, "format checks unavailable"):
                validate({"url": "https://example.com", "checked": "2026-10-31", "decision": "test", "provenance": "user_supplied"}, contracts.SOURCE)

    def test_rebuild_preserves_existing_frontmatter_and_valid_policy(self):
        import yaml
        source = self.legacy()
        (source / "SKILL.md").write_text(
            "---\nname: normalize-customers\ndescription: Old description.\nlicense: MIT\nmetadata:\n  owner: example-team\n  version: '2'\n---\n\nKeep policy EXACT.\n"
        )
        produced = deepcopy(PRODUCE)
        produced["instructions"] += " Keep policy EXACT."
        produced["files"]["assets/keep.txt"] = "original"
        produced["remove"] = ["keep.txt"]
        plan = deepcopy(PLAN)
        plan["domains"][0]["owned_paths"].append("assets/keep.txt")
        self.produced(request={"operation": "rebuild", "source": str(source), "preserve_literals": ["Keep policy EXACT."]}, plan=plan, produce=produced)
        metadata = yaml.safe_load((self.run / "candidate/SKILL.md").read_text().split("---\n", 2)[1])
        self.assertEqual(metadata["license"], "MIT")
        self.assertEqual(metadata["metadata"], {"owner": "example-team", "version": "2"})
        workflow.run_evaluation(self.run, allow_exec=True)
        self.assertEqual(self.submit("review", self.review())["status"], "ready")

    def test_generated_readme_has_clone_explicit_invocation_and_eval_guidance(self):
        produced = deepcopy(PRODUCE)
        produced["documentation"]["repository_url"] = "https://github.com/example/normalize-customers"
        self.produced(produce=produced)
        text = (self.run / "candidate/README.md").read_text()
        self.assertIn("git clone https://github.com/example/normalize-customers normalize-customers", text)
        self.assertEqual(text.count("> /normalize-customers "), 3)
        self.assertIn("task_success_percent", text)
        self.assertIn("coverage_percent", text)
        self.assertIn("80%", text)
        self.assertIn("Evaluate and improve results", text)
        self.assertTrue(check_package(self.run / "candidate")["passed"])

    def test_readme_contract_rejects_missing_testing_and_wrong_invocation(self):
        bad = deepcopy(PRODUCE)
        del bad["documentation"]["testing"]
        with self.assertRaises(Invalid):
            self.produced(produce=bad)
        from runtime.readme import render
        documentation = deepcopy(PRODUCE["documentation"])
        documentation["quick_start"]["prompt"] = "/wrong-skill Normalize this record."
        with self.assertRaises(Invalid):
            render("normalize-customers", documentation)

    def test_broken_documented_command_blocks_candidate_acceptance(self):
        produced = deepcopy(PRODUCE)
        produced["documentation"]["verification"]["command"]["argv"] = ["python3", "scripts/missing.py"]
        self.produced(produce=produced)
        workflow.run_evaluation(self.run, allow_exec=True)
        result = self.submit("review", self.review())
        self.assertNotEqual(result["status"], "ready")
        self.assertTrue(any("missing.py" in item for item in result["package_check"]["findings"]))

    def test_actual_repository_install_is_complete_and_usable(self):
        from install_skill import install
        root = SCRIPTS.parent
        installed = self.root / "installed-skill"
        result = install(root, "codex", installed)
        self.assertEqual(result["status"], "installed")
        for name in ["tests", "tools", "config"]:
            self.assertTrue((installed / name).exists(), name)
        self.assertFalse((installed / "docs/internal").exists())
        self.assertIn("skill-readme:source", (installed / "README.md").read_text())
        self.assertIn("## Development", (installed / "README.md").read_text())
        self.assertTrue(check_package(installed)["passed"])
        process = subprocess.run([sys.executable, str(installed / "scripts/smoke_check.py")], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)
        self.assertTrue(json.loads(process.stdout)["passed"])
        with self.assertRaises(ValueError):
            install(root, "codex", installed)

    def test_installed_readme_regeneration_retains_repository_guide(self):
        from install_skill import install
        from runtime.readme import write, check
        installed = self.root / "installed-skill"
        install(SCRIPTS.parent, "claude-code", installed)
        write(installed)
        self.assertTrue(check(installed)["passed"])
        self.assertIn("## Development", (installed / "README.md").read_text())

    def test_optional_upload_zip_contains_the_same_public_repository(self):
        from install_skill import make_archive
        from evaluate import hash_tree
        root = SCRIPTS.parent
        before = hash_tree(root)
        output = self.root / "skill-builder.zip"
        result = make_archive(root, output)
        self.assertEqual(result["status"], "packaged")
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            self.assertIn("skill-builder/SKILL.md", names)
            self.assertIn("skill-builder/scripts/install_skill.py", names)
            self.assertTrue(any("/tests/" in name for name in names))
            self.assertFalse(any("/docs/internal/" in name or "/.git/" in name or "/.venv/" in name for name in names))
            self.assertIn("## Development", archive.read("skill-builder/README.md").decode())
        self.assertEqual(hash_tree(root), before)
        with self.assertRaises(FileExistsError):
            make_archive(root, output)

    def test_readme_cannot_advertise_a_different_skill_name(self):
        from runtime.readme import check, write
        self.produced()
        root = self.run / "candidate"
        data = json.loads((root / "config/documentation.json").read_text())
        data["name"] = "wrong-skill"
        save(root / "config/documentation.json", data)
        write(root)
        result = check(root)
        self.assertFalse(result["passed"])
        self.assertTrue(any("does not match" in finding for finding in result["findings"]))

    def test_readme_walkthrough_imports_the_documented_input_output_pair(self):
        from install_skill import install
        from runtime.readme import render
        installed = self.root / "skill"
        install(SCRIPTS.parent, "codex", installed)
        data = json.loads((installed / "config/documentation.json").read_text())
        doc = data["documentation"]
        scenario = next(row for row in doc["scenarios"] if row["title"] == "Build from input/output examples")
        for step in scenario["steps"]:
            for file in step.get("files", []):
                path = (installed / file["path"]).resolve()
                self.assertTrue(path.is_relative_to(self.root.resolve()))
                path.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(file["content"], str):
                    path.write_text(file["content"])
                else:
                    save(path, file["content"])
            if "command" in step:
                argv = list(step["command"]["argv"])
                if argv[0] == ".venv/bin/python":
                    argv[0] = sys.executable
                process = subprocess.run(argv, cwd=installed, capture_output=True, text=True)
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        bundle = json.loads((self.root / "skill-data/paired-data/examples.json").read_text())
        self.assertEqual(len(bundle["pairs"]), 1)
        pair = bundle["pairs"][0]
        self.assertEqual(pair["input"]["extracted"]["value"]["expected"], "The new category is saved.")
        self.assertIn("## Expected result\n\nThe new category is saved.", pair["output"]["extracted"]["value"])
        text = render(data["name"], doc)
        walkthrough = text.split("### Build from input/output examples", 1)[1].split("### Audit an existing skill", 1)[0]
        evaluation = text.split("## Evaluate and improve results", 1)[1]
        self.assertIn("pairs.json", walkthrough)
        self.assertNotIn("pairs.json", evaluation)
        self.assertNotIn("input.json", evaluation)


if __name__ == "__main__":
    unittest.main()
