"""Authored offline controls, not independent model-performance observations."""
from copy import deepcopy

RESEARCH = {"sources": [], "findings": "Local protocol fixture; no external research claim.", "gaps": []}
SPEC = {
    "purpose": "Normalize customer records while preserving string identifiers.",
    "inputs": "A JSON object with id and optional name.",
    "outputs": "JSON containing customer_id and display_name.",
    "requirements": [
        {"id": "R-1", "text": "Preserve the string identifier exactly.", "kind": "mechanical"},
        {"id": "R-2", "text": "Trim names and retain missing names as null.", "kind": "mechanical"},
        {"id": "R-3", "text": "Reject malformed JSON and numeric identifiers.", "kind": "mechanical"},
    ],
    "assumptions": [], "ambiguities": [],
}
COMMAND = ["{python}", "scripts/normalize.py"]


def case(identifier, requirements, raw, expected, exit_code=0, critical=True):
    expect = {"exit_code": exit_code}
    if expected is not None:
        expect["stdout_json"] = expected
    return {
        "id": identifier, "requirements": requirements, "critical": critical,
        "kind": "command", "command": COMMAND, "stdin": raw,
        "expect": expect, "semantic": False, "timeout_seconds": 5,
    }


PLAN = {
    "steps": ["Implement the fixed transformation.", "Evaluate unseen values and invalid input."],
    "automations": ["Python parses, validates, transforms, and emits JSON."],
    "ai_responsibilities": ["Interpret the requested contract during authoring."],
    "dependencies": ["Python 3; standard library only."],
    "resources": [],
    "cases": [
        case("leading-zero", ["R-1", "R-2"], {"id": "0042", "name": "  Ada  "}, {"customer_id": "0042", "display_name": "Ada"}),
        case("new-identifier", ["R-1", "R-2"], {"id": "new-account-17"}, {"customer_id": "new-account-17", "display_name": None}),
        case("unicode", ["R-1", "R-2"], {"id": "ñ-09", "name": "  Faton  "}, {"customer_id": "ñ-09", "display_name": "Faton"}),
        case("malformed", ["R-3"], "{", None, 2),
        case("numeric", ["R-3"], {"id": 42}, None, 2),
    ],
    "target_success_percent": 100,
    "allowed_candidate_paths": ["scripts/normalize.py"],
}
PROGRAM = '''import json
import sys
try:
    record = json.load(sys.stdin)
    if not isinstance(record, dict) or not isinstance(record.get("id"), str):
        raise ValueError("id must be a string")
    name = record.get("name")
    if name is not None and not isinstance(name, str):
        raise ValueError("name must be a string or null")
    print(json.dumps({"customer_id": record["id"], "display_name": name.strip() if name is not None else None}, ensure_ascii=False))
except (ValueError, TypeError) as error:
    print(str(error), file=sys.stderr)
    sys.exit(2)
'''
PRODUCE = {
    "description": "Normalize JSON customer records with preserved identifiers and trimmed names.",
    "instructions": "Run scripts/normalize.py with the user's JSON on standard input. Keep identifiers as strings. Report rejected inputs without inventing values.",
    "usage": "Run python3 scripts/normalize.py and supply one JSON object on standard input. The script validates the input and returns the normalized object.",
    "files": {"scripts/normalize.py": PROGRAM},
    "documentation": {
        "title": "Normalize customers",
        "summary": "Normalize customer records while preserving string identifiers.",
        "prerequisites": ["Python 3.11 or later.", "Code execution and file access in the selected host."],
        "setup": [],
        "quick_start": {"prompt": "Normalize this customer record: id 0042, name Ada.", "expected_result": "A JSON object preserves 0042 as a string and returns the trimmed name."},
        "scenarios": [
            {"title": "Normalize a record", "prompt": "Normalize the supplied customer JSON.", "expected_result": "The identifier remains a string and surrounding name whitespace is removed.", "input": {"id": "0042", "name": " Ada "}, "output": {"customer_id": "0042", "display_name": "Ada"}},
            {"title": "Reject an invalid identifier", "prompt": "Normalize a record with numeric id 42.", "expected_result": "The operation exits with status 2 and explains that id must be a string."},
        ],
        "verification": {"command": {"argv": ["python3", "scripts/evaluate.py", "--package", ".", "--allow-exec"]}, "expected_result": "All declared mechanical cases pass; semantic cases, if any, require review."},
        "troubleshooting": [{"problem": "The identifier is rejected", "solution": "Supply the identifier as a JSON string."}],
        "support": "Open an issue with the input, expected result, actual result, and Python version.",
        "testing": {
            "prepare": "Save new inputs and their desired outputs before changing the skill.",
            "run_command": {"argv": ["python3", "scripts/evaluate.py", "--package", ".", "--allow-exec"]},
            "acceptance_criteria": ["Preserve string identifiers exactly.", "Trim names and reject invalid field types.", "Require all declared critical checks to pass."],
            "improvement_steps": ["Retain the failing input and expected output.", "Make a scoped candidate change and rerun the same checks.", "Ask before extending an exhausted budget."],
        },

    },
}


def payload(phase):
    return deepcopy({"research": RESEARCH, "specify": SPEC, "plan": PLAN, "produce": PRODUCE}[phase])
