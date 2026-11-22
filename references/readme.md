# Public documentation contract

Use the required `technical-writer` skill for document guidance and acceptance. This reference defines Skill Builder’s generated package interface; the renderer and schema enforce that interface.

## Documentation contract

For every skill README, open `references/readme.md` in the resolved Technical Writer dependency and apply its “Decide what belongs in the README” guidance to both authored profiles. Follow the [dependency resolution steps](technical_writer.md#before-you-begin). The root README contains the first usable path. Put additional public guides in `docs/` by default and link directly to them from the README. Reuse the project’s existing documentation location where appropriate. Create an additional page only when a reader needs it.

Keep supported setup, examples, evaluation procedures, coverage definitions, recovery and support discoverable in the distributed package. A direct link from the root to the relevant section satisfies that obligation. Keep detailed fixture and evaluation instructions with their actual procedures. Verify the first request has its prerequisites in reading order and an observable result. Preserve these links and their targets in both source and installed copies.

Keep setup for a particular usage scenario within that scenario. For creation from paired examples, explain each input file, desired-output file, and manifest, how their paths connect, and the import step before the invocation. Keep evaluation instructions focused on running checks against an existing candidate, reading results, and improving failures; they must also work for skills created without paired examples. In legacy version 1 records, use the scenario's structured `steps` for multi-step walkthroughs. In version 2, author those walkthroughs in the complete documentation profiles.

The shared renderer creates the `README.md` from `config/documentation.json`. The builder uses the same renderer for its own `README.md`. The schema lives in `scripts/runtime/contracts.py`; public rendering and checks live in `scripts/runtime/readme.py`.

Use `readme --package FOLDER --check` to check the generated content and documented script paths. Run relevant installation, setup, verification, and usage commands in an exported copy. Complete [Technical Writer validation](technical_writer.md) on the rendered output.

## Source and installed copies

Use the `README.md` file’s `## Documentation` section for repository navigation, public development instructions, and worked examples. Preserve that section and its linked files in installed copies and upload ZIPs: the complete repository is the artifact. Apply grader filtering only in disposable evaluation staging; it must not change the source repository or installed artifact.

Every public local link must resolve within the selected distribution. Excluding a private file from a ZIP while linking to it from the `README.md` still produces a broken guide.

This is the project's documentation contract, based on [GitHub's README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes). The [Agent Skills specification](https://agentskills.io/specification) defines the agent-facing `SKILL.md` and supporting resources; it does not mandate a universal document outline.

The skill repository itself is installed. Show one root `README.md`, `SKILL.md` and `LICENSE`. Put Python dependency paths under scripts/; do not advertise separate source/runtime trees or a dist directory.

## Version 2 authored documentation

New authoring supplies `documentation.schema_version: 2`, its responsible `owner`, complete authored `profiles.source` and `profiles.runtime`, and structured `commands` for bundled-path checks. Technical Writer-guided agents author and review the substantive text, qualifiers, setup, acceptance and retry guidance. Code copies the selected profile exactly; it adds no substantive wording. Both profiles are required, even when identical. Missing sections remain failures of the complete Technical Writer contract.

Existing version 1 records retain their compatibility renderer and original evidence. Migrate by authoring and reviewing complete profiles that preserve applicable custom text and source/runtime scope, then obtain new acceptance bound to the resulting document. Merely copying hidden strings into a file without a responsible owner and applicability review is not a completed migration. The current Builder documentation uses version 2.

A native skill needs only the installation and checks its capability supports. Document manual native installation or available host tools when sufficient; do not advertise absent scripts. A maintained skill may bundle selected mechanics with explicit requirement-based justification and their required dependencies. Code checks declared paths; semantic review confirms the package preserves outcomes and safeguards.
