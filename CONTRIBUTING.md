# Contributing

Sonazyme is early and is built by a small team. The process below is how that
team works. It is written down so a new member can pick it up in an hour.

## Outside contributions

Bug reports are welcome through the bug form. Pull requests from outside the
team are not merged while the stage contract and the target schema are
unsettled, because work written against a moving contract is wasted for
everyone.

Dependabot is the one bot that opens pull requests. Its bumps are reviewed
like any other change.

## How the team works

### Issues first

Nothing is built without an issue. Each milestone opens with a Wayfinder map
issue that names the open decisions. Research and grilling tickets resolve
those into ADRs. Build tickets are labelled `ready-for-agent` only once their
spec is settled.

### ADR before code

Write an ADR before writing code for anything that touches:

- the stage contract or the run manifest format
- the target schema
- which external model a stage calls
- the ranking objectives
- what the scientist agent is allowed to say
- a new dependency

### Retrodiction with the scoring model

A scoring model arrives with at least one retrodiction case, and the tolerance
is agreed on the issue before the model is run against it. See
[docs/validation/README.md](docs/validation/README.md).

### Sources for biology

Every sequence, structure, temperature, pH and published measurement cites
where it came from, in the code or the target file next to the value. No
values from memory. If the source is missing, say so and leave a
`needs-research` note rather than writing a plausible number.

### Small pull requests

One issue, one pull request. Green CI before review. Squash only if the
commits do not each stand on their own.

## Commits

Conventional Commits: `<type>(<scope>): <description>`, lowercase, imperative,
no full stop, 72 characters at most. Types: `feat`, `fix`, `docs`, `test`,
`refactor`, `perf`, `build`, `ci`, `chore`, `revert`. Scopes follow the
package layout: `core`, `sense`, `chassis`, `design`, `fold`, `score`, `rank`,
`explain`, `runs`, `api`, `web`, `targets`, `bio`, `adr`.

The body says why, not what. Say what was checked and how. Reference the issue
with `refs #<n>`, never a closing keyword. No co-author trailers.

## Local setup

```bash
pip install -e ".[dev]"
just install-hooks
just ci
```

`just ci` runs what CI runs: `ruff check`, `ruff format --check`, `pytest`.

## Writing

British English. Plain, short sentences. No em dashes. Use the terms in
[CONTEXT.md](CONTEXT.md), and the words under _Words we do not use_ stay
unused. Do not claim more than a model has predicted.
