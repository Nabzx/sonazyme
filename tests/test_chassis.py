"""Check sourced construct identity and manifest provenance without modelling biology."""

import hashlib
import json
from copy import deepcopy

import pytest
from protein_fixtures import REAL_RECORD, ROOT, prepare

from sonazyme.chassis import run
from sonazyme.chassis.__main__ import main
from sonazyme.chassis.registry import load, parse
from sonazyme.core.records import validate_chassis


def test_real_chassis_matches_deposited_sequence_and_reference_mapping():
    record = load(REAL_RECORD)
    raw = (ROOT / "targets/chassis/sources/5bx9.fasta").read_bytes()
    deposited = "".join(raw.decode().splitlines()[1:])
    assert deposited.startswith("GSHM")
    assert record["sequence"]["value"] == deposited[4:]
    assert record["sequence"]["source_fasta_sha256"] == hashlib.sha256(raw).hexdigest()
    mapping = record["sequence"]["mapping"]
    assert mapping["reference_start"] == 31
    assert mapping["reference_end"] == 442
    assert [
        (r["position"], r["reference_position"]) for r in record["active_site"]["residues"]
    ] == [(135, 165), (246, 276)]
    assert record["design_ready"] is False


@pytest.mark.parametrize("section", ["sequence", "active_site", "anchor"])
def test_missing_chassis_source_fails(section):
    record = load(REAL_RECORD)
    record[section].pop("source")
    with pytest.raises(ValueError, match="source"):
        parse(json.dumps(record).encode())


def test_wrong_digest_and_residue_numbering_fail():
    record = load(REAL_RECORD)
    broken = deepcopy(record)
    broken["sequence"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        validate_chassis(broken)
    record["active_site"]["residues"][0]["position"] += 4
    with pytest.raises(ValueError, match="mapping"):
        validate_chassis(record)


def test_sources_survive_into_chassis_artefact(tmp_path):
    store, entry = prepare(tmp_path, load(REAL_RECORD))
    snapshot = json.loads(store.read(entry["artefacts"][0]))
    assert snapshot == load(REAL_RECORD)
    assert entry["metrics"] == []


def test_mismatched_anchor_is_rejected(tmp_path):
    store, entry = prepare(tmp_path)
    record = json.loads(store.read(entry["artefacts"][0]))
    record["anchor"]["bond"] = "different software fixture bond"
    ref = store.put(json.dumps(record).encode())
    with pytest.raises(ValueError, match="match"):
        run(store.load(), store=store, parameters={"registry": ref}, inputs=entry["inputs"])


def test_chassis_cli_reuses_snapshot_and_reports_design_limit(tmp_path, capsys):
    store, _ = prepare(tmp_path, load(REAL_RECORD))
    argv = [str(REAL_RECORD), "--run-dir", str(tmp_path)]
    main(argv)
    first = store.load()
    main(argv)
    assert store.load() == first
    assert "design remains blocked" in capsys.readouterr().out
