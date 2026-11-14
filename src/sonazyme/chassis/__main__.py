"""Snapshot and select a sourced chassis for an existing sense run."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from sonazyme.chassis import PRODUCER, run
from sonazyme.chassis.registry import parse
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.runs.store import RunStore


def main(argv: list[str] | None = None) -> None:
    """Select a matching registry record, retaining all sources and readiness limits."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        data = args.registry.read_bytes()
        record = parse(data)
        store = RunStore(args.run_dir)
        manifest = store.load()
        senses = [
            e for e in manifest["entries"] if e["stage"] == "sense" and e["status"] == "succeeded"
        ]
        if not senses:
            raise ValueError("Run sense first in this run directory")
        # A sealed run can still reuse an existing snapshot and stage success.
        if manifest["status"] == "finished":
            digest = hashlib.sha256(data).hexdigest()
            registry = {"path": f"artefacts/{digest}", "sha256": digest, "size_bytes": len(data)}
            store.read(registry)
        else:
            registry = store.put(data)
        run_stage(
            store,
            stage="chassis",
            producer=PRODUCER,
            parameters={"registry": registry},
            inputs=[senses[-1]["id"]],
            execute=run,
        )
    except (ValueError, KeyError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Chassis selection failed: {error}\n")
    print(f"Chassis recorded in {store.manifest_path}")
    if not record["design_ready"]:
        print(
            "Research record only. Complete binding-site exclusion is unresolved; "
            "design remains blocked."
        )
    print("No model prediction or Sonazyme wet-lab result.")


if __name__ == "__main__":
    main()
