from __future__ import annotations

from typing import Protocol

from auto_debugger.context import SolverContext


class Solver(Protocol):
    def __call__(self, context: SolverContext) -> str:
        ...

