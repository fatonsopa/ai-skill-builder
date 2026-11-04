# Test Skill Builder

Use the scoped runner for repository checks and keep model-performance evidence separate from authored controls.

## Start

Use the environment containing scripts/requirements-lock.txt. Preview impacted checks from the repository root, then run that selection:

```sh
.venv/bin/python scripts/run_tests.py
.venv/bin/python scripts/run_tests.py --execute
```

## Check the result

The report shows the triggering files and each check's actual outcome. Unmapped changes stop for an impact rule and never fall back to all tests.

Run final testing after the author verifies that every planned implementation change has been delivered and no implementation work remains. See [the implementation-completion gate](../references/maintenance.md#verify-implementation-before-final-testing) for the source-bound record and `--completion-record` command. No user batch approval is required; publication retains its existing authority requirements.

## Find your way around

Selection compares the last successful checkpoint or Git HEAD. config/test_impact.json maps changed behavior to related checks; modified test files select changed methods. tools/check_repository.py delegates to the same guarded entry point. The [repository readme](../README.md) explains installation and invocation.

## Limits and help

Model-adapter controls use recorded or mocked outputs. They are separate from fresh model-performance observations. Keep private inputs, completion records and test reports outside the repository. Use the [maintenance workflow](../references/maintenance.md) to diagnose failed checks and preserve their evidence.

The completion-policy controls exercise cumulative budgets across run directories, frozen requirements and check scope, receipt freshness, follow-up classification and the delivery boundary. Mocked host transport tests establish these mechanics; they are not model-performance results.
