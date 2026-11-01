# Write a skill README for its users

The README explains what the installed skill does and how to use it. Keep implementation plans, conversation history, deferred ideas, raw evaluations, and authoring decisions outside the public guide.

## Documentation contract

Every created skill needs a useful summary, runtime requirements, concrete host installation instructions, a quick-start request and expected result, representative scenarios, verification commands, troubleshooting, and a support path. Include Git clone instructions when the repository URL is known. Explain how to create an upload ZIP when that installation route needs one. Explicitly invoke the skill in every usage scenario, using the syntax supported by the host. Include license information only when the license is known.

Explain how to supply inputs and desired outputs, define acceptance criteria, execute evaluations, interpret counts and percentages, diagnose failures, improve a candidate, and rerun the same criteria. Distinguish installation checks from task-quality assessment. Explain both task-success and coverage denominators, pending semantic review, and critical failures. Scale fixtures to the task; include a normal case and a relevant variation or error case.

Keep setup for a particular usage scenario within that scenario. For creation from paired examples, explain each input file, desired-output file, and manifest, how their paths connect, and the import step before the invocation. Keep evaluation instructions focused on running checks against an existing candidate, reading results, and improving failures; they must also work for skills created without paired examples. Use the scenario's structured `steps` for multi-step walkthroughs.

Describe actual capabilities and interfaces. Separate host invocation from terminal commands. Use real file names, distinguish placeholders, and make input/output examples consistent with the task contract. Do not advertise commands, dependencies, installation methods, or outcomes that the package cannot support.

The shared renderer creates the README from `config/documentation.json`. The builder uses the same renderer for its own README. The schema lives in `scripts/runtime/contracts.py`; public rendering and checks live in `scripts/runtime/readme.py`.

Use `readme --package FOLDER --check` to check the generated content and documented script paths. Run relevant installation, setup, verification, and usage commands in an exported copy. Read the rendered guide as a new user; a complete heading list does not establish that the instructions work.

## Source and installed copies

Use the README's `## Documentation` section for repository navigation, public development instructions, and worked examples. Preserve that section and its linked files in installed copies and upload ZIPs: the complete repository is the artifact. Apply grader filtering only in disposable evaluation staging; it must not change the source repository or installed artifact.

Every public local link must resolve within the selected distribution. Excluding a private file from a ZIP while linking to it from the README still produces a broken guide.

This is the project's documentation contract, based on [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). The [Agent Skills specification](https://agentskills.io/specification) defines the agent-facing `SKILL.md` and supporting resources; it does not mandate a universal README outline.

The skill repository itself is installed. Show one root README, SKILL and LICENSE. Put Python dependency paths under scripts/; do not advertise separate source/runtime trees or a dist directory.
