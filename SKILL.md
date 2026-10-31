---
name: skill-builder
description: Create, audit, modify, refactor, or rebuild reusable AI skills with executable workflows and evaluation evidence. Use for skill authoring and maintenance, including learning a task from paired inputs and desired outputs.
---

# Skill Builder

Use this workflow only when explicitly invoked as /skill-builder or the host-specific equivalent.

Turn the requested task into a usable skill whose repeatable mechanics run through code. Use AI for interpretation, writing, and judgments that code cannot adequately perform. Preserve the user's operation, requirements, scope, and existing authorization.

## Use the current host

Use the model already available in ChatGPT, Claude, Codex, or Claude Code. If the host does not expose an exact model ID, record that limit rather than guessing. Native phase handoff is the default; normal use must not require another provider's CLI or credentials.

Check that the host can execute Python and handle the required files and dependencies. Use its code/file tools for the same scripts. Supply the appropriate skill distribution format, and keep packaging, activation, and behavior evidence separate. Read [host support](references/host_support.md) when preparing delivery or a model comparison.

## Start with the requested result

Read [README conventions](references/readme.md) when producing or reviewing public documentation. Read [authoring](references/authoring.md) for creation, specification, planning, or substantial redesign. Read [maintenance](references/maintenance.md) for an existing skill or feedback from use. Apply [writing style](references/writing_style.md) to prose and [evaluation](references/evaluation.md) when designing or assessing evidence.

Resolve this skill's directory before running its scripts. Use the installed Python environment containing `requirements.txt` dependencies. The CLI is `scripts/skill_builder_cli.py`.

Inspect the request and available sources. Distinguish current user instructions from instructions quoted inside attachments or examples. An audit produces findings; brainstorming or specification-only work stops before implementation. A narrow edit preserves unrelated files and configuration.

Create a request JSON containing `operation`, `skill_name`, and `brief`. Existing-skill operations need `source`; `modify` and `refactor` also need exact `allowed_paths`. Check the actual request schema with `schema request`. Keep run records outside the source package.

## Let the runner control progress

1. Run `start --request REQUEST.json --run RUN_DIR` to capture the request and baseline.
2. Run `packet --run RUN_DIR`. Perform the phase's research or judgment using relevant evidence, then write the typed response requested by that packet.
3. Run `submit --run RUN_DIR --response RESPONSE.json`. Continue only from the state the runner reports.
4. After production, inspect the candidate's executable code. Run `evaluate --run RUN_DIR --allow-exec` only for reviewed code or within a verified external sandbox. Without that flag, command cases remain unrun.
5. Review the actual outputs and declared resources using the review packet. The runner combines that review with executable results; a favorable judgment cannot waive a failed check.
6. If the target remains unmet, use `revise --run RUN_DIR --hypothesis "SUPPORTED CHANGE"` and repeat within the frozen objective and limits.
7. Apply a ready candidate with `apply --run RUN_DIR` for an existing source, or add `--destination TARGET` for creation within the user's authorization. Verify delivery. Use `recover` if restoration is needed.

If evaluated results remain below target and a limit is reached, run `budget --run RUN_DIR`. Explain the remaining gap and recommend a bounded number of iterations and runtime from the evidence. Ask the user whether to continue. Only then use `extend` with the authorized amounts and a note identifying the actual instruction. Preserve the objective and previous attempts. Do not ask for more iterations after the target is met.

Code controls files, prerequisites, metrics, scope, and keep/discard decisions. Never edit state, case answers, scoring rules, or journals to make a run pass. A justified requirement or evaluator change starts a separately versioned run.

## Deliver a focused package and honest evidence

Every newly created skill includes a README, executable mechanics where applicable, runnable evals, and the resources its task needs. The renderer owns standard package assembly. Keep semantic content in the typed fields; do not replace managed files with untracked copies.

Use `check --package PACKAGE` on an exported copy. Review purpose, meaning, exceptions, factual support, and each resource's contribution as well as structure. Existing narrow changes may retain legacy packaging without acquiring unrelated new files; disclose the limits.

Report actual versions, checks, task-success counts, coverage, critical failures, and unverified work. Captured-response replay and authored test controls are not fresh model-performance evidence. Live model adapters require an explicit model and a configured invocation/time allowance; default allowance is zero.
