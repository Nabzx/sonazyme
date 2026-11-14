"""Filter catalytic geometry before stability scoring, with an explicit policy."""

from __future__ import annotations

import json
import math
import re
from itertools import combinations
from uuid import uuid4

from sonazyme.core.folding import comparison_settings, model_producer, validate_settings
from sonazyme.core.manifest import append
from sonazyme.core.protein import read_pdb
from sonazyme.core.records import read_index, text, validate_chassis
from sonazyme.runs.store import RunStore

PRODUCER = {"name": "sonazyme.integrity", "version": "1", "kind": "code"}


def validate_policy(policy: dict) -> None:
    """Require a fixed threshold and distinguish software fixtures from agreed policies."""
    if policy.get("schema_version") != 1 or policy.get("kind") != "integrity-policy":
        raise ValueError("Unsupported integrity policy")
    if policy.get("method") != "max-pair-distance-v1":
        raise ValueError("Unsupported integrity method")
    if not text(policy.get("rationale")) or not text(policy.get("agreement")):
        raise ValueError("Integrity policy requires rationale and prior agreement reference")
    if policy.get("purpose") not in ("production", "software-test"):
        raise ValueError("Integrity policy purpose must be explicit")
    if policy["purpose"] == "production" and not re.fullmatch(
        r"https://github.com/Nabzx/sonazyme/issues/28#issuecomment-[0-9]+", policy["agreement"]
    ):
        raise ValueError("Production tolerance must reference its prior agreement on #28")
    for name, upper in (("max_distance_change_angstrom", math.inf), ("min_active_site_plddt", 1)):
        value = policy.get(name)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= upper:
            raise ValueError(f"Invalid integrity policy field: {name}")


def _handedness(atoms: dict, position: int) -> float:
    center = atoms[(position, "CA")]
    vectors = [
        tuple(a - b for a, b in zip(atoms[(position, name)], center, strict=True))
        for name in ("N", "C", "CB")
    ]
    a, b, c = vectors
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def check(chassis: dict, baseline: dict, variant: dict, policy: dict) -> dict:
    """Compare parsed predicted coordinates; passing is not an activity prediction."""
    validate_chassis(chassis)
    validate_policy(policy)
    keys = [
        (r["position"], atom) for r in chassis["active_site"]["residues"] for atom in r["atoms"]
    ]
    missing = [
        f"{p}:{a}"
        for p, a in keys
        if (p, a) not in baseline["atoms"] or (p, a) not in variant["atoms"]
    ]
    report = {
        "schema_version": 1,
        "kind": "integrity",
        "producer": PRODUCER,
        "basis": "prediction-derived geometry filter",
        "purpose": policy["purpose"],
        "passed": False,
        "reason": None,
        "max_distance_change_angstrom": None,
        "min_active_site_plddt": None,
        "notice": "Catalytic-core filter only. No activity guarantee or Sonazyme wet-lab result.",
    }
    if missing:
        report["reason"] = "Missing protected atoms: " + ", ".join(missing)
        return report
    maximum = max(
        abs(
            math.dist(baseline["atoms"][a], baseline["atoms"][b])
            - math.dist(variant["atoms"][a], variant["atoms"][b])
        )
        for a, b in combinations(keys, 2)
    )
    minimum_confidence = min(
        parsed["confidence"][r["position"]]
        for parsed in (baseline, variant)
        for r in chassis["active_site"]["residues"]
    )
    report.update(max_distance_change_angstrom=maximum, min_active_site_plddt=minimum_confidence)
    for residue in chassis["active_site"]["residues"]:
        p = residue["position"]
        if residue["amino_acid"] != "G":
            if any(
                (p, name) not in parsed["atoms"]
                for parsed in (baseline, variant)
                for name in ("N", "CA", "C", "CB")
            ):
                report["reason"] = "Missing atoms needed for the handedness check"
                return report
            if _handedness(baseline["atoms"], p) * _handedness(variant["atoms"], p) <= 0:
                report["reason"] = "Protected residue handedness changed or is degenerate"
                return report
    if minimum_confidence < policy["min_active_site_plddt"]:
        report["reason"] = "Active-site predicted confidence is below the fixed policy"
    elif maximum > policy["max_distance_change_angstrom"]:
        report["reason"] = "Active-site geometry is outside the fixed tolerance"
    else:
        report.update(passed=True, reason=None)
    return report


