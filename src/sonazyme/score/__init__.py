"""The score stage: stability in the envelope, and active-site integrity.

Runs the integrity check first and rejects any variant whose active-site
geometry moved (ADR-0005), then estimates how well the survivors hold their
fold in the envelope. A scoring model is trusted only after it retrodicts
published measurements. See docs/validation/README.md.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the score stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("score")
