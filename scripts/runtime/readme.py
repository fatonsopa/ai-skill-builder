"""Public, user-facing skill README contract shared by the builder and its outputs."""
import json
from pathlib import Path
import shlex
import re

from .common import Invalid, load, validate
from .contracts import DOCUMENTATION


def code_command(command):
    argv = shlex.join(command["argv"])
    if "stdin" not in command:
        return f"```sh\n{argv}\n```"
    value = command["stdin"]
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return f"```sh\n{argv} <<'SKILL_INPUT'\n{text}\nSKILL_INPUT\n```"


def invoked(name, prompt):
    prompt = prompt.strip()
    if re.match(rf"^[/@{chr(36)}]{re.escape(name)}(?:\s|$)", prompt):
        return prompt
    if re.match(r"^[/@\$][a-z0-9-]+(?:\s|$)", prompt):
        raise Invalid("Usage example invokes a different skill.")
    return f"/{name} {prompt}"


def render(name, documentation, profile="source"):
    validate(documentation, DOCUMENTATION)
    d = documentation
    rows = [
        f"# {d['title']}", "", d["summary"], "",
        "## Requirements", "",
        *[f"- {item}" for item in d["prerequisites"]], "",
        "## Installation", "",
        "### Get the skill", "",
    ]
    if d.get("repository_url"):
        rows += [
            "Clone the repository, then enter the skill folder:", "",
            code_command({"argv": ["git", "clone", d["repository_url"], name]}), "",
            code_command({"argv": ["cd", name]}), "",
            "You can also download the repository ZIP from GitHub's Code menu and extract it.", "",
        ]
    else:
        rows += ["Download and extract the skill ZIP. Open the folder containing `SKILL.md`.", ""]
    rows += [
        "### ChatGPT desktop and Codex", "",
        "For a filesystem-enabled ChatGPT desktop/Codex workspace, run:", "",
        "```sh\npython3 scripts/install_skill.py --host codex\n```", "",
        f"The installer copies the runtime files to `~/.agents/skills/{name}/`. "
        f"Start a new chat and select `@{name}` in ChatGPT desktop or invoke `{chr(36)}{name}` in Codex. "
        "In the desktop app, Skills is available from the sidebar. "
        "This installation uses local skill support; it does not install a browser or mobile add-on.", "",
        "### Claude Code", "",
        "```sh\npython3 scripts/install_skill.py --host claude-code\n```", "",
        f"The destination is `~/.claude/skills/{name}/`. Start a new Claude Code session and invoke `/{name}`.", "",
        "### Claude", "",
        "Create the upload ZIP from the extracted skill folder:", "",
        code_command({"argv": ["python3", "scripts/install_skill.py", "--archive", f"../{name}.zip"]}), "",
        f"Upload `../{name}.zip` through Claude's custom-skills settings: "
        "Customize → Skills → Create skill → Upload a skill. Newer layouts may show Skills under Plugins. "
        "Enable code execution and file creation, then enable the uploaded skill. "
        "[Claude's upload instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).", "",
    ]
    if d["setup"]:
        rows += ["### Set up runtime dependencies", "",
            "After a local installation, change to the destination printed by the installer. "
            "Run the following commands there, or ask the host to run them with its code tools:", ""]
        for command in d["setup"]:
            rows += [code_command(command), ""]
    rows += [
        "## Quick start", "",
        f"Explicitly invoke the skill before giving it a task. Examples below use `/{name}`. "
        f"Use `@{name}` in ChatGPT desktop and `{chr(36)}{name}` in Codex.", "",
        "> " + invoked(name, d["quick_start"]["prompt"]).replace("\n", "\n> "), "",
        d["quick_start"]["expected_result"], "",
        "## Usage scenarios", "",
    ]
    for scenario in d["scenarios"]:
        rows += ["### " + scenario["title"], ""]
        if scenario.get("introduction"):
            rows += [scenario["introduction"], ""]
        for index, step in enumerate(scenario.get("steps", []), 1):
            rows += [f"#### {index}. {step['title']}", "", step["text"], ""]
            if "command" in step:
                rows += [code_command(step["command"]), ""]
            for file in step.get("files", []):
                content = file["content"]
                text = content.rstrip("\n") if isinstance(content, str) else json.dumps(content, indent=2, ensure_ascii=False)
                rows += [f"Save as `{file['path']}`:", "", "```" + ("text" if isinstance(content, str) else "json"), text, "```", ""]
        if scenario.get("steps"):
            rows += ["Then invoke the skill:", ""]
        rows += [
            "> " + invoked(name, scenario["prompt"]).replace("\n", "\n> "), "",
            scenario["expected_result"], "",
        ]
        if "command" in scenario:
            rows += [code_command(scenario["command"]), ""]
        for key, label in [("input", "Example input"), ("output", "Expected output")]:
            if key in scenario:
                value = scenario[key]
                text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
                rows += [label + ":", "", "```" + ("text" if isinstance(value, str) else "json"), text, "```", ""]
    rows += [
        "## Verification", "", code_command(d["verification"]["command"]), "",
        d["verification"]["expected_result"], "",
        "## Evaluate and improve results", "", d["testing"]["prepare"], "",
    ]
    rows += ["### Acceptance criteria", ""]
    rows += [f"- {item}" for item in d["testing"]["acceptance_criteria"]]
    rows += ["", "### Run the evaluations", "",
        "Use the evaluation command below. Replace named placeholders with the paths returned by the skill.", "",
        code_command(d["testing"]["run_command"]), "",
        "### Read the results", "",
        "| Result field | Meaning |", "| --- | --- |",
        "| `task_success_percent` | Accepted task attempts ÷ evaluated attempts × 100 |",
        "| `coverage_percent` | Evaluated attempts ÷ planned attempts × 100 |",
        "| `critical_failures` | Failed non-negotiable requirements; these block acceptance |",
        "| `pending_review` | Outputs that still need a semantic judgment |",
        "",
        "For example, 8 accepted attempts out of 10 evaluated attempts gives 80% task success. "
        "If 12 attempts were planned, coverage is 83.3%. A missing denominator is reported as not measured. "
        "Wrong or malformed task outputs count as failed attempts. Infrastructure gaps reduce coverage. "
        "A quality rubric score is reported separately from truth-based accuracy.", "",
        "A candidate is accepted only when its declared target, coverage, critical checks, and required reviews pass. "
        "An installation self-check is not a complete quality assessment of a generated skill.", "",
        "### Improve and retest", "",
    ]
    rows += [f"{index}. {step}" for index, step in enumerate(d["testing"]["improvement_steps"], 1)]
    rows += ["",
        "## Models and run limits", "",
        "AI work uses the model already available in the current host. "
        "The skill records an unknown model identity rather than guessing one. "
        "Mechanical operations run through the packaged scripts.", "",
        "If evaluation remains below target when a run limit is reached, the skill reports the gap "
        "and recommends a bounded continuation. Additional iterations or runtime require your approval. "
        "Requirements and scoring stay fixed.", "",
        "## Troubleshooting", "",
    ]
    for item in d["troubleshooting"]:
        rows += ["### " + item["problem"], "", item["solution"], ""]
    rows += ["## Support", "", d["support"], ""]
    if d.get("license"):
        rows += ["## License", "", d["license"], ""]
    if profile == "source" and d.get("repository"):
        rows += ["<!-- repository:start -->", "", "## Development", "", d["repository"]["text"], ""]
        for link in d["repository"]["links"]:
            rows += [f"- [{link['label']}]({link['path']})"]
        rows.append("")
        rows += ["<!-- repository:end -->", ""]
    rows += [f"<!-- skill-readme:{profile} -->", ""]
    return "\n".join(rows)


