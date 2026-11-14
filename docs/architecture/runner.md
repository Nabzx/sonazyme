# Running and resuming a stage

The runner implements #24 under [ADR-0009](../adr/0009-single-writer-stage-runner.md).
It uses the [manifest and store](manifest-v1.md), with no runtime dependencies.

## Try the implemented stage

From the repository root, create and activate a local environment first:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Then run:

```bash
python -m sonazyme.sense targets/psl-literature.toml --run-dir runs/target-check
```

Activation is needed in each new terminal. If the environment is already
installed, `.venv/bin/python -m sonazyme.sense ...` also works without activation.

The command validates the target, stores the original bytes, appends a `sense`
entry pointing at normalised JSON and saves `runs/target-check/manifest.json`.
Running it again reuses the saved success. Changing the source target requires
a new run directory. The saved target remains the original input, even if a
file elsewhere changes. This is schema and provenance integration only, not a
design run or evidence of envelope-aware scoring. No model is called.

## Add a stage adapter

`run_stage(store, stage=..., producer=..., parameters=..., inputs=..., execute=...)`
loads the saved run, checks the request and calls the supplied function only
if there is no matching success. The callable contract is:

```python
def execute(manifest, *, store, parameters, inputs):
    # Read the target and declared input entries' artefacts.
    # Write any output files using store.put(bytes).
    # Return append(manifest, entry), with exactly one new entry.
    ...
```

The new entry must match the requested stage, producer, parameters and ordered
input ids. It needs its own unique id, status, metrics, artefacts and reason
under the manifest contract. The runner verifies all referenced files before
saving. The adapter does not call `store.save` or seal the run. It must declare
every input and setting influencing output, including seed, round and tool
versions. The runner cannot infer whether the adapter omitted one.

Reuse requires the same target within the same run, stage, exact producer
version, parameters and ordered input entry ids. Changed settings or input
entries trigger execution. Failures and rejects never count as cache hits.
`use_cache=False` requests a new attempt. There is no cross-run reuse.

An adapter exception or invalid returned manifest records a failed attempt,
then raises `StageExecutionError`. Provider messages are withheld to avoid
putting credentials in the manifest. A subsequent invocation retries without
deleting the failure. A returned rejection is recorded and returned to the
caller; downstream requests cannot use it as a successful input.

## Replay and completion

`store.load()` verifies the complete saved artefact chain without invoking a
stage. It works offline. A successful request can also be reused on a sealed
run. A new request on a sealed run fails. Call `store.save(finish(manifest))`
only when writing the run has ended. A sealed run may contain failures and
does not imply that a shortlist or trusted prediction exists.

The single writer owns the run directory. There is no lock or parallel stage
execution. Interrupts can leave unreferenced output files or a remote job
whose completion was never saved. Recovery of remote jobs and provider-side
idempotency belong in the service adapters. This is not an exactly-once
external execution guarantee, scheduler or autonomous orchestrator.
