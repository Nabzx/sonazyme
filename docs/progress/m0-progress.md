# M0 progress

The scaffold milestone. Updated as tickets close.

## Done

- Repo structure, CI, Dependabot, labeler, issue templates, commit hooks.
- ADR-0001 to ADR-0006 accepted.
- Glossary, roadmap, architecture, retrodiction policy.
- `docs/biology/`, eleven pages, GCSE level.
- `docs/platform/`, one note per external service.
- `docs/design/dashboard.md`, the five screens.
- Package skeleton: seven stages, each naming the milestone that builds it.

## Since the scaffold (local, unreleased)

- A research-only Psl target, evidence-bearing loader, manifest store and
  single-writer runner are implemented. `sense` can record a target.
- The sourced PslG registry and `chassis` selection are implemented. A baseline
  Boltz wrapper and policy-driven integrity helper pass synthetic software
  checks. No real model prediction has run. Full binding-site exclusion and
  the biological integrity tolerance remain unresolved.

## Not done

- No end-to-end design run has been attempted.
- No external service has been called from this repo.
- No retrodiction case exists, so no scoring model is trusted yet.
- `web/` is a specification, not an app.
