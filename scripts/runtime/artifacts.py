"""Package rendering and checks; supplied documents never execute themselves."""
import json
from pathlib import Path
import re
import shutil
from datetime import datetime, timezone
from repository_layout import check as check_layout
from run_tests import broad_command
from evaluate import grade_process
from urllib.parse import unquote, urlsplit

import yaml

from .common import Invalid, digest, inside, inventory, relative, save, copy_package
from .hosts import POLICY
from .readme import render as render_readme, check as check_readme

MANAGED = {"scripts/case_inputs.py", "scripts/provider_results.py", "scripts/host_coverage.py", "config/host_validation.json", "scripts/continuation.py", "scripts/run_tests.py", "config/test_impact.json", "AGENTS.md", "CLAUDE.md", "LICENSE", "config/repository_layout.json", "config/domains.json", "scripts/repository_files.py", "scripts/repository_layout.py", "SKILL.md", "README.md", "config/documentation.json", "evals/cases.json", "scripts/evaluate.py", "scripts/install_skill.py", "config/build_record.json", "config/host_policy.json"}
EVALUATOR = Path(__file__).resolve().parents[1] / "evaluate.py"



def workflow_requirements(spec):
    """Required test scenarios derived from the declared process, before tuning."""
    result = {}
    workflows = spec.get("workflows", [])
    if not workflows:
        raise Invalid("Inventory every workflow/process before planning its tests.")
    for flow in workflows:
        identifier, steps = flow["id"], flow["steps"]
        if identifier in result or not steps or len(steps) != len(set(steps)):
            raise Invalid("Workflow IDs and step IDs must be unique and nonempty.")
        checks = {"success", "behavior"}
        if len(steps) == 1:
            checks.add("invalid_input")
        else:
            checks.update("omission:" + step for step in steps)
            checks.update("order:" + a + "->" + b for a, b in zip(steps, steps[1:]))
        for scenario, field in (("boundary", "boundaries"), ("branch", "branches"), ("recovery", "recovery")):
            names = [item["id"] for item in flow[field]]
            if len(names) != len(set(names)):
                raise Invalid("Workflow condition IDs must be unique within their kind.")
            checks.update(scenario + ":" + name for name in names)
        result[identifier] = sorted(checks)
    return result


def check_workflow_coverage(spec, plan):
    required = workflow_requirements(spec)
    flows = {item["id"]: item for item in spec["workflows"]}
    covered = {identifier: set() for identifier in required}
    for case in plan["cases"]:
        flow_case = case.get("workflow")
        if not flow_case:
            continue
        identifier = flow_case["id"]
        if identifier not in flows:
            raise Invalid("A case names an unknown workflow: " + identifier)
        if case["critical"] is not True:
            raise Invalid("Workflow checks are mandatory; mark their cases critical.")
        scenario = flow_case["scenario"]
        labels = {scenario} if scenario in {"success", "invalid_input", "behavior"} else {scenario + ":" + value for value in flow_case["covers"]}
        if not labels or labels - set(required[identifier]):
            raise Invalid("Workflow case covers an undeclared or empty check: " + case["id"])
        flow = flows[identifier]
        if scenario == "behavior":
            if case["kind"] != "behavior" or not case["semantic"] or "request" not in case or not case.get("resources"):
                raise Invalid("Every workflow needs a real AI behavioral case, its task/resources, and semantic review.")
        elif case["kind"] == "behavior":
            raise Invalid("Classify model observations as behavioral coverage, not mechanical workflow proof.")
        process = case["expect"].get("process")
        if process:
            if set(process["order"]) - set(flow["steps"]) or (set(process["visible"]) | set(process["evidence"])) - set(process["order"]):
                raise Invalid("Trace assertions name unknown or absent workflow steps.")
        if scenario == "success" and len(flow["steps"]) > 1:
            if not process or process["order"] != flow["steps"] or not case["semantic"]:
                raise Invalid("A multi-step success case needs its full ordered trace and semantic evidence review.")
        covered[identifier].update(labels)
    missing = {name: sorted(set(checks) - covered[name]) for name, checks in required.items() if set(checks) - covered[name]}
    if missing:
        raise Invalid("Missing workflow/process tests: " + json.dumps(missing, sort_keys=True))
    return {name: {"required": checks, "covered": sorted(covered[name])} for name, checks in required.items()}


