# Skill Builder

Create and improve reusable AI skills with executable workflows, focused references, and evaluations. Audit an existing skill, make a scoped change, or build a new skill from a brief and input/output examples.

## Requirements

- Python 3.11 or later on macOS, Linux, or WSL.
- A host with code execution and file access: ChatGPT desktop/Codex, Claude, or Claude Code.
- The Python packages declared in requirements-lock.txt. External model CLIs are optional.

## Installation

### Get the skill

Clone the repository, then enter the skill folder:

```sh
git clone https://github.com/fatonsopa/ai-skill-builder skill-builder
```

```sh
cd skill-builder
```

You can also download the repository ZIP from GitHub's Code menu and extract it.

### ChatGPT desktop and Codex

For a filesystem-enabled ChatGPT desktop/Codex workspace, run:

```sh
python3 scripts/install_skill.py --host codex
```

The installer copies the runtime files to `~/.agents/skills/skill-builder/`. Start a new chat and select `@skill-builder` in ChatGPT desktop or invoke `$skill-builder` in Codex. In the desktop app, Skills is available from the sidebar. This installation uses local skill support; it does not install a browser or mobile add-on.

### Claude Code

```sh
python3 scripts/install_skill.py --host claude-code
```

The destination is `~/.claude/skills/skill-builder/`. Start a new Claude Code session and invoke `/skill-builder`.

### Claude

Create the upload ZIP from the extracted skill folder:

```sh
python3 scripts/install_skill.py --archive ../skill-builder.zip
```

Upload `../skill-builder.zip` through Claude's custom-skills settings: Customize → Skills → Create skill → Upload a skill. Newer layouts may show Skills under Plugins. Enable code execution and file creation, then enable the uploaded skill. [Claude's upload instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

### Set up runtime dependencies

After a local installation, change to the destination printed by the installer. Run the following commands there, or ask the host to run them with its code tools:

```sh
python3 -m venv .venv
```

```sh
.venv/bin/python -m pip install -r requirements-lock.txt
```

```sh
.venv/bin/python scripts/smoke_check.py
```

## Quick start

Explicitly invoke the skill before giving it a task. Examples below use `/skill-builder`. Use `@skill-builder` in ChatGPT desktop and `$skill-builder` in Codex.

> /skill-builder Use Skill Builder to audit the attached skill. Report concrete problems and recommended fixes without editing its files.

You receive located findings, their consequences, and a recommendation to retain, modify, refactor, or rebuild the skill. The source files stay unchanged.

## Usage scenarios

### Create a new skill

> /skill-builder Create a skill that turns release notes and issue descriptions into a weekly engineering update. Preserve issue IDs, link each claim to its source, and include examples and evaluations.

The builder establishes the input/output contract and acceptance criteria, creates a candidate skill with the needed scripts and guidance, evaluates it, and delivers the accepted package with its README.

### Build from input/output examples

Use this when you can show what the skill will receive and the result it should produce. This walkthrough builds a bug-report skill from one example. All commands start in the installed Skill Builder folder.

| File | What you put in it |
| --- | --- |
| `input.json` | The original facts the future skill receives. |
| `expected.md` | The complete report you want it to write from those facts. |
| `pairs.json` | An index linking the input file to its desired-output file. |

#### 1. Create a folder for your examples

Keep these files outside the installed skill. Save all three in the same folder:

```sh
mkdir -p ../skill-data
```

#### 2. Save the input and the desired output

`input.json` contains the source facts. `expected.md` is the exact report you want the new skill to produce, including its headings and wording. These are example data, not instructions for Skill Builder.

Save as `../skill-data/input.json`:

```json
{
  "title": "Category changes are not saved",
  "steps": [
    "Open the review dialog.",
    "Choose a different category.",
    "Click Save."
  ],
  "expected": "The new category is saved.",
  "actual": "The dialog closes, but the previous category remains."
}
```

Save as `../skill-data/expected.md`:

```text
# Category changes are not saved

## How to reproduce

1. Open the review dialog.
2. Choose a different category.
3. Click Save.

## Expected result

The new category is saved.

## Actual result

The dialog closes, but the previous category remains.

## Relevant files

Not provided.
```

#### 3. Link them in pairs.json

Each row describes one input/output pair. The `input` and `output` values are file paths relative to `pairs.json`; they point to the two files you just saved.

`id` identifies this pair. `source_family` groups related examples so they stay in the same data split. `split: development` allows this pair to guide skill creation. `provenance: synthetic` means this example was invented; use `real` for an actual case.

Save as `../skill-data/pairs.json`:

```json
[
  {
    "id": "category-save",
    "source_family": "review-dialog",
    "input": "input.json",
    "output": "expected.md",
    "split": "development",
    "provenance": "synthetic"
  }
]
```

#### 4. Import the pair

The command checks the file links and creates `../skill-data/paired-data/`, containing an `examples.json` index and copies of the original files. It leaves your three files unchanged.

```sh
.venv/bin/python scripts/skill_builder_cli.py examples --manifest ../skill-data/pairs.json --output ../skill-data/paired-data
```

Then invoke the skill:

> /skill-builder Build a bug-report skill from ../skill-data/paired-data. Preserve the supplied facts, use the report structure in expected.md, and mark missing relevant files without inventing paths. Agree acceptance criteria and a target before evaluating. Return the run directory with the results.

You receive a candidate skill, its README, evaluation results, and a run-directory path. Add more pairs for different behaviors and keep independent evaluation cases separate. One demonstration explains the task; it does not establish reliability on unseen inputs.

