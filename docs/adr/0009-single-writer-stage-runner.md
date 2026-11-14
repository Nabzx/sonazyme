# ADR-0009: Resume stages from verified successful entries

- Status: Accepted
- Date: 2026-11-14
- Issue: #24

## Context

The manifest and store exist. A runner must preserve failures and avoid
repeating identical successful calls while models are being integrated.

## Decision

Execute one stage request at a time. A request names stage, producer and exact
version, parameters (including seed and round where relevant), and input entry
ids. The runner reads and verifies the saved manifest before every request.
Inputs must name successful earlier entries. A bound stage reads the manifest,
uses the supplied store for I/O and returns a manifest with exactly one new
entry matching the request. The runner owns manifest persistence.

Reuse an existing successful entry only when stage, producer, parameters and
ordered input ids match exactly in the same run. The target is immutable and
all referenced bytes are verified before reuse. The existing entry is the
cache record; no second cache index is maintained. Do not reuse failed or
rejected attempts. Changed versions, settings, seed, round or inputs require
a new call. Adapters must include every setting affecting output and record
actual immutable model versions. A mutable provider alias is not sufficient.

Cache reuse does not append a fictitious model call. Disabling cache forces a
new attempt. A finished run may be read or reused but cannot execute anything
new. Replay is verified loading only and never invokes a stage.

If execution or output validation raises, append a failed attempt with a
generic reason, then raise StageExecutionError without provider error text.
An interrupt or process crash may leave unreferenced artefacts. Resume retries
an unrecorded call; exactly-once external execution is not guaranteed. Adapter
idempotency and provider job recovery remain integration concerns.

## Consequences

The first runner works offline for saved successful requests and imports no
stage internals. There is no scheduler, cross-run cache, parallel execution,
automatic retry loop or claim that an integrity check has passed. These need
separate stage and orchestration contracts.

## Alternatives considered

Caching by sequence alone ignores envelope, model and design settings.
Cross-run reuse complicates copying and verifying the provenance chain.
Both are deferred in favour of conservative run-local reuse.
