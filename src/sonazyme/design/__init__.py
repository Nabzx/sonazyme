"""The design stage: variants of a chassis, through Tamarind Bio.

Proposes mutation sets away from the active site (ADR-0005), recording the
strategy behind each variant and keeping the rejects. See
docs/platform/tamarind.md.
"""

from __future__ import annotations

from sonazyme.core import stage_not_built


def run(manifest: object) -> object:
    """Run the design stage over a run manifest, returning the longer manifest."""
    raise stage_not_built("design")
