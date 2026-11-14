"""The rank stage: the shortlist, with its trade-offs visible.

Multi-objective: predicted stability, predicted activity or its proxy, and
model confidence. The front is kept rather than collapsed into one number,
because stabilising an enzyme often slows it.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the rank stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("rank")
