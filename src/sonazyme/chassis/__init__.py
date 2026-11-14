"""The chassis stage: parent enzymes that cut the target's anchors.

Selects natural enzymes known to cut each anchor's bond, with sequence,
source and an explicitly scoped active-site definition. Baseline folding
and scoring are separate stage calls over the selected record.
"""

from __future__ import annotations

import json
from uuid import uuid4

from sonazyme.chassis.registry import parse
from sonazyme.core.manifest import append
from sonazyme.runs.store import RunStore

PRODUCER = {"name": "sonazyme.chassis", "version": "1", "kind": "code"}


def run(manifest: dict, *, store: RunStore, parameters: dict, inputs: list[str]) -> dict:
    """Select a sourced chassis matching a known anchor in a saved sense output."""
    if set(parameters) != {"registry"} or len(inputs) != 1:
        raise ValueError("chassis requires one sense input and a registry reference")
    previous = next(e for e in manifest["entries"] if e["id"] == inputs[0])
    if previous["stage"] != "sense" or previous["status"] != "succeeded":
        raise ValueError("chassis requires a successful sense entry")
    target = json.loads(store.read(previous["artefacts"][0]))
    record = parse(store.read(parameters["registry"]))
    if not any(
        a["component"].get("value") == record["anchor"]["component"]
        and a["bond"].get("value") == record["anchor"]["bond"]
        for a in target["anchor"]
    ):
        raise ValueError("Chassis does not match a known target anchor and bond")
    ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
    return append(
        manifest,
        {
            "id": f"chassis-{uuid4().hex}",
            "stage": "chassis",
            "status": "succeeded",
            "producer": PRODUCER,
            "inputs": inputs,
            "parameters": parameters,
            "metrics": [],
            "artefacts": [ref, parameters["registry"]],
            "reason": None,
        },
    )
