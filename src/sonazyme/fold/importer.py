"""Bring an externally predicted structure into a run, with its provenance stated.

A structure that arrives as a file carries no record of what produced it, and
a structure with no producer cannot be shown (ADR-0004). So the importer
refuses to run without a model name and version supplied by the person doing
the importing, and records exactly what they said.

The imported artefact holds the backbone trace and per-residue confidence as
the file reported it. Nothing here re-folds, re-scores or infers anything.
"""

from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.runs.store import RunStore

# The three-letter residue codes a backbone trace may contain.
RESIDUES = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}  # fmt: skip


def parse_pdb(data: bytes, *, chain: str | None = None) -> dict:
    """Read the alpha-carbon trace of one chain, with its confidence column.

    The B-factor column of a predicted structure usually carries a per-residue
    confidence. It is kept as the file reported it and labelled as the file's
    own number, not as anything this repo computed.
    """
    points: list[dict] = []
    sequence: list[str] = []
    seen: set[tuple[str, int]] = set()
    chosen = chain
    for line in data.decode("utf-8", errors="strict").splitlines():
        if not line.startswith(("ATOM  ", "HETATM")):
            continue
        if line[12:16].strip() != "CA":
            continue
        residue_name = line[17:20].strip().upper()
        if residue_name not in RESIDUES:
            continue
        line_chain = line[21].strip() or "A"
        if chosen is None:
            chosen = line_chain
        if line_chain != chosen:
            continue
        try:
            position = int(line[22:26])
            xyz = [float(line[30:38]), float(line[38:46]), float(line[46:54])]
            confidence = float(line[60:66]) if line[60:66].strip() else None
        except ValueError as error:
            raise ValueError(f"Unreadable coordinate line: {error}") from None
        key = (line_chain, position)
        if key in seen:
            continue
        seen.add(key)
        points.append({"position": position, "xyz": xyz, "confidence": confidence})
        sequence.append(RESIDUES[residue_name])

    if len(points) < 2:
        raise ValueError("No alpha-carbon trace found in this file")
    points.sort(key=lambda point: point["position"])
    return {"chain": chosen, "points": points, "sequence": "".join(sequence)}


def structure_record(
    data: bytes,
    *,
    model: str,
    version: str,
    source_note: str,
    chain: str | None = None,
    active_site: list[int] | None = None,
    changed: list[int] | None = None,
) -> dict:
    """Build a structure artefact from a predicted file, provenance required."""
    for name, value in (("model", model), ("version", version), ("source_note", source_note)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"An imported structure requires {name}")
    trace = parse_pdb(data, chain=chain)
    positions = {point["position"] for point in trace["points"]}
    for label, selection in (("active_site", active_site or []), ("changed", changed or [])):
        for position in selection:
            if position not in positions:
                raise ValueError(f"{label} position {position} is not in this structure")
    confidences = [p["confidence"] for p in trace["points"] if p["confidence"] is not None]
    return {
        "schema_version": 1,
        "kind": "structure",
        "basis": "prediction",
        "producer": {"name": model, "version": version, "kind": "model"},
        "source_note": source_note,
        "chain": trace["chain"],
        "residue_count": len(trace["points"]),
        "sequence": trace["sequence"],
        "confidence": {
            "per_residue": "as reported in the file's B-factor column",
            "mean": round(sum(confidences) / len(confidences), 2) if confidences else None,
        },
        "points": trace["points"],
        "active_site": sorted(active_site or []),
        "changed": sorted(changed or []),
    }


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append an imported structure as a fold entry, with the stated producer."""
    parameters = parameters or {}
    ref = parameters["structure"]
    record = json.loads(store.read(ref))
    if record.get("kind") != "structure" or record.get("schema_version") != 1:
        raise ValueError("An imported fold entry needs a v1 structure record")
    producer = record["producer"]
    metrics = [
        {
            "name": metric["name"],
            "value": metric["value"],
            "unit": metric["unit"],
            "basis": "prediction",
            "source": producer,
        }
        for metric in parameters.get("metrics", [])
    ]
    return append(
        manifest,
        {
            "id": f"fold-{uuid4().hex}",
            "stage": "fold",
            "status": "succeeded",
            "producer": producer,
            "inputs": inputs or [],
            "parameters": parameters,
            "metrics": metrics,
            "artefacts": [ref],
            "reason": None,
        },
    )


def main(argv: list[str] | None = None) -> None:
    """Import one predicted structure file into a run."""
    import argparse
    from pathlib import Path

    from sonazyme.runs.runner import StageExecutionError, run_stage

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("structure", type=Path, help="a predicted structure, as PDB")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--model", required=True, help="the model that produced it")
    parser.add_argument("--model-version", required=True, help="its version")
    parser.add_argument(
        "--source-note",
        required=True,
        help="where this file came from, in one sentence, for the record",
    )
    parser.add_argument("--chain")
    parser.add_argument("--active-site", type=int, nargs="*", default=[])
    parser.add_argument(
        "--metric",
        action="append",
        default=[],
        metavar="NAME=VALUE=UNIT",
        help="a confidence number the predictor reported, recorded against it",
    )
    args = parser.parse_args(argv)
    try:
        data = args.structure.read_bytes()
        record = structure_record(
            data,
            model=args.model,
            version=args.model_version,
            source_note=args.source_note,
            chain=args.chain,
            active_site=args.active_site,
        )
        metrics = []
        for raw in args.metric:
            name, _, rest = raw.partition("=")
            value, _, unit = rest.partition("=")
            if not name.strip() or not unit.strip():
                raise ValueError("A metric reads NAME=VALUE=UNIT")
            metrics.append({"name": name.strip(), "value": float(value), "unit": unit.strip()})
        store = RunStore(args.run_dir)
        store.load()
        ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
        run_stage(
            store,
            stage="fold",
            producer=record["producer"],
            parameters={
                "structure": ref,
                "file_sha256": hashlib.sha256(data).hexdigest(),
                "metrics": metrics,
            },
            inputs=[],
            execute=run,
        )
    except (ValueError, KeyError, OSError, StageExecutionError) as error:
        parser.exit(2, f"Structure import failed: {error}\n")
    print(f"Structure recorded in {store.manifest_path}")
    print("Imported prediction. Not re-folded, not scored, no wet-lab result.")


if __name__ == "__main__":
    main()
