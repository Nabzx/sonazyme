"""The sense stage: what holds this film together, and in what conditions.

Reads a target file and turns it into the run's working definition: the
anchors to attack and the envelope to survive, carrying through whether each
value is sourced or assumed. No model calls; the intelligence is in the target
file (ADR-0002).
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the sense stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("sense")
