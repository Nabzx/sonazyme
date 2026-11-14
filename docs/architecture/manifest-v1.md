# Using the run manifest

Implemented for #22 and #23, under
[ADR-0007](../adr/0007-manifest-and-artefact-format.md).
No external service is called by this example. It is an integration example,
not a biological run, retrodiction case or model prediction.

```python
from pathlib import Path

from sonazyme.core.manifest import append, create, finish
from sonazyme.runs.store import RunStore

store = RunStore(Path("runs/integration-example"))
target = store.put(b"integration example only")
manifest = create("integration-example", target)
store.save(manifest)

entry = {
    "id": "sense-1",
    "stage": "sense",
    "status": "succeeded",
    "producer": {"name": "sonazyme", "version": "0.0.1", "kind": "code"},
    "inputs": [],
    "parameters": {},
    "metrics": [],
    "artefacts": [],
    "reason": None,
}
manifest = append(manifest, entry)
store.save(manifest)
store.save(finish(manifest))
assert store.load()["status"] == "finished"
```

## Integration hand-off

Each adapter keeps its large response in `store.put(response_bytes)` and adds
the returned reference to `artefacts`. Save each attempt before starting the
next external call. Keep the provider's model name and actual version in
`producer`, never a guessed version. An unavailable version blocks recording
a successful prediction. The provider/service name, strategy, seed, round and
public request settings belong in `parameters`.

`inputs` links entries, not artefact paths. Each consumed artefact must be
reachable from the target or an input entry. The caller still enforces the
stage-specific input/output fields; v1 validates only the common envelope.
Variants, mutation sets, structures and score tables need their own agreed
artefact formats before the first integration run.

For a predicted metric, use `basis="prediction"` and copy the producer object
into `source`. A measured metric uses `basis="measurement"` with a citation
string. `unit` is mandatory, including for dimensionless metrics. Rejects and
failures carry a public `reason`, no success metrics, and any useful diagnostic
artefact. Keep rejected variants in the variant artefact, not just in a log.

Unknown target values remain unknown. A target assumption is not a measurement
and does not belong in a measured metric. Its marking stays in the target.

## Limits

- This is persistence. The [runner](runner.md) adds execution and run-local
  cache reuse (#24).
- A finished manifest means writing has ended. It does not mean every stage
  succeeded, that a shortlist exists, or that the science is trusted.
- The reader verifies artefact bytes, not the truth of their contents.
- Scoring retrodiction, active-site integrity and ranking gates remain the
  responsibility of their stages. Persistence does not approve a score.
- One process owns a run. Concurrent writers need a later locking decision.
- Caller-supplied parameters and diagnostics must exclude credentials.

## Next work

#7 now has an [evidence-bearing target schema](../../targets/README.md).
The evidence gathered so far is in [the target research note](../research/demo-target.md).
#8 still needs sequence and construct mapping and a sourced active-site
definition. The runner requires exact producer, parameter and input identity
for reuse, rather than inferring a cache hit from model name alone.
