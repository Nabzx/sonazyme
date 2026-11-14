# ADR-0007: Version the manifest and address artefacts by content

- Status: Accepted
- Date: 2026-11-14
- Issues: #22, #23

## Context

Design and scoring are being built separately from the rest of the pipeline.
Both need a concrete contract before integration. ADR-0004 requires one record
of every attempt, including failures, without embedding large artefacts.

## Decision

Use UTF-8 JSON with `schema_version: 1`. A manifest holds a `run_id`,
`target` artefact reference, `status` (`running` or `finished`) and an ordered
`entries` list. An entry holds `id`, `stage`, `status` (`succeeded`, `failed`
or `rejected`), `producer` (`name`, `version`, `kind`), `inputs` (earlier
entry ids), `parameters`, `metrics`, `artefacts` and `reason`.

Producer kind is `model` or `code`. Even deterministic stages name their code
version. Parameters include the seed when a model exposes one. A failed or
rejected entry requires a reason and cannot carry metrics. Entry ids are
unique within a run. Repeated stages are allowed for attempts and rounds.

A metric has `name`, finite numeric `value`, `unit`, `basis` (`prediction`
or `measurement`) and `source`. A prediction's source is the entry's model
producer; a measurement's source is its citation. Storing a prediction does
not authorise display or ranking: the scoring retrodiction gate still applies.
Targets retain their own sourced or assumed markings in their artefact.

Artefacts are stored as `artefacts/<sha256>` relative to the run directory.
A reference holds `path`, `sha256` and `size_bytes`. Readers verify all three.
The target is itself an artefact, so replay never relies on a mutable target
file outside the run. Consumers carry a display filename separately if needed.

The writer reads the existing manifest before saving and accepts only a longer
entry list with an identical prefix. A finished manifest cannot change. Writes
replace a temporary file atomically. One writer owns a run; concurrent writers
are unsupported. This does not yet implement scheduling, retries or a cache
key for external model calls (#24).

Keys and credentials are never parameters or artefacts. Callers must pass only
public model settings and sanitised failure reasons.

## Consequences

Both integrations can use the same reader and writer without new dependencies.
Offline readers can detect missing or changed artefacts. Append-only is enforced
by the API, not a tamper-proof audit guarantee against manual file edits.

## Alternatives considered

Separate stage files would make ordering and provenance harder to follow.
A database adds deployment work before the first run exists. Both are deferred.
