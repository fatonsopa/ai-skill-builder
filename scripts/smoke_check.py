#!/usr/bin/env python3
"""Check the installed Skill Builder entry point and typed workflow."""
import json
from pathlib import Path
import tempfile

from runtime.artifacts import check_package
from runtime.common import Invalid, validate
from runtime import contracts, workflow, completion


def check(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    package = check_package(root)
    if not package["passed"]:
        return {"passed": False, "checks": [], "errors": package["findings"]}
    checks = ["repository structure, MIT license and public README"]
    try:
        validate({"url": "not a uri", "checked": "2026-10-31", "decision": "check", "provenance": "user_supplied"}, contracts.SOURCE)
    except Invalid:
        checks.append("required URI validation rejects invalid input")
    else:
        return {"passed": False, "checks": checks, "errors": ["URI validation accepted invalid input."]}
    with tempfile.TemporaryDirectory(prefix="skill-builder-smoke-") as folder:
        run = Path(folder) / "run"
        policy = completion.create(folder, {'objective_id': 'installation-check', 'goal': 'Verify the installed native handoff.',
            'project': str(Path(folder) / 'smoke-target'), 'scope': ['**'],
            'checks': [{'id': 'report', 'kind': 'report', 'dependencies': []}],
            'budget': {'runs': 1, 'revisions': 0, 'model_calls': 0, 'seconds': 600},
            'delivery': {'kind': 'report', 'authority': 'Local installation smoke check only.'}})['policy']
        workflow.start(run, {'completion_policy': policy,"operation": "specify", "skill_name": "installation-check", "brief": "Check the authoring handoff."})
        packet = workflow.packet(run)
        workflow.submit(run, {
            "run_id": packet["run_id"], "phase": packet["phase"],
            "packet_sha256": packet["packet_sha256"],
            "data": {"sources": [], "findings": "Local installation check.", "gaps": []},
        })
        if workflow.read_state(run)["phase"] != "specify":
            return {"passed": False, "checks": checks, "errors": ["Invalid workflow transition."]}
        checks.append("typed workflow advances from research to specification")
    return {"passed": True, "checks": checks, "errors": []}


if __name__ == "__main__":
    result = check()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
