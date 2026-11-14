"""Versioned run records, with validation at every persistence boundary."""

from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from pathlib import Path

from sonazyme.core import STAGES


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_reference(ref: dict) -> None:
    """Reject references outside the content-addressed artefact layout."""
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "size_bytes"}:
        raise ValueError("An artefact requires path, sha256 and size_bytes")
    digest = ref["sha256"]
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid artefact sha256")
    if ref["path"] != f"artefacts/{digest}":
        raise ValueError("Artefact path must match its content address")
    if type(ref["size_bytes"]) is not int or ref["size_bytes"] < 0:
        raise ValueError("Invalid artefact size")


def validate(manifest: dict) -> None:
    """Check the v1 contract without trusting caller-owned dictionaries."""
    try:
        _validate(manifest)
    except (TypeError, OverflowError) as error:
        raise ValueError(f"Invalid manifest value: {error}") from error


def _validate(manifest: dict) -> None:
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "run_id",
        "target",
        "status",
        "entries",
    }:
        raise ValueError("Invalid manifest fields")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported manifest schema version")
    if not _text(manifest["run_id"]) or manifest["status"] not in {"running", "finished"}:
        raise ValueError("Invalid run id or status")
    validate_reference(manifest["target"])
    if not isinstance(manifest["entries"], list):
        raise ValueError("Entries must be a list")
    seen = set()
    for entry in manifest["entries"]:
        if not isinstance(entry, dict) or set(entry) != {
            "id",
            "stage",
            "status",
            "producer",
            "inputs",
            "parameters",
            "metrics",
            "artefacts",
            "reason",
        }:
            raise ValueError("Invalid entry fields")
        if not _text(entry["id"]) or entry["id"] in seen:
            raise ValueError("Entry ids must be non-empty and unique")
        if entry["stage"] not in STAGES:
            raise ValueError("Unknown stage")
        if entry["status"] not in {"succeeded", "failed", "rejected"}:
            raise ValueError("Invalid entry status")
        producer = entry["producer"]
        if not isinstance(producer, dict) or set(producer) != {"name", "version", "kind"}:
            raise ValueError("A producer requires name, version and kind")
        if not all(_text(producer[k]) for k in ("name", "version")):
            raise ValueError("Producer name and version are required")
        if producer["kind"] not in {"code", "model"}:
            raise ValueError("Invalid producer kind")
        if not isinstance(entry["inputs"], list) or any(
            not isinstance(i, str) or i not in seen for i in entry["inputs"]
        ):
            raise ValueError("Inputs must reference earlier entries")
        if not isinstance(entry["parameters"], dict):
            raise ValueError("Parameters must be an object")
        if not isinstance(entry["metrics"], list) or not isinstance(entry["artefacts"], list):
            raise ValueError("Metrics and artefacts must be lists")
        if entry["status"] != "succeeded":
            if not _text(entry["reason"]) or entry["metrics"]:
                raise ValueError("Failures and rejects require a reason and no metrics")
        elif entry["reason"] is not None:
            raise ValueError("Successful entries have no failure reason")
        for metric in entry["metrics"]:
            if not isinstance(metric, dict) or set(metric) != {
                "name",
                "value",
                "unit",
                "basis",
                "source",
            }:
                raise ValueError("Invalid metric fields")
            if not all(_text(metric[k]) for k in ("name", "unit")):
                raise ValueError("Metrics require a name and unit")
            if type(metric["value"]) not in {int, float} or not math.isfinite(metric["value"]):
                raise ValueError("Metric values must be finite numbers")
            if metric["basis"] not in {"prediction", "measurement"}:
                raise ValueError("Metrics must be labelled prediction or measurement")
            if metric["basis"] == "measurement" and not _text(metric["source"]):
                raise ValueError("Measurements require a citation")
            if metric["basis"] == "prediction" and (
                producer["kind"] != "model" or metric["source"] != producer
            ):
                raise ValueError("Predictions must cite their model producer")
        for ref in entry["artefacts"]:
            validate_reference(ref)
        seen.add(entry["id"])
    # Reject NaN in parameters too, and anything that cannot be replayed as JSON.
    encoded = json.dumps(manifest, allow_nan=False)
    if json.loads(encoded) != manifest:
        raise ValueError("Manifest values must survive a JSON round trip unchanged")


def create(run_id: str, target: dict) -> dict:
    """Start an empty run referencing a stored target."""
    manifest = dict(
        schema_version=1, run_id=run_id, target=deepcopy(target), status="running", entries=[]
    )
    validate(manifest)
    return manifest


def append(manifest: dict, entry: dict) -> dict:
    """Return a longer record without mutating either argument."""
    validate(manifest)
    if manifest["status"] != "running":
        raise ValueError("A finished run cannot be appended to")
    result = deepcopy(manifest)
    result["entries"].append(deepcopy(entry))
    validate(result)
    return result


def finish(manifest: dict) -> dict:
    """Seal a run, including a run containing failed attempts."""
    validate(manifest)
    result = deepcopy(manifest)
    result["status"] = "finished"
    return result


def load(path: Path) -> dict:
    """Read and validate a manifest; never migrate an unknown version silently."""
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate(manifest)
    return manifest
