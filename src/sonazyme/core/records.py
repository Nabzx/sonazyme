"""Shared artefact contracts, independent of individual stage implementations."""

from __future__ import annotations

import hashlib
import json

from sonazyme.core.protein import validate_sequence


def text(value: object) -> bool:
    """Return whether a required text field is present."""
    return isinstance(value, str) and bool(value.strip())


def validate_chassis(record: dict) -> None:
    """Require sequence provenance, construct mapping and a sourced catalytic core."""
    if record.get("schema_version") != 1 or record.get("kind") != "chassis":
        raise ValueError("Unsupported chassis record")
    if not all(text(record.get(k)) for k in ("id", "name", "selection_reason")):
        raise ValueError("Chassis identity and selection reason are required")
    sequence = record["sequence"]
    validate_sequence(sequence["value"])
    if not text(sequence.get("source")):
        raise ValueError("Chassis sequence source is required")
    if hashlib.sha256(sequence["value"].encode()).hexdigest() != sequence.get("sha256"):
        raise ValueError("Chassis sequence digest mismatch")
    mapping = sequence["mapping"]
    if not text(mapping.get("source")) or not text(mapping.get("reference")):
        raise ValueError("Construct mapping requires a source and reference")
    start, end = mapping["reference_start"], mapping["reference_end"]
    if type(start) is not int or type(end) is not int or start < 1:
        raise ValueError("Invalid reference range")
    if end - start + 1 != len(sequence["value"]):
        raise ValueError("Construct length and reference range disagree")
    anchor = record["anchor"]
    if not all(text(anchor.get(k)) for k in ("component", "bond", "source")):
        raise ValueError("Chassis anchor, bond and source are required")
    active = record["active_site"]
    if not text(active.get("source")) or not text(active.get("scope")):
        raise ValueError("Active-site source and scope are required")
    if type(record.get("design_ready")) is not bool:
        raise ValueError("Chassis design readiness must be explicit")
    residues = active["residues"]
    if not isinstance(residues, list) or not residues:
        raise ValueError("A non-empty active-site definition is required")
    seen = set()
    for residue in residues:
        position = residue["position"]
        if type(position) is not int or not 1 <= position <= len(sequence["value"]):
            raise ValueError("Protected position outside construct")
        if position in seen:
            raise ValueError("Duplicate protected position")
        seen.add(position)
        if residue["reference_position"] != start + position - 1:
            raise ValueError("Protected residue reference mapping disagrees")
        if sequence["value"][position - 1] != residue["amino_acid"]:
            raise ValueError("Protected residue identity disagrees with sequence")
        atoms = residue["atoms"]
        if not isinstance(atoms, list) or len(atoms) < 2 or not all(text(a) for a in atoms):
            raise ValueError("Protected atoms must be explicit")
        if len(set(atoms)) != len(atoms):
            raise ValueError("Duplicate protected atom")
    json.dumps(record, allow_nan=False)


def read_index(store, entry: dict, kind: str) -> dict:
    """Read the first artefact of a successful entry as its typed JSON index."""
    if entry["status"] != "succeeded" or not entry["artefacts"]:
        raise ValueError("A successful input entry with an artefact is required")
    record = json.loads(store.read(entry["artefacts"][0]))
    if record.get("kind") != kind or record.get("schema_version") != 1:
        raise ValueError(f"Expected a v1 {kind} artefact")
    return record
