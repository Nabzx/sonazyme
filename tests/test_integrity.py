"""Synthetic geometry checks only; no biological tolerance is agreed by these tests."""

import json
from copy import deepcopy
from uuid import uuid4

import pytest
from protein_fixtures import FakeBoltz, chassis_record, fold_subject, pdb, policy, prepare, variant

from sonazyme.core.manifest import append
from sonazyme.core.protein import read_pdb
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.score.integrity import PRODUCER, check, require_integrity, run, validate_policy


def test_rotation_and_translation_do_not_change_verdict():
    reference = read_pdb(pdb(), "AEG")
    moved = read_pdb(pdb(transform=lambda x, y, z: (-y + 10, x - 5, z + 2)), "AEG")
    report = check(chassis_record(), reference, moved, policy())
    assert report["passed"] is True
    assert report["max_distance_change_angstrom"] == 0


@pytest.mark.parametrize(
    "arguments,reason",
    [
        ({"shift": 2}, "outside"),
        ({"omit": (2, "OE1")}, "Missing"),
        ({"confidence": 10}, "confidence"),
        ({"transform": lambda x, y, z: (-x, y, z)}, "handedness"),
    ],
)
def test_broken_uncertain_or_incomplete_geometry_is_rejected(arguments, reason):
    report = check(
        chassis_record(), read_pdb(pdb(), "AEG"), read_pdb(pdb(**arguments), "AEG"), policy()
    )
    assert report["passed"] is False
    assert reason in report["reason"]


def pair(tmp_path, **backend_arguments):
    store, parent = prepare(tmp_path)
    baseline = fold_subject(store, parent)
    ref, design_id = variant(store, parent)
    proposed = fold_subject(store, parent, ref, design_id, FakeBoltz(**backend_arguments))
    return store, [parent["id"], baseline["id"], proposed["id"]]


def evaluate(store, inputs):
    ref = store.put(json.dumps(policy()).encode())
    parameters = {"role": "integrity", "policy": ref}
    result = run_stage(
        store, stage="score", producer=PRODUCER, parameters=parameters, inputs=inputs, execute=run
    )
    return result


def test_rejection_is_saved_with_reason_before_any_stability_stage(tmp_path):
    store, inputs = pair(tmp_path, shift=2)
    result = evaluate(store, inputs)
    entry = result["entries"][-1]
    assert entry["status"] == "rejected"
    assert "outside" in entry["reason"]
    assert entry["metrics"] == []
    assert json.loads(store.read(entry["artefacts"][0]))["passed"] is False
    with pytest.raises(ValueError, match="No passing"):
        require_integrity(result, store, inputs[1], inputs[2], policy=entry["parameters"]["policy"])


def test_software_fixture_pass_cannot_authorise_stability_scoring(tmp_path):
    store, inputs = pair(tmp_path)
    result = evaluate(store, inputs)
    assert result["entries"][-1]["status"] == "succeeded"
    with pytest.raises(ValueError, match="No passing"):
        require_integrity(
            result,
            store,
            inputs[1],
            inputs[2],
            policy=result["entries"][-1]["parameters"]["policy"],
        )


def test_incompatible_model_provenance_fails_closed(tmp_path):
    store, parent = prepare(tmp_path)
    baseline = fold_subject(store, parent)
    ref, design_id = variant(store, parent)
    from protein_fixtures import settings

    config = settings()
    config["seed"] += 1
    proposed = fold_subject(store, parent, ref, design_id, config=config)
    with pytest.raises(StageExecutionError):
        evaluate(store, [parent["id"], baseline["id"], proposed["id"]])
    assert store.load()["entries"][-1]["status"] == "failed"


def test_production_policy_requires_prior_agreement_reference():
    config = policy()
    config["purpose"] = "production"
    with pytest.raises(ValueError, match="prior agreement"):
        validate_policy(config)
    config = policy()
    config["max_distance_change_angstrom"] = float("nan")
    with pytest.raises(ValueError, match="Invalid"):
        validate_policy(config)


def test_scoring_gate_binds_policy_and_blocks_later_failure(tmp_path, monkeypatch):
    import sonazyme.score.integrity as integrity

    # Simulate agreement metadata for this software-only gate test. This does
    # not approve a biological policy or invent a real GitHub comment.
    def fixture_policy_validation(value):
        validate_policy({**value, "purpose": "software-test"})

    monkeypatch.setattr(integrity, "validate_policy", fixture_policy_validation)
    store, inputs = pair(tmp_path)
    config = {**policy(), "purpose": "production"}
    ref = store.put(json.dumps(config).encode())
    result = run_stage(
        store,
        stage="score",
        producer=PRODUCER,
        parameters={"role": "integrity", "policy": ref},
        inputs=inputs,
        execute=run,
    )
    assert require_integrity(result, store, inputs[1], inputs[2], policy=ref)["passed"] is True
    different = store.put(json.dumps({**config, "rationale": "different fixture policy"}).encode())
    with pytest.raises(ValueError, match="No passing"):
        require_integrity(result, store, inputs[1], inputs[2], policy=different)
    later = deepcopy(result["entries"][-1])
    later.update(
        id=uuid4().hex, status="failed", reason="software fixture later failure", artefacts=[]
    )
    result = append(result, later)
    store.save(result)
    with pytest.raises(ValueError, match="No passing"):
        require_integrity(result, store, inputs[1], inputs[2], policy=ref)
