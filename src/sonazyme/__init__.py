"""Sonazyme: enzymes designed to break down biofilm and to survive the loop.

Scaffold. The package installs and imports, and every stage that is not built
yet raises :class:`NotBuiltError` naming the milestone that will build it. See
ROADMAP.md, and docs/biology/ for the biology behind the terms.
"""

from sonazyme.core import STAGES, NotBuiltError

__version__ = "0.0.1"

__all__ = ["STAGES", "NotBuiltError", "__version__"]
