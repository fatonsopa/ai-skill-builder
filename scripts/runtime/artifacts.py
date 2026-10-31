"""Package rendering and checks; supplied documents never execute themselves."""
import json
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit

import yaml

from .common import Invalid, digest, inside, inventory, relative, save, copy_package
from .hosts import POLICY
from .readme import render as render_readme, check as check_readme

MANAGED = {"SKILL.md", "README.md", "documentation.json", "evals/cases.json", "scripts/evaluate.py", "scripts/install_skill.py", ".skill-builder.json", "host_policy.json"}
EVALUATOR = Path(__file__).resolve().parents[1] / "evaluate.py"


def check_plan(spec, plan):
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
        if case["kind"] == "command" and not case.get("command"):
            raise Invalid(f"Case {case['id']} needs a command.")
        if case["kind"] == "artifact" and "file" not in case["expect"]:
            raise Invalid(f"Artifact case {case['id']} needs an expected file.")
    paths = [item["path"] for item in plan["resources"]]
    if len(paths) != len(set(paths)):
        raise Invalid("Resource paths must be unique.")
    if set(paths).intersection(MANAGED):
        raise Invalid("Managed artifacts are already routed/reviewed; declare task-specific resources only.")
    if set(plan["allowed_candidate_paths"]).intersection({"evals/cases.json", "scripts/evaluate.py", "host_policy.json", ".skill-builder.json"}):
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
    for name, content in response["files"].items():
        path = inside(root, name)
        if creating and name in MANAGED:
            raise Invalid(f"Use structured fields rather than overriding managed file {name}.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    if creating:
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
            {**inherited, "name": data["name"], "description": data["description"]}, sort_keys=False
        ).strip()
        routing = "\n".join(
            f"- [{item['path']}]({item['path']}): {item['purpose']} Read when {item['when']}."
            for item in data["resources"]
        )
        (root / "SKILL.md").write_text(
            f"---\n{metadata}\n---\n\n# {data['name']}\n\n{data['instructions'].strip()}\n"
            + (f"\n## Resources\n\n{routing}\n" if routing else "")
            + "\n## Host and improvement behavior\n\n"
            "Use the current host's model when AI judgment is needed. Keep shared mechanics portable across ChatGPT, Claude, Codex, and Claude Code; check the task's required execution and file tools. Do not require another provider's CLI for normal use.\n\n"
            "If evaluation remains below target and the iteration or runtime allowance is exhausted, report the gap and ask the user whether to authorize another bounded batch. Recommend limits from observed progress and runtime. Preserve the target and scoring rules; never extend the budget silently.\n"
        )
        readme = render_readme(data["name"], data["documentation"])
        save(root / "documentation.json", {"schema_version": 1, "name": data["name"], "documentation": data["documentation"]})
        (root / "README.md").write_text(readme)
        (root / "evals").mkdir(exist_ok=True)
        (root / "scripts").mkdir(exist_ok=True)
        save(root / "evals/cases.json", plan["cases"])
        shutil.copyfile(EVALUATOR, root / "scripts/evaluate.py")
        shutil.copyfile(EVALUATOR.parent / "install_skill.py", root / "scripts/install_skill.py")
        save(root / "host_policy.json", {
            **POLICY,
            "maintenance": {
                "max_experiments": request.get("limits", {}).get("max_experiments", 5),
                "max_stagnant_experiments": request.get("limits", {}).get("max_stagnant_experiments", 3),
                "max_seconds": request.get("limits", {}).get("max_seconds", 600),
                "target_success_percent": plan["target_success_percent"],
                "allowed_candidate_paths": plan["allowed_candidate_paths"],
            },
        })
        managed = {name: digest((root / name).read_bytes()) for name in MANAGED if name != ".skill-builder.json"}
        save(root / ".skill-builder.json", {"schema_version": 1, "source": data, "managed_hashes": managed})
    return inventory(root)


def check_package(root, full=True, literals=()):
    root = Path(root)
    findings = []
    files = inventory(root)
    required = ["SKILL.md"] + (["README.md", "evals/cases.json", "scripts/evaluate.py", "host_policy.json"] if full else [])
    for name in required:
        if name not in files:
            findings.append(f"Missing required file: {name}")
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
    contract_path = root / ".skill-builder.json"
    if full and (root / "host_policy.json").is_file():
        try:
            policy = json.loads((root / "host_policy.json").read_text())
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
    if (root / "documentation.json").is_file():
        try:
            findings.extend(check_readme(root)["findings"])
        except (Invalid, OSError, ValueError, KeyError) as error:
            findings.append(f"Invalid public README: {error}")
    return {"passed": not findings, "findings": findings, "name": name, "files": files}
