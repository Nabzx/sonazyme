import json
from pathlib import Path

import pytest

from sonazyme.core.manifest import create
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.runs.store import RunStore
from sonazyme.sense.acoustic import RESOLUTION_UM, estimate, forward, survey
from sonazyme.sense.loop import parse_loop, validate_loop, validate_reading
from sonazyme.sense.survey import PRODUCER, reading
from sonazyme.sense.survey import run as run_survey

LOOP_FILE = Path(__file__).resolve().parents[1] / "targets" / "loops" / "demo-loop.toml"


@pytest.fixture
def loop():
    return parse_loop(LOOP_FILE.read_bytes())


def test_the_demo_loop_map_is_valid(loop):
    assert loop["id"] == "demo-loop"
    assert {section["id"] for section in loop["section"]} >= {"exchanger-inlet"}


def test_a_loop_section_needs_material_geometry_and_a_sensor_answer():
    base = {
        "schema_version": 1,
        "kind": "loop",
        "id": "l",
        "name": "l",
        "basis_note": "assumed",
        "section": [
            {
                "id": "a",
                "role": "r",
                "material": "copper",
                "bore_mm": 6,
                "wall_mm": 1,
                "length_m": 1,
                "sensor": True,
            }
        ],
    }
    validate_loop(base)
    for broken in (
        {"material": "titanium"},
        {"bore_mm": 0},
        {"wall_mm": -1},
        {"sensor": "maybe"},
        {"role": ""},
    ):
        record = json.loads(json.dumps(base))
        record["section"][0].update(broken)
        with pytest.raises(ValueError):
            validate_loop(record)


def test_a_clean_wall_returns_no_round_trip():
    features = forward(material="copper", layer="none", thickness_um=0, seed=1)
    assert features["round_trip_us"] == 0
    assert estimate(features, material="copper")["film_thickness_um"] is None


def test_a_thin_film_is_not_claimed():
    features = forward(material="copper", layer="biofilm", thickness_um=RESOLUTION_UM / 3, seed=2)
    result = estimate(features, material="copper")
    assert result["film_thickness_um"] is None
    assert result["layer"] == "undetermined"
    assert "resolution" in result["reason"]


def test_a_soft_layer_is_recovered_with_a_wide_interval():
    truth = 300.0
    features = forward(material="stainless-steel", layer="biofilm", thickness_um=truth, seed=3)
    result = estimate(features, material="stainless-steel")
    assert result["layer"] == "soft"
    low, high = result["interval_um"]
    assert low <= result["film_thickness_um"] <= high
    assert low <= truth <= high, "the simulated truth should sit inside the reported interval"
    # A soft layer is barely distinguishable from water, so the interval is wide.
    assert (high - low) / result["film_thickness_um"] > 0.2


def test_scale_is_separated_from_a_soft_film():
    hard = estimate(
        forward(material="stainless-steel", layer="scale", thickness_um=200, seed=4),
        material="stainless-steel",
    )
    soft = estimate(
        forward(material="stainless-steel", layer="biofilm", thickness_um=200, seed=4),
        material="stainless-steel",
    )
    assert hard["layer"] == "hard"
    assert soft["layer"] == "soft"
    # And the hard case is the better determined of the two.
    hard_width = hard["interval_um"][1] - hard["interval_um"][0]
    soft_width = soft["interval_um"][1] - soft["interval_um"][0]
    assert hard_width < soft_width


def test_every_estimate_carries_its_assumptions():
    for layer, thickness in (("none", 0), ("biofilm", 400), ("scale", 400)):
        result = estimate(
            forward(material="copper", layer=layer, thickness_um=thickness, seed=5),
            material="copper",
        )
        names = {item["name"] for item in result["assumptions"]}
        assert {"media impedance and speed", "feature noise", "resolution floor"} <= names
        assert all(item["basis"] == "assumption" for item in result["assumptions"])


