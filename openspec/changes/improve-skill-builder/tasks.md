# Skill Builder implementation tasks

The numbered checkboxes are the apply list for this change. Follow each row to its existing Issue for detailed acceptance and proof. The local T number preserves earlier references. [Behavioral baseline](./specs/skill-assignments/spec.md) · [Delivery design](./design.md)

Start with B1/T17 on the bound Builder baseline. T36 can run alongside it on the separate performer interface. T50 can use a staged writer as soon as the baseline is bound. The first usable result is a bounded assignment that reaches the next work packet. An accepted Builder with B5/T50 is the input to the writer handoff.

Start only when the listed inputs, authority and dependencies are settled. During authorized implementation, record the criterion verdicts, candidate and evidence in the owning Issue before marking its row complete. A writing-only request ends with the documents. [Read-only handoff test](../../../plan/test.md)
<a id="b1--commission-work-that-serves-an-approved-requirement"></a>

## 1. B1 · Commission work that serves an approved requirement

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./specs/skill-assignments/spec.md#b1--commission-work-that-serves-an-approved-requirement)

- [x] 1.1 [T17](#t17--admit-a-source-bound-work-assignment) (T001). Admit the sourced work and justified safeguard into the next packet. Reject an unknown criterion and a valid ID attached to unrelated publishing. May start in parallel. Start here after binding the baseline.

### T17 · Admit a source-bound work assignment

#### Description

Today an unrelated publication step can sit alongside complete case coverage. The plan author and reviewer need to know exactly what the implementer may deliver.

#### Expected outcome

A maintainer can submit one bounded assignment through plan admission and hand the accepted entry to production. This commit ships both the producer and the consuming packet.

#### Scope

Cover independent work, permitted effects, governing revision, criterion or justified safeguard, owner role, prerequisites and proof. Keep ordinary substeps inline. Preserve existing versioned reads and scope enforcement.

#### Specification

Parent [B1](./specs/skill-assignments/spec.md#b1--commission-work-that-serves-an-approved-requirement) · [B1.a](./specs/skill-assignments/spec.md#b1-a) · R1/A1. Owner role: plan-contract maintainer. Input: the captured plan fixture and the audit’s publishing-step mutation.

#### Acceptance criteria

- **T17.a** Given the approved fixture, submit an authorized contribution, then a necessary safeguard with an explicit rationale. Each accepted entry appears in the next work packet with the same revision, scope and proof. Save the submitted and consumed rows. <a id="t17-a"></a>
- **T17.b** Replace its criterion with an unknown ID. Admission identifies the row and ID before production. Attach the real ID to the unrelated publishing instruction instead. The plan reviewer rejects its meaning. Save the diagnostic and the reviewer’s cited source. Neither case permits publication. <a id="t17-b"></a>

#### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

#### Additional context

Use this handoff’s B4/T48 Issue as the supported contribution in [B-PACKET](../../../plan/test.md#cases). Inspect the real admitted and consumed assignment. Keep the existing justified-safeguard, rejection and compatibility checks.

First signal: reuse the audit mutation at its documented consistency-function boundary. Close on the packet and semantic verdict at the supported interface. One fixture covers the variations. No customer data or publishing command is needed.

#### Verdicts

Candidate: the commit that adds plan protocol 7 on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the observed packet and diagnostics with this Issue and [B1.a](./specs/skill-assignments/spec.md#b1-a).

- **T17.a Met.** The real admission route accepted a criterion-bound entry and a safeguard with its rationale. The produce packet's `assignments.entries` equals the submitted rows, with the same `governing_revision`, permitted effects and proof. Regression: `AssignmentAdmissionTests.test_t17a_admitted_contribution_and_safeguard_reach_the_next_work_packet`.
- **T17.b Met.** An unknown ID stops admission and names the entry, row and ID. A real ID attached to the publishing instruction stops on the reviewer's rejection and repeats its cited source. The run stays at `plan`, and the packet states that admission grants no publication. Regression: `AssignmentAdmissionTests.test_t17b_unknown_criterion_and_unrelated_publication_stop_before_production`.
- **B-PACKET Met.** The admitted and consumed T48 entry identifies T48, B4.a, its T17 prerequisite and the administrator's retry boundary. The investigation was not executed. The private run log holds the submitted and consumed rows and both diagnostics.

<a id="b3--assess-an-ordinary-request-without-revealing-the-graders-clues"></a>

## 2. B3 · Assess an ordinary request without revealing the grader’s clues

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./specs/skill-assignments/spec.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [x] 2.1 [T36](#t36--export-a-neutral-native-task-with-a-traceable-result) (T002). Inspect the native performer view for the ordinary filename and absence of grader clues. Only a matching case/candidate observation is eligible. May start in parallel. Can start alongside T17 on the native evaluator. Coordinate edits with T24 if both would change the same evaluator.

### T36 · Export a neutral native task with a traceable result

#### Description

The native packet exposes a descriptive case ID and development filenames. Some contain a strong clue about the expected answer.

#### Expected outcome

A caller can export the task, supply it to a performer and associate the returned observation with its original case through the controller.

#### Scope

Change the native export and its actual controller consumer together. Preserve user-specified filenames, task resources, historical report reading and case/candidate bindings.

#### Specification

Parent [B3](./specs/skill-assignments/spec.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues) · [B3.a](./specs/skill-assignments/spec.md#b3-a) · R3/A3. Owner role: native-evaluation maintainer. Input: the captured native packet and one ordinary user filename.

#### Acceptance criteria

- **T36.a** Export a case with a distinctive test label and a separate user filename. Inspect the actual performer view. It retains the ordinary request and file, and excludes the label, expected answer and grader-only inventory. Save the exported view. <a id="t36-a"></a>
- **T36.b** Submit a matching observation to the controller and then one with a stale case binding. Only the matching observation is eligible for the intended case and candidate. Save the two decisions; a match alone does not prove task success. <a id="t36-b"></a>

#### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_behavior_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_evaluation.py)

#### Additional context

Use one local export and the matching/mismatched observation pair. Stop at the controller decision. The commit can ship independently because native callers and their new result mapping are updated together.

#### Verdicts

Candidate: the T36 commit on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the exported view and controller decisions with this Issue and [B3.a](./specs/skill-assignments/spec.md#b3-a).

- **T36.a Met.** `evaluate.py --behavior-packet builder-no-mechanical-only-claim --binding NEW_FILE` returned a view with only `task_id`, `request`, `skill`, `resources`, `role` and `instructions`. The request and `quarterly-notes.md` are intact. The descriptive case ID, expected answer, `evals/cases.json` inventory and package hashes are absent; they appear only in the controller binding. Regression: `NeutralExportTests.test_t36a_performer_view_keeps_request_and_file_without_grader_material`.
- **T36.b Met.** An observation whose `task_id` resolves through the current binding is eligible and is graded against the case. Its hidden expected text was still missing, so a match alone did not pass the task. A binding from an earlier case version is rejected as stale. Regression: `NeutralExportTests.test_t36b_only_the_matching_binding_is_eligible`. Legacy `case_id` and `case_sha256` records remain readable under the existing tests.

<a id="b1--commission-work-that-serves-an-approved-requirement-continued"></a>

## 3. B1 · Commission work that serves an approved requirement (continued)

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./specs/skill-assignments/spec.md#b1--commission-work-that-serves-an-approved-requirement)

- [x] 3.1 [T18](#t18--expose-a-requirement-that-has-tests-but-no-owning-work) (T003). Remove the only owning assignment and identify the orphan despite its test. Restore coverage and read the historical plan with its original meaning. After T17 supplies the admitted assignment.

### T18 · Expose a requirement that has tests but no owning work

#### Description

A complete set of cases can still leave no implementer responsible for a requirement. The plan owner needs the reverse mapping before claiming coverage.

#### Expected outcome

A maintainer reviewing a plan can locate an unowned requirement and correct its assignment in the same work record.

#### Scope

Extend the existing coverage result and its normal plan consumer. Preserve the T17 safeguard route and the historical plan reader.

#### Specification

Parent [B1](./specs/skill-assignments/spec.md#b1--commission-work-that-serves-an-approved-requirement) · [B1.b](./specs/skill-assignments/spec.md#b1-b) · R1/A1. Owner role: coverage maintainer. Dependency: the admitted [T17](#t17--admit-a-source-bound-work-assignment) assignment representation.

#### Acceptance criteria

- **T18.a** From a valid T17 plan, remove the sole owning assignment while retaining its test. Coverage names the orphaned requirement and cannot report complete coverage. Restore that assignment and observe the resolved result. Retain the two results from the same fixture. <a id="t18-a"></a>
- **T18.b** Open one captured pre-change plan through its supported reader. Its original version and recorded meaning remain readable. Cite existing binding-compatible evidence when the reader and its inputs are unchanged. <a id="t18-b"></a>

#### Relevant files

[scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [scripts/runtime/workflow.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/workflow.py) · [tests/test_plan_consistency.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_plan_consistency.py)

#### Additional context

Commit the reverse-coverage result, its consumer and focused regression together. Stop after the orphan, recovery and compatibility evidence is recorded. Reuse the forward-mapping verdict from T17.

#### Verdicts

Candidate: the T18 commit on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the coverage results with this Issue and [B1.b](./specs/skill-assignments/spec.md#b1-b). The forward mapping reuses the T17 verdict.

- **T18.a Met.** Removing W3, the sole owner of R-3, left its `malformed` and `numeric` cases in place. Admission reported that R-3 has tests but no owning assignment and kept the run at `plan`. Restoring W3 in the same run admitted the plan, and the produce packet's `assignments.coverage` maps every requirement to an owner. Regression: `ReverseCoverageTests.test_t18a_orphaned_requirement_is_named_and_the_same_plan_recovers`.
- **T18.b Met.** A plan captured under protocol 6 is read with its original version and contract: no assignments are required, its stored plan is unchanged, and its packets carry no assignment coverage. Regression: `ReverseCoverageTests.test_t18b_captured_protocol_6_plan_keeps_its_original_meaning`. The existing protocol-6 replay check in `test_completion.py` still rebuilds the recorded candidate.

<a id="b2--accept-valid-work-in-either-order"></a>

## 4. B2 · Accept valid work in either order

**Demonstrate the story.** Accept both valid read orders and locate a premature decision or missing prerequisite. [Story criteria](./specs/skill-assignments/spec.md#b2--accept-valid-work-in-either-order)

- [x] 4.1 [T24](#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case) (T004). Grade both valid read orders successfully. Reject a premature decision, missing read or malformed relation for its actual violated condition. Start once the dependency representation and its version boundary with B1 are settled. Coordinate evaluator edits with T36.

### T24 · Grade independent reads in an explicitly supplied evaluation case

#### Description

The current grader rejects a correct trace solely because the example was read before the brief. A maintainer with an explicitly supplied case needs a usable evaluation path immediately.

#### Expected outcome

A case author can run an opt-in dependency-aware case through the existing evaluator’s `--suite` and `--case` entry. Existing strict cases continue to run.

#### Scope

Ship the reader for the new case form, its validation, grading, evidence and visibility checks, usage guidance and regression together. Keep normal generated plans on the existing format until T25 can emit the new one safely.

#### Specification

Parent [B2](./specs/skill-assignments/spec.md#b2--accept-valid-work-in-either-order) · [B2.a](./specs/skill-assignments/spec.md#b2-a) · R2/A2. Owner role: evaluator maintainer. Input: the captured three-step failure. Settle the dependency representation with the workflow maintainer first.

#### Acceptance criteria

- **T24.a** Run the same three-step case with each valid read order. Both pass the process check. Move the decision before one read, omit a read, or withhold required evidence/visibility. Each affected variant fails for its actual missing condition. Retain the process verdict per trace. <a id="t24-a"></a>
- **T24.b** Submit a malformed relation with an unknown prerequisite or cycle. It cannot yield a passing process result. Reuse the existing reversed strict-order case to show legacy behavior. Preserve the original failed audit trace. <a id="t24-b"></a>

#### Relevant files

[scripts/evaluate.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/evaluate.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md) · [tests/test_process_evaluation.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_process_evaluation.py)

#### Additional context

One parameterised three-step fixture is sufficient. Use existing visibility/omission controls where their path and inputs remain applicable. The commit ships a directly usable evaluator feature, including its failure handling. No generated package or model run is needed to accept this task.

#### Verdicts

Candidate: the T24 commit on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the per-trace verdicts from `evaluate.py --suite --case` with this Issue and [B2.a](./specs/skill-assignments/spec.md#b2-a). The dependency representation is the opt-in `expect.process.requires` map. It stays outside the protocol-7 plan schema settled in T17 until T25 emits it.

- **T24.a Met.** With `requires: {decide: [read_brief, read_example]}`, both read orders passed. A decision before `read_example` failed as premature, an omitted read failed as omitted, a hidden decision failed its visibility check and a blank read reference failed its evidence check. Each failure names only its own missing condition, apart from the omitted read, which also leaves the decision premature. Regression: `DependencyAwareProcessTests.test_t24a_both_read_orders_pass_and_each_violation_fails_for_its_condition`.
- **T24.b Met.** An unknown prerequisite and a cycle each fail an otherwise valid trace. The legacy strict case without `requires` still fails the audit's reversed-read trace, which keeps the original failure. Regression: `DependencyAwareProcessTests.test_t24b_malformed_relation_cannot_pass_and_legacy_strict_order_still_fails`.

- [x] 4.2 [T25](#t25--generate-checks-only-for-declared-workflow-dependencies) (T005). Generate a case requiring both reads before the decision in either order. Reject an unknown prerequisite or cycle and preserve legacy strict ordering. After T24, with T17’s schema-version boundary settled.

### T25 · Generate checks only for declared workflow dependencies

#### Description

The plan authoring path still derives an order obligation for adjacent steps. An author needs its emitted cases to honor the same relation the evaluator can grade.

#### Expected outcome

Submitting a dependency-aware workflow now generates a usable case for the distributed evaluator. Both ends support the same rule at this commit.

#### Scope

Update authoring instructions, versioned declarations, coverage derivation and the actual generated consumer. Preserve the default for historical workflows, required branches and recovery checks.

#### Specification

Parent [B2](./specs/skill-assignments/spec.md#b2--accept-valid-work-in-either-order) · [B2.b](./specs/skill-assignments/spec.md#b2-b) · R2/A2. Owner role: workflow-contract maintainer. Requires [T24](#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case) and a settled schema-version boundary with [T17](#t17--admit-a-source-bound-work-assignment).

#### Acceptance criteria

- **T25.a** Submit the three-step workflow. Its emitted case requires both reads before the decision and contains no invented dependency between reads. Run one previously rejected valid order using the generated evaluator. Retain the emitted relation and verdict. Reuse T24’s trace matrix when the grader is unchanged. <a id="t25-a"></a>
- **T25.b** Submit the same declaration with a cycle and then an unknown prerequisite. Plan admission identifies the offending relationship before execution. A legacy strict declaration still emits its strict order. Retain the diagnostics and original-format comparison. <a id="t25-b"></a>

#### Relevant files

[scripts/runtime/contracts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/contracts.py) · [scripts/runtime/artifacts.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/runtime/artifacts.py) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md) · [tests/test_workflow_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_workflow_coverage.py)

#### Additional context

First inspect the emitted relation. If correct but execution disagrees, resume at the generated evaluator, preserving the accepted admission evidence. This single connected check closes the producer/consumer gap without exercising every permutation.

#### Verdicts

Candidate: the T25 commit on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the emitted relation and generated-evaluator result with this Issue and [B2.b](./specs/skill-assignments/spec.md#b2-b). The declaration uses protocol 7, the version boundary T17 introduced.

- **T25.a Met.** The three-step workflow with `requires: {decide: [read_brief, read_example]}` derived omission tests for each step and order tests only for `read_brief->decide` and `read_example->decide`, with no order between the reads. The generated package's `evals/cases.json` carries the same `requires`. Its own `scripts/evaluate.py` graded the previously rejected order `read_example, read_brief, decide` as passing. T24's trace matrix still covers the other variants because the grader is unchanged. Regression: `DeclaredDependencyGenerationTests.test_t25a_emitted_case_requires_both_reads_and_the_generated_evaluator_accepts_either_order`.
- **T25.b Met.** A cycle and an unknown prerequisite each stop the specification before planning or execution, and each names the offending relation. A declaration without `requires` still derives the adjacent `read_brief->read_example` order test, and protocol 6 rejects the new field. Regression: `DeclaredDependencyGenerationTests.test_t25b_invalid_relations_stop_at_admission_and_legacy_declarations_stay_strict`.

<a id="b3--assess-an-ordinary-request-without-revealing-the-graders-clues-continued"></a>

## 5. B3 · Assess an ordinary request without revealing the grader’s clues (continued)

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./specs/skill-assignments/spec.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [x] 5.1 [T37](#t37--stage-a-neutral-host-workspace-and-recover-its-real-case-identity) (T006). Inspect each host’s final staged arguments for grader clues. Bind a real captured result to the original case and reject a stale binding. After T36 supplies the fixture and controller identity.

### T37 · Stage a neutral host workspace and recover its real case identity

#### Description

A neutral native packet does not fix the host route. The current harness inserts the descriptive case ID into paths shown to the performer.

#### Expected outcome

A maintainer can stage and launch a task through the existing harness and look up its evidence under the true case after return.

#### Scope

Cover the host-visible prompt, submitted arguments, working directory, task and dependency paths. Keep user files, historic report lookup, receipt bindings and unchanged host permission settings.

#### Specification

Parent [B3](./specs/skill-assignments/spec.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues) · [B3.b](./specs/skill-assignments/spec.md#b3-b) · R3/A3. Owner role: host-harness maintainer. Reuse [T36](#t36--export-a-neutral-native-task-with-a-traceable-result)’s fixture and controller identity convention.

#### Acceptance criteria

- **T37.a** Stage that case through the actual launch builder with a local recording adapter. Inspect the final submitted inputs and staged roots. The user filename is intact and no grader-only label, answer or path inventory reaches the performer. Capture both host-specific forms where their path or argument construction differs. <a id="t37-a"></a>
- **T37.b** Resolve the captured result to the original case and candidate through the normal report consumer. Open one historical report using its recorded identity. A stale binding remains ineligible. Reuse T36’s negative evidence wherever the same unchanged reader decides it. <a id="t37-b"></a>

#### Relevant files

[tools/run_behavioral_evals.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tools/run_behavioral_evals.py) · [scripts/host_coverage.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/scripts/host_coverage.py) · [tests/test_behavior_harness.py](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/tests/test_behavior_harness.py) · [references/evaluation.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/evaluation.md)

#### Additional context

Ship the harness, changed reader and path-compatibility regression together. A recorded launch settles this input question. Spend a live host run only for the separately specified A5 behavior.

#### Verdicts

Candidate: the T37 commit on `implementation/improve-skill-builder`. Reviewer: implementing agent, comparing the recorded launch inputs and report decisions with this Issue and [B3.b](./specs/skill-assignments/spec.md#b3-b). The neutral `task_id` reuses T36's controller convention.

- **T37.a Met.** A local recording adapter captured the final arguments, prompt, working directory and staged tree for Codex and Claude Code. Their path and argument construction differ: Codex receives `--cd` and `--output-last-message`. Each attempt folder is `001-task-…`, the prompt names `quarterly-notes.md`, and neither host form contains `builder-no-mechanical-only-claim`, the grader-only answer or `evals/cases.json`. Regression: `NeutralLaunchTests.test_t37a_each_host_receives_the_user_file_without_grader_clues`.
- **T37.b Met.** `host_coverage.py assess` resolved the new Codex report to the original case and candidate, and the report captured with the earlier `001-builder-no-mechanical-only-claim` folder still opened through its recorded attempt ID. A report row bound to an earlier version of the case was rejected. Regression: `NeutralLaunchTests.test_t37b_report_consumer_resolves_new_and_historical_identities_and_rejects_stale_bindings`. T36 covers native-route stale bindings.

<a id="b4--keep-related-observations-and-decision-authority-through-a-handoff"></a>

## 6. B4 · Keep related observations and decision authority through a handoff

**Demonstrate the story.** Follow the two sourced observations from assignment to return while the retry decision stays with its owner. [Story criteria](./specs/skill-assignments/spec.md#b4--keep-related-observations-and-decision-authority-through-a-handoff)

- [ ] 6.1 [T48](#t48--commission-related-reports-as-a-bounded-investigation) (T007). Commission the two observed reports under WEB-09 without declaring a common cause. Recover the bounded investigation and preserve the owner’s retry authority. After T17 supplies the accepted assignment shape.

### T48 · Commission related reports as a bounded investigation

#### Description

The current delegation guide describes independent modules. Add an example showing how the lead decides what to do with two correlated reports before dispatch.

#### Expected outcome

A skill author can use a worked assignment from the existing guide, complete with sources, shared criterion, allowed work, recipient, return obligation and stop condition.

#### Scope

Cover the lead’s decision and outgoing assignment, including a single-owner path and a justified split. Include contrasting weak and corrected wording. Preserve current role definitions and host capabilities.

#### Specification

Parent [B4](./specs/skill-assignments/spec.md#b4--keep-related-observations-and-decision-authority-through-a-handoff) · [B4.a](./specs/skill-assignments/spec.md#b4-a) · R4/A4. Owner role: orchestration-guidance maintainer. Requires [T17](#t17--admit-a-source-bound-work-assignment)’s assignment shape. Use the synthetic reports and actual WEB-09 source in the [integrated assignment](./design.md#integrated-acceptance-on-codex-and-claude-code).

#### Acceptance criteria

- **T48.a** Give a reader the finished assignment and its linked sources. They can recover both observations, WEB-09, allowed investigation and the required return. The cause remains open. A split must identify independent outputs or their integration owner. Retain the reviewed passage and source comparison. <a id="t48-a"></a>
- **T48.b** In the single-owner variant, the same assignment remains usable without dispatch. The worker has no authority to issue a retry. Inspect the authority and recipient fields in that same example. <a id="t48-b"></a>

#### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [references/authoring.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/authoring.md)

#### Additional context

The commit ships a complete, reusable commissioning example. Review the actual writing through Technical Writer. Reuse that review for the authored example; the later A4/A5 observation establishes behavior through the installed skill.

- [ ] 6.2 [T49](#t49--return-supported-conclusions-and-the-owners-retry-decision) (T008). Report the supported observations and open cause. A claimed read, common cause or automatic retry without its evidence must fail the rubric. After T48 supplies the assignment.

### T49 · Return supported conclusions and the owner’s retry decision

#### Description

A useful assignment can still end with a lead treating an unverified cause as established or presenting an optional retry as required.

#### Expected outcome

A lead can consume the T48 assignment and its returned evidence, then give the owner an accurate disposition through the existing orchestration guide.

#### Scope

Complete the return and user-facing side of the worked example. Bind one realistic shared assessment to the existing case and rubric system. Keep expected answers outside the performer’s task.

#### Specification

Parent [B4](./specs/skill-assignments/spec.md#b4--keep-related-observations-and-decision-authority-through-a-handoff) · [B4.b](./specs/skill-assignments/spec.md#b4-b) · R4/A4. Owner role: orchestration-guidance maintainer. Dependency: the [T48](#t48--commission-related-reports-as-a-bounded-investigation) assignment and the existing retry rule. Integration owner handles A5 on the complete candidate.

#### Acceptance criteria

- **T49.a** Given a worker return with sourced observations but no confirmed cause, produce a user message that identifies inspected evidence, separates the inference and leaves the retry choice with the administrator after reconciliation. Inspect the returned artifact and actual message or single-agent equivalent. <a id="t49-a"></a>
- **T49.b** Use the same rubric on a supplied wrong return that claims an uninspected read, a confirmed common cause, or an automatic retry. Each material contradiction must prevent acceptance and name the unsupported claim or changed permission. The same rubric must accept a source-supported alternative phrasing. <a id="t49-b"></a>

#### Relevant files

[references/agents_and_skills.md](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/references/agents_and_skills.md) · [evals/agent_guidance_cases.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/agent_guidance_cases.json) · [evals/behavior_rubric.json](https://github.com/fatonsopa/ai-skill-builder/blob/222b356fd5ac7a2df9fd9621e3744db883ecede0/evals/behavior_rubric.json)

#### Additional context

The commit ships a usable return example and its assessment together. Use the [shared A4/A5 assignment](./design.md#integrated-acceptance-on-codex-and-claude-code) on the first eligible host to close T49. On the same candidate, carry that result into A5 and collect only the remaining host evidence. If another task subsequently changes the assignment’s inputs or execution path, reassess that binding. Keep the wrong-return comparison local. Reuse the same host output if it covers both B4 criteria; do not launch a second investigation for a different heading.

<a id="b5--keep-checked-authoring-available-across-the-writer-rename"></a>

## 7. B5 · Keep checked authoring available across the writer rename

**Demonstrate the story.** Validate a document with the renamed dependency, resolve its legacy identity and reject an unrelated explicit selection. [Story criteria](./specs/skill-assignments/spec.md#b5--keep-checked-authoring-available-across-the-writer-rename)

- [x] 7.1 [T50](#t50--resolve-specdev-and-its-legacy-identity) (T009). Resolve the staged canonical writer and validate an actual document. Preserve explicit legacy-path precedence and reject an unrelated identity without fallback. Use a staged writer after binding the Builder baseline. The live rename follows acceptance of this Issue and of Builder.

<a id="t50--resolve-spec-writer-and-its-legacy-identity"></a>

### T50 · Resolve SpecDev and its legacy identity

#### Description

The resolver searches standard folders under `technical-writer` and rejects any frontmatter name other than `technical-writer`, including when the user supplies an explicit path. Renaming the writer alone would break checked document delivery.

#### Expected outcome

A Builder installation can author and validate a document with either supported package identity.

#### Scope

Accept both `specdev` and the legacy `technical-writer` as supported dependency identities. Preserve explicit path precedence, existing request and environment keys, validation of required files and source snapshot integrity.

#### Specification

Parent: [B5](./specs/skill-assignments/spec.md#b5--keep-checked-authoring-available-across-the-writer-rename). Supports [B5.a](./specs/skill-assignments/spec.md#b5-a) and R5/A6. Owner role: dependency maintainer. Ship on the Builder handoff before the writer changes its public identity. Use a staged copy of the real writer with the new metadata to avoid a circular release dependency.

#### Acceptance criteria

- **T50.1** Given a complete canonical candidate in a supported discovery location and a legacy candidate at an explicit path, use the real resolver. Default selection locates the canonical candidate, the explicit path wins, and the normal validation flow returns a document-bound result for the canonical candidate. Preserve the legacy request key and environment setting. <a id="t50-1"></a>
- **T50.2** Give an explicit unrelated frontmatter identity or missing required validator. Reject the selected package without fallback. Reuse the existing snapshot-change failure where applicable. Record selected paths, versions, document receipt and refusal; a resolver-only pass cannot establish document delivery. <a id="t50-2"></a>

#### Relevant files

scripts/runtime/technical_writer.py, references/technical_writer.md and the affected dependency examples. [Dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)

#### Additional context

One commit ships compatible discovery, checks and guidance. Record the candidate, evidence and criterion verdicts. W46 supplies final renamed-release readback. No repeated host matrix for a shared resolver.

#### Verdicts

Candidate: the T50 commit on `implementation/improve-skill-builder`, staged as a working copy beside a staged writer. The staged writer is Technical Writer `4a8e7c92e20404f05e68708c1a3ea26c6961b178` with its frontmatter name changed to `specdev`. The legacy candidate is the unmodified checkout of that revision. Reviewer: implementing agent, comparing the resolver, receipt and refusals with this Issue and [B5.a](./specs/skill-assignments/spec.md#b5-a).

- **T50.1 Met.** With the staged `specdev` beside the staged Builder and the legacy writer still installed under `~/.agents/skills/technical-writer`, default selection bound `specdev`. An explicit path to the legacy checkout, through the `technical_writer` request key or `SKILL_BUILDER_TECHNICAL_WRITER`, selected `technical-writer`. A completed `specify` run bound to `specdev` validated `explanation.md` through the writer's own prepare, check, review and finalize steps and Builder's `validate-documents`. The receipt and accepted copy both carry SHA-256 `9b0a0da5…65b8d4`, and the planning document gate passed. Regression: `WriterIdentityTests.test_t50_default_prefers_canonical_and_explicit_legacy_path_wins`.
- **T50.2 Met.** `start` with an explicit writer named `notes-writer` failed and named the identity and path; no fallback was attempted. An explicit `specdev` without `scripts/validate_document.py` failed as incomplete. Changing the bound writer after capture made the document gate fail with the existing snapshot error, and restoring it passed again. Regression: `WriterIdentityTests.test_t50_explicit_unrelated_identity_or_missing_validator_is_rejected_without_fallback`; snapshot: the existing `test_dependency_change_or_disappearance_blocks_delivery`.

## 8. B6 · Install the release and connect a host

A developer can install the release on a second computer, reach the skill from a selected host, and maintain it without disturbing an existing project. [Story acceptance](specs/skill-assignments/spec.md#install-the-release-and-connect-a-host)

- [ ] 8.1 [T51](#t51-issue) (T010). Install the GitHub release and connect the chosen host. After T50 and its staged writer or supported legacy installation.

<a id="t51-issue"></a>

### T51 · Install the GitHub release and connect the chosen host

#### Description

A user can acquire Skill Builder without cloning, check its version, select a host and use the skill. Reuse the existing source installer for the packaged resources. Ship the candidate installer, checksum manifest, launcher, host setup and matching GitHub installation section together.

#### Expected outcome

A developer can follow the [Skill Builder installation instructions](../../../README.md#planned-release-installation) against the packaged candidate from outside its source tree.

#### Scope

Use the supported runtime and existing host destinations. Limit writes to the chosen install and host paths. Preserve local edits and unrelated software. Public distribution requires release-owner authority.

#### Specification

Release maintainer · [B6](specs/skill-assignments/spec.md#install-the-release-and-connect-a-host) · R6/A7a. Requires T50 and its staged writer or supported legacy installation.

#### Acceptance criteria

- **T51.1** From an isolated user directory without a checkout, install the tagged candidate through the documented release installer. Verify `skill-builder --version` and its PATH location. Use `skill-builder host init --tools codex` and request one bounded assignment with the accepted writing dependency and recover its governing requirement from the installed result. Keep the tag, digest, actual host invocation, result and selected path. Inspect that the sibling host and an untouched project were not modified. <a id="t51-1"></a>
- **T51.2** Give the same installer an asset that disagrees with its release checksum. It must identify the mismatch and leave the prior usable version and unrelated files intact. If a prerequisite is absent, report the required prerequisite and recovery. Limit platform claims to release assets with compatible install evidence. <a id="t51-2"></a>

#### Relevant files

Current `scripts/install_skill.py`, `scripts/requirements-lock.txt`, root `README.md` and the candidate’s release entry. Record the candidate, each verdict and its evidence in this Issue. [Shared Definition of Done](design.md#requirement-coverage)

- [ ] 8.2 [T52](#t52-issue) (T011). Install with npm and refresh the same skill. After T51 and its accepted payload.

<a id="t52-issue"></a>

### T52 · Install with npm and refresh the same skill

#### Description

An npm user can reach the same Skill Builder version, update it through npm and remove owned files safely. Use the same host setup and payload as the GitHub installer. Ship the package manifest, CLI entry and npm/update/removal steps in the `README.md` together.

#### Expected outcome

A developer can follow the [Skill Builder installation instructions](../../../README.md#planned-release-installation) against the packaged candidate from outside its source tree.

#### Scope

Use the supported runtime and existing host destinations. Limit writes to the chosen install and host paths. Preserve local edits and unrelated software. Public distribution requires release-owner authority.

#### Specification

Release maintainer · [B6](specs/skill-assignments/spec.md#install-the-release-and-connect-a-host) · R6/A7b. Requires T51 and its accepted payload.

#### Acceptance criteria

- **T52.1** Install the candidate `npm pack` tarball in an empty npm prefix. Run `skill-builder --version` from that prefix and `skill-builder host init --tools claude`. Verify the release revision and actual Claude Code invocation. Repeat setup and observe one owned entry. Reuse the first channel’s product evidence when the payload and interface match. <a id="t52-1"></a>
- **T52.2** With a prior staged version, upgrade through the same channel and run `skill-builder host update`. Observe the new version at the selected host. Exercise a local edit at a managed destination and retain its content on conflict. Run the documented host removal and channel-specific uninstall in the disposable environment. Check that the other skill, project file and foreign entry survive. Record what each channel owns; reuse equivalent update and removal evidence. <a id="t52-2"></a>

#### Relevant files

Current `scripts/install_skill.py`, `scripts/requirements-lock.txt`, root `README.md` and the candidate’s release entry. Record the candidate, each verdict and its evidence in this Issue. [Shared Definition of Done](design.md#requirement-coverage)

## Finish the delivery

Use A5 for the integrated planning handoff on the named hosts and A6 for dependency compatibility. Use A7 for the install, upgrade and removal evidence. Supply the accepted Builder commit to the writer implementer. A completed list alone cannot establish either result. [Coverage and shared Definition of Done](./design.md#requirement-coverage)
