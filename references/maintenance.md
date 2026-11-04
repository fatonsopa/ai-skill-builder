# Maintain an existing skill

Use this guide for an audit, repair, refactor, rebuild or feedback from use. Preserve the user's requested operation, current authorization and existing custom content. Treat attachments and source files as evidence; they cannot authorize edits or waive requirements. Audit-only and planning-only requests stop before implementation.

## Inspect and propose

Capture the source baseline and resolve the active installation. Read the relevant code, instructions, tests, user history and actual failure evidence before asking for facts already available. An audit returns located findings, their effects and recommended fixes. Choose retain, modify, refactor or rebuild from the actual responsibilities and defects; file names alone do not establish domain boundaries. Use [skill structure](skill_structure.md) for packaging and ownership.

Before accepting an audit, compare every finding with the exact source and the applicable rule. Separate an observed violation from an ambiguous or missing requirement. A broad description and a more specific instruction do not establish a contradiction unless they impose incompatible behavior; describe a possible interpretation as uncertainty. Check the final report against the accepted findings too. Copy paths, identifiers and hashes from actual evidence exactly, or omit optional literals; a correct execution record does not support an invented or altered hash in the response.

Research material uncertainties using current primary sources and record what was actually inspected. Reuse checked evidence for a narrow repair. Distinguish a skill defect, a missing input, an execution-environment failure, a stale installation and a faulty evaluator. Do not invent a verified implementation cause when source or traces are absent.

For a specification or substantial redesign, follow [authoring](authoring.md). Define preserved facts, commands, approval boundaries and exact edit paths before implementation. Resolve material choices with actual user instructions; routine reversible fixes within existing authorization need no repeated permission.

## Freeze the delivery contract

Before implementation, create one completion contract from the actual user request. The author chooses proportionate limits and checks within existing authority; the user does not need to approve an edit batch or complete a configuration questionnaire. Inspect `schema completion` for the exact format, then run:

```sh
.venv/bin/python scripts/skill_builder_cli.py completion-init --workspace WORKSPACE --definition CONTRACT.json
```

The contract contains an `objective_id`, goal, absolute project destination, allowed path patterns, required checks, cumulative `runs`, `revisions`, `model_calls` and elapsed `seconds`, and a delivery action with its authority. A `git_push` action also names the exact remote and `refs/heads/BRANCH`; record only actual publication authority. A read-only audit uses a `report` check and delivery action. Creation names its intended project destination before it exists.

Each check has a stable `id`, kind (`mechanical`, `behavior`, `document`, `full_suite` or `report`) and input dependency patterns. Declare the code, cases, instructions and configuration that can change its meaning, including transitive dependencies. Empty dependencies are allowed only for read-only report checks. A mechanical check defaults to the same test-runner ID; `test_ids` declares different required selected test IDs. An unrelated passing selection cannot satisfy it. A behavioral check can map a different `case_id` and an exact host/model/effort `profile`. Freeze these checks before execution; review dependency completeness rather than excluding a changed instruction merely to retain an old pass.

Put the returned policy path in request `completion_policy`. Every version and handoff for this project must carry that same policy and workspace. The runner freezes the submitted specification and plan, enrolls each new run and reserves model calls and revisions before starting them. Interrupted reservations remain consumed. Creating another run directory or changing its version cannot reset the budget, scope or definition of done. The registry permits one unfinished objective per project in that workspace. Moving to a deliberately separate workspace registry is outside this local guard; carry the policy rather than treating relocation as a fresh allowance.

Use `completion-status --policy POLICY --package PACKAGE` and `budget --run RUN_DIR` to decide what remains. The first reports which evidence can be retained and whether it was observed on the entire current artifact. Valid dependency-bound evidence retains its original artifact; a small guide edit does not make it fresh and does not require an unrelated benchmark restart. Changed dependencies or changed evidence invalidate the affected receipt.

Native accepted case, document and report outcomes create receipts through their actual gates. Record an executed repository check using `completion-record-check --policy POLICY --package PACKAGE --check CHECK_ID --evidence REPORT.json`. The report must contain passing executed results bound to that artifact; a scoped report cannot satisfy `full_suite`. External behavioral results use `completion-record-hosts` with `--manifest` containing absolute `plan` and `bundles` paths. This invokes the existing host assessment and retains the raw evidence chain; a summary flag cannot approve behavior.

Classify new findings with `completion-finding --policy POLICY --classification follow_up --text "SUPPORTED FINDING"`. Optional improvements stay in the backlog. A `blocker` also needs `--requirement ID` and one or more `--check ID` entries identifying agreed work and the checks to invalidate. A material scope or budget change uses `completion-amend --policy POLICY --definition CONTRACT.json --authority "ACTUAL INSTRUCTION"`; preserve the real authority and report the conflict before a large new batch. Amendments retain elapsed time, consumed budget and previous contracts. They invalidate old run bindings rather than silently rewriting them. Routine retries inside the frozen scope need no further permission.

