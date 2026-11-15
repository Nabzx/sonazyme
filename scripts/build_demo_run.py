"""Build the demo run from the NucB pipeline outputs, through the normal importers.

Nothing here invents a number. Every structure is a file the predictor wrote, and
every score is read from the pipeline's own tables.

One conversion happens on the way in. The pipeline folded the 110-residue mature
chain, numbered 1 to 110. This repository models the 142-residue precursor, and
the mature chain is precursor residues 33 to 142. Variant structures are
renumbered by adding 32 so that one numbering frame holds for the chassis, the
wild-type fold, the ranking and the dashboard.

Usage:
    python scripts/build_demo_run.py --pipeline <nucb-pipeline dir> --run-dir runs/demo
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402

from sonazyme.core.manifest import create  # noqa: E402
from sonazyme.design.importer import read_ranking, records  # noqa: E402
from sonazyme.design.importer import run as design_run  # noqa: E402
from sonazyme.fold.importer import run as fold_run  # noqa: E402
from sonazyme.fold.importer import structure_record  # noqa: E402
from sonazyme.runs.runner import run_stage  # noqa: E402
from sonazyme.runs.store import RunStore  # noqa: E402
from sonazyme.sense import PRODUCER as SENSE_PRODUCER  # noqa: E402
from sonazyme.sense import run as sense_run  # noqa: E402
from sonazyme.sense.targets import parse as parse_target  # noqa: E402

OFFSET = 32
ACTIVE_SITE = [53, 93, 94, 108, 117]
BOLTZ = ("boltz", "2.2.1")


def renumber(pdb: bytes, offset: int) -> bytes:
    """Shift every residue number in an ATOM/HETATM record by `offset`."""
    out = []
    for line in pdb.decode("utf-8", "replace").splitlines():
        if line.startswith(("ATOM", "HETATM")) and len(line) >= 26:
            number = int(line[22:26]) + offset
            line = f"{line[:22]}{number:>4}{line[26:]}"
        out.append(line)
    return ("\n".join(out) + "\n").encode()


def import_structure(store, data: bytes, *, note: str, changed: list[int],
                     metrics: list[dict]) -> None:
    record = structure_record(
        data, model=BOLTZ[0], version=BOLTZ[1], source_note=note,
        chain="A", active_site=ACTIVE_SITE, changed=changed,
    )
    ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
    run_stage(
        store, stage="fold", producer=record["producer"],
        # `changed` is recorded on the entry as well as inside the structure, so
        # a reader can tell a variant from its parent without fetching and
        # verifying every artefact first.
        parameters={"structure": ref, "file_sha256": hashlib.sha256(data).hexdigest(),
                    "changed": sorted(changed), "metrics": metrics},
        inputs=[], execute=fold_run,
    )


def metric(name: str, value, unit: str) -> dict:
    return {"name": name, "value": float(value), "unit": unit}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pipeline", type=Path, required=True)
    p.add_argument("--run-dir", type=Path, default=ROOT / "runs" / "demo")
    p.add_argument("--target", type=Path, default=ROOT / "targets" / "edna-literature.toml")
    p.add_argument("--top", type=int, default=10)
    args = p.parse_args()

    pipe = args.pipeline.resolve()
    store = RunStore(args.run_dir)

    # 1. The target, which creates the run.
    data = args.target.read_bytes()
    target = parse_target(data)
    if not store.manifest_path.exists():
        store.save(create(target["target"]["id"], store.put(data)))
    run_stage(store, stage="sense", producer=SENSE_PRODUCER, parameters={}, inputs=[],
              execute=sense_run)
    print(f"sense: {target['target']['id']}")

    # 2. The chassis, through its own importer CLI.
    from sonazyme.chassis.__main__ import main as chassis_main

    chassis_main([str(ROOT / "targets" / "chassis" / "nucb-precursor.json"),
                  "--run-dir", str(args.run_dir)])

    # 3. The wild type, already in precursor numbering.
    wt = ROOT / "docs" / "result-NucB_Biofilm_DNase" / "best.pdb"
    import_structure(
        store, wt.read_bytes(),
        note="Boltz 2.2.1 prediction of the 142-residue precursor, best of five by "
             "confidence, committed to this repository.",
        changed=[], metrics=[],
    )
    print("fold: wild type (precursor, 142 residues)")

    # 4. The variants, renumbered from the mature chain into precursor coordinates.
    checks = pd.read_csv(pipe / "output" / "structural_check.csv")
    labels = []
    for row in checks.head(args.top).itertuples():
        short = row.variant.replace("nucb-", "")
        src = pipe / "work" / "folds" / f"{row.variant}.pdb"
        if not src.exists():
            print(f"  skipped {short}: no folded structure")
            continue
        mature_pos = int(re.findall(r"\d+", row.mutations)[0])
        pos = mature_pos + OFFSET
        label = f"{row.mutations[0]}{pos}{row.mutations[-1]}"
        conf = json.loads(
            (pipe / "jobs" / "results" / f"{row.variant}-fold"
             / "confidence_result_model_0.json").read_text(encoding="utf-8"))
        import_structure(
            store, renumber(src.read_bytes(), OFFSET),
            note=f"Boltz 2.2.1 prediction of the mature chain carrying {label}, "
                 f"renumbered into precursor coordinates by adding {OFFSET}. "
                 f"Proposed by ThermoMPNN.",
            changed=[pos],
            metrics=[
                metric("thermompnn_ddg", row.ddg, "kcal/mol"),
                metric("backbone_rmsd_to_wild_type", row.global_rmsd_a, "angstrom"),
                metric("catalytic_rmsd_to_wild_type", row.catalytic_rmsd_a, "angstrom"),
                metric("plddt", conf["complex_plddt"], "fraction"),
                metric("ptm", conf["ptm"], "fraction"),
            ],
        )
        labels.append(label)
        print(f"fold: {label}  ddG {row.ddg:+.2f}  RMSD {row.global_rmsd_a} A")

    # 5. The ranking, split by the active site by the importer itself.
    ranking_csv = pipe / "output" / "thermompnn_precursor.csv"
    ranking = read_ranking(ranking_csv.read_bytes())
    manifest = store.load()
    chassis_entry = [e for e in manifest["entries"]
                     if e["stage"] == "chassis" and e["status"] == "succeeded"][-1]
    proposals, rejected = records(
        ranking, chassis_id="nucb-precursor", active_site=ACTIVE_SITE,
        model="ThermoMPNN", version="tamarind-2026-11",
        source_note="Scanned on the 110-residue mature chain folded by Boltz 2.2.1, "
                    "then mapped to precursor numbering by adding 32. The model "
                    "reports one score per mutation and no ensemble spread.",
    )
    for record in (proposals, rejected):
        ref = store.put((json.dumps(record, indent=2, allow_nan=False) + "\n").encode())
        run_stage(store, stage="design", producer=record["producer"],
                  parameters={"record": ref}, inputs=[chassis_entry["id"]],
                  execute=design_run)
    print(f"design: {len(proposals['proposals'])} proposals, "
          f"{len(rejected['rejected'])} rejected on the active site")

    final = store.load()
    print(f"\nrun {final['run_id']} at {store.manifest_path}")
    print(f"  {len(final['entries'])} entries, {len(labels)} variant structures")
    print("  every number above came from a pipeline artefact, none typed in")
    return 0


if __name__ == "__main__":
    sys.exit(main())
