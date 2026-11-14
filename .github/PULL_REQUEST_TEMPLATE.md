## What this does

One or two sentences. Reference the issue in the body: `refs #<n>`.

## Why

The reason, or a pointer to the ADR or map that called for it.

## How it was checked

What you ran and what you saw. For a scoring change: which retrodiction cases,
and whether each is blind or a calibration check.

## Checklist

- [ ] Title and commits follow Conventional Commits; `refs #<n>`, not `closes #<n>`
- [ ] Advances a labelled issue
- [ ] An ADR covers anything touching the stage contract, the run manifest, the target schema, which model a stage calls, the ranking objectives, what the scientist may say, or a new dependency
- [ ] Every biological value cites its source next to it, or is marked as an assumption
- [ ] Every number shown to a human carries its model and version, and is labelled a prediction
- [ ] A new scoring model has a passing retrodiction case, with its tolerance agreed on the issue first
- [ ] Nothing here claims a wet-lab result, an efficacy figure or a saving
- [ ] Within the scope in `SECURITY.md`
- [ ] `ruff check`, `ruff format --check` and `pytest` pass locally
- [ ] British English, no em dashes, no co-author trailer, terms from `CONTEXT.md`
- [ ] Docs updated (`CONTEXT.md`, `ROADMAP.md`, `docs/progress/`, `CHANGELOG.md`) if behaviour changed
