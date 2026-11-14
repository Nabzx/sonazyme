# ADR-0008: Preserve evidence and unknowns in target records

- Status: Accepted
- Date: 2026-11-14
- Issue: #7

## Context

The target research found literature and fluid guidance, not operator samples.
A schema must not turn an unknown chemistry into untreated water or a guideline
into a measurement. ADR-0002 requires targets to remain data.

## Decision

Use TOML, parsed by the standard library, with `schema_version = 1`. Require
`target` metadata (`id`, `name`, `summary`, `loop`), `community`, an `anchor`
list, and `envelope`. Ids and prose are editorial metadata. Loop, community,
all anchor fields and all envelope fields are evidence records.

An evidence record has `basis`, plus `value` when known. `literature`,
`guidance` and `measurement` require a non-empty `source`. `assumption`
requires a `reason` and may cite a source. `unknown` requires a `reason` and
forbids a value. Known records may carry a reason for scope limits. Reject
missing markings and unknown keys. No default biological values are supplied.

Anchor fields are `component`, `kind`, `bond`, `enzyme_family` and `share`.
Envelope fields are `temperature_c`, `ph`, `chemistry` and `residence_time_s`.
Ranges are ordered pairs of finite numbers; residence time is non-negative.
Share, if known, is a fraction from zero to one. Chemistry is a list of names;
concentrations are not inferred. Unknown records omit `value` in TOML and
remain unknown in the normalised JSON artefact.

`sense` reads the target artefact, validates it and appends one entry pointing
at normalised JSON with every evidence record intact. It makes no model call
and makes no readiness, efficacy or stability claim. A research target with
unknowns can pass `sense`; downstream stages must require their own inputs.

The function still reads and returns a manifest. An explicit `store` keyword
supplies run-local file I/O, not biological inputs. Parameters and input entry
ids are recorded explicitly. No stage imports another stage's implementation.

## Consequences

Unknowns are visible downstream. Target loading is useful before the first
scoring run. A source's presence is checked, not its scientific truth. A
research target is not an operational envelope. Target files must use evidence
records instead of the earlier illustrative schema in targets/README.md.

## Alternatives considered

Flat values with a shared citation lose which value the citation supports.
Requiring every value to be known encourages invented contact times. Both
are rejected.
