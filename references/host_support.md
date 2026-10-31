# Use the skill on its host

Use the model already available in ChatGPT, Claude, Codex, or Claude Code. Record an unavailable exact model identity as unknown. Normal use does not require another provider's CLI or credentials.

## Install and invoke

The public README contains the installation commands and host requirements. Install the runtime skill folder or ZIP. Use /skill-builder in Claude Code, @skill-builder in ChatGPT desktop, or $skill-builder in Codex. Every usage scenario must explicitly invoke the selected skill.

Native handoff lets the current host read a typed phase packet, perform the requested judgment or research with its tools, and submit the response through the same Python runner. The default model command emits that handoff without starting an external CLI. Populate host context from the actual session rather than credentials, file paths, or guessed model IDs.

Executable steps require Python, file access, and declared dependencies. If a host cannot execute a step, report the specific missing capability and keep that result unverified. Local standalone skill support does not imply installation support on every browser or mobile surface. Check current host instructions when installing.

## Runtime and source distributions

The runtime distribution contains the skill, required scripts, references, metadata, dependency declarations, README, and compact runtime checks. The source distribution adds development tests and tools. A declared distribution profile selects files explicitly; excluded private records are not copied into either public profile.

Use package --profile runtime for installation and --profile source for a source archive. No global installation or external publishing occurs during packaging.

## Evaluation and continuation

Use explicit model configurations for optional external comparisons. A cross-provider route needs a configured choice. Preserve model-specific results, missing coverage, and failed attempts.

When a target is unmet and a budget is exhausted, report the best metrics and remaining failures. Recommend bounded additional iterations and runtime from observed effort and progress, and ask before extending. Preserve acceptance criteria and prior results. A budget receipt must represent the user's actual instruction.

Generated skills have a portable evaluator and bounded maintenance session. Store its records outside the skill folder, review pending semantic cases, and export an accepted version to a new destination. Do not silently modify the installed skill during ordinary use.
