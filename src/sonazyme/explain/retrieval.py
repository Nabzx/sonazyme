"""What a run actually contains, assembled so every statement can cite it.

This is the retrieval half of the scientist (#31). It reads a run's manifest
and its artefacts and returns facts, each carrying the entry and artefact it
came from. Nothing here interprets, scores or compares: a fact is present or
it is not, and what is not present is listed too, because the gaps are what
the refusals are built from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from sonazyme.core import STAGES
from sonazyme.runs.store import RunStore


@dataclass(frozen=True)
class Citation:
    """Where a fact came from: an entry, and the artefact it was read from."""

    entry_id: str
    stage: str
    producer: str
    artefact_sha256: str | None = None

    def as_dict(self) -> dict:
        """Return the citation in the shape the dashboard renders."""
        return {
            "entry_id": self.entry_id,
            "stage": self.stage,
            "producer": self.producer,
            "artefact_sha256": self.artefact_sha256,
        }


@dataclass
class Index:
    """A run, read once, with its records and its gaps both explicit."""

    run_id: str
    status: str
    target: dict | None = None
    chassis: dict | None = None
    structures: list[dict] = field(default_factory=list)
    readings: list[dict] = field(default_factory=list)
    designs: list[dict] = field(default_factory=list)
    rejections: list[dict] = field(default_factory=list)
    scores: list[dict] = field(default_factory=list)
    fold_metrics: list[dict] = field(default_factory=list)
    ranked: list[dict] = field(default_factory=list)
    citations: dict[str, Citation] = field(default_factory=dict)
    stages_present: set[str] = field(default_factory=set)
    rejected: list[dict] = field(default_factory=list)

    def missing(self) -> list[str]:
        """Stages this run has no successful entry for, in pipeline order."""
        return [stage for stage in STAGES if stage not in self.stages_present]

    def cite(self, key: str) -> dict | None:
        """Return one citation as a dictionary, if the fact was recorded."""
        citation = self.citations.get(key)
        return citation.as_dict() if citation else None


def _producer(entry: dict) -> str:
    return f"{entry['producer']['name']} {entry['producer']['version']}"


def build(store: RunStore, manifest: dict | None = None) -> Index:
    """Read a run into an index, verifying every artefact on the way."""
    manifest = manifest or store.load()
    index = Index(run_id=manifest["run_id"], status=manifest["status"])

    for entry in manifest["entries"]:
        if entry["status"] == "rejected":
            index.rejected.append(
                {"id": entry["id"], "stage": entry["stage"], "reason": entry["reason"]}
            )
        if entry["status"] == "failed":
            continue
        if entry["status"] == "succeeded":
            index.stages_present.add(entry["stage"])
        for ref in entry["artefacts"]:
            try:
                record = json.loads(store.read(ref))
            except (ValueError, OSError):
                # An artefact that will not verify is not a fact about anything.
                continue
            if not isinstance(record, dict):
                continue
            citation = Citation(entry["id"], entry["stage"], _producer(entry), ref["sha256"])
            kind = record.get("kind")
            if entry["stage"] == "sense" and kind == "reading":
                index.readings.append(record)
                index.citations.setdefault("reading", citation)
                index.citations[f"reading:{len(index.readings)}"] = citation
            elif entry["stage"] == "sense" and "target" in record:
                index.target = record
                index.citations["target"] = citation
            elif kind == "chassis":
                index.chassis = record
                index.citations["chassis"] = citation
            elif kind == "structure":
                index.structures.append(record)
                index.citations.setdefault("structure", citation)
            elif kind == "variant":
                index.designs.append(record)
                index.citations.setdefault("design", citation)
            elif kind == "variant-proposals":
                index.designs.extend(record.get("proposals", []))
                index.citations.setdefault("design", citation)
            elif kind == "variant-rejections":
                index.rejections.append(record)
                index.citations.setdefault("rejection", citation)
        if entry["stage"] == "score" and entry["metrics"]:
            index.scores.append({"entry": entry["id"], "metrics": entry["metrics"]})
            index.citations.setdefault(
                "score", Citation(entry["id"], entry["stage"], _producer(entry))
            )
        if entry["stage"] == "rank":
            index.ranked.append({"entry": entry["id"], "parameters": entry["parameters"]})
            index.citations.setdefault(
                "rank", Citation(entry["id"], entry["stage"], _producer(entry))
            )
        if entry["stage"] == "fold" and entry["metrics"]:
            # A fold confidence is not a stability score. Keeping them apart is
            # what lets the scientist refuse a comparison it cannot make.
            index.citations.setdefault(
                "fold-metrics", Citation(entry["id"], entry["stage"], _producer(entry))
            )
            index.fold_metrics.append({"entry": entry["id"], "metrics": entry["metrics"]})

    return index
