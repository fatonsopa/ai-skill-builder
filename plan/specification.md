# Skill Builder assignment and verification specification

Status: Approved behavioral scope, revision 5. Applies to Codex and Claude Code. [Audit](./audit.md) · [Implementation plan](./implementation-plan.md)

Source: The owner’s approved scope and the [comparative audit](./audit.md).

## Purpose and scope

A maintainer can use Skill Builder to commission a bounded skill change, give its implementer enough authority and context to act, and assess what the resulting skill delivers. The first downstream use is the Technical Writer implementation plan. Use its approved specification and plan revision, identified by commit, for the example handoff. Their implementation needs its own authority.

The change covers plan admission, workflow coverage and process grading, the two performer-input routes, and an example of lead-to-worker-to-user communication. Preserve existing permission boundaries, historical evidence, explicit invocation, dependency checks, document validation, and the scope of each host claim. Product delivery, external publication, new provider adapters and changes to Mirai are outside the authorized audit.

## Definitions

An **assignment** is independently owned work with a usable outcome. A **substep** is an ordinary action inside that assignment. A **material dependency** exists when the consumer cannot reach a valid or authorized result until its prerequisite completes. The **performer** receives the task. The **controller** retains the case identity, expected outcomes and evidence bindings. A **criterion** identifies the observable behavior the owner agreed to accept.

## Scenarios

1. A maintainer commissions the first connected handoff from the Technical Writer implementation plan. The implementer sees the approved revision, source, criterion, permissible change and proof. The implementer can reject an unrelated request even if it names a real criterion.
2. A lead has two related observations and an unconfirmed explanation. The lead preserves both sources and can keep the investigation together or split genuinely independent work. The user can tell what was observed and what still needs a decision.
3. The assessor runs a case in which two sources can be read in either order. Both reads must precede the decision. The performer sees the ordinary request. The assessor can attribute the result to the exact case and host after the run.

### B1 · Commission work that serves an approved requirement

As a skill maintainer, I want to trace each assignment to an approved outcome and each requirement to its owner, so that I can release a bounded work packet without granting extra authority.

#### Acceptance criteria

- **B1.a** Given a frozen requirement and an assignment, submit the real plan packet. A supported contribution or justified safeguard is eligible. An invented criterion is located before production and an unrelated publication instruction fails semantic review even when it cites a valid ID. Inspect the row, diagnostic and reviewer decision. T17 supplies this proof. <a id="b1-a"></a>
- **B1.b** Given an in-scope requirement with a test but no owning work, review coverage. The uncovered requirement is visible and blocks a complete-coverage claim. Assign the work and confirm the same plan can proceed. Inspect the before/after mapping and one historical plan read. T18 supplies this proof. <a id="b1-b"></a>

#### Scope and sources

