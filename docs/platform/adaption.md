# Adaption Labs

**Stages:** `score`, and the refinement loop behind `design`

## What we use it for

Two jobs.

1. **Scoring.** Predicting how well a variant holds its fold in the target's
   envelope, from the sequence and the predicted structure.
2. **Refinement.** Feeding what the scores showed back into the next round of
   design, so later rounds propose better variants than earlier ones.

## What the stage must do around it

- **Retrodict before trusting.** A scoring model reaches a shortlist only
  after at least one retrodiction case passes: a published measurement, the
  model's prediction of it, and a tolerance fixed beforehand
  ([docs/validation/](../validation/README.md)).
- **Record the sign convention.** Stability conventions differ between tools.
  The manifest records which model produced a number so two numbers are never
  silently compared.
- **Keep rounds separate.** Round two exists because of round one, and the
  manifest shows that chain, which is what makes the refinement loop worth
  claiming.

## What we trust it for

Ranking variants against each other within one model and one envelope.

## What we do not

Absolute numbers. A predicted melting temperature is not a measured melting
temperature, and nothing in this repo presents one as though it were.

## Manifest fields

`stage: score`, model, version, variant id, stability estimate with its
convention, integrity check result and tolerance, round number, and the
artefact path for the score table.
