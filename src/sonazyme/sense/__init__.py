"""The sense stage: what holds this film together, and in what conditions.

Reads a target file and turns it into the run's working definition: the
anchors to attack and the envelope to survive, carrying through whether each
value is sourced or assumed. No model calls; the intelligence is in the target
file (ADR-0002).
"""

from __future__ import annotations

import json
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.runs.store import RunStore
from sonazyme.sense.targets import parse

PRODUCER = {"name": "sonazyme.sense", "version": "1", "kind": "code"}


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append the normalised target without converting assumptions into evidence."""
    if parameters:
        raise ValueError("sense v1 has no configurable parameters")
    target = parse(store.read(manifest["target"]))
    ref = store.put((json.dumps(target, indent=2, allow_nan=False) + "\n").encode())
    return append(
        manifest,
        {
            "id": f"sense-{uuid4().hex}",
            "stage": "sense",
            "status": "succeeded",
            "producer": PRODUCER,
            "inputs": inputs or [],
            "parameters": {},
            "metrics": [],
            "artefacts": [ref],
            "reason": None,
        },
    )