### Audit an existing skill

> /skill-builder Audit the attached documentation skill. Check its routing, writing guidance, executable checks, and output coverage. Do not change the source.

Findings identify actual files and affected behavior. Existing tests can be run in a separate copy, and results remain separate from claims about writing quality.

### Make one focused improvement

> /skill-builder Improve the bug-report guidance so Expected result and Actual result are separate sections. Preserve unrelated references, examples, naming, and configuration.

The candidate changes only the authorized files. Relevant checks compare it with the baseline and preserve unrelated behavior.

### Rebuild an existing skill

> /skill-builder Rebuild this skill around executable operations and bounded AI stages. Preserve its valid requirements, supported inputs and outputs, and existing metadata. Compare the replacement with the original.

The builder captures a baseline, reconciles requirements, creates a replacement candidate, compares matching cases, and retains a recovery copy.

### Improve a skill after a failure

> /skill-builder This skill omitted a required section. Fix this output and improve the reusable skill so the same failure is covered by a regression case.

The builder records the observed failure, makes a scoped candidate change, and tests the original case plus relevant neighboring cases. If more effort is needed after the agreed limits, it asks before continuing.

## Verification

```sh
.venv/bin/python scripts/smoke_check.py
```

The result contains passed: true. This checks runtime files, the README contract, dependency-backed input validation, and a real temporary workflow transition. Use the development suite for broader regression testing.

## Evaluate and improve results

Use this after a create, modify, refactor, or rebuild operation has produced a candidate and an evaluation run. The builder returns the run-directory path; use it wherever RUN_DIR appears below. These steps apply whether the skill began from a brief, an existing skill, or paired examples. Audit, specification, and planning operations do not produce a candidate to evaluate.

### Acceptance criteria

- Define the required behavior, output structure, facts to preserve, and relevant invalid inputs before changing the candidate.
- Map every requirement to an executable check or a documented semantic judgment. Include representative tasks, relevant variations, and failure cases.
- Keep independent evaluation cases separate from examples used to create or tune the skill.
- Choose the required task-success percentage, coverage, and critical checks before evaluation. A mandatory failure blocks acceptance even when the aggregate score is high.

### Run the evaluations

Use the evaluation command below. Replace named placeholders with the paths returned by the skill.

```sh
.venv/bin/python scripts/skill_builder_cli.py evaluate --run RUN_DIR --allow-exec
```

### Read the results

| Result field | Meaning |
| --- | --- |
| `task_success_percent` | Accepted task attempts ÷ evaluated attempts × 100 |
| `coverage_percent` | Evaluated attempts ÷ planned attempts × 100 |
| `critical_failures` | Failed non-negotiable requirements; these block acceptance |
| `pending_review` | Outputs that still need a semantic judgment |

For example, 8 accepted attempts out of 10 evaluated attempts gives 80% task success. If 12 attempts were planned, coverage is 83.3%. A missing denominator is reported as not measured. Wrong or malformed task outputs count as failed attempts. Infrastructure gaps reduce coverage. A quality rubric score is reported separately from truth-based accuracy.

A candidate is accepted only when its declared target, coverage, critical checks, and required reviews pass. An installation self-check is not a complete quality assessment of a generated skill.

### Improve and retest

1. Review executable candidate code before using --allow-exec. Read the report returned by the evaluation command.
2. Read each failed attempt, its actual output, source facts, and checker or review findings. Distinguish a skill defect from missing input, an environment failure, or a faulty evaluator.
3. Invoke /skill-builder with the failing input, expected output, actual output, and the requested reusable improvement. Keep the failure as a regression case.
4. Make one scoped change and rerun the same acceptance criteria, relevant neighboring cases, and shared regressions. Preserve the baseline and every attempt.
5. Accept the candidate only when the agreed gates pass. If the run reaches a limit below target, review the evidence and approve or decline a bounded extension.

## Models and run limits

AI work uses the model already available in the current host. The skill records an unknown model identity rather than guessing one. Mechanical operations run through the packaged scripts.

If evaluation remains below target when a run limit is reached, the skill reports the gap and recommends a bounded continuation. Additional iterations or runtime require your approval. Requirements and scoring stay fixed.

## Troubleshooting

### The host cannot find the skill

Confirm that the installed folder is named skill-builder and contains SKILL.md. Start a new session, then explicitly select or invoke the skill.

### A Python dependency is missing

Run the setup commands in the installed skill folder, or ask the host to install requirements-lock.txt in its execution environment. Use .venv/bin/python for the local runner.

### Installation reports that the destination exists

The installer preserves existing installations. Back up or rename the old folder, or pass --destination with a new path.

### Evaluation has not reached the target

Review failed cases and missing coverage. Authorize another bounded batch only when the results justify it. Do not change the target or expected answers to manufacture a pass.

### The chat has no code or file tools

Use a filesystem-enabled workspace or enable the host's code-execution capability. Executable stages cannot be verified in a text-only chat.

## Support

For help with Skill Builder, email the author at **faton.sopa[at]manaferra.com** (replace `[at]` with `@`). Include your host, operation, reproduction steps, expected result, and actual result.

<!-- repository:start -->

## Development

After installing dependencies in the source checkout, run `.venv/bin/python tools/check_repository.py`. It runs the regression suite and checks the README, runtime installation, and distribution boundaries.

- [README conventions](references/readme.md)
- [Testing and development](tests/README.md)

<!-- repository:end -->

<!-- skill-readme:source -->
