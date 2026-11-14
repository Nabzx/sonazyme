"""The fold stage: a predicted structure per variant, through Boltz-2.

Folds the chassis and every variant with the same model at the same version,
carrying confidence through. See docs/platform/boltz2.md.
"""

from __future__ import annotations

import json
import math
from uuid import uuid4

from sonazyme.core.folding import (
    model_producer,
    request_document,
    subject_sequence,
    validate_settings,
)
from sonazyme.core.manifest import append
from sonazyme.core.protein import read_pdb
from sonazyme.core.records import read_index, validate_chassis
from sonazyme.runs.store import RunStore


def run(manifest: dict, *, store: RunStore, parameters: dict, inputs: list[str], backend) -> dict:
    """Fold a declared subject and preserve raw coordinates and confidence predictions."""
    if set(parameters) != {"subject", "settings"}:
        raise ValueError("fold requires subject and settings")
    settings = parameters["settings"]
    validate_settings(settings)
    entries = [e for e in manifest["entries"] if e["id"] in inputs]
    parents = [e for e in entries if e["stage"] == "chassis"]
    if len(parents) != 1 or len(entries) != len(inputs):
        raise ValueError("fold requires exactly one declared chassis input")
    if any(e["status"] != "succeeded" for e in entries):
        raise ValueError("fold inputs must be successful")
    if not any(parameters["subject"] in e["artefacts"] for e in entries):
        raise ValueError("Fold subject must be an artefact of a declared input")
    chassis = read_index(store, parents[0], "chassis")
    validate_chassis(chassis)
    subject = json.loads(store.read(parameters["subject"]))
    sequence = subject_sequence(subject, chassis)
    document = request_document(sequence, settings)
    msa_ref = settings["msa"].get("artefact")
    msa = store.read(msa_ref) if msa_ref is not None else None
    pdb_data, raw_confidence = backend.predict(document, settings, msa)
    parsed = read_pdb(pdb_data, sequence)
    aggregate = json.loads(raw_confidence)
    for name in ("confidence_score", "complex_plddt"):
        value = aggregate.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("Missing or invalid Boltz confidence summary")
    model = model_producer(settings)
    confidence = {
        "basis": "prediction",
        "producer": model,
        "aggregate": aggregate,
        "per_residue_plddt": {str(k): v for k, v in parsed["confidence"].items()},
        "active_site_plddt": {
            str(r["position"]): parsed["confidence"][r["position"]]
            for r in chassis["active_site"]["residues"]
        },
        "method": "PDB B-factor pLDDT divided by 100; rounded by the Boltz PDB writer",
    }
    refs = [
        store.put(data)
        for data in (
            pdb_data,
            raw_confidence,
            json.dumps(confidence, allow_nan=False).encode(),
            json.dumps(document, allow_nan=False).encode(),
        )
    ]
    index = {
        "schema_version": 1,
        "kind": "fold",
        "basis": "prediction",
        "producer": model,
        "subject_id": subject["id"],
        "chassis_id": chassis["id"],
        "sequence": sequence,
        "role": "baseline" if subject["kind"] == "chassis" else "variant",
        "settings": settings,
        "subject": parameters["subject"],
        "pdb": refs[0],
        "raw_confidence": refs[1],
        "confidence": refs[2],
        "request": refs[3],
        "notice": "Predicted structure and confidence only. No Sonazyme wet-lab result.",
    }
    index_ref = store.put(json.dumps(index, allow_nan=False).encode())
    return append(
        manifest,
        {
            "id": f"fold-{uuid4().hex}",
            "stage": "fold",
            "status": "succeeded",
            "producer": model,
            "inputs": inputs,
            "parameters": parameters,
            "metrics": [
                {
                    "name": k,
                    "value": aggregate[k],
                    "unit": "dimensionless",
                    "basis": "prediction",
                    "source": model,
                }
                for k in ("confidence_score", "complex_plddt")
            ],
            "artefacts": [index_ref, *refs, *([msa_ref] if msa_ref is not None else [])],
            "reason": None,
        },
    )
