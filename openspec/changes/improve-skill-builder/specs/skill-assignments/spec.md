# Skill Builder assignments and verification

## Purpose

Skill Builder lets a maintainer commission a bounded skill change, give its implementer the authority and evidence needed to act, and assess the result against the original requirement. This change carries forward approved behavioral revision 6. The five requirements below own the product behavior. The original findings, delivery approach, nine bounded tasks and handoff cases have separate owners. [Audit](../../../../../plan/audit.md) · [Design](../../design.md) · [Tasks](../../tasks.md) · [Handoff cases](../../../../../plan/test.md)

## ADDED Requirements

### Requirement: B1 / R1 · Commission work that serves an approved requirement

<a id="scenarios"></a>
<a id="b1--commission-work-that-serves-an-approved-requirement"></a>

At plan freeze, the plan owner SHALL bind each independently owned assignment to its governing revision and agreed criterion or justify it as a necessary safeguard. The assessor SHALL check coverage from each requirement to its owning work and from each assignment back to its authority. Ordinary substeps can remain inline.

#### Scenario: B1.a / A1 · Admit a bounded assignment and reject unsupported work

<a id="b1-a"></a>

- **WHEN** the maintainer submits a real plan packet against the frozen requirement, with a valid contribution, a justified safeguard, an unknown explicit criterion or an unrelated publication instruction citing a real criterion
- **THEN** the eligible contributions remain eligible, admission identifies the unknown criterion and its location before production, and semantic review rejects the unrelated instruction. The implementer can recover the permitted outcome, owner, scope, prerequisites, material failure behavior and proof from the admitted packet. No variant authorizes publication.
- **EVIDENCE** T17 retains the admitted and consumed assignment, located diagnostic and reviewer decisions. For B-PACKET, use the actual T48 assignment. Its readback must identify T48, B4.a, its T17 prerequisite and the administrator’s retry authority without executing the investigation.

D1 records the owner’s approval of the original specification revision 2 and delivery plan revision 3. Their approved scope carries forward in behavioral revision 6. Implement Skill Builder first using a distinct staged candidate and a local implementation branch. Existing file scope, dependency and publication controls apply independently of admission. Scope expansion and external publication require their actual owner’s authority. A reviewer cannot grant implementation authority. The downstream writer change, new provider adapters and Mirai changes are outside this assignment.

#### Scenario: B1.b / A1 · Find and repair a gap in work ownership

<a id="b1-b"></a>

- **WHEN** a frozen requirement has a verification check and no owning assignment
- **THEN** the assessor identifies the uncovered requirement and withholds a complete-coverage verdict. Adding an eligible owner lets the same plan proceed.
- **EVIDENCE** T18 retains the before/after mapping and reads one historical plan through its supported reader. Preserve readback, historical identity and recovery. New semantics require an explicit applicable version.

### Requirement: B2 / R2 · Accept valid work in either order

<a id="b2--accept-valid-work-in-either-order"></a>

The workflow generator and process grader SHALL use the same declared material prerequisites. A prerequisite is material when the dependent action cannot reach a valid or authorized result before it completes. Required steps, explicit boundaries, branches, recovery paths and consequential visibility or evidence obligations remain assessable. Older strict sequences SHALL keep their original ordering rules and authority.

#### Scenario: B2.a / A2 · Grade both valid read orders and detect the invalid traces

<a id="b2-a"></a>

- **WHEN** an evaluator grades a decision that requires reading both a brief and an example, including traces with reordered reads, an early decision, an omission or missing required visible evidence
- **THEN** either read order can pass. An early decision identifies the unmet prerequisite. Omission and missing visible evidence each fail at their own boundary. Reversing a legacy strict sequence still fails.
- **EVIDENCE** T24 retains the actual verdicts. Reuse compatible omission, visibility and historical-read controls.

#### Scenario: B2.b / A2 · Carry the declared dependencies into the evaluator

<a id="b2-b"></a>

- **WHEN** a workflow author submits the same dependency relation through plan admission and runs the generated evaluator, then submits a circular relation and an unknown prerequisite
- **THEN** derivation and grading agree on the valid relation. Admission rejects each invalid relation before execution.
- **EVIDENCE** T25 retains the generated case, its grading result and the two admission diagnostics.

### Requirement: B3 / R3 · Assess an ordinary request without revealing the grader’s clues

<a id="b3--assess-an-ordinary-request-without-revealing-the-graders-clues"></a>

On both performer-input routes, the controller SHALL supply the user’s request and legitimate filenames, skills or tools while withholding the descriptive case ID, expected answer, grader-only inventory and evidence bindings. The controller SHALL preserve the receipt and host assessment, bind the result to its original case, source bytes, candidate and host, and preserve historical report identity and recovery.

#### Scenario: B3.a / A3 · Export the ordinary request and reconcile the result

<a id="b3-a"></a>

- **WHEN** the controller exports a native task with a deliberately descriptive case ID and a filename the user explicitly requested, then reconciles the returned result
- **THEN** the performer receives the request and file without grader-only material. The controller can recover the real case and source and rejects a stale or mismatched result.
- **EVIDENCE** T36 retains the exported view and controller-side assessment binding. A digest identifies the bytes. A reviewer judges whether the result satisfies the requirement.