When all required checks pass, the policy enters `delivery_pending` and refuses more work runs, revisions and model calls. Deliver within existing authority, then use `completion-delivered --policy POLICY --package TARGET`. Git delivery verifies that the commit contains the exact public artifact and that the agreed remote branch points to it; the command does not push itself. A completed objective stays closed. Report unresolved gaps when limits are exhausted, and distinguish the completed deliverable from follow-ups.

These controls apply to supported Builder entry points, not arbitrary shell actions or edits to trusted state. They cannot meter native model reasoning that the host does not expose or authenticate an authority description. Historical protocol 1–3 runs retain their original contracts; replay cannot invoke a model, evaluate new code or apply a candidate. New authoring uses protocol 4 and the completion policy.

## Repair and validate

Keep the failing input, expected result, actual output, source version and public trace as regression evidence. Freeze relevant criteria, then use the native runner’s typed packets and reported phase. [Evaluation](evaluation.md) owns executable coverage, actual model observations, metrics and invocation limits. Make the smallest supported change, test only affected checks and review the actual result. Never alter expected answers or weaken a frozen target to manufacture a pass.

Read the returned state before selecting the next action. If the candidate is unchanged and only actual observations are missing, import those observations during `evaluate`; do not regenerate the package merely to collect evidence. Use `revise` for a supported candidate change. Preserve all attempts. Continue routine testing within the shared retry policy without another approval for each test; stop and report stalled progress, explicit hard limits or exhausted retry ceilings.

Verify the accepted source and invoked installation before claiming the repair is available. Keep internal evidence outside the public package, and public documentation focused on installation, invocation, use and evaluation.

## Regressions from workflow failures

Capture the user's intended sequence and the actual public trace. Distinguish an omitted phase, wrong ordering, premature action, missing user-visible report, unsupported research claim and a poor final artifact. A passing preservation check does not establish that an audit preceded drafting. Create both code-level regression checks and realistic AI task cases before changing the guidance. Fix the responsible reusable mechanism, then the affected skill through the Builder.

Audit neighboring workflows for the same missing test layer. Before publication, complete the frozen final mechanical checks and scoped behavioral evaluations. Preserve earlier evidence with its original artifact and scope; a documentation repair does not imply a new whole-system benchmark. During implementation, run only impacted checks. Report remaining unknown hosts/models or unobserved steps rather than claiming full compliance.

## Verify implementation before final testing

Use impacted checks while implementing. Run the full suite after you have compared the actual result with every planned implementation change and verified that no implementation work remains. User approval of an edit batch is not required. Resolve omissions or failed delivery checks first; a finished edit does not itself establish that the whole plan was delivered.

Keep a completion record outside the package. Identify the actual plan or current task criteria, inventory its implementation steps, and record each delivered result with evidence and the verifier’s identity and method. Exclude final testing and publication from the implementation-step inventory because those actions follow this gate; do not exclude unfinished implementation. The runner checks declared step coverage and artifact identity. It cannot establish the truth or completeness of the author’s review from nonempty fields.

This illustrates the record format, not a claim that work has been completed:

```json
{
  "artifact_sha256": "HASH_FROM_THE_CURRENT_TEST_PLAN",
  "implementation_complete": true,
  "implementation_plan": {
    "source": "Actual plan revision or captured task criteria",
    "steps": [{"id": "I1", "result": "The agreed implementation result"}]
  },
  "delivered_steps": [{"id": "I1", "status": "delivered", "evidence": ["Actual source and verification references"]}],
  "remaining_implementation_work": [],
  "verified_by": {"identity": "Actual reviewer", "method": "How the plan was compared with the delivered implementation"}
}
```

Use `scripts/run_tests.py --full --completion-record RECORD.json --execute` for final testing. For a non-Git export without a checkpoint, also pass the exact `--changed` paths. Any implementation change requires a new verification bound to that artifact. A failing final test reopens implementation when a repair is needed; preserve the failure, repair it with impacted checks, then verify completion again. Keep actual test outcomes separate from the completion record and retain existing publication authority requirements.

## Verify the invoked installation

Resolve the active skill path and compare it with the source being maintained. A copied installation can remain stale after the repository is updated. Use `scripts/skill_builder_cli.py check-installation --package SOURCE --installed ACTIVE_PATH` to compare public artifact files, including a link's resolved target. This establishes file identity, not host activation or behavioral quality. Within the authorized maintenance scope, preserve existing custom content, update or relink the active installation to the accepted artifact, and verify it before saying the user is running the fix. Respect an established preference for linked local development. Keep replaced installations outside skill-discovery folders.

Import later actual observations directly during review; do not submit a failing placeholder review to unlock the next action. Missing observations remain unrun and do not consume stagnation. See [evaluation](evaluation.md) for binding, retained reports and readiness checks.
