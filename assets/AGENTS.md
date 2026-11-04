# Repository instructions

## Test changes

During implementation, use `scripts/run_tests.py --execute` to run only impacted tests. The script derives changes from the last successful checkpoint or Git HEAD and reports why each check was selected. Do not invoke full unittest/pytest discovery or a full-suite helper directly. Unmapped changes must be assigned an impact rule; they must not trigger a full-suite fallback.

Run the full suite when you have verified that every planned implementation change has been delivered and no implementation work remains. Use an implementation-completion record bound to the current artifact; do not ask the user to approve an edit batch. Implementation completion does not assert that final validation or publication has passed. An implementation change invalidates the record. Final testing does not grant push approval.

## Complete the agreed work

Freeze the requested outcome, implementation scope, definition of done, validation checks and cumulative budget before implementation. Carry that contract and all consumed budget across versions and new run directories. Classify later findings as requirement blockers, follow-ups or material scope changes. A follow-up belongs in the backlog; only an evidenced blocker against an agreed requirement reopens the current work.

Use impacted checks and retain valid evidence for unchanged inputs, with its original artifact and date. Do not describe retained evidence as fresh or restart a whole benchmark after a small documentation edit. Report a scope or budget conflict before starting a large new batch. Once required work and checks pass, commit and deliver within existing authority, including pushing when authorized. Do not keep improving the completed scope.

## Routine test retries

Routine testing and necessary retries are part of the authorized task. Choose and record bounded batches from task complexity and observed results; do not ask for each extra test or retry. Use scripts/continuation.py for bounded extensions with a concrete reason. Preserve frozen criteria and all attempts. Stop and report when retries stall or their ceiling is reached. Explicit user hard limits, host permissions, scope changes and paid-service restrictions still apply.

## GitHub approval

Publish only within the user's existing explicit authority for this deliverable, remote and branch. Preserve that authority across routine edits and retries within the agreed scope; do not ask again merely because the implementation changed. If publication is not authorized, prepare the tested result for review and ask only for that remaining action. Never infer push or merge authority from permission to edit or test.

## Shared instructions

Keep repository workflow rules in AGENTS.md. Always provide CLAUDE.md with an @AGENTS.md import so Claude Code uses the same rules. Preserve this pattern in skills created or maintained by Skill Builder.
