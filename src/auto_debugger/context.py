from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from auto_debugger.repo import RepoManager
from auto_debugger.types import SWEProblem

if TYPE_CHECKING:
    pass


class SolverContext:
    def __init__(self, problem: SWEProblem, work_dir: str | None = None) -> None:
        self.problem = problem
        repo_url = f"https://github.com/{problem.repo}.git"
        self._manager = RepoManager(repo_url, problem.base_commit, work_dir)

    # ── repository access ──────────────────────────────────────────────────

    def get_repo_path(self) -> Path:
        return self._manager.clone_and_checkout()

    def read_file(self, file_path: str) -> str:
        return self._manager.read_file(file_path)

    def write_file(self, file_path: str, content: str) -> None:
        self._manager.write_file(file_path, content)

    def list_files(self, pattern: str = "**/*.py") -> list[str]:
        return self._manager.list_files(pattern)

    # ── test execution ─────────────────────────────────────────────────────

    def run_failing_tests(self) -> tuple[bool, str]:
        return self._manager.run_tests(self.problem.fail_to_pass)

    def run_passing_tests(self) -> tuple[bool, str]:
        return self._manager.run_tests(self.problem.pass_to_pass)

    def run_tests(self, test_names: tuple[str, ...]) -> tuple[bool, str]:
        return self._manager.run_tests(test_names)

    # ── patching ───────────────────────────────────────────────────────────

    def apply_patch(self, patch: str) -> tuple[bool, str]:
        return self._manager.apply_patch(patch)

    # ── summary ────────────────────────────────────────────────────────────

    def get_problem_summary(self, include_repo_structure: bool = True) -> str:
        p = self.problem
        lines: list[str] = [
            f"Instance ID : {p.instance_id}",
            f"Repository  : {p.repo}",
            f"Base commit : {p.base_commit}",
        ]
        if p.version:
            lines.append(f"Version     : {p.version}")
        lines += [
            "",
            "── Problem statement ──────────────────────────────────────────",
            p.problem_statement,
        ]
        if p.hints_text:
            lines += ["", "── Hints ──────────────────────────────────────────────────────", p.hints_text]
        fail_lines = [f"  {t}" for t in p.fail_to_pass] or ["  (none)"]
        pass_lines = [f"  {t}" for t in p.pass_to_pass] or ["  (none)"]
        lines += [
            "",
            "── Tests to fix (fail → pass) ─────────────────────────────────",
            *fail_lines,
            "",
            "── Tests to keep passing ──────────────────────────────────────",
            *pass_lines,
        ]
        if p.issue_url:
            lines.append(f"\nIssue : {p.issue_url}")
        if p.pr_url:
            lines.append(f"PR    : {p.pr_url}")

        if include_repo_structure:
            try:
                py_files = self.list_files("**/*.py")[:30]
                lines += [
                    "",
                    "── Repository structure (first 30 .py files) ─────────────────",
                    *[f"  {f}" for f in py_files],
                ]
            except Exception:
                pass

        return "\n".join(lines)

    # ── lifecycle ──────────────────────────────────────────────────────────

    def cleanup(self) -> None:
        self._manager.cleanup()

    def __enter__(self) -> "SolverContext":
        return self

    def __exit__(self, *_: object) -> None:
        self.cleanup()

