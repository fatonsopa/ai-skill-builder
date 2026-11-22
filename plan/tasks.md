# Skill Builder implementation tasks

Read the [specification](./specification.md) for the required behavior and the [implementation plan](./implementation-plan.md) for the delivery approach. Each row links to the Issue that owns its scope, acceptance criteria and proof. The path in a row points to a starting file. The Issue identifies the full change. The short task number is local to this list. Use the linked Issue ID when handing work to another repository.

Start with B1/T17 on the bound Builder baseline. T36 can run alongside it on the separate performer interface. T50 can use a staged writer as soon as the baseline is bound. The first usable result is a bounded assignment that reaches the next work packet. An accepted Builder with B5/T50 is the input to the writer handoff.

Order expresses delivery preference. An Issue can start when its stated inputs, authority and dependencies are settled. `[P]` identifies the opening pair whose changes can run in parallel. A writing-only request ends at the reviewed list. During an authorized build, open the next eligible Issue, verify it, record the candidate and evidence there, mark its row, then return here. Verify each story at its linked acceptance criteria. [Read-only handoff test](./test.md)

## B1 · Commission work that serves an approved requirement

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./implementation-plan.md#b1--commission-work-that-serves-an-approved-requirement)

- [ ] T001 [P] [US1] Admit a source-bound work assignment. `scripts/runtime/contracts.py`. [T17 · T17.a, T17.b](./implementation-plan.md#t17--admit-a-source-bound-work-assignment) Start here after binding the baseline.

## B3 · Assess an ordinary request without revealing the grader’s clues

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./implementation-plan.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [ ] T002 [P] [US3] Export a neutral native task with a traceable result. `scripts/evaluate.py`. [T36 · T36.a, T36.b](./implementation-plan.md#t36--export-a-neutral-native-task-with-a-traceable-result) Can start alongside T17 on the native evaluator. Coordinate edits with T24 if both would change the same evaluator.

## B1 · Commission work that serves an approved requirement (continued)

**Demonstrate the story.** Follow an admitted assignment into production and locate a requirement with no owning work. [Story criteria](./implementation-plan.md#b1--commission-work-that-serves-an-approved-requirement)

- [ ] T003 [US1] Expose a requirement that has tests but no owning work. `scripts/runtime/artifacts.py`. [T18 · T18.a, T18.b](./implementation-plan.md#t18--expose-a-requirement-that-has-tests-but-no-owning-work) After T17 supplies the admitted assignment.

## B2 · Accept valid work in either order

**Demonstrate the story.** Accept both valid read orders and locate a premature decision or missing prerequisite. [Story criteria](./implementation-plan.md#b2--accept-valid-work-in-either-order)

- [ ] T004 [US2] Grade independent reads in an explicitly supplied evaluation case. `scripts/evaluate.py`. [T24 · T24.a, T24.b](./implementation-plan.md#t24--grade-independent-reads-in-an-explicitly-supplied-evaluation-case) Start once the dependency representation and its version boundary with B1 are settled. Coordinate evaluator edits with T36.
- [ ] T005 [US2] Generate checks only for declared workflow dependencies. `scripts/runtime/contracts.py`. [T25 · T25.a, T25.b](./implementation-plan.md#t25--generate-checks-only-for-declared-workflow-dependencies) After T24, with T17’s schema-version boundary settled.

## B3 · Assess an ordinary request without revealing the grader’s clues (continued)

**Demonstrate the story.** Recover the original case at the controller while the performer sees an ordinary request. [Story criteria](./implementation-plan.md#b3--assess-an-ordinary-request-without-revealing-the-graders-clues)

- [ ] T006 [US3] Stage a neutral host workspace and recover its real case identity. `tools/run_behavioral_evals.py`. [T37 · T37.a, T37.b](./implementation-plan.md#t37--stage-a-neutral-host-workspace-and-recover-its-real-case-identity) After T36 supplies the fixture and controller identity.

## B4 · Keep related observations and decision authority through a handoff

**Demonstrate the story.** Follow the two sourced observations from assignment to return while the retry decision stays with its owner. [Story criteria](./implementation-plan.md#b4--keep-related-observations-and-decision-authority-through-a-handoff)

- [ ] T007 [US4] Commission related reports as a bounded investigation. `references/agents_and_skills.md`. [T48 · T48.a, T48.b](./implementation-plan.md#t48--commission-related-reports-as-a-bounded-investigation) After T17 supplies the accepted assignment shape.
- [ ] T008 [US4] Return supported conclusions and the owner’s retry decision. `references/agents_and_skills.md`. [T49 · T49.a, T49.b](./implementation-plan.md#t49--return-supported-conclusions-and-the-owners-retry-decision) After T48 supplies the assignment.

## B5 · Keep checked authoring available across the writer rename

**Demonstrate the story.** Validate a document with the renamed dependency, resolve its legacy identity and reject an unrelated explicit selection. [Story criteria](./implementation-plan.md#b5--keep-checked-authoring-available-across-the-writer-rename)

- [ ] T009 [US5] Resolve Spec Writer and its legacy identity. `scripts/runtime/technical_writer.py`. [T50 · T50.1, T50.2](./implementation-plan.md#t50--resolve-spec-writer-and-its-legacy-identity) Use a staged writer after binding the Builder baseline. The live rename follows acceptance of this Issue and of Builder.

## Finish the delivery

Use A5 for the integrated planning handoff on the named hosts and A6 for dependency compatibility. Supply the accepted Builder commit to the writer implementer. A completed list alone cannot establish either result. [Coverage and shared Definition of Done](./implementation-plan.md#requirement-coverage)
