# ADR-0013: Simulate the acoustic front end, and label every reading simulated

- Status: Accepted
- Date: 2026-11-14
- Issue: #66

## Context

A cooling loop is a sealed box. Treatment is dosed on a schedule rather than
on evidence, so the project wants a sensing front end: pulses sent through the
pipe wall, returning changed by whatever is on the inside, giving a map of
where a film is building.

We have no instrumented loop, no fouled test rig and no public dataset of
acoustic returns from a biofilm. The three ways to show the idea were a
physics forward model producing synthetic signals, published measurement data,
or a bench rig with a transducer on a pipe section. A rig is out of reach in
the time available, and no dataset we can redistribute has been found.

The risk with simulation is obvious. A synthetic echo shown as though it were
a reading would be the worst thing in this project, worse than showing
nothing, because it is the one claim nobody in the room could check.

## Decision

The acoustic front end is simulated, through a forward model that takes a
stated layer thickness and returns the signal features such a layer would
produce. The inverse direction, estimating thickness from features, runs on
that simulated signal.

Three rules make that admissible.

1. **A reading carries its basis.** Every reading record states
   `basis: "simulation"`, names the forward model and its version, and carries
   the physical constants it used, each marked sourced or assumed.
2. **The screen says so.** Anywhere a reading, a fouling map or a thickness
   appears, it is labelled simulated, in the interface rather than in a
   footnote, in the same way an illustration is labelled.
3. **Uncertainty is not optional.** An estimate is reported with an interval,
   and the forward model's assumptions determine that interval. A simulation
   that reports a confident number is lying twice.

The constants are assumptions until #64 sources them. Biofilm is mostly water,
so its acoustic contrast with water is small, and the model is expected to
show wide uncertainty on a thin film. That is the honest result and it is not
hidden: it is the finding that #68 will either confirm or overturn.

## Consequences

- The sensing half of the product can be demonstrated end to end, and the
  pipeline can be wired for readings that a real instrument would later
  supply in the same shape.
- The limits are visible rather than argued about. A viewer can see the
  estimate widen as the film thins.
- Every surface that shows a reading needs the simulated marking, which is
  work in the dashboard as well as in the pipeline (#71, #75).
- Nothing here establishes that acoustics can distinguish biofilm from scale
  in a real loop. That question stays open in #68, and the ADR does not
  pre-empt it.
- When a rig or a dataset arrives, the reading record does not change shape:
  only its basis and its source change, which is the point of recording the
  basis at all.

## Alternatives considered

**Wait for real data.** Rejected for now. It leaves the sensing half of the
pitch as an assertion, and the pipeline unexercised.

**Show a hand-drawn animation only.** Rejected. It is honest but it teaches
the team nothing, and it produces no reading record for the rest of the
pipeline to consume.

**Simulate quietly, and describe it as sensing.** Rejected outright. It
contradicts ADR-0004, and it is the single fastest way to lose the room.
