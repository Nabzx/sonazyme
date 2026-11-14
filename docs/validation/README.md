# Retrodiction

How Sonazyme checks that a model it relies on is worth relying on. The policy
sits under the invariants in [AGENTS.md](../../AGENTS.md); this is how to
follow it.

## A retrodiction case

Four parts, all required:

1. **Measurement.** A published experimental number, with its source: a
   paper, a public dataset, a database entry. For stability that is usually a
   measured melting temperature or a measured stability change for a known
   mutation.
2. **Prediction.** What our model says, produced by code in the case, through
   the same stage the pipeline uses.
3. **Tolerance.** Fixed before the run, with one line on why it is that size.
   Experimental spread between labs is a good reason. "It is what the model
   achieves" is not.
4. **Kind.** `blind` if the measurement played no part in choosing or tuning
   the model. `calibration` if it did.

A case reports a simple baseline where one exists, for example predicting no
change at all. A model that cannot beat that baseline is not informative,
whatever its correlation looks like.

## Where they live

Cases are pytest files in [`validation/cases/`](../../validation/cases), one
per case, run in CI with the unit tests. Reference data goes in
`validation/data/` only if its licence allows redistribution. Otherwise the
case fetches it, or describes it and skips with a reason when it is absent.

## Rules

- A tolerance is never loosened to make a case pass.
- A failing case is a finding. Write it up in `docs/research/`, then change
  the model or document the limit.
- A case that only ever passed as a calibration check is not evidence that the
  model predicts anything.
- A scoring model with no passing case does not reach a shortlist or the
  dashboard.

## The ladder

Cases get harder as the milestones go on.

| Level | Question | First milestone |
| --- | --- | --- |
| Sanity | does the pipeline reproduce a chassis structure close to its known one? | M2 |
| Direction | for known mutations, does the score move the right way? | M4 |
| Magnitude | is the predicted stability change the right size? | M4 |
| Ranking | within one protein family, does the ranking match the measured order? | M5 |
| Held out | does it work on a protein family it was not chosen on? | M5 |

The honest position until the direction case passes: Sonazyme produces an
ordering nobody has checked. The repo says that where it matters.
