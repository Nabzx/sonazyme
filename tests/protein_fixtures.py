"""Synthetic protocol fixtures only; coordinates and confidence are not model results."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from sonazyme.chassis import run as select_chassis
from sonazyme.core.folding import model_producer
from sonazyme.core.manifest import append, create
from sonazyme.fold import run as fold
from sonazyme.runs.runner import run_stage
from sonazyme.runs.store import RunStore
from sonazyme.sense import run as sense

ROOT = Path(__file__).resolve().parents[1]
REAL_RECORD = ROOT / "targets/chassis/pslg-31-442.json"
ATOM_NAMES = ["N", "CA", "C", "O", "CB", "CG", "CD", "OE1", "OE2"]
CODE = {"name": "software-fixture", "version": "1", "kind": "code"}


def chassis_record():
    # A tiny artificial sequence; it is not the sourced PslG chassis.
    real = json.loads(REAL_RECORD.read_text())
    sequence = "AEG"
    return {
        "schema_version": 1,
        "kind": "chassis",
        "id": "software-fixture",
        "name": "Software fixture only",
        "selection_reason": "Protocol test, no biological claim",
        "design_ready": True,
        "anchor": real["anchor"],
        "sequence": {
            "value": sequence,
            "sha256": hashlib.sha256(sequence.encode()).hexdigest(),
            "source": "software fixture, not a biological sequence source",
            "mapping": {
                "reference": "software fixture",
                "reference_start": 1,
                "reference_end": 3,
                "source": "software fixture, not a measurement",
            },
        },
        "active_site": {
            "scope": "software fixture only",
            "source": "software fixture only",
            "residues": [
                {"position": 2, "reference_position": 2, "amino_acid": "E", "atoms": ATOM_NAMES}
            ],
        },
    }


def pdb(sequence="AEG", shift=0.0, transform=None, omit=None, confidence=90):
    # All numbers are chosen software fixtures, not molecular measurements.
    offsets = dict(
        N=(-1, 1, 0),
        CA=(0, 0, 0),
        C=(1, 0, 0),
        O=(1, 1, 0),
        CB=(0, 0, 1),
        CG=(0, 1, 2),
        CD=(0, 1, 3),
        OE1=(1, 1, 3),
        OE2=(-1, 1, 3),
    )
    residues = dict(A="ALA", V="VAL", E="GLU", G="GLY")
    lines = []
    for position, residue in enumerate(sequence, 1):
        for atom in ATOM_NAMES:
            if (position, atom) == omit:
                continue
            x, y, z = offsets[atom]
            x += position * 5
            if position == 2 and atom == "OE1":
                x += shift
            if transform:
                x, y, z = transform(x, y, z)
            lines.append(
                f"ATOM  {len(lines) + 1:5d} {atom:^4s} {residues[residue]:3s} A{position:4d}    "
                f"{x:8.3f}{y:8.3f}{z:8.3f}{1:6.2f}{confidence:6.2f}           C"
            )
    return ("\n".join(lines) + "\nEND\n").encode()


class FakeBoltz:
    def __init__(self, **pdb_arguments):
        self.calls = []
        self.pdb_arguments = pdb_arguments

    def predict(self, request, settings, msa):
        self.calls.append((request, settings, msa))
        return (
            pdb(request["sequences"][0]["protein"]["sequence"], **self.pdb_arguments),
            b'{"confidence_score": 0.8, "complex_plddt": 0.9, "notice": "software fixture"}',
        )


def settings():
    return {
        "adapter_version": "1",
        "package_version": "software-fixture-not-a-model",
        "checkpoint_sha256": "a" * 64,
        "seed": 1,
        "accelerator": "cpu",
        "recycling_steps": 1,
        "sampling_steps": 1,
        "msa": {"mode": "single"},
        "ligand": None,
    }


def prepare(tmp_path, record=None):
    store = RunStore(tmp_path)
    target = store.put((ROOT / "targets/psl-literature.toml").read_bytes())
    manifest = create("software-fixture", target)
    store.save(manifest)
    manifest = sense(manifest, store=store)
    store.save(manifest)
    ref = store.put(json.dumps(record or chassis_record()).encode())
    manifest = select_chassis(
        manifest, store=store, parameters={"registry": ref}, inputs=[manifest["entries"][-1]["id"]]
    )
    store.save(manifest)
    return store, manifest["entries"][-1]


def variant(store, parent):
    record = {
        "schema_version": 1,
        "kind": "variant",
        "id": "software-variant",
        "chassis_id": "software-fixture",
        "sequence": "VEG",
        "mutation_set": ["A1V"],
    }
    ref = store.put(json.dumps(record).encode())
    design = {
        "id": uuid4().hex,
        "stage": "design",
        "status": "succeeded",
        "producer": CODE,
        "parameters": {},
        "inputs": [parent["id"]],
        "metrics": [],
        "artefacts": [ref],
        "reason": None,
    }
    store.save(append(store.load(), design))
    return ref, design["id"]


def fold_subject(store, parent, subject=None, design_id=None, backend=None, config=None):
    config = deepcopy(config or settings())
    parameters = {"subject": subject or parent["artefacts"][0], "settings": config}
    inputs = [parent["id"], *([design_id] if design_id else [])]

    def execute(manifest, **kwargs):
        return fold(manifest, backend=backend or FakeBoltz(), **kwargs)

    result = run_stage(
        store,
        stage="fold",
        producer=model_producer(config),
        parameters=parameters,
        inputs=inputs,
        execute=execute,
    )
    return result["entries"][-1]


def policy():
    return {
        "schema_version": 1,
        "kind": "integrity-policy",
        "method": "max-pair-distance-v1",
        "purpose": "software-test",
        "agreement": "software fixture only, no biological approval",
        "rationale": "Chosen test boundary, not a biological tolerance",
        "max_distance_change_angstrom": 0.2,
        "min_active_site_plddt": 0.5,
    }
