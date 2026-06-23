# Agent Capabilities for Solving SWE-Bench Problems

This document summarizes the complete information and capabilities available to an agent/LLM solving SWE-bench problems.

## Overview

An agent now has **everything it needs** to solve an SWE-bench problem:
1. Complete problem metadata and requirements
2. Full access to the repository code
3. The ability to run tests and see failures
4. Tools to apply and verify fixes

## What Was Added

### New Modules

#### `src/auto_debugger/repo.py`
Repository management with:
- **`RepoManager`** class for cloning repositories and managing them
- Clone repository at a specific commit
- Read/write files
- List files with glob patterns
- Apply patches
- Run tests with pytest
- Track changed files

#### `src/auto_debugger/context.py`
Complete solver context combining:
- **`SolverContext`** class wrapping problem + repo access
- Methods to read/write files
- Test execution (failing tests, passing tests, custom tests)
- Problem summary generation
- Patch application and verification

### Updated Modules

#### `src/auto_debugger/solver.py`
- Changed `Solver` protocol: `problem: SWEProblem` → `context: SolverContext`
- Now solvers receive complete context, not just metadata

#### `src/auto_debugger/runner.py`
- Added `work_dir` parameter to `run_solver()`
- Creates `SolverContext` for each problem
- Passes context to solver functions

#### `src/auto_debugger/example_solver.py`
- Updated example to show how to use context
- Demonstrates available methods
- Shows how to read files, run tests, apply patches

#### `src/auto_debugger/cli.py`
- Updated `show` command to display full problem summaries
- Added `--work-dir` flag to `run` command
- Shows repo structure, test info, and metadata

## What Agents Can Now Do

### 1. Understand the Problem
```python
context.get_problem_summary()  # Full formatted problem description

context.problem.problem_statement  # The issue description
context.problem.hints_text         # Optional hints
context.problem.issue_url          # Reference to original issue
```

### 2. Explore the Code
```python
repo_path = context.get_repo_path()         # Get repository path
files = context.list_files("**/*.py")       # List Python files
code = context.read_file("src/module.py")   # Read any file
context.write_file("src/fix.py", code)      # Write modifications
```

### 3. Run Tests
```python
# See what's failing
success, output = context.run_failing_tests()

# Verify fixes don't break existing tests
success, output = context.run_passing_tests()

# Run specific tests
success, output = context.run_tests(("test_file.py::test_name",))
```

### 4. Verify Solutions
```python
# Test patch before returning it
success, output = context.apply_patch(patch_content)

# Run full test suite to verify fix
failing_pass, _ = context.run_failing_tests()
passing_pass, _ = context.run_passing_tests()

if failing_pass and passing_pass:
    return patch_string
```

## Information Provided to Agent

### From SWEProblem
- `instance_id` - Problem identifier
- `repo` - Repository name
- `base_commit` - Starting commit
- `problem_statement` - What needs fixing
- `fail_to_pass` - Tests that should be fixed
- `pass_to_pass` - Tests that must not break
- `hints_text` - Optional hints
- `issue_url` - Original issue link
- `pr_url` - Solution PR link
- `version` - Problem version
- `extras` - Additional metadata

### From Repository
- Complete code at base_commit
- All source files readable
- Test files with actual test code
- Git history and metadata
- File structure and organization

### From Test Execution
- Real pytest test output
- Actual failure messages and tracebacks
- Stack traces for debugging
- Test status (pass/fail)

## Example: Complete Solution Flow

```python
def solve_problem(context: SolverContext) -> str:
    # 1. Understand what needs fixing
    summary = context.get_problem_summary()
    problem = context.problem
    
    # 2. See the failures
    fails, output = context.run_failing_tests()
    print(f"Failures to fix: {output}")
    
    # 3. Explore relevant code
    files = context.list_files("**/test_*.py")
    for test_file in files:
        test_code = context.read_file(test_file)
        # Analyze test to understand requirements
    
    # 4. Make the fix
    source = context.read_file("src/buggy.py")
    fixed = source.replace("bug", "fix")
    context.write_file("src/buggy.py", fixed)
    
    # 5. Verify the fix
    if context.run_failing_tests()[0] and context.run_passing_tests()[0]:
        # Generate patch
        import subprocess
        result = subprocess.run(
            ["git", "diff", context.problem.base_commit],
            cwd=context.get_repo_path(),
            capture_output=True,
            text=True
        )
        return result.stdout
    
    # Handle failure case
    return ""
```

## Usage

### Show a problem with full context
```bash
python -m auto_debugger show --instance-id sympy__sympy-20590
```

This prints:
- Problem metadata (ID, repo, commit)
- Full problem statement
- List of tests to fix
- List of tests that must pass
- Repository structure
- Hints and references

### Run solver on a problem
```bash
python -m auto_debugger run \
    --solver my_solver:solve_problem \
    --instance-id sympy__sympy-20590
```

### Run solver on multiple problems with persistent repo
```bash
python -m auto_debugger run \
    --solver my_solver:solve_problem \
    --limit 100 \
    --work-dir /tmp/swe-bench-repos \
    --output predictions.jsonl
```

## Key Advantages

1. **No Guessing Required** - Agents have the actual failing test output
2. **Verification Built-in** - Agents can test their fixes immediately
3. **Full Context** - All relevant code and test information available
4. **Real Tests** - Not mocked; agents see actual pytest output
5. **Problem Hints** - Optional hints and references to original issues
6. **Flexible** - Agents can use any strategy; context provides tools

## Architecture

```
┌─────────────────────────────────────┐
│         SWE-Bench Dataset           │
│  (Problems with metadata)           │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      SolverContext                  │
│  • Problem metadata                 │
│  • RepoManager (git operations)     │
│  • Test runner (pytest)             │
│  • File I/O helpers                 │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Agent/Solver Function            │
│  (Your code here)                   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    Unified Diff Patch               │
│  (returned to runner)               │
└─────────────────────────────────────┘
```

## Next Steps

1. Implement your solver function using `SolverContext`
2. See `SOLVER_GUIDE.md` for detailed API documentation
3. See `src/auto_debugger/example_solver.py` for usage examples
4. Run `python -m auto_debugger show --instance-id <ID>` to see real problems
