# Skill Builder change proposal

## Why

A maintainer needs to commission one bounded skill change and know whether the assigned agent actually delivered it. The audit found gaps in requirement coverage, process grading and the evidence the maintainer receives.

## What Changes

- Tie each admitted assignment and necessary safeguard to the approved requirement and verify that the implementer receives that same bounded assignment.
- Grade only real dependencies. Keep the assessor's clues out of the performer's prompt; preserve candidate, host and observed evidence.
- Accept the staged `specdev` and legacy `technical-writer` authoring dependencies under the current selection and verification rules.
- Distribute Skill Builder as a verified GitHub release and an npm package, with one documented path for connecting Codex and Claude Code.

## Capabilities

### New Capabilities

- `skill-assignments` records the proposed assignment, assessment and checked writing dependency behavior of Skill Builder. This is the first native specification for this capability in this repository.

### Modified Capabilities

There is no previous OpenSpec capability baseline in this repository.

## Impact

Affected consumers include skill maintainers, the performer and assessor, and the SpecDev implementation handoff. Deliver the accepted local Builder commit to the SpecDev implementer. Product release, GitHub publication and archive keep their existing authority boundaries. [Audit](../../../plan/audit.md) · [Design and delivery plan](design.md) · [Ordered work](tasks.md)
