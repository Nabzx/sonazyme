# Boltz-2

**Stage:** `fold`

The [local wrapper and artefact contract](../architecture/folding-and-integrity.md)
are implemented. They have protocol checks using synthetic outputs, not a
passing real inference run. Boltz compute and checkpoint provisioning remain
external. No Sonazyme model prediction or wet-lab result exists yet.

## What we use it for

Predicting a three-dimensional structure for each variant, with confidence,
and where the run calls for it, predicting the enzyme together with a fragment
of its substrate so the active-site geometry can be compared with the
chassis.

## What the stage must do around it

- **Fold the chassis first.** Every comparison is variant against chassis,
  predicted by the same model at the same version. Comparing a predicted
  variant with an experimental chassis structure would mix two different kinds
  of thing.
- **Carry confidence through.** A structure with low confidence in the region
  that matters is a weak basis for a score, and the dashboard shows that
  rather than hiding it.
- **Keep the coordinates.** The structure file is the artefact the dashboard
  renders and the agent cites.

## What we trust it for

A good prediction of the folded shape, and a usable comparison between a
variant's shape and its chassis.

## What we do not

- **Stability.** A structure is not a melting temperature. Stability is a
  separate prediction in `score`.
- **Temperature or pH behaviour.** The model takes neither as an input and
  returns one static structure rather than an ensemble. This is the specific
  reason pre-compensated design is out of scope
  ([ADR-0003](../adr/0003-rigidify-not-pre-compensate.md)).
- **Activity.** Geometry surviving is a filter, not a promise that the enzyme
  still cuts.

## Manifest fields

`stage: fold`, model, version, variant id, structure artefact path, confidence
summary and per-region confidence for the active site.
