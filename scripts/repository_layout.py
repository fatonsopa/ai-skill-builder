"""Check the canonical skill repository layout without executing its content."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(root, policy=None):
    root = Path(root).resolve()
    policy = policy or json.loads((ROOT / "config/repository_layout.json").read_text())
    findings = []
    def issue(path, problem, recommendation):
        findings.append({"path": path, "problem": problem, "recommendation": recommendation})
    for name in policy["required_root_files"]:
        path = root / name
        if not path.is_file() or not path.read_text().strip():
            issue(name, "Missing or empty required root file.", "Provide " + name + " at the repository root.")
    allowed = set(policy["required_root_files"] + policy["optional_root_files"] + policy["local_only"]) | set(policy["resource_directories"])
    for path in sorted(root.iterdir()):
        if path.name not in allowed:
            target = policy["relocate_root_files"].get(path.name)
            issue(path.name, "File or directory has no root responsibility.", "Move to " + target if target else "Assign it to a resource folder or preserve internal records outside the repository.")
    for name in policy["external_records"]:
        if (root / name).exists():
            issue(name, "Internal records or a separate distribution are inside the skill.", "Archive internal records outside the repository; use the repository itself as the artifact.")
    for path in root.rglob("SKILL.md"):
        relative = path.relative_to(root)
        if relative == Path("SKILL.md") or any(part in {".git", ".venv", "__pycache__"} for part in relative.parts):
            continue
        issue(relative.as_posix(), "Nested skill entry point can cause duplicate discovery.", "Keep one canonical root SKILL.md; move snapshots outside the repository.")
    claude = root / "CLAUDE.md"
    if claude.is_file() and "@AGENTS.md" not in claude.read_text().splitlines():
        issue("CLAUDE.md", "Claude instructions do not import the shared rules.", "Include @AGENTS.md on its own line and keep shared rules in AGENTS.md.")
    domains_file = root / "config/domains.json"
    if domains_file.is_file():
        try:
            domains = json.loads(domains_file.read_text())["domains"]
            names = {row["name"] for row in domains}
            if len(names) != len(domains):
                raise ValueError("Domain names must be unique.")
            ownership = {}
            for row in domains:
                if not row.get("purpose", "").strip() or not row.get("owned_paths"):
                    raise ValueError("Each domain needs a purpose and owned paths.")
                if set(row.get("depends_on", [])) - names:
                    raise ValueError("A domain refers to an unknown dependency.")
                for name in row["owned_paths"]:
                    path = Path(name)
                    if path.is_absolute() or ".." in path.parts or not (root / name).exists():
                        raise ValueError("Missing or unsafe domain path: " + name)
                    if any(name == old or name.endswith("/") and old.startswith(name) or old.endswith("/") and name.startswith(old) for old in ownership):
                        raise ValueError("Overlapping domain ownership: " + name)
                    ownership[name] = row["name"]
            def visit(name, trail):
                if name in trail:
                    raise ValueError("Cyclic domain dependencies: " + " -> ".join([*trail, name]))
                row = next(row for row in domains if row["name"] == name)
                for dependency in row.get("depends_on", []):
                    visit(dependency, [*trail, name])
            for name in names:
                visit(name, [])
        except (ValueError, KeyError, TypeError) as error:
            issue("config/domains.json", str(error), "Give each component one owner and explicit acyclic dependencies; review actual responsibilities too.")
    return {"passed": not findings, "findings": findings, "root": str(root), "limits": "Structure and declared ownership only; domain cohesion and useful boundaries need semantic review."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = check(args.package)
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
