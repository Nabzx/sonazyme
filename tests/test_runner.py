"""Exercise restart, cache identity and failure handling without model calls."""

from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest

from sonazyme.core.manifest import append, create, finish
from sonazyme.runs.runner import StageExecutionError, run_stage
from sonazyme.runs.store import RunStore
from sonazyme.sense import PRODUCER, run

TARGET = Path(__file__).resolve().parents[1] / "targets" / "psl-literature.toml"
PRODUCER_FIXTURE = {"name": "test-stage", "version": "1", "kind": "code"}


@pytest.fixture
def store(tmp_path):
    store = RunStore(tmp_path)
    store.save(create("runner-test", store.put(TARGET.read_bytes())))
    return store


def execute(manifest, *, store, parameters, inputs):
    ref = store.put(b"software fixture output")
    return append(
        manifest,
        {
            "id": uuid4().hex,
            "stage": "chassis",
            "status": "succeeded",
            "producer": deepcopy(PRODUCER_FIXTURE),
            "inputs": inputs,
            "parameters": parameters,
            "metrics": [],
            "artefacts": [ref],
            "reason": None,
        },
    )


def request(store, **overrides):
    arguments = dict(
        stage="chassis",
        producer=PRODUCER_FIXTURE,
        parameters={},
        inputs=[],
        execute=execute,
    )
    arguments.update(overrides)
    return run_stage(store, **arguments)


def never_execute(*args, **kwargs):
    raise AssertionError("Replay must not call a stage")


def test_sense_runs_through_runner_then_reuses_saved_output(store):
    arguments = dict(stage="sense", producer=PRODUCER, parameters={}, inputs=[])
    first = run_stage(store, execute=run, **arguments)
    reopened = RunStore(store.directory)
    cached = run_stage(reopened, execute=never_execute, **arguments)
    assert cached == first
    assert len(cached["entries"]) == 1
    assert reopened.load() == first  # Replay has no callable or network dependency.


def test_cache_uses_parameters_and_distinguishes_bool_from_number(store):
    first = request(store, parameters={"setting": True})
    second = request(store, parameters={"setting": 1})
    assert len(second["entries"]) == len(first["entries"]) + 1
    assert request(store, parameters={"setting": 1}, execute=never_execute) == second


def test_cache_can_be_disabled(store):
    request(store)
    result = request(store, use_cache=False)
    assert len(result["entries"]) == 2


def test_changed_version_requires_new_execution(store):
    request(store)
    calls = []

    def version_two(manifest, **kwargs):
        calls.append(True)
        result = execute(manifest, **kwargs)
        result["entries"][-1]["producer"]["version"] = "2"
        return result

    result = request(store, producer={**PRODUCER_FIXTURE, "version": "2"}, execute=version_two)
    assert len(result["entries"]) == 2
    assert calls == [True]


def test_changed_inputs_require_a_new_execution(store):
    first = request(store)
    result = request(store, inputs=[first["entries"][-1]["id"]])
    assert len(result["entries"]) == 2
    assert result["entries"][-1]["inputs"] == [first["entries"][-1]["id"]]


def test_error_is_recorded_without_provider_message_and_retry_succeeds(store):
    def failure(*args, **kwargs):
        raise RuntimeError("secret diagnostic text")

    with pytest.raises(StageExecutionError) as raised:
        request(store, execute=failure)
    assert "secret" not in str(raised.value)
    assert "secret" not in store.manifest_path.read_text()
    failed = store.load()["entries"][-1]
    assert failed["status"] == "failed"
    assert failed["metrics"] == []
    with pytest.raises(ValueError, match="successful"):
        request(store, inputs=[failed["id"]])
    result = request(store)
    assert [e["status"] for e in result["entries"]] == ["failed", "succeeded"]


@pytest.mark.parametrize("change", ["history", "metadata", "request", "no-entry", "missing-file"])
def test_invalid_stage_output_cannot_corrupt_history(store, change):
    first = request(store)

    def invalid(manifest, **kwargs):
        result = execute(manifest, **kwargs)
        if change == "history":
            result["entries"][0]["parameters"] = {"rewritten": True}
        elif change == "metadata":
            result["run_id"] = "changed"
        elif change == "request":
            result["entries"][-1]["parameters"] = {"unrequested": True}
        elif change == "no-entry":
            return manifest
        else:
            ref = store.put(b"unavailable fixture")
            result["entries"][-1]["artefacts"] = [ref]
            (store.directory / ref["path"]).unlink()
        return result

    with pytest.raises(StageExecutionError):
        request(store, execute=invalid, use_cache=False)
    saved = store.load()
    assert saved["entries"][:-1] == first["entries"]
    assert saved["entries"][-1]["status"] == "failed"


def test_rejected_attempt_is_saved_and_never_reused(store):
    def rejected(manifest, **kwargs):
        result = execute(manifest, **kwargs)
        result["entries"][-1].update(status="rejected", reason="software fixture rejection")
        return result

    request(store, execute=rejected)
    result = request(store)
    assert [e["status"] for e in result["entries"]] == ["rejected", "succeeded"]


def test_finished_run_reuses_success_but_refuses_new_work(store):
    store.save(finish(request(store)))
    assert request(store, execute=never_execute)["status"] == "finished"
    with pytest.raises(ValueError, match="finished"):
        request(store, parameters={"new": True})


def test_corrupt_cache_fails_before_calling_stage(store):
    result = request(store)
    ref = result["entries"][-1]["artefacts"][0]
    (store.directory / ref["path"]).write_bytes(b"changed")
    with pytest.raises(ValueError, match="mismatch"):
        request(store, execute=never_execute)


def test_invalid_request_has_no_call_or_manifest_entry(store):
    with pytest.raises(ValueError, match="earlier"):
        request(store, inputs=["missing"], execute=never_execute)
    assert store.load()["entries"] == []
