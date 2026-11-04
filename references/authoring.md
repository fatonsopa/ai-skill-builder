# Create a skill from a task and evidence

Start with the task's users, triggering requests, inputs, expected results, constraints, and important failure cases. Use available conversations and project files before asking for information again. Separate demonstrated requirements from assumptions; examples alone may not determine a general rule.

## Shape a useful capability

Ground the procedure in actual task outputs, corrections, project conventions and known failures. Choose one coherent capability that users can select and evaluate; [skill structure](skill_structure.md) owns package boundaries. Give a working default and the condition for choosing an alternative. Explain reusable steps rather than prescribing the answer to one example. Include the domain facts and pitfalls the agent would otherwise miss, with enough detail to perform the task.

Match control to the operation: fragile steps need precise inputs, order and checks; judgment can allow supported alternatives. Keep the root focused on the common path. Put conditional detail in existing references with an explicit reading trigger, and retain essential precautions where they will be seen before the action. Review real traces for irrelevant reading, unnecessary branches and repeated mistakes before adding more instructions.

Use [Agent Skills best practices](https://agentskills.io/skill-creation/best-practices) for these authoring decisions. Read its relevant sections when creating or materially changing a capability, and record the source/date and decision; do not copy every suggested pattern into every skill.

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

For agent-based designs, use [agents, skills and orchestration](agents_and_skills.md) when selecting roles, delegation contracts and host-specific resources.

## Describe when the skill applies

State the user's intent, matching requests and meaningful exclusions in the description. Keep implementation detail in the body and preserve approved metadata. Read [description guidance](https://agentskills.io/skill-creation/optimizing-descriptions) when changing selection behavior. It recommends imperative phrasing, while [Anthropic's description guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices#writing-effective-descriptions) recommends third person. These recommendations do not establish one grammar for every host. Follow actual host requirements and assess realistic selection requests using [evaluation](evaluation.md#test-activation-separately-from-performance). Preserve an explicit-invocation boundary where the skill requires it.

Freeze the requested deliverable, allowed edits, definition of done, validation scope and cumulative budget using [the completion contract](maintenance.md#freeze-the-delivery-contract). Include only checks needed for the actual change and claim. Keep later improvements as follow-ups; a material addition needs a recorded scope decision. Budget all versions together and move to delivery once the agreed work passes.

## Decide what belongs in code

Encode parsing, transformations, file handling, state, schemas, literals, identifiers, required structure, scoring, and stopping rules when their behavior can be defined. Reuse suitable commands. Explain residual AI responsibilities, such as interpreting a novel brief or judging supported prose. An unconstrained prompt behind a script is not an executable contract.

For an AI-assisted runtime, define what enters the AI stage, which structured output returns, what code verifies, and what happens on refusal, malformed output, or uncertainty. Supply the required implementation with the skill, or declare an available supported dependency. The builder's optional CLI model helper generates phase responses; it does not supply a universal runtime to every generated skill.

## Define script interfaces

When adding or changing commands, read [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts). Reuse a suitable existing command; bundle a script when repeatable logic warrants it. State the runtime, required tools, dependency versions and invocation directory. Pin external package versions where reproducibility matters, while retaining the project's established dependency mechanism.

Provide concise `--help` with supported arguments, defaults and examples. Accept inputs through arguments, files, environment or stdin without waiting for a terminal prompt; required inputs should fail clearly. Keep structured results on stdout and diagnostics on stderr. Explain what failed, what input was expected and the supported next step; use documented nonzero exit codes for failure. Bound large output or write it to a file.

For stateful operations, define safe defaults, applicable preview support and retry behavior before execution. A noninteractive flag does not grant authority for an external action. Test the actual interface, missing prerequisites, invalid inputs and failures; do not invent flags for an existing command.

## Learn from paired examples

Use `examples --manifest PAIRS.json --output BUNDLE_DIR`. Each pair declares `id`, `source_family`, `input` and `output` paths, `split`, and `provenance`. Splits are `development`, `regression`, or `protected`; provenance is `real` or `synthetic`.

The current adapters support JSON, UTF-8 text, and Markdown. They preserve original copies and extracted values. Other document formats require a verified adapter; report unsupported formats instead of silently dropping their structure.

Set the request's `examples` field to the bundle directory. Authoring packets omit protected pairs. The runner rejects cross-split family labels and exact duplicate content; semantic near duplicates still need review. Keep protected material out of candidate resources and use verified external isolation where confidentiality matters.

Infer transformations, invariant values, acceptable variation, and unknowns. Test new values and boundary conditions. For structured data, turn preservation promises into typed invariants before selecting a parser or serializer. Exercise retained fields, null and absent values, nesting, Unicode and numeric precision where the contract permits them. A present field with an explicit null value is distinct from an absent field unless the actual contract equates them. A rule requiring a string or integer does not make null a missing field; derive the invalid-type and missing-input tests separately from the supplied rules. A parse-and-write round trip can change a value even when the main transformation is correct. Check value preservation separately from formatting, using a comparator that does not lose the same information as the implementation. A synthetic variant is not independent ground truth. One pair cannot establish broad generalization or justify an invented target.

## Assemble and verify

During `produce`, supply the description, instructions, usage, and task-specific files. For creation and rebuilding, code renders `SKILL.md`, `README.md`, the evaluation suite, and the portable evaluator. It prevents direct replacement of those managed files. Resource declarations control the generated routing.

For narrow maintenance, `files` and optional `remove` modify only authorized paths on a captured source copy. Keep custom content and host metadata unless the requested change affects them. A rebuild is appropriate when generation must replace the whole managed structure.

Use Technical Writer for document authoring and review, then complete [document validation](technical_writer.md). Use a different scenario to test transfer. Evaluate the candidate independently before delivery; file generation is not evidence that its language, decisions, installation, or model behavior are correct.

## Repository and domain contract

Apply [skill structure](skill_structure.md). Declare focused domains, responsibilities, owned paths and dependencies in the plan. Code owns file mechanics; source-grounded review judges cohesion and coupling. New skills need the supplied copyright holder before the approved MIT template is rendered. The repository must install and test independently of Builder.

Before declaring the generated checks usable, run the scoped test entry point for an actual runtime file and a shared implementation dependency. Confirm that it selects the relevant controls and excludes an independent component. A mapping for the test script alone does not establish coverage of the code it exercises. The generator follows declared domain ownership and dependencies; compare those declarations with actual imports and consumers. Resolve unmapped implementation files with an accurate dependency or impact rule, never a full-suite fallback.

## Inventory processes and build their tests

Each new skill declares its workflows with triggers, steps and applicable boundaries, branches and recovery paths. During maintenance, inventory the workflows affected by the change and preserve unrelated contracts and cases. During a whole-skill audit or rebuild, inspect the complete inventory against the actual instructions; listing one broad phase cannot hide a multi-step process.

Choose workflow boundaries from how the capability is invoked and completed. A clarification that continues the same review can be a branch of that review; a separately invoked operation with its own result remains a workflow. Preserve the branch's steps, evidence and failure tests either way. Do not split every helper command into a workflow or combine independent operations merely to reduce test obligations.

Before freezing the plan, check that its mandatory fresh trials fit the supplied execution bounds. Record each bound's source and scope, the required cases, the specialist calls and rounds each needs, and the combined total. Account for a case that needs more than one worker and for any separately required hosts. If an actual requirement cannot fit, report the conflict before production or calls; do not commit to an impossible acceptance plan and request more calls after spending the allowance. [Evaluation](evaluation.md#preserve-the-scope-of-execution-bounds) explains how to keep local controls, a scoped pilot and broader host claims distinct.

Each workflow needs a valid execution test and an AI behavioral case tied to its intent. A multi-step process also needs an omission test for every step and order tests for adjacent phases, plus checks for each declared boundary, branch and recovery path. One case may cover several related checks when its actual execution supports that coverage. Simple one-step transformations use meaningful valid/invalid-input tests without artificial phases. Every process case is mandatory.

Command or artifact tests establish mechanical properties. Behavioral cases use `kind: behavior`, a realistic `request`, relevant `resources`, and semantic assessment. They must evaluate what the skill should accomplish, not merely repeat its instructions or look for keywords. A multi-step mechanical success case also captures its full event order and required evidence/visibility, then receives semantic review of those actual artifacts.

Prepare and review the cases and graders before running them. Deliberately wrong paths must be detectable. Fresh task outputs come from a performing AI, not from the skill author writing a desired answer. Keep expected answers and grading criteria out of the performing packet. Preserve each attempt, including malformed output and workflow violations; do not rename these as infrastructure failures.

For an output workflow whose final summary can introduce unchecked facts, return a concise checked handoff from the delivery code. Keep the substantive explanation in the reviewed artifact. Test a matching actual handoff, an altered final message, missing evidence and changed delivered bytes; inspect the real host trace as well as any saved copy. Apply this boundary where it serves the task rather than prescribing a canned response for every skill.

## Source review

The linked Agent Skills authoring, description and script sections, and Anthropic description guidance, were opened on 2026-11-03. Consult current primary guidance for the decision being changed; [host support](host_support.md#discovery-and-loading) owns client-specific loading responsibilities.