Delivery approach: [implementation plan](./implementation-plan.md). Owner role: plan-contract maintainer. Finding [B1](#b1--commission-work-that-serves-an-approved-requirement), requirement R1, criterion A1. The source of authority is the frozen specification. Existing file scope and publication controls remain in force. Close the epic when the implementer can recover the allowed work and proof from the admitted packet alone. Use the same packet and review evidence from [T17](./tasks.md#t17--admit-a-source-bound-work-assignment) and [T18](./tasks.md#t18--expose-a-requirement-that-has-tests-but-no-owning-work).

### B2 · Accept valid work in either order

As a workflow author, I want to declare which steps depend on each other, so that a correct result can pass and a premature decision can be caught.

#### Acceptance criteria

- **B2.a** Given a case requiring two independent reads before a decision, run it through the evaluator. Both read orders pass. Omission, an early decision and missing required visible evidence fail at their respective boundaries. Reversing a legacy strict sequence still fails. Inspect the verdicts from T24. <a id="b2-a"></a>
- **B2.b** Given the same relation in an authored workflow, submit the plan and use its generated evaluator. Derivation and grading agree on the prerequisites. A cyclic or unknown dependency fails admission. Inspect the generated case, its result and the two admission diagnostics from T25. <a id="b2-b"></a>

#### Scope and sources

Delivery approach: [implementation plan](./implementation-plan.md). Owner role: workflow-contract maintainer. Finding [B2](#b2--accept-valid-work-in-either-order), R2/A2. The declaration concerns material prerequisites. Legacy workflows keep their strict sequence and all existing permission, omission and recovery obligations. Close on one connected path from authored workflow to distributed evaluator.

### B3 · Assess an ordinary request without revealing the grader’s clues

As a skill evaluator, I want to give the performer realistic inputs while retaining case identity in the controller, so that I can attribute a result to the right case without hinting at the intended answer.

#### Acceptance criteria

- **B3.a** Export a native task with a deliberately descriptive case ID and a genuine user filename. The performer receives the task and file, while the controller retains the real case identity and rejects a mismatched result. Inspect T36’s exported view and readback. <a id="b3-a"></a>
- **B3.b** Stage the same case through the live-harness launch path. The submitted arguments, prompt, working directory and staged paths carry no grader-only clue. The controller can still resolve the candidate and a historical report. Inspect T37’s recorded launch and assessment. <a id="b3-b"></a>

#### Scope and sources

Delivery approach: [implementation plan](./implementation-plan.md). Owner role: evaluation-harness maintainer. Finding [B3](#b3--assess-an-ordinary-request-without-revealing-the-graders-clues), R3/A3. Keep case identity and evidence provenance on the controller. This epic covers the two task-input interfaces. Its acceptance measures what the performer is given. Model performance remains a separate claim.

### B4 · Keep related observations and decision authority through a handoff

As a investigation lead, I want to commission related reports together when they share a criterion and explain what the evidence supports, so that the owner can act without losing uncertainty or retry authority.

#### Acceptance criteria

- **B4.a** Given two reports consistent with a lost response, commission the investigation. Both source observations, the shared criterion and the owner’s retry boundary survive in one assignment or a justified split with independent outputs or an integration owner. Inspect the assignment against the supplied passages. <a id="b4-a"></a>
- **B4.b** Given the return and an unconfirmed shared cause, report the result to the user. The message distinguishes observed, inferred and unresolved facts. A fresh read precedes any offered retry, and only the administrator may choose it. Unsupported source inspection, a confirmed-cause claim without proof, or an automatic retry fails. Use one actual exchange to judge both criteria. <a id="b4-b"></a>

#### Scope and sources

Delivery approach: [implementation plan](./implementation-plan.md). Owner role: orchestration-guidance maintainer. Finding [B4](#b4--keep-related-observations-and-decision-authority-through-a-handoff), R4/A4. Requires the assignment interface from [B1](#b1--commission-work-that-serves-an-approved-requirement). The single-agent equivalent is eligible. The task is to write and use the handoff guidance. Claim actual specialist execution only with observed dispatch and return.

### B5 · Keep checked authoring available across the writer rename

As a skill maintainer, I want Builder to resolve the new and legacy writing packages, so that a name change preserves document acceptance.

#### Acceptance criteria

- **B5.a** On a complete staged writer package bearing the new name, resolve the dependency and validate a document through the real Builder validation path. A legacy package still resolves. An explicitly selected wrong identity fails without fallback; an already-bound run cannot silently accept a changed dependency. <a id="b5-a"></a>

#### Scope and sources

Delivery approach: [implementation plan](./implementation-plan.md). Owner role: Builder dependency maintainer. [T50](./tasks.md#t50--resolve-spec-writer-and-its-legacy-identity) supports [B5.a](#b5-a), R5/A6. [Dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)

## Requirements and business rules

| ID | Required behavior and owner |
| --- | --- |
| R1 | At plan freeze, the plan owner maps every independent assignment to a governing revision and criterion or an explicitly justified necessary safeguard. The assignment supplies owner, outcome, scope, prerequisites, material failure behavior and proof. The assessor checks the reverse mapping for uncovered requirements. Ordinary substeps can remain inline. A scope expansion requires the actual owner. |
| R2 | The workflow author declares material prerequisites where more than one sequence is valid. The coverage generator and process grader use the same definition. Every required step, explicit boundary, branch, recovery path and consequential visibility/evidence obligation remains assessable. Existing strict sequences retain their meaning. |
| R3 | The controller supplies a realistic task through either supported performer-input route. It keeps descriptive case identity, grading material and its binding outside what it submits to the performer. The reviewer must still reconcile the original case, source bytes, candidate, host and captured result. A task may legitimately name a user file, skill or tool. |
| R4 | The lead routes related reports with the shared criterion, source revision and authority intact. The receiver reports checked source, observed outcome, inferred cause, missing evidence and next permissible action where material. The lead preserves unresolved disagreement and communicates the decision needed in plain language. One eligible agent can own the complete task. |
| R5 | Accept both `spec-writer` and the legacy `technical-writer` as supported dependency identities. Preserve explicit path precedence, existing request and environment keys, validation of required files and source snapshot integrity. |

## Quality and interface constraints

Plan and evaluation records are existing interfaces. Preserve readback, historical identity and recovery for older versions. Represent new semantics explicitly in the applicable version. No inference may silently give an old record a new ordering rule or new authority. Keep candidate write scope and publication controls independent from a plan’s reference check. The receipt and host assessment remain controller responsibilities. A digest identifies bytes. A semantic reviewer judges whether those bytes satisfy the requirement.

One case can prove several criteria if the actual outputs expose each distinction. Distinct hosts retain distinct results. Preserve the settings each host exposes and record a missing observation as such. Apply the project’s own scope, track and approval rules when consuming Mirai material. A reviewer cannot grant implementation authority.

## Acceptance criteria

| ID | Starting state and action | Expected result and failure boundary | Required proof on the candidate |
| --- | --- | --- | --- |
| A1 · R1 | Submit a proposed assignment against a frozen requirement, then use an unknown criterion, an unrelated action labeled with a real criterion, and a justified safeguard. | The valid assignment and justified safeguard remain eligible. An unknown explicit ID is located at admission. Semantic review rejects unrelated work with a real ID. A requirement left with no owning work is visible. No variant grants authority to publish. | Retain the admitted entry, located rejection, reverse coverage and the reviewer’s decision on the mismatched action and safeguard. Open one historical plan through its supported reader. |
| A2 · R2 | Under a dependency-aware declaration, read a brief and an example before deciding. Exchange the two reads, then move the decision ahead of the second read, then omit one read. Submit a legacy strict trace in reversed order. | Both legitimate orders pass. The premature decision names its unmet prerequisite. The omitted read and reversed legacy sequence fail. Required evidence and visibility still apply. A circular or unknown prerequisite cannot reach execution. | Derivation and grading on the same declared relation, with actual verdicts and diagnostics. Reuse existing unchanged omission, visibility and historical-read controls where applicable. |
| A3 · R3 | Export the native task and capture the other route’s rendered launch inputs using a deliberately descriptive case ID. Include an ordinary source filename the user explicitly requested. Reconcile the result at the controller. | Both task views preserve the request and ordinary filename. Neither exposes the descriptive test label, expected answer or grader-only inventory in the submitted text, paths or staged task inputs. The controller still resolves the true case and source. A stale or mismatched result remains ineligible. | Inspect actual rendered task inputs and paths for both routes, plus a controller-side assessment binding. Retain existing historical-report compatibility proof. |
| A4 · R4 | Give the lead two observations consistent with one lost response, an owner-controlled retry rule and no evidence establishing the cause. Ask it to commission the smallest useful investigation and report the result. | The assignment preserves both observations and their shared criterion. Any split has independent outputs or an explicit integration owner. The return identifies what was inspected, preserves uncertainty, and conveys that reconciliation precedes offering an administrator a retry. Neither a worker nor the lead initiates or requires a retry. | Actual assignment, return, and user-facing message or equivalent single-agent handoff. Compare each material claim with the supplied source and authority. A fabricated read or unsupported common cause fails. |
| A5 · R1–R4 | Through the supported skill, give each target host the same approved-for-the-example Technical Writer planning brief and read-only inputs. Request one bounded work item and its verification design. | A downstream reader can recover WEB-09, the exact permitted contribution, material dependency and proof. The rubric accepts valid alternatives. Evidence distinguishes written instructions from anything actually executed. Cross-host completion needs a qualifying result per host. | Identified candidate, common input and rubric, actual assignment and public result per host, governing source, reviewer verdict and visible limitations. This proves planning behavior only. |
| A6 · R5 | Provide staged canonical, legacy and unrelated dependency identities. | On a complete staged writer package bearing the new name, resolve the dependency and validate a document through the real Builder validation path. A legacy package still resolves. An explicitly selected wrong identity fails without fallback; an already-bound run cannot silently accept a changed dependency. | Inspect the selected paths, document-bound result, rejection and snapshot guard on the candidate. |

## Open decisions

**D2.** The owner chose Spec Writer (`spec-writer`). Builder B5/T50 must accept both identities before the live rename in the writer handoff.

**D1.** The owner approved specification revision 2 and implementation plan revision 3. Implement Skill Builder first, with a distinct staged candidate and a local implementation branch. Cross-host claims require evidence from both named hosts. Missing observations stay open.

## Related design and work

Use this specification as the behavior source for the Skill Builder change itself. The [Scenarios](#scenarios) section owns the stories and their acceptance. The [implementation plan](./implementation-plan.md) explains the delivery approach. The [task list](./tasks.md) contains the ordered work and its bounded Issue records, and the [handoff test specification](./test.md) checks whether a reader can use them. Each Issue owns its acceptance criteria and the evidence needed to close it. As T17 becomes usable, submit this plan’s actual T48 assignment and inspect the consumed result as described in B-PACKET.

The Implementation Plan (IP) assigns R1–R5 to five epics and nine bounded tasks and names the checks that can change each acceptance decision. Technical Writer retains ownership of document guidance. Its proposed improvement and the Skill Builder change are separate deliveries. [Task and verification plan](./implementation-plan.md) · [Technical Writer behavioral baseline](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/specification.md) · [Technical Writer implementation plan](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/implementation-plan.md)
