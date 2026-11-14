# ADR-0006: Build the five-screen demo ahead of the milestones

- Status: Accepted
- Date: 2026-11-14
- Issue: #1

## Context

The milestones build the platform bottom up, and the first milestone that
would show a person anything is several in. The project also has to be
explained, from cold, in a few minutes, to people who will not read the repo.
A pipeline nobody can see is indistinguishable from a pipeline that does not
exist.

Running the demo live carries risk: three external services, variable
latencies, and conference networking.

## Decision

The five-screen demo track runs ahead of the milestones and is the first goal.
The screens are listed in ROADMAP.md.

It is driven by one real run on one target, end to end, with its manifest
kept. The demo may replay that cached manifest rather than call the services
live, and whenever it does, the screen says it is a cached run with its date.
The pipeline behind it is the real pipeline, not a mock: no screen is allowed
to display a number that no model produced.

Screen 4, the question to the scientist agent, is answered from the run's own
artefacts. If the agent cannot answer from the run, it says so on stage. That
is a better demo than a fluent answer nobody can check.

## Consequences

- Something is visible from the first day, and the thinnest end-to-end path is
  forced early, which is where integration problems surface.
- Work goes into a dashboard before the scoring is good. Accepted: the
  dashboard reads manifests, so improving the scoring improves the demo with
  no rework.
- Cached runs need a clear visual marker, or the demo quietly becomes a
  pretence.
- The demo must not grow features the milestones do not want. Anything it
  needs that outlives it becomes a milestone ticket.

## Alternatives considered

**Build the platform first, demo later.** Rejected. Integration risk stays
hidden until the end, and nothing is showable in between.

**A mocked demo with invented numbers.** Rejected outright. It contradicts
ADR-0004, and it is the thing a sharp question destroys.
