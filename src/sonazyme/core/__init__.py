"""The run manifest, the envelope, and the contract every stage meets.

A stage is a function from a run manifest to a longer run manifest. It reads
the manifest and the artefacts the manifest points at, writes artefacts as
files, and appends entries recording what it did: inputs, model, version,
parameters, scores and artefact paths. See
docs/architecture/ARCHITECTURE.md.

Nothing here is built yet. The manifest format is an M1 decision and arrives
with its ADR, so this module holds only the error type and the stage list.
"""

from __future__ import annotations

#: Each stage, and the milestone that builds it. See ROADMAP.md.
STAGES: dict[str, int] = {
    "sense": 1,
    "chassis": 2,
    "design": 3,
    "fold": 3,
    "score": 4,
    "rank": 5,
    "explain": 6,
}


class NotBuiltError(NotImplementedError):
    """Raised by any stage the roadmap has not reached yet."""

    def __init__(self, what: str, milestone: int) -> None:
        """Name the missing piece and the milestone that builds it."""
        self.what = what
        self.milestone = milestone
        super().__init__(
            f"{what} is not built yet. It is planned for M{milestone}; see ROADMAP.md."
        )


def stage_not_built(stage: str) -> NotBuiltError:
    """Return the error a stage raises until its milestone builds it."""
    return NotBuiltError(f"The {stage} stage", milestone=STAGES[stage])
