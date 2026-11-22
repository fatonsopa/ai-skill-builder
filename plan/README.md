# Skill Builder implementation handoff

Use this handoff to implement Skill Builder on a local branch. It contains the starting prompt for Claude or Codex and the approved work for this repository.

The approved behavior and scope carry forward into specification revision 4 and implementation plan revision 5. The five epics contain nine tasks. The handoff branch contains the audited Skill Builder source at `222b356fd5ac7a2df9fd9621e3744db883ecede0` and the planning packet. Implementation begins on the other computer. Implement and accept Skill Builder before using that candidate to implement Technical Writer. Start with B1/T17. B3/T36 can start alongside it on the separate evaluator. B5/T50 can use a staged writer as soon as the baseline is bound. Use Technical Writer at its audited revision as the writing dependency. [Technical Writer handoff](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/README.md)

## Start

Open this handoff in the checkout you will use. Give the implementing agent the path to this file. It can read the starting prompt here. For a read-only rehearsal, give it only the checkout and the assessor’s question.

### Starting prompt

> Use Skill Builder to implement its approved changes on a local branch. Use the audited Technical Writer as the writing dependency. Stage and accept both writer identities under T50 before handing the accepted Builder commit to the writer implementer. Read the repository instructions, then follow this guide: read `plan/specification.md` and `plan/implementation-plan.md`, open `plan/tasks.md` and follow the next eligible row to its Issue. Implement only its scope. Verify its criteria on the candidate, record the evidence in the Issue and the private JSON log, commit the increment, and update its checkbox. Resume from the evidence on the next eligible row. Use `plan/test.md` for the handoff checks. Finish the approved integrated checks and report the local result.


## Execution rules

1. **Bind the work.** Identify the handoff commit, governing specification, applicable repository instructions, candidate and skill dependencies. On resumption, read the existing task’s last accepted commit, evidence, open criteria and next eligible task. Protect existing work on all branches.
2. **Select one deliverable.** Resolve the task, parent outcome, supported criterion, affected interface, prerequisites, allowed change and required proof. Work from the reviewed record. Stop only affected work if a required decision or dependency is missing. Continue eligible independent tasks.
3. **Implement within scope.** Inspect the real entry point and keep the increment independently usable. Choose internal details within the agreed contract. Keep the original acceptance criteria and source authority. A new deliverable, new external action, changed permission or weaker criterion requires the owner’s explicit decision.
4. **Use evidence to limit verification.** Reuse applicable results. Run the smallest check that can disprove the candidate against the task’s criterion. A rare extra verification is appropriate when a concrete failure, changed input or missing evidence makes the approved result uncertain. Record the criterion, what the check established and the action it changes. Apply a supported better technique directly when it remains inside the task’s behavior, authority and quality obligations. General best-practice advice alone cannot enlarge scope.
5. **Defer other discoveries.** Append a brief entry to [Pending owner decisions](./implementation-plan.md#pending-owner-decisions). Record evidence, impact, proposed change and any blocked task. Leave the change pending and move to eligible work. A material blocker can keep a criterion open without erasing prior results.
6. **Close and resume.** In the existing task, record each criterion as Met, Failed or Not demonstrated, with the exact candidate and evidence. Retain failures through correction. Commit each accepted increment on the local implementation branch, record the next task and continue. Reuse task evidence for story acceptance where it actually proves the integrated result. Report host-specific results separately. Remote integration, releases and deployment require separate authority.

## Check the result

For a read-only rehearsal, compare the reader’s choices with the [test specification](./test.md). During implementation, record each criterion’s verdict and evidence in the linked Issue. Close the delivery when its integrated checks and shared Definition of Done pass on the identified candidate.

## Find your way around

1. Read the [audit](./audit.md) for the source of a finding and the [specification](./specification.md) for the agreed behavior.
2. Open the [implementation plan](./implementation-plan.md) for the approach, story outcomes and detailed Issues.
3. Use [tasks.md](./tasks.md) to select the next eligible Issue. Its criteria and proof live in the linked plan section. A separate `task.md` is optional.
4. Use [test.md](./test.md) for the read-only rehearsal and the later implementation case.

## Limits and help

A rehearsal authorizes reading only. During a build, record an out-of-scope discovery under [Pending owner decisions](./implementation-plan.md#pending-owner-decisions) and continue eligible work. If an Issue conflicts with the governing specification or its proof is stale, hold the affected row and use the plan’s [recovery instructions](./implementation-plan.md#rollout-and-recovery).

## JSON execution log

Use the run’s existing JSON records first. Skill Builder’s behavioral harness already writes `public-events.json` during execution. Keep it in its native format. For task decisions or manual actions it does not capture, append one JSON object per line to `execution.jsonl` in the private run directory outside the repository. Link existing event IDs or evidence paths instead of copying full traces. On resumption, locate the same run and read the last confirmed checkpoint. Record observed actions and decisions when they happen.

| When | What to record |
| --- | --- |
| Choose work | UTC timestamp, run ID, task ID, criterion ID, candidate or source revision, intended action, and the clause that puts it in scope. |
| Before an extra test, review or retry | The unresolved criterion, changed input or observed failure, existing evidence inspected, the smallest useful check, and how pass or failure would change the next action. If neither outcome changes the decision, skip the check and record the reuse decision once. |
| Receive a result | Actual observation, outcome or error, evidence reference and candidate. Preserve failed attempts. For a correction, reference the original failure and resume from the last confirmed boundary. Record an unobserved result as unknown. |
| Defer or close | Scope decision, owner question if needed, criterion verdict, commit or candidate, evidence reused and next eligible task. Record a lesson only when evidence supports it, and change the current work only within its approved scope. |

A decision entry might look like the following. The values are illustrative.

```json
{"time":"2026-11-22T10:00:00Z","run_id":"example-run","task_id":"example-task","criterion_id":"example-criterion","candidate":"example-commit","event":"verification_decision","action":"reuse","reason":"The accepted result covers this criterion on the same candidate and the relevant input is unchanged.","evidence_ref":"task-evidence/observed-result.json","next":"Close this criterion"}
```

At task closure, read the task’s entries once. Check that every implemented change serves an approved criterion or necessary safeguard, and that each extra verification had a reason that could change the decision. Use any discrepancy to correct the current task or defer a new proposal. A JSON entry points to the evidence that proves the result. Keep the log metadata small. Exclude secrets, private reasoning and raw personal or customer content. The Markdown pending section holds owner decisions. Run events and the private JSON log stay outside the published handoff. [Skill Builder’s execution records](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/maintenance.md#diagnose-and-recover-stalled-work) · [OpenTelemetry log fields](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