def check_plan(spec, plan, require_workflows=False):
    if require_workflows:
        check_workflow_coverage(spec, plan)
    requirements = [item["id"] for item in spec["requirements"]]
    if len(set(requirements)) != len(requirements):
        raise Invalid("Requirement IDs must be unique.")
    cases = plan["cases"]
    if len({case["id"] for case in cases}) != len(cases):
        raise Invalid("Case IDs must be unique.")
    mapped = {value for case in cases for value in case["requirements"]}
    if mapped != set(requirements):
        raise Invalid("Every requirement needs a case; cases may not refer to unknown requirements.")
    semantic = {item["id"] for item in spec["requirements"] if item["kind"] == "semantic"}
    covered_semantic = {
        item for case in cases if case["semantic"] for item in case["requirements"]
    }
    if not semantic.issubset(covered_semantic):
        raise Invalid("Every semantic requirement needs at least one semantic case.")
    for case in cases:
        expected = case['expect']
        process = expected.get('process')
        if case['kind'] == 'command' and process and 'trace_file' not in process and ('stdout_json' in expected or 'stdout_text' in expected):
            try:
                trace = expected['stdout_json'] if 'stdout_json' in expected else json.loads(expected['stdout_text'])
                compatible = grade_process(trace, process)['passed']
            except (ValueError, TypeError):
                compatible = False
            if not compatible:
                raise Invalid(f"Case {case['id']} has contradictory exact stdout and process-trace expectations. Use trace_file for a separate captured trace, or make the exact stdout contain the required trace.")
        if case["kind"] == "command" and not case.get("command"):
            raise Invalid(f"Case {case['id']} needs a command.")
        if case["kind"] == "command" and broad_command(case.get("command", [])):
            raise Invalid("Unrestricted test discovery is not an iterative check; use the scoped test runner.")
        if case["kind"] == "artifact" and "file" not in case["expect"]:
            raise Invalid(f"Artifact case {case['id']} needs an expected file.")
    domains = plan.get("domains", [])
    if not domains or len({row["name"] for row in domains}) != len(domains):
        raise Invalid("Declare unique domains with purposes, owned paths and dependencies.")
    owners = {}
    names = {row["name"] for row in domains}
    for row in domains:
        if set(row["depends_on"]) - names:
            raise Invalid("A domain refers to an unknown dependency.")
        for path in row["owned_paths"]:
            relative(path.rstrip("/"))
            if any(path == old or path.endswith("/") and old.startswith(path) or old.endswith("/") and path.startswith(old) for old in owners):
                raise Invalid("Overlapping domain ownership: " + path)
            owners[path] = row["name"]
    for resource in plan["resources"]:
        if not any(resource["path"] == path or path.endswith("/") and resource["path"].startswith(path) for path in owners):
            raise Invalid("No domain owns resource: " + resource["path"])
    def visit(name, trail):
        if name in trail:
            raise Invalid("Cyclic domain dependencies.")
        row = next(row for row in domains if row["name"] == name)
        for dependency in row["depends_on"]:
            visit(dependency, [*trail, name])
    for name in names:
        visit(name, [])
    paths = [item["path"] for item in plan["resources"]]
    if len(paths) != len(set(paths)):
        raise Invalid("Resource paths must be unique.")
    if set(paths).intersection(MANAGED):
        raise Invalid("Managed artifacts are already routed/reviewed; declare task-specific resources only.")
    if set(plan["allowed_candidate_paths"]).intersection({"evals/cases.json", "scripts/evaluate.py", "config/host_policy.json", "config/build_record.json"}):
        raise Invalid("Frozen checks and generated policy are not candidate-edit surfaces.")
    for path in [*paths, *plan["allowed_candidate_paths"]]:
        relative(path)


