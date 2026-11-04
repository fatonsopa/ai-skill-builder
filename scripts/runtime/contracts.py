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
    "examples": TEXT, "technical_writer": TEXT, "document_paths": STRINGS,
    "copyright_holder": TEXT,
    "repair_structure": BOOL,
    "completion_policy": TEXT,
    "host": HOST,
    "preserve_literals": STRINGS,
    "target_success_percent": {"type": "number", "minimum": 0, "maximum": 100},
    "limits": LIMITS,
    "hard_limits": obj({name: {"type": "integer", "minimum": 0} for name in ("attempts", "seconds", "invocations")}, required=[]),
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
    "domains": array(obj({"name": TEXT, "purpose": TEXT, "owned_paths": array(TEXT, 1), "depends_on": STRINGS}), 1),
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
    "repository_instructions": TEXT,
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


# Version 1 remains available only for runs captured before workflow contracts.
PROTOCOL_VERSION = 2
LEGACY_PHASES = dict(PHASES)
WORKFLOW = obj({
    "id": TEXT, "purpose": TEXT, "trigger": TEXT,
    "steps": array(TEXT, 1),
    "boundaries": array(obj({"id": TEXT, "text": TEXT})),
    "branches": array(obj({"id": TEXT, "text": TEXT})),
    "recovery": array(obj({"id": TEXT, "text": TEXT})),
})
PROCESS = obj({
    "order": array(TEXT, 1), "visible": STRINGS, "evidence": STRINGS,
    "trace_file": TEXT,
}, required=["order", "visible", "evidence"])
WORKFLOW_CASE = obj({
    "id": TEXT,
    "scenario": {"enum": ["success", "invalid_input", "omission", "order", "boundary", "branch", "recovery", "behavior"]},
    "covers": STRINGS,
})
EXPECT = obj({**EXPECT["properties"], "process": PROCESS}, required=EXPECT["required"])
CASE = obj({**CASE["properties"], "kind": {"enum": ["command", "artifact", "behavior"]}, "expect": EXPECT, "workflow": WORKFLOW_CASE, "request": ANY, "resources": STRINGS}, required=CASE["required"])
SPEC = obj({**SPEC["properties"], "workflows": array(WORKFLOW, 1)})
PLAN = obj({**PLAN["properties"], "cases": array(CASE, 1)})
REVIEW = obj({
    **REVIEW["properties"],
    "workflow_findings": array(obj({"id": TEXT, "accepted": BOOL, "evidence": TEXT})),
    "workflow_inventory": obj({"accepted": BOOL, "evidence": TEXT}),
}, required=REVIEW["required"])
PHASES = {**PHASES, "specify": SPEC, "plan": PLAN, "review": REVIEW}


V2_PHASES = dict(PHASES)
PROTOCOL_VERSION = 4
AUTHORITY = obj({"tools": STRINGS, "read_roots": STRINGS, "write_roots": STRINGS,
                 "external_actions": STRINGS, "may_delegate": BOOL})
ROLE = obj({
    "id": TEXT, "eligibility": TEXT, "exclusions": TEXT,
    "inputs": array(TEXT, 1), "outputs": array(TEXT, 1), "recipient": TEXT,
    "authority": AUTHORITY, "dispatch": TEXT, "limits": TEXT, "recovery": TEXT,
    "method": TEXT,
    "assets": array(obj({"host": TEXT, "path": TEXT, "loaded_paths": STRINGS}), 1),
})
COVERAGE = obj({"requirement": TEXT, "status": {"enum": ["covered", "excluded", "unresolved"]},
                "roles": STRINGS, "cases": STRINGS, "reason": TEXT})
LIFECYCLE = obj({"event": {"enum": ["drift", "revocation", "late_result", "lost_return", "followup"]},
                 "applicable": BOOL, "reason": TEXT, "record_outcome": TEXT,
                 "accept_evidence": TEXT, "cases": STRINGS})
BINDING = obj({"id": TEXT, "origin": {"enum": ["source", "conversation", "external", "dependency", "output"]},
               "root": TEXT, "access": {"enum": ["read", "write"]}, "version_binding": TEXT})
DOCUMENT_CONTEXT = obj({"applicable": BOOL, "reason": TEXT, "sources": array(obj({
    "id": TEXT, "kind": TEXT,
    "status": {"enum": ["available", "missing", "stale", "conflicting", "not_applicable"]},
    "authority": {"enum": ["agreed", "proposed", "unknown", "superseded"]},
    "origin": TEXT, "version": TEXT, "sections": STRINGS,
    "roles": STRINGS, "requirements": STRINGS,
}))})
EXECUTION = obj({
    "mode": {"enum": ["single", "multi"]}, "rationale": TEXT,
    "file_workflow": BOOL, "file_reason": TEXT, "bindings": array(BINDING), "document_context": DOCUMENT_CONTEXT,
    "final_owner": TEXT, "roles": array(ROLE), "coverage": array(COVERAGE),
    "lifecycle": array(LIFECYCLE),
}, required=["mode", "rationale", "file_workflow", "file_reason", "bindings", "document_context"])
CASE = obj({**CASE["properties"], "fixtures": array(obj({"path": TEXT, "destination": TEXT, "sha256": TEXT}))}, required=CASE["required"])
PLAN = obj({**PLAN["properties"], "cases": array(CASE, 1), "execution": EXECUTION})
REVIEW = obj({**REVIEW["properties"], "execution_review": obj({
    "accepted": BOOL, "evidence": TEXT,
    "instruction_reviews": array(obj({"role": TEXT, "host": TEXT, "bundle_sha256": TEXT,
                                      "accepted": BOOL, "evidence": TEXT})),
})}, required=[*REVIEW["required"], "execution_review"])
PHASES = {**PHASES, "plan": PLAN, "review": REVIEW}


def response_schema(phase, protocol_version=PROTOCOL_VERSION):
    if protocol_version not in (1, 2, 3, PROTOCOL_VERSION):
        raise ValueError("Unsupported authoring protocol version.")
    phases = {1: LEGACY_PHASES, 2: V2_PHASES, 3: PHASES, 4: PHASES}[protocol_version]
    return obj({
        "run_id": TEXT, "phase": {"const": phase},
        "packet_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
        "data": phases[phase],
    })


# Captured execution events are distinct from a case's expected process order.
PROCESS_TRACE = obj({
    "provenance": obj({"kind": {"enum": ["authored_control", "historical_replay", "instrumented_execution", "host_observation"]}, "source": TEXT}),
    "events": array(obj({"phase": TEXT, "visible": BOOL, "evidence": TEXT}, required=["phase"]), 1),
})
PROCESS_TRACE["additionalProperties"] = True
PROCESS_TRACE["properties"]["provenance"]["additionalProperties"] = True
PROCESS_TRACE["properties"]["events"]["items"]["additionalProperties"] = True
PROCESS_TRACE_EXAMPLE = {
    "provenance": {"kind": "authored_control", "source": "Illustrative executable probe; replace with the actual capture source."},
    "events": [{"phase": "validate", "evidence": "probe-results.json"}],
}

LEGACY_REQUEST = REQUEST
REQUEST = {**REQUEST, 'required': [*REQUEST['required'], 'completion_policy']}
