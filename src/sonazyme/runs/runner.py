"""Execute single-writer stage requests and reuse verified successes."""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from uuid import uuid4

from sonazyme.core.manifest import append, validate
from sonazyme.runs.store import RunStore


class StageExecutionError(RuntimeError):
    """A recorded failed attempt, with provider diagnostics withheld."""


def _identity(value: object) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False)


def run_stage(
    store: RunStore,
    *,
    stage: str,
    producer: dict,
    parameters: dict,
    inputs: list[str],
    execute: Callable[..., dict],
    use_cache: bool = True,
) -> dict:
    """Run one exact request or return the current manifest on a verified cache hit."""
    manifest = store.load()
    request = deepcopy(dict(stage=stage, producer=producer, parameters=parameters, inputs=inputs))
    entry = dict(
        id=f"{stage}-{uuid4().hex}",
        status="succeeded",
        metrics=[],
        artefacts=[],
        reason=None,
        **request,
    )
    # Validate the request before executing or recording any external call.
    probe = deepcopy(manifest)
    probe["status"] = "running"
    append(probe, entry)
    upstream = {e["id"]: e for e in manifest["entries"]}
    if any(upstream[i]["status"] != "succeeded" for i in inputs):
        raise ValueError("Stage inputs must be successful entries")
    if use_cache:
        for previous in reversed(manifest["entries"]):
            if previous["status"] == "succeeded" and _identity(
                {key: previous[key] for key in request}
            ) == _identity(request):
                return manifest
    if manifest["status"] != "running":
        raise ValueError("A finished run cannot execute a new request")
    try:
        result = execute(
            deepcopy(manifest),
            store=store,
            parameters=deepcopy(parameters),
            inputs=deepcopy(inputs),
        )
        validate(result)
        if any(
            _identity(result[key]) != _identity(manifest[key])
            for key in manifest
            if key != "entries"
        ):
            raise ValueError("A stage changed run metadata")
        if len(result["entries"]) != len(manifest["entries"]) + 1 or _identity(
            result["entries"][:-1]
        ) != _identity(manifest["entries"]):
            raise ValueError("A stage must append exactly one entry")
        if _identity({key: result["entries"][-1][key] for key in request}) != _identity(request):
            raise ValueError("Stage output does not match the request")
        store.verify(result)
    except Exception:
        entry.update(status="failed", reason="Stage execution failed; diagnostics withheld")
        store.save(append(manifest, entry))
        raise StageExecutionError(f"{stage} failed; see entry {entry['id']}") from None
    store.save(result)
    return result
