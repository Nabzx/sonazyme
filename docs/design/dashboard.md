# Sonazyme Lab

The dashboard. Five screens, in order, built to be walked through in about
four minutes and then left running for anyone who wants to poke at it.

The rule underneath all of it: every number on screen comes from a run
manifest entry, with the model that produced it shown next to it, labelled as
a prediction ([ADR-0004](../adr/0004-provenance-on-every-number.md)). A screen
reading a cached run says so, with the date of the run
([ADR-0006](../adr/0006-demo-track.md)).

## Screen 1, the problem

An animation, not a wall of text. A pipe wall, cells arriving and sticking,
the matrix building up, a biocide dose arriving, the cells at the surface
dying, the matrix staying, the film returning over the following days.

The one line it has to land: killing the cells does not remove what holds the
film to the wall.

No numbers here, so nothing to cite.

## Screen 2, the baseline

The chassis enzyme, rendered in 3D and rotating, with the active site coloured
distinctly.

Beside it, the envelope from the target file, each value marked as sourced or
assumed, and the chassis stability estimate in that envelope with the model
that produced it. Where the estimate says the chassis gives way inside the
envelope, the overlay says so plainly: this is the enzyme you would buy, and
this is where it stops holding its shape.

Reads: `sense`, `chassis`, `fold`, `score` entries.

## Screen 3, the redesign

The core of the demo. Variants arrive in a list as they are scored, each with
its mutation set, its stability estimate and its integrity result. Rejected
variants appear struck through with the reason, because a search that only
shows winners is not showing a search.

Then the comparison: chassis and best variant side by side, same orientation,
with the changed region highlighted in one colour and the active site in
another, visibly untouched.

Reads: `design`, `fold`, `score`, `rank` entries.

## Screen 4, the question

A text box. Ask the scientist agent something about what is on screen, for
example why the top variant beat the chassis, or what the integrity check
actually checked.

The answer comes back with what it cites: which manifest entries, which
artefacts. If the run does not contain the answer, the agent says so. That
refusal is part of the demo, not a failure of it, and it is the thing that
separates this from a chatbot with a protein picture behind it.

Reads: `explain`, which reads everything above.

## Screen 5, the case

The status quo against the approach, with the open questions named rather than
hidden: no wet-lab result, assumed envelope, predicted numbers throughout,
and what it would take to find out. Positioned as a design and triage tool for
industrial biotech partners.

## Visual language

- Dark, instrument-panel feel. The hero image in `assets/hero.svg` sets the
  palette.
- One accent colour for predictions, one for the active site, one for the
  changed region. Those three never swap meaning between screens.
- Every tile carries its model and version in small type. No exceptions, no
  hover-to-reveal.
- An assumed value is visually marked as assumed wherever it appears.

## Build notes

The app reads the API, which serves run manifests and artefacts and computes
nothing ([ARCHITECTURE.md](../architecture/ARCHITECTURE.md)). It must run from
a cached run with no network, because conference wifi is not a dependency
anyone should accept.
