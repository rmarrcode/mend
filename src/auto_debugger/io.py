from __future__ import annotations

import json
from pathlib import Path

from auto_debugger.types import SWEProblem


def load_predictions(path: str | Path) -> list[dict]:
    predictions = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                predictions.append(json.loads(line))
    return predictions


def append_prediction(path: str | Path, instance_id: str, model_name: str, patch: str) -> None:
    record = {
        "instance_id": instance_id,
        "model_name_or_path": model_name,
        "model_patch": patch,
    }
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def existing_instance_ids(path: str | Path) -> set[str]:
    if not Path(path).exists():
        return set()
    return {r["instance_id"] for r in load_predictions(path)}


def load_dataset(dataset_name: str, split: str) -> list[SWEProblem]:
    from datasets import load_dataset as hf_load

    ds = hf_load(dataset_name, split=split)
    return [SWEProblem.from_dataset_row(dict(row)) for row in ds]