def contract(root):
    path = Path(root) / "documentation.json"
    data = load(path)
    if data.get("schema_version") != 1 or not isinstance(data.get("name"), str):
        raise Invalid("Invalid documentation contract.")
    validate(data["documentation"], DOCUMENTATION)
    return data


def write(root, profile=None):
    root = Path(root)
    if profile is None:
        existing = root / "README.md"
        profile = "runtime" if existing.is_file() and "<!-- skill-readme:runtime -->" in existing.read_text() else "source"
    data = contract(root)
    (root / "README.md").write_text(render(data["name"], data["documentation"], profile))


def check(root):
    root = Path(root)
    data = contract(root)
    actual = (root / "README.md").read_text()
    profile = "runtime" if "<!-- skill-readme:runtime -->" in actual else "source"
    errors = []
    if actual != render(data["name"], data["documentation"], profile):
        errors.append("README differs from its public documentation contract.")
    metadata = (root / "SKILL.md").read_text().split("---\n", 2)
    if len(metadata) != 3 or not re.search(rf"^name:\s*['\"]?{re.escape(data['name'])}['\"]?\s*$", metadata[1], re.M):
        errors.append("README skill name does not match SKILL.md metadata.")
    commands = [*data["documentation"]["setup"], data["documentation"]["verification"]["command"], data["documentation"]["testing"]["run_command"]]
    commands += [row["command"] for row in data["documentation"]["scenarios"] if "command" in row]
    commands += [step["command"] for row in data["documentation"]["scenarios"] for step in row.get("steps", []) if "command" in step]
    for command in commands:
        for value in command["argv"][1:]:
            if value.endswith((".py", ".sh", ".txt")) and not value.startswith("-"):
                path = (root / value).resolve()
                if not path.is_relative_to(root.resolve()) or not path.is_file():
                    errors.append(f"Documented command references missing file: {value}")
    return {"passed": not errors, "findings": errors, "profile": profile}
