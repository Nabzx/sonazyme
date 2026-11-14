# ADR-0002: Targets are data, not code

- Status: Accepted
- Date: 2026-11-14
- Issue: #3

## Context

The biofilm inside a cooling loop is not one fixed thing. Which organisms
dominate, which polymers hold the film together, and what the water is like
all vary with the site, the metal, the temperature and the treatment history.
The team does not know, on day one, which composition matters most, and the
honest answer at the demo is that the target is an assumption we can change.

The same pipeline is also meant to reach beyond data centres later, to marine
surfaces and spacecraft water loops, where both the film and the conditions
differ.

If the organism, the anchors or the envelope are embedded in the stages, every
one of those changes is a code change, and the claim that this is a platform
is not true.

## Decision

A target is a file in `targets/`, one per target. It names the organism or
community, the anchors in its matrix, the bond each anchor offers, and the
envelope: temperature range, pH range, treatment chemistry present, residence
time.

Each value in a target carries its source, or is marked explicitly as an
assumption. A stage reads a target and never hard-codes any part of one.

Adding a target is adding a file. If supporting a new target requires changing
a stage, that is a defect in the stage contract and gets an issue.

## Consequences

- The uncertainty about composition is visible on the surface of the repo
  rather than buried in code.
- Swapping to the marine or spacecraft case is a demo, not a rewrite.
- The target schema carries weight, and a mistake in it costs more than a
  mistake in a stage. It gets its own research ticket in M1.
- Two targets can disagree about the same organism. That is allowed, and the
  disagreement is readable.

## Alternatives considered

**One hard-coded data-centre target.** Rejected. Faster for a weekend, but it
makes the platform claim false and makes the first partner conversation a
rewrite.

**A database.** Rejected for now. Files diff, review and travel with the repo.
A database is worth revisiting when targets are generated from site data
rather than written by hand.
