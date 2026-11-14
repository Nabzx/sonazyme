"""Fold a selected chassis using explicitly provisioned Boltz compute."""

from __future__ import annotations

import argparse
import json
from functools import partial
from pathlib import Path

from sonazyme.core.folding import model_producer, validate_settings
from sonazyme.fold import run
from sonazyme.fold.boltz import LocalBoltz
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.runs.store import RunStore


def main(argv: list[str] | None = None) -> None:
    """Run or reuse one baseline prediction without installing Boltz implicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--settings", type=Path, required=True)
    parser.add_argument("--boltz-python", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        settings = json.loads(args.settings.read_text())
        validate_settings(settings)
        store = RunStore(args.run_dir)
        manifest = store.load()
        parents = [
            e for e in manifest["entries"] if e["stage"] == "chassis" and e["status"] == "succeeded"
        ]
        if not parents:
            raise ValueError("Select a chassis first")
        parent = parents[-1]
        backend = LocalBoltz(args.boltz_python, args.checkpoint, args.cache)
        run_stage(
            store,
            stage="fold",
            producer=model_producer(settings),
            parameters={"subject": parent["artefacts"][0], "settings": settings},
            inputs=[parent["id"]],
            execute=partial(run, backend=backend),
        )
    except (ValueError, KeyError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Fold failed: {error}\n")
    print(f"Predicted structure and confidence recorded in {store.manifest_path}")
    print("No stability or activity estimate. No Sonazyme wet-lab result.")


if __name__ == "__main__":
    main()
