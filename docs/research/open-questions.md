# Open questions

- Date: 2026-11-14

What we do not know, roughly in the order it hurts. Each one is a candidate
research ticket.

## 1. What is actually growing in a data-centre loop

We have no composition data from a real loop. The default target is an
assumption, marked as one. Without a partner sample, every downstream choice
rests on a guess about which anchor dominates.

**Would settle it.** A biofilm sample from an operator, sequenced, with the
matrix composition characterised.

## 2. Whether the envelope is right

Temperature, pH, treatment chemistry and contact time in the default target
are assumptions. If the real loop is cooler or less alkaline than assumed, the
design problem gets easier and some natural enzymes may already do the job.

**Would settle it.** Operating data from a running loop.

## 3. Whether our stability predictions mean anything

Until a direction case and a magnitude case pass, the shortlist is an ordering
nobody has checked. This is the gap most worth closing with hours, because it
is the one that decides whether the whole pipeline is informative.

**Would settle it.** Retrodiction against published stability measurements,
with the tolerance fixed first.

## 4. Whether a stabilised variant still cuts

The integrity check is a geometry filter, not an activity prediction. A
variant can pass it and still be slower, and we would not see that.

**Would settle it.** An activity proxy worth trusting, or assay feedback from
a partner.

## 5. Whether enzyme reaches the film at all

Diffusion into a dense matrix, in flowing water, with limited contact time, is
a transport problem this repo does not model. An enzyme that works in a test
tube may do nothing in a loop for reasons that have nothing to do with its
fold.

**Would settle it.** A simple transport model first, then a rig.

## 6. Cost and dosing reality

Enzymes are made by fermentation and are not free. Whether a dose that does
anything useful is affordable at loop volumes is an economics question we have
not touched.

**Would settle it.** A partner conversation, and a back-of-envelope dose
calculation once an enzyme and a loading are named.
