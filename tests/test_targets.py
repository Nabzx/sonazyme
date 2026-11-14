"""Reject uncited values and preserve uncertainty through the sense stage."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from sonazyme.core.manifest import create
from sonazyme.runs.store import RunStore
from sonazyme.sense import run
from sonazyme.sense.__main__ import main
from sonazyme.sense.targets import load, parse, validate

TARGET = Path(__file__).resolve().parents[1] / "targets" / "psl-literature.toml"


@pytest.fixture
def target():
    return load(TARGET)


def test_sense_preserves_evidence_and_does_not_fill_unknowns(tmp_path, target):
    store = RunStore(tmp_path)
    manifest = create("sense-example", store.put(TARGET.read_bytes()))
    store.save(manifest)
    result = run(manifest, store=store)
    store.save(result)
    entry = store.load()["entries"][-1]
    normalised = json.loads(store.read(entry["artefacts"][0]))
    assert normalised == target
    assert entry["metrics"] == []
    assert normalised["community"]["basis"] == "assumption"
    assert normalised["anchor"][0]["component"]["source"].startswith("https://doi.org/")
    assert "value" not in normalised["envelope"]["chemistry"]
    assert manifest["entries"] == []


@pytest.mark.parametrize("basis", ["literature", "guidance", "measurement"])
def test_known_value_without_source_fails_with_field_path(target, basis):
    target["envelope"]["ph"] = {"basis": basis, "value": [1, 2]}
    with pytest.raises(ValueError, match=r"envelope.ph: .*requires a source"):
        validate(target)


def test_assumptions_require_reasons_and_unknowns_forbid_values(target):
    target["community"].pop("reason")
    with pytest.raises(ValueError, match="community: assumption requires a reason"):
        validate(target)
    target["community"] = {"basis": "unknown", "reason": "not measured", "value": []}
    with pytest.raises(ValueError, match="forbids a value"):
        validate(target)


@pytest.mark.parametrize("value", [[2, 1], [1], [True, 2], [float("nan"), 2], "1-2"])
def test_invalid_envelope_ranges_are_rejected(target, value):
    target["envelope"]["temperature_c"] = {
        "basis": "assumption",
        "reason": "software fixture only",
        "value": value,
    }
    with pytest.raises(ValueError, match="envelope.temperature_c"):
        validate(target)


def test_no_target_specific_branch_is_needed(target):
    second = deepcopy(target)
    second["target"]["id"] = "software-fixture"
    second["anchor"][0]["component"] = {
        "basis": "assumption",
        "value": "software fixture, no biological claim",
        "reason": "Check that the schema does not hard-code an anchor",
    }
    validate(second)


def test_unknown_chemistry_is_distinct_from_known_empty_chemistry(target):
    unknown = deepcopy(target["envelope"]["chemistry"])
    target["envelope"]["chemistry"] = {
        "basis": "assumption",
        "value": [],
        "reason": "software fixture only",
    }
    validate(target)
    assert unknown != target["envelope"]["chemistry"]


def test_unmarked_and_extra_fields_are_rejected(target):
    target["envelope"]["chemistry"] = []
    with pytest.raises(ValueError, match="evidence record"):
        validate(target)
    target["envelope"]["chemistry"] = {"basis": "unknown", "reason": "not measured"}
    target["envelope"]["invented_field"] = "not accepted"
    with pytest.raises(ValueError, match="envelope: expected fields"):
        validate(target)


def test_unknown_version_and_malformed_toml_fail(target):
    target["schema_version"] = 2
    with pytest.raises(ValueError, match="unsupported"):
        validate(target)
    with pytest.raises(ValueError):
        parse(b"not valid toml")


def test_cli_can_resume_and_refuses_target_replacement(tmp_path, capsys):
    directory = tmp_path / "run"
    argv = [str(TARGET), "--run-dir", str(directory)]
    main(argv)
    store = RunStore(directory)
    first = store.load()
    main(argv)
    assert store.load() == first
    assert "No model or wet-lab result" in capsys.readouterr().out
    changed = tmp_path / "changed.toml"
    changed.write_bytes(TARGET.read_bytes().replace(b"psl-literature", b"changed-target"))
    with pytest.raises(SystemExit) as raised:
        main([str(changed), "--run-dir", str(directory)])
    assert raised.value.code == 2
    assert store.load() == first


def test_cli_rejects_invalid_target_before_creating_run(tmp_path):
    invalid = tmp_path / "invalid.toml"
    invalid.write_text("schema_version = 1\n")
    directory = tmp_path / "unused"
    with pytest.raises(SystemExit) as raised:
        main([str(invalid), "--run-dir", str(directory)])
    assert raised.value.code == 2
    assert not directory.exists()