def render(root, request, spec, plan, response, source=None):
    root = Path(root)
    if root.exists():
        raise Invalid("Candidate directory already exists.")
    if source:
        copy_package(source, root)
    else:
        root.mkdir(parents=True)
    creating = request["operation"] in {"create", "rebuild"}
    for name in response.get("remove", []):
        path = inside(root, name)
        if creating and name in MANAGED:
            raise Invalid(f"Cannot remove managed artifact: {name}")
        if not path.is_file():
            raise Invalid(f"Removal does not identify an existing file: {name}")
        path.unlink()
        parent = path.parent
        while parent != root:
            try:
                parent.rmdir()
            except OSError:
                break
            parent = parent.parent
    for name, content in response["files"].items():
        path = inside(root, name)
        if creating and name in MANAGED:
            raise Invalid(f"Use structured fields rather than overriding managed file {name}.")
        if creating and not any(name == owned or owned.endswith("/") and name.startswith(owned) for domain in plan["domains"] for owned in domain["owned_paths"]):
            raise Invalid("No domain owns produced resource: " + name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    if creating:
        holder = request.get("copyright_holder")
        existing_license = (root / "LICENSE").read_text() if (root / "LICENSE").is_file() else None
        if not existing_license and (not isinstance(holder, str) or not holder.strip()):
            raise Invalid("Supply copyright_holder before creating a new MIT-licensed skill.")
        if not existing_license:
            template = EVALUATOR.parent.parent / "assets/MIT-LICENSE.txt"
            (root / "LICENSE").write_text(template.read_text().format(year=datetime.now(timezone.utc).year, copyright_holder=holder))
        shared = (EVALUATOR.parent.parent / "assets/AGENTS.md").read_text()
        project_notes = response.get("repository_instructions")
        if project_notes is None and (root / "AGENTS.md").is_file():
            project_notes = (root / "AGENTS.md").read_text()
        instructions = shared
        if project_notes and project_notes.strip() != shared.strip():
            instructions += "\n## Project guidance\n\nThe shared testing and approval rules above take precedence over conflicting project notes.\n\n" + project_notes.strip() + "\n"
        (root / "AGENTS.md").write_text(instructions)
        (root / "CLAUDE.md").write_text("@AGENTS.md\n")
        for name in ("case_inputs.py", "continuation.py", "repository_files.py", "repository_layout.py", "run_tests.py", "host_coverage.py", "provider_results.py"):
            (root / "scripts").mkdir(exist_ok=True)
            shutil.copyfile(EVALUATOR.parent / name, root / "scripts" / name)
        save(root / "config/host_validation.json", {"schema_version": 1, "required_hosts": ["codex", "claude-code"], "case_files": [{"path": "evals/cases.json"}]})
        save(root / "config/repository_layout.json", json.loads((EVALUATOR.parent.parent / "config/repository_layout.json").read_text()))
        save(root / "config/domains.json", {"schema_version": 1, "domains": plan["domains"]})
        test_groups = {case["id"]: {"argv": ["{python}", "scripts/evaluate.py", "--package", ".", "--allow-exec", "--case", case["id"]]} for case in plan["cases"]}
        impact_rules = []
        for case in plan["cases"]:
            paths = [value for value in case.get("command", [])[1:] if not value.startswith("-") and (root / value).is_file()]
            if case["expect"].get("file"):
                paths.append(case["expect"]["file"])
            if paths:
                impact_rules.append({"paths": sorted(set(paths)), "tests": [case["id"]]})
        impact_rules.append({"paths": ["evals/cases.json", "scripts/evaluate.py"], "tests": list(test_groups)})
        impact_rules.append({"paths": ["AGENTS.md", "CLAUDE.md", "README.md", "SKILL.md", "LICENSE"], "tests": [], "reason": "Review changed instructions; unrelated executable cases are not selected."})
        save(root / "config/test_impact.json", {"schema_version": 1, "tests": test_groups, "rules": impact_rules, "final_checks": test_groups})
        data = {
            "name": request["skill_name"], "description": response["description"],
            "instructions": response["instructions"], "resources": plan["resources"],
            "documentation": response["documentation"],
        }
        inherited = {}
        if source and (Path(source) / "SKILL.md").is_file():
            parts = (Path(source) / "SKILL.md").read_text().split("---\n", 2)
            if len(parts) != 3:
                raise Invalid("Reconcile malformed source frontmatter before rebuilding.")
            inherited = yaml.safe_load(parts[1])
            if not isinstance(inherited, dict):
                raise Invalid("Source frontmatter must be a mapping.")
        metadata = yaml.safe_dump(
            {**inherited, "name": data["name"], "description": data["description"], "license": inherited.get("license", "See LICENSE") if existing_license else "MIT"}, sort_keys=False
        ).strip()
        routing = "\n".join(
            f"- [{item['path']}]({item['path']}): {item['purpose']} Read when {re.sub(r'(?i)^when +', '', item['when'])}."
            for item in data["resources"]
        )
        (root / "SKILL.md").write_text(
            f"---\n{metadata}\n---\n\n# {data['name']}\n\n{data['instructions'].strip()}\n"
            + (f"\n## Resources\n\n{routing}\n" if routing else "")
            + "\n## Host and improvement behavior\n\n"
            "Use the current host's model when AI judgment is needed. Keep shared mechanics portable across ChatGPT, Claude, Codex, and Claude Code; check the task's required execution and file tools. Do not require another provider's CLI for normal use.\n\n"
            "Before claiming multi-host validation, freeze config/host_validation.json with scripts/host_coverage.py, collect actual tasks and public traces on each required host, and assess their bound reviews. A missing host or unreviewed result prevents acceptance of that claim; installation or a mechanical pass is not behavioral evidence. Native use still requires only the current host.\n\n"
            "An observed task timeout is failed even with an incomplete trace; missing observations are not run. Preserve both the failed attempt and uncertainty about its cause. Do not relabel a timeout as unrun or require a code change merely to retry an unchanged task.\n\n"
            "Routine testing and necessary retries are part of the authorized task. Choose bounded batches from task complexity and observed runtime, and continue without asking for each extra test. Use scripts/continuation.py to enforce retry ceilings, record each reason and preserve failed attempts and frozen criteria. Stop and report stalled progress or exhausted retry ceilings. Respect explicit user hard limits, host permissions and paid-service restrictions; ask only when a material change requires a new decision.\n"
        )
        readme = render_readme(data["name"], data["documentation"])
        save(root / "config/documentation.json", {"schema_version": 1, "name": data["name"], "documentation": data["documentation"]})
        (root / "README.md").write_text(readme)
        (root / "evals").mkdir(exist_ok=True)
        (root / "scripts").mkdir(exist_ok=True)
        save(root / "evals/cases.json", plan["cases"])
        shutil.copyfile(EVALUATOR, root / "scripts/evaluate.py")
        shutil.copyfile(EVALUATOR.parent / "install_skill.py", root / "scripts/install_skill.py")
        save(root / "config/host_policy.json", {
            **POLICY,
            "maintenance": {
                "max_experiments": request.get("limits", {}).get("max_experiments", 5),
                "max_stagnant_experiments": request.get("limits", {}).get("max_stagnant_experiments", 3),
                "max_seconds": request.get("limits", {}).get("max_seconds", 600),
                "target_success_percent": plan["target_success_percent"],
                "allowed_candidate_paths": plan["allowed_candidate_paths"],
                "hard_limits": request.get("hard_limits", {}),
            },
        })
        managed = {name: digest((root / name).read_bytes()) for name in sorted(MANAGED) if name != "config/build_record.json"}
        save(root / "config/build_record.json", {"schema_version": 1, "source": data, "managed_hashes": managed})
    return inventory(root)


def check_package(root, full=True, literals=(), structure=False):
    root = Path(root)
    findings = []
    files = inventory(root)
    required = ["SKILL.md"] + (["LICENSE", "README.md", "AGENTS.md", "CLAUDE.md", "evals/cases.json", "scripts/evaluate.py", "config/host_policy.json"] if full else [])
    for name in required:
        if name not in files:
            findings.append(f"Missing required file: {name}")
    if full or structure:
        findings.extend(item["path"] + ": " + item["problem"] for item in check_layout(root)["findings"])
        if not (root / "config/domains.json").is_file():
            findings.append("Missing domain ownership contract: config/domains.json")
    name = None
    if "SKILL.md" in files:
        text = (root / "SKILL.md").read_text()
        try:
            if not text.startswith("---\n"):
                raise Invalid("SKILL.md needs YAML frontmatter.")
            pieces = text.split("---\n", 2)
            if len(pieces) != 3 or not pieces[2].strip():
                raise Invalid("Missing closing frontmatter delimiter or instructions.")
            metadata = yaml.safe_load(pieces[1])
            name = metadata["name"]
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
                raise Invalid("Invalid skill name.")
            if not isinstance(metadata["description"], str) or not metadata["description"].strip():
                raise Invalid("Missing skill description.")
        except (IndexError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
            findings.append(f"Invalid metadata: {error}")
    texts = {}
    for filename in files:
        path = root / filename
        if path.suffix == ".py":
            try:
                compile(path.read_text(), filename, "exec")
            except (SyntaxError, UnicodeError) as error:
                findings.append(f"Invalid Python in {filename}: {error}")
        if path.suffix == ".md":
            content = path.read_text()
            texts[filename] = content
            for match in re.finditer(r"\]\((<[^>]+>|[^)\s]+)\)", content):
                link = match[1].strip("<>")
                parsed = urlsplit(link)
                if parsed.scheme or not parsed.path:
                    continue
                target = (path.parent / unquote(parsed.path)).resolve()
                if not target.is_relative_to(root.resolve()) or not target.is_file() or target.relative_to(root.resolve()).as_posix() not in files:
                    findings.append(f"Broken or external local link in {filename}: {link}")
    combined = "\n".join(texts.values())
    for literal in literals:
        if literal not in combined:
            findings.append(f"Missing preserved literal: {literal!r}")
    contract_path = root / "config/build_record.json"
    if full and (root / "config/host_policy.json").is_file():
        try:
            policy = json.loads((root / "config/host_policy.json").read_text())
            if set(policy["designed_hosts"]) != set(POLICY["designed_hosts"]) or policy["default_ai_route"] != "current_host_model" or policy["external_cli_required"] is not False:
                findings.append("Host policy must preserve the required hosts and native-model default.")
        except (KeyError, TypeError, ValueError) as error:
            findings.append(f"Invalid host policy: {error}")
    if contract_path.exists():
        try:
            contract = json.loads(contract_path.read_text())
            for filename, expected in contract["managed_hashes"].items():
                if files.get(filename) != expected:
                    findings.append(f"Managed-file drift: {filename}")
            for resource in contract["source"]["resources"]:
                if resource["path"] not in files:
                    findings.append(f"Missing declared resource: {resource['path']}")
        except (KeyError, TypeError, ValueError) as error:
            findings.append(f"Invalid managed-artifact record: {error}")
    if (root / "config/documentation.json").is_file():
        try:
            findings.extend(check_readme(root)["findings"])
        except (Invalid, OSError, ValueError, KeyError) as error:
            findings.append(f"Invalid public README: {error}")
    return {"passed": not findings, "findings": findings, "name": name, "files": files}
