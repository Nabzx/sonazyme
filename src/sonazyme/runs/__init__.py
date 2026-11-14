"""Run manifests and the artefact store.

A run is identified, immutable once finished, and replayable from its manifest
alone. Artefacts are files; the manifest references them and never contains
them. See docs/architecture/ARCHITECTURE.md.

Nothing here is built yet. The manifest format is an M1 decision.
"""

from __future__ import annotations
