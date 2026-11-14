"""Shared fold request and artefact contracts, with no stage-to-stage imports."""

from __future__ import annotations

import re

from sonazyme.core.protein import validate_sequence
from sonazyme.core.records import text


def model_producer(settings: dict) -> dict:
    """Name the actual package and checkpoint, rather than a mutable model alias."""
    return {
        "name": "Boltz-2",
        "version": f"{settings['package_version']}/sha256:{settings['checkpoint_sha256']}",
        "kind": "model",
    }


def validate_settings(settings: dict) -> None:
    """Require explicit inference settings; no environment input is implied."""
    if set(settings) != {
        "adapter_version",
        "package_version",
        "checkpoint_sha256",
        "seed",
        "accelerator",
        "recycling_steps",
        "sampling_steps",
        "msa",
        "ligand",
    }:
        raise ValueError("Invalid fold settings")
    if settings["adapter_version"] != "1" or not text(settings["package_version"]):
        raise ValueError("Explicit adapter and Boltz package versions are required")
    if not re.fullmatch(r"[0-9a-f]{64}", settings["checkpoint_sha256"]):
        raise ValueError("Explicit checkpoint SHA-256 is required")
    for field in ("seed", "recycling_steps", "sampling_steps"):
        if type(settings[field]) is not int or settings[field] < (0 if field == "seed" else 1):
            raise ValueError(f"Invalid {field}")
    if settings["accelerator"] not in ("cpu", "gpu"):
        raise ValueError("Select cpu or gpu explicitly")
    msa = settings["msa"]
    if not isinstance(msa, dict) or msa.get("mode") not in ("single", "provided"):
        raise ValueError("An explicit MSA policy is required")
    expected = {"mode"} if msa["mode"] == "single" else {"mode", "artefact"}
    if set(msa) != expected:
        raise ValueError("Invalid MSA fields")
    ligand = settings["ligand"]
    if ligand is not None and (
        not isinstance(ligand, dict)
        or set(ligand) != {"format", "value", "source"}
        or ligand["format"] not in ("smiles", "ccd")
        or not all(text(ligand[k]) for k in ("value", "source"))
    ):
        raise ValueError("A ligand requires a sourced SMILES or CCD identifier")


def subject_sequence(subject: dict, chassis: dict) -> str:
    """Verify substitutions and protected identities before a fold request."""
    parent = chassis["sequence"]["value"]
    if subject.get("kind") == "chassis":
        if subject != chassis:
            raise ValueError("Baseline subject differs from the selected chassis")
        return parent
    if subject.get("schema_version") != 1 or subject.get("kind") != "variant":
        raise ValueError("Unsupported fold subject")
    if not text(subject.get("id")) or subject.get("chassis_id") != chassis["id"]:
        raise ValueError("Variant must identify the selected chassis")
    if not chassis["design_ready"]:
        raise ValueError("Chassis binding-site exclusion is incomplete; variant folding is blocked")
    sequence = subject["sequence"]
    validate_sequence(sequence)
    if len(sequence) != len(parent):
        raise ValueError("Only substitution variants are supported")
    mutations = subject["mutation_set"]
    if not isinstance(mutations, list) or len(set(mutations)) != len(mutations):
        raise ValueError("Mutation set must be a unique list")
    actual = [
        f"{a}{i}{b}" for i, (a, b) in enumerate(zip(parent, sequence, strict=True), 1) if a != b
    ]
    if sorted(actual) != sorted(mutations):
        raise ValueError("Mutation set does not match the sequence")
    if any(
        sequence[r["position"] - 1] != r["amino_acid"] for r in chassis["active_site"]["residues"]
    ):
        raise ValueError("Variant changes a protected residue")
    return sequence


def request_document(sequence: str, settings: dict) -> dict:
    """Build YAML-compatible JSON without allowing caller-supplied YAML fragments."""
    protein = {"id": "A", "sequence": sequence}
    protein["msa"] = "empty" if settings["msa"]["mode"] == "single" else "protein.a3m"
    request = {"version": 1, "sequences": [{"protein": protein}]}
    if settings["ligand"] is not None:
        ligand = settings["ligand"]
        request["sequences"].append({"ligand": {"id": "B", ligand["format"]: ligand["value"]}})
    return request


def comparison_settings(settings: dict) -> dict:
    """Compare inference policy while allowing sequence-specific MSA bytes."""
    return {**settings, "msa": {"mode": settings["msa"]["mode"]}}
