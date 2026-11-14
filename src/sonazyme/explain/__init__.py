"""The explain stage: the scientist agent, answering from the run.

Answers questions about a run using that run's manifest and artefacts, citing
what it used, and saying so when the run does not contain the answer. The
retrieval half is in `retrieval.py`, the composition half in `answers.py`.

The composer is deterministic today, and the stage records it as code rather
than as a model, so nothing on screen claims a model wrote it. A fine-tuned
scientist replaces the composer later (#18) and keeps the contract: a claim
arrives with its citation or it does not arrive.
"""

from __future__ import annotations

import json
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.explain.answers import COMPOSER, compose
from sonazyme.explain.retrieval import build
from sonazyme.runs.store import RunStore

PRODUCER = COMPOSER


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append one explanation of this run, grounded or refusing, as an artefact."""
    if parameters:
        raise ValueError("explain v1 has no configurable parameters")
    record = compose(build(store, manifest))
    ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
    return append(
        manifest,
        {
            "id": f"explain-{uuid4().hex}",
            "stage": "explain",
            "status": "succeeded",
            "producer": PRODUCER,
            "inputs": inputs or [],
            "parameters": {},
            "metrics": [],
            "artefacts": [ref],
            "reason": None,
        },
    )


def main(argv: list[str] | None = None) -> None:
    """Write an explanation of a saved run."""
    import argparse
    from pathlib import Path

    from sonazyme.runs.runner import StageExecutionError, run_stage

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        store = RunStore(args.run_dir)
        store.load()
        run_stage(
            store,
            stage="explain",
            producer=PRODUCER,
            parameters={},
            inputs=[],
            execute=run,
            use_cache=False,
        )
    except (ValueError, KeyError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Explanation failed: {error}\n")
    print(f"Explanation recorded in {store.manifest_path}")
    print("Composed from this run only. Unanswerable questions are refused, not filled in.")
