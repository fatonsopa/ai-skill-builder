# Technical Writer integration

Skill Builder requires the `technical-writer` skill for every document it creates or changes. That dependency owns writing guidance, document contracts, review criteria and document acceptance. Skill Builder keeps package schemas, rendering, evaluation, edit scope, recovery and publication controls.

## Before you begin

Set `technical_writer` in the request to the skill folder or its `SKILL.md`, or set `SKILL_BUILDER_TECHNICAL_WRITER`. Otherwise the runner looks for an adjacent `technical-writer` folder, then the standard local skill locations under `~/.agents`, `~/.codex` and `~/.claude`. An explicit path takes precedence. The runner captures the dependency’s files; a changed dependency requires a new run. An unavailable dependency blocks document delivery.

Read the dependency guidance returned in each phase packet, then use its applicable references while authoring. The runner does not carry a second writing guide.

## Steps

After evaluation, the review packet lists `documents`, with paths and content hashes, and `document_validation_source`, containing the captured request and objective. The inventory includes generated instructions, public documentation, references, examples, text templates, visual documents and agent metadata. For maintenance, unchanged files and removals need no new document receipt. Declare additional document paths in request `document_paths` when a custom format is not automatically recognized. Unsupported document formats remain required and block delivery until Technical Writer can validate them.

For each listed document:

1. Use Technical Writer’s `validate_document.py` workflow to prepare a session outside the candidate and source. Include the exact `document_validation_source` as an inline source, alongside any other evidence needed to review the document.
2. Select the applicable kind and the complete output scope. `SKILL.md`, `README.md` and `AGENTS.md` require their respective complete `skill`, `readme` and project `agent` contracts. For supporting resources whose existing format must be retained, use Technical Writer’s review operation with the applicable kind. The `CLAUDE.md` import also uses review, preserving its consumed format.
3. Set the session destination to a separate validation copy. Run Technical Writer’s checks and source-grounded review against the actual candidate file. Retain the accepted review path. Follow Technical Writer’s workflow for any required discovery or rewrite preflight.
4. Save a manifest containing every required path exactly once:

```json
[
  {
    "path": "SKILL.md",
    "session": "/absolute/work/skill-document-session",
    "review": "/absolute/work/skill-document-session/reviews/OUTPUT_HASH/REVIEW_HASH.json"
  }
]
```

The paths above illustrate the manifest format; use the actual session and accepted review returned by Technical Writer. Then run:

```sh
.venv/bin/python scripts/skill_builder_cli.py validate-documents --run RUN_DIR --manifest MANIFEST.json
```

The runner invokes Technical Writer’s finalization on each exact candidate file, checks its accepted copy, and records the evidence outside the package. Refresh the review packet after this command and submit the existing evaluation and resource review. Missing, failed, incomplete or stale document validation prevents readiness. Favorable evaluation scores cannot waive this gate.

Before application or archive delivery, the runner rechecks the selected candidate, dependency, retained receipts, accepted copies and Technical Writer session validity. Changed documents need new validation. Archive delivery also requires the validated run: `package --run RUN_DIR --package PACKAGE --output OUTPUT.zip`. Historical replay retains its recorded evidence and cannot apply or export changes.

## Confirm success

Run `scripts/run_tests.py --execute` for impacted checks. The integration tests cover missing and failed validation, omitted documents, stale content, changed dependency/evidence, readiness and application. Authored validator transport controls test the runner’s boundaries; they do not establish language quality or fresh model performance. Use the installed Technical Writer for actual document acceptance.

## If it fails

Read `document_check.findings` in the lifecycle response and retain the failed attempt. Supply missing sessions or repair failed document checks through Technical Writer, then refresh the review packet. A later failed validation invalidates earlier acceptance for the current candidate; the runner retains its earlier receipts. If candidate bytes change, reevaluate the candidate and validate the changed documents again. A changed or unavailable Technical Writer dependency requires a new run with the intended skill installed.
