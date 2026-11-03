# Use the skill on its host

Use the model already available in ChatGPT, Claude, Codex, or Claude Code. Record an unavailable exact model identity as unknown. Normal use does not require another provider's CLI or credentials.

## Install and invoke

The public `README.md` contains the installation commands and host requirements. Install the repository folder or download its GitHub ZIP. Use /skill-builder in Claude Code, @skill-builder in ChatGPT desktop, or $skill-builder in Codex. Every usage scenario must explicitly invoke the selected skill.

Native handoff lets the current host read a typed phase packet, perform the requested judgment or research with its tools, and submit the response through the same Python runner. The default model command emits that handoff without starting an external CLI. Populate host context from the actual session rather than credentials, file paths, or guessed model IDs.

Executable steps require Python, file access, and declared dependencies. If a host cannot execute a step, report the specific missing capability and keep that result unverified. Local standalone skill support does not imply installation support on every browser or mobile surface. Check current host instructions when installing.

## Discovery and loading

Read [the Agent Skills client guide](https://agentskills.io/client-implementation/adding-skills-support) when a task changes discovery, activation or context handling. The client discovers skill locations, parses metadata, presents the catalog, loads the selected instructions and makes referenced resources available. It also manages duplicate activations and retained skill context as the conversation grows. These are client responsibilities; authoring a skill normally uses an existing host and does not require a custom client, daemon or service.

Keep references behind clear reading triggers instead of loading the entire package at startup. Inspect the target host's actual discovery locations, supported explicit/implicit invocation, resource permissions and context behavior. The portable format does not mandate one installation directory or guarantee identical host behavior. Optional subagent activation does not require delegation; use [agents and skills](agents_and_skills.md) when distinct roles are justified.

Verify discovery or explicit loading separately from installed file identity and task performance. Preserve any unsupported capability as an evidence gap. The client guide and [OpenAI skill guidance](https://learn.chatgpt.com/docs/build-skills) were opened on 2026-11-03; check current host documentation before relying on host-specific behavior.

## One repository artifact

The repository root is the installable skill. Its `README.md`, `SKILL.md`, `LICENSE`, references, scripts, configuration, tests and evals stay together. There are no separate source/runtime trees or distribution manifest. Local environments and private records are excluded from installation; internal histories stay outside the repository. See [skill structure](skill_structure.md).

An optional host-upload ZIP contains those same public files and must be written outside the repository. It does not create a dist directory or a separate maintained copy. Installation and publishing remain distinct actions.

## Distinguish failed attempts from missing observations

An actual attempted task that times out is failed, even if its public trace is partial or its cause is unknown. Keep that failure in history. “Not run” means the task was not attempted or no actual observation was supplied; it must not replace an observed timeout. Incomplete diagnostic evidence does not erase an execution outcome. Retry the unchanged case when evidence supports more runtime; a retry does not itself require a code change.

## Evaluation and continuation

Use explicit model configurations for optional external comparisons. A cross-provider route needs a configured choice. Preserve model-specific results, missing coverage, and failed attempts.

Routine testing includes necessary retries. Select bounded batches from task complexity and observed runtime, preserve failed attempts and criteria, and continue without asking for each extra test. Use the shared continuation guard for extensions and record the concrete reason. Use up to five testing rounds, including the initial round and at most four bounded continuations, each adding up to two attempts, four handoffs, four model invocations or fifteen minutes as applicable. These are local defaults; explicit user hard limits take precedence. Stop and report stalled progress or exhausted retry ceilings. A different scope, permission or paid-service arrangement still needs the appropriate user decision.

Generated skills have a portable evaluator and bounded maintenance session. Store its records outside the skill folder, review pending semantic cases, and export an accepted version to a new destination. Do not silently modify the installed skill during ordinary use.

## Validate each required execution host

Before claiming multi-host readiness, freeze the intended host/case matrix with `scripts/host_coverage.py freeze --package PACKAGE --config config/host_validation.json --output PLAN.json`. The shared matrix requires Codex and Claude Code as execution hosts; it does not establish browser/mobile or every model support. Run each selected task through its actual skill with tools on each declared host. Keep the same task criteria, source artifact, public trace and actual outputs; record requested and observed model identity separately. Capture a source-grounded review bound to each report, attempt and public trace, then use `scripts/host_coverage.py assess --package PACKAGE --plan PLAN.json --bundles BUNDLES.json --output NEW_REPORT.json`. Missing hosts, unreviewed outputs, stale artifacts and failed critical cells prevent matrix acceptance. Native use and single-host testing remain available with their scope stated.

Freeze the intended model and reasoning settings as well as the execution hosts. The matrix config accepts `profiles`, with one `{host, model, reasoning_effort}` object per required host; unavailable identities stay null. Assessment rejects different configurations in one host result. Keep each model/effort profile separate rather than selecting passing subsets from different models. Before a broad batch, pilot an actual task matching the skill's intended output; for Skill Builder that includes creating a usable skill from supplied input/output examples, not only explaining an audit or plan.
