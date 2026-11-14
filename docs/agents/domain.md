# Domain docs

How an engineering agent should consume this repo's domain documentation.

## Before working in an area, read these

- [`CONTEXT.md`](../../CONTEXT.md) at the repo root: the glossary.
- [`docs/biology/`](../biology): the biology behind every term, at GCSE level.
  Read it before writing anything that names a biological concept.
- [`docs/adr/`](../adr): the ADRs touching the area you are about to change.
- [`docs/architecture/ARCHITECTURE.md`](../architecture/ARCHITECTURE.md): the
  stage contract.
- [`docs/validation/README.md`](../validation/README.md): what a retrodiction
  case is.

## Use the glossary's vocabulary

When your output names a domain concept, in an issue title, an ADR, a test
name or a dashboard label, use the term as defined in `CONTEXT.md`. Do not
drift to a synonym the glossary lists under _Avoid_, and do not use the words
under _Words we do not use_.

If the concept you need is not in the glossary, that is a signal. Either you
are inventing language the project does not use, in which case reconsider, or
there is a real gap, in which case note it.

## Biology is not guessed

A sequence, a structure, an active-site definition, a temperature, a pH or a
published measurement comes from a cited source, next to the value. If you do
not have the source, say so and leave a `needs-research` note. Do not write a
plausible-looking number from memory, and do not let a number without a source
reach a target file, a score or the dashboard.

## Predictions are labelled

Any number a model produced is presented as a prediction, with the model and
version beside it, wherever it appears: code comments, issue bodies, commit
messages, dashboard copy.

## Flag ADR conflicts

If your change would contradict an Accepted ADR, say so openly rather than
quietly working around it:

> Contradicts ADR-0005 (the active site is not a design target), but worth
> reopening because ...

An Accepted ADR is changed only by a new ADR that supersedes it.

## The boundary

Before starting any piece of work, check it against the scope in
[`SECURITY.md`](../../SECURITY.md). Work that would increase the harm an
organism can do is out of scope here, whatever the framing on the issue.