def test_a_survey_keeps_the_simulated_truth_beside_the_estimate(loop):
    observations = survey(loop, {"riser": {"layer": "biofilm", "thickness_um": 150}}, seed=6)
    riser = next(item for item in observations if item["section_id"] == "riser")
    assert riser["simulated_truth"]["thickness_um"] == 150
    assert "simulation" in riser["simulated_truth"]["note"].lower()


def test_a_reading_declares_its_basis(loop):
    record = reading(loop, {"riser": {"layer": "biofilm", "thickness_um": 150}}, seed=7)
    validate_reading(record)
    assert record["basis"] == "simulation"
    assert "ADR-0013" in record["basis_reason"]
    assert PRODUCER["name"] in record["instrument"]


def test_a_reading_without_a_basis_is_refused(loop):
    record = reading(loop, {}, seed=8)
    record["basis"] = "instrument"
    record["basis_reason"] = ""
    with pytest.raises(ValueError):
        validate_reading(record)


def test_an_estimate_with_no_value_must_say_why(loop):
    record = reading(loop, {}, seed=9)
    record["observation"][0]["estimate"] = {"layer": "undetermined", "film_thickness_um": None}
    with pytest.raises(ValueError):
        validate_reading(record)


def test_a_survey_lands_in_the_run_as_a_sense_entry(tmp_path, loop):
    store = RunStore(tmp_path / "run")
    target = store.put(b"schema_version = 1\n")
    store.save(create("survey-run", target))
    parameters = {"loop": loop, "truth": {"riser": {"layer": "scale", "thickness_um": 300}}}
    manifest = run_stage(
        store,
        stage="sense",
        producer=PRODUCER,
        parameters={**parameters, "seed": 11},
        inputs=[],
        execute=run_survey,
    )
    entry = manifest["entries"][-1]
    assert entry["stage"] == "sense" and entry["producer"] == PRODUCER
    record = json.loads(store.read(entry["artefacts"][0]))
    assert record["kind"] == "reading" and record["basis"] == "simulation"
    # The same request replays from the manifest rather than re-simulating.
    again = run_stage(
        store,
        stage="sense",
        producer=PRODUCER,
        parameters={**parameters, "seed": 11},
        inputs=[],
        execute=run_survey,
    )
    assert len(again["entries"]) == len(manifest["entries"])


def test_a_survey_seed_must_be_an_integer(tmp_path, loop):
    store = RunStore(tmp_path / "run")
    store.save(create("survey-run", store.put(b"schema_version = 1\n")))
    with pytest.raises(StageExecutionError):
        run_stage(
            store,
            stage="sense",
            producer=PRODUCER,
            parameters={"loop": loop, "truth": {}, "seed": "later"},
            inputs=[],
            execute=run_survey,
        )


def test_a_survey_does_not_become_the_chassis_input(tmp_path, loop):
    """A survey is a sense entry too, so chassis selection must skip it."""
    import json as json_module
    from pathlib import Path as PathType

    from protein_fixtures import REAL_RECORD, ROOT

    from sonazyme.chassis.__main__ import main as chassis_main
    from sonazyme.core.manifest import create as create_manifest
    from sonazyme.sense import run as sense_run

    run_dir = tmp_path / "run"
    store = RunStore(run_dir)
    target = store.put((ROOT / "targets/psl-literature.toml").read_bytes())
    store.save(create_manifest("survey-then-chassis", target))
    store.save(sense_run(store.load(), store=store))
    store.save(
        run_survey(
            store.load(),
            store=store,
            parameters={"loop": loop, "truth": {}, "seed": 12},
        )
    )
    assert store.load()["entries"][-1]["producer"]["kind"] == "model"

    registry = PathType(REAL_RECORD)
    chassis_main([str(registry), "--run-dir", str(run_dir)])
    entry = store.load()["entries"][-1]
    assert entry["stage"] == "chassis" and entry["status"] == "succeeded"
    record = json_module.loads(store.read(entry["artefacts"][0]))
    assert record["kind"] == "chassis"
