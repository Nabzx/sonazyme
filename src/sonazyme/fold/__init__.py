"""The fold stage: a predicted structure per variant, through Boltz-2.

Folds the chassis and every variant with the same model at the same version,
carrying confidence through. See docs/platform/boltz2.md.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the fold stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("fold")
