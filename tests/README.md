# Test Skill Builder

Use the environment containing scripts/requirements-lock.txt. Preview impacted checks from the repository root, then run that selection:

```sh
.venv/bin/python scripts/run_tests.py
.venv/bin/python scripts/run_tests.py --execute
```

Selection compares the last successful checkpoint or Git HEAD. config/test_impact.json maps changed behavior to related checks; modified test files select changed methods. The report shows the triggering files. Unmapped changes stop for an impact rule and never fall back to all tests. tools/check_repository.py delegates to the same guarded entry point.

Full testing requires actual user confirmation that the batch is finished. See [the maintenance workflow](../references/maintenance.md#scope-repository-tests-in-code) for the bound authorization record. Do not construct approval without the user's instruction, and do not treat test authorization as push approval.

Model-adapter controls use recorded or mocked outputs. They are separate from fresh model-performance observations. Keep private inputs, authorization records and test reports outside the repository.
