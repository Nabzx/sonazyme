# ADR-0005: The active site is not a design target

- Status: Accepted
- Date: 2026-11-14
- Issue: #3

## Context

Stability and activity pull against each other. The parts of an enzyme that
move are often the parts that work, and a search that optimises only for
holding its fold will happily stiffen the enzyme into something that no longer
cuts anything. The search has no way of noticing, because the stability model
it is scored by does not know what the enzyme is for.

A dead but very stable variant at the top of a shortlist is the most damaging
failure this project can have, because it looks like a success.

## Decision

Design changes the chain away from the active site. The active site is defined
for each chassis, with its source, before any design runs.

Every variant passes an integrity check before it is scored: its predicted
active-site geometry matches the chassis within a tolerance fixed in advance.
A variant that fails the check is rejected and recorded as rejected, whatever
its stability estimate. Rejected variants stay in the manifest, because what
the search tried and lost is information.

The dashboard shows the active site coloured separately from the changed
region on every structure it displays, so the viewer can see it was left
alone.

## Consequences

- The shortlist cannot be topped by a stabilised brick.
- The demo has a clear visual answer to "how do you know it still works":
  changed region in one colour, untouched active site in another.
- Defining the active site per chassis is manual work in M2 and needs a cited
  source for each one.
- Mutations far from the site can still affect activity through the chain, and
  this check does not catch that. It is a filter, not a guarantee, and it is
  described that way wherever it appears.

## Alternatives considered

**Score activity directly and let the ranking balance it.** Rejected as the
only mechanism, for now. Activity prediction for a designed enzyme on a polymer
substrate is a much weaker prediction than stability, so leaning on it alone
would put confidence where it is not earned. The integrity check is a cheap
hard filter underneath whatever activity signal is added later.

**Allow active-site redesign for better substrate fit.** Rejected at this
stage. It is a real technique, and it needs assay feedback that this project
does not have.