#### Scenario: B3.b / A3 · Preserve the same separation at live launch

<a id="b3-b"></a>

- **WHEN** the live-harness route stages that case for launch
- **THEN** the submitted arguments, prompt, working directory, staged paths and files preserve the ordinary request without disclosing a grader-only clue. The controller can resolve the candidate, returned evidence and a historical report.
- **EVIDENCE** T37 inspects the actual rendered launch inputs and assessment. This proves what the performer receives. Model performance requires its own evidence.

### Requirement: B4 / R4 · Preserve related observations and decision authority

<a id="b4--keep-related-observations-and-decision-authority-through-a-handoff"></a>

Using the B1 assignment interface, the lead SHALL preserve source revisions, the shared criterion, observations and authority when commissioning related work. The receiver SHALL distinguish inspected sources, observations, inferences, material missing evidence, unresolved disagreements and the next permissible action.

#### Scenario: B4.a / A4 · Commission the investigation without assuming a cause

<a id="b4-a"></a>

- **WHEN** one supplied report describes the lost response to batch two and another describes a summary that lost track of uncertain rows
- **THEN** the assignment keeps both source observations, the shared acceptance criterion and the owner’s retry boundary. The lead may keep one investigation or split it when the outputs are independent or an explicit integration owner will reconcile them.
- **EVIDENCE** A single eligible agent may own the whole task. T48 compares the actual assignment with both supplied passages. A claim of specialist execution requires observed dispatch and return. The reports are synthetic inputs to the planning case.

#### Scenario: B4.b / A4 · Return supported conclusions and preserve the retry decision

<a id="b4-b"></a>

- **WHEN** the investigation returns without evidence proving a common cause
- **THEN** the lead’s message separates observation, inference and uncertainty and states any decision needed from the owner in plain language. A fresh read precedes offering a retry, and only the administrator may choose to retry. Neither the lead nor the worker initiates or requires it. A fabricated read, unsupported common cause or automatic retry fails.
- **EVIDENCE** T49 retains the assignment, return and user-facing message or equivalent single-agent exchange. Compare material claims with their sources and authority. One actual exchange can cover B4.a and B4.b when it shows both distinctions.

#### Scenario: A5 / R1–R4 · Demonstrate the planning handoff on each named host

- **WHEN** Codex and Claude Code each receive the same approved-for-the-example Technical Writer brief and read-only source material through the supported Skill Builder entry and are asked for one bounded work item and its verification design
- **THEN** the downstream reader can recover WEB-09, the permitted contribution, material dependency and proof. In the T16 example, loss of the second response leaves 500 confirmed IDs, 500 unresolved and one unattempted. Reconciliation precedes offering the administrator a retry. The task can specify that behavior without executing the application.
- **EVIDENCE** Use the same candidate, request, sources and rubric. Retain each host’s actual assignment, public result, exposed model/settings, inspected-source evidence, reviewer verdict and limitations. Accept valid alternatives and reuse qualifying evidence where it proves the same criterion. Written instructions alone cannot establish execution. Cross-host acceptance needs a qualifying result for each host. Report a missing observation as Not demonstrated.
- This case establishes planning and handoff behavior. Local A2 and A3 checks cover their own interfaces. Broader Builder readiness requires the applicable existing host matrix and its real skill-creation pilot. Apply the consuming project’s own scope, track and approval rules. [WEB-09](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/examples/spec_driven_development.md#L118) · [T16](https://github.com/fatonsopa/ai-technical-writer/blob/4a8e7c92e20404f05e68708c1a3ea26c6961b178/examples/test_specification.md#L55)

### Requirement: B5 / R5 · Keep checked authoring available across the writer rename

<a id="b5--keep-checked-authoring-available-across-the-writer-rename"></a>

D2 records the owner’s choice of SpecDev (`specdev`). Before the live writer rename, Builder SHALL resolve both the canonical `specdev` and the legacy `technical-writer` dependency. Preserve explicit path precedence, existing request and environment keys, validation of required files and source snapshot integrity. A run bound to a dependency must retain that binding.

#### Scenario: B5.a / A6 · Validate a document through Builder with the staged writer

<a id="b5-a"></a>

- **WHEN** T50 exercises the real Builder dependency resolver and document-validation entry with complete canonical and legacy staged packages, an explicitly selected unrelated identity and a dependency changed after the run was bound
- **THEN** the `specdev` package resolves and yields a document-bound validation result. The legacy `technical-writer` package still resolves. Explicit selection of a wrong identity fails without fallback, and the changed dependency cannot silently replace the bound snapshot.
- **EVIDENCE** Inspect the selected paths, the document-bound result, wrong-identity rejection and snapshot guard on the identified candidate. Hand off the accepted Builder commit with the qualifying A5 and A6 evidence. Product acceptance remains pending those observations. [Historical dependency resolver](https://github.com/fatonsopa/ai-skill-builder/blob/ae394124929e99ea8650fb95578f081ce0930734/scripts/runtime/technical_writer.py#L18-L32)
