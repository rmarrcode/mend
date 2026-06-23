# Solver Guide: Complete Context for Solving SWE-Bench Problems

Your solver function receives a `SolverContext` object that provides **everything needed** to understand and solve an SWE-bench problem.

## Quick Start

```python
from auto_debugger.context import SolverContext

def solve_problem(context: SolverContext) -> str:
    """
    Solve an SWE bench problem.
    
    Returns: A unified diff patch string
    """
    # Get the problem metadata
    problem = context.problem
    print(f"Solving {problem.instance_id}")
    print(f"Repository: {problem.repo}")
    
    # See the full problem summary
    print(context.get_problem_summary())
    
    # Run tests to understand what's failing
    success, output = context.run_failing_tests()
    print(f"Test output:\n{output}")
    
    # Fix the code...
    # Then verify your fix works
    success, output = context.run_passing_tests()
    
    # Return the patch
    return "diff --git a/file.py b/file.py\n..."
```

## Available Context Methods

### Problem Information

- **`context.problem`** - The `SWEProblem` object with:
  - `instance_id` - Unique problem identifier
  - `repo` - Repository name (e.g., "sympy/sympy")
  - `base_commit` - Git commit to start from
  - `problem_statement` - Description of what needs fixing
  - `fail_to_pass` - Test names that should fail before fix
  - `pass_to_pass` - Test names that should stay passing
  - `hints_text` - Optional hints about the fix
  - `issue_url` - Link to the original issue
  - `pr_url` - Link to a solution PR

- **`context.get_problem_summary(include_repo_structure=True)`** - Formatted problem description with all metadata

### Repository Access

- **`context.get_repo_path() -> Path`** - Get the cloned repository path (clones it if needed)

- **`context.read_file(file_path: str) -> str`** - Read a file from the repository
  ```python
  content = context.read_file("src/module.py")
  ```

- **`context.list_files(pattern: str = "**/*.py") -> list[str]`** - List files matching a glob pattern
  ```python
  py_files = context.list_files("**/*.py")
  test_files = context.list_files("**/test_*.py")
  ```

- **`context.write_file(file_path: str, content: str)`** - Write a file to the repository
  ```python
  context.write_file("src/fix.py", "# fixed code")
  ```

### Test Execution

- **`context.run_failing_tests() -> (bool, str)`** - Run tests in `fail_to_pass`
  - Returns: (all_passed, test_output)
  - These should FAIL before your fix, PASS after

- **`context.run_passing_tests() -> (bool, str)`** - Run tests in `pass_to_pass`
  - Returns: (all_passed, test_output)
  - These should PASS before and after your fix

- **`context.run_tests(test_names: tuple[str, ...]) -> (bool, str)`** - Run specific tests
  ```python
  success, output = context.run_tests(("test_module.py::test_func",))
  ```

### Patching

- **`context.apply_patch(patch: str) -> (bool, str)`** - Apply a patch to verify it works
  ```python
  success, output = context.apply_patch(patch_string)
  if success:
      print("Patch applied successfully")
  ```

## Example: A Real Solver

Here's a complete example that uses the context to solve a problem:

```python
def solve_problem(context: SolverContext) -> str:
    # 1. Understand the problem
    print(context.get_problem_summary())
    
    # 2. See what tests are failing
    success, output = context.run_failing_tests()
    if not success:
        print("Failing tests output:")
        print(output)
    
    # 3. Examine the code
    repo_path = context.get_repo_path()
    test_files = context.list_files("**/test_*.py")
    
    # Look at one of the failing tests to understand what's expected
    for test_file in test_files[:1]:
        content = context.read_file(test_file)
        print(f"Test file {test_file}:")
        print(content[:500])  # First 500 chars
    
    # 4. Make your fix
    # For example, fix a bug in a source file
    source_file = "src/module.py"
    source_code = context.read_file(source_file)
    
    # Apply your fix (e.g., replace buggy code)
    fixed_code = source_code.replace(
        "buggy_function():",
        "fixed_function():"
    )
    
    context.write_file(source_file, fixed_code)
    
    # 5. Verify the fix
    failing_success, failing_output = context.run_failing_tests()
    passing_success, passing_output = context.run_passing_tests()
    
    if failing_success and passing_success:
        print("SUCCESS! All tests pass.")
    else:
        print("Tests still failing:")
        if not failing_success:
            print(failing_output)
        if not passing_success:
            print(passing_output)
    
    # 6. Return a unified diff patch
    # You can use git diff to generate it
    import subprocess
    result = subprocess.run(
        ["git", "diff", context.problem.base_commit],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.stdout
```

## What Gets Provided

### Problem Metadata
- Instance ID and repository information
- The exact failing tests to fix
- The passing tests that must not break
- Optional hints and references

### Code Access
- Full repository cloned at the base commit
- Ability to read any file
- Ability to list files and navigate structure

### Testing Capability
- Run the actual tests (not mocked)
- See real test failures and error messages
- Verify fixes work before submission

### Execution Context
- Current working directory is the repository
- Full file system access within the repo
- Can run any shell commands via subprocess

## Error Handling

The context handles common errors:

```python
try:
    content = context.read_file("nonexistent.py")
except FileNotFoundError:
    print("File doesn't exist")

success, output = context.run_failing_tests()
if not success:
    print(f"Tests failed: {output}")

success, output = context.apply_patch(bad_patch)
if not success:
    print(f"Patch failed: {output}")
```

## Running the Solver

```bash
# Show a problem summary
python -m auto_debugger show --instance-id sympy__sympy-20590

# Run your solver on one problem
python -m auto_debugger run \
    --solver my_module:solve_problem \
    --instance-id sympy__sympy-20590

# Run on multiple problems
python -m auto_debugger run \
    --solver my_module:solve_problem \
    --limit 10 \
    --output predictions.jsonl
```

## Context Cleanup

The context automatically cleans up the cloned repository when done:

```python
# Automatic cleanup (recommended)
with SolverContext(problem) as context:
    solve(context)
# Repository is cleaned up here

# Or manual cleanup
context = SolverContext(problem)
try:
    solve(context)
finally:
    context.cleanup()
```

## Important Notes

1. **Patches must be unified diffs** - Return output from `git diff` or similar
2. **Tests run with pytest** - The harness expects pytest-compatible tests
3. **Temporary directories** - Repositories are cloned to temporary directories by default, specify `--work-dir` to persist them
4. **Test names** - Use pytest-style test identifiers (e.g., `tests/test_file.py::test_function`)
