from __future__ import annotations

import subprocess

from auto_debugger.context import SolverContext


def solve_problem(context: SolverContext) -> str:
    """Example solver that demonstrates how to use SolverContext."""
    problem = context.problem
    print(f"\nSolving {problem.instance_id}")
    print(f"Repository: {problem.repo}")

    print("\n" + context.get_problem_summary(include_repo_structure=False))

    # Run failing tests to understand what's broken
    print("\nRunning failing tests …")
    success, output = context.run_failing_tests()
    print(f"Failing tests passed: {success}")
    print(output[:2000])

    # Explore the repository
    py_files = context.list_files("**/*.py")
    print(f"\nRepository has {len(py_files)} Python files")

    # After making changes, generate the patch with git diff
    repo_path = context.get_repo_path()
    result = subprocess.run(
        ["git", "diff", problem.base_commit],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    return result.stdout

