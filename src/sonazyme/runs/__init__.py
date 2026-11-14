"""Run manifests and the artefact store.

A run is identified, immutable once finished, and replayable from its manifest
alone. Artefacts are files; the manifest references them and never contains
them. See docs/architecture/ARCHITECTURE.md.

The content-addressed artefact store and manifest writer live in runs.store
(ADR-0007). The single-writer stage runner and run-local cache live in
runs.runner (ADR-0009). External service adapters remain unbuilt.
"""

from __future__ import annotations
