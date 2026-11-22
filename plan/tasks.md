# Skill Builder implementation tasks

Read the [specification](./specification.md) for the required behavior and the [implementation plan](./implementation-plan.md) for the delivery approach. In this Markdown handoff, each row links to its Issue immediately below. Expand its details for the scope, acceptance criteria, required proof and parent story criterion. The path in a row points to a starting file. The Issue identifies the full change. The short task number is local to this list. Use the linked Issue ID when handing work to another repository.

Start with B1/T17 on the bound Builder baseline. T36 can run alongside it on the separate performer interface. T50 can use a staged writer as soon as the baseline is bound. The first usable result is a bounded assignment that reaches the next work packet. An accepted Builder with B5/T50 is the input to the writer handoff.

Order expresses delivery preference. An Issue can start when its stated inputs, authority and dependencies are settled. `[P]` identifies the opening pair whose changes can run in parallel. A writing-only request ends at the reviewed list. During an authorized build, open the next eligible Issue, verify it, record the candidate and evidence there, mark its row, then return here. Verify each story at its linked acceptance criteria. [Read-only handoff test](./test.md)

## B1 · Commission work that serves an approved requirement

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./specification.md#b1--commission-work-that-serves-an-approved-requirement)

- [ ] T001 [P] [US1] Admit a source-bound work assignment. `scripts/runtime/contracts.py`. [T17 · T17.a, T17.b](#t17--admit-a-source-bound-work-assignment) Start here after binding the baseline.

### T17 · Admit a source-bound work assignment

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

Today an unrelated publication step can sit alongside complete case coverage. The plan author and reviewer need to know exactly what the implementer may deliver.

#### Expected outcome

A maintainer can submit one bounded assignment through plan admission and hand the accepted entry to production. This commit ships both the producer and the consuming packet.

#### Scope

Cover independent work, permitted effects, governing revision, criterion or justified safeguard, owner role, prerequisites and proof. Keep ordinary substeps inline. Preserve existing versioned reads and scope enforcement.

#### Specification

Parent [B1](./specification.md#b1--commission-work-that-serves-an-approved-requirement) · [B1.a](./specification.md#b1-a) · R1/A1. Owner role: plan-contract maintainer. Input: the captured plan fixture and the audit’s publishing-step mutation.

#### Acceptance criteria

- **T17.a** Given the approved fixture, submit an authorized contribution, then a necessary safeguard with an explicit rationale. Each accepted entry appears in the next work packet with the same revision, scope and proof. Save the submitted and consumed rows. <a id="t17-a"></a>
- **T17.b** Replace its criterion with an unknown ID. Admission identifies the row and ID before production. Attach the real ID to the unrelated publishing instruction instead. The plan reviewer rejects its meaning. Save the diagnostic and the reviewer’s cited source. Neither case permits publication. <a id="t17-b"></a>

#### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

#### Additional context

Use this handoff’s B4/T48 Issue as the supported contribution in [B-PACKET](./test.md#cases). Inspect the real admitted and consumed assignment. Keep the existing justified-safeguard, rejection and compatibility checks.

First signal: reuse the audit mutation at its documented consistency-function boundary. Close on the packet and semantic verdict at the supported interface. One fixture covers the variations. No customer data or publishing command is needed.

</details>

## B3 · Assess an ordinary request without revealing the grader’s clues

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./specification.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [ ] T002 [P] [US3] Export a neutral native task with a traceable result. `scripts/evaluate.py`. [T36 · T36.a, T36.b](#t36--export-a-neutral-native-task-with-a-traceable-result) Can start alongside T17 on the native evaluator. Coordinate edits with T24 if both would change the same evaluator.

### T36 · Export a neutral native task with a traceable result

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

The native packet exposes a descriptive case ID and development filenames. Some contain a strong clue about the expected answer.

#### Expected outcome

A caller can export the task, supply it to a performer and associate the returned observation with its original case through the controller.

#### Scope

Change the native export and its actual controller consumer together. Preserve user-specified filenames, task resources, historical report reading and case/candidate bindings.

#### Specification

Parent [B3](./specification.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues) · [B3.a](./specification.md#b3-a) · R3/A3. Owner role: native-evaluation maintainer. Input: the captured native packet and one ordinary user filename.

#### Acceptance criteria

- **T36.a** Export a case with a distinctive test label and a separate user filename. Inspect the actual performer view. It retains the ordinary request and file, and excludes the label, expected answer and grader-only inventory. Save the exported view. <a id="t36-a"></a>
- **T36.b** Submit a matching observation to the controller and then one with a stale case binding. Only the matching observation is eligible for the intended case and candidate. Save the two decisions; a match alone does not prove task success. <a id="t36-b"></a>

#### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_behavior_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_evaluation.py)

#### Additional context

Use one local export and the matching/mismatched observation pair. Stop at the controller decision. The commit can ship independently because native callers and their new result mapping are updated together.

</details>

## B1 · Commission work that serves an approved requirement (continued)

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./specification.md#b1--commission-work-that-serves-an-approved-requirement)

- [ ] T003 [US1] Expose a requirement that has tests but no owning work. `scripts/runtime/artifacts.py`. [T18 · T18.a, T18.b](#t18--expose-a-requirement-that-has-tests-but-no-owning-work) After T17 supplies the admitted assignment.

### T18 · Expose a requirement that has tests but no owning work

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

A complete set of cases can still leave no implementer responsible for a requirement. The plan owner needs the reverse mapping before claiming coverage.

#### Expected outcome

A maintainer reviewing a plan can locate an unowned requirement and correct its assignment in the same work record.

#### Scope

Extend the existing coverage result and its normal plan consumer. Preserve the T17 safeguard route and the historical plan reader.

#### Specification

Parent [B1](./specification.md#b1--commission-work-that-serves-an-approved-requirement) · [B1.b](./specification.md#b1-b) · R1/A1. Owner role: coverage maintainer. Dependency: the admitted [T17](#t17--admit-a-source-bound-work-assignment) assignment representation.

#### Acceptance criteria

- **T18.a** From a valid T17 plan, remove the sole owning assignment while retaining its test. Coverage names the orphaned requirement and cannot report complete coverage. Restore that assignment and observe the resolved result. Retain the two results from the same fixture. <a id="t18-a"></a>
- **T18.b** Open one captured pre-change plan through its supported reader. Its original version and recorded meaning remain readable. Cite existing binding-compatible evidence when the reader and its inputs are unchanged. <a id="t18-b"></a>

#### Relevant files

[scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

#### Additional context

Commit the reverse-coverage result, its consumer and focused regression together. Stop after the orphan, recovery and compatibility evidence is recorded. Reuse the forward-mapping verdict from T17.

</details>

## B2 · Accept valid work in either order

**Demonstrate the story.** Accept both valid read orders and locate a premature decision or missing prerequisite. [Story criteria](./specification.md#b2--accept-valid-work-in-either-order)

- [ ] T004 [US2] Grade independent reads in an explicitly supplied evaluation case. `scripts/evaluate.py`. [T24 · T24.a, T24.b](#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case) Start once the dependency representation and its version boundary with B1 are settled. Coordinate evaluator edits with T36.

### T24 · Grade independent reads in an explicitly supplied evaluation case

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

The current grader rejects a correct trace solely because the example was read before the brief. A maintainer with an explicitly supplied case needs a usable evaluation path immediately.

#### Expected outcome

A case author can run an opt-in dependency-aware case through the existing evaluator’s `--suite` and `--case` entry. Existing strict cases continue to run.

#### Scope

Ship the reader for the new case form, its validation, grading, evidence and visibility checks, usage guidance and regression together. Keep normal generated plans on the existing format until T25 can emit the new one safely.

#### Specification

Parent [B2](./specification.md#b2--accept-valid-work-in-either-order) · [B2.a](./specification.md#b2-a) · R2/A2. Owner role: evaluator maintainer. Input: the captured three-step failure. Settle the dependency representation with the workflow maintainer first.

#### Acceptance criteria

- **T24.a** Run the same three-step case with each valid read order. Both pass the process check. Move the decision before one read, omit a read, or withhold required evidence/visibility. Each affected variant fails for its actual missing condition. Retain the process verdict per trace. <a id="t24-a"></a>
- **T24.b** Submit a malformed relation with an unknown prerequisite or cycle. It cannot yield a passing process result. Reuse the existing reversed strict-order case to show legacy behavior. Preserve the original failed audit trace. <a id="t24-b"></a>

#### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_process_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_process_evaluation.py)

#### Additional context

One parameterised three-step fixture is sufficient. Use existing visibility/omission controls where their path and inputs remain applicable. The commit ships a directly usable evaluator feature, including its failure handling. No generated package or model run is needed to accept this task.

</details>
- [ ] T005 [US2] Generate checks only for declared workflow dependencies. `scripts/runtime/contracts.py`. [T25 · T25.a, T25.b](#t25--generate-checks-only-for-declared-workflow-dependencies) After T24, with T17’s schema-version boundary settled.

### T25 · Generate checks only for declared workflow dependencies

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

The plan authoring path still derives an order obligation for adjacent steps. An author needs its emitted cases to honor the same relation the evaluator can grade.

#### Expected outcome

Submitting a dependency-aware workflow now generates a usable case for the distributed evaluator. Both ends support the same rule at this commit.

#### Scope

Update authoring instructions, versioned declarations, coverage derivation and the actual generated consumer. Preserve the default for historical workflows, required branches and recovery checks.

#### Specification

Parent [B2](./specification.md#b2--accept-valid-work-in-either-order) · [B2.b](./specification.md#b2-b) · R2/A2. Owner role: workflow-contract maintainer. Requires [T24](#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case) and a settled schema-version boundary with [T17](#t17--admit-a-source-bound-work-assignment).

#### Acceptance criteria

- **T25.a** Submit the three-step workflow. Its emitted case requires both reads before the decision and contains no invented dependency between reads. Run one previously rejected valid order using the generated evaluator. Retain the emitted relation and verdict. Reuse T24’s trace matrix when the grader is unchanged. <a id="t25-a"></a>
- **T25.b** Submit the same declaration with a cycle and then an unknown prerequisite. Plan admission identifies the offending relationship before execution. A legacy strict declaration still emits its strict order. Retain the diagnostics and original-format comparison. <a id="t25-b"></a>

#### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_workflow_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_workflow_coverage.py)

#### Additional context

First inspect the emitted relation. If correct but execution disagrees, resume at the generated evaluator, preserving the accepted admission evidence. This single connected check closes the producer/consumer gap without exercising every permutation.

</details>

## B3 · Assess an ordinary request without revealing the grader’s clues (continued)

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./specification.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [ ] T006 [US3] Stage a neutral host workspace and recover its real case identity. `tools/run_behavioral_evals.py`. [T37 · T37.a, T37.b](#t37--stage-a-neutral-host-workspace-and-recover-its-real-case-identity) After T36 supplies the fixture and controller identity.

### T37 · Stage a neutral host workspace and recover its real case identity

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

A neutral native packet does not fix the host route. The current harness inserts the descriptive case ID into paths shown to the performer.

#### Expected outcome

A maintainer can stage and launch a task through the existing harness and look up its evidence under the true case after return.

#### Scope

Cover the host-visible prompt, submitted arguments, working directory, task and dependency paths. Keep user files, historic report lookup, receipt bindings and unchanged host permission settings.

#### Specification

Parent [B3](./specification.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues) · [B3.b](./specification.md#b3-b) · R3/A3. Owner role: host-harness maintainer. Reuse [T36](#t36--export-a-neutral-native-task-with-a-traceable-result)’s fixture and controller identity convention.

#### Acceptance criteria

- **T37.a** Stage that case through the actual launch builder with a local recording adapter. Inspect the final submitted inputs and staged roots. The user filename is intact and no grader-only label, answer or path inventory reaches the performer. Capture both host-specific forms where their path or argument construction differs. <a id="t37-a"></a>
- **T37.b** Resolve the captured result to the original case and candidate through the normal report consumer. Open one historical report using its recorded identity. A stale binding remains ineligible. Reuse T36’s negative evidence wherever the same unchanged reader decides it. <a id="t37-b"></a>

#### Relevant files

[tools/run_behavioral_evals.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tools/run_behavioral_evals.py) · [scripts/host_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/host_coverage.py) · [tests/test_behavior_harness.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_harness.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md)

#### Additional context

Ship the harness, changed reader and path-compatibility regression together. A recorded launch settles this input question. Spend a live host run only for the separately specified A5 behavior.

</details>

## B4 · Keep related observations and decision authority through a handoff

**Demonstrate the story.** Follow the two sourced observations from assignment to return while the retry decision stays with its owner. [Story criteria](./specification.md#b4--keep-related-observations-and-decision-authority-through-a-handoff)

- [ ] T007 [US4] Commission related reports as a bounded investigation. `references/agents_and_skills.md`. [T48 · T48.a, T48.b](#t48--commission-related-reports-as-a-bounded-investigation) After T17 supplies the accepted assignment shape.

### T48 · Commission related reports as a bounded investigation

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

The current delegation guide describes independent modules. Add an example showing how the lead decides what to do with two correlated reports before dispatch.

#### Expected outcome

A skill author can use a worked assignment from the existing guide, complete with sources, shared criterion, allowed work, recipient, return obligation and stop condition.

#### Scope

Cover the lead’s decision and outgoing assignment, including a single-owner path and a justified split. Include contrasting weak and corrected wording. Preserve current role definitions and host capabilities.

#### Specification

Parent [B4](./specification.md#b4--keep-related-observations-and-decision-authority-through-a-handoff) · [B4.a](./specification.md#b4-a) · R4/A4. Owner role: orchestration-guidance maintainer. Requires [T17](#t17--admit-a-source-bound-work-assignment)’s assignment shape. Use the synthetic reports and actual WEB-09 source in the [integrated assignment](./implementation-plan.md#integrated-acceptance-on-codex-and-claude-code).

#### Acceptance criteria

- **T48.a** Give a reader the finished assignment and its linked sources. They can recover both observations, WEB-09, allowed investigation and the required return. The cause remains open. A split must identify independent outputs or their integration owner. Retain the reviewed passage and source comparison. <a id="t48-a"></a>
- **T48.b** In the single-owner variant, the same assignment remains usable without dispatch. The worker has no authority to issue a retry. Inspect the authority and recipient fields in that same example. <a id="t48-b"></a>

#### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md)

#### Additional context

The commit ships a complete, reusable commissioning example. Review the actual writing through Technical Writer. Reuse that review for the authored example; the later A4/A5 observation establishes behavior through the installed skill.

</details>
- [ ] T008 [US4] Return supported conclusions and the owner’s retry decision. `references/agents_and_skills.md`. [T49 · T49.a, T49.b](#t49--return-supported-conclusions-and-the-owners-retry-decision) After T48 supplies the assignment.

### T49 · Return supported conclusions and the owner’s retry decision

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

A useful assignment can still end with a lead treating an unverified cause as established or presenting an optional retry as required.

#### Expected outcome

A lead can consume the T48 assignment and its returned evidence, then give the owner an accurate disposition through the existing orchestration guide.

#### Scope

Complete the return and user-facing side of the worked example. Bind one realistic shared assessment to the existing case and rubric system. Keep expected answers outside the performer’s task.

#### Specification

Parent [B4](./specification.md#b4--keep-related-observations-and-decision-authority-through-a-handoff) · [B4.b](./specification.md#b4-b) · R4/A4. Owner role: orchestration-guidance maintainer. Dependency: the [T48](#t48--commission-related-reports-as-a-bounded-investigation) assignment and the existing retry rule. Integration owner handles A5 on the complete candidate.

#### Acceptance criteria

- **T49.a** Given a worker return with sourced observations but no confirmed cause, produce a user message that identifies inspected evidence, separates the inference and leaves the retry choice with the administrator after reconciliation. Inspect the returned artifact and actual message or single-agent equivalent. <a id="t49-a"></a>
- **T49.b** Use the same rubric on a supplied wrong return that claims an uninspected read, a confirmed common cause, or an automatic retry. Each material contradiction must prevent acceptance and name the unsupported claim or changed permission. The same rubric must accept a source-supported alternative phrasing. <a id="t49-b"></a>

#### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [evals/agent_guidance_cases.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/agent_guidance_cases.json) · [evals/behavior_rubric.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/behavior_rubric.json)

#### Additional context

The commit ships a usable return example and its assessment together. Use the [shared A4/A5 assignment](./implementation-plan.md#integrated-acceptance-on-codex-and-claude-code) on the first eligible host to close T49. On the same candidate, carry that result into A5 and collect only the remaining host evidence. If another task subsequently changes the assignment’s inputs or execution path, reassess that binding. Keep the wrong-return comparison local. Reuse the same host output if it covers both B4 criteria; do not launch a second investigation for a different heading.

</details>

## B5 · Keep checked authoring available across the writer rename

**Demonstrate the story.** Validate a document with the renamed dependency, resolve its legacy identity and reject an unrelated explicit selection. [Story criteria](./specification.md#b5--keep-checked-authoring-available-across-the-writer-rename)

- [ ] T009 [US5] Resolve Spec Writer and its legacy identity. `scripts/runtime/technical_writer.py`. [T50 · T50.1, T50.2](#t50--resolve-spec-writer-and-its-legacy-identity) Use a staged writer after binding the Builder baseline. The live rename follows acceptance of this Issue and of Builder.

### T50 · Resolve Spec Writer and its legacy identity

<details>
<summary>Scope, acceptance criteria and evidence</summary>

#### Description

The resolver searches standard folders under `technical-writer` and rejects any frontmatter name other than `technical-writer`, including when the user supplies an explicit path. Renaming the writer alone would break checked document delivery.

#### Expected outcome

A Builder installation can author and validate a document with either supported package identity.

#### Scope

Accept both `spec-writer` and the legacy `technical-writer` as supported dependency identities. Preserve explicit path precedence, existing request and environment keys, validation of required files and source snapshot integrity.

#### Specification

Parent: [B5](./specification.md#b5--keep-checked-authoring-available-across-the-writer-rename). Supports [B5.a](./specification.md#b5-a) and R5/A6. Owner role: dependency maintainer. Ship on the Builder handoff before the writer changes its public identity. Use a staged copy of the real writer with the new metadata to avoid a circular release dependency.

#### Acceptance criteria

- **T50.1** Given a complete canonical candidate in a supported discovery location and a legacy candidate at an explicit path, use the real resolver. Default selection locates the canonical candidate, the explicit path wins, and the normal validation flow returns a document-bound result for the canonical candidate. Preserve the legacy request key and environment setting. <a id="t50-1"></a>
- **T50.2** Give an explicit unrelated frontmatter identity or missing required validator. Reject the selected package without fallback. Reuse the existing snapshot-change failure where applicable. Record selected paths, versions, document receipt and refusal; a resolver-only pass cannot establish document delivery. <a id="t50-2"></a>

#### Relevant files

scripts/runtime/technical_writer.py, references/technical_writer.md and the affected dependency examples. [Dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)

#### Additional context

One commit ships compatible discovery, checks and guidance. Record the candidate, evidence and criterion verdicts. W46 supplies final renamed-release readback. No repeated host matrix for a shared resolver.

</details>

## Finish the delivery

Use A5 for the integrated planning handoff on the named hosts and A6 for dependency compatibility. Supply the accepted Builder commit to the writer implementer. A completed list alone cannot establish either result. [Coverage and shared Definition of Done](./implementation-plan.md#requirement-coverage)
