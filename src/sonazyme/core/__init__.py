"""The run manifest, the envelope, and the contract every stage meets.

A stage is a function from a run manifest to a longer run manifest. It reads
the manifest and the artefacts the manifest points at, writes artefacts as
files, and appends entries recording what it did: inputs, model, version,
parameters, scores and artefact paths. See
docs/architecture/ARCHITECTURE.md.

The versioned manifest contract lives in core.manifest (ADR-0007). This module
holds the error type and stage list so unbuilt stages can still name their milestone.
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
