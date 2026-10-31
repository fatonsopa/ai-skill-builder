# Audit, repair, and rebuild skills

Identify the reported problem and the requested scope. Inspect the actual package, relevant callers, requirements, outputs, and available evidence. Preserve a baseline before changing files. A request to repair one answer does not automatically authorize a persistent rule.

## Choose the change from evidence

An audit returns located findings, consequences, and recommendations. Retain a valid skill. Use modification for a deliberate behavior change, refactoring for a behavior-preserving change, and rebuilding when the existing structure cannot support the agreed requirements reliably.

For `modify` and `refactor`, specify exact `allowed_paths` before staging changes. Include renamed or removed files and their actual callers. Preserve visible labels, identifiers, exceptions, invocation preferences, and relevant metadata. Code checks content hashes and local links; semantic preservation still needs review.

For rebuilding, reconcile the original requirements first. Capture baseline results with `evaluate --baseline` after freezing the plan, using execution permission only for reviewed code. Compare matching cases and disclose differences. Do not erase a valid capability because the replacement has a better average score.

## Repair through a bounded experiment

Retain the failed output, diagnosis, and a scoped hypothesis. Freeze cases, scoring, targets, and editable candidate paths before tuning. Use `revise` to request a new candidate within the declared experiment, execution-time, and stagnation limits.

The runner keeps the best candidate satisfying mandatory checks, discards worse candidates, and marks a candidate ready only when its target is met. Semantic judgments cannot override failed mechanical checks. A target already met ends that optimization run. When the target is unmet and a limit is exhausted, use `budget` to explain the evidence and recommend bounded additional iterations and runtime. Ask the user before `extend` records a new allowance. A new objective or evaluator correction requires a new versioned run.

If a semantic judge is wrong, retain its original judgment and document the correction. Never lower a criterion merely to pass.

## Capture and close feedback

Use `feedback --run RUN_DIR --text "OBSERVATION"` to retain a local report. Add `--maintenance` when the request includes reusable changes. Keep the expected behavior, actual result, input, artifact version, and reproduction uncertainty when available.

Classify the cause as a defect, changed requirement, preference, missing context, environment, model, or grader issue. A hypothesis is not a proven cause. Preserve intermittent observations and use fresh repetitions where needed; replaying the saved answer is not fresh reproduction.

Create a faithful regression and test relevant neighboring inputs. After validated maintenance is applied, use `resolve-feedback --run ORIGINAL_RUN --id FEEDBACK_ID --classification CLASS --resolution-run FIX_RUN --case REGRESSION_ID`. Closure requires an applied, unchanged candidate and a passing linked case. The agent must still verify that this case represents the reported failure.

## Apply and recover

`apply` checks the source snapshot again, journals each write, and verifies the delivered file contents against the accepted candidate. Existing-source changes apply to that captured source. New packages need an explicit destination.

`recover` restores recorded before-images only when the current file still matches the applied value. It preserves newer user changes and reports conflicts. Recovery can be repeated. Multi-file application is journaled, not atomic; inspect unresolved interruptions before continuing.

`replay` rebuilds artifacts from captured phase responses and frozen inputs. It reuses recorded evaluation observations without rerunning commands, calling models, or repeating delivery. Changed runner/dependency versions can invalidate replay and must be reported.

## Structure repairs

Use the [canonical structure](skill_structure.md) for layout audits and authorized refactors. Report the runner's automatic structure findings. Include both sides of each move in allowed_paths, preserve private history externally, update all consumers and verify a fresh repository install. Narrow modifications do not authorize unrelated moves.
