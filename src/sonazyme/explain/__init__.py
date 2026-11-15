"""The explain stage: the scientist agent, answering from the run.

Answers questions about a run using that run's manifest and artefacts, citing
what it used, and saying so when the run does not contain the answer. The
retrieval half is in `retrieval.py`, the composition half in `answers.py`.

When configured, the stage also asks Adaption for one preliminary choice among
successful folded candidates. That separate report cites the selected fold
and states when integrity, scoring, ranking or training-data evidence is absent.
"""

from __future__ import annotations

import json
import os
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.explain.adaption import AdaptionExplainer, build_evidence
from sonazyme.explain.answers import COMPOSER, compose
from sonazyme.explain.retrieval import build
from sonazyme.runs.store import RunStore

PRODUCER = COMPOSER


def producer_for(model: str | None) -> dict:
    """Return the manifest producer for the selected explanation composer."""
    if model is None:
        return PRODUCER
    if not model.strip():
        raise ValueError("An Adaption inference model or stack id is required.")
    return {"name": "adaption.responses", "version": model.strip(), "kind": "model"}


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append one explanation of this run, grounded or refusing, as an artefact."""
    parameters = parameters or {}
    if set(parameters) - {"adaption_model"}:
        raise ValueError("Unsupported explain parameters.")
    model = parameters.get("adaption_model")
    if model is not None and not isinstance(model, str):
        raise ValueError("The Adaption inference model id must be a string.")
    index = build(store, manifest)
    record = compose(index)
    producer = producer_for(model)
    if model is not None:
        evidence = build_evidence(store, manifest)
        writeup = AdaptionExplainer(model).writeup(evidence)
        limitations = list(writeup["limitations"])
        limitations.append(
            "This is an Adaption model selection from folded candidates, not a stability score, "
            "validated rank or experimental result."
        )
        if any(
            candidate["integrity_status"] != "passed"
            for candidate in evidence["candidates"]
        ):
            limitations.append(
                "At least one candidate has no passing integrity verdict; this preliminary "
                "selection is not a design recommendation."
            )
        limitations.append(
            "No training-data records were supplied, so this report does not compare the "
            "candidate with Adaption's training data."
        )
        limitations.append(
            "Run measurements do not record assay conditions, so comparable experimental "
            "conditions were not established."
        )
        record["stability_writeup"] = {
            **writeup,
            "limitations": limitations,
            "producer": producer,
            "basis": "model-generated candidate selection; not a new stability score",
            "selection_basis": "successful folded candidates in this run",
            "training_data_comparison": {
                "status": "unavailable",
                "message": (
                    "No training-data records were supplied. No comparison with Adaption's "
                    "training data was made."
                ),
            },
            "citation_entry_ids": evidence["citation_entry_ids"],
        }
    ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
    return append(
        manifest,
        {
            "id": f"explain-{uuid4().hex}",
            "stage": "explain",
            "status": "succeeded",
            "producer": producer,
            "inputs": inputs or [],
            "parameters": parameters,
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
    parser.add_argument(
        "--adaption-model",
        default=os.environ.get("ADAPTION_EXPLAINER_MODEL"),
        help="Adaption hosted model id or active inference stack slug. "
        "Defaults to ADAPTION_EXPLAINER_MODEL.",
    )
    args = parser.parse_args(argv)
    parameters = {"adaption_model": args.adaption_model} if args.adaption_model else {}
    producer = producer_for(args.adaption_model)
    try:
        store = RunStore(args.run_dir)
        store.load()
        run_stage(
            store,
            stage="explain",
            producer=producer,
            parameters=parameters,
            inputs=[],
            execute=run,
            use_cache=bool(args.adaption_model),
        )
    except (ValueError, KeyError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Explanation failed: {error}\n")
    print(f"Explanation recorded in {store.manifest_path}")
    if args.adaption_model:
        print(
            "Adaption selected one folded candidate using cited run evidence. "
            "No new scores or training-data comparisons were produced."
        )
    else:
        print("Composed from this run only. Unanswerable questions are refused, not filled in.")
