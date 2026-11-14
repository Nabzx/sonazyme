# Folding and the integrity gate

Contracts for #27 and #28 are in
[ADR-0010](../adr/0010-chassis-fold-and-integrity-contracts.md).
Automated checks use synthetic software fixtures. No real Boltz prediction,
biological integrity comparison or Sonazyme wet-lab result has been produced.

## Provision the model separately

The wrapper uses the [official Boltz CLI](https://github.com/jwohlwend/boltz/blob/b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc/docs/prediction.md).
Command and output handling were checked against source revision
`b1ebfc46ecf57f5414e0d1a6f9027bbb122c53bc`. This is the source inspected, not
a claim that its weights were downloaded or its package installed here.

Provision a Boltz Python environment and checkpoint on suitable compute.
Sonazyme does not install that stack as part of its own package. The wrapper
checks `importlib.metadata.version('boltz')` in the selected environment
and hashes the checkpoint bytes before execution. Record those exact values
in a settings JSON file. A mutable model alias is not a version.

The settings shape is:

```json
{
  "adapter_version": "1",
  "package_version": "REPLACE_WITH_INSTALLED_BOLTZ_VERSION",
  "checkpoint_sha256": "REPLACE_WITH_CHECKPOINT_SHA256",
  "seed": 0,
  "accelerator": "gpu",
  "recycling_steps": 3,
  "sampling_steps": 200,
  "msa": {"mode": "single"},
  "ligand": null
}
```

Seed and inference settings are configuration choices, not predicted numbers.
The placeholders deliberately fail validation. Boltz's documented default
recycling and sampling settings are shown; choose and record settings
before prediction. Seeds do not guarantee bit-identical GPU output.

Single-sequence mode is an explicit opt-in and reduces accuracy according to
the official documentation. Prefer a supplied A3M alignment when available:
`msa` then has `mode: provided` and `artefact: <run reference>`.
The wrapper never enables the public MSA server. The upstream CLI may still
download model or chemical resources into the supplied cache; this is not an
offline inference promise.

After [loading a target and chassis](../../targets/chassis/README.md), run:

```bash
python -m sonazyme.fold --run-dir runs/chassis-check \
  --settings /path/to/fold-settings.json \
  --boltz-python /path/to/boltz-environment/bin/python \
  --checkpoint /path/to/boltz2-checkpoint.ckpt \
  --cache /path/to/boltz-cache
```

Those paths need real provisioned resources. No such model environment or
checkpoint is configured here. Cache identity uses checkpoint bytes and the
package version, not the filename.

## Artefacts and variants

`fold` consumes one declared chassis entry and a subject artefact from its
declared inputs. A baseline subject is the selected chassis record. A variant
subject is v1 JSON with `kind: variant`, `id`, `chassis_id`, `sequence`
and `mutation_set` (substitutions such as `A1V`). It must be recorded by a
successful upstream entry. Protected substitutions, incomplete exclusions,
indels and inconsistent mutation sets fail before inference. No real variant
record is shipped; the current PslG record is not design-ready.

The fold entry's first artefact is its JSON index. It references raw
PDB, raw confidence summary, normalised confidence and the request document.
All are listed directly in the manifest entry. Per-residue pLDDT is read
from the PDB B-factor scale, divided by 100, retaining the writer's rounding.
Protected-region confidence is separate. These are predictions, not stability
or activity estimates. No dashboard exists yet.

For complex mode, `ligand` has `format` (`smiles` or `ccd`), `value` and
`source`. It supplies one additional chain. This does not establish that the
ligand represents the matrix polymer. #52 remains open. No fragment is
invented and affinity prediction is disabled.

## Integrity policy and scoring hand-off

`sonazyme.score.integrity.run` accepts three ordered entry ids: chassis,
baseline fold and variant fold. Parameters are `role: integrity` and
`policy: <run artefact reference>`. Call it through the runner with the
`sonazyme.integrity` producer. It records a success or rejection with a
reason and geometry report, and calculates no stability estimate.

The policy requires `schema_version: 1`, `kind: integrity-policy`,
`method: max-pair-distance-v1`, `max_distance_change_angstrom`,
`min_active_site_plddt`, `rationale`, `purpose` and `agreement`. There is no
production threshold file or default. A production policy needs a link to
the prior agreement comment on #28. The software checks reference format;
it cannot verify that the comment approved the policy contents.

The check compares pairwise distances among protected named atoms and local
handedness. It is invariant to global translation and rotation. Missing atoms,
low predicted confidence, protected identity changes and geometry outside the
fixed threshold are rejected. Incompatible model or inference provenance
fails before comparison. Equivalent atom naming can cause conservative false
rejection. This is a catalytic-core filter, not evidence that a variant cuts
Psl or works in a loop.

Before calling Adaption for a stability estimate, its adapter must call:

```python
from sonazyme.score.integrity import require_integrity

report = require_integrity(
    manifest, store, baseline_fold_id, variant_fold_id, policy=policy_reference
)
```

This requires a passing production check for those exact folds and policy,
plus a design-ready chassis. A later failed or rejected attempt for the same
inputs and policy blocks reuse of an older pass. A `software-test` policy
never authorises scoring. Scoring also needs its separate retrodiction gate.

## Still unresolved

- Complete sourced binding-site exclusion for this PslG construct.
- A biological tolerance and confidence policy agreed on #28 before a run.
- Provisioned compute and an actual Boltz baseline, then a variant comparison.
- Enforcement of the integrity gate in the separate Adaption adapter.
- Evidence that the assumed target or envelope represents a real loop.
