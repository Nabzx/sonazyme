"""Bring a mutation ranking into a run, split by whether it touches the site.

A ranking tool scores mutations on how favourable they look, which is not the
same as how useful they are. It will happily propose changing a catalytic
residue, because the thing it optimises does not know what the enzyme is for.

So the import splits the ranking in two: proposals that leave the active site
alone, and proposals that do not. The second group is recorded as a rejected
entry with its reason, not dropped, because what a search tried and lost is
information (ADR-0005).
"""

from __future__ import annotations

import csv
import io
import json
from uuid import uuid4

from sonazyme.core.manifest import append
from sonazyme.runs.store import RunStore

REQUIRED = {"score", "score_conservative", "score_std", "chain", "position", "wildtype", "mutant"}


def read_ranking(data: bytes) -> list[dict]:
    """Read a mutation ranking table, keeping only the fields we rely on."""
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    if not rows:
        raise ValueError("The ranking table is empty")
    missing = REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"The ranking table is missing {', '.join(sorted(missing))}")
    ranking = []
    for row in rows:
        try:
            ranking.append(
                {
                    "mutation": row.get("mutation")
                    or f"{row['wildtype']}{row['position']}{row['mutant']}",
                    "chain": row["chain"],
                    "position": int(row["position"]),
                    "wildtype": row["wildtype"],
                    "mutant": row["mutant"],
                    "score": float(row["score"]),
                    "score_conservative": float(row["score_conservative"]),
                    "score_std": float(row["score_std"]),
                }
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Unreadable ranking row: {error}") from None
    return ranking


def split(ranking: list[dict], active_site: list[int]) -> tuple[list[dict], list[dict]]:
    """Return proposals that leave the active site alone, and those that do not."""
    protected = set(active_site)
    kept = [row for row in ranking if row["position"] not in protected]
    touched = [row for row in ranking if row["position"] in protected]
    kept.sort(key=lambda row: row["score_conservative"], reverse=True)
    touched.sort(key=lambda row: row["score_conservative"], reverse=True)
    return kept, touched


def records(
    ranking: list[dict],
    *,
    chassis_id: str,
    active_site: list[int],
    model: str,
    version: str,
    source_note: str,
    keep: int = 24,
) -> tuple[dict, dict]:
    """Build the proposal record and the rejection record for one ranking."""
    if not model.strip() or not version.strip() or not source_note.strip():
        raise ValueError("An imported ranking requires a model, a version and a source note")
    kept, touched = split(ranking, active_site)
    producer = {"name": model, "version": version, "kind": "model"}
    common = {
        "schema_version": 1,
        "chassis_id": chassis_id,
        "producer": producer,
        "basis": "prediction",
        "source_note": source_note,
        "active_site": sorted(active_site),
        "scored": len(ranking),
    }
    proposals = {
        **common,
        "kind": "variant-proposals",
        "note": (
            "Single point mutations ranked by predicted favourability, with every mutation "
            "at a catalytic residue removed before ranking. A score here is a prediction "
            "about the fold, not about whether the enzyme still cuts anything."
        ),
        "proposals": kept[:keep],
    }
    rejected = {
        **common,
        "kind": "variant-rejections",
        "note": (
            "Mutations the ranking favoured that fall on a catalytic residue. They are kept "
            "because what a search proposed and lost is information, and because a model "
            "that ranks on stability has no way of knowing what the enzyme is for."
        ),
        "rejected": touched[: keep * 2],
        "reason": "Mutates a catalytic residue",
    }
    return proposals, rejected


def run(
    manifest: dict,
    *,
    store: RunStore,
    parameters: dict | None = None,
    inputs: list[str] | None = None,
) -> dict:
    """Append one record: proposals as a design entry, rejections as a rejected one.

    The runner appends exactly one entry per call, so a ranking lands as two
    calls: what survived the active site, and what did not.
    """
    parameters = parameters or {}
    record = json.loads(store.read(parameters["record"]))
    kind = record.get("kind")
    if kind not in ("variant-proposals", "variant-rejections"):
        raise ValueError("A design import needs a proposal or rejection record")
    rejected = kind == "variant-rejections"
    reason = None
    if rejected:
        reason = (
            f"{len(record['rejected'])} proposals fall on a catalytic residue "
            f"({', '.join(str(p) for p in record['active_site'])}) and are not designs."
        )
    return append(
        manifest,
        {
            "id": f"design-{uuid4().hex}",
            "stage": "design",
            "status": "rejected" if rejected else "succeeded",
            "producer": record["producer"],
            "inputs": inputs or [],
            "parameters": parameters,
            "metrics": [],
            "artefacts": [parameters["record"]],
            "reason": reason,
        },
    )
