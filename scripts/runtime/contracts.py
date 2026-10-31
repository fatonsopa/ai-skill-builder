"""Canonical machine-readable contracts; exposed by the CLI schema command."""


def obj(properties, required=None):
    return {
        "type": "object", "properties": properties,
        "required": list(properties) if required is None else required,
        "additionalProperties": False,
    }


def array(items, minimum=0):
    return {"type": "array", "items": items, "minItems": minimum}


TEXT = {"type": "string", "minLength": 1}
STRINGS = array(TEXT)
BOOL = {"type": "boolean"}
NUMBER = {"type": "number", "minimum": 0}
ANY = {}
REQUIREMENT = obj({"id": TEXT, "text": TEXT, "kind": {"enum": ["mechanical", "semantic"]}})
RESOURCE = obj({"path": TEXT, "purpose": TEXT, "when": TEXT, "outputs": STRINGS})
EXPECT = obj({
    "exit_code": {"type": "integer"},
    "stdout_json": ANY,
    "stdout_text": {"type": "string"},
    "contains": STRINGS,
    "file": TEXT,
    "file_json": ANY,
}, required=["exit_code"])
CASE = obj({
    "id": TEXT, "requirements": array(TEXT, 1), "critical": BOOL,
    "kind": {"enum": ["command", "artifact"]},
    "command": array(TEXT, 1), "stdin": ANY,
    "expect": EXPECT, "semantic": BOOL,
    "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 600},
}, required=["id", "requirements", "critical", "kind", "expect", "semantic"])
LIMITS = obj({
    "max_experiments": {"type": "integer", "minimum": 1},
    "max_seconds": {"type": "integer", "minimum": 1},
    "max_live_calls": {"type": "integer", "minimum": 0},
    "max_stagnant_experiments": {"type": "integer", "minimum": 1},
}, required=[])
HOST = obj({
    "platform": {"enum": ["chatgpt", "claude", "codex", "claude-code", "unknown"]},
    "model": {"type": ["string", "null"]},
    "code_execution": BOOL, "file_access": BOOL, "external_cli": BOOL,
    "allow_cross_provider": BOOL,
})
REQUEST = obj({
    "operation": {"enum": ["create", "modify", "refactor", "rebuild", "audit", "specify", "plan"]},
    "skill_name": {"type": "string", "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$", "maxLength": 64},
    "brief": TEXT, "source": TEXT, "allowed_paths": STRINGS,
    "examples": TEXT,
    "host": HOST,
    "preserve_literals": STRINGS,
    "target_success_percent": {"type": "number", "minimum": 0, "maximum": 100},
    "limits": LIMITS,
}, required=["operation", "skill_name", "brief"])
SOURCE = obj({
    "url": {"type": "string", "format": "uri"},
    "checked": {"type": "string", "format": "date"},
    "decision": TEXT,
    "provenance": {"enum": ["opened_by_agent", "user_supplied", "not_verified"]},
})
SPEC = obj({
    "purpose": TEXT, "inputs": TEXT, "outputs": TEXT,
    "requirements": array(REQUIREMENT, 1),
    "assumptions": STRINGS, "ambiguities": STRINGS,
})
PLAN = obj({
    "steps": array(TEXT, 1), "automations": array(TEXT, 1),
    "ai_responsibilities": STRINGS, "dependencies": STRINGS,
    "resources": array(RESOURCE),
    "cases": array(CASE, 1),
    "target_success_percent": {"type": "number", "minimum": 0, "maximum": 100},
    "allowed_candidate_paths": STRINGS,
})
DOC_COMMAND = obj({"argv": array(TEXT, 1), "stdin": ANY}, required=["argv"])
DOC_FILE = obj({"path": TEXT, "content": ANY})
DOC_STEP = obj({
    "title": TEXT, "text": TEXT,
    "command": DOC_COMMAND, "files": array(DOC_FILE, 1),
}, required=["title", "text"])
DOC_SCENARIO = obj({
    "title": TEXT, "prompt": TEXT, "expected_result": TEXT,
    "command": DOC_COMMAND, "input": ANY, "output": ANY,
    "introduction": TEXT, "steps": array(DOC_STEP, 1),
}, required=["title", "prompt", "expected_result"])
DOCUMENTATION = obj({
    "title": TEXT, "summary": TEXT, "prerequisites": STRINGS, "setup": array(DOC_COMMAND),
    "quick_start": obj({"prompt": TEXT, "expected_result": TEXT}),
    "scenarios": array(DOC_SCENARIO, 2),
    "verification": obj({"command": DOC_COMMAND, "expected_result": TEXT}),
    "troubleshooting": array(obj({"problem": TEXT, "solution": TEXT}), 1),
    "support": TEXT,
    "repository": obj({"text": TEXT, "links": array(obj({"label": TEXT, "path": TEXT}))}),
    "license": TEXT,
    "repository_url": {"type": "string", "format": "uri"},
    "testing": obj({
        "prepare": TEXT,
        "run_command": DOC_COMMAND,
        "acceptance_criteria": array(TEXT, 1),
        "improvement_steps": array(TEXT, 1),
    }),
}, required=["title", "summary", "prerequisites", "setup", "quick_start", "scenarios", "verification", "troubleshooting", "support", "testing"])
PRODUCE = obj({
    "description": TEXT, "instructions": TEXT, "usage": TEXT,
    "files": {"type": "object", "additionalProperties": {"type": "string"}},
    "remove": STRINGS,
    "documentation": DOCUMENTATION,
}, required=["description", "instructions", "files", "documentation"])
REVIEW = obj({
    "reviewer": obj({
        "kind": {"enum": ["human", "model"]}, "identity": TEXT,
        "method": TEXT,
    }),
    "cases": array(obj({
        "id": TEXT, "accepted": BOOL, "rationale": TEXT,
    })),
    "resource_findings": array(obj({
        "path": TEXT, "accepted": BOOL, "evidence": TEXT,
    })),
})
AUDIT = obj({
    "findings": array(obj({"path": TEXT, "problem": TEXT, "consequence": TEXT, "recommendation": TEXT})),
    "recommendation": {"enum": ["retain", "modify", "refactor", "rebuild"]},
    "rationale": TEXT,
})
PHASES = {
    "research": obj({"sources": array(SOURCE), "findings": TEXT, "gaps": STRINGS}),
    "specify": SPEC, "plan": PLAN, "produce": PRODUCE, "review": REVIEW, "audit": AUDIT,
}


def response_schema(phase):
    return obj({
        "run_id": TEXT, "phase": {"const": phase},
        "packet_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "data": PHASES[phase],
    })
