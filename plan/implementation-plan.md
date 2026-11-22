# Skill Builder implementation plan

Status: Scope approved for implementation on the handoff computer. Revision 5. Each audit finding is one epic in the Technical Writer User Story (US) format. Each child task uses its Issue template. The five epics and nine tasks live in this plan. [Story template](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/references/user_story.md) · [Task template](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/references/issue.md)

## Goal and specification

Deliver a local Skill Builder revision that commissions bounded work and verifies it against the owner’s requirements. The [behavioral specification, revision 4](./specification.md) owns R1–R5 and A1–A6. The [audit](./audit.md) owns B1–B5 and their supporting evidence. Start from Skill Builder commit `222b356fd5ac7a2df9fd9621e3744db883ecede0` or reconcile material changes since that baseline. The approved scope, candidate, Technical Writer dependency and allowed paths must be captured before implementation. Technical Writer’s own implementation is a separate delivery.

## Current context and approach

**One task is one usable increment.** Ship through the supported interface named in its expected outcome. Keep the change, affected consumers, guidance and closest regression in the same independently reviewable commit. Every commit must work with the previous supported inputs. A maintainer can stop after it and still use what was delivered.

**Find the problem before widening the change.** At task entry, use the named counterexample against the affected interface. Reuse an audit control if its inputs and boundary still match. If the expected failure is already fixed, inspect the current output against the criterion and record the existing evidence. Otherwise make the smallest correction and retry at the first failing boundary. A fresh run requires a failed criterion, changed input or missing observation. An unexpected contract or authority change goes back to the owner before dependent work proceeds.

**Close the increment immediately.** Review the actual diff and evidence. Run the applicable impacted checks with the repository’s `scripts/run_tests.py --execute` route. Record each criterion’s verdict, commit or identified working candidate, evidence location and reviewer in its existing task. Under implementation authority, commit and hand off the accepted increment before expanding it. A failed check stays in history. Local commit, local package application and publication are separate actions. The shared Definition of Done and integrated release check appear below.

The owner approved the work order, scope and local integration authority. Start with the execution prompt in the repository’s [execution guide](./README.md). Use this plan for dependencies, task boundaries, required evidence and closure. Keep the private JSON execution log described in the starting prompt. Reuse native run records and document the reason for each extra verification before it runs.

## Work sequence

Open the [task list](./tasks.md) to select work. Follow its row to the existing Issue below and use that Issue’s scope, criterion IDs and proof. The [handoff test specification](./test.md) exercises this same route on the actual packet. Use the B1–B5 outcomes below as the stories. Their Issues are already scoped, so an extra story layer would duplicate the plan.

B5 can use a staged candidate after the initial Builder baseline is bound. The new identity becomes live on the other computer only after T50 is accepted. The real renamed release is a consumer check in writer W46.

Start with B1 and use its accepted assignment format for B4. B2 can proceed once the shared schema version boundary with B1 is settled. B3 has its own performer/controller interface and can proceed independently, with a coordinated edit to the shared evaluator file if needed. Within each epic, ship the first child, then extend its working result with the second. Each issue below is the unit of commit and handoff. Attach its evidence before marking it accepted. All task and epic criteria currently have the verdict **Not demonstrated**. D1 records the owner’s approval.

### B1 · Commission work that serves an approved requirement

As a skill maintainer, I want to trace each assignment to an approved outcome and each requirement to its owner, so that I can release a bounded work packet without granting extra authority.

#### Acceptance criteria

- **B1.a** Given a frozen requirement and an assignment, submit the real plan packet. A supported contribution or justified safeguard is eligible. An invented criterion is located before production and an unrelated publication instruction fails semantic review even when it cites a valid ID. Inspect the row, diagnostic and reviewer decision. T17 supplies this proof.
- **B1.b** Given an in-scope requirement with a test but no owning work, review coverage. The uncovered requirement is visible and blocks a complete-coverage claim. Assign the work and confirm the same plan can proceed. Inspect the before/after mapping and one historical plan read. T18 supplies this proof.

#### Scope and sources

Parent: this plan. Owner role: plan-contract maintainer. Finding B1, requirement R1, criterion A1. The source of authority is the frozen specification. Existing file scope and publication controls remain in force. Close the epic when the implementer can recover the allowed work and proof from the admitted packet alone. Use the same packet and review evidence from T17 and T18.

#### T17 · Admit a source-bound work assignment

##### Description

