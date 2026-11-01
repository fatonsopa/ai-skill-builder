# Create a skill from a task and evidence

Start with the task's users, triggering requests, inputs, expected results, constraints, and important failure cases. Use available conversations and project files before asking for information again. Separate demonstrated requirements from assumptions; examples alone may not determine a general rule.

## Research, specify, and plan

Inspect an existing package before proposing replacements. Research current official host documentation and domain uncertainties that affect this task. Record the source, date, relevant decision, and whether it was actually opened. Report unsupported claims as unverified. The runner records these statements; it does not independently prove that browsing occurred.

The research response leads to a specification containing purpose, inputs, outputs, stable requirement IDs, a workflow inventory, assumptions, and material ambiguities. Resolve the ambiguities before advancing. Then plan executable mechanics, residual AI responsibilities, dependencies, resource purposes, acceptance cases, and the permitted candidate edit surface.

Use `schema PHASE` for exact fields. Each response includes the packet's `run_id`, `phase`, `packet_sha256`, and typed `data`. A response for a stale packet cannot advance the run.

The CLI uses these operations:

| Operation | Result |
| --- | --- |
| `create` | New package |
| `modify` | Intended changes within exact allowed paths |
| `refactor` | Reorganization preserving the agreed behavior |
| `rebuild` | Recreated package compared with its preserved source |
| `audit` | Findings and a retain/modify/refactor/rebuild recommendation |
| `specify` or `plan` | Requested planning artifact; no implementation |

Stage evidence can reuse current research and decisions for a narrow edit. Record what was reused; do not invent checks or burden an ordinary edit with unrelated research.

## Decide what belongs in code

Encode parsing, transformations, file handling, state, schemas, literals, identifiers, required structure, scoring, and stopping rules when their behavior can be defined. Reuse suitable commands. Explain residual AI responsibilities, such as interpreting a novel brief or judging supported prose. An unconstrained prompt behind a script is not an executable contract.

For an AI-assisted runtime, define what enters the AI stage, which structured output returns, what code verifies, and what happens on refusal, malformed output, or uncertainty. Supply the required implementation with the skill, or declare an available supported dependency. The builder's optional CLI model helper generates phase responses; it does not supply a universal runtime to every generated skill.

## Learn from paired examples

Use `examples --manifest PAIRS.json --output BUNDLE_DIR`. Each pair declares `id`, `source_family`, `input` and `output` paths, `split`, and `provenance`. Splits are `development`, `regression`, or `protected`; provenance is `real` or `synthetic`.

The current adapters support JSON, UTF-8 text, and Markdown. They preserve original copies and extracted values. Other document formats require a verified adapter; report unsupported formats instead of silently dropping their structure.

Set the request's `examples` field to the bundle directory. Authoring packets omit protected pairs. The runner rejects cross-split family labels and exact duplicate content; semantic near duplicates still need review. Keep protected material out of candidate resources and use verified external isolation where confidentiality matters.

Infer transformations, invariant values, acceptable variation, and unknowns. Test new values and boundary conditions. A synthetic variant is not independent ground truth. One pair cannot establish broad generalization or justify an invented target.

## Assemble and verify

During `produce`, supply the description, instructions, usage, and task-specific files. For creation and rebuilding, code renders `SKILL.md`, `README.md`, the evaluation suite, and the portable evaluator. It prevents direct replacement of those managed files. Resource declarations control the generated routing.

For narrow maintenance, `files` and optional `remove` modify only authorized paths on a captured source copy. Keep custom content and host metadata unless the requested change affects them. A rebuild is appropriate when generation must replace the whole managed structure.

Check complete output examples where depth matters, and use a different scenario to test transfer. Review all prose using the writing guide. Evaluate the candidate independently before delivery; file generation is not evidence that its language, decisions, installation, or model behavior are correct.

## Repository and domain contract

Apply [skill structure](skill_structure.md). Declare focused domains, responsibilities, owned paths and dependencies in the plan. Code owns file mechanics; source-grounded review judges cohesion and coupling. New skills need the supplied copyright holder before the approved MIT template is rendered. The repository must install and test independently of Builder.

## Inventory processes and build their tests

Each new skill declares its workflows with triggers, steps and applicable boundaries, branches and recovery paths. During maintenance, inventory the workflows affected by the change and preserve unrelated contracts and cases. During a whole-skill audit or rebuild, inspect the complete inventory against the actual instructions; listing one broad phase cannot hide a multi-step process.

Each workflow needs a valid execution test and an AI behavioral case tied to its intent. A multi-step process also needs an omission test for every step and order tests for adjacent phases, plus checks for each declared boundary, branch and recovery path. One case may cover several related checks when its actual execution supports that coverage. Simple one-step transformations use meaningful valid/invalid-input tests without artificial phases. Every process case is mandatory.

Command or artifact tests establish mechanical properties. Behavioral cases use `kind: behavior`, a realistic `request`, relevant `resources`, and semantic assessment. They must evaluate what the skill should accomplish, not merely repeat its instructions or look for keywords. A multi-step mechanical success case also captures its full event order and required evidence/visibility, then receives semantic review of those actual artifacts.

Prepare and review the cases and graders before running them. Deliberately wrong paths must be detectable. Fresh task outputs come from a performing AI, not from the skill author writing a desired answer. Keep expected answers and grading criteria out of the performing packet. Preserve each attempt, including malformed output and workflow violations; do not rename these as infrastructure failures.
