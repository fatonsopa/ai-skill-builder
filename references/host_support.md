# Use the skill on its host

Use the model already available in ChatGPT, Claude, Codex, or Claude Code. Record an unavailable exact model identity as unknown. Normal use does not require another provider's CLI or credentials.

## Install and invoke

The public README contains the installation commands and host requirements. Install the repository folder or download its GitHub ZIP. Use /skill-builder in Claude Code, @skill-builder in ChatGPT desktop, or $skill-builder in Codex. Every usage scenario must explicitly invoke the selected skill.

Native handoff lets the current host read a typed phase packet, perform the requested judgment or research with its tools, and submit the response through the same Python runner. The default model command emits that handoff without starting an external CLI. Populate host context from the actual session rather than credentials, file paths, or guessed model IDs.

Executable steps require Python, file access, and declared dependencies. If a host cannot execute a step, report the specific missing capability and keep that result unverified. Local standalone skill support does not imply installation support on every browser or mobile surface. Check current host instructions when installing.

## One repository artifact

The repository root is the installable skill. Its README, SKILL, LICENSE, references, scripts, configuration, tests and evals stay together. There are no separate source/runtime trees or distribution manifest. Local environments and private records are excluded from installation; internal histories stay outside the repository. See [skill structure](skill_structure.md).

An optional host-upload ZIP contains those same public files and must be written outside the repository. It does not create a dist directory or a separate maintained copy. Installation and publishing remain distinct actions.

## Evaluation and continuation

Use explicit model configurations for optional external comparisons. A cross-provider route needs a configured choice. Preserve model-specific results, missing coverage, and failed attempts.

Routine testing includes necessary retries. Select bounded batches from task complexity and observed runtime, preserve failed attempts and criteria, and continue without asking for each extra test. Use the shared continuation guard for extensions and record the concrete reason. Use up to five testing rounds, including the initial round and at most four bounded continuations, each adding up to two attempts, four handoffs, four model invocations or fifteen minutes as applicable. These are local defaults; explicit user hard limits take precedence. Stop and report stalled progress or exhausted retry ceilings. A different scope, permission or paid-service arrangement still needs the appropriate user decision.

Generated skills have a portable evaluator and bounded maintenance session. Store its records outside the skill folder, review pending semantic cases, and export an accepted version to a new destination. Do not silently modify the installed skill during ordinary use.
