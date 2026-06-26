from __future__ import annotations

import argparse
import json
import sys


def cmd_show(args: argparse.Namespace) -> None:
    from auto_debugger.context import SolverContext
    from auto_debugger.io import load_dataset

    problems = load_dataset(args.dataset_name, args.split)
    matches = [p for p in problems if p.instance_id == args.instance_id]
    if not matches:
        print(f"Instance {args.instance_id!r} not found in {args.dataset_name}/{args.split}", file=sys.stderr)
        sys.exit(1)

    problem = matches[0]
    with SolverContext(problem) as ctx:
        print(ctx.get_problem_summary(include_repo_structure=args.repo_structure))


def cmd_run(args: argparse.Namespace) -> None:
    from auto_debugger.runner import run_solver

    run_solver(
        args.solver,
        dataset_name=args.dataset_name,
        split=args.split,
        instance_ids=tuple(args.instance_id) if args.instance_id else (),
        limit=args.limit,
        output=args.output,
        work_dir=args.work_dir,
        resume=args.resume,
    )


def cmd_evaluate(args: argparse.Namespace) -> None:
    try:
        from swebench.harness.run_evaluation import main as swe_eval
    except ImportError:
        print(
            "swebench is not installed. Run: pip install 'auto-debugger[eval]'",
            file=sys.stderr,
        )
        sys.exit(1)

    swe_eval(
        dataset_name=args.dataset_name,
        split=args.split,
        predictions_path=args.predictions,
        run_id=args.run_id,
        max_workers=args.max_workers,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto-debugger",
        description="SWE-bench runner scaffold",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── show ──────────────────────────────────────────────────────────────
    p_show = sub.add_parser("show", help="Display problem context for one instance")
    p_show.add_argument("--instance-id", required=True)
    p_show.add_argument("--dataset-name", default="SWE-bench/SWE-bench_Lite")
    p_show.add_argument("--split", default="test")
    p_show.add_argument(
        "--no-repo-structure",
        dest="repo_structure",
        action="store_false",
        default=True,
        help="Skip cloning and listing repository files",
    )
    p_show.set_defaults(func=cmd_show)

    # ── run ───────────────────────────────────────────────────────────────
    p_run = sub.add_parser("run", help="Run a solver against SWE-bench instances")
    p_run.add_argument("--solver", required=True, help="module:function or file.py:function")
    p_run.add_argument("--model-name", default="auto-debugger")
    p_run.add_argument("--dataset-name", default="SWE-bench/SWE-bench_Lite")
    p_run.add_argument("--split", default="test")
    p_run.add_argument("--instance-id", action="append", metavar="ID")
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--output", default=None, metavar="FILE")
    p_run.add_argument("--work-dir", default=None, metavar="DIR")
    p_run.add_argument("--resume", action="store_true")
    p_run.set_defaults(func=cmd_run)

    # ── evaluate ──────────────────────────────────────────────────────────
    p_eval = sub.add_parser("evaluate", help="Evaluate predictions using the official harness")
    p_eval.add_argument("--predictions", required=True, metavar="FILE")
    p_eval.add_argument("--run-id", required=True)
    p_eval.add_argument("--dataset-name", default="SWE-bench/SWE-bench_Lite")
    p_eval.add_argument("--split", default="test")
    p_eval.add_argument("--max-workers", type=int, default=4)
    p_eval.set_defaults(func=cmd_evaluate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

