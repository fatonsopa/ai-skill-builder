# Repository instructions

## Test changes

During implementation, use `scripts/run_tests.py --execute` to run only impacted tests. The script derives changes from the last successful checkpoint or Git HEAD and reports why each check was selected. Do not invoke full unittest/pytest discovery or a full-suite helper directly. Unmapped changes must be assigned an impact rule; they must not trigger a full-suite fallback.

Run the full suite only after the user confirms the batch is finished, with an authorization record bound to the current artifact. Do not create that record without the actual user instruction. Final testing does not grant push approval.

## Routine test retries

Routine testing and necessary retries are part of the authorized task. Choose and record bounded batches from task complexity and observed results; do not ask for each extra test or retry. Use scripts/continuation.py for bounded extensions with a concrete reason. Preserve frozen criteria and all attempts. Stop and report when retries stall or their ceiling is reached. Explicit user hard limits, host permissions, scope changes and paid-service restrictions still apply.

## GitHub approval

Do not push to GitHub without the user's explicit approval for the completed changes being published. An earlier approval does not cover later edits. Prepare a concrete, reviewable result, report its validation, and wait for approval before pushing. A request to continue editing is not push approval.

## Shared instructions

Keep repository workflow rules in AGENTS.md. Always provide CLAUDE.md with an @AGENTS.md import so Claude Code uses the same rules. Preserve this pattern in skills created or maintained by Skill Builder.

## Repository maintenance

Keep one skill at the repository root and use config/repository_layout.json for its structure. Put repeatable mechanics in scripts, domain guidance in references, tests and evals with their responsible components, and internal records outside the repository. Review actual responsibilities as well as declared domain ownership.

README.md is rendered from config/documentation.json. Update its generator, guidance and affected tests when changing `README.md` requirements. New skills use the approved MIT template with a supplied copyright holder; preserve an existing license unless a change is authorized.

Use the environment containing scripts/requirements-lock.txt. Run impacted test methods or modules while editing. The repository-check helper uses the same scoped test runner. Keep private inputs and run snapshots outside the repository; keep public documentation focused on installation, invocation, use, evaluation and support.

## Document changes

Use the required `technical-writer` skill for every document created or updated in this repository, including instructions, references and generated public documentation. Follow references/technical_writer.md for the integration. Keep writing guidance in that dependency; Skill Builder owns its package schema, rendering and execution controls.
