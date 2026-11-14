# Agent guide

How an engineering agent should work in this repo.

## Skills

### Issue tracker

Issues and specs live in this repo's GitHub Issues. See
[`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Domain docs

Single-context layout: [`CONTEXT.md`](CONTEXT.md) and [`docs/adr/`](docs/adr)
at the repo root, with the biology behind them in
[`docs/biology/`](docs/biology). See
[`docs/agents/domain.md`](docs/agents/domain.md).

### Wayfinder

Each milestone opens with a `wayfinder:map` issue. Research and grilling
tickets hang off it and resolve into ADRs before build tickets start. The
frontier is the set of open child tickets with no open blocker.

## Invariants

These do not change without an ADR that supersedes this list.

### Nothing is claimed that a model cannot support

Every number in this repo, in the dashboard, in an issue and in a demo comes
from a named model at a named version, or from a cited measurement. A
prediction is labelled as a prediction wherever it is shown. No efficacy
claim, no saving figure, no dosing advice.

### No wet lab, and no pretending otherwise

Nothing here has been tested on a real biofilm. Any output that could be read
as a result carries that fact next to it.

### Targets are data

A biofilm composition, an organism, an anchor or an envelope belongs in a file
under `targets/`, never in code (ADR-0002). A change that supports a new
target should not touch a stage.

### Stages talk only through the run manifest

A stage reads the manifest and appends to it. No stage imports another
stage's internals. Two implementations of the same stage are interchangeable
if they read and write the same manifest fields.

### The active site is not a design target

Design changes the chain away from the active site. Every variant passes the
integrity check before it is scored, and a variant that fails is rejected
whatever its stability estimate (ADR-0005).

### A scoring model is trusted only after it retrodicts

Before a scoring model's numbers reach the shortlist or the dashboard, it has
at least one retrodiction case: a published measurement, the prediction, and a
tolerance agreed before the run. A tolerance is never loosened to make a case
pass; a failing case is a finding, written up as one.

### The scientist cites or declines

The `explain` agent answers from the artefacts of the run in front of it. If
the run does not contain the answer, it says so. It does not reach for general
knowledge and present it as a result of the run.

### Nothing here makes an organism more harmful

Sonazyme designs enzymes that degrade matrix polymers outside the cell. No
work on toxins, virulence, host range, transmissibility or resistance, and no
design against a human or animal target. See [SECURITY.md](SECURITY.md).

## House style

British English. Plain, short sentences. No marketing tone in commits, issues,
or ADRs. No em dashes.

Do not oversell. Sonazyme is an early design tool with no experimental
results. Say what has been built and what a model predicted, and nothing more.

Commit messages and pull request titles follow Conventional Commits:
`<type>(<scope>): <description>`, lowercase, imperative, concise, for example
`feat(score): add the active-site integrity check`. The body, when present,
stays plain and explains why. Reference an issue with `refs #<n>` in the body,
never a closing keyword; build issues close when their release is tagged, not
on merge. No commit carries a co-author trailer.
`scripts/conventional_commits.py` enforces the format in CI.
