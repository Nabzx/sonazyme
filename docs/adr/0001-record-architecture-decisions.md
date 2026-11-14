# ADR-0001: Record architecture decisions

- Status: Accepted
- Date: 2026-11-14
- Issue: #3

## Context

Sonazyme starts under time pressure, and the decisions made in the first days
are the ones that are hardest to see later: which model is trusted for what,
what a target is allowed to contain, what the system is permitted to claim.
A decision that lives only in someone's head is re-argued every week and
quietly reversed by the next person to touch the code.

## Decision

Every decision that constrains future work is written as a numbered ADR in
`docs/adr/`, using `0000-template.md`. An ADR is written before the code it
governs. Once Accepted it is immutable; it changes only by a new ADR that
supersedes it.

ADRs are required for anything touching the stage contract, the run manifest,
the target schema, which external model a stage calls, the ranking objectives,
what the scientist agent may say, and any new dependency.

## Consequences

- An argument is had once and stays had.
- A reviewer can reject a change by pointing at an ADR instead of relitigating.
- Writing an ADR costs time at the start of each piece of work.
- The repo doubles as the explanation of itself, which is most of what a judge
  or a partner wants to read.

## Alternatives considered

**Decisions in the README.** Rejected. The README is overwritten constantly
and keeps no history of what was considered and dropped.

**Decisions in issues.** Rejected on its own. Issues record the discussion but
close and sink. An ADR is the settled output; the issue stays as the trail.
