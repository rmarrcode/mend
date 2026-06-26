from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Callable

from auto_debugger.context import SolverContext
from auto_debugger.io import append_prediction, existing_instance_ids, load_dataset
from auto_debugger.types import SWEProblem


def _load_solver(solver_spec: str) -> Callable[[SolverContext], str]:
    if ":" not in solver_spec:
        raise ValueError(f"solver must be 'module:function', got: {solver_spec!r}")
    module_path, func_name = solver_spec.rsplit(":", 1)

    # Support file-path style (e.g. src/my_solver.py:solve)
    if module_path.endswith(".py"):
        p = Path(module_path).resolve()
        sys.path.insert(0, str(p.parent))
        module_path = p.stem

    module = importlib.import_module(module_path)
    return getattr(module, func_name)


def run_solver(
    solver_spec: str,
    *,
    dataset_name: str = "SWE-bench/SWE-bench_Lite",
    split: str = "test",
    instance_ids: tuple[str, ...] = (),
    limit: int | None = None,
    output: str | None = None,
    work_dir: str | None = None,
    resume: bool = False,
) -> list[dict]:
    solver_fn = _load_solver(solver_spec)

    problems = load_dataset(dataset_name, split)

    if instance_ids:
        id_set = set(instance_ids)
        problems = [p for p in problems if p.instance_id in id_set]

    done: set[str] = set()
    if resume and output:
        done = existing_instance_ids(output)
        problems = [p for p in problems if p.instance_id not in done]

    if limit is not None:
        problems = problems[:limit]

    results: list[dict] = []
    for problem in problems:
        print(f"Solving {problem.instance_id} …")
        with SolverContext(problem, work_dir) as ctx:
            try:
                patch = solver_fn(ctx)
            except Exception as exc:
                print(f"  ERROR: {exc}")
                patch = ""

        record = {
            "instance_id": problem.instance_id,
            "model_patch": patch,
        }
        results.append(record)

        if output:
            append_prediction(output, problem.instance_id, solver_spec, patch)

    return results

