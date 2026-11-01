# Skill structure and domain boundaries

The source of truth is [the repository layout contract](../config/repository_layout.json). This project requires more than the minimum Agent Skills format: every skill is its own repository, directly installable from its root, with one `SKILL.md`, one `README.md`, a `LICENSE`, and shared repository instructions in `AGENTS.md` imported by `CLAUDE.md`. The repository is the artifact. Create only resource folders the task needs; do not create a separate distribution or duplicate runtime tree.

## Assign responsibilities

A skill owns one coherent capability. Split distinct capabilities when they have different users, triggers, inputs, outputs or acceptance rules. Within a skill, give each component one responsibility and a clear interface. Keep domain rules independent of provider execution, installation and evaluation. Use small modules when complexity warrants them; this does not require network services or a folder per function.

- `SKILL.md` routes and coordinates the work.
- `references/` owns domain knowledge and writing guidance; examples demonstrate it without becoming a competing rule source.
- `scripts/` owns deterministic transformations and validation. Put its dependency declarations here.
- `evals/` owns cases, source fixtures, rubrics and acceptance evidence. Development tests can live in `tests/` or beside the scripts.
- `config/` owns required machine configuration and generated bookkeeping. Public guidance belongs in the README or references.
- Host adapters translate execution requests. They must not redefine domain rules or acceptance criteria.

Plans declare each domain's purpose, owned resource paths and dependencies. Code checks names, ownership, paths and dependency cycles. Review actual responsibilities and code imports as well: a directory name is not proof of separation of concerns. Keep shared rules in one authoritative file and derive or cross-check their consumers.

## Audit and repair existing skills

Run `scripts/repository_layout.py --package PATH` and include its located findings in the audit. The phase packet also supplies this report. Inspect purpose, ownership, coupling and duplicated rules before choosing moves. For an authorized repair, use the refactor workflow with `repair_structure: true` and explicit old and new paths, update every consumer, preserve a before-image, and archive private records outside the repository. Resolve collisions rather than overwriting unrelated content. Never call a file deletion a migration without preserving its required information.

A narrow modification reports unrelated structure debt without widening its permission. A requested structural refactor must meet this contract before acceptance. Test installation from the repository alone, without the Builder checkout, and check that the host discovers one entry point.

## License and delivery

Use MIT by default for new skills, with the supplied copyright holder and current year. Use the approved template; do not invent legal terms or author identity. Preserve an existing license unless its owner authorizes a change. Verify a nonempty root LICENSE and public installation, invocation, evaluation and support instructions. Keep prompts, migration notes, audit history and run snapshots outside the published skill.

The [Agent Skills specification](https://agentskills.io/specification) defines the interoperable skill format. The root README/LICENSE, repository layout and domain declarations above are this Builder's delivery contract. [MIT license text](https://opensource.org/license/mit).

[OpenAI skill structure](https://learn.chatgpt.com/docs/build-skills) and [Anthropic authoring guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) both support concise instructions and resources loaded as needed. Add only folders with a concrete responsibility; schema and evaluation files below config/ are Builder implementation choices, not host requirements. Reusable output templates belong in assets/.

## Repository collaboration rules

Generate AGENTS.md and CLAUDE.md for every new skill. AGENTS.md owns the shared rules; CLAUDE.md imports it with `@AGENTS.md`, following [Claude Code's documented import pattern](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools). These are repository maintenance instructions, separate from SKILL.md's task workflow.

Run impacted tests during editing and the full relevant suite for the final candidate before commit/push. Push only after the user's explicit approval covering the completed batch. Preserve project-specific instructions when rebuilding, reconcile conflicts with current authorization, and review both instruction files before accepting delivery.