def run(manifest: dict, *, store: RunStore, parameters: dict, inputs: list[str]) -> dict:
    """Append an integrity verdict for one baseline/variant pair, without scoring stability."""
    if (
        set(parameters) != {"role", "policy"}
        or parameters["role"] != "integrity"
        or len(inputs) != 3
    ):
        raise ValueError("Integrity requires chassis, baseline and variant inputs, plus a policy")
    entries = {e["id"]: e for e in manifest["entries"]}
    parent_entry, baseline_entry, variant_entry = [entries[i] for i in inputs]
    if [e["stage"] for e in (parent_entry, baseline_entry, variant_entry)] != [
        "chassis",
        "fold",
        "fold",
    ]:
        raise ValueError("Integrity inputs must be ordered chassis, baseline fold, variant fold")
    chassis = read_index(store, parent_entry, "chassis")
    validate_chassis(chassis)
    baseline = read_index(store, baseline_entry, "fold")
    variant = read_index(store, variant_entry, "fold")
    policy = json.loads(store.read(parameters["policy"]))
    validate_policy(policy)
    for fold, entry in ((baseline, baseline_entry), (variant, variant_entry)):
        validate_settings(fold["settings"])
        if (
            fold["producer"] != model_producer(fold["settings"])
            or fold["producer"] != entry["producer"]
        ):
            raise ValueError("Fold model provenance disagrees with its entry")
        if fold["chassis_id"] != chassis["id"] or parent_entry["id"] not in entry["inputs"]:
            raise ValueError("Fold does not reference the declared chassis entry")
        if fold["pdb"] not in entry["artefacts"]:
            raise ValueError("Fold coordinates are not in its artefact chain")
    if baseline["producer"] != variant["producer"] or comparison_settings(
        baseline["settings"]
    ) != comparison_settings(variant["settings"]):
        raise ValueError("Baseline and variant must use the same model and inference policy")
    if baseline["role"] != "baseline" or variant["role"] != "variant":
        raise ValueError("Expected a baseline and a variant fold")
    if baseline["sequence"] != chassis["sequence"]["value"]:
        raise ValueError("Predicted baseline sequence differs from the chassis")
    if len(variant["sequence"]) != len(baseline["sequence"]):
        raise ValueError("Integrity supports substitution variants only")
    parsed = [read_pdb(store.read(fold["pdb"]), fold["sequence"]) for fold in (baseline, variant)]
    report = check(chassis, *parsed, policy)
    if any(
        variant["sequence"][r["position"] - 1] != r["amino_acid"]
        for r in chassis["active_site"]["residues"]
    ):
        report.update(passed=False, reason="Variant changes a protected residue")
    report.update(
        inputs=inputs, policy=parameters["policy"], structure_producer=baseline["producer"]
    )
    ref = store.put(json.dumps(report, allow_nan=False).encode())
    return append(
        manifest,
        {
            "id": f"integrity-{uuid4().hex}",
            "stage": "score",
            "status": "succeeded" if report["passed"] else "rejected",
            "producer": PRODUCER,
            "inputs": inputs,
            "parameters": parameters,
            "metrics": [],
            "artefacts": [ref, parameters["policy"]],
            "reason": report["reason"],
        },
    )


def require_integrity(
    manifest: dict,
    store: RunStore,
    baseline_id: str,
    variant_id: str,
    *,
    policy: dict,
) -> dict:
    """Require a production-policy pass on these exact folds before stability scoring."""
    for entry in reversed(manifest["entries"]):
        if entry["stage"] != "score" or entry["producer"] != PRODUCER:
            continue
        if entry["parameters"].get("role") != "integrity":
            continue
        if (
            entry["inputs"][1:] != [baseline_id, variant_id]
            or entry["parameters"]["policy"] != policy
        ):
            continue
        if entry["status"] != "succeeded":
            break
        report = read_index(store, entry, "integrity")
        agreement = json.loads(store.read(policy))
        validate_policy(agreement)
        parents = {e["id"]: e for e in manifest["entries"]}
        chassis = read_index(store, parents[entry["inputs"][0]], "chassis")
        validate_chassis(chassis)
        if (
            agreement["purpose"] == "production"
            and report["purpose"] == "production"
            and report["passed"] is True
            and report["inputs"] == entry["inputs"]
            and report["policy"] == policy
            and chassis["design_ready"] is True
        ):
            return report
    raise ValueError("No passing production integrity check for these exact fold inputs")
