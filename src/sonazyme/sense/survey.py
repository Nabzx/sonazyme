"""Record one acoustic survey of a loop as a sense entry.

The survey is simulated (ADR-0013). The entry says so, the artefact says so,
and the dashboard shows it. When an instrument eventually supplies readings,
the record keeps its shape and only its basis and source change.
"""

from __future__ import annotations

import json
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.runs.store import RunStore
from sonazyme.sense.acoustic import VERSION, survey
from sonazyme.sense.loop import validate_loop, validate_reading

PRODUCER = {
    "name": "sonazyme.sense.acoustic.forward-model",
    "version": VERSION,
    "kind": "model",
}


def reading(loop: dict, truth: dict, *, seed: int | None = None) -> dict:
    """Build a validated reading record for one loop, from the forward model."""
    validate_loop(loop)
    record = {
        "schema_version": 1,
        "kind": "reading",
        "basis": "simulation",
        "basis_reason": (
            "Produced by the Sonazyme forward model, not by an instrument. No loop has "
            "been pinged. See ADR-0013."
        ),
        "loop_id": loop["id"],
        "instrument": f"{PRODUCER['name']} {PRODUCER['version']}",
        "observation": survey(loop, truth, seed=seed),
    }
    return validate_reading(record)


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append a simulated survey, keeping the loop map and the reading as artefacts."""
    parameters = parameters or {}
    loop = validate_loop(parameters["loop"])
    truth = parameters.get("truth") or {}
    seed = parameters.get("seed")
    if seed is not None and type(seed) is not int:
        raise ValueError("A survey seed must be an integer so the run replays")
    record = reading(loop, truth, seed=seed)
    ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
    return append(
        manifest,
        {
            "id": f"sense-{uuid4().hex}",
            "stage": "sense",
            "status": "succeeded",
            "producer": PRODUCER,
            "inputs": inputs or [],
            "parameters": parameters,
            "metrics": [],
            "artefacts": [ref],
            "reason": None,
        },
    )


def main(argv: list[str] | None = None) -> None:
    """Record one simulated survey into a run, or reuse the saved entry."""
    import argparse
    from pathlib import Path

    from sonazyme.runs.runner import StageExecutionError, run_stage
    from sonazyme.sense.loop import parse_loop

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("loop", type=Path, help="a loop map, as TOML")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--truth",
        type=Path,
        required=True,
        help="JSON mapping each section id to the layer the simulation should put there",
    )
    parser.add_argument("--seed", type=int, default=0, help="kept so the run replays")
    args = parser.parse_args(argv)
    try:
        loop = parse_loop(args.loop.read_bytes())
        truth = json.loads(args.truth.read_text(encoding="utf-8"))
        if not isinstance(truth, dict):
            raise ValueError("The truth file must map section ids to layers")
        unknown = set(truth) - {section["id"] for section in loop["section"]}
        if unknown:
            raise ValueError(f"Truth names sections not in the loop: {', '.join(sorted(unknown))}")
        store = RunStore(args.run_dir)
        store.load()
        run_stage(
            store,
            stage="sense",
            producer=PRODUCER,
            parameters={"loop": loop, "truth": truth, "seed": args.seed},
            inputs=[],
            execute=run,
        )
    except (ValueError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Survey failed: {error}\n")
    print(f"Simulated survey recorded in {store.manifest_path}")
    print("Simulated readings. No loop has been pinged. See ADR-0013.")


if __name__ == "__main__":
    main()
