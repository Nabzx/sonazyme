# ADR-0003: Rigidify the chassis, do not pre-compensate the fold

- Status: Accepted
- Date: 2026-11-14
- Issue: #1

## Context

An enzyme dosed into a cooling loop meets conditions that most useful enzymes
were not evolved for: warm water, alkaline pH, and treatment chemistry already
in the loop. A protein that loses its fold there stops working, and an enzyme
bought off the shelf is tuned for a detergent or a food process rather than
for this.

Two ways to get an enzyme that works in the loop were on the table.

**Rigidify.** Keep the job, change the parts of the chain that give way first,
so the fold survives the envelope. This is ordinary protein engineering, and
the field has worked this way for decades: consensus and ancestral sequence
reconstruction, prolines at flexible loops, new disulfides and salt bridges,
repacking a loose core. There are public measurements to check a scoring model
against, so a prediction can be retrodicted rather than only asserted.

**Pre-compensate.** Predict how the fold shifts under load and design the
chain so that it lands in the working shape once it is hot, in the way an
engineer pre-bends a part that will relax after welding. This is the more
striking idea, and it is the one in the original pitch.

The problem with pre-compensation is what today's structure predictors
produce. A model like Boltz-2 predicts a structure, not a temperature-
dependent ensemble, and it does not take temperature or pH as an input. There
is no conditioning knob to aim off with. Doing this properly means sampling an
ensemble, usually with molecular dynamics at the target temperature, which is
far outside a hackathon and would arrive with no retrodiction to back it.
Claiming it on stage, in front of anyone with a structural biology
background, is a claim the repo cannot support.

## Decision

Sonazyme designs for stability in the envelope by rigidifying the chassis. The
`design` stage proposes mutations away from the active site, `score` predicts
how well the variant holds its fold in the envelope, and the shortlist is
ranked on that against predicted activity and confidence.

Pre-compensation is recorded as a research direction in the roadmap, under
"later, not scheduled". It is not claimed, not demonstrated and not implied in
the dashboard, the README or the pitch. If it is explored, it starts with a
retrodiction question: can any available method predict the direction of a
measured conformational shift with temperature, on cases where the answer is
already known.

## Consequences

- Every number the demo shows rests on a method with public measurements
  behind it, so the retrodiction policy is possible to follow.
- The pitch loses its most eye-catching line and gains one that survives
  questions. The honest framing is stated in the README: the enzyme is
  redesigned to hold its shape, not redesigned to arrive at a shape.
- Rigidifying risks trading away activity, since a stiffer protein is often a
  slower one. The ranking has to show that trade-off rather than hide it
  behind one blended score, which is why ranking is multi-objective in M5.
- If a conditioned structure model arrives that takes temperature as an input,
  this decision is worth reopening with a new ADR.

## Alternatives considered

**Pre-compensate now.** Rejected. No conditioning input exists in the models
available, the proper method does not fit the time, and the claim would be
unbackable.

**Screen natural thermophile enzymes only, no design.** Rejected as the whole
answer. It is a sensible baseline and belongs in `chassis` as a source of
parents, but it is not a platform, and the chance that a natural enzyme
matches both the anchor and the envelope is thin.

**Immobilise or encapsulate the enzyme instead.** Rejected for now as a
different product. It is a formulation route rather than a design route, and
it does not use the tools this project is built on. Worth revisiting with a
partner.
