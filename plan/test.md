# Skill Builder handoff test specification

Test basis: [Behavioral specification](../openspec/changes/improve-skill-builder/specs/skill-assignments/spec.md) and the [approved task records](../openspec/changes/improve-skill-builder/tasks.md) in this handoff revision.

Test item: The [execution guide](README.md), [task list](../openspec/changes/improve-skill-builder/tasks.md) and linked Issue records at the same Git revision. Record the candidate used for each observation.

## Coverage and setup

The first two cases test whether a reader can select a task, find its criteria and stop at a real dependency. Use a read-only checkout. Supply hypothetical completion states in the question. Leave the actual task boxes and Issue verdicts untouched. The last two cases require an implementation candidate. Use the real T48 assignment for admission as T17 ships. At release, reuse the host and dependency checks already required by A5 and A6.

For this handoff, inspect the native change status and the task context returned by `openspec instructions apply --change improve-skill-builder --json`. Compare the row identities, evidence and checked states with the native task list. This read-only check is separate from exercising the future skill.

## Cases

| ID / requirement | Preconditions and action | Expected outcome |
| --- | --- | --- |
| B-START · B1.a/B3.a | On the bound baseline with no accepted Issues, ask what can start together and where the first result will appear. | Select T17 and T36 on separate interfaces. Open T17.a for its expected admitted and consumed assignment. Hold T48 until the accepted T17 assignment shape is available. |
| B-RESUME · B1.b/B4.a | Provide a hypothetical accepted T17 commit with evidence for T17.a and T17.b. Ask what becomes eligible and who can authorize publication. | T18 and T48 can consume the accepted assignment. The implementer can recover their distinct criteria from their Issues. The handoff grants local implementation authority only. |
| B-HANDOFF · A5/A6 | On the eventual Builder candidate, use the already scheduled host assignment and staged dependency check. Ask what the writer implementer can consume. | Collect the existing A5 and A6 evidence, including T50’s canonical, legacy and wrong-identity outcomes. Hand the accepted Builder commit to Writer. Missing host proof remains visible. |
| B-PACKET · T17.a/T48.a | As T17 ships, give the supported plan-admission route the actual B4/T48 assignment from this revision. Follow the Issue’s link to B4.a in the specification. Identify the allowed investigation, prerequisites and proof in the Issue. Read the next production packet without carrying out the assignment. | The admitted and consumed records both identify T48, B4.a, the T17 prerequisite and the owner-controlled retry boundary. Follow the packet back to the Issue and its required evidence. Reuse this readback as the valid-assignment part of T17.a when it proves that part. The separate safeguard and rejection checks still apply. |

## Procedure and cleanup

1. Give the reader the execution guide and the starting state for each of the first two cases. Keep the expected answers with the assessor. Ask for the selected and blocked work, the owning Issue or criterion, and the source of its authority.
2. Compare the returned choices and links with the expected outcomes. Record the candidate, exact sources and observed result in the private JSON execution log. A wrong selection fails the affected case. Reuse the other case while its inputs still match.
3. For the implementation cases, use the named Issue’s checks on its actual candidate. Compare the resolved Issues, behaviors and dependencies. Different wording or local task numbers can be valid. Keep its evidence with that Issue. The reading exercise creates no tracked state to clean up.

## Open prerequisites

Admission requires the T17 candidate. The release case needs the accepted candidate, the staged writer dependency and the host evidence already required by A5 and A6. Reading the handoff cannot establish those results.
