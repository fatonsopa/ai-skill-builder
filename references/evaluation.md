# Evaluate intended behavior

Define acceptance before tuning. Each requirement needs a case, and each declared guidance resource needs a purpose-linked review. Test what the task should accomplish: structure and keyword checks establish only the properties they actually measure.

## Build meaningful cases

Use exact JSON or literal checks when the contract requires them. Mark meaning-dependent cases for semantic review. Test new inputs, relevant invalid input, exceptions, preservation, and actual executable behavior. A writing skill needs complete factual and semantic review as well as required sections.

The runner supports command cases and artifact cases. Command cases declare an argument array, standard input, expected exit status, and relevant output values. `{python}` resolves to the current interpreter. Artifact cases declare an expected file and optional JSON value. Use `schema plan` for the exact case contract.

Command evaluation requires `--allow-exec` after reviewing the code, or a verified external sandbox. Each case receives a disposable package copy, and timeouts terminate the process group. Copies, hash checks, and read-only model modes are not a complete security boundary for arbitrary untrusted code.

Cases marked semantic remain pending until a review response covers their actual outputs. Review also covers `SKILL.md`, `README.md`, and every declared resource in context. Identify human or model reviewers and their methods honestly. Authored labels used in unit tests are not independent human calibration.

## Interpret results correctly

Task success is accepted valid evaluated attempts divided by all valid evaluated attempts. Coverage is valid evaluated attempts divided by planned attempts. Show counts with percentages. Wrong or malformed task outputs are failures, not excluded observations. Missing facilities reduce coverage; zero valid observations yields an undefined success percentage.

Critical failures and missing coverage prevent readiness regardless of the average. Quality scores require a named rubric and should not be called accuracy. Truth-based accuracy needs a known oracle and a declared unit; the current runner reports task-success percentages, not a universal accuracy estimate.

Preserve every attempt. Use repeated fresh runs for variable behavior and show mixed outcomes. Avoid treating correlated repetitions or synthetic variants as independent examples.

## Models and independent contexts

Separate the model authoring a skill, a model using that skill, and the judge. The default `model --run RUN_DIR` hands the phase to the current host model. The optional `--provider codex|claude --model EXACT_ID` helper obtains one structured phase response through a declared external route. It records provider, requested identifier, duration, failure, and response without automatically submitting or promoting it.

The request's `limits.max_live_calls` is an allowance for CLI invocations, not a provider request counter or a billing cap. Its default is zero. Select the exact model and time allowance before execution. CLI presence does not establish authentication or model availability. The helper does not silently substitute models.

The adapters use a temporary working directory and verified command-line options. Codex uses read-only execution and ignores user configuration while retaining host rules. Claude uses bare mode with tools and skills disabled, so it requires compatible API/provider credentials rather than assuming subscription OAuth. These routes are explicit-response helpers, not skill-discovery tests.

A cross-model runtime claim needs actual matched tasks on each selected model using the same exported artifact. Do not call the phase-response helper a completed runtime benchmark. Native host discovery, model comparisons, judge calibration, and protected acceptance remain separate checks.

## Improve without changing the target

Record the baseline, hypothesis, candidate version, objective, attempts, and keep/discard decision. Use development evidence to tune; keep protected examples and answers out of the optimizing context. Inspect the whole relevant output and execution trace before diagnosing a failure.

Correct an evaluator through a separate justified version, then establish comparable baselines. If acceptance failures guide another repair, they become regressions and need replacement protected cases. Stop at the target, the user's interruption, or declared limits, and preserve the best candidate when the target remains unmet.

## Bounded continuation

Use observed scores, failures, coverage, and execution time to recommend another batch when a target remains unmet. Ask the user before increasing limits. The builder records approved extensions with `extend`; generated skills enforce the same policy through the portable evaluator's `--session` records and explicit extension arguments. A new budget does not change the frozen objective.

For machine labels such as route IDs, declare the public enum in the performing request before using exact comparison. Otherwise evaluate the intended meaning. A hidden preferred label is not a valid oracle for an underspecified response.