Today an unrelated publication step can sit alongside complete case coverage. The plan author and reviewer need to know exactly what the implementer may deliver.

##### Expected outcome

A maintainer can submit one bounded assignment through plan admission and hand the accepted entry to production. This commit ships both the producer and the consuming packet.

##### Scope

Cover independent work, permitted effects, governing revision, criterion or justified safeguard, owner role, prerequisites and proof. Keep ordinary substeps inline. Preserve existing versioned reads and scope enforcement.

##### Specification

Parent B1 · B1.a · R1/A1. Owner role: plan-contract maintainer. Input: the captured plan fixture and the audit’s publishing-step mutation.

##### Acceptance criteria

- **T17.a** Given the approved fixture, submit an authorized contribution, then a necessary safeguard with an explicit rationale. Each accepted entry appears in the next work packet with the same revision, scope and proof. Save the submitted and consumed rows.
- **T17.b** Replace its criterion with an unknown ID. Admission identifies the row and ID before production. Attach the real ID to the unrelated publishing instruction instead. The plan reviewer rejects its meaning. Save the diagnostic and the reviewer’s cited source. Neither case permits publication.

##### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

##### Additional context

Use this plan’s B4/T48 Issue as the supported contribution in [B-PACKET](./test.md#cases). Inspect the real admitted and consumed assignment. Keep the existing justified-safeguard, rejection and compatibility checks.

First signal: reuse the audit mutation at its documented consistency-function boundary. Close on the packet and semantic verdict at the supported interface. One fixture covers the variations. No customer data or publishing command is needed.

#### T18 · Expose a requirement that has tests but no owning work

##### Description

A complete set of cases can still leave no implementer responsible for a requirement. The plan owner needs the reverse mapping before claiming coverage.

##### Expected outcome

A maintainer reviewing a plan can locate an unowned requirement and correct its assignment in the same work record.

##### Scope

Extend the existing coverage result and its normal plan consumer. Preserve the T17 safeguard route and the historical plan reader.

##### Specification

Parent B1 · B1.b · R1/A1. Owner role: coverage maintainer. Dependency: the admitted T17 assignment representation.

##### Acceptance criteria

- **T18.a** From a valid T17 plan, remove the sole owning assignment while retaining its test. Coverage names the orphaned requirement and cannot report complete coverage. Restore that assignment and observe the resolved result. Retain the two results from the same fixture.
- **T18.b** Open one captured pre-change plan through its supported reader. Its original version and recorded meaning remain readable. Cite existing binding-compatible evidence when the reader and its inputs are unchanged.

##### Relevant files

[scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

##### Additional context

Commit the reverse-coverage result, its consumer and focused regression together. Stop after the orphan, recovery and compatibility evidence is recorded. Reuse the forward-mapping verdict from T17.

### B2 · Accept valid work in either order

As a workflow author, I want to declare which steps depend on each other, so that a correct result can pass and a premature decision can be caught.

#### Acceptance criteria

- **B2.a** Given a case requiring two independent reads before a decision, run it through the evaluator. Both read orders pass. Omission, an early decision and missing required visible evidence fail at their respective boundaries. Reversing a legacy strict sequence still fails. Inspect the verdicts from T24.
- **B2.b** Given the same relation in an authored workflow, submit the plan and use its generated evaluator. Derivation and grading agree on the prerequisites. A cyclic or unknown dependency fails admission. Inspect the generated case, its result and the two admission diagnostics from T25.

#### Scope and sources

Parent: this plan. Owner role: workflow-contract maintainer. Finding B2, R2/A2. The declaration concerns material prerequisites. Legacy workflows keep their strict sequence and all existing permission, omission and recovery obligations. Close on one connected path from authored workflow to distributed evaluator.

#### T24 · Grade independent reads in an explicitly supplied evaluation case

##### Description

The current grader rejects a correct trace solely because the example was read before the brief. A maintainer with an explicitly supplied case needs a usable evaluation path immediately.

##### Expected outcome

A case author can run an opt-in dependency-aware case through the existing evaluator’s `--suite` and `--case` entry. Existing strict cases continue to run.

##### Scope

Ship the reader for the new case form, its validation, grading, evidence and visibility checks, usage guidance and regression together. Keep normal generated plans on the existing format until T25 can emit the new one safely.

##### Specification

Parent B2 · B2.a · R2/A2. Owner role: evaluator maintainer. Input: the captured three-step failure. Settle the dependency representation with the workflow maintainer first.

##### Acceptance criteria

- **T24.a** Run the same three-step case with each valid read order. Both pass the process check. Move the decision before one read, omit a read, or withhold required evidence/visibility. Each affected variant fails for its actual missing condition. Retain the process verdict per trace.
- **T24.b** Submit a malformed relation with an unknown prerequisite or cycle. It cannot yield a passing process result. Reuse the existing reversed strict-order case to show legacy behavior. Preserve the original failed audit trace.

##### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_process_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_process_evaluation.py)

##### Additional context

One parameterised three-step fixture is sufficient. Use existing visibility/omission controls where their path and inputs remain applicable. The commit ships a directly usable evaluator feature, including its failure handling. No generated package or model run is needed to accept this task.

#### T25 · Generate checks only for declared workflow dependencies

##### Description

The plan authoring path still derives an order obligation for adjacent steps. An author needs its emitted cases to honor the same relation the evaluator can grade.

##### Expected outcome

Submitting a dependency-aware workflow now generates a usable case for the distributed evaluator. Both ends support the same rule at this commit.

##### Scope

Update authoring instructions, versioned declarations, coverage derivation and the actual generated consumer. Preserve the default for historical workflows, required branches and recovery checks.

##### Specification

Parent B2 · B2.b · R2/A2. Owner role: workflow-contract maintainer. Requires T24 and a settled schema-version boundary with T17.

##### Acceptance criteria

- **T25.a** Submit the three-step workflow. Its emitted case requires both reads before the decision and contains no invented dependency between reads. Run one previously rejected valid order using the generated evaluator. Retain the emitted relation and verdict. Reuse T24’s trace matrix when the grader is unchanged.
- **T25.b** Submit the same declaration with a cycle and then an unknown prerequisite. Plan admission identifies the offending relationship before execution. A legacy strict declaration still emits its strict order. Retain the diagnostics and original-format comparison.

##### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_workflow_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_workflow_coverage.py)

##### Additional context

First inspect the emitted relation. If correct but execution disagrees, resume at the generated evaluator, preserving the accepted admission evidence. This single connected check closes the producer/consumer gap without exercising every permutation.

### B3 · Assess an ordinary request without revealing the grader’s clues

As a skill evaluator, I want to give the performer realistic inputs while retaining case identity in the controller, so that I can attribute a result to the right case without hinting at the intended answer.

#### Acceptance criteria

- **B3.a** Export a native task with a deliberately descriptive case ID and a genuine user filename. The performer receives the task and file, while the controller retains the real case identity and rejects a mismatched result. Inspect T36’s exported view and readback.
- **B3.b** Stage the same case through the live-harness launch path. The submitted arguments, prompt, working directory and staged paths carry no grader-only clue. The controller can still resolve the candidate and a historical report. Inspect T37’s recorded launch and assessment.

#### Scope and sources

Parent: this plan. Owner role: evaluation-harness maintainer. Finding B3, R3/A3. Keep case identity and evidence provenance on the controller. This epic covers the two task-input interfaces. Its acceptance measures what the performer is given. Model performance remains a separate claim.

#### T36 · Export a neutral native task with a traceable result

##### Description

The native packet exposes a descriptive case ID and development filenames. Some contain a strong clue about the expected answer.

##### Expected outcome

A caller can export the task, supply it to a performer and associate the returned observation with its original case through the controller.

##### Scope

Change the native export and its actual controller consumer together. Preserve user-specified filenames, task resources, historical report reading and case/candidate bindings.

##### Specification

Parent B3 · B3.a · R3/A3. Owner role: native-evaluation maintainer. Input: the captured native packet and one ordinary user filename.

##### Acceptance criteria

- **T36.a** Export a case with a distinctive test label and a separate user filename. Inspect the actual performer view. It retains the ordinary request and file, and excludes the label, expected answer and grader-only inventory. Save the exported view.
- **T36.b** Submit a matching observation to the controller and then one with a stale case binding. Only the matching observation is eligible for the intended case and candidate. Save the two decisions; a match alone does not prove task success.

##### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_behavior_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_evaluation.py)

##### Additional context

Use one local export and the matching/mismatched observation pair. Stop at the controller decision. The commit can ship independently because native callers and their new result mapping are updated together.

#### T37 · Stage a neutral host workspace and recover its real case identity

##### Description

A neutral native packet does not fix the host route. The current harness inserts the descriptive case ID into paths shown to the performer.

##### Expected outcome

A maintainer can stage and launch a task through the existing harness and look up its evidence under the true case after return.

##### Scope

Cover the host-visible prompt, submitted arguments, working directory, task and dependency paths. Keep user files, historic report lookup, receipt bindings and unchanged host permission settings.

##### Specification

Parent B3 · B3.b · R3/A3. Owner role: host-harness maintainer. Reuse T36’s fixture and controller identity convention.

##### Acceptance criteria

- **T37.a** Stage that case through the actual launch builder with a local recording adapter. Inspect the final submitted inputs and staged roots. The user filename is intact and no grader-only label, answer or path inventory reaches the performer. Capture both host-specific forms where their path or argument construction differs.
- **T37.b** Resolve the captured result to the original case and candidate through the normal report consumer. Open one historical report using its recorded identity. A stale binding remains ineligible. Reuse T36’s negative evidence wherever the same unchanged reader decides it.

##### Relevant files

[tools/run_behavioral_evals.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tools/run_behavioral_evals.py) · [scripts/host_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/host_coverage.py) · [tests/test_behavior_harness.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_harness.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md)

##### Additional context

Ship the harness, changed reader and path-compatibility regression together. A recorded launch settles this input question. Spend a live host run only for the separately specified A5 behavior.

### B4 · Keep related observations and decision authority through a handoff

As a investigation lead, I want to commission related reports together when they share a criterion and explain what the evidence supports, so that the owner can act without losing uncertainty or retry authority.

#### Acceptance criteria

- **B4.a** Given two reports consistent with a lost response, commission the investigation. Both source observations, the shared criterion and the owner’s retry boundary survive in one assignment or a justified split with independent outputs or an integration owner. Inspect the assignment against the supplied passages.
- **B4.b** Given the return and an unconfirmed shared cause, report the result to the user. The message distinguishes observed, inferred and unresolved facts. A fresh read precedes any offered retry, and only the administrator may choose it. Unsupported source inspection, a confirmed-cause claim without proof, or an automatic retry fails. Use one actual exchange to judge both criteria.

#### Scope and sources

Parent: this plan. Owner role: orchestration-guidance maintainer. Finding B4, R4/A4. Requires the assignment interface from B1. The single-agent equivalent is eligible. The task is to write and use the handoff guidance. Claim actual specialist execution only with observed dispatch and return.

#### T48 · Commission related reports as a bounded investigation

##### Description

The current delegation guide describes independent modules. Add an example showing how the lead decides what to do with two correlated reports before dispatch.

##### Expected outcome

A skill author can use a worked assignment from the existing guide, complete with sources, shared criterion, allowed work, recipient, return obligation and stop condition.

##### Scope

Cover the lead’s decision and outgoing assignment, including a single-owner path and a justified split. Include contrasting weak and corrected wording. Preserve current role definitions and host capabilities.

##### Specification

Parent B4 · B4.a · R4/A4. Owner role: orchestration-guidance maintainer. Requires T17’s assignment shape. Use the synthetic reports and actual WEB-09 source below.

##### Acceptance criteria

- **T48.a** Give a reader the finished assignment and its linked sources. They can recover both observations, WEB-09, allowed investigation and the required return. The cause remains open. A split must identify independent outputs or their integration owner. Retain the reviewed passage and source comparison.
- **T48.b** In the single-owner variant, the same assignment remains usable without dispatch. The worker has no authority to issue a retry. Inspect the authority and recipient fields in that same example.

##### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md)

##### Additional context

The commit ships a complete, reusable commissioning example. Review the actual writing through Technical Writer. Reuse that review for the authored example; the later A4/A5 observation establishes behavior through the installed skill.

#### T49 · Return supported conclusions and the owner’s retry decision

##### Description

A useful assignment can still end with a lead treating an unverified cause as established or presenting an optional retry as required.

##### Expected outcome

A lead can consume the T48 assignment and its returned evidence, then give the owner an accurate disposition through the existing orchestration guide.

##### Scope

Complete the return and user-facing side of the worked example. Bind one realistic shared assessment to the existing case and rubric system. Keep expected answers outside the performer’s task.

##### Specification

Parent B4 · B4.b · R4/A4. Owner role: orchestration-guidance maintainer. Dependency: the T48 assignment and the existing retry rule. Integration owner handles A5 on the complete candidate.

##### Acceptance criteria

- **T49.a** Given a worker return with sourced observations but no confirmed cause, produce a user message that identifies inspected evidence, separates the inference and leaves the retry choice with the administrator after reconciliation. Inspect the returned artifact and actual message or single-agent equivalent.
- **T49.b** Use the same rubric on a supplied wrong return that claims an uninspected read, a confirmed common cause, or an automatic retry. Each material contradiction must prevent acceptance and name the unsupported claim or changed permission. The same rubric must accept a source-supported alternative phrasing.

##### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [evals/agent_guidance_cases.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/agent_guidance_cases.json) · [evals/behavior_rubric.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/behavior_rubric.json)

##### Additional context

The commit ships a usable return example and its assessment together. Use the shared A4/A5 assignment below on the first eligible host to close T49. On the same candidate, carry that result into A5 and collect only the remaining host evidence. If another task subsequently changes the assignment’s inputs or execution path, reassess that binding. Keep the wrong-return comparison local. Reuse the same host output if it covers both B4 criteria; do not launch a second investigation for a different heading.

### B5 · Keep checked authoring available across the writer rename

As a skill maintainer, I want Builder to resolve the new and legacy writing packages, so that a name change preserves document acceptance.

#### Acceptance criteria

- **B5.a** On a complete staged writer package bearing the new name, resolve the dependency and validate a document through the real Builder validation path. A legacy package still resolves. An explicitly selected wrong identity fails without fallback; an already-bound run cannot silently accept a changed dependency.

#### Scope and sources

Parent: this implementation plan. Owner role: Builder dependency maintainer. T50 supports B5.a, R5/A6. [Dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)

#### T50 · Resolve Spec Writer and its legacy identity

##### Description

The resolver searches standard folders under `technical-writer` and rejects any frontmatter name other than `technical-writer`, including when the user supplies an explicit path. Renaming the writer alone would break checked document delivery.

##### Expected outcome

A Builder installation can author and validate a document with either supported package identity.

##### Scope

Accept both `spec-writer` and the legacy `technical-writer` as supported dependency identities. Preserve explicit path precedence, existing request and environment keys, validation of required files and source snapshot integrity.

##### Specification

Parent: B5. Supports B5.a and R5/A6. Owner role: dependency maintainer. Ship on the Builder handoff before the writer changes its public identity. Use a staged copy of the real writer with the new metadata to avoid a circular release dependency.

##### Acceptance criteria

- **T50.1** Given a complete canonical candidate in a supported discovery location and a legacy candidate at an explicit path, use the real resolver. Default selection locates the canonical candidate, the explicit path wins, and the normal validation flow returns a document-bound result for the canonical candidate. Preserve the legacy request key and environment setting.
- **T50.2** Give an explicit unrelated frontmatter identity or missing required validator. Reject the selected package without fallback. Reuse the existing snapshot-change failure where applicable. Record selected paths, versions, document receipt and refusal; a resolver-only pass cannot establish document delivery.

##### Relevant files

scripts/runtime/technical_writer.py, references/technical_writer.md and the affected dependency examples. [Dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)

##### Additional context

One commit ships compatible discovery, checks and guidance. Record the candidate, evidence and criterion verdicts. W46 supplies final renamed-release readback. No repeated host matrix for a shared resolver.

### Integrated acceptance on Codex and Claude Code

The verifier uses the actual modified Builder on the existing Technical Writer example. Give the performer the source documents, the two observations below and a natural request to plan one scoped improvement to the bulk-edit handoff. Give the reviewer the A5 rubric and the applicable A1/A4 criteria. Local A2/A3 evidence remains bound to its own interfaces. Use the literal source requirement WEB-09. Under its T16 example, loss of the second response leaves 500 confirmed IDs, 500 unresolved and one unattempted. A fresh read precedes any offered retry, and only the administrator can choose to retry. The example specifies what a future writer should document. Its application does not need to be executed. [Source requirement](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/examples/spec_driven_development.md#L118) · [T16](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/examples/test_specification.md#L55)

**Example performer request.** “Please use Skill Builder to prepare the first Technical Writer change for the maintainer. One reviewer saw the second batch stop returning a response. Another saw the completion summary lose track of which rows were still uncertain. They may be related. Use the attached bulk-edit specification and test example. Give me the work item, what would prove it, and a brief return to the owner based on the supplied evidence, including any decision that still belongs to me. Keep this to planning.”

The two observations are synthetic case inputs. They add no incident claim to the Technical Writer audit. Keep the reviewer’s answer key out of the task. For example, an acceptable lead return could say, “Both reports concern the same bulk operation. The evidence does not yet show a shared cause. The work item asks the writer to distinguish the three row states and preserve the administrator’s choice about a retry.” Accept other wording and a justified independent split that preserves the same facts and ownership.

Use the same skill, request, sources and rubric for Codex and Claude Code. Keep actual outputs, public messages, evidence of inspected sources and model/settings where exposed separately. A supplied passage can establish access without an extra tool call. Use the same assignment, return and message for B1, B4 and A5 wherever their actual content proves those criteria. This run establishes planning and handoff behavior. Any broader Builder readiness claim still requires the applicable existing host matrix and its real skill-creation pilot. Reuse qualifying evidence, and report missing cells as Not demonstrated.

## Requirement coverage

| Finding and specification | Child tasks and story criteria | Evidence that closes the epic |
| --- | --- | --- |
| B1 · R1/A1 | T17 → B1.a, T18 → B1.b | One source-bound assignment through admission and consumption, reverse coverage and historical readback. |
| B2 · R2/A2 | T24 → B2.a, T25 → B2.b | One three-step fixture from explicit case to generated workflow, with legitimate and forbidden orders distinguished. |
| B3 · R3/A3 | T36 → B3.a, T37 → B3.b | One sentinel and real filename through both performer routes, controller reconciliation and old report readback. |
| B4 · R4/A4 | T48 → B4.a, T49 → B4.b | One actual assignment, return and user message preserving both sourced reports, uncertainty and the administrator’s decision. |
| Delivery · A5 | Integration owner, with evidence from B1–B4 | One comparable planning assignment per supported host on the identified candidate, with a separate verdict and artifact per host. |
| R5 / A6 | B5 → T50 | Real document validation with the new identity, legacy selection and rejection of an unrelated explicit dependency. |

Revision 1 grouped B1/B4 under S1 and B2/B3 under S2. This revision carries the former T17.1, T24.1, T36.1 and T48.1 obligations at their respective epic boundaries. The additional child IDs divide ownership and proof. The current specification covers R1–R5 and A1–A6.

**Shared Definition of Done.** After approval use Skill Builder’s existing modify, document-validation, review and local-apply workflow. Freeze the task, permitted paths, case inputs and acceptance before production. At iteration use `scripts/run_tests.py --execute` with the affected set selected by the repository. Correct an unmapped change at its impact rule. Where verification is semantic, record the actual source passage, observed artifact, wrong result the criterion rejects, and reviewer. Preserve required independent review when the actual workflow calls for it. A written self-review cannot stand in for that review.

Before a wider run name the unmet criterion, changed dependency or failed boundary and what observation would change the decision. Use compatible evidence for unchanged behavior. A local recording adapter settles a payload question. A requested per-host behavior claim needs the corresponding host observation. Run the repository-required final suite once the implementation-completion record identifies the complete candidate. Confirm integration on the authorized local target and retain the original evidence. Further runs need a new reason.

## Rollout and recovery

Keep historical schema and report readers addressable by version. Freeze the current Builder executable and the separate Technical Writer dependency before modifying Builder itself. Run the current Builder against a distinct staged candidate so the controller and its policy do not change underneath the job. Verify the candidate through its own supported entry before local application. Preserve the prior package and recovery record. If plan readback breaks, an old report loses its identity, a missing prerequisite passes, or a case cue reaches the performer, stop at that boundary. Fix and retest only the affected path. Use Builder’s supported recovery if local application fails.

## Risks and open decisions

The approved behavior and scope carry forward into specification revision 4 and implementation plan revision 5. Implement Skill Builder first, with a distinct staged candidate and a local implementation branch. Internal file names and implementation choices are delegated within the approved scope. A missing host observation remains Not demonstrated.

At closure record each task criterion, story criterion and A1–A6 as Met, Failed or Not demonstrated with its candidate and evidence in the existing work item. Preserve earlier failures. Close each finding’s epic on its story-level evidence and the delivery on A5 and A6. A parent rollup of closed tasks cannot establish either verdict. Deliver the locally applied Builder revision to the owner. Any subsequent Technical Writer implementation starts with its separately approved specification and implementation plan. [Technical Writer implementation plan](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/implementation-plan.md)

## Pending owner decisions

None at handoff. Append out-of-scope discoveries here with their source, observed effect, proposed change, impact of deferral and any task actually blocked. Only an explicit owner decision can add them to implementation scope.
