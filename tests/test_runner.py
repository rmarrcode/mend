from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from auto_debugger.context import SolverContext
from auto_debugger.types import SWEProblem


def _make_problem(**kwargs) -> SWEProblem:
    defaults = dict(
        instance_id="test__repo-1",
        repo="org/repo",
        base_commit="abc123",
        problem_statement="Fix the bug.",
        fail_to_pass=("tests/test_foo.py::test_bar",),
        pass_to_pass=("tests/test_foo.py::test_baz",),
    )
    defaults.update(kwargs)
    return SWEProblem(**defaults)


class TestSWEProblem:
    def test_from_dataset_row_basic(self):
        row = {
            "instance_id": "sympy__sympy-20590",
            "repo": "sympy/sympy",
            "base_commit": "deadbeef",
            "problem_statement": "Something is broken.",
            "FAIL_TO_PASS": '["tests/test_a.py::test_x"]',
            "PASS_TO_PASS": '["tests/test_b.py::test_y"]',
            "hints_text": "Look at sympy/core/foo.py",
            "issue_url": "https://github.com/sympy/sympy/issues/20590",
        }
        p = SWEProblem.from_dataset_row(row)
        assert p.instance_id == "sympy__sympy-20590"
        assert p.fail_to_pass == ("tests/test_a.py::test_x",)
        assert p.pass_to_pass == ("tests/test_b.py::test_y",)
        assert p.hints_text == "Look at sympy/core/foo.py"

    def test_from_dataset_row_list_fields(self):
        row = {
            "instance_id": "x",
            "repo": "a/b",
            "base_commit": "c",
            "problem_statement": "p",
            "FAIL_TO_PASS": ["test_a.py::test_1", "test_a.py::test_2"],
            "PASS_TO_PASS": [],
        }
        p = SWEProblem.from_dataset_row(row)
        assert p.fail_to_pass == ("test_a.py::test_1", "test_a.py::test_2")
        assert p.pass_to_pass == ()


class TestSolverContext:
    def test_context_creation(self):
        problem = _make_problem()
        with patch("auto_debugger.repo.RepoManager.clone_and_checkout") as mock_clone:
            ctx = SolverContext(problem)
            assert ctx.problem is problem

    def test_get_problem_summary(self):
        problem = _make_problem(hints_text="Try fixing foo.")
        with patch("auto_debugger.context.SolverContext.list_files", return_value=[]):
            ctx = SolverContext(problem)
            summary = ctx.get_problem_summary(include_repo_structure=False)
        assert "test__repo-1" in summary
        assert "org/repo" in summary
        assert "Fix the bug." in summary
        assert "Try fixing foo." in summary
        assert "tests/test_foo.py::test_bar" in summary

    def test_context_manager(self):
        problem = _make_problem()
        with patch("auto_debugger.repo.RepoManager.cleanup") as mock_cleanup:
            with SolverContext(problem) as ctx:
                assert ctx.problem is problem
            mock_cleanup.assert_called_once()

