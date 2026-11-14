"""A ranking is split by whether it touches the catalytic site, never dropped."""

import json

import pytest

from sonazyme.core.manifest import create
from sonazyme.design.importer import read_ranking, records, split
from sonazyme.design.importer import run as design_run
from sonazyme.runs.runner import run_stage
from sonazyme.runs.store import RunStore

CSV = b"""score,score_conservative,score_std,chain,position,wildtype,mutant,mutation
1.6,1.4,0.1,A,8,H,L,H8L
1.5,1.3,0.2,A,117,N,V,N117V
1.2,1.1,0.1,A,135,T,W,T135W
0.4,0.2,0.1,A,93,D,V,D93V
"""
SITE = [53, 93, 94, 108, 117]


def test_a_table_without_the_fields_we_rely_on_is_refused():
    with pytest.raises(ValueError, match="missing"):
        read_ranking(b"mutation,score\nH8L,1.2\n")
    with pytest.raises(ValueError, match="empty"):
        read_ranking(b"score,score_conservative,score_std,chain,position,wildtype,mutant\n")


def test_the_site_is_separated_and_both_halves_are_kept():
    kept, touched = split(read_ranking(CSV), SITE)
    assert [row["mutation"] for row in kept] == ["H8L", "T135W"]
    assert [row["mutation"] for row in touched] == ["N117V", "D93V"]
    # Ordered by the conservative score, which is the one with the spread taken off.
    assert kept[0]["score_conservative"] >= kept[-1]["score_conservative"]


def test_a_favoured_mutation_on_the_site_is_still_rejected():
    """The whole point: the ranking liked N117V, and it is still not a design."""
    ranking = read_ranking(CSV)
    best = max(ranking, key=lambda row: row["score_conservative"])
    proposals, rejected = records(
        ranking, chassis_id="c", active_site=SITE, model="m", version="1", source_note="n"
    )
    assert best["mutation"] == "H8L"
    favoured_on_site = rejected["rejected"][0]
    assert favoured_on_site["mutation"] == "N117V"
    assert favoured_on_site["score_conservative"] > proposals["proposals"][-1]["score_conservative"]
    assert all(row["position"] not in SITE for row in proposals["proposals"])


@pytest.mark.parametrize("missing", ["model", "version", "source_note"])
def test_provenance_is_required(missing):
    fields = {"model": "m", "version": "1", "source_note": "n"}
    fields[missing] = " "
    with pytest.raises(ValueError, match="model, a version and a source note"):
        records(read_ranking(CSV), chassis_id="c", active_site=SITE, **fields)


def _run(store, record):
    ref = store.put((json.dumps(record) + "\n").encode())
    return run_stage(
        store,
        stage="design",
        producer=record["producer"],
        parameters={"record": ref},
        inputs=[],
        execute=design_run,
    )


def test_proposals_succeed_and_rejections_are_recorded_as_rejected(tmp_path):
    store = RunStore(tmp_path / "run")
    store.save(create("design-run", store.put(b"schema_version = 1\n")))
    proposals, rejected = records(
        read_ranking(CSV), chassis_id="c", active_site=SITE, model="m", version="1", source_note="n"
    )
    manifest = _run(store, proposals)
    assert manifest["entries"][-1]["status"] == "succeeded"
    manifest = _run(store, rejected)
    entry = manifest["entries"][-1]
    assert entry["status"] == "rejected"
    assert "catalytic residue" in entry["reason"]
    # A rejected entry carries no metrics, and keeps its artefact.
    assert entry["metrics"] == [] and entry["artefacts"]
    assert json.loads(store.read(entry["artefacts"][0]))["kind"] == "variant-rejections"
