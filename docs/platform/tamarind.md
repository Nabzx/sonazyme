# Tamarind Bio

**Stage:** `design`

## What we use it for

Generating and optimising variants of a chassis enzyme without standing up
protein design infrastructure ourselves. We hand it a chassis sequence, the
region that must not change (the active site), and the objective we are
designing for, and it returns candidate variants.

## What the stage must do around it

- **Supply the exclusion.** The active site, as defined for that chassis, is
  passed as off limits. Any returned variant touching it is rejected before
  scoring ([ADR-0005](../adr/0005-active-site-is-not-a-design-target.md)).
- **Record the strategy.** Which design approach produced each variant, so a
  shortlist can be read as "consensus found this" rather than "the computer
  said so".
- **Keep the rejects.** Variants proposed and then rejected stay in the
  manifest. What the search tried and lost is information.

## What we trust it for

Proposing plausible variants, faster and better than hand-picking mutations.

## What we do not

Deciding whether a variant is good. Design scores from a design tool are a
proposal, not an assessment: scoring is a separate stage, scored by a model
that has retrodicted published measurements.

## Manifest fields

`stage: design`, service, model, version, chassis id, excluded region, the
objective, variant ids with mutation sets and originating strategy, rejects
with reasons, and the artefact path for the variant set.
