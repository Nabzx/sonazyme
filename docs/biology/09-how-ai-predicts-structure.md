# 9. How AI predicts structure

Finding a protein's shape by experiment is slow and expensive. X-ray
crystallography, cryo-electron microscopy and related methods have produced a
public archive of solved structures built up over decades, the Protein Data
Bank.

Structure prediction turns that archive into a shortcut: given a sequence, say
what the folded shape is. Modern models do this well enough that for many
proteins the prediction is close to what an experiment would show.

## Roughly how it works

Two ingredients.

**Evolution.** Take the sequence you care about and find hundreds of related
sequences from other organisms. If two positions in the chain are always
mutated together across that family, something is holding them in a fixed
relationship, which usually means they touch in the folded shape. That is
information about the three-dimensional shape hidden inside a pile of
one-dimensional sequences.

**Learned structure.** A large model trained on the solved structures learns
the patterns proteins actually adopt: how helices pack, how loops close, what
geometry is physically possible. The model combines that with the evolutionary
signal to produce coordinates for every atom.

The output is a predicted structure plus a **confidence** score, usually per
residue. Confidence is itself a prediction, and low confidence often marks a
part of the protein that genuinely has no single fixed shape.

## What Boltz-2 gives us

Boltz-2 is an open structure model. For Sonazyme it does two jobs:

1. Fold a variant. Does the designed sequence still fold the way the chassis
   does, and is the model confident about it?
2. Predict interaction. Modelling the enzyme together with a piece of its
   substrate shows whether the active site still presents the right geometry
   to grip it.

## What Tamarind Bio gives us

Tamarind Bio is the platform we use to run protein design and optimisation
without building that infrastructure ourselves. It proposes variants of a
chassis and runs the tooling around them. In this repo it sits behind the
`design` stage, and what it produced for a run, at which version, is recorded
in that run's manifest.

## The limits, stated plainly

These matter more than the capability, and a judge is right to press on them.

- **A prediction is not a measurement.** A confident structure is a very good
  guess, and the prediction is strongest for proteins resembling what the
  model has seen.
- **It predicts one shape, not the ensemble.** A real protein wobbles between
  arrangements. The model gives a single representative structure.
- **Temperature and pH are not inputs.** You cannot ask a structure model for
  "this protein at 50 °C and pH 9". This is precisely the gap that rules out
  pre-compensated design for now
  ([ADR-0003](../adr/0003-rigidify-not-pre-compensate.md)).
- **Structure is not stability, and neither is activity.** Knowing the shape
  does not tell you the melting temperature or the reaction rate. Those are
  separate predictions from separate models, which is why `score` is a
  separate stage, and why a scoring model must retrodict published
  measurements before its numbers are allowed into a shortlist
  ([docs/validation/](../validation/README.md)).

**Next:** [inside a cooling loop](10-inside-a-cooling-loop.md).
