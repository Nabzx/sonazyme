# ADR-0004: One run manifest, provenance on every number

- Status: Accepted
- Date: 2026-11-14
- Issue: #3

## Context

A run passes through several external models: variant design at Tamarind Bio,
structure prediction at Boltz-2, stability scoring through Adaption Labs. Each
has its own version, its own failure modes and its own idea of what a score
means. By the time a number reaches a dashboard tile or the mouth of an agent,
it is very easy to lose track of which model produced it and on what input.

That matters more here than in most projects. The whole value of this repo is
triage: telling a partner which variants are worth making. A shortlist nobody
can audit is worth nothing, and an agent that explains a candidate using
general knowledge rather than the run's own output is a demo trick.

## Decision

Every run has one manifest. Each stage appends to it: the inputs it read, the
model and version it called, the parameters, the score it produced, and the
path of every artefact it wrote. Artefacts are files; the manifest references
them and does not contain them.

Nothing downstream reads anything except the manifest and the artefacts it
points at. The dashboard reads the manifest. The scientist agent reads the
manifest. A run can be replayed from the manifest alone.

Every number shown to a human is shown with the model and version that
produced it, and is labelled as a prediction. A number with no manifest entry
behind it does not get displayed.

## Consequences

- Any claim on screen can be traced to a model call in a few seconds, which is
  the answer to the sharpest question a judge or a partner can ask.
- The scientist agent becomes checkable: its claims point at artefacts.
- Caching, replay and the offline demo fall out of the same structure.
- Every stage carries manifest-writing code, and the manifest format becomes a
  contract that needs an ADR to change.
- Scores from different models are not comparable just because they sit in the
  same table, and the manifest does not fix that on its own. Ranking has to
  handle it explicitly.

## Alternatives considered

**Stages passing objects in memory.** Rejected. Faster to write, but the run
is then unreproducible and the agent has nothing solid to cite.

**Logging.** Rejected as the mechanism. Logs are for humans debugging, are
written in whatever shape suits the moment, and are not a contract.
