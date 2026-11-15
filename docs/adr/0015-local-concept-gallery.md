# ADR-0015: Simplify the local front page and add an enzyme concept gallery

- Status: Accepted
- Date: 2026-11-15
- Scope: the local visual experiment requested by the user

## Context

The user wants Sonazyme to use Doctor of Pipes as its hero headline, with
autonomous cleaning of cooling pipes and a diagnose-then-prescribe narrative.
They explicitly requested removal of several explanatory notices and selected
stylised shapes labelled AI-generated enzyme concepts for a new carousel.

## Decision

Keep Sonazyme as the brand. Rename the visible Sonar section to Detection.
Use a blue material for the hero enzyme without changing its predicted
coordinates or the simulation card's active-site colours.

Remove the requested notices and their empty layout space. For this local
visual experiment, this supersedes the presentation-notice requirements of
ADR-0006, ADR-0013, ADR-0014 and the agent guide's adjacent experimental-status
notice. It does not change the basis or provenance of saved data, pipeline
behaviour, scoring requirements or the explain stage's evidence rules.

Add one carousel of decorative parametric sculptures using the existing
self-hosted Three.js dependency. Label the section AI-generated enzyme
concepts. The sculptures are visual concepts, not predicted coordinates or
functional protein sequences, and never enter a run manifest or shortlist.
Their family descriptions use the general biology in
`docs/biology/06-which-enzyme-cuts-what.md`. Do not attach fabricated scores,
measurements, catalytic positions or activity claims to them.

Support selection by buttons, keyboard, horizontal dragging, clicking a
sculpture and wheel input. Wheel scrolling passes back to the page at the
first and last entries. Respect reduced motion and keep the text controls
usable without WebGL. The gallery only renders while visible.

## Consequences

The local page is shorter and less repetitive. The hero describes the intended
product workflow rather than operating a physical cleaning system. Actual
Boltz and HyperMPNN information remains distinct from decorative concepts.
No new runtime dependency, model inference, deployment or lab result is added.
