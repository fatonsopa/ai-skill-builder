# Skill Builder implementation plan

Status: Scope approved for implementation on the handoff computer. Revision 6. Each audit finding is one epic in the Technical Writer User Story (US) format. Each child task uses its Issue template. The specification owns the five epic stories. The task list contains their nine Issues. [Story template](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/references/user_story.md) · [Task template](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/references/issue.md)

## Goal and specification

Deliver a local Skill Builder revision that commissions bounded work and verifies it against the owner’s requirements. The [behavioral specification, revision 5](./specification.md) owns R1–R5 and A1–A6. The [audit](./audit.md) owns B1–B5 and their supporting evidence. Start from Skill Builder commit `222b356fd5ac7a2df9fd9621e3744db883ecede0` or reconcile material changes since that baseline. The approved scope, candidate, Technical Writer dependency and allowed paths must be captured before implementation. Technical Writer’s own implementation is a separate delivery.

## Current context and approach

**One task is one usable increment.** Ship through the supported interface named in its expected outcome. Keep the change, affected consumers, guidance and closest regression in the same independently reviewable commit. Every commit must work with the previous supported inputs. A maintainer can stop after it and still use what was delivered.

**Find the problem before widening the change.** At task entry, use the named counterexample against the affected interface. Reuse an audit control if its inputs and boundary still match. If the expected failure is already fixed, inspect the current output against the criterion and record the existing evidence. Otherwise make the smallest correction and retry at the first failing boundary. A fresh run requires a failed criterion, changed input or missing observation. An unexpected contract or authority change goes back to the owner before dependent work proceeds.

**Close the increment immediately.** Review the actual diff and evidence. Run the applicable impacted checks with the repository’s `scripts/run_tests.py --execute` route. Record each criterion’s verdict, commit or identified working candidate, evidence location and reviewer in its existing task. Under implementation authority, commit and hand off the accepted increment before expanding it. A failed check stays in history. Local commit, local package application and publication are separate actions. The shared Definition of Done and integrated release check appear below.

The owner approved the work order, scope and local integration authority. Start with the execution prompt in the repository’s [execution guide](./README.md). Use this plan for delivery dependencies, integrated evidence and closure. Each Issue owns its task boundaries and required proof. Keep the private JSON execution log described in the starting prompt. Reuse native run records and document the reason for each extra verification before it runs.

## Work sequence

Open the [task list](./tasks.md) to select work. Follow its row to the owning Issue in that list and use that Issue’s scope, criterion IDs and proof. The [handoff test specification](./test.md) exercises this same route on the actual packet. Use the B1–B5 outcomes in the [specification](./specification.md#scenarios) as the stories. Their Issues are already scoped, so an extra story layer would duplicate the plan.

B5 can use a staged candidate after the initial Builder baseline is bound. The new identity becomes live on the other computer only after T50 is accepted. The real renamed release is a consumer check in writer W46.

Start with B1 and use its accepted assignment format for B4. B2 can proceed once the shared schema version boundary with B1 is settled. B3 has its own performer/controller interface and can proceed independently, with a coordinated edit to the shared evaluator file if needed. Within each epic, ship the first child, then extend its working result with the second. Each Issue in the task list is the unit of commit and handoff. Attach its evidence before marking it accepted. All task and epic criteria currently have the verdict **Not demonstrated**. D1 records the owner’s approval.

| Governing outcome | Shippable Issues |
| --- | --- |
| <a id="b1--commission-work-that-serves-an-approved-requirement"></a>[B1](./specification.md#b1--commission-work-that-serves-an-approved-requirement) | <a id="t17--admit-a-source-bound-work-assignment"></a>[T17](./tasks.md#t17--admit-a-source-bound-work-assignment), <a id="t18--expose-a-requirement-that-has-tests-but-no-owning-work"></a>[T18](./tasks.md#t18--expose-a-requirement-that-has-tests-but-no-owning-work) |
| <a id="b2--accept-valid-work-in-either-order"></a>[B2](./specification.md#b2--accept-valid-work-in-either-order) | <a id="t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case"></a>[T24](./tasks.md#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case), <a id="t25--generate-checks-only-for-declared-workflow-dependencies"></a>[T25](./tasks.md#t25--generate-checks-only-for-declared-workflow-dependencies) |
| <a id="b3--assess-an-ordinary-request-without-revealing-the-graders-clues"></a>[B3](./specification.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues) | <a id="t36--export-a-neutral-native-task-with-a-traceable-result"></a>[T36](./tasks.md#t36--export-a-neutral-native-task-with-a-traceable-result), <a id="t37--stage-a-neutral-host-workspace-and-recover-its-real-case-identity"></a>[T37](./tasks.md#t37--stage-a-neutral-host-workspace-and-recover-its-real-case-identity) |
| <a id="b4--keep-related-observations-and-decision-authority-through-a-handoff"></a>[B4](./specification.md#b4--keep-related-observations-and-decision-authority-through-a-handoff) | <a id="t48--commission-related-reports-as-a-bounded-investigation"></a>[T48](./tasks.md#t48--commission-related-reports-as-a-bounded-investigation), <a id="t49--return-supported-conclusions-and-the-owners-retry-decision"></a>[T49](./tasks.md#t49--return-supported-conclusions-and-the-owners-retry-decision) |
| <a id="b5--keep-checked-authoring-available-across-the-writer-rename"></a>[B5](./specification.md#b5--keep-checked-authoring-available-across-the-writer-rename) | <a id="t50--resolve-spec-writer-and-its-legacy-identity"></a>[T50](./tasks.md#t50--resolve-spec-writer-and-its-legacy-identity) |

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

The approved behavior and scope carry forward into specification revision 5 and implementation plan revision 6. Implement Skill Builder first, with a distinct staged candidate and a local implementation branch. Internal file names and implementation choices are delegated within the approved scope. A missing host observation remains Not demonstrated.

At closure record each task criterion, story criterion and A1–A6 as Met, Failed or Not demonstrated with its candidate and evidence in the existing work item. Preserve earlier failures. Close each finding’s epic on its story-level evidence and the delivery on A5 and A6. A parent rollup of closed tasks cannot establish either verdict. Deliver the locally applied Builder revision to the owner. Any subsequent Technical Writer implementation starts with its separately approved specification and implementation plan. [Technical Writer implementation plan](https://github.com/fatonsopa/ai-technical-writer/blob/docs/autonomous-implementation/plan/implementation-plan.md)

## Pending owner decisions

None at handoff. Append out-of-scope discoveries here with their source, observed effect, proposed change, impact of deferral and any task actually blocked. Only an explicit owner decision can add them to implementation scope.
