# Summary of Changes: Complete Agent Context for SWE-Bench

## What Was Done

The repository now provides **complete information and capabilities** for an agent/LLM to solve SWE-bench problems. Previously, the agent only received problem metadata. Now it has everything it needs:

## Key Additions

### 1. New Module: `src/auto_debugger/repo.py`
A `RepoManager` class that handles:
- **Repository cloning** at a specific commit
- **File operations** (read/write/list)
- **Test execution** with pytest
- **Patch application** with verification
- **Automatic cleanup**

```python
manager = RepoManager("https://github.com/user/repo.git", "abc123")
repo_path = manager.clone_and_checkout()
content = manager.read_file("src/module.py")
success, output = manager.run_tests(("test_module.py::test_func",))
```

### 2. New Module: `src/auto_debugger/context.py`
A `SolverContext` class that wraps everything together:
- **Problem metadata** from `SWEProblem`
- **Repository management** via `RepoManager`
- **Test execution helpers**
- **Problem summary generation**

```python
context = SolverContext(problem)
summary = context.get_problem_summary()
success, output = context.run_failing_tests()
code = context.read_file("src/file.py")
```

### 3. Updated: `src/auto_debugger/solver.py`
Changed the solver protocol:
- **Before**: `def solve(problem: SWEProblem) -> str`
- **After**: `def solve(context: SolverContext) -> str`

Solvers now receive the complete context instead of just metadata.

### 4. Updated: `src/auto_debugger/runner.py`
- Creates `SolverContext` for each problem
- Passes full context to solver
- Handles automatic repository cleanup
- Added `work_dir` parameter to `run_solver()`

### 5. Updated: `src/auto_debugger/cli.py`
- `show` command now displays complete problem context
- `run` command supports `--work-dir` flag
- Full problem information available before solving

### 6. Updated: `src/auto_debugger/example_solver.py`
- Shows how to use `SolverContext`
- Demonstrates all available methods
- Includes usage examples

### 7. Updated: Tests in `tests/test_runner.py`
- Added test for `SolverContext` creation
- Verified backward compatibility

### 8. New Documentation
- **`SOLVER_GUIDE.md`** - Comprehensive API reference and examples
- **`AGENT_CAPABILITIES.md`** - What information is available to agents
- **`CHANGES_SUMMARY.md`** - This file

## What Agents Can Now Do

### 1. Understand the Problem
```python
# Get formatted summary with all context
summary = context.get_problem_summary()

# Access individual fields
problem = context.problem
print(problem.problem_statement)
print(problem.fail_to_pass)
print(problem.hints_text)
```

### 2. Explore the Repository
```python
# Get the cloned repo path
repo_path = context.get_repo_path()

# Read any file
code = context.read_file("src/module.py")

# List files
files = context.list_files("**/*.py")

# Navigate the structure
for file in files:
    if "test" in file:
        test_code = context.read_file(file)
```

### 3. Run Tests and See Failures
```python
# Run tests that should fail
success, output = context.run_failing_tests()
print("Test failures:")
print(output)  # Real pytest output with tracebacks

# Run tests that should pass
success, output = context.run_passing_tests()

# Run specific tests
success, output = context.run_tests(("test_file.py::test_func",))
```

### 4. Make and Verify Fixes
```python
# Modify code
source = context.read_file("src/buggy.py")
fixed = source.replace("bug", "fix")
context.write_file("src/buggy.py", fixed)

# Verify the fix
if context.run_failing_tests()[0]:
    print("Tests now pass!")

# Apply a patch
success, output = context.apply_patch(patch_string)

# Generate the final patch
import subprocess
result = subprocess.run(
    ["git", "diff", context.problem.base_commit],
    cwd=context.get_repo_path(),
    capture_output=True,
    text=True
)
patch = result.stdout
```

## Information Provided

### Problem Metadata
- `instance_id` - Unique problem identifier
- `repo` - Repository name
- `base_commit` - Starting commit
- `problem_statement` - Description of what needs fixing
- `fail_to_pass` - Test names that should be fixed
- `pass_to_pass` - Test names that must not break
- `hints_text` - Optional hints
- `issue_url` - Link to original issue
- `pr_url` - Link to solution PR
- `version` - Problem version
- `extras` - Additional metadata

### Repository
- Complete code at base commit
- All source files readable and modifiable
- Full test suite available
- Git history and metadata
- File structure and organization

### Test Results
- Real pytest output
- Actual error messages and tracebacks
- Test pass/fail status
- Stack traces for debugging

## Usage Examples

### View Complete Problem Context
```bash
python -m auto_debugger show --instance-id sympy__sympy-20590
```

Output includes:
- Problem metadata
- Full problem statement
- Tests to fix and keep passing
- Repository structure
- Hints and references

### Run Solver with Context
```bash
python -m auto_debugger run \
    --solver my_solver:solve_problem \
    --instance-id sympy__sympy-20590 \
    --work-dir /tmp/repos
```

Your solver function receives `SolverContext` with full access.

### Run on Multiple Problems
```bash
python -m auto_debugger run \
    --solver my_solver:solve_problem \
    --limit 100 \
    --work-dir /tmp/swe-bench \
    --output predictions.jsonl
```

## Architecture

```
Problem Data (instance_id, repo, commit, tests, hints)
        ↓
    RepoManager (clone, checkout, run tests)
        ↓
    SolverContext (unified interface)
        ↓
    Solver Function (agent/LLM)
        ↓
    Unified Diff Patch
        ↓
    Evaluation Harness
```

## Backward Compatibility

The changes maintain backward compatibility with the output format:
- Solvers still return unified diff patches
- Output format remains compatible with official harness
- Existing evaluation code works unchanged

## Benefits

1. **Complete Context** - Agents have all information needed
2. **Real Tests** - Not mocked; see actual pytest output
3. **Verification** - Agents can test before submitting
4. **Exploration** - Can examine code structure before fixing
5. **No Guessing** - Error messages available directly
6. **Flexible** - Agents can use any strategy

## Files Changed

### Created
- `src/auto_debugger/repo.py` - Repository management
- `src/auto_debugger/context.py` - Solver context
- `SOLVER_GUIDE.md` - API reference
- `AGENT_CAPABILITIES.md` - Capabilities overview
- `CHANGES_SUMMARY.md` - This file

### Modified
- `src/auto_debugger/solver.py` - Updated protocol
- `src/auto_debugger/runner.py` - Context integration
- `src/auto_debugger/example_solver.py` - Updated example
- `src/auto_debugger/cli.py` - Display enhancements
- `tests/test_runner.py` - Test updates
- `README.md` - Documentation updates

## Next Steps

1. Review `SOLVER_GUIDE.md` for detailed API documentation
2. Check `AGENT_CAPABILITIES.md` for capability overview
3. Look at `example_solver.py` for usage patterns
4. Run `python -m auto_debugger show --instance-id <ID>` to see real problems
5. Implement your solver using the `SolverContext`

## Testing

All changes have been verified:
- ✓ Imports work correctly
- ✓ Context creation works
- ✓ Problem summary generation works
- ✓ Backward compatibility maintained
- ✓ Core runner tests pass
