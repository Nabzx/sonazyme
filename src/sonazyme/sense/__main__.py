"""Load a research target into a resumable run without calling external models."""

from __future__ import annotations

import argparse
from pathlib import Path

from sonazyme.core.manifest import create
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.runs.store import RunStore
from sonazyme.sense import PRODUCER, run
from sonazyme.sense.targets import parse


def main(argv: list[str] | None = None) -> None:
    """Validate, snapshot and normalise one target, or reuse the saved sense entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        data = args.target.read_bytes()
        target = parse(data)
        run_id = args.run_id or target["target"]["id"]
        store = RunStore(args.run_dir)
        if store.manifest_path.exists():
            manifest = store.load()
            if manifest["run_id"] != run_id or store.read(manifest["target"]) != data:
                raise ValueError(
                    "Existing run has a different id or target; use a new run directory"
                )
        else:
            store.save(create(run_id, store.put(data)))
        run_stage(store, stage="sense", producer=PRODUCER, parameters={}, inputs=[], execute=run)
    except (ValueError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Target check failed: {error}\n")
    print(f"Target recorded in {store.manifest_path}")
    print("Schema check only. Unknowns remain unknown. No model or wet-lab result.")


if __name__ == "__main__":
    main()
