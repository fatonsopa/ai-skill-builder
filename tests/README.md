# Test Skill Builder

Install the locked dependencies in a Python environment, then run from the repository root:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/smoke_check.py
.venv/bin/python scripts/skill_builder_cli.py readme --package . --check
```

Use `.venv/bin/python tools/check_repository.py` to run the suite and validate a complete independent repository copy in one command. It also runs the self-check from the copied repository.

The regression suite covers workflow contracts, output checks, preservation, recovery, replay, example ingestion, native host routing, README generation, and repository structure, MIT licensing and domain ownership. Model-adapter controls use recorded or mocked results; they do not count as new model-performance observations.

The installed copy contains the same public repository files, including tests and development tools. Local environments and private records are excluded.

Review executable changes before running command cases. Use fresh result directories, retain failed attempts, and keep private input data out of public fixtures.
