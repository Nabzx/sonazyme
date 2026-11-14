# ADR-0012: Run the API independently and replay verified snapshots

- Status: Accepted
- Date: 2026-11-14
- Issues: #32, #33, #34
- Supersedes: ADR-0011's requirement to serve the dashboard beside the API

## Context

The user has deferred website work while changing the colour scheme. Model
execution and outputs belong to the partner. Backend work can proceed without
either dependency. The current manifest and content-addressed store can
already represent saved runs.

## Decision

Run `python -m sonazyme.api` as a standalone loopback HTTP service. The root
returns JSON route discovery. Static files are optional and enabled only by an
explicit `--web-dir`; no HTML or stylesheet is needed to start the service.
All routes remain read-only. No model clients or stage implementations are
imported by the API.

Add `GET /api/runs/<key>/events` as a server-sent event stream of verified
saved manifests. Event ids are the digest of canonical manifest JSON. Honour
`Last-Event-ID` to avoid repeating an unchanged manifest. Send a comment
heartbeat while unchanged, and an `end` event when the saved run is sealed.
This observes disk writes, not remote model execution. A corrupt snapshot
ends the stream with an error rather than sending unverified data.

Snapshot export includes only the manifest's directly referenced artefacts,
encoded as base64 with the existing content digests and sizes. CLI restore
validates the complete manifest, all encodings, sizes and hashes before
publishing a new run directory. It never overwrites an existing directory or
changes scientific fields. It does not execute stages. Snapshot file timestamps
are metadata, not inferred model dates. Export and restore have bounded input
sizes and single-writer scope. There is no cross-process transaction guarantee.

Read routes reject traversal, undeclared artefacts and symlink escapes. Invalid
run directories are reported separately from available runs. Optional static
files remain allowlisted. Mutation requests receive an explicit method error.

## Consequences

The frontend can be built later against a tested API. The partner can append
outputs through the existing manifest contract; the API does not need their
service credentials. A development snapshot can be moved and inspected
offline. This does not complete the real model-driven fixture in #34.

## Alternatives considered

Waiting for the website would block independently useful backend work.
Streaming provider-specific job messages would couple the API to the partner's
integrations. Both are rejected. SSE is simpler than a bidirectional socket
for a read-only sequence of saved manifests.
