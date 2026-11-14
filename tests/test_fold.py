"""Test the Boltz protocol using synthetic outputs, never a live prediction."""

import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from protein_fixtures import FakeBoltz, fold_subject, pdb, prepare, settings, variant

from sonazyme.core.folding import subject_sequence
from sonazyme.core.protein import read_pdb
from sonazyme.fold.boltz import LocalBoltz
from sonazyme.runs.runner import StageExecutionError


def test_fold_preserves_pdb_request_and_per_region_confidence(tmp_path):
    store, parent = prepare(tmp_path)
    backend = FakeBoltz()
    entry = fold_subject(store, parent, backend=backend)
    index = json.loads(store.read(entry["artefacts"][0]))
    assert index["basis"] == "prediction"
    assert store.read(index["pdb"]) == pdb()
    confidence = json.loads(store.read(index["confidence"]))
    assert confidence["active_site_plddt"] == {"2": 0.9}  # Synthetic fixture only.
    assert index["role"] == "baseline"
    assert all(
        ref in entry["artefacts"] for ref in (index["pdb"], index["confidence"], index["request"])
    )
    assert len(backend.calls) == 1
    fold_subject(store, parent, backend=backend)
    assert len(backend.calls) == 1


def test_variant_and_sourced_complex_mode(tmp_path):
    store, parent = prepare(tmp_path)
    ref, design_id = variant(store, parent)
    config = settings()
    config["ligand"] = {"format": "smiles", "value": "O", "source": "software fixture only"}
    config["msa"] = {"mode": "provided", "artefact": store.put(b">fixture\nVEG\n")}
    backend = FakeBoltz()
    entry = fold_subject(store, parent, ref, design_id, backend, config)
    document, _, msa = backend.calls[0]
    assert document["sequences"][1] == {"ligand": {"id": "B", "smiles": "O"}}
    assert msa == b">fixture\nVEG\n"
    assert json.loads(store.read(entry["artefacts"][0]))["role"] == "variant"


def test_variants_require_complete_exclusion_and_match_their_mutation_set(tmp_path):
    store, parent = prepare(tmp_path)
    chassis = json.loads(store.read(parent["artefacts"][0]))
    subject = {
        "schema_version": 1,
        "kind": "variant",
        "id": "fixture",
        "chassis_id": chassis["id"],
        "sequence": "VEG",
        "mutation_set": ["A1V"],
    }
    assert subject_sequence(subject, chassis) == "VEG"
    subject["mutation_set"] = []
    with pytest.raises(ValueError, match="Mutation set"):
        subject_sequence(subject, chassis)
    subject.update(sequence="AAG", mutation_set=["E2A"])
    with pytest.raises(ValueError, match="protected"):
        subject_sequence(subject, chassis)
    chassis["design_ready"] = False
    with pytest.raises(ValueError, match="incomplete"):
        subject_sequence(subject, chassis)


def test_bad_confidence_fails_without_a_successful_fold_entry(tmp_path):
    store, parent = prepare(tmp_path)

    class MissingConfidence:
        def predict(self, *args):
            return pdb(), b"{}"

    with pytest.raises(StageExecutionError):
        fold_subject(store, parent, backend=MissingConfidence())
    assert store.load()["entries"][-1]["status"] == "failed"


def test_strict_pdb_reader_rejects_missing_residues_duplicates_and_nan():
    source = pdb()
    read_pdb(source, "AEG")
    lines = source.splitlines()
    for broken in (
        b"\n".join(line for line in lines if line[22:26].strip() != b"2"),
        source + lines[0] + b"\n",
        source.replace(b"   4.000", b"     nan", 1),
        b"MODEL        1\n" + source + b"MODEL        2\n" + source,
    ):
        with pytest.raises(ValueError):
            read_pdb(broken, "AEG")


def test_local_wrapper_checks_identity_and_constructs_documented_command(tmp_path, monkeypatch):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.write_bytes(b"software fixture checkpoint")
    config = settings()
    config["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    calls = []

    def subprocess_fixture(command, **kwargs):
        calls.append(command)
        if "-c" in command:
            return subprocess.CompletedProcess(command, 0, stdout=config["package_version"] + "\n")
        request_path = Path(command[command.index("predict") + 1])
        request = json.loads(request_path.read_text())
        assert Path(request["sequences"][0]["protein"]["msa"]).read_bytes() == b">fixture\nAEG\n"
        out = (
            Path(command[command.index("--out_dir") + 1])
            / "boltz_results_request/predictions/request"
        )
        out.mkdir(parents=True)
        (out / "request_model_0.pdb").write_bytes(pdb())
        (out / "confidence_request_model_0.json").write_bytes(b"{}")
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", subprocess_fixture)
    backend = LocalBoltz(Path(sys.executable), checkpoint, tmp_path / "cache")
    document = {
        "version": 1,
        "sequences": [{"protein": {"id": "A", "sequence": "AEG", "msa": "protein.a3m"}}],
    }
    assert backend.predict(document, config, b">fixture\nAEG\n")[0] == pdb()
    command = calls[-1]
    assert command[command.index("--model") + 1] == "boltz2"
    assert "--use_msa_server" not in command
    assert "--seed" in command and "--override" in command
    wrong = deepcopy(config)
    wrong["checkpoint_sha256"] = "0" * 64
    count = len(calls)
    with pytest.raises(ValueError, match="digest"):
        backend.predict(document, wrong, None)
    assert len(calls) == count


def test_local_wrapper_rejects_package_version_mismatch(tmp_path, monkeypatch):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.write_bytes(b"software fixture checkpoint")
    config = settings()
    config["checkpoint_sha256"] = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], 0, stdout="wrong-version"),
    )
    with pytest.raises(ValueError, match="version"):
        LocalBoltz(Path(sys.executable), checkpoint, tmp_path / "cache").predict({}, config, None)
