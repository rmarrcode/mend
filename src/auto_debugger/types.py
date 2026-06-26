from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SWEProblem:
    instance_id: str
    repo: str
    base_commit: str
    problem_statement: str
    fail_to_pass: tuple[str, ...]
    pass_to_pass: tuple[str, ...]
    hints_text: str = ""
    issue_url: str = ""
    pr_url: str = ""
    version: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dataset_row(cls, row: dict[str, Any]) -> "SWEProblem":
        def _to_tuple(value: Any) -> tuple[str, ...]:
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return tuple(parsed)
                except (json.JSONDecodeError, ValueError):
                    pass
                return (value,) if value else ()
            if isinstance(value, (list, tuple)):
                return tuple(value)
            return ()

        known = {
            "instance_id",
            "repo",
            "base_commit",
            "problem_statement",
            "FAIL_TO_PASS",
            "PASS_TO_PASS",
            "hints_text",
            "issue_url",
            "pr_url",
            "version",
        }
        extras = {k: v for k, v in row.items() if k not in known}

        return cls(
            instance_id=row.get("instance_id", ""),
            repo=row.get("repo", ""),
            base_commit=row.get("base_commit", ""),
            problem_statement=row.get("problem_statement", ""),
            fail_to_pass=_to_tuple(row.get("FAIL_TO_PASS", [])),
            pass_to_pass=_to_tuple(row.get("PASS_TO_PASS", [])),
            hints_text=row.get("hints_text", ""),
            issue_url=row.get("issue_url", ""),
            pr_url=row.get("pr_url", ""),
            version=row.get("version", ""),
            extras=extras,
        )

