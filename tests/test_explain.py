"""The scientist answers from the run in front of it, or refuses."""

import json

from protein_fixtures import ROOT, prepare

from sonazyme.core.manifest import create
from sonazyme.explain import run as explain_run
from sonazyme.explain.answers import QUESTIONS, compose
from sonazyme.explain.retrieval import build
from sonazyme.runs.runner import run_stage
from sonazyme.runs.store import RunStore
from sonazyme.sense import run as sense_run
from sonazyme.sense.loop import parse_loop
from sonazyme.sense.survey import PRODUCER as SURVEY_PRODUCER
from sonazyme.sense.survey import run as survey_run

LOOP = parse_loop((ROOT / "targets/loops/demo-loop.toml").read_bytes())


def _empty_run(tmp_path):
    store = RunStore(tmp_path / "run")
    store.save(create("empty", store.put(b"schema_version = 1\n")))
    return store


def test_an_empty_run_answers_only_its_inventory(tmp_path):
    record = compose(build(_empty_run(tmp_path)))
    answers = {item["key"]: item for item in record["answers"]}
    assert answers["inventory"]["grounded"] is True
    for key in ("loop", "chassis", "candidates", "treatment"):
        assert answers[key]["grounded"] is False, key
        assert answers[key]["missing"], key
        assert answers[key]["citations"] == []


def test_every_grounded_answer_cites_something(tmp_path):
    store, _ = prepare(tmp_path)
    store.save(
        survey_run(
            store.load(),
            store=store,
            parameters={"loop": LOOP, "truth": {"riser": {"layer": "scale", "thickness_um": 300}}},
        )
    )
    record = compose(build(store))
    for answer in record["answers"]:
        if answer["grounded"]:
            assert answer["citations"], answer["key"]
            for citation in answer["citations"]:
                assert citation["entry_id"] and citation["stage"] and citation["producer"]


def test_a_refusal_names_what_is_missing(tmp_path):
    store, _ = prepare(tmp_path)
    record = compose(build(store))
    answers = {item["key"]: item for item in record["answers"]}
    assert answers["candidates"]["grounded"] is False
    assert "a design entry" in answers["candidates"]["missing"]
    assert answers["treatment"]["grounded"] is False
    # A refusal never carries a recommendation anyway.
    assert "dose" not in answers["treatment"]["text"].lower().split(".")[0]


def test_a_simulated_survey_is_described_as_simulated(tmp_path):
    store, _ = prepare(tmp_path)
    store.save(
        survey_run(
            store.load(),
            store=store,
            parameters={
                "loop": LOOP,
                "truth": {"exchanger-inlet": {"layer": "biofilm", "thickness_um": 400}},
            },
        )
    )
    answers = {item["key"]: item for item in compose(build(store))["answers"]}
    assert answers["loop"]["grounded"] is True
    assert "simulated" in answers["loop"]["text"].lower()
    assert answers["loop"]["confidence"] == "simulated"


def test_the_next_step_list_points_at_real_work(tmp_path):
    store, _ = prepare(tmp_path)
    answers = {item["key"]: item for item in compose(build(store))["answers"]}
    steps = answers["next"]["steps"]
    assert steps and all(step["step"] and step["settles"] and step["issue"] for step in steps)


def test_the_stage_records_the_composer_as_code(tmp_path):
    store, _ = prepare(tmp_path)
    manifest = run_stage(
        store,
        stage="explain",
        producer={"name": "sonazyme.explain", "version": "1", "kind": "code"},
        parameters={},
        inputs=[],
        execute=explain_run,
    )
    entry = manifest["entries"][-1]
    assert entry["stage"] == "explain"
    # Nothing on screen may imply a model wrote this.
    assert entry["producer"]["kind"] == "code"
    record = json.loads(store.read(entry["artefacts"][0]))
    assert record["kind"] == "explanation"
    assert {item["key"] for item in record["answers"]} == set(QUESTIONS)


def test_the_index_lists_the_stages_a_run_is_missing(tmp_path):
    store = RunStore(tmp_path / "run")
    store.save(create("sense-only", store.put((ROOT / "targets/psl-literature.toml").read_bytes())))
    store.save(sense_run(store.load(), store=store))
    index = build(store)
    assert "sense" in index.stages_present
    assert "design" in index.missing() and "fold" in index.missing()


def test_a_survey_is_not_mistaken_for_a_target(tmp_path):
    store, _ = prepare(tmp_path)
    store.save(
        survey_run(store.load(), store=store, parameters={"loop": LOOP, "truth": {}, "seed": 3})
    )
    index = build(store)
    assert index.target is not None and "target" in index.target
    assert index.readings and index.readings[0]["kind"] == "reading"
    assert index.citations["reading"].producer.startswith(SURVEY_PRODUCER["name"])
