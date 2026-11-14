# ADR-0011: Serve a buildless dashboard beside a read-only run API

- Status: Accepted
- Date: 2026-11-14
- Issues: #32, #35, #37, #46

## Context

The run store exists. Partner-owned models will supply predictions separately.
The demo must work on a laptop with no external network. The app must not
create another copy of the science or invent values to fill missing panels.

## Decision

Use browser-native HTML, CSS and JavaScript modules under `web/`, with no
runtime package manager, CDN, hosted service or remote font. Serve the app and
a read-only JSON API on the same loopback origin using Python's standard
library HTTP server. This is a local development and offline demo server,
not an authenticated internet service or a production hosting decision.

`GET /api/runs` lists saved run directories with their manifest identity and
snapshot file modification time. The latter is file metadata, never a claimed
model run date. `GET /api/runs/<key>/manifest` returns the unchanged manifest.
`GET /api/runs/<key>/artefacts/<sha256>` returns only an artefact referenced by
that manifest, after integrity verification. No mutation routes or model calls
exist. Invalid snapshots are reported rather than repaired or silently used.
Filesystem traversal and symlink escapes are rejected. Static files use an
explicit allowlist, so repository files and credentials cannot be browsed.

A snapshot export contains the manifest, its referenced artefact bytes and
snapshot metadata. The browser can open this file and verify its digests for
offline inspection. Exporting a development run does not make it the real
end-to-end demo fixture required by #34. It is labelled as a saved snapshot.

The UI presents three acts from the existing specification. The run inspector
is driven by the manifest and artefacts. It shows sources and evidence basis
beside target values, each stage's actual status, and links to original
artefacts. It never treats successful parsing as scientific validation.
Missing predictions, shortlist and scientist artefacts have explicit empty
states. The API does not rank, score, call an agent or compute scientific data.

Use a shared provenance component for metric display. A prediction requires
its entry's named model and version and matching source. Scoring metrics are
withheld until an agreed retrodiction-evidence contract is integrated. A
measurement requires its citation. Source presence is not verification of the
source's truth. Confidence is labelled as predicted confidence, never activity.

Use a lightweight, labelled alpha-carbon trace to inspect supplied PDB
coordinates, with pointer rotation and zoom. It is not a molecular surface,
unfolding simulation or substitute for a full molecular viewer. No placeholder
protein appears when coordinates are absent. Colours remain fixed: prediction,
active site, changed region. The overhead workflow is permanently labelled as
an illustration of intended behaviour, even during animation or screenshots.

## Consequences

`python -m sonazyme.api` is enough to run the first local app. No deployment
is required or included. The existing Sites skill's local-only workflow fits
this repository's Python service and offline requirement. Real model fixture
integration, retrodiction display, ranking and scientist behaviour remain
separate work. A public deployment needs a later hosting and access decision.

## Alternatives considered

A React application adds a build and dependency workflow before the first
data screen exists. A hosted dashboard cannot reach this local Python API
without additional infrastructure. Both are deferred. A scientific viewer
library is worth revisiting if the alpha-carbon trace proves insufficient.
