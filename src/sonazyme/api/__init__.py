"""The service Sonazyme Lab reads.

Serves run manifests and artefacts, and nothing else. It holds no second copy
of the science and computes no number of its own: if it is on screen, it came
from a manifest entry (ADR-0004).

The local read-only service lives in api.server. Run python -m sonazyme.api
from the repository root. See ADR-0011 for its routes and local-only scope.
"""

from __future__ import annotations
