"""Check provenance, history protection and offline artefact integrity."""

from copy import deepcopy

import pytest

from sonazyme.core.manifest import append, create, finish, validate
from sonazyme.runs.store import RunStore


@pytest.fixture
def run(tmp_path):
    store = RunStore(tmp_path / "run")
    manifest = create("test-run", store.put(b"test target, no biological values"))
    return store, manifest


def entry():
    return {
        "id": "sense-1",
        "stage": "sense",
        "status": "succeeded",
        "producer": {"name": "sonazyme", "version": "test", "kind": "code"},
        "inputs": [],
        "parameters": {},
        "metrics": [],
        "artefacts": [],
        "reason": None,
    }


def test_round_trip_and_seal(run):
    store, manifest = run
    store.save(manifest)
    result = append(manifest, entry())
    assert manifest["entries"] == []
    store.save(result)
    sealed = finish(result)
    store.save(sealed)
    assert store.load() == sealed
    store.save(sealed)  # Idempotent writes are harmless.
    with pytest.raises(ValueError, match="finished"):
        append(sealed, entry())
    with pytest.raises(ValueError, match="finished"):
        store.put(b"later")
    with pytest.raises(ValueError, match="immutable"):
        store.save(result)


def test_history_cannot_be_edited_or_truncated(run):
    store, manifest = run
    saved = append(manifest, entry())
    store.save(saved)
    changed = deepcopy(saved)
    changed["entries"][0]["parameters"] = {"changed": True}
    for invalid in (manifest, changed):
        with pytest.raises(ValueError, match="history"):
            store.save(invalid)
    assert store.load() == saved


def test_retries_keep_failure_and_dependencies(run):
    store, manifest = run
    failed = entry()
    failed.update(status="failed", reason="Public error: provider unavailable")
    first = append(manifest, failed)
    retry = entry()
    retry.update(id="sense-2", inputs=["sense-1"])
    result = append(first, retry)
    store.save(result)
    assert [e["status"] for e in store.load()["entries"]] == ["failed", "succeeded"]
    with pytest.raises(ValueError, match="unique"):
        append(result, retry)
    retry.update(id="sense-3", inputs=["future-entry"])
    with pytest.raises(ValueError, match="earlier"):
        append(result, retry)


@pytest.mark.parametrize("field,value", [("version", ""), ("name", ""), ("kind", "unknown")])
def test_missing_or_invalid_producer_is_rejected(run, field, value):
    _, manifest = run
    attempt = entry()
    attempt["producer"][field] = value
    with pytest.raises(ValueError):
        append(manifest, attempt)


def test_prediction_must_cite_model(run):
    _, manifest = run
    attempt = entry()
    attempt["stage"] = "score"
    attempt["producer"] = {"name": "test-model", "version": "test", "kind": "model"}
    metric = dict(
        name="test-only",
        value=0.0,
        unit="test-unit",
        basis="prediction",
        source=deepcopy(attempt["producer"]),
    )
    attempt["metrics"] = [metric]
    validate(append(manifest, attempt))
    metric["source"] = "uncited"
    with pytest.raises(ValueError, match="cite"):
        append(manifest, attempt)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, "0"])
def test_non_numeric_or_non_finite_metrics_are_rejected(run, value):
    _, manifest = run
    attempt = entry()
    attempt["metrics"] = [
        dict(
            name="test",
            value=value,
            unit="test",
            basis="measurement",
            source="test fixture, no biological measurement",
        )
    ]
    with pytest.raises(ValueError, match="finite"):
        append(manifest, attempt)


def test_failures_cannot_have_success_metrics(run):
    _, manifest = run
    attempt = entry()
    attempt.update(status="failed", reason="")
    with pytest.raises(ValueError, match="reason"):
        append(manifest, attempt)
    attempt.update(reason="failed", metrics=[{}])
    with pytest.raises(ValueError, match="no metrics"):
        append(manifest, attempt)


def test_corruption_missing_files_and_traversal(run):
    store, manifest = run
    store.save(manifest)
    ref = manifest["target"]
    path = store.directory / ref["path"]
    path.write_bytes(b"corrupted")
    with pytest.raises(ValueError, match="mismatch"):
        store.load()
    path.unlink()
    with pytest.raises(FileNotFoundError):
        store.load()
    with pytest.raises(ValueError, match="path"):
        store.read({**ref, "path": "../escape"})


def test_content_addressing_and_symlink_escape(run, tmp_path):
    store, _ = run
    ref = store.put(b"same")
    assert store.put(b"same") == ref
    path = store.directory / ref["path"]
    path.unlink()
    outside = tmp_path / "outside"
    outside.write_bytes(b"same")
    path.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        store.read(ref)


def test_unknown_schema_is_rejected(run):
    _, manifest = run
    manifest["schema_version"] = 999
    with pytest.raises(ValueError, match="schema"):
        validate(manifest)


@pytest.mark.parametrize("parameters", [{"seed": (1, 2)}, {1: "non-string key"}])
def test_parameters_cannot_change_during_serialisation(run, parameters):
    _, manifest = run
    attempt = entry()
    attempt["parameters"] = parameters
    with pytest.raises(ValueError, match="round trip"):
        append(manifest, attempt)


def test_missing_output_prevents_manifest_save(run):
    store, manifest = run
    store.save(manifest)
    ref = store.put(b"stage output")
    attempt = entry()
    attempt["artefacts"] = [ref]
    (store.directory / ref["path"]).unlink()
    with pytest.raises(FileNotFoundError):
        store.save(append(manifest, attempt))
    assert store.load() == manifest


def test_history_cannot_change_bool_into_number(run):
    store, manifest = run
    attempt = entry()
    attempt["parameters"] = {"setting": True}
    saved = append(manifest, attempt)
    store.save(saved)
    changed = deepcopy(saved)
    changed["entries"][0]["parameters"]["setting"] = 1
    with pytest.raises(ValueError, match="history"):
        store.save(changed)
