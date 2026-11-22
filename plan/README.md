# Skill Builder implementation handoff

To run Skill Builder and SpecDev together in Claude Code or Codex, use [Implement both plans](#implement-both-plans). For Skill Builder alone, use the [starting prompt](#starting-prompt).

This native change carries forward the approved Builder scope. The six epics contain eleven tasks. The handoff branch contains the audited Skill Builder source at `222b356fd5ac7a2df9fd9621e3744db883ecede0` and the planning packet. Implementation begins on the other computer. Implement and accept Skill Builder before using that candidate to ship SpecDev from the Technical Writer repository. Start with B1/T17. B3/T36 can start alongside it on the separate evaluator. B5/T50 can use a staged writer as soon as the baseline is bound. Use Technical Writer at its audited revision as the writing dependency. [Technical Writer handoff](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/README.md)

## Start

Open this handoff in the checkout you will use. Give the implementing agent the path to this file. It can read the starting prompt here. For a read-only rehearsal, give it only the checkout and the assessor’s question.

### Starting prompt

> Use Skill Builder to implement its approved changes on a local branch. Use the audited Technical Writer as the writing dependency. Stage and accept both writer identities under T50 before handing the accepted Builder commit to the writer implementer. Read the repository instructions, then follow this guide: open the native specification and design linked below, then follow the next eligible row in the native task list to its Issue. Implement only its scope. Verify its criteria on the candidate, record the evidence in the Issue and the private JSON log, commit the increment, and update its checkbox. Resume from the evidence on the next eligible row. Use `plan/test.md` for the handoff checks. Finish the approved integrated checks and report the local result.

## Implement both plans

**Session goal**

> Implement Skill Builder first, then use its accepted commit to implement SpecDev. Deliver each task against its own approved acceptance criteria. Test the riskiest assumption early, fix in-scope failures before dependent work continues, and use established engineering practices within the agreed scope. Verify each skill’s integrated behavior on Claude Code and Codex. Push all accepted changes to the two GitHub implementation branches and confirm the remote commits.

Either Claude Code or Codex can run this assignment. Read each repository’s `AGENTS.md` and follow its specification and execution rules. For this combined run, the owner authorizes ordinary pushes to each repository’s implementation branch. This supplies the push authority referenced in the individual handoffs. Merging to `main`, publishing packages and deploying still require separate authorization.

1. **Download and install both skills.** Follow [Set up a new computer](#set-up-a-new-computer) before invoking either skill. Record the checkout paths and handoff commits. When resuming, use the recorded local branches, installed copies and private JSON logs.
2. **Implement Skill Builder first.** Use the Skill Builder skill from its checkout and follow the [Builder starting prompt](#starting-prompt). Give Builder a separate checkout of [the audited Technical Writer](https://github.com/fatonsopa/ai-technical-writer/tree/4a8e7c92e20404f05e68708c1a3ea26c6961b178) through its existing `technical_writer` request field. Read the governing specification before changing code. Select eligible work from [Builder’s task list](../openspec/changes/improve-skill-builder/tasks.md), starting with T17 on a fresh run. Apply the task and push rules below to each increment in both repositories. T50 exercises both writer identities on staged copies while SpecDev stays at its handoff revision.
3. **Accept Builder and continue automatically.** Apply [Builder’s coverage and Definition of Done](../openspec/changes/improve-skill-builder/design.md#requirement-coverage), including the [integrated checks on Claude Code and Codex](../openspec/changes/improve-skill-builder/design.md#integrated-acceptance-on-codex-and-claude-code). Record the accepted Builder commit, its checkout path, the T50 result and the supporting evidence in the existing run records. Confirm the accepted Builder commit on GitHub, then continue directly into SpecDev. If a required check is blocked, continue eligible Builder work and report the missing proof before starting SpecDev.
4. **Implement SpecDev using the accepted Builder.** In the SpecDev checkout, read and execute the [SpecDev starting prompt](https://github.com/fatonsopa/ai-technical-writer/blob/c5e866daadf61cdf564c6f5c5f5d9781f6d16afa/plan/README.md#starting-prompt) as the next part of this assignment. Resolve Skill Builder from the accepted checkout and confirm its commit before the first change. Follow SpecDev’s native specification, design and task list, including its exclusions. T50 permits W46 to exercise the actual rename. Use SpecDev’s own integrated checks to verify the result on Claude Code and Codex.
5. **Verify each task as you go.** Before editing, read its scope, dependencies, criterion IDs and required proof. Check a risky dependency or shared interface as soon as the first usable change can exercise it. Prefer documented project conventions and established practices. When a technical choice is uncertain, consult the relevant official guidance. On a failure, record what happened, fix the cause within scope and rerun the smallest affected check. Close the task only when evidence on the identified candidate supports every criterion and the applicable Definition of Done. Reuse valid evidence. Keep out-of-scope discoveries in the owning plan’s pending decisions.
6. **Push and confirm delivery.** Commit and push each accepted increment to the implementation branch in its owning GitHub repository. Push the remaining approved integration and documentation changes when their checks pass. Use ordinary fast-forward updates and preserve existing work. If a push is rejected or its result is unclear, read the remote branch before deciding how to proceed. Keep private JSON logs outside Git. At closure, confirm each remote branch points to its accepted final commit, report both GitHub links and the separate host results, and identify any unproven criterion. If blocked, report the last confirmed result and the exact prerequisite for resuming.

### Set up a new computer

Use the same workspace as the original Mac: `/Users/faton/Documents/ChatGPT`. Create it if needed. Use the machine’s existing GitHub access (SSH or authenticated HTTPS). On an empty machine the checkout commands are:

```sh
workspace=/Users/faton/Documents/ChatGPT
mkdir -p "$workspace"
git clone --branch docs/autonomous-implementation git@github.com:fatonsopa/ai-skill-builder.git "$workspace/skill-builder"
git clone --branch docs/autonomous-implementation git@github.com:fatonsopa/ai-technical-writer.git "$workspace/technical-writer"
```

Skip a clone if the launch prompt already downloaded it. Verify its remote and revision. In each checkout, create a new local implementation branch at the specified commit: the Builder revision in the launch prompt and [the SpecDev handoff revision](https://github.com/fatonsopa/ai-technical-writer/tree/c5e866daadf61cdf564c6f5c5f5d9781f6d16afa). Use `implementation/improve-skill-builder` in `fatonsopa/ai-skill-builder` and `implementation/ship-specdev` in `fatonsopa/ai-technical-writer`. If a name is already in unrelated use, choose and record a fresh implementation branch. On a resumed run, stay on the recorded implementation branches. Preserve existing files and branches. If the exact directory is unavailable or belongs to another project, report that path before choosing a different one.

Check for Git, Python 3.11 or later, and Node.js 22.20.0 or later with npm. If a prerequisite is missing, use the machine’s existing user-level package manager when available. Report any permission or sign-in the owner must supply. Use the repositories’ source installers for this handoff. Run the commands below from each checkout, first `technical-writer`, then `skill-builder`. Use a supported Python executable if the system’s `python3` is older.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r scripts/requirements-lock.txt
.venv/bin/python scripts/install_skill.py --host claude-code
.venv/bin/python scripts/install_skill.py --host codex
```

Each installer prints its destination under `~/.claude/skills/` or `~/.agents/skills/`. In each installed folder, set up its `.venv` from its own `scripts/requirements-lock.txt` using the first two commands above. Run `.venv/bin/python scripts/smoke_check.py` there and check for `passed: true`. Reuse a matching installation and working environment on resume. Preserve a different installation and its edits. Use the source checkout directly for implementation while a host registration conflict is resolved.

Install this handoff’s locked OpenSpec dependency once and check the local executable:

```sh
npm ci --prefix /Users/faton/Documents/ChatGPT/technical-writer/tools/openspec
/Users/faton/Documents/ChatGPT/technical-writer/tools/openspec/node_modules/.bin/openspec --version
```

The expected OpenSpec version is `2.1.1`. Keep the implementation checkouts at the two workspace paths above. For Builder’s audited writing dependency, make a separate checkout of `4a8e7c92e20404f05e68708c1a3ea26c6961b178` in the private run directory and supply that path in the `technical_writer` request field. The current session can start work by reading `skill-builder/SKILL.md` from its checkout. Use fresh host sessions for the required activation checks. After Builder is accepted, use its accepted checkout for SpecDev as directed in step 4.

## Open the active change

The [proposal](../openspec/changes/improve-skill-builder/proposal.md), [specification](../openspec/changes/improve-skill-builder/specs/skill-assignments/spec.md), [implementation plan](../openspec/changes/improve-skill-builder/design.md) and [task list](../openspec/changes/improve-skill-builder/tasks.md) are the live implementation files. The links in `plan/` are for readers with an earlier bookmark. Mark completed work once, in the native task list.

From this repository's root, use OpenSpec 2.1.1 to inspect the handoff:

```sh
openspec status --change improve-skill-builder --json
openspec instructions apply --change improve-skill-builder --json
```

The second command reads task and artifact context. Implementation still requires the starting prompt's authority and settled task prerequisites. A ready artifact means the file exists; the criterion and evidence determine delivery. For the exact locked CLI, use the SpecDev handoff checkout alongside this one. Run `npm ci --prefix /path/to/technical-writer/tools/openspec`, then invoke `/path/to/technical-writer/tools/openspec/node_modules/.bin/openspec` from this Builder checkout. Supply the actual checkout path. This is a maintainer tool for this handoff; it adds no runtime dependency to Builder.

The release install and host setup are in [T51 and T52](../openspec/changes/improve-skill-builder/tasks.md#t51-issue). Exercise packaged candidates in isolated locations. Keep the public release commands marked as planned until the corresponding release asset or registry package is verified.

## Execution rules

1. **Bind the work.** Identify the handoff commit, governing specification, applicable repository instructions, candidate and skill dependencies. On resumption, read the existing task’s last accepted commit, evidence, open criteria and next eligible task. Protect existing work on all branches.
2. **Select one deliverable.** Resolve the task, parent outcome, supported criterion, affected interface, prerequisites, allowed change and required proof. Work from the reviewed record. Stop only affected work if a required decision or dependency is missing. Continue eligible independent tasks.
3. **Implement within scope.** Inspect the real entry point and keep the increment independently usable. Choose internal details within the agreed contract. Keep the original acceptance criteria and source authority. A new deliverable, new external action, changed permission or weaker criterion requires the owner’s explicit decision.
4. **Use evidence to limit verification.** Reuse applicable results. Run the smallest check that can disprove the candidate against the task’s criterion. A rare extra verification is appropriate when a concrete failure, changed input or missing evidence makes the approved result uncertain. Record the criterion, what the check established and the action it changes. Apply a supported better technique directly when it remains inside the task’s behavior, authority and quality obligations. General best-practice advice alone cannot enlarge scope.
5. **Defer other discoveries.** Append a brief entry to [Pending owner decisions](../openspec/changes/improve-skill-builder/design.md#pending-owner-decisions). Record evidence, impact, proposed change and any blocked task. Leave the change pending and move to eligible work. A material blocker can keep a criterion open without erasing prior results.
6. **Close and resume.** In the existing task, record each criterion as Met, Failed or Not demonstrated, with the exact candidate and evidence. Retain failures through correction. Commit each accepted increment on the local implementation branch, record the next task and continue. Reuse task evidence for story acceptance where it actually proves the integrated result. Report host-specific results separately. Remote integration, releases and deployment require separate authority.

## Check the result

For a read-only rehearsal, compare the reader’s choices with the [test specification](test.md). During implementation, record each criterion’s verdict and evidence in the linked Issue. Close the delivery when its integrated checks and shared Definition of Done pass on the identified candidate.

## Find your way around

1. Read the [audit](audit.md) for the source of a finding and the [specification](../openspec/changes/improve-skill-builder/specs/skill-assignments/spec.md) for the agreed behavior, stories and acceptance scenarios.
2. Open the [implementation plan](../openspec/changes/improve-skill-builder/design.md) for the approach, material dependencies, rollout and recovery.
3. Use [tasks.md](../openspec/changes/improve-skill-builder/tasks.md) to select the next eligible Issue. Its scope, acceptance criteria and proof live at that row. Follow its parent link to the story criterion in the specification. A separate `task.md` is optional.
4. Use [test.md](test.md) for the read-only rehearsal and the later implementation case.

## Limits and help

A rehearsal authorizes reading only. During a build, record an out-of-scope discovery under [Pending owner decisions](../openspec/changes/improve-skill-builder/design.md#pending-owner-decisions) and continue eligible work. If an Issue conflicts with the governing specification or its proof is stale, hold the affected row and use the plan’s [recovery instructions](../openspec/changes/improve-skill-builder/design.md#rollout-and-recovery).

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
