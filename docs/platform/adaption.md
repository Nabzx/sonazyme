# Adaption Labs

**Implemented here:** `explain`

The explanation integration uses the Responses API through the official
Python SDK. It reads `ADAPTION_API_KEY` from the process environment and
requires `ADAPTION_EXPLAINER_MODEL` to name an active model or inference stack.
For a trained AutoScientist checkpoint, publish it through an active inference
stack and use its `stack:<slug>` identifier. Install the optional SDK
dependency with `pip install ".[api]"`. Numerical scoring and refinement are
not implemented by this adapter.

## What we use it for

Producing a final, model-generated selection from the successful folded
candidates in the current run. The report names one candidate, gives its
rationale and entry citations, and includes any comparable measurements
recorded in the run.

## What the stage must do around it

- **Use run evidence only.** Candidate codes and measurements come from the
  run. The selected candidate cites its fold entry, and any measurement
  comparison cites the run entry that records it.
- **Compare like with like.** A prediction is compared with a measurement only
  when the metric name and unit match.
- **Decline unsupported comparisons.** If the run contains no comparable
  measured metric, the write-up must say so.
- **Do not imply training-set access.** No training-data export is supplied to
  inference. The report states that it did not compare against Adaption's
  training records.
- **Keep the selection qualified.** A model choice among folded candidates is
  not a ranked shortlist, a stability score or an experimental result.

## What we trust it for

Selecting one folded candidate for further investigation and explaining the
choice against recorded run evidence.

## What we do not

Generating scores, measurements, activity claims, or treatment advice. A
model-generated explanation is not an experimental result.

## Manifest fields

`stage: explain`, Adaption model or stack id, candidate codes, run-entry
citations, measured comparisons when present, and the explanation artefact
path. API keys are never recorded.

The explanation CLI accepts `--adaption-model`; otherwise it reads
`ADAPTION_EXPLAINER_MODEL`. When configured, the final `explain` stage sends
the successful folded candidates and any measured metrics recorded in the run.
Its structured report is stored with the run, and its citations are checked
against run entry ids. No exact training-data export is present in this
repository, so the report explicitly says that it did not compare the choice
with Adaption's training records. It must not infer a FireProtDB precedent or a
training-set value from model memory.
