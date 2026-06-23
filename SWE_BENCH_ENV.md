# auto-debugger

Scaffold for running an agent/LLM solver against SWE-bench instances with **complete problem context**.

## What this gives you

- **Complete problem context**: metadata, failing tests, passing tests, hints, and references
- **Repository access**: cloned and checked out at the base commit, readable files
- **Test execution**: run tests and see actual failures and errors
- **Code modification**: read and write files, apply patches, verify fixes
- A `SWEProblem` dataclass with all SWE-bench fields
- A `SolverContext` that wraps the repository and provides all capabilities
- A CLI that loads problems, calls your solver with full context, and outputs predictions
- Integration with the official SWE-bench evaluation harness

**Your solver receives everything it needs to solve the problem** — no guessing required.

## Setup

Create the virtualenv once at the repo parent:

```bash
python3 -m venv ../.venv
../.venv/bin/pip install --upgrade pip
../.venv/bin/pip install -e .
```

Install the official local evaluation harness only if you plan to run containerized scoring:

```bash
../.venv/bin/pip install -e ".[eval]"
```

`swebench` local evaluation also requires Docker to be installed and running.

## Project layout

```text
auto_debugger/
  src/auto_debugger/
    cli.py              # CLI for show/run/evaluate
    context.py          # SolverContext with complete problem info
    example_solver.py   # Example solver showing how to use context
    io.py               # I/O utilities
    repo.py             # Repository management (clone, run tests, etc.)
    runner.py           # Core runner that creates context and calls solver
    solver.py           # Solver protocol
    types.py            # SWEProblem and related types
  SOLVER_GUIDE.md       # Detailed guide for writing solvers
  AGENT_CAPABILITIES.md # What information is available to agents
```

## Implement your solver

Point the CLI at a function that receives `SolverContext`:

```python
from auto_debugger.context import SolverContext


def solve_problem(context: SolverContext) -> str:
    # Access the problem metadata
    problem = context.problem
    
    # Get a formatted summary
    print(context.get_problem_summary())
    
    # Run the failing tests to understand what's broken
    success, output = context.run_failing_tests()
    
    # Read and modify code
    code = context.read_file("src/buggy.py")
    context.write_file("src/buggy.py", fixed_code)
    
    # Verify your fix works
    success, output = context.run_passing_tests()
    
    # Return a unified diff patch
    return "diff --git a/file.py b/file.py\n..."
```

The `SolverContext` provides:
- Complete problem metadata (instance_id, repo, base_commit, problem_statement, hints, etc.)
- Tests to fix (fail_to_pass) and tests that must not break (pass_to_pass)
- Repository cloned at the base commit
- Methods to read/write files
- Methods to run tests and see real failures
- Methods to apply and verify patches

See `SOLVER_GUIDE.md` for detailed API documentation.

## Inspect one instance

See the complete problem context that will be provided to your solver:

```bash
../.venv/bin/auto-debugger show \
  --instance-id sympy__sympy-20590
```

This outputs:
- **Problem metadata**: instance ID, repository, base commit
- **Problem statement**: what needs to be fixed
- **Tests to fix**: tests that currently fail and should pass
- **Tests to keep passing**: tests that should still pass after the fix
- **Repository structure**: list of files in the repo
- **Hints and references**: links to original issue and PR
- **Code access**: full repository cloned and ready for inspection

## Generate predictions

```bash
../.venv/bin/auto-debugger run \
  --solver src/auto_debugger/example_solver.py:solve_problem \
  --model-name my-solver \
  --limit 2 \
  --output predictions/lite.jsonl
```

Options:
- `--dataset-name` - Dataset to use (default: `SWE-bench/SWE-bench_Lite`)
- `--split` - Which split (default: `test`)
- `--instance-id` - Specific instance IDs to solve (repeat to add more)
- `--work-dir` - Directory for cloning repositories (default: temporary)
- `--resume` - Skip instances already in the output file

Your solver function receives a `SolverContext` with:
- The full problem metadata and requirements
- The cloned repository at the base commit
- Methods to run tests and see failures
- Methods to read/write files
- Utilities for patching and verification

## Evaluate predictions locally

```bash
../.venv/bin/auto-debugger evaluate \
  --predictions predictions/lite.jsonl \
  --run-id local-lite
```

This command shells out to the official SWE-bench harness. For large runs, expect significant disk and Docker usage.

If your installed harness version still expects the older namespace, pass `--dataset-name princeton-nlp/SWE-bench_Lite`.
