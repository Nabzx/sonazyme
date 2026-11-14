"""An imported structure may not enter a run without its provenance stated."""

import json

import pytest
from protein_fixtures import ROOT

from sonazyme.core.manifest import create
from sonazyme.fold.importer import parse_pdb, run, structure_record
from sonazyme.runs.runner import run_stage
from sonazyme.runs.store import RunStore

PDB = b"""\
ATOM      1  N   MET A   1     -40.350 -15.152   6.101  1.00 65.90           N
ATOM      2  CA  MET A   1     -39.699 -13.836   6.121  1.00 65.90           C
ATOM      3  C   MET A   1     -38.640 -13.791   7.219  1.00 65.90           C
ATOM      9  CA  ILE A   2     -37.100 -12.000   8.000  1.00 80.10           C
ATOM     20  CA  LYS A   3     -35.000 -11.000   9.000  1.00 91.20           C
ATOM     31  CA  GLY B   1     -10.000  -1.000   2.000  1.00 50.00           C
END
"""


def test_a_trace_reads_one_chain_with_its_confidence():
    trace = parse_pdb(PDB)
    assert trace["chain"] == "A"
    assert trace["sequence"] == "MIK"
    assert [point["position"] for point in trace["points"]] == [1, 2, 3]
    assert trace["points"][2]["confidence"] == 91.2


def test_a_file_without_a_trace_is_refused():
    with pytest.raises(ValueError, match="alpha-carbon"):
        parse_pdb(b"HEADER something\nEND\n")


@pytest.mark.parametrize("missing", ["model", "version", "source_note"])
def test_provenance_is_required(missing):
    fields = {"model": "m", "version": "1", "source_note": "n"}
    fields[missing] = "  "
    with pytest.raises(ValueError, match=missing):
        structure_record(PDB, **fields)


def test_a_selection_outside_the_structure_is_refused():
    with pytest.raises(ValueError, match="active_site"):
        structure_record(PDB, model="m", version="1", source_note="n", active_site=[99])


def test_the_record_states_the_model_and_keeps_confidence():
    record = structure_record(
        PDB, model="demo-folder", version="2", source_note="written in a test", active_site=[2]
    )
    assert record["basis"] == "prediction"
    assert record["producer"] == {"name": "demo-folder", "version": "2", "kind": "model"}
    assert record["residue_count"] == 3
    assert record["confidence"]["mean"] == round((65.9 + 80.1 + 91.2) / 3, 2)
    assert record["active_site"] == [2]


def test_the_real_file_reads_as_a_single_chain_trace():
    record = structure_record(
        (ROOT / "docs/result_model_0.pdb").read_bytes(),
        model="demo-folder",
        version="2",
        source_note="the file committed to the repository",
    )
    assert record["residue_count"] == 142
    assert record["points"][0]["position"] == 1
    assert 0 < record["confidence"]["mean"] <= 100


def test_an_imported_structure_lands_as_a_fold_entry(tmp_path):
    store = RunStore(tmp_path / "run")
    store.save(create("import-run", store.put(b"schema_version = 1\n")))
    record = structure_record(PDB, model="demo-folder", version="2", source_note="a test")
    ref = store.put((json.dumps(record) + "\n").encode())
    manifest = run_stage(
        store,
        stage="fold",
        producer=record["producer"],
        parameters={
            "structure": ref,
            "file_sha256": "0" * 64,
            "metrics": [{"name": "plddt", "value": 88.9, "unit": "percent"}],
        },
        inputs=[],
        execute=run,
    )
    entry = manifest["entries"][-1]
    assert entry["stage"] == "fold" and entry["producer"]["kind"] == "model"
    # The record travels as an artefact, and its numbers cite the model.
    assert entry["artefacts"] == [ref]
    assert entry["metrics"][0]["basis"] == "prediction"
    assert entry["metrics"][0]["source"] == record["producer"]
    assert json.loads(store.read(entry["artefacts"][0]))["kind"] == "structure"
