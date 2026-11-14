"""The chassis stage: parent enzymes that cut the target's anchors.

Selects natural enzymes known to cut each anchor's bond, with sequence,
source and a defined active site, and folds each once to give the baseline a
redesign has to beat.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the chassis stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("chassis")
