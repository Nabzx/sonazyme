"""The explain stage: the scientist agent, answering from the run.

Answers questions about a run using that run's manifest and artefacts, citing
what it used, and says so when the run does not contain the answer.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the explain stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("explain")
